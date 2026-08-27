import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.attempts import attempt_response, create_attempt, owned_attempt
from app.auth import (
    CurrentUser,
    clear_session_cookie,
    create_session_from_invite,
    revoke_session,
    session_response,
    set_session_cookie,
    user_response,
)
from app.config import Settings, get_settings
from app.content.preview import content_preview, list_content_previews
from app.content.preview_schemas import ContentPreviewListResponse, ContentPreviewResponse
from app.database import get_database_session
from app.profiles import (
    archive_target,
    create_profile,
    create_target,
    get_profile,
    list_targets,
    patch_profile,
    patch_target,
)
from app.schemas import (
    AttemptCreateRequest,
    AttemptResponse,
    ErrorEnvelope,
    ExamTargetCreateRequest,
    ExamTargetListResponse,
    ExamTargetPatchRequest,
    ExamTargetResponse,
    HealthResponse,
    PilotLoginRequest,
    PresignUploadRequest,
    PresignUploadResponse,
    SessionResponse,
    StudyProfileCreateRequest,
    StudyProfilePatchRequest,
    StudyProfileResponse,
    UploadResponse,
    UserResponse,
)
from app.security import utc_now
from app.static_journey.mocks import DeterministicMockBoundary, get_mock_boundary
from app.static_journey.schemas import (
    AvailableExamCycleListResponse,
    ConceptVersionResponse,
    MockEvaluationRequest,
    MockEvaluationResponse,
    NextHintRequest,
    NextHintResponse,
    StaticDailyPlanResponse,
)
from app.static_journey.service import (
    available_exam_cycles,
    concept_version,
    mock_evaluation,
    next_hint,
    static_daily_plan,
)
from app.storage import ObjectStorage, get_object_storage
from app.transcription.provider import StrictTranscriptionProvider
from app.transcription.schemas import (
    TranscribeRequest,
    TranscriptConfirmationResponse,
    TranscriptConfirmRequest,
    TranscriptionResponse,
    TranscriptionStateResponse,
    TranscriptVersionCreateRequest,
    TranscriptVersionResponse,
    UploadDownloadResponse,
)
from app.transcription.service import (
    confirm_transcript,
    create_transcript_version,
    get_transcription_provider,
    transcribe_attempt,
    transcription_state,
    upload_download_url,
)
from app.uploads import complete_upload, create_upload, owned_upload, upload_response

error_responses: dict[int | str, dict[str, Any]] = {
    500: {"model": ErrorEnvelope, "description": "An unexpected server error occurred"},
    401: {"model": ErrorEnvelope, "description": "Authentication failed or is required"},
    404: {"model": ErrorEnvelope, "description": "Owned resource was not found"},
    409: {"model": ErrorEnvelope, "description": "Request conflicts with current state"},
    502: {"model": ErrorEnvelope, "description": "An upstream structured response was invalid"},
    422: {"model": ErrorEnvelope, "description": "Request or upload validation failed"},
    503: {"model": ErrorEnvelope, "description": "A required service is unavailable"},
}

router = APIRouter(prefix="/api/v1", responses=error_responses)


