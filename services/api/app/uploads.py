import uuid
from datetime import timedelta
from pathlib import PurePath
from typing import Annotated

from fastapi import Depends
from minio.error import S3Error
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.auth import CurrentUser
from app.config import Settings, get_settings
from app.database import get_database_session
from app.errors import AppError
from app.models import SolutionUpload, User
from app.schemas import (
    AllowedImageType,
    PresignUploadRequest,
    PresignUploadResponse,
    UploadResponse,
    UploadStatus,
)
from app.security import utc_now
from app.storage import ObjectNotFoundError, ObjectStorage, get_object_storage

Database = Annotated[AsyncSession, Depends(get_database_session)]
Storage = Annotated[ObjectStorage, Depends(get_object_storage)]
AppSettings = Annotated[Settings, Depends(get_settings)]


def safe_file_name(value: str) -> str:
    name = PurePath(value.replace("\\", "/")).name.strip()
    if not name or name in {".", ".."} or "\x00" in name:
        raise AppError(
            status_code=422,
            code="invalid_file_name",
            message="Choose an image with a valid file name.",
        )
    return name


def allowed_image_type(value: str) -> AllowedImageType:
    if value == "image/jpeg":
        return "image/jpeg"
    if value == "image/png":
        return "image/png"
    if value == "image/webp":
        return "image/webp"
    raise RuntimeError("Stored upload has an invalid content type")


def upload_status(value: str) -> UploadStatus:
    if value == "pending":
        return "pending"
    if value == "ready":
        return "ready"
    if value == "rejected":
        return "rejected"
    raise RuntimeError("Stored upload has an invalid status")


def upload_response(upload: SolutionUpload) -> UploadResponse:
    return UploadResponse(
        id=upload.id,
        file_name=upload.original_file_name,
        content_type=allowed_image_type(upload.expected_content_type),
        size_bytes=upload.expected_size_bytes,
        status=upload_status(upload.status),
        created_at=upload.created_at,
    )


async def create_upload(
    payload: PresignUploadRequest,
    user: CurrentUser,
    database: Database,
    storage: Storage,
    settings: AppSettings,
) -> PresignUploadResponse:
    if payload.size_bytes > settings.upload_max_bytes:
        raise AppError(
            status_code=422,
            code="file_too_large",
            message="Choose an image no larger than 10 MB.",
        )
    upload_id = uuid.uuid4()
    upload = SolutionUpload(
        id=upload_id,
        user_id=user.id,
        object_key=f"users/{user.id}/solution-uploads/{upload_id}",
        original_file_name=safe_file_name(payload.file_name),
        expected_content_type=payload.content_type,
        expected_size_bytes=payload.size_bytes,
    )
    database.add(upload)
    expires_at = utc_now() + timedelta(seconds=settings.upload_url_expiry_seconds)
    try:
        upload_url = storage.presign_put(
            upload.object_key,
            settings.upload_url_expiry_seconds,
        )
        await database.commit()
    except Exception:
        await database.rollback()
        raise
    return PresignUploadResponse(
        upload_id=upload.id,
        upload_url=upload_url,
        expires_at=expires_at,
    )


async def owned_upload(
    upload_id: uuid.UUID,
    user: User,
    database: AsyncSession,
) -> SolutionUpload:
    upload = await database.scalar(
        select(SolutionUpload).where(
            SolutionUpload.id == upload_id,
            SolutionUpload.user_id == user.id,
        )
    )
    if upload is None:
        raise AppError(status_code=404, code="upload_not_found", message="Upload not found.")
    return upload


async def complete_upload(
    upload_id: uuid.UUID,
    user: CurrentUser,
    database: Database,
    storage: Storage,
) -> UploadResponse:
    upload = await owned_upload(upload_id, user, database)
    if upload.status == "ready":
        return upload_response(upload)
    if upload.status == "rejected":
        raise AppError(
            status_code=422,
            code="upload_rejected",
            message="Choose the image again and retry.",
        )
    try:
        item = await run_in_threadpool(storage.stat, upload.object_key)
    except ObjectNotFoundError as error:
        raise AppError(
            status_code=409,
            code="upload_not_received",
            message="The upload has not arrived yet. Try again.",
        ) from error
    except S3Error as error:
        raise AppError(
            status_code=503,
            code="storage_unavailable",
            message="Image storage is temporarily unavailable.",
        ) from error

    if item.size != upload.expected_size_bytes or item.content_type != upload.expected_content_type:
        try:
            await run_in_threadpool(storage.remove, upload.object_key)
        finally:
            upload.status = "rejected"
            upload.verified_size_bytes = item.size
            upload.verified_content_type = item.content_type
            await database.commit()
        raise AppError(
            status_code=422,
            code="upload_verification_failed",
            message="The stored image did not match the selected file.",
        )

    upload.status = "ready"
    upload.verified_size_bytes = item.size
    upload.verified_content_type = item.content_type
    await database.commit()
    return upload_response(upload)
