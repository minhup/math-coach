import json
import uuid
from dataclasses import dataclass
from datetime import date

from pydantic import TypeAdapter

from app.content.schemas import ContentBlock
from app.content.schemas import GeometrySceneVersion as GeometrySceneVersionSchema
from app.static_journey.schemas import (
    StaticDailyPlanResponse,
    StaticPlanItem,
    StaticPlanTarget,
    StudentProblemContent,
)

PRIMARY_PROBLEM_CODE = "SYN-M4-GEO-001"
FOLLOW_UP_PROBLEM_CODE = "SYN-M2-GEO-001"
PLAN_NAMESPACE = uuid.UUID("50000000-0000-4000-8000-000000000500")

blocks_adapter = TypeAdapter(list[ContentBlock])
scene_adapter = TypeAdapter(GeometrySceneVersionSchema)


@dataclass(frozen=True)
class PlanTargetInput:
    target_id: uuid.UUID
    exam_cycle_id: uuid.UUID
    exam_name: str
    cycle_code: str
    priority_rank: int


@dataclass(frozen=True)
class PlanProblemInput:
    problem_id: uuid.UUID
    problem_version_id: uuid.UUID
    external_code: str
    version: int
    estimated_minutes: int
    statement: list[object]
    geometry_scene: object | None
    relevant_cycle_ids: tuple[uuid.UUID, ...]


def _problem_content(problem: PlanProblemInput) -> StudentProblemContent:
    scene = None
    if problem.geometry_scene is not None:
        scene = scene_adapter.validate_python(problem.geometry_scene)
    return StudentProblemContent(
        problem_id=problem.problem_id,
        problem_version_id=problem.problem_version_id,
        external_code=problem.external_code,
        version=problem.version,
        estimated_minutes=problem.estimated_minutes,
        statement=blocks_adapter.validate_python(problem.statement),
        geometry_scene=scene,
    )


def build_static_daily_plan(
    *,
    profile_id: uuid.UUID,
    plan_date: date,
    targets: list[PlanTargetInput],
    problems: list[PlanProblemInput],
    concept_version_id: uuid.UUID,
) -> StaticDailyPlanResponse:
    ordered_targets = sorted(targets, key=lambda item: (item.priority_rank, str(item.target_id)))
    problems_by_code = {problem.external_code: problem for problem in problems}
    items: list[StaticPlanItem] = []

    primary = problems_by_code.get(PRIMARY_PROBLEM_CODE)
    if primary is not None:
        supported = [
            target.target_id
            for target in ordered_targets
            if target.exam_cycle_id in primary.relevant_cycle_ids
        ]
        if supported:
            items.append(
                StaticPlanItem(
                    position=len(items) + 1,
                    problem=_problem_content(primary),
                    supported_target_ids=supported,
                    selection_reason="shared_target_foundation",
                    concept_version_id=concept_version_id,
                )
            )

    follow_up = problems_by_code.get(FOLLOW_UP_PROBLEM_CODE)
    if follow_up is not None:
        supported = next(
            (
                [target.target_id]
                for target in ordered_targets
                if target.exam_cycle_id in follow_up.relevant_cycle_ids
            ),
            [],
        )
        if supported:
            items.append(
                StaticPlanItem(
                    position=len(items) + 1,
                    problem=_problem_content(follow_up),
                    supported_target_ids=supported,
                    selection_reason="priority_target_follow_up",
                    concept_version_id=concept_version_id,
                )
            )

    canonical_inputs = json.dumps(
        {
            "date": plan_date.isoformat(),
            "items": [str(item.problem.problem_version_id) for item in items],
            "profileId": str(profile_id),
            "targets": [str(target.target_id) for target in ordered_targets],
        },
        separators=(",", ":"),
        sort_keys=True,
    )
    return StaticDailyPlanResponse(
        schema_version="1.0.0",
        plan_id=uuid.uuid5(PLAN_NAMESPACE, canonical_inputs),
        plan_date=plan_date,
        profile_id=profile_id,
        targets=[
            StaticPlanTarget(
                target_id=target.target_id,
                exam_cycle_id=target.exam_cycle_id,
                exam_name=target.exam_name,
                cycle_code=target.cycle_code,
                priority_rank=target.priority_rank,
            )
            for target in ordered_targets
        ],
        items=items,
    )
