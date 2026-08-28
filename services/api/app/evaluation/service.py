import hashlib
import json
import uuid
from decimal import Decimal
from functools import lru_cache
from typing import Literal, cast

from pydantic import SecretStr, TypeAdapter
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.attempt_models import Attempt
from app.attempts import owned_attempt
from app.config import get_settings
from app.content.models import (
    Concept,
    GeometrySceneVersion,
    ProblemHint,
    ProblemVersion,
    ReferenceSolution,
    RubricItem,
)
from app.content.schemas import (
    AnimateAction,
    AskSelectAction,
    ContentBlock,
    GeometryAction,
    TextBlock,
)
from app.content.schemas import (
    GeometrySceneVersion as GeometrySceneVersionSchema,
)
from app.errors import AppError
from app.evaluation.fake_provider import DeterministicFakeEvaluationProvider
from app.evaluation.gemini_provider import GeminiEvaluationProvider
from app.evaluation.models import AttemptStep, Evaluation, EvaluationRun, HintEvent
from app.evaluation.prompt import (
    PROMPT_HASH,
    PROMPT_TEXT,
    PROMPT_VERSION,
    PROVIDER_SCHEMA_VERSION,
)
from app.evaluation.provider import (
    EvaluationProviderPermanentError,
    EvaluationProviderRequest,
    EvaluationProviderResult,
    EvaluationProviderSchemaError,
    EvaluationProviderTransportError,
    StrictEvaluationProvider,
)
from app.evaluation.schemas import (
    EvaluationFailureState,
    EvaluationNotStartedState,
    EvaluationProcessingState,
    EvaluationReadyState,
    EvaluationRequest,
    EvaluationResponse,
    EvaluationRunResponse,
    EvaluationStateResponse,
    EvaluationUncertainState,
    NextHintRequest,
    NextHintResponse,
    ProviderReadyEvaluation,
    ReadyEvaluationResponse,
    ReasoningStepResponse,
    RubricScoreResponse,
    UncertainEvaluationResponse,
)
from app.models import User
from app.security import utc_now
from app.transcription.models import PromptVersion, TranscriptConfirmation, TranscriptVersion
from app.transcription.schemas import TranscriptDocument, canonical_transcript_hash

PROMPT_VERSION_ID = uuid.UUID("70000000-0000-4000-8000-000000000100")
blocks_adapter = TypeAdapter(list[ContentBlock])
actions_adapter = TypeAdapter(list[GeometryAction])
scene_adapter = TypeAdapter(GeometrySceneVersionSchema)


def _required_key(value: SecretStr | None) -> str:
    if value is None:
        raise RuntimeError("Configured evaluation provider has no server API key")
    return value.get_secret_value()


@lru_cache
def get_evaluation_provider() -> StrictEvaluationProvider:
    settings = get_settings()
    if settings.evaluation_provider == "fake":
        return DeterministicFakeEvaluationProvider()
    return GeminiEvaluationProvider(
        api_key=_required_key(settings.gemini_api_key),
        model_snapshot=settings.evaluation_model_snapshot,
        timeout_seconds=settings.evaluation_timeout_seconds,
    )


async def _prompt_version(database: AsyncSession) -> PromptVersion:
    await database.execute(
        pg_insert(PromptVersion)
        .values(
            id=PROMPT_VERSION_ID,
            operation="evaluation",
            version=PROMPT_VERSION,
            prompt_text=PROMPT_TEXT,
            prompt_sha256=PROMPT_HASH,
            schema_version=PROVIDER_SCHEMA_VERSION,
        )
        .on_conflict_do_nothing(index_elements=[PromptVersion.id])
    )
    stored = await database.get(PromptVersion, PROMPT_VERSION_ID)
    if stored is None:
        raise RuntimeError("Evaluation prompt version could not be persisted")
    if (
        stored.operation != "evaluation"
        or stored.version != PROMPT_VERSION
        or stored.prompt_text != PROMPT_TEXT
        or stored.prompt_sha256 != PROMPT_HASH
        or stored.schema_version != PROVIDER_SCHEMA_VERSION
    ):
        raise RuntimeError("Stored evaluation prompt identity does not match application code")
    return stored


