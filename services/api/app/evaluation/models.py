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
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('processing', 'succeeded', 'uncertain', 'retryable_failure', "
            "'permanent_failure', 'invalid_schema')",
            name="ck_evaluation_runs_status",
        ),
        CheckConstraint(
            "schema_attempts >= 0 AND schema_attempts <= 2",
            name="ck_evaluation_runs_schema_attempts",
        ),
        CheckConstraint("retry_count >= 0 AND retry_count <= 1", name="ck_evaluation_runs_retry"),
        CheckConstraint("latency_ms IS NULL OR latency_ms >= 0", name="ck_evaluation_runs_latency"),
        CheckConstraint(
            "input_tokens IS NULL OR input_tokens >= 0", name="ck_evaluation_runs_input"
        ),
        CheckConstraint(
            "output_tokens IS NULL OR output_tokens >= 0", name="ck_evaluation_runs_output"
        ),
        CheckConstraint("cost_usd IS NULL OR cost_usd >= 0", name="ck_evaluation_runs_cost"),
        Index(
            "ix_evaluation_runs_attempt_fingerprint_started",
            "attempt_id",
            "request_fingerprint",
            "started_at",
        ),
        Index(
            "uq_evaluation_runs_attempt_processing",
            "attempt_id",
            unique=True,
            postgresql_where=text("status = 'processing'"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    attempt_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("attempts.id", ondelete="RESTRICT")
    )
    confirmed_transcript_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("transcript_versions.id", ondelete="RESTRICT")
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
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    input_tokens: Mapped[int | None] = mapped_column(Integer)
    output_tokens: Mapped[int | None] = mapped_column(Integer)
    cost_usd: Mapped[Decimal | None] = mapped_column(Numeric(12, 6))
    error_code: Mapped[str | None] = mapped_column(String(80))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AttemptStep(Base):
    __tablename__ = "attempt_steps"
    __table_args__ = (
        CheckConstraint("position > 0", name="ck_attempt_steps_position"),
        CheckConstraint(
            "judgment IN ('correct', 'incorrect', 'uncertain', 'not_assessable')",
            name="ck_attempt_steps_judgment",
        ),
        CheckConstraint(
            "error_kind IN ('none', 'root', 'dependent')", name="ck_attempt_steps_error_kind"
        ),
        UniqueConstraint("evaluation_run_id", "position", name="uq_attempt_steps_run_position"),
        Index("ix_attempt_steps_run_position", "evaluation_run_id", "position"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    evaluation_run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("evaluation_runs.id", ondelete="RESTRICT")
    )
    position: Mapped[int] = mapped_column(Integer)
    transcript_block_ids_json: Mapped[list[Any]] = mapped_column(JSONB)
    summary_json: Mapped[list[Any]] = mapped_column(JSONB)
    judgment: Mapped[str] = mapped_column(String(24))
    error_kind: Mapped[str] = mapped_column(String(16))
    depends_on_step_ids_json: Mapped[list[Any]] = mapped_column(JSONB)
    feedback_json: Mapped[list[Any]] = mapped_column(JSONB)


class Evaluation(Base):
    __tablename__ = "evaluations"
    __table_args__ = (
        CheckConstraint("outcome IN ('ready', 'uncertain')", name="ck_evaluations_outcome"),
        CheckConstraint("score IS NULL OR score >= 0", name="ck_evaluations_score"),
        CheckConstraint("maximum_score IS NULL OR maximum_score > 0", name="ck_evaluations_max"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    evaluation_run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("evaluation_runs.id", ondelete="RESTRICT"), unique=True
    )
    outcome: Mapped[str] = mapped_column(String(16))
    score: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    maximum_score: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    rubric_breakdown_json: Mapped[list[Any] | None] = mapped_column(JSONB)
    feedback_json: Mapped[list[Any] | None] = mapped_column(JSONB)
    next_steps_json: Mapped[list[Any] | None] = mapped_column(JSONB)
    uncertainty_reason_json: Mapped[list[Any] | None] = mapped_column(JSONB)
    recommended_action: Mapped[str | None] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class HintEvent(Base):
    __tablename__ = "hint_events"
    __table_args__ = (
        CheckConstraint("hint_level >= 1 AND hint_level <= 5", name="ck_hint_events_level"),
        UniqueConstraint("attempt_id", "hint_level", name="uq_hint_events_attempt_level"),
        Index("ix_hint_events_attempt_level", "attempt_id", "hint_level"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    attempt_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("attempts.id", ondelete="RESTRICT")
    )
    evaluation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("evaluations.id", ondelete="RESTRICT")
    )
    hint_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("problem_hints.id", ondelete="RESTRICT")
    )
    hint_level: Mapped[int] = mapped_column(Integer)
    idempotency_key: Mapped[uuid.UUID] = mapped_column(Uuid, unique=True)
    released_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