@router.get("/health", response_model=HealthResponse, tags=["system"])
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.post("/auth/pilot-login", response_model=SessionResponse, tags=["auth"])
async def pilot_login(
    payload: PilotLoginRequest,
    response: Response,
    database: Annotated[AsyncSession, Depends(get_database_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> SessionResponse:
    token, user, session = await create_session_from_invite(payload, database, settings)
    set_session_cookie(response, token, settings)
    return session_response(user, session)


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT, tags=["auth"])
async def logout(
    request: Request,
    response: Response,
    database: Annotated[AsyncSession, Depends(get_database_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    math_coach_session = request.cookies.get(settings.session_cookie_name)
    await revoke_session(math_coach_session, database)
    clear_session_cookie(response, settings)


@router.get("/auth/me", response_model=UserResponse, tags=["auth"])
async def current_user(user: CurrentUser) -> UserResponse:
    return user_response(user)


@router.get(
    "/exam-cycles",
    response_model=AvailableExamCycleListResponse,
    tags=["static-journey"],
)
async def get_exam_cycles(
    _user: CurrentUser,
    database: Annotated[AsyncSession, Depends(get_database_session)],
) -> AvailableExamCycleListResponse:
    return await available_exam_cycles(database)


@router.get(
    "/plans/today",
    response_model=StaticDailyPlanResponse,
    tags=["static-journey"],
)
async def get_static_daily_plan(
    user: CurrentUser,
    database: Annotated[AsyncSession, Depends(get_database_session)],
) -> StaticDailyPlanResponse:
    return await static_daily_plan(user, database, utc_now().date())


@router.post(
    "/attempts/{attempt_id}/mock-evaluation",
    response_model=MockEvaluationResponse,
    tags=["static-journey"],
)
async def post_mock_evaluation(
    attempt_id: uuid.UUID,
    payload: MockEvaluationRequest,
    user: CurrentUser,
    database: Annotated[AsyncSession, Depends(get_database_session)],
    boundary: Annotated[DeterministicMockBoundary, Depends(get_mock_boundary)],
) -> MockEvaluationResponse:
    return await mock_evaluation(
        attempt_id=attempt_id,
        payload=payload,
        user=user,
        database=database,
        boundary=boundary,
    )


@router.post(
    "/attempts/{attempt_id}/hints/next",
    response_model=NextHintResponse,
    tags=["static-journey"],
)
async def post_next_hint(
    attempt_id: uuid.UUID,
    payload: NextHintRequest,
    user: CurrentUser,
    database: Annotated[AsyncSession, Depends(get_database_session)],
) -> NextHintResponse:
    return await next_hint(
        attempt_id=attempt_id,
        payload=payload,
        user=user,
        database=database,
    )


@router.get(
    "/concept-versions/{concept_version_id}",
    response_model=ConceptVersionResponse,
    tags=["static-journey"],
)
async def get_concept_version(
    concept_version_id: uuid.UUID,
    _user: CurrentUser,
    database: Annotated[AsyncSession, Depends(get_database_session)],
) -> ConceptVersionResponse:
    return await concept_version(concept_version_id, database)


@router.post("/uploads/presign", response_model=PresignUploadResponse, tags=["uploads"])
async def presign_upload(
    payload: PresignUploadRequest,
    user: CurrentUser,
    database: Annotated[AsyncSession, Depends(get_database_session)],
    storage: Annotated[ObjectStorage, Depends(get_object_storage)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> PresignUploadResponse:
    return await create_upload(payload, user, database, storage, settings)


@router.post(
    "/uploads/{upload_id}/complete",
    response_model=UploadResponse,
    tags=["uploads"],
)
async def mark_upload_complete(
    upload_id: uuid.UUID,
    user: CurrentUser,
    database: Annotated[AsyncSession, Depends(get_database_session)],
    storage: Annotated[ObjectStorage, Depends(get_object_storage)],
) -> UploadResponse:
    return await complete_upload(upload_id, user, database, storage)


@router.get("/uploads/{upload_id}", response_model=UploadResponse, tags=["uploads"])
async def get_upload(
    upload_id: uuid.UUID,
    user: CurrentUser,
    database: Annotated[AsyncSession, Depends(get_database_session)],
) -> UploadResponse:
    upload = await owned_upload(upload_id, user, database)
    return upload_response(upload)


@router.post(
    "/uploads/{upload_id}/download-url",
    response_model=UploadDownloadResponse,
    tags=["uploads"],
)
async def get_upload_download_url(
    upload_id: uuid.UUID,
    user: CurrentUser,
    database: Annotated[AsyncSession, Depends(get_database_session)],
    storage: Annotated[ObjectStorage, Depends(get_object_storage)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> UploadDownloadResponse:
    return await upload_download_url(
        upload_id=upload_id,
        user=user,
        database=database,
        storage=storage,
        settings=settings,
    )


@router.post(
    "/attempts/{attempt_id}/transcribe",
    response_model=TranscriptionResponse,
    tags=["transcription"],
)
async def post_transcription(
    attempt_id: uuid.UUID,
    payload: TranscribeRequest,
    user: CurrentUser,
    database: Annotated[AsyncSession, Depends(get_database_session)],
    storage: Annotated[ObjectStorage, Depends(get_object_storage)],
    settings: Annotated[Settings, Depends(get_settings)],
    provider: Annotated[StrictTranscriptionProvider, Depends(get_transcription_provider)],
) -> TranscriptionResponse:
    return await transcribe_attempt(
        attempt_id=attempt_id,
        payload=payload,
        user=user,
        database=database,
        storage=storage,
        settings=settings,
        provider=provider,
    )


@router.get(
    "/attempts/{attempt_id}/transcription",
    response_model=TranscriptionStateResponse,
    tags=["transcription"],
)
async def get_transcription_state(
    attempt_id: uuid.UUID,
    user: CurrentUser,
    database: Annotated[AsyncSession, Depends(get_database_session)],
) -> TranscriptionStateResponse:
    return await transcription_state(
        attempt_id=attempt_id,
        user=user,
        database=database,
    )


@router.post(
    "/attempts/{attempt_id}/transcripts",
    response_model=TranscriptVersionResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["transcription"],
)
async def post_transcript_version(
    attempt_id: uuid.UUID,
    payload: TranscriptVersionCreateRequest,
    user: CurrentUser,
    database: Annotated[AsyncSession, Depends(get_database_session)],
) -> TranscriptVersionResponse:
    return await create_transcript_version(
        attempt_id=attempt_id,
        payload=payload,
        user=user,
        database=database,
    )


@router.post(
    "/attempts/{attempt_id}/confirm-transcript",
    response_model=TranscriptConfirmationResponse,
    tags=["transcription"],
)
async def post_transcript_confirmation(
    attempt_id: uuid.UUID,
    payload: TranscriptConfirmRequest,
    user: CurrentUser,
    database: Annotated[AsyncSession, Depends(get_database_session)],
) -> TranscriptConfirmationResponse:
    return await confirm_transcript(
        attempt_id=attempt_id,
        payload=payload,
        user=user,
        database=database,
    )


@router.get("/study-profile", response_model=StudyProfileResponse, tags=["study-profile"])
async def read_study_profile(
    user: CurrentUser,
    database: Annotated[AsyncSession, Depends(get_database_session)],
) -> StudyProfileResponse:
    return await get_profile(user, database)


@router.post(
    "/study-profile",
    response_model=StudyProfileResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["study-profile"],
)
async def post_study_profile(
    payload: StudyProfileCreateRequest,
    user: CurrentUser,
    database: Annotated[AsyncSession, Depends(get_database_session)],
) -> StudyProfileResponse:
    return await create_profile(payload, user, database)


@router.patch("/study-profile", response_model=StudyProfileResponse, tags=["study-profile"])
async def update_study_profile(
    payload: StudyProfilePatchRequest,
    user: CurrentUser,
    database: Annotated[AsyncSession, Depends(get_database_session)],
) -> StudyProfileResponse:
    return await patch_profile(payload, user, database)


@router.get("/exam-targets", response_model=ExamTargetListResponse, tags=["exam-targets"])
async def read_exam_targets(
    user: CurrentUser,
    database: Annotated[AsyncSession, Depends(get_database_session)],
) -> ExamTargetListResponse:
    return await list_targets(user, database)


@router.post(
    "/exam-targets",
    response_model=ExamTargetResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["exam-targets"],
)
async def post_exam_target(
    payload: ExamTargetCreateRequest,
    user: CurrentUser,
    database: Annotated[AsyncSession, Depends(get_database_session)],
) -> ExamTargetResponse:
    return await create_target(payload, user, database)


@router.patch(
    "/exam-targets/{target_id}",
    response_model=ExamTargetResponse,
    tags=["exam-targets"],
)
async def update_exam_target(
    target_id: uuid.UUID,
    payload: ExamTargetPatchRequest,
    user: CurrentUser,
    database: Annotated[AsyncSession, Depends(get_database_session)],
) -> ExamTargetResponse:
    return await patch_target(target_id, payload, user, database)


@router.delete(
    "/exam-targets/{target_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["exam-targets"],
)
async def delete_exam_target(
    target_id: uuid.UUID,
    user: CurrentUser,
    database: Annotated[AsyncSession, Depends(get_database_session)],
) -> None:
    await archive_target(target_id, user, database)


@router.post(
    "/attempts",
    response_model=AttemptResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["attempts"],
)
async def post_attempt(
    payload: AttemptCreateRequest,
    user: CurrentUser,
    database: Annotated[AsyncSession, Depends(get_database_session)],
) -> AttemptResponse:
    return await create_attempt(payload, user, database)


@router.get("/attempts/{attempt_id}", response_model=AttemptResponse, tags=["attempts"])
async def get_attempt(
    attempt_id: uuid.UUID,
    user: CurrentUser,
    database: Annotated[AsyncSession, Depends(get_database_session)],
) -> AttemptResponse:
    return attempt_response(await owned_attempt(attempt_id, user, database))


@router.get(
    "/internal/content-preview",
    response_model=ContentPreviewListResponse,
    tags=["internal-content"],
)
async def get_content_previews(
    _user: CurrentUser,
    database: Annotated[AsyncSession, Depends(get_database_session)],
) -> ContentPreviewListResponse:
    return await list_content_previews(database)


@router.get(
    "/internal/content-preview/{problem_id}",
    response_model=ContentPreviewResponse,
    tags=["internal-content"],
)
async def get_content_preview(
    problem_id: uuid.UUID,
    _user: CurrentUser,
    database: Annotated[AsyncSession, Depends(get_database_session)],
) -> ContentPreviewResponse:
    return await content_preview(problem_id, database)