def _request_fingerprint(
    *,
    attempt_id: uuid.UUID,
    transcript_version_id: uuid.UUID,
    transcript_hash: str,
    provider: StrictEvaluationProvider,
) -> str:
    identity = provider.identity
    source = ":".join(
        (
            str(attempt_id),
            str(transcript_version_id),
            transcript_hash,
            identity.provider,
            identity.model_snapshot,
            identity.prompt_hash,
            identity.schema_version,
        )
    )
    return hashlib.sha256(source.encode()).hexdigest()


async def _confirmed_transcript(
    *,
    attempt: Attempt,
    transcript_version_id: uuid.UUID,
    database: AsyncSession,
) -> tuple[TranscriptVersion, TranscriptDocument]:
    confirmation = await database.scalar(
        select(TranscriptConfirmation).where(
            TranscriptConfirmation.attempt_id == attempt.id,
            TranscriptConfirmation.transcript_version_id == transcript_version_id,
        )
    )
    if confirmation is None:
        raise AppError(
            status_code=409,
            code="transcript_not_confirmed",
            message="Confirm this exact transcript version before evaluation.",
        )
    version = await database.get(TranscriptVersion, transcript_version_id)
    if version is None or version.attempt_id != attempt.id:
        raise RuntimeError("Confirmed transcript relationship is invalid")
    transcript = TranscriptDocument.model_validate(version.document_json)
    if (
        transcript.attempt_id != attempt.id
        or canonical_transcript_hash(transcript) != confirmation.transcript_sha256
        or version.transcript_sha256 != confirmation.transcript_sha256
    ):
        raise RuntimeError("Confirmed transcript identity is invalid")
    return version, transcript


async def _evaluation_context(
    *,
    attempt: Attempt,
    transcript: TranscriptDocument,
    database: AsyncSession,
) -> tuple[str, list[RubricItem], ProblemVersion]:
    problem = await database.get(ProblemVersion, attempt.problem_version_id)
    if problem is None:
        raise RuntimeError("Attempt lost its immutable problem version")
    references = list(
        await database.scalars(
            select(ReferenceSolution)
            .where(ReferenceSolution.problem_version_id == problem.id)
            .order_by(ReferenceSolution.solution_code, ReferenceSolution.id)
        )
    )
    if not references or any(not reference.non_exhaustive for reference in references):
        raise RuntimeError("Evaluation references must be explicitly non-exhaustive")
    rubric = list(
        await database.scalars(
            select(RubricItem)
            .where(RubricItem.problem_version_id == problem.id)
            .order_by(RubricItem.order_index, RubricItem.id)
        )
    )
    if not rubric or sum((item.maximum_score for item in rubric), Decimal("0")) != Decimal(
        problem.maximum_score
    ):
        raise RuntimeError("Immutable rubric does not match the problem maximum score")
    context = {
        "problemStatement": problem.statement_json,
        "confirmedTranscript": transcript.model_dump(mode="json", by_alias=True),
        "referenceSolutions": [
            {
                "methodLabel": reference.method_label,
                "content": reference.content_json,
                "nonExhaustive": True,
            }
            for reference in references
        ],
        "rubric": [
            {
                "rubricCode": item.rubric_code,
                "description": item.description_json,
                "maximumScore": str(item.maximum_score),
                "skillId": str(item.skill_id),
            }
            for item in rubric
        ],
        "referenceSolutionsNonExhaustive": True,
    }
    return json.dumps(context, ensure_ascii=False, separators=(",", ":")), rubric, problem


def _text_block(identifier: str, text: str) -> list[dict[str, object]]:
    block = TextBlock(id=identifier, type="text", text=text)
    return [block.model_dump(mode="json", by_alias=True)]


