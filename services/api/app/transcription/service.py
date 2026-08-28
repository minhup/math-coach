import hashlib
import json
import uuid
from datetime import timedelta
from decimal import Decimal
from functools import lru_cache
from time import perf_counter
from typing import Literal, cast

from minio.error import S3Error
from pydantic import SecretStr, ValidationError
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.attempt_models import Attempt
from app.attempts import owned_attempt
from app.config import Settings, get_settings
from app.content.models import ProblemVersion
from app.errors import AppError
from app.models import SolutionUpload, User
from app.security import utc_now
from app.storage import ObjectNotFoundError, ObjectStorage
from app.transcription.anthropic_provider import AnthropicTranscriptionProvider
from app.transcription.fake_provider import DeterministicFakeTranscriptionProvider
from app.transcription.gemini_provider import GeminiTranscriptionProvider
from app.transcription.models import (
    AIModelRun,
    AttemptAsset,
    PromptVersion,
    TranscriptConfirmation,
    TranscriptVersion,
)
from app.transcription.openai_provider import OpenAITranscriptionProvider
from app.transcription.prompt import (
    PROMPT_HASH,
    PROMPT_TEXT,
    PROMPT_VERSION,
    PROVIDER_SCHEMA_VERSION,
)
from app.transcription.provider import (
    ProviderPermanentError,
    ProviderRequest,
    ProviderResult,
    ProviderSchemaError,
    ProviderTransportError,
    StrictTranscriptionProvider,
)
from app.transcription.schemas import (
    ReadyTranscriptionResponse,
    TranscribeRequest,
    TranscriptConfirmationResponse,
    TranscriptConfirmRequest,
    TranscriptDocument,
    TranscriptionFailureState,
    TranscriptionNotStartedState,
    TranscriptionProcessingState,
    TranscriptionReadyState,
    TranscriptionResponse,
    TranscriptionRunResponse,
    TranscriptionStateResponse,
    TranscriptionUncertainState,
    TranscriptVersionCreateRequest,
    TranscriptVersionResponse,
    TranscriptWarning,
    UncertainTranscriptionResponse,
    UploadDownloadResponse,
    canonical_transcript_hash,
)
from app.uploads import allowed_image_type, owned_upload

PROMPT_VERSION_ID = uuid.UUID("60000000-0000-4000-8000-000000000100")


@lru_cache
def get_transcription_provider() -> StrictTranscriptionProvider:
    settings = get_settings()
    if settings.transcription_provider == "fake":
        return DeterministicFakeTranscriptionProvider()
    if settings.transcription_provider == "gemini":
        key = _required_key(settings.gemini_api_key)
        return GeminiTranscriptionProvider(
            api_key=key,
            model_snapshot=settings.transcription_model_snapshot,
            timeout_seconds=settings.transcription_timeout_seconds,
        )
    if settings.transcription_provider == "openai":
        key = _required_key(settings.openai_api_key)
        return OpenAITranscriptionProvider(
            api_key=key,
            timeout_seconds=settings.transcription_timeout_seconds,
        )
    key = _required_key(settings.anthropic_api_key)
    return AnthropicTranscriptionProvider(
        api_key=key,
        timeout_seconds=settings.transcription_timeout_seconds,
    )


def _required_key(value: SecretStr | None) -> str:
    if value is None:
        raise RuntimeError("Configured transcription provider has no server API key")
    return value.get_secret_value()


def _request_fingerprint(
    *,
    attempt_id: uuid.UUID,
    attempt_asset_id: uuid.UUID,
    provider: StrictTranscriptionProvider,
) -> str:
    identity = provider.identity
    source = ":".join(
        (
            str(attempt_id),
            str(attempt_asset_id),
            identity.provider,
            identity.model_snapshot,
            identity.prompt_hash,
            identity.schema_version,
        )
    )
    return hashlib.sha256(source.encode()).hexdigest()


def _detected_content_type(image: bytes) -> Literal["image/jpeg", "image/png", "image/webp"]:
    if image.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if image.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if len(image) >= 12 and image.startswith(b"RIFF") and image[8:12] == b"WEBP":
        return "image/webp"
    raise ProviderPermanentError("invalid_media")


