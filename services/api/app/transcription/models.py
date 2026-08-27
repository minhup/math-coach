import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class AttemptAsset(Base):
    __tablename__ = "attempt_assets"
    __table_args__ = (
        CheckConstraint("length(content_sha256) = 64", name="ck_attempt_assets_hash"),
        UniqueConstraint("attempt_id", "solution_upload_id", name="uq_attempt_assets_link"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    attempt_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("attempts.id", ondelete="RESTRICT")
    )
    solution_upload_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("solution_uploads.id", ondelete="RESTRICT")
    )
    content_sha256: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PromptVersion(Base):
    __tablename__ = "prompt_versions"
    __table_args__ = (
        UniqueConstraint("operation", "version", name="uq_prompt_versions_operation_version"),
        CheckConstraint("length(prompt_sha256) = 64", name="ck_prompt_versions_hash"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    operation: Mapped[str] = mapped_column(String(40))
    version: Mapped[str] = mapped_column(String(80))
    prompt_text: Mapped[str] = mapped_column(Text)
    prompt_sha256: Mapped[str] = mapped_column(String(64), unique=True)
    schema_version: Mapped[str] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AIModelRun(Base):
    __tablename__ = "ai_model_runs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('processing', 'succeeded', 'uncertain', 'retryable_failure', "
            "'permanent_failure', 'invalid_schema')",
            name="ck_ai_model_runs_status",
        ),
        CheckConstraint(
            "schema_attempts >= 0 AND schema_attempts <= 2",
            name="ck_ai_model_runs_schema_attempts",
        ),
        CheckConstraint("latency_ms IS NULL OR latency_ms >= 0", name="ck_ai_model_runs_latency"),
        CheckConstraint(
            "input_tokens IS NULL OR input_tokens >= 0", name="ck_ai_model_runs_input_tokens"
        ),
        CheckConstraint(
            "output_tokens IS NULL OR output_tokens >= 0", name="ck_ai_model_runs_output_tokens"
        ),
        CheckConstraint("cost_usd IS NULL OR cost_usd >= 0", name="ck_ai_model_runs_cost"),
        Index(
            "ix_ai_model_runs_asset_fingerprint_created",
            "attempt_asset_id",
            "request_fingerprint",
            "started_at",
        ),
        Index(
            "uq_ai_model_runs_asset_processing",
            "attempt_asset_id",
            unique=True,
            postgresql_where=text("status = 'processing'"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    attempt_asset_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("attempt_assets.id", ondelete="RESTRICT")
    )
    prompt_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("prompt_versions.id", ondelete="RESTRICT")
    )
    provider: Mapped[str] = mapped_column(String(80))
    model_snapshot: Mapped[str] = mapped_column(String(120))
    schema_version: Mapped[str] = mapped_column(String(80))
    pricing_version: Mapped[str] = mapped_column(String(80))
    idempotency_key: Mapped[uuid.UUID] = mapped_column(Uuid, unique=True)
    request_fingerprint: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), default="processing")
    schema_attempts: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    input_tokens: Mapped[int | None] = mapped_column(Integer)
    output_tokens: Mapped[int | None] = mapped_column(Integer)
    cost_usd: Mapped[Decimal | None] = mapped_column(Numeric(12, 6))
    error_code: Mapped[str | None] = mapped_column(String(80))
    result_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class TranscriptVersion(Base):
    __tablename__ = "transcript_versions"
    __table_args__ = (
        CheckConstraint("version > 0", name="ck_transcript_versions_version"),
        CheckConstraint("origin IN ('provider', 'learner')", name="ck_transcript_versions_origin"),
        CheckConstraint("length(transcript_sha256) = 64", name="ck_transcript_versions_hash"),
        UniqueConstraint("attempt_id", "version", name="uq_transcript_versions_number"),
        UniqueConstraint("attempt_id", "transcript_sha256", name="uq_transcript_versions_hash"),
        Index(
            "ix_transcript_versions_source_run_version",
            "source_model_run_id",
            "version",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    attempt_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("attempts.id", ondelete="RESTRICT")
    )
    source_model_run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("ai_model_runs.id", ondelete="RESTRICT")
    )
    parent_transcript_version_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("transcript_versions.id", ondelete="RESTRICT")
    )
    version: Mapped[int] = mapped_column(Integer)
    schema_version: Mapped[str] = mapped_column(String(24))
    document_json: Mapped[dict[str, Any]] = mapped_column(JSONB)
    transcript_sha256: Mapped[str] = mapped_column(String(64))
    origin: Mapped[str] = mapped_column(String(24))
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="RESTRICT")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TranscriptConfirmation(Base):
    __tablename__ = "transcript_confirmations"
    __table_args__ = (
        CheckConstraint("length(transcript_sha256) = 64", name="ck_confirmations_hash"),
        UniqueConstraint("attempt_id", name="uq_transcript_confirmations_attempt"),
        UniqueConstraint("transcript_version_id", name="uq_transcript_confirmations_version"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    attempt_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("attempts.id", ondelete="RESTRICT")
    )
    transcript_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("transcript_versions.id", ondelete="RESTRICT")
    )
    transcript_sha256: Mapped[str] = mapped_column(String(64))
    confirmed_by_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="RESTRICT")
    )
    confirmed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
