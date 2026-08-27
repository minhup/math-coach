import uuid
from datetime import date

from app.static_journey.planning import (
    PlanProblemInput,
    PlanTargetInput,
    build_static_daily_plan,
)

PROFILE_ID = uuid.UUID("50000000-0000-4000-8000-000000000010")
AURORA_CYCLE_ID = uuid.UUID("10000000-0000-4000-8000-000000000201")
HARBOR_CYCLE_ID = uuid.UUID("10000000-0000-4000-8000-000000000202")
AURORA_TARGET_ID = uuid.UUID("50000000-0000-4000-8000-000000000011")
HARBOR_TARGET_ID = uuid.UUID("50000000-0000-4000-8000-000000000012")


def problem(
    *,
    problem_id: str,
    version_id: str,
    external_code: str,
    relevant_cycle_ids: tuple[uuid.UUID, ...],
) -> PlanProblemInput:
    return PlanProblemInput(
        problem_id=uuid.UUID(problem_id),
        problem_version_id=uuid.UUID(version_id),
        external_code=external_code,
        version=1,
        estimated_minutes=12,
        statement=[{"id": f"{external_code}-text", "type": "text", "text": "Synthetic."}],
        geometry_scene=None,
        relevant_cycle_ids=relevant_cycle_ids,
    )


def test_static_daily_plan_is_deterministic_and_records_one_and_many_target_records() -> None:
    targets = [
        PlanTargetInput(
            target_id=HARBOR_TARGET_ID,
            exam_cycle_id=HARBOR_CYCLE_ID,
            exam_name="Synthetic Harbor Mathematics Examination",
            cycle_code="SYN-HARBOR-2027",
            priority_rank=2,
        ),
        PlanTargetInput(
            target_id=AURORA_TARGET_ID,
            exam_cycle_id=AURORA_CYCLE_ID,
            exam_name="Synthetic Aurora Mathematics Examination",
            cycle_code="SYN-AURORA-2027",
            priority_rank=1,
        ),
    ]
    problems = [
        problem(
            problem_id="10000000-0000-4000-8000-000000000700",
            version_id="10000000-0000-4000-8000-000000000701",
            external_code="SYN-M2-GEO-001",
            relevant_cycle_ids=(AURORA_CYCLE_ID, HARBOR_CYCLE_ID),
        ),
        problem(
            problem_id="40000000-0000-4000-8000-000000000700",
            version_id="40000000-0000-4000-8000-000000000701",
            external_code="SYN-M4-GEO-001",
            relevant_cycle_ids=(AURORA_CYCLE_ID, HARBOR_CYCLE_ID),
        ),
    ]

    first = build_static_daily_plan(
        profile_id=PROFILE_ID,
        plan_date=date(2026, 8, 27),
        targets=targets,
        problems=problems,
        concept_version_id=uuid.UUID("10000000-0000-4000-8000-000000000601"),
    )
    second = build_static_daily_plan(
        profile_id=PROFILE_ID,
        plan_date=date(2026, 8, 27),
        targets=list(reversed(targets)),
        problems=list(reversed(problems)),
        concept_version_id=uuid.UUID("10000000-0000-4000-8000-000000000601"),
    )

    assert first.model_dump(mode="json") == second.model_dump(mode="json")
    assert [target.target_id for target in first.targets] == [AURORA_TARGET_ID, HARBOR_TARGET_ID]
    assert [item.problem.external_code for item in first.items] == [
        "SYN-M4-GEO-001",
        "SYN-M2-GEO-001",
    ]
    assert first.items[0].supported_target_ids == [AURORA_TARGET_ID, HARBOR_TARGET_ID]
    assert first.items[1].supported_target_ids == [AURORA_TARGET_ID]
    assert first.items[0].problem.problem_version_id == uuid.UUID(
        "40000000-0000-4000-8000-000000000701"
    )
