"""Create Milestone 7 evaluation, scoring, and progressive hint records.

Revision ID: 20260828_0004
Revises: 20260827_0003
Create Date: 2026-08-28
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260828_0004"
down_revision: str | None = "20260827_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

IMMUTABLE_TABLES = ("attempt_steps", "evaluations", "hint_events")


def upgrade() -> None:
    op.create_table(
        "evaluation_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("attempt_id", sa.Uuid(), nullable=False),
        sa.Column("confirmed_transcript_version_id", sa.Uuid(), nullable=False),
        sa.Column("prompt_version_id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("model_snapshot", sa.String(length=120), nullable=False),
        sa.Column("schema_version", sa.String(length=80), nullable=False),
        sa.Column("pricing_version", sa.String(length=80), nullable=False),
        sa.Column("idempotency_key", sa.Uuid(), nullable=False),
        sa.Column("request_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("schema_attempts", sa.Integer(), nullable=False),
        sa.Column("retry_count", sa.Integer(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("cost_usd", sa.Numeric(precision=12, scale=6), nullable=True),
        sa.Column("error_code", sa.String(length=80), nullable=True),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('processing', 'succeeded', 'uncertain', 'retryable_failure', "
            "'permanent_failure', 'invalid_schema')",
            name="ck_evaluation_runs_status",
        ),
        sa.CheckConstraint(
            "schema_attempts >= 0 AND schema_attempts <= 2",
            name="ck_evaluation_runs_schema_attempts",
        ),
        sa.CheckConstraint(
            "retry_count >= 0 AND retry_count <= 1", name="ck_evaluation_runs_retry"
        ),
        sa.CheckConstraint(
            "latency_ms IS NULL OR latency_ms >= 0", name="ck_evaluation_runs_latency"
        ),
        sa.CheckConstraint(
            "input_tokens IS NULL OR input_tokens >= 0", name="ck_evaluation_runs_input"
        ),
        sa.CheckConstraint(
            "output_tokens IS NULL OR output_tokens >= 0", name="ck_evaluation_runs_output"
        ),
        sa.CheckConstraint("cost_usd IS NULL OR cost_usd >= 0", name="ck_evaluation_runs_cost"),
        sa.ForeignKeyConstraint(["attempt_id"], ["attempts.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["confirmed_transcript_version_id"],
            ["transcript_versions.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["prompt_version_id"], ["prompt_versions.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key"),
    )
    op.create_index(
        "ix_evaluation_runs_attempt_fingerprint_started",
        "evaluation_runs",
        ["attempt_id", "request_fingerprint", "started_at"],
    )
    op.create_index(
        "uq_evaluation_runs_attempt_processing",
        "evaluation_runs",
        ["attempt_id"],
        unique=True,
        postgresql_where=sa.text("status = 'processing'"),
    )
    op.execute(
        """
        CREATE FUNCTION enforce_m7_evaluation_run_transition() RETURNS trigger AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                RAISE EXCEPTION 'evaluation runs cannot be deleted';
            END IF;
            IF OLD.status <> 'processing' OR NEW.status = 'processing' THEN
                RAISE EXCEPTION 'completed evaluation runs are immutable';
            END IF;
            IF NEW.id IS DISTINCT FROM OLD.id
                OR NEW.attempt_id IS DISTINCT FROM OLD.attempt_id
                OR NEW.confirmed_transcript_version_id IS DISTINCT
                    FROM OLD.confirmed_transcript_version_id
                OR NEW.prompt_version_id IS DISTINCT FROM OLD.prompt_version_id
                OR NEW.provider IS DISTINCT FROM OLD.provider
                OR NEW.model_snapshot IS DISTINCT FROM OLD.model_snapshot
                OR NEW.schema_version IS DISTINCT FROM OLD.schema_version
                OR NEW.pricing_version IS DISTINCT FROM OLD.pricing_version
                OR NEW.idempotency_key IS DISTINCT FROM OLD.idempotency_key
                OR NEW.request_fingerprint IS DISTINCT FROM OLD.request_fingerprint
                OR NEW.started_at IS DISTINCT FROM OLD.started_at THEN
                RAISE EXCEPTION 'evaluation run identity is immutable';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_m7_evaluation_runs_transition
        BEFORE UPDATE OR DELETE ON evaluation_runs
        FOR EACH ROW EXECUTE FUNCTION enforce_m7_evaluation_run_transition();
        """
    )

    op.create_table(
        "attempt_steps",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("evaluation_run_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("transcript_block_ids_json", postgresql.JSONB(), nullable=False),
        sa.Column("summary_json", postgresql.JSONB(), nullable=False),
        sa.Column("judgment", sa.String(length=24), nullable=False),
        sa.Column("error_kind", sa.String(length=16), nullable=False),
        sa.Column("depends_on_step_ids_json", postgresql.JSONB(), nullable=False),
        sa.Column("feedback_json", postgresql.JSONB(), nullable=False),
        sa.CheckConstraint("position > 0", name="ck_attempt_steps_position"),
        sa.CheckConstraint(
            "judgment IN ('correct', 'incorrect', 'uncertain', 'not_assessable')",
            name="ck_attempt_steps_judgment",
        ),
        sa.CheckConstraint(
            "error_kind IN ('none', 'root', 'dependent')", name="ck_attempt_steps_error_kind"
        ),
        sa.ForeignKeyConstraint(["evaluation_run_id"], ["evaluation_runs.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("evaluation_run_id", "position", name="uq_attempt_steps_run_position"),
    )
    op.create_index(
        "ix_attempt_steps_run_position", "attempt_steps", ["evaluation_run_id", "position"]
    )
    op.create_table(
        "evaluations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("evaluation_run_id", sa.Uuid(), nullable=False),
        sa.Column("outcome", sa.String(length=16), nullable=False),
        sa.Column("score", sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column("maximum_score", sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column("rubric_breakdown_json", postgresql.JSONB(), nullable=True),
        sa.Column("feedback_json", postgresql.JSONB(), nullable=True),
        sa.Column("next_steps_json", postgresql.JSONB(), nullable=True),
        sa.Column("uncertainty_reason_json", postgresql.JSONB(), nullable=True),
        sa.Column("recommended_action", sa.String(length=32), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("outcome IN ('ready', 'uncertain')", name="ck_evaluations_outcome"),
        sa.CheckConstraint("score IS NULL OR score >= 0", name="ck_evaluations_score"),
        sa.CheckConstraint("maximum_score IS NULL OR maximum_score > 0", name="ck_evaluations_max"),
        sa.ForeignKeyConstraint(["evaluation_run_id"], ["evaluation_runs.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("evaluation_run_id"),
    )
    op.create_table(
        "hint_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("attempt_id", sa.Uuid(), nullable=False),
        sa.Column("evaluation_id", sa.Uuid(), nullable=False),
        sa.Column("hint_id", sa.Uuid(), nullable=False),
        sa.Column("hint_level", sa.Integer(), nullable=False),
        sa.Column("idempotency_key", sa.Uuid(), nullable=False),
        sa.Column(
            "released_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("hint_level >= 1 AND hint_level <= 5", name="ck_hint_events_level"),
        sa.ForeignKeyConstraint(["attempt_id"], ["attempts.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["evaluation_id"], ["evaluations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["hint_id"], ["problem_hints.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key"),
        sa.UniqueConstraint("attempt_id", "hint_level", name="uq_hint_events_attempt_level"),
    )
    op.create_index("ix_hint_events_attempt_level", "hint_events", ["attempt_id", "hint_level"])
    for table_name in IMMUTABLE_TABLES:
        op.execute(
            f"""
            CREATE TRIGGER trg_m7_{table_name}_immutable
            BEFORE UPDATE OR DELETE ON {table_name}
            FOR EACH ROW EXECUTE FUNCTION reject_immutable_content_change();
            """
        )


def downgrade() -> None:
    for table_name in reversed(IMMUTABLE_TABLES):
        op.execute(f"DROP TRIGGER trg_m7_{table_name}_immutable ON {table_name}")
    op.drop_index("ix_hint_events_attempt_level", table_name="hint_events")
    op.drop_table("hint_events")
    op.drop_table("evaluations")
    op.drop_index("ix_attempt_steps_run_position", table_name="attempt_steps")
    op.drop_table("attempt_steps")
    op.execute("DROP TRIGGER trg_m7_evaluation_runs_transition ON evaluation_runs")
    op.execute("DROP FUNCTION enforce_m7_evaluation_run_transition()")
    op.drop_index("uq_evaluation_runs_attempt_processing", table_name="evaluation_runs")
    op.drop_index("ix_evaluation_runs_attempt_fingerprint_started", table_name="evaluation_runs")
    op.drop_table("evaluation_runs")