def _run_response(run: EvaluationRun, prompt: PromptVersion) -> EvaluationRunResponse:
    return EvaluationRunResponse(
        id=run.id,
        status=cast(
            Literal[
                "processing",
                "succeeded",
                "uncertain",
                "retryable_failure",
                "permanent_failure",
                "invalid_schema",
            ],
            run.status,
        ),
        provider=run.provider,
        model_snapshot=run.model_snapshot,
        prompt_version=prompt.version,
        prompt_hash=prompt.prompt_sha256,
        schema_version=run.schema_version,
        pricing_version=run.pricing_version,
        schema_attempts=run.schema_attempts,
        retry_count=run.retry_count,
        latency_ms=run.latency_ms,
        input_tokens=run.input_tokens,
        output_tokens=run.output_tokens,
        cost_usd=run.cost_usd,
        error_code=run.error_code,
        started_at=run.started_at,
        completed_at=run.completed_at,
    )


async def _response_for_run(
    run: EvaluationRun, database: AsyncSession
) -> EvaluationResponse | None:
    prompt = await database.get(PromptVersion, run.prompt_version_id)
    if prompt is None:
        raise RuntimeError("Evaluation run lost its immutable prompt")
    evaluation = await database.scalar(
        select(Evaluation).where(Evaluation.evaluation_run_id == run.id)
    )
    if evaluation is None:
        return None
    if evaluation.outcome == "uncertain":
        if evaluation.uncertainty_reason_json is None:
            raise RuntimeError("Uncertain evaluation lost its safe reason")
        return UncertainEvaluationResponse(
            outcome="uncertain",
            evaluation_id=evaluation.id,
            confirmed_transcript_version_id=run.confirmed_transcript_version_id,
            reason=blocks_adapter.validate_python(evaluation.uncertainty_reason_json),
            recommended_action="manual_review",
            run=_run_response(run, prompt),
        )
    rows = list(
        await database.scalars(
            select(AttemptStep)
            .where(AttemptStep.evaluation_run_id == run.id)
            .order_by(AttemptStep.position)
        )
    )
    if (
        evaluation.score is None
        or evaluation.maximum_score is None
        or evaluation.rubric_breakdown_json is None
        or evaluation.feedback_json is None
        or evaluation.next_steps_json is None
        or not rows
    ):
        raise RuntimeError("Ready evaluation is incomplete")
    steps = [
        ReasoningStepResponse(
            id=row.id,
            position=row.position,
            transcript_block_ids=cast(list[str], row.transcript_block_ids_json),
            summary=blocks_adapter.validate_python(row.summary_json),
            judgment=cast(
                Literal["correct", "incorrect", "uncertain", "not_assessable"], row.judgment
            ),
            error_kind=cast(Literal["none", "root", "dependent"], row.error_kind),
            depends_on_step_ids=[uuid.UUID(value) for value in row.depends_on_step_ids_json],
            feedback=blocks_adapter.validate_python(row.feedback_json),
        )
        for row in rows
    ]
    return ReadyEvaluationResponse(
        outcome="ready",
        evaluation_id=evaluation.id,
        confirmed_transcript_version_id=run.confirmed_transcript_version_id,
        score=evaluation.score,
        maximum_score=evaluation.maximum_score,
        reasoning_steps=steps,
        rubric_breakdown=[
            RubricScoreResponse.model_validate(item) for item in evaluation.rubric_breakdown_json
        ],
        feedback=blocks_adapter.validate_python(evaluation.feedback_json),
        next_steps=blocks_adapter.validate_python(evaluation.next_steps_json),
        reference_solutions_non_exhaustive=True,
        run=_run_response(run, prompt),
    )


def _complete_failure(
    run: EvaluationRun,
    *,
    status: Literal["retryable_failure", "permanent_failure", "invalid_schema"],
    schema_attempts: int,
    latency_ms: int,
    input_tokens: int,
    output_tokens: int,
    cost_usd: Decimal,
    error_code: str,
) -> None:
    run.status = status
    run.schema_attempts = schema_attempts
    run.retry_count = max(0, schema_attempts - 1)
    run.latency_ms = latency_ms
    run.input_tokens = input_tokens
    run.output_tokens = output_tokens
    run.cost_usd = cost_usd
    run.error_code = error_code
    run.completed_at = utc_now()


