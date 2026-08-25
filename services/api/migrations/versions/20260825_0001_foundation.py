"""Create Milestone 1 authentication and upload foundation.

Revision ID: 20260825_0001
Revises: None
Create Date: 2026-08-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260825_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("account_status", sa.String(length=24), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("account_status IN ('active', 'disabled')", name="ck_users_status"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "pilot_invites",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code_digest", sa.String(length=64), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("max_uses", sa.Integer(), nullable=False),
        sa.Column("use_count", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("status IN ('active', 'disabled')", name="ck_pilot_invites_status"),
        sa.CheckConstraint("use_count >= 0", name="ck_pilot_invites_use_count"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code_digest"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_table(
        "user_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("token_digest", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_digest"),
    )
    op.create_index(
        "ix_user_sessions_user_active",
        "user_sessions",
        ["user_id", "expires_at", "revoked_at"],
    )
    op.create_table(
        "solution_uploads",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("object_key", sa.String(length=512), nullable=False),
        sa.Column("original_file_name", sa.String(length=255), nullable=False),
        sa.Column("expected_content_type", sa.String(length=64), nullable=False),
        sa.Column("expected_size_bytes", sa.Integer(), nullable=False),
        sa.Column("verified_content_type", sa.String(length=64), nullable=True),
        sa.Column("verified_size_bytes", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'ready', 'rejected')", name="ck_solution_uploads_status"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("object_key"),
    )
    op.create_index("ix_solution_uploads_status", "solution_uploads", ["status"])
    op.create_index(
        "ix_solution_uploads_user_created",
        "solution_uploads",
        ["user_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_solution_uploads_user_created", table_name="solution_uploads")
    op.drop_index("ix_solution_uploads_status", table_name="solution_uploads")
    op.drop_table("solution_uploads")
    op.drop_index("ix_user_sessions_user_active", table_name="user_sessions")
    op.drop_table("user_sessions")
    op.drop_table("pilot_invites")
    op.drop_table("users")