async def _prompt_version(database: AsyncSession) -> PromptVersion:
    await database.execute(
        pg_insert(PromptVersion)
        .values(
            id=PROMPT_VERSION_ID,
            operation="transcription",
            version=PROMPT_VERSION,
            prompt_text=PROMPT_TEXT,
            prompt_sha256=PROMPT_HASH,
            schema_version=PROVIDER_SCHEMA_VERSION,
        )
        .on_conflict_do_nothing(index_elements=[PromptVersion.id])
    )
    stored = await database.get(PromptVersion, PROMPT_VERSION_ID)
    if stored is None:
        raise RuntimeError("Transcription prompt version could not be persisted")
    if (
        stored.operation != "transcription"
        or stored.version != PROMPT_VERSION
        or stored.prompt_text != PROMPT_TEXT
        or stored.prompt_sha256 != PROMPT_HASH
        or stored.schema_version != PROVIDER_SCHEMA_VERSION
    ):
        raise RuntimeError("Stored transcription prompt identity does not match application code")
    return stored


def _run_response(run: AIModelRun, prompt: PromptVersion) -> TranscriptionRunResponse:
    return TranscriptionRunResponse(
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
        latency_ms=run.latency_ms,
        input_tokens=run.input_tokens,
        output_tokens=run.output_tokens,
        cost_usd=run.cost_usd,
        error_code=run.error_code,
        started_at=run.started_at,
        completed_at=run.completed_at,
    )


def _stored_document(version: TranscriptVersion) -> TranscriptDocument:
    try:
        document = TranscriptDocument.model_validate(version.document_json)
    except ValidationError as error:
        raise RuntimeError("Stored transcript failed its authoritative schema") from error
    if document.attempt_id != version.attempt_id:
        raise RuntimeError("Stored transcript attempt relationship is invalid")
    if canonical_transcript_hash(document) != version.transcript_sha256:
        raise RuntimeError("Stored transcript hash is invalid")
    return document


def _version_response(version: TranscriptVersion) -> TranscriptVersionResponse:
    return TranscriptVersionResponse(
        id=version.id,
        attempt_id=version.attempt_id,
        source_run_id=version.source_model_run_id,
        parent_transcript_version_id=version.parent_transcript_version_id,
        version=version.version,
        transcript_hash=version.transcript_sha256,
        origin=cast(Literal["provider", "learner"], version.origin),
        document=_stored_document(version),
        created_at=version.created_at,
    )


def _confirmation_response(
    confirmation: TranscriptConfirmation,
) -> TranscriptConfirmationResponse:
    return TranscriptConfirmationResponse(
        id=confirmation.id,
        attempt_id=confirmation.attempt_id,
        transcript_version_id=confirmation.transcript_version_id,
        transcript_hash=confirmation.transcript_sha256,
        confirmed_at=confirmation.confirmed_at,
    )


def _stored_warnings(run: AIModelRun) -> list[TranscriptWarning]:
    if run.result_json is None:
        return []
    value = run.result_json.get("warnings")
    if not isinstance(value, list):
        raise RuntimeError("Stored transcription warning data is invalid")
    try:
        return [TranscriptWarning.model_validate(item) for item in value]
    except ValidationError as error:
        raise RuntimeError("Stored transcription warning data is invalid") from error


async def _response_for_run(
    run: AIModelRun,
    database: AsyncSession,
) -> TranscriptionResponse:
    prompt = await database.get(PromptVersion, run.prompt_version_id)
    if prompt is None:
        raise RuntimeError("Transcription run has no prompt version")
    response = _run_response(run, prompt)
    if run.status == "succeeded":
        version = await database.scalar(
            select(TranscriptVersion)
            .where(TranscriptVersion.source_model_run_id == run.id)
            .order_by(TranscriptVersion.version.desc())
        )
        if version is None:
            raise RuntimeError("Successful transcription has no transcript version")
        return ReadyTranscriptionResponse(
            outcome="ready",
            run=response,
            transcript_version=_version_response(version),
        )
    if run.status == "uncertain":
        return UncertainTranscriptionResponse(
            outcome="uncertain",
            run=response,
            warnings=_stored_warnings(run),
        )
    raise _stored_run_error(run)


def _stored_run_error(run: AIModelRun) -> AppError:
    messages = {
        "timeout": "Transcription timed out. Try again.",
        "rate_limited": "Transcription is busy right now. Try again.",
        "transport_failed": "Transcription is temporarily unavailable. Try again.",
        "invalid_media": "The uploaded image could not be transcribed.",
        "provider_rejected": "The transcription service rejected this image.",
        "invalid_schema": "The transcription response was invalid after one retry.",
    }
    code = run.error_code or "transport_failed"
    if run.status == "retryable_failure":
        status_code = 503
    elif run.status == "permanent_failure":
        status_code = 422 if code == "invalid_media" else 502
    else:
        status_code = 502
    return AppError(
        status_code=status_code,
        code=f"transcription_{code}",
        message=messages.get(code, "Transcription could not be completed."),
    )


