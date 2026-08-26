import uuid
from typing import cast

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.content.models import Exam, ExamCycle
from app.errors import AppError
from app.models import User
from app.profile_models import StudentExamTarget, StudyProfile
from app.schemas import (
    ExamTargetCreateRequest,
    ExamTargetListResponse,
    ExamTargetPatchRequest,
    ExamTargetResponse,
    StudyProfileCreateRequest,
    StudyProfilePatchRequest,
    StudyProfileResponse,
)


async def owned_active_profile(user: User, database: AsyncSession) -> StudyProfile:
    profile = await database.scalar(
        select(StudyProfile).where(
            StudyProfile.user_id == user.id,
            StudyProfile.status == "active",
        )
    )
    if profile is None:
        raise AppError(
            status_code=404,
            code="study_profile_not_found",
            message="Study profile not found.",
        )
    return profile


def _target_status(value: str) -> str:
    if value in {"active", "completed", "archived"}:
        return value
    raise RuntimeError("Stored exam target has an invalid status")


async def target_responses(
    profile_id: uuid.UUID,
    database: AsyncSession,
) -> list[ExamTargetResponse]:
    rows = (
        await database.execute(
            select(StudentExamTarget, ExamCycle, Exam)
            .join(ExamCycle, ExamCycle.id == StudentExamTarget.exam_cycle_id)
            .join(Exam, Exam.id == ExamCycle.exam_id)
            .where(StudentExamTarget.study_profile_id == profile_id)
            .order_by(StudentExamTarget.priority_rank, StudentExamTarget.created_at)
        )
    ).all()
    return [
        ExamTargetResponse(
            id=cast(StudentExamTarget, row[0]).id,
            exam_cycle_id=cast(ExamCycle, row[1]).id,
            exam_id=cast(Exam, row[2]).id,
            exam_code=cast(Exam, row[2]).code,
            exam_name=cast(Exam, row[2]).name,
            exam_date=cast(ExamCycle, row[1]).exam_date,
            target_score=cast(StudentExamTarget, row[0]).target_score,
            priority_rank=cast(StudentExamTarget, row[0]).priority_rank,
            status=_target_status(cast(StudentExamTarget, row[0]).status),
            created_at=cast(StudentExamTarget, row[0]).created_at,
        )
        for row in rows
    ]


