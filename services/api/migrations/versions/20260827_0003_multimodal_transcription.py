"""Create Milestone 6 multimodal transcription records.

Revision ID: 20260827_0003
Revises: 20260826_0002
Create Date: 2026-08-27
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260827_0003"
down_revision: str | None = "20260826_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

IMMUTABLE_TABLES = (
    "attempt_assets",
    "prompt_versions",
    "transcript_versions",
    "transcript_confirmations",
)


def upgrade() -> None:
    op.create_table(
        "attempt_assets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("attempt_id", sa.Uuid(), nullable=False),
        sa.Column("solution_upload_id", sa.Uuid(), nullable=False),
        sa.Column("content_sha256", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("length(content_sha256) = 64", name="ck_attempt_assets_hash"),
        sa.ForeignKeyConstraint(["attempt_id"], ["attempts.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["solution_upload_id"], ["solution_uploads.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("attempt_id", "solution_upload_id", name="uq_attempt_assets_link"),
    )
    op.create_table(
        "prompt_versions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("operation", sa.String(length=40), nullable=False),
        sa.Column("version", sa.String(length=80), nullable=False),
        sa.Column("prompt_text", sa.Text(), nullable=False),
        sa.Column("prompt_sha256", sa.String(length=64), nullable=False),
        sa.Column("schema_version", sa.String(length=80), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("length(prompt_sha256) = 64", name="ck_prompt_versions_hash"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("prompt_sha256"),
        sa.UniqueConstraint("operation", "version", name="uq_prompt_versions_operation_version"),
    )

    op.create_table(
        "ai_model_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("attempt_asset_id", sa.Uuid(), nullable=False),
        sa.Column("prompt_version_id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("model_snapshot", sa.String(length=120), nullable=False),
        sa.Column("schema_version", sa.String(length=80), nullable=False),
        sa.Column("pricing_version", sa.String(length=80), nullable=False),
        sa.Column("idempotency_key", sa.Uuid(), nullable=False),
        sa.Column("request_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("schema_attempts", sa.Integer(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("cost_usd", sa.Numeric(precision=12, scale=6), nullable=True),
        sa.Column("error_code", sa.String(length=80), nullable=True),
        sa.Column("result_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
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
            name="ck_ai_model_runs_status",
        ),
        sa.CheckConstraint(
            "schema_attempts >= 0 AND schema_attempts <= 2",
            name="ck_ai_model_runs_schema_attempts",
        ),
        sa.CheckConstraint(
            "latency_ms IS NULL OR latency_ms >= 0", name="ck_ai_model_runs_latency"
        ),
        sa.CheckConstraint(
            "input_tokens IS NULL OR input_tokens >= 0", name="ck_ai_model_runs_input_tokens"
        ),
        sa.CheckConstraint(
            "output_tokens IS NULL OR output_tokens >= 0", name="ck_ai_model_runs_output_tokens"
        ),
        sa.CheckConstraint("cost_usd IS NULL OR cost_usd >= 0", name="ck_ai_model_runs_cost"),
        sa.ForeignKeyConstraint(["attempt_asset_id"], ["attempt_assets.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["prompt_version_id"], ["prompt_versions.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key"),
    )
    op.create_index(
        "ix_ai_model_runs_asset_fingerprint_created",
        "ai_model_runs",
        ["attempt_asset_id", "request_fingerprint", "started_at"],
    )
    op.create_index(
        "uq_ai_model_runs_asset_processing",
        "ai_model_runs",
        ["attempt_asset_id"],
        unique=True,
        postgresql_where=sa.text("status = 'processing'"),
    )
    op.execute(
        """
        CREATE FUNCTION enforce_m6_model_run_transition() RETURNS trigger AS $$
        BEGIN
            IF OLD.status <> 'processing' OR NEW.status = 'processing' THEN
                RAISE EXCEPTION 'completed AI model runs are immutable';
            END IF;
            IF NEW.id IS DISTINCT FROM OLD.id
                OR NEW.attempt_asset_id IS DISTINCT FROM OLD.attempt_asset_id
                OR NEW.prompt_version_id IS DISTINCT FROM OLD.prompt_version_id
                OR NEW.provider IS DISTINCT FROM OLD.provider
                OR NEW.model_snapshot IS DISTINCT FROM OLD.model_snapshot
                OR NEW.schema_version IS DISTINCT FROM OLD.schema_version
                OR NEW.pricing_version IS DISTINCT FROM OLD.pricing_version
                OR NEW.idempotency_key IS DISTINCT FROM OLD.idempotency_key
                OR NEW.request_fingerprint IS DISTINCT FROM OLD.request_fingerprint
                OR NEW.started_at IS DISTINCT FROM OLD.started_at THEN
                RAISE EXCEPTION 'AI model run identity is immutable';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_m6_ai_model_runs_transition
        BEFORE UPDATE OR DELETE ON ai_model_runs
        FOR EACH ROW EXECUTE FUNCTION enforce_m6_model_run_transition();
        """
    )

    op.create_table(
        "transcript_versions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("attempt_id", sa.Uuid(), nullable=False),
        sa.Column("source_model_run_id", sa.Uuid(), nullable=False),
        sa.Column("parent_transcript_version_id", sa.Uuid(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("schema_version", sa.String(length=24), nullable=False),
        sa.Column("document_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("transcript_sha256", sa.String(length=64), nullable=False),
        sa.Column("origin", sa.String(length=24), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("version > 0", name="ck_transcript_versions_version"),
        sa.CheckConstraint(
            "origin IN ('provider', 'learner')", name="ck_transcript_versions_origin"
        ),
        sa.CheckConstraint("length(transcript_sha256) = 64", name="ck_transcript_versions_hash"),
        sa.ForeignKeyConstraint(["attempt_id"], ["attempts.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["source_model_run_id"], ["ai_model_runs.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["parent_transcript_version_id"], ["transcript_versions.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("attempt_id", "version", name="uq_transcript_versions_number"),
        sa.UniqueConstraint("attempt_id", "transcript_sha256", name="uq_transcript_versions_hash"),
    )
    op.create_index(
        "ix_transcript_versions_source_run_version",
        "transcript_versions",
        ["source_model_run_id", "version"],
    )

    op.create_table(
        "transcript_confirmations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("attempt_id", sa.Uuid(), nullable=False),
        sa.Column("transcript_version_id", sa.Uuid(), nullable=False),
        sa.Column("transcript_sha256", sa.String(length=64), nullable=False),
        sa.Column("confirmed_by_user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "confirmed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("length(transcript_sha256) = 64", name="ck_confirmations_hash"),
        sa.ForeignKeyConstraint(["attempt_id"], ["attempts.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["transcript_version_id"], ["transcript_versions.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["confirmed_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("attempt_id", name="uq_transcript_confirmations_attempt"),
        sa.UniqueConstraint("transcript_version_id", name="uq_transcript_confirmations_version"),
    )

    for table_name in IMMUTABLE_TABLES:
        op.execute(
            f"""
            CREATE TRIGGER trg_m6_{table_name}_immutable
            BEFORE UPDATE OR DELETE ON {table_name}
            FOR EACH ROW EXECUTE FUNCTION reject_immutable_content_change();
            """
        )


def downgrade() -> None:
    for table_name in reversed(IMMUTABLE_TABLES):
        op.execute(f"DROP TRIGGER trg_m6_{table_name}_immutable ON {table_name}")
    op.drop_table("transcript_confirmations")
    op.drop_index("ix_transcript_versions_source_run_version", table_name="transcript_versions")
    op.drop_table("transcript_versions")
    op.execute("DROP TRIGGER trg_m6_ai_model_runs_transition ON ai_model_runs")
    op.execute("DROP FUNCTION enforce_m6_model_run_transition()")
    op.drop_index("uq_ai_model_runs_asset_processing", table_name="ai_model_runs")
    op.drop_index("ix_ai_model_runs_asset_fingerprint_created", table_name="ai_model_runs")
    op.drop_table("ai_model_runs")
    op.drop_table("prompt_versions")
    op.drop_table("attempt_assets")
