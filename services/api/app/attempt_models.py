import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class Attempt(Base):
    __tablename__ = "attempts"
    __table_args__ = (
        CheckConstraint("status IN ('draft', 'submitted')", name="ck_attempts_status"),
        Index("ix_attempts_profile_created", "study_profile_id", "created_at"),
        Index("ix_attempts_problem_version", "problem_version_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    study_profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("study_profiles.id", ondelete="RESTRICT")
    )
    problem_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("problem_versions.id", ondelete="RESTRICT")
    )
    status: Mapped[str] = mapped_column(String(24), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
