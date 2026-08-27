import uuid
from datetime import date
from typing import cast

from pydantic import TypeAdapter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.attempts import owned_attempt
from app.content.models import (
    Concept,
    ConceptVersion,
    Exam,
    ExamCycle,
    GeometrySceneVersion,
    Problem,
    ProblemHint,
)
from app.content.preview import content_preview
from app.content.schemas import ContentBlock, GeometryAction
from app.content.schemas import GeometrySceneVersion as GeometrySceneVersionSchema
from app.errors import AppError
from app.models import User
from app.profile_models import StudentExamTarget
from app.profiles import owned_active_profile
from app.static_journey.mocks import (
    DeterministicMockBoundary,
    MockPayloadInvalidError,
    MockSourceError,
)
from app.static_journey.planning import (
    FOLLOW_UP_PROBLEM_CODE,
    PRIMARY_PROBLEM_CODE,
    PlanProblemInput,
    PlanTargetInput,
    build_static_daily_plan,
)
from app.static_journey.schemas import (
    AvailableExamCycleListResponse,
    AvailableExamCycleResponse,
    ConceptVersionResponse,
    MockEvaluationRequest,
    MockEvaluationResponse,
    NextHintRequest,
    NextHintResponse,
    StaticDailyPlanResponse,
)
from app.transcription.models import TranscriptConfirmation, TranscriptVersion
from app.transcription.schemas import TranscriptDocument, canonical_transcript_hash

CONCEPT_CODE = "SYN-MIDPOINT-COORDINATES"
blocks_adapter = TypeAdapter(list[ContentBlock])
actions_adapter = TypeAdapter(list[GeometryAction])
scene_adapter = TypeAdapter(GeometrySceneVersionSchema)


def _mock_source_failure(error: MockSourceError) -> AppError:
    if error.retryable:
        return AppError(
            status_code=503,
            code="mock_temporarily_unavailable",
            message="The synthetic mock is temporarily unavailable. Try again.",
        )
    return AppError(
        status_code=502,
        code="mock_permanent_failure",
        message="The synthetic mock could not complete this operation.",
    )


async def available_exam_cycles(database: AsyncSession) -> AvailableExamCycleListResponse:
    rows = (
        await database.execute(
            select(ExamCycle, Exam)
            .join(Exam, Exam.id == ExamCycle.exam_id)
            .where(ExamCycle.status == "synthetic", Exam.status == "synthetic")
            .order_by(Exam.code, ExamCycle.exam_date, ExamCycle.cycle_code)
        )
    ).all()
    return AvailableExamCycleListResponse(
        items=[
            AvailableExamCycleResponse(
                id=cast(ExamCycle, row[0]).id,
                exam_id=cast(Exam, row[1]).id,
                exam_code=cast(Exam, row[1]).code,
                exam_name=cast(Exam, row[1]).name,
                cycle_code=cast(ExamCycle, row[0]).cycle_code,
                year=cast(ExamCycle, row[0]).year,
                exam_date=cast(ExamCycle, row[0]).exam_date,
            )
            for row in rows
        ]
    )


async def static_daily_plan(
    user: User,
    database: AsyncSession,
    plan_date: date,
) -> StaticDailyPlanResponse:
    profile = await owned_active_profile(user, database)
    target_rows = (
        await database.execute(
            select(StudentExamTarget, ExamCycle, Exam)
            .join(ExamCycle, ExamCycle.id == StudentExamTarget.exam_cycle_id)
            .join(Exam, Exam.id == ExamCycle.exam_id)
            .where(
                StudentExamTarget.study_profile_id == profile.id,
                StudentExamTarget.status == "active",
                ExamCycle.status == "synthetic",
                Exam.status == "synthetic",
            )
            .order_by(StudentExamTarget.priority_rank, StudentExamTarget.id)
        )
    ).all()
    targets = [
        PlanTargetInput(
            target_id=cast(StudentExamTarget, row[0]).id,
            exam_cycle_id=cast(ExamCycle, row[1]).id,
            exam_name=cast(Exam, row[2]).name,
            cycle_code=cast(ExamCycle, row[1]).cycle_code,
            priority_rank=cast(StudentExamTarget, row[0]).priority_rank,
        )
        for row in target_rows
    ]
    if len(targets) < 2:
        raise AppError(
            status_code=409,
            code="two_active_targets_required",
            message="Add at least two active examination targets before planning.",
        )

    stored_problems = list(
        await database.scalars(
            select(Problem)
            .where(
                Problem.external_code.in_([PRIMARY_PROBLEM_CODE, FOLLOW_UP_PROBLEM_CODE]),
                Problem.status == "synthetic",
            )
            .order_by(Problem.external_code)
        )
    )
    problems: list[PlanProblemInput] = []
    for problem in stored_problems:
        preview = await content_preview(problem.id, database)
        problems.append(
            PlanProblemInput(
                problem_id=preview.problem_id,
                problem_version_id=preview.problem_version_id,
                external_code=preview.external_code,
                version=preview.version,
                estimated_minutes=preview.estimated_minutes,
                statement=list(preview.statement),
                geometry_scene=preview.geometry_scene,
                relevant_cycle_ids=tuple(
                    supported.exam_cycle_id for supported in preview.supported_exams
                ),
            )
        )

    concept_version_id = await database.scalar(
        select(Concept.current_version_id).where(
            Concept.code == CONCEPT_CODE,
            Concept.status == "synthetic",
        )
    )
    if concept_version_id is None:
        raise AppError(
            status_code=503,
            code="static_plan_unavailable",
            message="The static plan is temporarily unavailable.",
        )
    return build_static_daily_plan(
        profile_id=profile.id,
        plan_date=plan_date,
        targets=targets,
        problems=problems,
        concept_version_id=concept_version_id,
    )


