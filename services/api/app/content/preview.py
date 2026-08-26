import uuid
from typing import cast

from pydantic import TypeAdapter
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.content.models import (
    Exam,
    ExamCycle,
    GeometrySceneVersion,
    Problem,
    ProblemExamRelevance,
    ProblemHint,
    ProblemSkillLink,
    ProblemVersion,
    ReferenceSolution,
    RubricItem,
    Skill,
)
from app.content.preview_schemas import (
    ContentPreviewListResponse,
    ContentPreviewResponse,
    ContentPreviewSummary,
    PreviewExamRelevance,
    PreviewHint,
    PreviewReferenceSolution,
    PreviewRubricItem,
    PreviewSkillLink,
)
from app.content.schemas import (
    ContentBlock,
    GeometryAction,
    Provenance,
)
from app.content.schemas import (
    GeometrySceneVersion as GeometrySceneVersionSchema,
)
from app.errors import AppError

blocks_adapter = TypeAdapter(list[ContentBlock])
actions_adapter = TypeAdapter(list[GeometryAction])
scene_adapter = TypeAdapter(GeometrySceneVersionSchema)
provenance_adapter = TypeAdapter(Provenance)


async def list_content_previews(database: AsyncSession) -> ContentPreviewListResponse:
    rows = (
        await database.execute(
            select(
                Problem,
                ProblemVersion,
                func.count(ProblemExamRelevance.exam_cycle_id),
            )
            .join(ProblemVersion, ProblemVersion.id == Problem.current_version_id)
            .join(
                ProblemExamRelevance,
                ProblemExamRelevance.problem_version_id == ProblemVersion.id,
            )
            .where(Problem.status == "synthetic")
            .group_by(Problem.id, ProblemVersion.id)
            .order_by(Problem.external_code)
        )
    ).all()
    return ContentPreviewListResponse(
        items=[
            ContentPreviewSummary(
                problem_id=cast(Problem, row[0]).id,
                problem_version_id=cast(ProblemVersion, row[1]).id,
                external_code=cast(Problem, row[0]).external_code,
                version=cast(ProblemVersion, row[1]).version,
                supported_exam_count=cast(int, row[2]),
            )
            for row in rows
        ]
    )


async def content_preview(
    problem_id: uuid.UUID,
    database: AsyncSession,
) -> ContentPreviewResponse:
    row = (
        await database.execute(
            select(Problem, ProblemVersion)
            .join(ProblemVersion, ProblemVersion.id == Problem.current_version_id)
            .where(Problem.id == problem_id, Problem.status == "synthetic")
        )
    ).one_or_none()
    if row is None:
        raise AppError(
            status_code=404,
            code="content_preview_not_found",
            message="Content preview not found.",
        )
    problem = cast(Problem, row[0])
    version = cast(ProblemVersion, row[1])

    exam_rows = (
        await database.execute(
            select(ProblemExamRelevance, ExamCycle, Exam)
            .join(ExamCycle, ExamCycle.id == ProblemExamRelevance.exam_cycle_id)
            .join(Exam, Exam.id == ExamCycle.exam_id)
            .where(ProblemExamRelevance.problem_version_id == version.id)
            .order_by(Exam.code)
        )
    ).all()
    skill_rows = (
        await database.execute(
            select(ProblemSkillLink, Skill)
            .join(Skill, Skill.id == ProblemSkillLink.skill_id)
            .where(ProblemSkillLink.problem_version_id == version.id)
            .order_by(ProblemSkillLink.importance.desc(), Skill.code)
        )
    ).all()
    solutions = list(
        await database.scalars(
            select(ReferenceSolution)
            .where(ReferenceSolution.problem_version_id == version.id)
            .order_by(ReferenceSolution.solution_code)
        )
    )
    rubric = list(
        await database.scalars(
            select(RubricItem)
            .where(RubricItem.problem_version_id == version.id)
            .order_by(RubricItem.order_index)
        )
    )
    hints = list(
        await database.scalars(
            select(ProblemHint)
            .where(ProblemHint.problem_version_id == version.id)
            .order_by(ProblemHint.hint_level)
        )
    )
    scene: GeometrySceneVersionSchema | None = None
    if version.geometry_scene_version_id is not None:
        stored_scene = await database.get(GeometrySceneVersion, version.geometry_scene_version_id)
        if stored_scene is None:
            raise RuntimeError("Stored problem version references a missing geometry scene")
        scene = scene_adapter.validate_python(stored_scene.scene_json)

    return ContentPreviewResponse(
        problem_id=problem.id,
        problem_version_id=version.id,
        external_code=problem.external_code,
        version=version.version,
        statement=blocks_adapter.validate_python(version.statement_json),
        maximum_score=version.maximum_score,
        difficulty_band=version.difficulty_band,
        estimated_minutes=version.estimated_minutes,
        supported_exams=[
            PreviewExamRelevance(
                exam_cycle_id=cast(ExamCycle, exam_row[1]).id,
                exam_id=cast(Exam, exam_row[2]).id,
                exam_code=cast(Exam, exam_row[2]).code,
                exam_name=cast(Exam, exam_row[2]).name,
                cycle_code=cast(ExamCycle, exam_row[1]).cycle_code,
                exam_date=cast(ExamCycle, exam_row[1]).exam_date,
                relevance_level=cast(ProblemExamRelevance, exam_row[0]).relevance_level,
                relevance_note=cast(ProblemExamRelevance, exam_row[0]).relevance_note,
            )
            for exam_row in exam_rows
        ],
        skills=[
            PreviewSkillLink(
                skill_id=cast(Skill, skill_row[1]).id,
                skill_code=cast(Skill, skill_row[1]).code,
                skill_name=cast(Skill, skill_row[1]).name,
                role=cast(ProblemSkillLink, skill_row[0]).role,
                importance=cast(ProblemSkillLink, skill_row[0]).importance,
            )
            for skill_row in skill_rows
        ],
        reference_solutions=[
            PreviewReferenceSolution(
                id=solution.id,
                solution_code=solution.solution_code,
                method_label=solution.method_label,
                content=blocks_adapter.validate_python(solution.content_json),
                expert_verified=solution.expert_verified,
                non_exhaustive=solution.non_exhaustive,
            )
            for solution in solutions
        ],
        rubric=[
            PreviewRubricItem(
                id=item.id,
                rubric_code=item.rubric_code,
                description=blocks_adapter.validate_python(item.description_json),
                maximum_score=item.maximum_score,
                skill_id=item.skill_id,
                order_index=item.order_index,
            )
            for item in rubric
        ],
        hints=[
            PreviewHint(
                id=hint.id,
                hint_level=hint.hint_level,
                content=blocks_adapter.validate_python(hint.content_json),
                geometry_actions=actions_adapter.validate_python(hint.geometry_actions_json),
                reveals_complete_solution=hint.reveals_complete_solution,
                concept_id=hint.concept_id,
            )
            for hint in hints
        ],
        geometry_scene=scene,
        provenance=provenance_adapter.validate_python(version.provenance_json),
    )