async def profile_response(
    profile: StudyProfile,
    database: AsyncSession,
) -> StudyProfileResponse:
    status = profile.status
    if status not in {"active", "archived"}:
        raise RuntimeError("Stored study profile has an invalid status")
    return StudyProfileResponse(
        id=profile.id,
        name=profile.name,
        weekly_study_minutes=profile.weekly_study_minutes,
        status=status,
        student_exam_targets=await target_responses(profile.id, database),
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


async def get_profile(user: User, database: AsyncSession) -> StudyProfileResponse:
    return await profile_response(await owned_active_profile(user, database), database)


async def create_profile(
    payload: StudyProfileCreateRequest,
    user: User,
    database: AsyncSession,
) -> StudyProfileResponse:
    profile = StudyProfile(
        user_id=user.id,
        name=payload.name,
        weekly_study_minutes=payload.weekly_study_minutes,
    )
    database.add(profile)
    try:
        await database.commit()
    except IntegrityError as error:
        await database.rollback()
        raise AppError(
            status_code=409,
            code="active_study_profile_exists",
            message="An active study profile already exists.",
        ) from error
    return await profile_response(profile, database)


async def patch_profile(
    payload: StudyProfilePatchRequest,
    user: User,
    database: AsyncSession,
) -> StudyProfileResponse:
    profile = await owned_active_profile(user, database)
    if payload.name is not None:
        profile.name = payload.name
    if payload.weekly_study_minutes is not None:
        profile.weekly_study_minutes = payload.weekly_study_minutes
    if payload.status is not None:
        profile.status = payload.status
    await database.commit()
    return await profile_response(profile, database)


async def list_targets(user: User, database: AsyncSession) -> ExamTargetListResponse:
    profile = await owned_active_profile(user, database)
    return ExamTargetListResponse(items=await target_responses(profile.id, database))


async def _target_response(
    target: StudentExamTarget,
    database: AsyncSession,
) -> ExamTargetResponse:
    cycle = await database.get(ExamCycle, target.exam_cycle_id)
    if cycle is None:
        raise RuntimeError("Stored exam target references a missing exam cycle")
    exam = await database.get(Exam, cycle.exam_id)
    if exam is None:
        raise RuntimeError("Stored exam cycle references a missing exam")
    return ExamTargetResponse(
        id=target.id,
        exam_cycle_id=cycle.id,
        exam_id=exam.id,
        exam_code=exam.code,
        exam_name=exam.name,
        exam_date=cycle.exam_date,
        target_score=target.target_score,
        priority_rank=target.priority_rank,
        status=_target_status(target.status),
        created_at=target.created_at,
    )


async def create_target(
    payload: ExamTargetCreateRequest,
    user: User,
    database: AsyncSession,
) -> ExamTargetResponse:
    profile = await owned_active_profile(user, database)
    cycle = await database.get(ExamCycle, payload.exam_cycle_id)
    if cycle is None or cycle.status != "synthetic":
        raise AppError(
            status_code=404,
            code="exam_cycle_not_found",
            message="Exam cycle not found.",
        )
    if payload.target_score > cycle.maximum_score:
        raise AppError(
            status_code=422,
            code="target_score_out_of_range",
            message="Target score cannot exceed the exam maximum.",
        )
    target = StudentExamTarget(
        study_profile_id=profile.id,
        exam_cycle_id=cycle.id,
        target_score=payload.target_score,
        priority_rank=payload.priority_rank,
    )
    database.add(target)
    try:
        await database.commit()
    except IntegrityError as error:
        await database.rollback()
        raise AppError(
            status_code=409,
            code="exam_target_conflict",
            message="Choose a different active exam or priority rank.",
        ) from error
    return await _target_response(target, database)


async def owned_target(
    target_id: uuid.UUID,
    user: User,
    database: AsyncSession,
) -> StudentExamTarget:
    target = await database.scalar(
        select(StudentExamTarget)
        .join(StudyProfile, StudyProfile.id == StudentExamTarget.study_profile_id)
        .where(StudentExamTarget.id == target_id, StudyProfile.user_id == user.id)
    )
    if target is None:
        raise AppError(
            status_code=404,
            code="exam_target_not_found",
            message="Exam target not found.",
        )
    return target


async def patch_target(
    target_id: uuid.UUID,
    payload: ExamTargetPatchRequest,
    user: User,
    database: AsyncSession,
) -> ExamTargetResponse:
    target = await owned_target(target_id, user, database)
    if payload.target_score is not None:
        cycle = await database.get(ExamCycle, target.exam_cycle_id)
        if cycle is None:
            raise RuntimeError("Stored exam target references a missing exam cycle")
        if payload.target_score > cycle.maximum_score:
            raise AppError(
                status_code=422,
                code="target_score_out_of_range",
                message="Target score cannot exceed the exam maximum.",
            )
        target.target_score = payload.target_score
    if payload.priority_rank is not None:
        target.priority_rank = payload.priority_rank
    if payload.status is not None:
        target.status = payload.status
    try:
        await database.commit()
    except IntegrityError as error:
        await database.rollback()
        raise AppError(
            status_code=409,
            code="exam_target_conflict",
            message="Choose a different active exam or priority rank.",
        ) from error
    return await _target_response(target, database)


async def archive_target(
    target_id: uuid.UUID,
    user: User,
    database: AsyncSession,
) -> None:
    target = await owned_target(target_id, user, database)
    target.status = "archived"
    await database.commit()