async def _attempt_asset(
    *,
    attempt: Attempt,
    upload: SolutionUpload,
    content_hash: str,
    database: AsyncSession,
) -> AttemptAsset:
    asset = await database.scalar(
        select(AttemptAsset).where(
            AttemptAsset.attempt_id == attempt.id,
            AttemptAsset.solution_upload_id == upload.id,
        )
    )
    if asset is not None:
        if asset.content_sha256 != content_hash:
            raise AppError(
                status_code=409,
                code="upload_content_changed",
                message="The verified image changed. Upload it again.",
            )
        return asset
    asset = AttemptAsset(
        attempt_id=attempt.id,
        solution_upload_id=upload.id,
        content_sha256=content_hash,
    )
    database.add(asset)
    await database.flush()
    return asset


async def _load_verified_image(
    *,
    upload: SolutionUpload,
    storage: ObjectStorage,
    settings: Settings,
) -> bytes:
    try:
        image = await run_in_threadpool(
            storage.read,
            upload.object_key,
            settings.upload_max_bytes,
        )
    except ObjectNotFoundError as error:
        raise AppError(
            status_code=409,
            code="upload_not_received",
            message="The uploaded image is no longer available.",
        ) from error
    except (S3Error, ValueError) as error:
        raise AppError(
            status_code=503,
            code="storage_unavailable",
            message="Image storage is temporarily unavailable.",
        ) from error
    if len(image) != upload.verified_size_bytes:
        raise AppError(
            status_code=409,
            code="upload_content_changed",
            message="The verified image changed. Upload it again.",
        )
    return image


def _complete_run(
    run: AIModelRun,
    *,
    status: Literal[
        "succeeded",
        "uncertain",
        "retryable_failure",
        "permanent_failure",
        "invalid_schema",
    ],
    schema_attempts: int,
    latency_ms: int,
    input_tokens: int,
    output_tokens: int,
    cost_usd: Decimal,
    error_code: str | None = None,
    warnings: tuple[TranscriptWarning, ...] = (),
) -> None:
    run.status = status
    run.schema_attempts = schema_attempts
    run.latency_ms = latency_ms
    run.input_tokens = input_tokens
    run.output_tokens = output_tokens
    run.cost_usd = cost_usd
    run.error_code = error_code
    run.result_json = (
        None
        if not warnings
        else {
            "warnings": [
                warning.model_dump(by_alias=True, exclude_none=True, mode="json")
                for warning in warnings
            ]
        }
    )
    run.completed_at = utc_now()


