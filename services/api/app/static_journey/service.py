import uuid
from datetime import date
from typing import cast

from pydantic import TypeAdapter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.content.models import (
    Concept,
    ConceptVersion,
    Exam,
    ExamCycle,
    GeometrySceneVersion,
    Problem,
)
from app.content.preview import content_preview
from app.content.schemas import ContentBlock
from app.content.schemas import GeometrySceneVersion as GeometrySceneVersionSchema
from app.errors import AppError
from app.models import User
from app.profile_models import StudentExamTarget
from app.profiles import owned_active_profile
from app.static_journey.planning import (
    FOLLOW_UP_PROBLEM_CODE,
    PRIMARY_PROBLEM_CODE,
    PlanProblemInput,
    PlanTargetInput,
    build_static_daily_plan,
)
from app.static_journey.schemas import (
    AvailableExamCycleListResponse,
    AvailableExamCycleResponse,
    ConceptVersionResponse,
    StaticDailyPlanResponse,
)

CONCEPT_CODE = "SYN-MIDPOINT-COORDINATES"
blocks_adapter = TypeAdapter(list[ContentBlock])
scene_adapter = TypeAdapter(GeometrySceneVersionSchema)


async def available_exam_cycles(database: AsyncSession) -> AvailableExamCycleListResponse:
    rows = (
        await database.execute(
            select(ExamCycle, Exam)
            .join(Exam, Exam.id == ExamCycle.exam_id)
            .where(ExamCycle.status == "synthetic", Exam.status == "synthetic")
            .order_by(Exam.code, ExamCycle.exam_date, ExamCycle.cycle_code)
        )
    ).all()
    return AvailableExamCycleListResponse(
        items=[
            AvailableExamCycleResponse(
                id=cast(ExamCycle, row[0]).id,
                exam_id=cast(Exam, row[1]).id,
                exam_code=cast(Exam, row[1]).code,
                exam_name=cast(Exam, row[1]).name,
                cycle_code=cast(ExamCycle, row[0]).cycle_code,
                year=cast(ExamCycle, row[0]).year,
                exam_date=cast(ExamCycle, row[0]).exam_date,
            )
            for row in rows
        ]
    )


async def static_daily_plan(
    user: User,
    database: AsyncSession,
    plan_date: date,
) -> StaticDailyPlanResponse:
    profile = await owned_active_profile(user, database)
    target_rows = (
        await database.execute(
            select(StudentExamTarget, ExamCycle, Exam)
            .join(ExamCycle, ExamCycle.id == StudentExamTarget.exam_cycle_id)
            .join(Exam, Exam.id == ExamCycle.exam_id)
            .where(
                StudentExamTarget.study_profile_id == profile.id,
                StudentExamTarget.status == "active",
                ExamCycle.status == "synthetic",
                Exam.status == "synthetic",
            )
            .order_by(StudentExamTarget.priority_rank, StudentExamTarget.id)
        )
    ).all()
    targets = [
        PlanTargetInput(
            target_id=cast(StudentExamTarget, row[0]).id,
            exam_cycle_id=cast(ExamCycle, row[1]).id,
            exam_name=cast(Exam, row[2]).name,
            cycle_code=cast(ExamCycle, row[1]).cycle_code,
            priority_rank=cast(StudentExamTarget, row[0]).priority_rank,
        )
        for row in target_rows
    ]
    if len(targets) < 2:
        raise AppError(
            status_code=409,
            code="two_active_targets_required",
            message="Add at least two active examination targets before planning.",
        )

    stored_problems = list(
        await database.scalars(
            select(Problem)
            .where(
                Problem.external_code.in_([PRIMARY_PROBLEM_CODE, FOLLOW_UP_PROBLEM_CODE]),
                Problem.status == "synthetic",
            )
            .order_by(Problem.external_code)
        )
    )
    problems: list[PlanProblemInput] = []
    for problem in stored_problems:
        preview = await content_preview(problem.id, database)
        problems.append(
            PlanProblemInput(
                problem_id=preview.problem_id,
                problem_version_id=preview.problem_version_id,
                external_code=preview.external_code,
                version=preview.version,
                estimated_minutes=preview.estimated_minutes,
                statement=list(preview.statement),
                geometry_scene=preview.geometry_scene,
                relevant_cycle_ids=tuple(
                    supported.exam_cycle_id for supported in preview.supported_exams
                ),
            )
        )

    concept_version_id = await database.scalar(
        select(Concept.current_version_id).where(
            Concept.code == CONCEPT_CODE,
            Concept.status == "synthetic",
        )
    )
    if concept_version_id is None:
        raise AppError(
            status_code=503,
            code="static_plan_unavailable",
            message="The static plan is temporarily unavailable.",
        )
    return build_static_daily_plan(
        profile_id=profile.id,
        plan_date=plan_date,
        targets=targets,
        problems=problems,
        concept_version_id=concept_version_id,
    )


async def concept_version(
    concept_version_id: uuid.UUID,
    database: AsyncSession,
) -> ConceptVersionResponse:
    row = (
        await database.execute(
            select(Concept, ConceptVersion)
            .join(ConceptVersion, ConceptVersion.concept_id == Concept.id)
            .where(
                ConceptVersion.id == concept_version_id,
                Concept.status == "synthetic",
            )
        )
    ).one_or_none()
    if row is None:
        raise AppError(
            status_code=404,
            code="concept_version_not_found",
            message="Concept version not found.",
        )
    concept = cast(Concept, row[0])
    version = cast(ConceptVersion, row[1])
    scene = None
    if version.geometry_scene_version_id is not None:
        stored_scene = await database.get(GeometrySceneVersion, version.geometry_scene_version_id)
        if stored_scene is None:
            raise RuntimeError("Stored concept version references a missing geometry scene")
        scene = scene_adapter.validate_python(stored_scene.scene_json)
    return ConceptVersionResponse(
        concept_id=concept.id,
        concept_version_id=version.id,
        code=concept.code,
        name=concept.name,
        version=version.version,
        content=blocks_adapter.validate_python(version.content_json),
        geometry_scene=scene,
    )
