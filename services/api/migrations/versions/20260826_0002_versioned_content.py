"""Create Milestone 2 versioned content and multi-exam schema.

Revision ID: 20260826_0002
Revises: 20260825_0001
Create Date: 2026-08-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260826_0002"
down_revision: str | None = "20260825_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

IMMUTABLE_TABLES = (
    "exam_skill_weights",
    "geometry_scene_versions",
    "concept_versions",
    "problem_versions",
    "problem_exam_relevance",
    "problem_skill_links",
    "reference_solutions",
    "rubric_items",
    "problem_hints",
)


def _timestamps() -> list[sa.Column[object]]:
    return [
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
    ]


def upgrade() -> None:
    op.create_table(
        "content_imports",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("package_id", sa.Uuid(), nullable=False),
        sa.Column("package_version", sa.Integer(), nullable=False),
        sa.Column("schema_version", sa.String(length=24), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("source_path", sa.String(length=512), nullable=False),
        sa.Column(
            "imported_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("length(content_hash) = 64", name="ck_content_imports_hash"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "package_id", "package_version", name="uq_content_imports_package_version"
        ),
    )
    op.create_table(
        "exams",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("region", sa.String(length=160), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("provenance_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.CheckConstraint("status IN ('synthetic', 'retired')", name="ck_exams_status"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_table(
        "skills",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("domain", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("provenance_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.CheckConstraint("status IN ('synthetic', 'retired')", name="ck_skills_status"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_table(
        "exam_cycles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("exam_id", sa.Uuid(), nullable=False),
        sa.Column("cycle_code", sa.String(length=100), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("exam_date", sa.Date(), nullable=False),
        sa.Column("maximum_score", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column("content_version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("provenance_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.CheckConstraint("content_version > 0", name="ck_exam_cycles_content_version"),
        sa.CheckConstraint("maximum_score > 0", name="ck_exam_cycles_maximum_score"),
        sa.CheckConstraint("status IN ('synthetic', 'retired')", name="ck_exam_cycles_status"),
        sa.ForeignKeyConstraint(["exam_id"], ["exams.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cycle_code"),
        sa.UniqueConstraint("exam_id", "cycle_code", name="uq_exam_cycles_exam_code"),
    )
    op.create_index("ix_exam_cycles_exam_date", "exam_cycles", ["exam_id", "exam_date"])
    op.create_table(
        "skill_edges",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("parent_skill_id", sa.Uuid(), nullable=False),
        sa.Column("child_skill_id", sa.Uuid(), nullable=False),
        sa.Column("relation_type", sa.String(length=24), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("provenance_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.CheckConstraint("parent_skill_id <> child_skill_id", name="ck_skill_edges_not_self"),
        sa.CheckConstraint(
            "relation_type IN ('prerequisite', 'related', 'subskill')",
            name="ck_skill_edges_relation",
        ),
        sa.ForeignKeyConstraint(["child_skill_id"], ["skills.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["parent_skill_id"], ["skills.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "parent_skill_id",
            "child_skill_id",
            "relation_type",
            name="uq_skill_edges_relationship",
        ),
    )
    op.create_table(
        "exam_skill_weights",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("exam_cycle_id", sa.Uuid(), nullable=False),
        sa.Column("skill_id", sa.Uuid(), nullable=False),
        sa.Column("weight", sa.Numeric(precision=6, scale=5), nullable=False),
        sa.Column("source_note", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("provenance_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.CheckConstraint("version > 0", name="ck_exam_skill_weights_version"),
        sa.CheckConstraint("weight > 0 AND weight <= 1", name="ck_exam_skill_weights_weight"),
        sa.ForeignKeyConstraint(["exam_cycle_id"], ["exam_cycles.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "exam_cycle_id",
            "skill_id",
            "version",
            name="uq_exam_skill_weights_cycle_skill_version",
        ),
    )
    op.create_index(
        "ix_exam_skill_weights_cycle_version",
        "exam_skill_weights",
        ["exam_cycle_id", "version"],
    )

    op.create_table(
        "geometry_scenes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("current_version_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.CheckConstraint(
            "status IN ('synthetic', 'withdrawn')", name="ck_geometry_scenes_status"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_table(
        "geometry_scene_versions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("geometry_scene_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("scene_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("provenance_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "published_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("version > 0", name="ck_geometry_scene_versions_version"),
        sa.ForeignKeyConstraint(
            ["geometry_scene_id"],
            ["geometry_scenes.id"],
            name="fk_geometry_scene_versions_scene",
            ondelete="RESTRICT",
            deferrable=True,
            initially="DEFERRED",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "geometry_scene_id", "version", name="uq_geometry_scene_versions_number"
        ),
    )
    op.create_index(
        "ix_geometry_scene_versions_scene", "geometry_scene_versions", ["geometry_scene_id"]
    )
    op.create_foreign_key(
        "fk_geometry_scenes_current_version",
        "geometry_scenes",
        "geometry_scene_versions",
        ["current_version_id"],
        ["id"],
        ondelete="RESTRICT",
        deferrable=True,
        initially="DEFERRED",
    )

    op.create_table(
        "concepts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("current_version_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.CheckConstraint("status IN ('synthetic', 'withdrawn')", name="ck_concepts_status"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_table(
        "concept_versions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("concept_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("content_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("geometry_scene_version_id", sa.Uuid(), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("provenance_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "published_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("version > 0", name="ck_concept_versions_version"),
        sa.ForeignKeyConstraint(
            ["concept_id"],
            ["concepts.id"],
            name="fk_concept_versions_concept",
            ondelete="RESTRICT",
            deferrable=True,
            initially="DEFERRED",
        ),
        sa.ForeignKeyConstraint(
            ["geometry_scene_version_id"],
            ["geometry_scene_versions.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("concept_id", "version", name="uq_concept_versions_number"),
    )
    op.create_index("ix_concept_versions_concept", "concept_versions", ["concept_id"])
    op.create_foreign_key(
        "fk_concepts_current_version",
        "concepts",
        "concept_versions",
        ["current_version_id"],
        ["id"],
        ondelete="RESTRICT",
        deferrable=True,
        initially="DEFERRED",
    )

    op.create_table(
        "problems",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("external_code", sa.String(length=120), nullable=False),
        sa.Column("origin_exam_cycle_id", sa.Uuid(), nullable=True),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("problem_number", sa.String(length=80), nullable=False),
        sa.Column("current_version_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.CheckConstraint("status IN ('synthetic', 'withdrawn')", name="ck_problems_status"),
        sa.ForeignKeyConstraint(["origin_exam_cycle_id"], ["exam_cycles.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("external_code"),
    )
    op.create_index("ix_problems_origin_cycle", "problems", ["origin_exam_cycle_id"])
    op.create_table(
        "problem_versions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("problem_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("statement_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("maximum_score", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column("difficulty_band", sa.String(length=24), nullable=False),
        sa.Column("estimated_minutes", sa.Integer(), nullable=False),
        sa.Column("geometry_scene_version_id", sa.Uuid(), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("provenance_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "published_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "difficulty_band IN ('introductory', 'core', 'advanced', 'challenge')",
            name="ck_problem_versions_difficulty",
        ),
        sa.CheckConstraint("estimated_minutes > 0", name="ck_problem_versions_minutes"),
        sa.CheckConstraint("maximum_score > 0", name="ck_problem_versions_score"),
        sa.CheckConstraint("version > 0", name="ck_problem_versions_version"),
        sa.ForeignKeyConstraint(
            ["geometry_scene_version_id"],
            ["geometry_scene_versions.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["problem_id"],
            ["problems.id"],
            name="fk_problem_versions_problem",
            ondelete="RESTRICT",
            deferrable=True,
            initially="DEFERRED",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("problem_id", "version", name="uq_problem_versions_number"),
    )
    op.create_index("ix_problem_versions_problem", "problem_versions", ["problem_id"])
    op.create_foreign_key(
        "fk_problems_current_version",
        "problems",
        "problem_versions",
        ["current_version_id"],
        ["id"],
        ondelete="RESTRICT",
        deferrable=True,
        initially="DEFERRED",
    )

    op.create_table(
        "problem_exam_relevance",
        sa.Column("problem_version_id", sa.Uuid(), nullable=False),
        sa.Column("exam_cycle_id", sa.Uuid(), nullable=False),
        sa.Column("relevance_level", sa.String(length=16), nullable=False),
        sa.Column("relevance_note", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("provenance_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.CheckConstraint(
            "relevance_level IN ('low', 'medium', 'high')",
            name="ck_problem_exam_relevance_level",
        ),
        sa.ForeignKeyConstraint(["exam_cycle_id"], ["exam_cycles.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["problem_version_id"], ["problem_versions.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("problem_version_id", "exam_cycle_id"),
    )
    op.create_index(
        "ix_problem_exam_relevance_cycle",
        "problem_exam_relevance",
        ["exam_cycle_id", "relevance_level"],
    )
    op.create_table(
        "problem_skill_links",
        sa.Column("problem_version_id", sa.Uuid(), nullable=False),
        sa.Column("skill_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(length=24), nullable=False),
        sa.Column("importance", sa.Numeric(precision=6, scale=5), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("provenance_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.CheckConstraint(
            "importance > 0 AND importance <= 1", name="ck_problem_skill_links_importance"
        ),
        sa.CheckConstraint(
            "role IN ('primary', 'secondary', 'prerequisite', 'diagnostic')",
            name="ck_problem_skill_links_role",
        ),
        sa.ForeignKeyConstraint(
            ["problem_version_id"], ["problem_versions.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("problem_version_id", "skill_id"),
    )
    op.create_index("ix_problem_skill_links_skill", "problem_skill_links", ["skill_id", "role"])
    op.create_table(
        "reference_solutions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("problem_version_id", sa.Uuid(), nullable=False),
        sa.Column("solution_code", sa.String(length=100), nullable=False),
        sa.Column("content_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("method_label", sa.String(length=200), nullable=False),
        sa.Column("expert_verified", sa.Boolean(), nullable=False),
        sa.Column("non_exhaustive", sa.Boolean(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("provenance_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.CheckConstraint("expert_verified", name="ck_reference_solutions_verified"),
        sa.CheckConstraint("non_exhaustive", name="ck_reference_solutions_non_exhaustive"),
        sa.ForeignKeyConstraint(
            ["problem_version_id"], ["problem_versions.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "problem_version_id", "solution_code", name="uq_reference_solutions_code"
        ),
    )
    op.create_index("ix_reference_solutions_problem", "reference_solutions", ["problem_version_id"])
    op.create_table(
        "rubric_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("problem_version_id", sa.Uuid(), nullable=False),
        sa.Column("rubric_code", sa.String(length=100), nullable=False),
        sa.Column("description_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("maximum_score", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column("skill_id", sa.Uuid(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("provenance_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.CheckConstraint("maximum_score > 0", name="ck_rubric_items_score"),
        sa.CheckConstraint("order_index > 0", name="ck_rubric_items_order"),
        sa.ForeignKeyConstraint(
            ["problem_version_id"], ["problem_versions.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("problem_version_id", "order_index", name="uq_rubric_items_order"),
        sa.UniqueConstraint("problem_version_id", "rubric_code", name="uq_rubric_items_code"),
    )
    op.create_index("ix_rubric_items_problem", "rubric_items", ["problem_version_id"])
    op.create_table(
        "problem_hints",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("problem_version_id", sa.Uuid(), nullable=False),
        sa.Column("hint_level", sa.Integer(), nullable=False),
        sa.Column("content_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("geometry_actions_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("reveals_complete_solution", sa.Boolean(), nullable=False),
        sa.Column("concept_id", sa.Uuid(), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("provenance_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.CheckConstraint("hint_level >= 1 AND hint_level <= 5", name="ck_problem_hints_level"),
        sa.ForeignKeyConstraint(["concept_id"], ["concepts.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["problem_version_id"], ["problem_versions.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("problem_version_id", "hint_level", name="uq_problem_hints_level"),
    )
    op.create_index(
        "ix_problem_hints_problem", "problem_hints", ["problem_version_id", "hint_level"]
    )

    op.create_table(
        "study_profiles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("weekly_study_minutes", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        *_timestamps(),
        sa.CheckConstraint("status IN ('active', 'archived')", name="ck_study_profiles_status"),
        sa.CheckConstraint("weekly_study_minutes > 0", name="ck_study_profiles_weekly_minutes"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_study_profiles_user_active",
        "study_profiles",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
    )
    op.create_table(
        "student_exam_targets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("study_profile_id", sa.Uuid(), nullable=False),
        sa.Column("exam_cycle_id", sa.Uuid(), nullable=False),
        sa.Column("target_score", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column("priority_rank", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        *_timestamps(),
        sa.CheckConstraint("priority_rank > 0", name="ck_student_exam_targets_priority"),
        sa.CheckConstraint("target_score >= 0", name="ck_student_exam_targets_score"),
        sa.CheckConstraint(
            "status IN ('active', 'completed', 'archived')",
            name="ck_student_exam_targets_status",
        ),
        sa.ForeignKeyConstraint(["exam_cycle_id"], ["exam_cycles.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["study_profile_id"], ["study_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_student_exam_targets_profile_status",
        "student_exam_targets",
        ["study_profile_id", "status"],
    )
    op.create_index(
        "uq_student_exam_targets_active_cycle",
        "student_exam_targets",
        ["study_profile_id", "exam_cycle_id"],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
    )
    op.create_index(
        "uq_student_exam_targets_active_priority",
        "student_exam_targets",
        ["study_profile_id", "priority_rank"],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
    )
    op.create_table(
        "attempts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("study_profile_id", sa.Uuid(), nullable=False),
        sa.Column("problem_version_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("status IN ('draft', 'submitted')", name="ck_attempts_status"),
        sa.ForeignKeyConstraint(
            ["problem_version_id"], ["problem_versions.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["study_profile_id"], ["study_profiles.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_attempts_problem_version", "attempts", ["problem_version_id"])
    op.create_index("ix_attempts_profile_created", "attempts", ["study_profile_id", "created_at"])

    op.execute(
        """
        CREATE FUNCTION reject_immutable_content_change() RETURNS trigger AS $$
        BEGIN
          RAISE EXCEPTION 'immutable content rows cannot be updated or deleted'
            USING ERRCODE = '55000';
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    for table_name in IMMUTABLE_TABLES:
        op.execute(
            f"""
            CREATE TRIGGER trg_{table_name}_immutable
            BEFORE UPDATE OR DELETE ON {table_name}
            FOR EACH ROW EXECUTE FUNCTION reject_immutable_content_change();
            """
        )


