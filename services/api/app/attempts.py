import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.attempt_models import Attempt
from app.content.models import Problem, ProblemVersion
from app.errors import AppError
from app.models import User
from app.profile_models import StudyProfile
from app.profiles import owned_active_profile
from app.schemas import AttemptCreateRequest, AttemptResponse


def attempt_response(attempt: Attempt) -> AttemptResponse:
    if attempt.status not in {"draft", "submitted"}:
        raise RuntimeError("Stored attempt has an invalid status")
    return AttemptResponse(
        id=attempt.id,
        study_profile_id=attempt.study_profile_id,
        problem_version_id=attempt.problem_version_id,
        status=attempt.status,
        created_at=attempt.created_at,
    )


async def create_attempt(
    payload: AttemptCreateRequest,
    user: User,
    database: AsyncSession,
) -> AttemptResponse:
    profile = await owned_active_profile(user, database)
    problem_version = await database.scalar(
        select(ProblemVersion)
        .join(Problem, Problem.id == ProblemVersion.problem_id)
        .where(
            ProblemVersion.id == payload.problem_version_id,
            Problem.status == "synthetic",
        )
    )
    if problem_version is None:
        raise AppError(
            status_code=404,
            code="problem_version_not_found",
            message="Problem version not found.",
        )
    attempt = Attempt(
        study_profile_id=profile.id,
        problem_version_id=problem_version.id,
    )
    database.add(attempt)
    await database.commit()
    return attempt_response(attempt)


async def owned_attempt(
    attempt_id: uuid.UUID,
    user: User,
    database: AsyncSession,
) -> Attempt:
    attempt = await database.scalar(
        select(Attempt)
        .join(StudyProfile, StudyProfile.id == Attempt.study_profile_id)
        .where(Attempt.id == attempt_id, StudyProfile.user_id == user.id)
    )
    if attempt is None:
        raise AppError(
            status_code=404,
            code="attempt_not_found",
            message="Attempt not found.",
        )
    return attempt