async def transcribe_attempt(
    *,
    attempt_id: uuid.UUID,
    payload: TranscribeRequest,
    user: User,
    database: AsyncSession,
    storage: ObjectStorage,
    settings: Settings,
    provider: StrictTranscriptionProvider,
) -> TranscriptionResponse:
    attempt = await owned_attempt(attempt_id, user, database)
    upload = await owned_upload(payload.upload_id, user, database)
    if (
        upload.status != "ready"
        or upload.verified_size_bytes is None
        or upload.verified_content_type is None
    ):
        raise AppError(
            status_code=409,
            code="upload_not_ready",
            message="Finish the image upload before transcription.",
        )

    # Serialize creation of the attempt/upload link; provider work begins only after this
    # transaction commits, so the lock never spans a paid network call.
    await database.execute(select(Attempt.id).where(Attempt.id == attempt.id).with_for_update())

    existing = await database.scalar(
        select(AIModelRun)
        .join(AttemptAsset, AttemptAsset.id == AIModelRun.attempt_asset_id)
        .where(AIModelRun.idempotency_key == payload.idempotency_key)
    )
    if existing is not None:
        asset = await database.get(AttemptAsset, existing.attempt_asset_id)
        if asset is None or asset.attempt_id != attempt.id or asset.solution_upload_id != upload.id:
            raise AppError(
                status_code=409,
                code="transcription_idempotency_conflict",
                message="Use a new transcription request identifier.",
            )
        if existing.status == "processing":
            raise AppError(
                status_code=409,
                code="transcription_in_progress",
                message="Transcription is already in progress.",
            )
        return await _response_for_run(existing, database)

    image = await _load_verified_image(upload=upload, storage=storage, settings=settings)
    content_hash = hashlib.sha256(image).hexdigest()
    asset = await _attempt_asset(
        attempt=attempt,
        upload=upload,
        content_hash=content_hash,
        database=database,
    )
    prompt = await _prompt_version(database)
    completed = await database.scalar(
        select(AIModelRun)
        .where(
            AIModelRun.attempt_asset_id == asset.id,
            AIModelRun.request_fingerprint
            == _request_fingerprint(
                attempt_id=attempt.id,
                attempt_asset_id=asset.id,
                provider=provider,
            ),
            AIModelRun.status.in_(
                ("succeeded", "uncertain", "permanent_failure", "invalid_schema")
            ),
        )
        .order_by(AIModelRun.started_at.desc(), AIModelRun.id.desc())
    )
    if completed is not None:
        return await _response_for_run(completed, database)
    run = AIModelRun(
        attempt_asset_id=asset.id,
        prompt_version_id=prompt.id,
        provider=provider.identity.provider,
        model_snapshot=provider.identity.model_snapshot,
        schema_version=provider.identity.schema_version,
        pricing_version=provider.identity.pricing_version,
        idempotency_key=payload.idempotency_key,
        request_fingerprint=_request_fingerprint(
            attempt_id=attempt.id,
            attempt_asset_id=asset.id,
            provider=provider,
        ),
        status="processing",
        schema_attempts=0,
    )
    database.add(run)
    try:
        await database.commit()
    except IntegrityError as error:
        await database.rollback()
        raise AppError(
            status_code=409,
            code="transcription_in_progress",
            message="Transcription is already in progress.",
        ) from error

    started = perf_counter()
    try:
        detected_type = _detected_content_type(image)
        expected_type = allowed_image_type(upload.verified_content_type)
        if detected_type != expected_type:
            raise ProviderPermanentError("invalid_media")
        problem_context_value = await database.scalar(
            select(ProblemVersion.statement_json).where(
                ProblemVersion.id == attempt.problem_version_id
            )
        )
        if problem_context_value is None:
            raise RuntimeError("Attempt lost its immutable problem version")
        result = await provider.transcribe(
            ProviderRequest(
                attempt_id=attempt.id,
                attempt_asset_id=asset.id,
                content_type=detected_type,
                image_bytes=image,
                problem_context=json.dumps(problem_context_value, ensure_ascii=False),
            )
        )
    except ProviderSchemaError as error:
        _complete_run(
            run,
            status="invalid_schema",
            schema_attempts=error.schema_attempts,
            latency_ms=error.latency_ms,
            input_tokens=error.input_tokens,
            output_tokens=error.output_tokens,
            cost_usd=provider.cost(
                input_tokens=error.input_tokens,
                output_tokens=error.output_tokens,
            ),
            error_code="invalid_schema",
        )
        await database.commit()
        raise _stored_run_error(run) from error
    except ProviderTransportError as error:
        _complete_run(
            run,
            status="retryable_failure",
            schema_attempts=0,
            latency_ms=max(0, round((perf_counter() - started) * 1000)),
            input_tokens=0,
            output_tokens=0,
            cost_usd=provider.cost(input_tokens=0, output_tokens=0),
            error_code=error.code,
        )
        await database.commit()
        raise _stored_run_error(run) from error
    except ProviderPermanentError as error:
        _complete_run(
            run,
            status="permanent_failure",
            schema_attempts=0,
            latency_ms=max(0, round((perf_counter() - started) * 1000)),
            input_tokens=0,
            output_tokens=0,
            cost_usd=provider.cost(input_tokens=0, output_tokens=0),
            error_code=error.code,
        )
        await database.commit()
        raise _stored_run_error(run) from error

    _record_provider_result(run, result, provider)
    if result.outcome == "uncertain":
        await database.commit()
        return UncertainTranscriptionResponse(
            outcome="uncertain",
            run=_run_response(run, prompt),
            warnings=list(result.warnings),
        )
    if result.transcript is None:
        raise RuntimeError("Ready provider result has no transcript")
    latest = await database.scalar(
        select(TranscriptVersion)
        .where(TranscriptVersion.attempt_id == attempt.id)
        .order_by(TranscriptVersion.version.desc())
    )
    version = TranscriptVersion(
        attempt_id=attempt.id,
        source_model_run_id=run.id,
        parent_transcript_version_id=None if latest is None else latest.id,
        version=1 if latest is None else latest.version + 1,
        schema_version=result.transcript.schema_version,
        document_json=result.transcript.model_dump(by_alias=True, exclude_none=True, mode="json"),
        transcript_sha256=canonical_transcript_hash(result.transcript),
        origin="provider",
        created_by_user_id=None,
    )
    database.add(version)
    await database.commit()
    return ReadyTranscriptionResponse(
        outcome="ready",
        run=_run_response(run, prompt),
        transcript_version=_version_response(version),
    )


