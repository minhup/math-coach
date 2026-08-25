import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class ApiModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class HealthResponse(ApiModel):
    status: Literal["ok"]


class ErrorDetail(ApiModel):
    code: str
    message: str
    request_id: str | None = None


class ErrorEnvelope(ApiModel):
    error: ErrorDetail


class PilotLoginRequest(ApiModel):
    invite_code: str = Field(min_length=4, max_length=128)


class UserResponse(ApiModel):
    id: uuid.UUID
    display_name: str


class SessionResponse(ApiModel):
    user: UserResponse
    expires_at: datetime


AllowedImageType = Literal["image/jpeg", "image/png", "image/webp"]
UploadStatus = Literal["pending", "ready", "rejected"]


class PresignUploadRequest(ApiModel):
    file_name: str = Field(min_length=1, max_length=255)
    content_type: AllowedImageType
    size_bytes: int = Field(ge=1, le=10 * 1024 * 1024)


class PresignUploadResponse(ApiModel):
    upload_id: uuid.UUID
    upload_url: str
    expires_at: datetime


class UploadResponse(ApiModel):
    id: uuid.UUID
    file_name: str
    content_type: AllowedImageType
    size_bytes: int
    status: UploadStatus
    created_at: datetime
