import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class StudyProfile(Base):
    __tablename__ = "study_profiles"
    __table_args__ = (
        CheckConstraint("weekly_study_minutes > 0", name="ck_study_profiles_weekly_minutes"),
        CheckConstraint("status IN ('active', 'archived')", name="ck_study_profiles_status"),
        Index(
            "uq_study_profiles_user_active",
            "user_id",
            unique=True,
            postgresql_where=text("status = 'active'"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(120))
    weekly_study_minutes: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(24), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class StudentExamTarget(Base):
    __tablename__ = "student_exam_targets"
    __table_args__ = (
        CheckConstraint("target_score >= 0", name="ck_student_exam_targets_score"),
        CheckConstraint("priority_rank > 0", name="ck_student_exam_targets_priority"),
        CheckConstraint(
            "status IN ('active', 'completed', 'archived')",
            name="ck_student_exam_targets_status",
        ),
        Index(
            "uq_student_exam_targets_active_priority",
            "study_profile_id",
            "priority_rank",
            unique=True,
            postgresql_where=text("status = 'active'"),
        ),
        Index(
            "uq_student_exam_targets_active_cycle",
            "study_profile_id",
            "exam_cycle_id",
            unique=True,
            postgresql_where=text("status = 'active'"),
        ),
        Index("ix_student_exam_targets_profile_status", "study_profile_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    study_profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("study_profiles.id", ondelete="CASCADE")
    )
    exam_cycle_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("exam_cycles.id", ondelete="RESTRICT")
    )
    target_score: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    priority_rank: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(24), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
