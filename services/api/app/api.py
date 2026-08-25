import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

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
from app.database import get_database_session
from app.schemas import (
    ErrorEnvelope,
    HealthResponse,
    PilotLoginRequest,
    PresignUploadRequest,
    PresignUploadResponse,
    SessionResponse,
    UploadResponse,
    UserResponse,
)
from app.storage import ObjectStorage, get_object_storage
from app.uploads import complete_upload, create_upload, owned_upload, upload_response

error_responses: dict[int | str, dict[str, Any]] = {
    500: {"model": ErrorEnvelope, "description": "An unexpected server error occurred"},
    401: {"model": ErrorEnvelope, "description": "Authentication failed or is required"},
    404: {"model": ErrorEnvelope, "description": "Owned resource was not found"},
    409: {"model": ErrorEnvelope, "description": "Request conflicts with current state"},
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