def _stored_run_error(run: EvaluationRun) -> AppError:
    if run.status == "retryable_failure":
        return AppError(
            status_code=503,
            code="evaluation_temporarily_unavailable",
            message="Evaluation is temporarily unavailable. Try again.",
        )
    if run.status == "invalid_schema":
        return AppError(
            status_code=502,
            code="evaluation_invalid_schema",
            message="The evaluation response was invalid after one repair attempt.",
        )
    return AppError(
        status_code=502,
        code="evaluation_permanent_failure",
        message="The evaluation provider could not evaluate this work.",
    )


async def _persist_result(
    *,
    run: EvaluationRun,
    result: EvaluationProviderResult,
    rubric: list[RubricItem],
    problem: ProblemVersion,
    database: AsyncSession,
) -> EvaluationResponse:
    run.schema_attempts = result.schema_attempts
    run.retry_count = result.schema_attempts - 1
    run.latency_ms = result.latency_ms
    run.input_tokens = result.input_tokens
    run.output_tokens = result.output_tokens
    run.cost_usd = result.cost_usd
    run.completed_at = utc_now()
    if result.outcome == "uncertain":
        run.status = "uncertain"
        payload = result.payload
        if isinstance(payload, ProviderReadyEvaluation):
            raise RuntimeError("Provider outcome and payload disagree")
        evaluation = Evaluation(
            evaluation_run_id=run.id,
            outcome="uncertain",
            uncertainty_reason_json=_text_block("m7-uncertainty-reason", payload.reason),
            recommended_action="manual_review",
        )
        database.add(evaluation)
        await database.commit()
        response = await _response_for_run(run, database)
        if response is None:
            raise RuntimeError("Uncertain evaluation was not persisted")
        return response

    payload = result.payload
    if not isinstance(payload, ProviderReadyEvaluation):
        raise RuntimeError("Provider outcome and payload disagree")
    run.status = "succeeded"
    step_ids = {step.step_key: uuid.uuid4() for step in payload.reasoning_steps}
    for position, step in enumerate(payload.reasoning_steps, start=1):
        database.add(
            AttemptStep(
                id=step_ids[step.step_key],
                evaluation_run_id=run.id,
                position=position,
                transcript_block_ids_json=list(step.transcript_block_ids),
                summary_json=_text_block(f"m7-step-{position}-summary", step.summary),
                judgment=step.judgment,
                error_kind=step.error_kind,
                depends_on_step_ids_json=[str(step_ids[key]) for key in step.depends_on_step_keys],
                feedback_json=_text_block(f"m7-step-{position}-feedback", step.feedback),
            )
        )
    rubric_by_code = {item.rubric_code: item for item in rubric}
    breakdown = [
        RubricScoreResponse(
            rubric_item_id=rubric_by_code[award.rubric_code].id,
            rubric_code=award.rubric_code,
            awarded_score=award.awarded_score,
            maximum_score=rubric_by_code[award.rubric_code].maximum_score,
            explanation=blocks_adapter.validate_python(
                _text_block(f"m7-rubric-{index}-explanation", award.explanation)
            ),
        )
        for index, award in enumerate(payload.rubric_awards, start=1)
    ]
    score = sum((item.awarded_score for item in breakdown), Decimal("0"))
    evaluation = Evaluation(
        evaluation_run_id=run.id,
        outcome="ready",
        score=score,
        maximum_score=problem.maximum_score,
        rubric_breakdown_json=[item.model_dump(mode="json", by_alias=True) for item in breakdown],
        feedback_json=_text_block("m7-overall-feedback", payload.overall_feedback),
        next_steps_json=_text_block("m7-next-action", payload.next_action),
    )
    database.add(evaluation)
    await database.commit()
    response = await _response_for_run(run, database)
    if response is None:
        raise RuntimeError("Ready evaluation was not persisted")
    return response