def downgrade() -> None:
    for table_name in reversed(IMMUTABLE_TABLES):
        op.execute(f"DROP TRIGGER trg_{table_name}_immutable ON {table_name}")
    op.execute("DROP FUNCTION reject_immutable_content_change()")

    op.drop_index("ix_attempts_profile_created", table_name="attempts")
    op.drop_index("ix_attempts_problem_version", table_name="attempts")
    op.drop_table("attempts")
    op.drop_index("uq_student_exam_targets_active_priority", table_name="student_exam_targets")
    op.drop_index("uq_student_exam_targets_active_cycle", table_name="student_exam_targets")
    op.drop_index("ix_student_exam_targets_profile_status", table_name="student_exam_targets")
    op.drop_table("student_exam_targets")
    op.drop_index("uq_study_profiles_user_active", table_name="study_profiles")
    op.drop_table("study_profiles")

    op.drop_index("ix_problem_hints_problem", table_name="problem_hints")
    op.drop_table("problem_hints")
    op.drop_index("ix_rubric_items_problem", table_name="rubric_items")
    op.drop_table("rubric_items")
    op.drop_index("ix_reference_solutions_problem", table_name="reference_solutions")
    op.drop_table("reference_solutions")
    op.drop_index("ix_problem_skill_links_skill", table_name="problem_skill_links")
    op.drop_table("problem_skill_links")
    op.drop_index("ix_problem_exam_relevance_cycle", table_name="problem_exam_relevance")
    op.drop_table("problem_exam_relevance")

    op.drop_constraint("fk_problems_current_version", "problems", type_="foreignkey")
    op.drop_index("ix_problem_versions_problem", table_name="problem_versions")
    op.drop_table("problem_versions")
    op.drop_index("ix_problems_origin_cycle", table_name="problems")
    op.drop_table("problems")

    op.drop_constraint("fk_concepts_current_version", "concepts", type_="foreignkey")
    op.drop_index("ix_concept_versions_concept", table_name="concept_versions")
    op.drop_table("concept_versions")
    op.drop_table("concepts")

    op.drop_constraint("fk_geometry_scenes_current_version", "geometry_scenes", type_="foreignkey")
    op.drop_index("ix_geometry_scene_versions_scene", table_name="geometry_scene_versions")
    op.drop_table("geometry_scene_versions")
    op.drop_table("geometry_scenes")

    op.drop_index("ix_exam_skill_weights_cycle_version", table_name="exam_skill_weights")
    op.drop_table("exam_skill_weights")
    op.drop_table("skill_edges")
    op.drop_index("ix_exam_cycles_exam_date", table_name="exam_cycles")
    op.drop_table("exam_cycles")
    op.drop_table("skills")
    op.drop_table("exams")
    op.drop_table("content_imports")