def _record_provider_result(
    run: AIModelRun,
    result: ProviderResult,
    provider: StrictTranscriptionProvider,
) -> None:
    if result.identity != provider.identity or (
        run.provider,
        run.model_snapshot,
        run.schema_version,
        run.pricing_version,
    ) != (
        provider.identity.provider,
        provider.identity.model_snapshot,
        provider.identity.schema_version,
        provider.identity.pricing_version,
    ):
        raise RuntimeError("Provider returned metadata outside its configured identity")
    _complete_run(
        run,
        status="succeeded" if result.outcome == "ready" else "uncertain",
        schema_attempts=result.schema_attempts,
        latency_ms=result.latency_ms,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        cost_usd=result.cost_usd,
        warnings=result.warnings,
    )


def _valid_learner_revision(base: TranscriptDocument, edited: TranscriptDocument) -> bool:
    if base.attempt_id != edited.attempt_id:
        return False
    base_blocks = {block.id: block for block in base.blocks}
    for block in edited.blocks:
        original = base_blocks.get(block.id)
        if original is None:
            if block.source_region is not None:
                return False
        elif original.type != block.type or original.source_region != block.source_region:
            return False
    base_warnings = {(warning.code, warning.message, warning.block_id) for warning in base.warnings}
    return not any(
        (warning.code, warning.message, warning.block_id) not in base_warnings
        for warning in edited.warnings
    )


async def create_transcript_version(
    *,
    attempt_id: uuid.UUID,
    payload: TranscriptVersionCreateRequest,
    user: User,
    database: AsyncSession,
) -> TranscriptVersionResponse:
    attempt = await owned_attempt(attempt_id, user, database)
    await database.execute(select(Attempt.id).where(Attempt.id == attempt.id).with_for_update())
    confirmation = await database.scalar(
        select(TranscriptConfirmation).where(TranscriptConfirmation.attempt_id == attempt_id)
    )
    if confirmation is not None:
        raise AppError(
            status_code=409,
            code="transcript_confirmed_locked",
            message="The confirmed transcript is locked.",
        )
    base = await database.scalar(
        select(TranscriptVersion).where(
            TranscriptVersion.id == payload.base_transcript_version_id,
            TranscriptVersion.attempt_id == attempt_id,
        )
    )
    if base is None:
        raise AppError(
            status_code=404,
            code="transcript_version_not_found",
            message="Transcript version not found.",
        )
    base_document = _stored_document(base)
    if not _valid_learner_revision(base_document, payload.document):
        raise AppError(
            status_code=422,
            code="transcript_structure_invalid",
            message="Only transcript text and mathematics can be corrected.",
        )
    transcript_hash = canonical_transcript_hash(payload.document)
    if transcript_hash == base.transcript_sha256:
        raise AppError(
            status_code=409,
            code="transcript_unchanged",
            message="Make a correction before saving a new version.",
        )
    existing_revision = await database.scalar(
        select(TranscriptVersion).where(
            TranscriptVersion.attempt_id == attempt_id,
            TranscriptVersion.transcript_sha256 == transcript_hash,
        )
    )
    if existing_revision is not None:
        if (
            existing_revision.parent_transcript_version_id == base.id
            and existing_revision.origin == "learner"
        ):
            return _version_response(existing_revision)
        raise AppError(
            status_code=409,
            code="transcript_version_conflict",
            message="Reload the latest transcript before saving.",
        )
    latest_version = await database.scalar(
        select(func.max(TranscriptVersion.version)).where(
            TranscriptVersion.attempt_id == attempt_id
        )
    )
    if base.version != latest_version:
        raise AppError(
            status_code=409,
            code="transcript_version_stale",
            message="Reload the latest transcript before saving.",
        )
    version = TranscriptVersion(
        attempt_id=attempt_id,
        source_model_run_id=base.source_model_run_id,
        parent_transcript_version_id=base.id,
        version=base.version + 1,
        schema_version=payload.document.schema_version,
        document_json=payload.document.model_dump(
            by_alias=True,
            exclude_none=True,
            mode="json",
        ),
        transcript_sha256=transcript_hash,
        origin="learner",
        created_by_user_id=user.id,
    )
    database.add(version)
    await database.commit()
    return _version_response(version)