async def evaluate_attempt(
    *,
    attempt_id: uuid.UUID,
    payload: EvaluationRequest,
    user: User,
    database: AsyncSession,
    provider: StrictEvaluationProvider,
) -> EvaluationResponse:
    attempt = await owned_attempt(attempt_id, user, database)
    await database.execute(select(Attempt.id).where(Attempt.id == attempt.id).with_for_update())
    version, transcript = await _confirmed_transcript(
        attempt=attempt,
        transcript_version_id=payload.confirmed_transcript_version_id,
        database=database,
    )
    context_json, rubric, problem = await _evaluation_context(
        attempt=attempt, transcript=transcript, database=database
    )
    fingerprint = _request_fingerprint(
        attempt_id=attempt.id,
        transcript_version_id=version.id,
        transcript_hash=version.transcript_sha256,
        provider=provider,
    )
    existing = await database.scalar(
        select(EvaluationRun).where(EvaluationRun.idempotency_key == payload.idempotency_key)
    )
    if existing is not None:
        if existing.attempt_id != attempt.id or existing.request_fingerprint != fingerprint:
            raise AppError(
                status_code=409,
                code="evaluation_idempotency_conflict",
                message="Use a new evaluation request identifier.",
            )
        if existing.status == "processing":
            raise AppError(
                status_code=409,
                code="evaluation_in_progress",
                message="Evaluation is already in progress.",
            )
        response = await _response_for_run(existing, database)
        if response is not None:
            return response
        raise _stored_run_error(existing)
    completed = await database.scalar(
        select(EvaluationRun)
        .where(
            EvaluationRun.attempt_id == attempt.id,
            EvaluationRun.request_fingerprint == fingerprint,
            EvaluationRun.status.in_(
                ("succeeded", "uncertain", "permanent_failure", "invalid_schema")
            ),
        )
        .order_by(EvaluationRun.started_at.desc(), EvaluationRun.id.desc())
    )
    if completed is not None:
        response = await _response_for_run(completed, database)
        if response is not None:
            return response
        raise _stored_run_error(completed)
    prompt = await _prompt_version(database)
    run = EvaluationRun(
        attempt_id=attempt.id,
        confirmed_transcript_version_id=version.id,
        prompt_version_id=prompt.id,
        provider=provider.identity.provider,
        model_snapshot=provider.identity.model_snapshot,
        schema_version=provider.identity.schema_version,
        pricing_version=provider.identity.pricing_version,
        idempotency_key=payload.idempotency_key,
        request_fingerprint=fingerprint,
        status="processing",
        schema_attempts=0,
        retry_count=0,
    )
    database.add(run)
    try:
        await database.commit()
    except IntegrityError as error:
        await database.rollback()
        raise AppError(
            status_code=409,
            code="evaluation_in_progress",
            message="Evaluation is already in progress.",
        ) from error
    request = EvaluationProviderRequest(
        attempt_id=attempt.id,
        transcript_block_ids=tuple(block.id for block in transcript.blocks),
        rubric_limits=tuple((item.rubric_code, item.maximum_score) for item in rubric),
        context_json=context_json,
    )
    try:
        result = await provider.evaluate(request)
    except EvaluationProviderSchemaError as error:
        _complete_failure(
            run,
            status="invalid_schema",
            schema_attempts=error.schema_attempts,
            latency_ms=error.latency_ms,
            input_tokens=error.input_tokens,
            output_tokens=error.output_tokens,
            cost_usd=provider.cost(
                input_tokens=error.input_tokens, output_tokens=error.output_tokens
            ),
            error_code="invalid_schema",
        )
        await database.commit()
        raise _stored_run_error(run) from error
    except EvaluationProviderTransportError as error:
        _complete_failure(
            run,
            status="retryable_failure",
            schema_attempts=0,
            latency_ms=0,
            input_tokens=0,
            output_tokens=0,
            cost_usd=Decimal("0"),
            error_code=error.code,
        )
        await database.commit()
        raise _stored_run_error(run) from error
    except EvaluationProviderPermanentError as error:
        _complete_failure(
            run,
            status="permanent_failure",
            schema_attempts=0,
            latency_ms=0,
            input_tokens=0,
            output_tokens=0,
            cost_usd=Decimal("0"),
            error_code=error.code,
        )
        await database.commit()
        raise _stored_run_error(run) from error
    return await _persist_result(
        run=run, result=result, rubric=rubric, problem=problem, database=database
    )


