import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator
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


class StudyProfileCreateRequest(ApiModel):
    name: str = Field(min_length=1, max_length=120)
    weekly_study_minutes: int = Field(ge=1, le=7 * 24 * 60)


class StudyProfilePatchRequest(ApiModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    weekly_study_minutes: int | None = Field(default=None, ge=1, le=7 * 24 * 60)
    status: Literal["active", "archived"] | None = None

    @model_validator(mode="after")
    def has_at_least_one_change(self) -> Self:
        if self.name is None and self.weekly_study_minutes is None and self.status is None:
            raise ValueError("at least one study profile field is required")
        return self


ExamTargetStatus = Literal["active", "completed", "archived"]


class ExamTargetCreateRequest(ApiModel):
    exam_cycle_id: uuid.UUID
    target_score: Decimal = Field(ge=0, max_digits=8, decimal_places=2)
    priority_rank: int = Field(ge=1)


class ExamTargetPatchRequest(ApiModel):
    target_score: Decimal | None = Field(default=None, ge=0, max_digits=8, decimal_places=2)
    priority_rank: int | None = Field(default=None, ge=1)
    status: ExamTargetStatus | None = None

    @model_validator(mode="after")
    def has_at_least_one_change(self) -> Self:
        if self.target_score is None and self.priority_rank is None and self.status is None:
            raise ValueError("at least one exam target field is required")
        return self


class ExamTargetResponse(ApiModel):
    id: uuid.UUID
    exam_cycle_id: uuid.UUID
    exam_id: uuid.UUID
    exam_code: str
    exam_name: str
    exam_date: date
    target_score: Decimal
    priority_rank: int
    status: ExamTargetStatus
    created_at: datetime


class ExamTargetListResponse(ApiModel):
    items: list[ExamTargetResponse]


class StudyProfileResponse(ApiModel):
    id: uuid.UUID
    name: str
    weekly_study_minutes: int
    status: Literal["active", "archived"]
    student_exam_targets: list[ExamTargetResponse]
    created_at: datetime
    updated_at: datetime


class AttemptCreateRequest(ApiModel):
    problem_version_id: uuid.UUID


class AttemptResponse(ApiModel):
    id: uuid.UUID
    study_profile_id: uuid.UUID
    problem_version_id: uuid.UUID
    status: Literal["draft", "submitted"]
    created_at: datetime