async def confirm_transcript(
    *,
    attempt_id: uuid.UUID,
    payload: TranscriptConfirmRequest,
    user: User,
    database: AsyncSession,
) -> TranscriptConfirmationResponse:
    attempt = await owned_attempt(attempt_id, user, database)
    await database.execute(select(Attempt.id).where(Attempt.id == attempt.id).with_for_update())
    existing = await database.scalar(
        select(TranscriptConfirmation).where(TranscriptConfirmation.attempt_id == attempt_id)
    )
    if existing is not None:
        if (
            existing.transcript_version_id == payload.transcript_version_id
            and existing.transcript_sha256 == payload.transcript_hash
        ):
            return _confirmation_response(existing)
        raise AppError(
            status_code=409,
            code="transcript_already_confirmed",
            message="This attempt already has a confirmed transcript.",
        )
    version = await database.scalar(
        select(TranscriptVersion).where(
            TranscriptVersion.id == payload.transcript_version_id,
            TranscriptVersion.attempt_id == attempt_id,
        )
    )
    if version is None:
        raise AppError(
            status_code=404,
            code="transcript_version_not_found",
            message="Transcript version not found.",
        )
    if version.transcript_sha256 != payload.transcript_hash:
        raise AppError(
            status_code=409,
            code="transcript_hash_mismatch",
            message="Reload the transcript before confirming it.",
        )
    confirmation = TranscriptConfirmation(
        attempt_id=attempt_id,
        transcript_version_id=version.id,
        transcript_sha256=version.transcript_sha256,
        confirmed_by_user_id=user.id,
    )
    database.add(confirmation)
    await database.commit()
    return _confirmation_response(confirmation)


async def transcription_state(
    *,
    attempt_id: uuid.UUID,
    user: User,
    database: AsyncSession,
) -> TranscriptionStateResponse:
    await owned_attempt(attempt_id, user, database)
    run = await database.scalar(
        select(AIModelRun)
        .join(AttemptAsset, AttemptAsset.id == AIModelRun.attempt_asset_id)
        .where(AttemptAsset.attempt_id == attempt_id)
        .order_by(AIModelRun.started_at.desc(), AIModelRun.id.desc())
    )
    if run is None:
        return TranscriptionNotStartedState(status="not_started")
    prompt = await database.get(PromptVersion, run.prompt_version_id)
    if prompt is None:
        raise RuntimeError("Transcription run has no prompt version")
    run_response = _run_response(run, prompt)
    if run.status == "processing":
        return TranscriptionProcessingState(status="processing", run=run_response)
    if run.status == "uncertain":
        return TranscriptionUncertainState(
            status="uncertain",
            run=run_response,
            warnings=_stored_warnings(run),
        )
    if run.status in {"retryable_failure", "permanent_failure", "invalid_schema"}:
        return TranscriptionFailureState(
            status=cast(
                Literal["retryable_failure", "permanent_failure", "invalid_schema"],
                run.status,
            ),
            run=run_response,
        )
    latest = await database.scalar(
        select(TranscriptVersion)
        .where(TranscriptVersion.attempt_id == attempt_id)
        .order_by(TranscriptVersion.version.desc())
    )
    if latest is None:
        raise RuntimeError("Successful transcription has no transcript version")
    confirmation = await database.scalar(
        select(TranscriptConfirmation).where(TranscriptConfirmation.attempt_id == attempt_id)
    )
    return TranscriptionReadyState(
        status="ready",
        run=run_response,
        transcript_version=_version_response(latest),
        confirmation=None if confirmation is None else _confirmation_response(confirmation),
    )


async def upload_download_url(
    *,
    upload_id: uuid.UUID,
    user: User,
    database: AsyncSession,
    storage: ObjectStorage,
    settings: Settings,
) -> UploadDownloadResponse:
    upload = await owned_upload(upload_id, user, database)
    if upload.status != "ready":
        raise AppError(
            status_code=409,
            code="upload_not_ready",
            message="Finish the image upload before viewing it.",
        )
    expires_at = utc_now() + timedelta(seconds=settings.upload_url_expiry_seconds)
    try:
        download_url = await run_in_threadpool(
            storage.presign_get,
            upload.object_key,
            settings.upload_url_expiry_seconds,
        )
    except S3Error as error:
        raise AppError(
            status_code=503,
            code="storage_unavailable",
            message="Image storage is temporarily unavailable.",
        ) from error
    return UploadDownloadResponse(
        upload_id=upload.id,
        download_url=download_url,
        expires_at=expires_at,
    )