async def evaluation_state(
    *, attempt_id: uuid.UUID, user: User, database: AsyncSession
) -> EvaluationStateResponse:
    await owned_attempt(attempt_id, user, database)
    run = await database.scalar(
        select(EvaluationRun)
        .where(EvaluationRun.attempt_id == attempt_id)
        .order_by(EvaluationRun.started_at.desc(), EvaluationRun.id.desc())
    )
    if run is None:
        return EvaluationNotStartedState(state="not_started")
    prompt = await database.get(PromptVersion, run.prompt_version_id)
    if prompt is None:
        raise RuntimeError("Evaluation run lost its immutable prompt")
    if run.status == "processing":
        return EvaluationProcessingState(state="processing", run=_run_response(run, prompt))
    response = await _response_for_run(run, database)
    if isinstance(response, ReadyEvaluationResponse):
        return EvaluationReadyState(state="ready", result=response)
    if isinstance(response, UncertainEvaluationResponse):
        return EvaluationUncertainState(state="uncertain", result=response)
    return EvaluationFailureState(
        state=cast(Literal["retryable_failure", "permanent_failure", "invalid_schema"], run.status),
        run=_run_response(run, prompt),
    )


def _action_ids(action: GeometryAction) -> tuple[set[str], set[str]]:
    if isinstance(action, AnimateAction):
        return {action.object_id}, {action.animation_id}
    if isinstance(action, AskSelectAction):
        return set(action.allowed_object_ids) | set(action.correct_object_ids or []), set()
    return set(action.object_ids or []), set()


def validate_geometry_actions_against_scene(
    actions: list[GeometryAction], scene: GeometrySceneVersionSchema
) -> None:
    objects = {item.id: item for item in scene.objects}
    animation_ids = set(scene.animation_ids)
    point_like = {"point", "midpoint", "intersection"}
    for action in actions:
        referenced_objects, referenced_animations = _action_ids(action)
        if not referenced_objects <= set(objects) or not referenced_animations <= animation_ids:
            raise ValueError("A hint action references unknown curated geometry IDs")
        if isinstance(action, AnimateAction) and objects[action.object_id].type not in point_like:
            raise ValueError("A hint animation target must be a curated point-like object")
        if isinstance(action, AskSelectAction):
            if any(not objects[object_id].selectable for object_id in action.allowed_object_ids):
                raise ValueError("A hint selection action must use selectable curated objects")
            if not set(action.correct_object_ids or []) <= set(action.allowed_object_ids):
                raise ValueError("Correct selection IDs must be part of the allowed finite set")


async def _validated_hint(
    *, hint: ProblemHint, problem: ProblemVersion, database: AsyncSession
) -> tuple[list[ContentBlock], list[GeometryAction]]:
    content = blocks_adapter.validate_python(hint.content_json)
    actions = actions_adapter.validate_python(hint.geometry_actions_json)
    if not actions:
        return content, actions
    if problem.geometry_scene_version_id is None:
        raise RuntimeError("A geometry hint requires an immutable geometry scene")
    row = await database.get(GeometrySceneVersion, problem.geometry_scene_version_id)
    if row is None:
        raise RuntimeError("A geometry hint references a missing geometry scene")
    scene = scene_adapter.validate_python(row.scene_json)
    try:
        validate_geometry_actions_against_scene(actions, scene)
    except ValueError as error:
        raise RuntimeError("A stored hint failed curated geometry action validation") from error
    return content, actions