async def mock_evaluation(
    *,
    attempt_id: uuid.UUID,
    payload: MockEvaluationRequest,
    user: User,
    database: AsyncSession,
    boundary: DeterministicMockBoundary,
) -> MockEvaluationResponse:
    await owned_attempt(attempt_id, user, database)
    confirmation = await database.scalar(
        select(TranscriptConfirmation).where(
            TranscriptConfirmation.attempt_id == attempt_id,
            TranscriptConfirmation.transcript_version_id == payload.confirmed_transcript_version_id,
        )
    )
    if confirmation is None:
        raise AppError(
            status_code=409,
            code="transcript_not_confirmed",
            message="Confirm this exact transcript version before evaluation.",
        )
    version = await database.get(TranscriptVersion, confirmation.transcript_version_id)
    if version is None or version.attempt_id != attempt_id:
        raise RuntimeError("Confirmed transcript relationship is invalid")
    transcript = TranscriptDocument.model_validate(version.document_json)
    if (
        transcript.attempt_id != attempt_id
        or canonical_transcript_hash(transcript) != confirmation.transcript_sha256
        or version.transcript_sha256 != confirmation.transcript_sha256
    ):
        raise RuntimeError("Confirmed transcript identity is invalid")
    try:
        return boundary.evaluate(transcript)
    except MockSourceError as error:
        raise _mock_source_failure(error) from error
    except MockPayloadInvalidError as error:
        raise AppError(
            status_code=502,
            code="mock_payload_invalid",
            message="The synthetic evaluation was invalid after one retry.",
        ) from error


async def next_hint(
    *,
    attempt_id: uuid.UUID,
    payload: NextHintRequest,
    user: User,
    database: AsyncSession,
) -> NextHintResponse:
    attempt = await owned_attempt(attempt_id, user, database)
    hint = await database.scalar(
        select(ProblemHint).where(
            ProblemHint.problem_version_id == attempt.problem_version_id,
            ProblemHint.hint_level == payload.previous_hint_level + 1,
        )
    )
    if hint is None:
        raise AppError(
            status_code=409,
            code="hint_ladder_exhausted",
            message="No further curated hint is available.",
        )
    concept_version_id = None
    if hint.concept_id is not None:
        concept_version_id = await database.scalar(
            select(Concept.current_version_id).where(
                Concept.id == hint.concept_id,
                Concept.status == "synthetic",
            )
        )
    return NextHintResponse(
        hint_id=hint.id,
        hint_level=hint.hint_level,
        content=blocks_adapter.validate_python(hint.content_json),
        geometry_actions=actions_adapter.validate_python(hint.geometry_actions_json),
        reveals_complete_solution=hint.reveals_complete_solution,
        concept_version_id=concept_version_id,
    )


async def concept_version(
    concept_version_id: uuid.UUID,
    database: AsyncSession,
) -> ConceptVersionResponse:
    row = (
        await database.execute(
            select(Concept, ConceptVersion)
            .join(ConceptVersion, ConceptVersion.concept_id == Concept.id)
            .where(
                ConceptVersion.id == concept_version_id,
                Concept.status == "synthetic",
            )
        )
    ).one_or_none()
    if row is None:
        raise AppError(
            status_code=404,
            code="concept_version_not_found",
            message="Concept version not found.",
        )
    concept = cast(Concept, row[0])
    version = cast(ConceptVersion, row[1])
    scene = None
    if version.geometry_scene_version_id is not None:
        stored_scene = await database.get(GeometrySceneVersion, version.geometry_scene_version_id)
        if stored_scene is None:
            raise RuntimeError("Stored concept version references a missing geometry scene")
        scene = scene_adapter.validate_python(stored_scene.scene_json)
    return ConceptVersionResponse(
        concept_id=concept.id,
        concept_version_id=version.id,
        code=concept.code,
        name=concept.name,
        version=version.version,
        content=blocks_adapter.validate_python(version.content_json),
        geometry_scene=scene,
    )
