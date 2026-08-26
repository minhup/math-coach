import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
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
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base

JsonObject = dict[str, object]
JsonArray = list[object]


class ContentImport(Base):
    __tablename__ = "content_imports"
    __table_args__ = (
        UniqueConstraint(
            "package_id", "package_version", name="uq_content_imports_package_version"
        ),
        CheckConstraint("length(content_hash) = 64", name="ck_content_imports_hash"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    package_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    package_version: Mapped[int] = mapped_column(Integer)
    schema_version: Mapped[str] = mapped_column(String(24))
    content_hash: Mapped[str] = mapped_column(String(64))
    source_path: Mapped[str] = mapped_column(String(512))
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Exam(Base):
    __tablename__ = "exams"
    __table_args__ = (
        CheckConstraint("status IN ('synthetic', 'retired')", name="ck_exams_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    code: Mapped[str] = mapped_column(String(80), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    region: Mapped[str] = mapped_column(String(160))
    status: Mapped[str] = mapped_column(String(24))
    provenance_json: Mapped[JsonObject] = mapped_column(JSONB)


class ExamCycle(Base):
    __tablename__ = "exam_cycles"
    __table_args__ = (
        CheckConstraint("maximum_score > 0", name="ck_exam_cycles_maximum_score"),
        CheckConstraint("content_version > 0", name="ck_exam_cycles_content_version"),
        CheckConstraint("status IN ('synthetic', 'retired')", name="ck_exam_cycles_status"),
        UniqueConstraint("exam_id", "cycle_code", name="uq_exam_cycles_exam_code"),
        Index("ix_exam_cycles_exam_date", "exam_id", "exam_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    exam_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("exams.id", ondelete="RESTRICT"))
    cycle_code: Mapped[str] = mapped_column(String(100), unique=True)
    year: Mapped[int] = mapped_column(Integer)
    exam_date: Mapped[date] = mapped_column(Date)
    maximum_score: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    content_version: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(24))
    content_hash: Mapped[str] = mapped_column(String(64))
    provenance_json: Mapped[JsonObject] = mapped_column(JSONB)


class Skill(Base):
    __tablename__ = "skills"
    __table_args__ = (
        CheckConstraint("status IN ('synthetic', 'retired')", name="ck_skills_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    code: Mapped[str] = mapped_column(String(100), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    description_json: Mapped[JsonArray] = mapped_column(JSONB)
    domain: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(24))
    content_hash: Mapped[str] = mapped_column(String(64))
    provenance_json: Mapped[JsonObject] = mapped_column(JSONB)


class SkillEdge(Base):
    __tablename__ = "skill_edges"
    __table_args__ = (
        CheckConstraint(
            "relation_type IN ('prerequisite', 'related', 'subskill')",
            name="ck_skill_edges_relation",
        ),
        CheckConstraint("parent_skill_id <> child_skill_id", name="ck_skill_edges_not_self"),
        UniqueConstraint(
            "parent_skill_id",
            "child_skill_id",
            "relation_type",
            name="uq_skill_edges_relationship",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    parent_skill_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("skills.id", ondelete="RESTRICT")
    )
    child_skill_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("skills.id", ondelete="RESTRICT")
    )
    relation_type: Mapped[str] = mapped_column(String(24))
    content_hash: Mapped[str] = mapped_column(String(64))
    provenance_json: Mapped[JsonObject] = mapped_column(JSONB)


class ExamSkillWeight(Base):
    __tablename__ = "exam_skill_weights"
    __table_args__ = (
        CheckConstraint("weight > 0 AND weight <= 1", name="ck_exam_skill_weights_weight"),
        CheckConstraint("version > 0", name="ck_exam_skill_weights_version"),
        UniqueConstraint(
            "exam_cycle_id",
            "skill_id",
            "version",
            name="uq_exam_skill_weights_cycle_skill_version",
        ),
        Index("ix_exam_skill_weights_cycle_version", "exam_cycle_id", "version"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    exam_cycle_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("exam_cycles.id", ondelete="RESTRICT")
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("skills.id", ondelete="RESTRICT"))
    weight: Mapped[Decimal] = mapped_column(Numeric(6, 5))
    source_note: Mapped[str] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer)
    content_hash: Mapped[str] = mapped_column(String(64))
    provenance_json: Mapped[JsonObject] = mapped_column(JSONB)


class GeometryScene(Base):
    __tablename__ = "geometry_scenes"
    __table_args__ = (
        CheckConstraint("status IN ('synthetic', 'withdrawn')", name="ck_geometry_scenes_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    code: Mapped[str] = mapped_column(String(100), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    current_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey(
            "geometry_scene_versions.id",
            name="fk_geometry_scenes_current_version",
            use_alter=True,
            deferrable=True,
            initially="DEFERRED",
            ondelete="RESTRICT",
        ),
    )
    status: Mapped[str] = mapped_column(String(24))


class GeometrySceneVersion(Base):
    __tablename__ = "geometry_scene_versions"
    __table_args__ = (
        CheckConstraint("version > 0", name="ck_geometry_scene_versions_version"),
        UniqueConstraint("geometry_scene_id", "version", name="uq_geometry_scene_versions_number"),
        Index("ix_geometry_scene_versions_scene", "geometry_scene_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    geometry_scene_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey(
            "geometry_scenes.id",
            name="fk_geometry_scene_versions_scene",
            deferrable=True,
            initially="DEFERRED",
            ondelete="RESTRICT",
        ),
    )
    version: Mapped[int] = mapped_column(Integer)
    scene_json: Mapped[JsonObject] = mapped_column(JSONB)
    content_hash: Mapped[str] = mapped_column(String(64))
    provenance_json: Mapped[JsonObject] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Concept(Base):
    __tablename__ = "concepts"
    __table_args__ = (
        CheckConstraint("status IN ('synthetic', 'withdrawn')", name="ck_concepts_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    code: Mapped[str] = mapped_column(String(100), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    current_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey(
            "concept_versions.id",
            name="fk_concepts_current_version",
            use_alter=True,
            deferrable=True,
            initially="DEFERRED",
            ondelete="RESTRICT",
        ),
    )
    status: Mapped[str] = mapped_column(String(24))


class ConceptVersion(Base):
    __tablename__ = "concept_versions"
    __table_args__ = (
        CheckConstraint("version > 0", name="ck_concept_versions_version"),
        UniqueConstraint("concept_id", "version", name="uq_concept_versions_number"),
        Index("ix_concept_versions_concept", "concept_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    concept_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey(
            "concepts.id",
            name="fk_concept_versions_concept",
            deferrable=True,
            initially="DEFERRED",
            ondelete="RESTRICT",
        ),
    )
    version: Mapped[int] = mapped_column(Integer)
    content_json: Mapped[JsonArray] = mapped_column(JSONB)
    geometry_scene_version_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("geometry_scene_versions.id", ondelete="RESTRICT")
    )
    content_hash: Mapped[str] = mapped_column(String(64))
    provenance_json: Mapped[JsonObject] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Problem(Base):
    __tablename__ = "problems"
    __table_args__ = (
        CheckConstraint("status IN ('synthetic', 'withdrawn')", name="ck_problems_status"),
        Index("ix_problems_origin_cycle", "origin_exam_cycle_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    external_code: Mapped[str] = mapped_column(String(120), unique=True)
    origin_exam_cycle_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("exam_cycles.id", ondelete="RESTRICT")
    )
    year: Mapped[int | None] = mapped_column(Integer)
    problem_number: Mapped[str] = mapped_column(String(80))
    current_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey(
            "problem_versions.id",
            name="fk_problems_current_version",
            use_alter=True,
            deferrable=True,
            initially="DEFERRED",
            ondelete="RESTRICT",
        ),
    )
    status: Mapped[str] = mapped_column(String(24))


class ProblemVersion(Base):
    __tablename__ = "problem_versions"
    __table_args__ = (
        CheckConstraint("version > 0", name="ck_problem_versions_version"),
        CheckConstraint("maximum_score > 0", name="ck_problem_versions_score"),
        CheckConstraint("estimated_minutes > 0", name="ck_problem_versions_minutes"),
        CheckConstraint(
            "difficulty_band IN ('introductory', 'core', 'advanced', 'challenge')",
            name="ck_problem_versions_difficulty",
        ),
        UniqueConstraint("problem_id", "version", name="uq_problem_versions_number"),
        Index("ix_problem_versions_problem", "problem_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    problem_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey(
            "problems.id",
            name="fk_problem_versions_problem",
            deferrable=True,
            initially="DEFERRED",
            ondelete="RESTRICT",
        ),
    )
    version: Mapped[int] = mapped_column(Integer)
    statement_json: Mapped[JsonArray] = mapped_column(JSONB)
    maximum_score: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    difficulty_band: Mapped[str] = mapped_column(String(24))
    estimated_minutes: Mapped[int] = mapped_column(Integer)
    geometry_scene_version_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("geometry_scene_versions.id", ondelete="RESTRICT")
    )
    content_hash: Mapped[str] = mapped_column(String(64))
    provenance_json: Mapped[JsonObject] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ProblemExamRelevance(Base):
    __tablename__ = "problem_exam_relevance"
    __table_args__ = (
        CheckConstraint(
            "relevance_level IN ('low', 'medium', 'high')",
            name="ck_problem_exam_relevance_level",
        ),
        Index("ix_problem_exam_relevance_cycle", "exam_cycle_id", "relevance_level"),
    )

    problem_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("problem_versions.id", ondelete="RESTRICT"), primary_key=True
    )
    exam_cycle_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("exam_cycles.id", ondelete="RESTRICT"), primary_key=True
    )
    relevance_level: Mapped[str] = mapped_column(String(16))
    relevance_note: Mapped[str] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(String(64))
    provenance_json: Mapped[JsonObject] = mapped_column(JSONB)


class ProblemSkillLink(Base):
    __tablename__ = "problem_skill_links"
    __table_args__ = (
        CheckConstraint(
            "role IN ('primary', 'secondary', 'prerequisite', 'diagnostic')",
            name="ck_problem_skill_links_role",
        ),
        CheckConstraint(
            "importance > 0 AND importance <= 1", name="ck_problem_skill_links_importance"
        ),
        Index("ix_problem_skill_links_skill", "skill_id", "role"),
    )

    problem_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("problem_versions.id", ondelete="RESTRICT"), primary_key=True
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("skills.id", ondelete="RESTRICT"), primary_key=True
    )
    role: Mapped[str] = mapped_column(String(24))
    importance: Mapped[Decimal] = mapped_column(Numeric(6, 5))
    content_hash: Mapped[str] = mapped_column(String(64))
    provenance_json: Mapped[JsonObject] = mapped_column(JSONB)


class ReferenceSolution(Base):
    __tablename__ = "reference_solutions"
    __table_args__ = (
        CheckConstraint("expert_verified", name="ck_reference_solutions_verified"),
        CheckConstraint("non_exhaustive", name="ck_reference_solutions_non_exhaustive"),
        UniqueConstraint("problem_version_id", "solution_code", name="uq_reference_solutions_code"),
        Index("ix_reference_solutions_problem", "problem_version_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    problem_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("problem_versions.id", ondelete="RESTRICT")
    )
    solution_code: Mapped[str] = mapped_column(String(100))
    content_json: Mapped[JsonArray] = mapped_column(JSONB)
    method_label: Mapped[str] = mapped_column(String(200))
    expert_verified: Mapped[bool] = mapped_column(Boolean)
    non_exhaustive: Mapped[bool] = mapped_column(Boolean)
    content_hash: Mapped[str] = mapped_column(String(64))
    provenance_json: Mapped[JsonObject] = mapped_column(JSONB)


class RubricItem(Base):
    __tablename__ = "rubric_items"
    __table_args__ = (
        CheckConstraint("maximum_score > 0", name="ck_rubric_items_score"),
        CheckConstraint("order_index > 0", name="ck_rubric_items_order"),
        UniqueConstraint("problem_version_id", "rubric_code", name="uq_rubric_items_code"),
        UniqueConstraint("problem_version_id", "order_index", name="uq_rubric_items_order"),
        Index("ix_rubric_items_problem", "problem_version_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    problem_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("problem_versions.id", ondelete="RESTRICT")
    )
    rubric_code: Mapped[str] = mapped_column(String(100))
    description_json: Mapped[JsonArray] = mapped_column(JSONB)
    maximum_score: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    skill_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("skills.id", ondelete="RESTRICT"))
    order_index: Mapped[int] = mapped_column(Integer)
    content_hash: Mapped[str] = mapped_column(String(64))
    provenance_json: Mapped[JsonObject] = mapped_column(JSONB)


class ProblemHint(Base):
    __tablename__ = "problem_hints"
    __table_args__ = (
        CheckConstraint("hint_level >= 1 AND hint_level <= 5", name="ck_problem_hints_level"),
        UniqueConstraint("problem_version_id", "hint_level", name="uq_problem_hints_level"),
        Index("ix_problem_hints_problem", "problem_version_id", "hint_level"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    problem_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("problem_versions.id", ondelete="RESTRICT")
    )
    hint_level: Mapped[int] = mapped_column(Integer)
    content_json: Mapped[JsonArray] = mapped_column(JSONB)
    geometry_actions_json: Mapped[JsonArray] = mapped_column(JSONB)
    reveals_complete_solution: Mapped[bool] = mapped_column(Boolean)
    concept_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("concepts.id", ondelete="RESTRICT")
    )
    content_hash: Mapped[str] = mapped_column(String(64))
    provenance_json: Mapped[JsonObject] = mapped_column(JSONB)