async def next_hint(
    *,
    attempt_id: uuid.UUID,
    payload: NextHintRequest,
    user: User,
    database: AsyncSession,
) -> NextHintResponse:
    attempt = await owned_attempt(attempt_id, user, database)
    await database.execute(select(Attempt.id).where(Attempt.id == attempt.id).with_for_update())
    existing = await database.scalar(
        select(HintEvent).where(HintEvent.idempotency_key == payload.idempotency_key)
    )
    if existing is not None:
        if existing.attempt_id != attempt.id:
            raise AppError(
                status_code=409,
                code="hint_idempotency_conflict",
                message="Use a new hint request identifier.",
            )
        hint = await database.get(ProblemHint, existing.hint_id)
        problem = await database.get(ProblemVersion, attempt.problem_version_id)
        if hint is None or problem is None:
            raise RuntimeError("Released hint lost immutable content")
        content, actions = await _validated_hint(hint=hint, problem=problem, database=database)
        concept_version_id = None
        if hint.concept_id is not None:
            concept_version_id = await database.scalar(
                select(Concept.current_version_id).where(
                    Concept.id == hint.concept_id, Concept.status == "synthetic"
                )
            )
        return NextHintResponse(
            hint_event_id=existing.id,
            evaluation_id=existing.evaluation_id,
            hint_id=hint.id,
            hint_level=hint.hint_level,
            content=content,
            geometry_actions=actions,
            reveals_complete_solution=hint.reveals_complete_solution,
            concept_version_id=concept_version_id,
            released_at=existing.released_at,
        )
    evaluation = await database.scalar(
        select(Evaluation)
        .join(EvaluationRun, EvaluationRun.id == Evaluation.evaluation_run_id)
        .join(
            TranscriptConfirmation,
            (TranscriptConfirmation.attempt_id == EvaluationRun.attempt_id)
            & (
                TranscriptConfirmation.transcript_version_id
                == EvaluationRun.confirmed_transcript_version_id
            ),
        )
        .where(EvaluationRun.attempt_id == attempt.id)
        .order_by(Evaluation.created_at.desc(), Evaluation.id.desc())
    )
    if evaluation is None:
        raise AppError(
            status_code=409,
            code="evaluation_required",
            message="Request an evaluation before revealing a hint.",
        )
    highest = await database.scalar(
        select(func.max(HintEvent.hint_level)).where(HintEvent.attempt_id == attempt.id)
    )
    next_level = (highest or 0) + 1
    hint = await database.scalar(
        select(ProblemHint).where(
            ProblemHint.problem_version_id == attempt.problem_version_id,
            ProblemHint.hint_level == next_level,
        )
    )
    if hint is None:
        raise AppError(
            status_code=409,
            code="hint_ladder_exhausted",
            message="No further curated hint is available.",
        )
    problem = await database.get(ProblemVersion, attempt.problem_version_id)
    if problem is None:
        raise RuntimeError("Attempt lost immutable problem content")
    content, actions = await _validated_hint(hint=hint, problem=problem, database=database)
    concept_version_id = None
    if hint.concept_id is not None:
        concept_version_id = await database.scalar(
            select(Concept.current_version_id).where(
                Concept.id == hint.concept_id, Concept.status == "synthetic"
            )
        )
    event = HintEvent(
        attempt_id=attempt.id,
        evaluation_id=evaluation.id,
        hint_id=hint.id,
        hint_level=hint.hint_level,
        idempotency_key=payload.idempotency_key,
    )
    database.add(event)
    try:
        await database.commit()
    except IntegrityError as error:
        await database.rollback()
        raise AppError(
            status_code=409,
            code="hint_release_conflict",
            message="Another hint request was completed first. Refresh and try again.",
        ) from error
    return NextHintResponse(
        hint_event_id=event.id,
        evaluation_id=event.evaluation_id,
        hint_id=hint.id,
        hint_level=hint.hint_level,
        content=content,
        geometry_actions=actions,
        reveals_complete_solution=hint.reveals_complete_solution,
        concept_version_id=concept_version_id,
        released_at=event.released_at,
    )
