from datetime import timedelta
from pathlib import Path
from uuid import uuid4

import httpx
import pytest
from app.content.importer import ContentImportError, import_content_package
from app.content.models import (
    ContentImport,
    Exam,
    Problem,
    ProblemExamRelevance,
    ProblemVersion,
    Skill,
)
from app.content.schemas import ContentPackage
from app.database import session_factory
from app.main import app
from app.models import PilotInvite
from app.scripts.seed_content import seed_content
from app.security import digest_secret, utc_now
from sqlalchemy import func, select, text
from sqlalchemy.exc import DBAPIError
from tests.fixtures.content import synthetic_content_package

pytestmark = pytest.mark.integration

FIRST_CYCLE_ID = "10000000-0000-4000-8000-000000000201"
SECOND_CYCLE_ID = "10000000-0000-4000-8000-000000000202"
PROBLEM_ID = "10000000-0000-4000-8000-000000000700"
PROBLEM_VERSION_ID = "10000000-0000-4000-8000-000000000701"
CONTENT_ROOT = Path(__file__).resolve().parents[4] / "content"


async def seed_synthetic_content() -> None:
    package = ContentPackage.model_validate(synthetic_content_package())
    async with session_factory() as database:
        await import_content_package(package, database)


async def add_invite(code: str, display_name: str) -> None:
    async with session_factory() as database:
        database.add(
            PilotInvite(
                code_digest=digest_secret(code),
                display_name=display_name,
                max_uses=1,
                expires_at=utc_now() + timedelta(hours=1),
            )
        )
        await database.commit()


async def login(client: httpx.AsyncClient, code: str) -> None:
    response = await client.post("/api/v1/auth/pilot-login", json={"inviteCode": code})
    assert response.status_code == 200


async def test_content_import_is_idempotent_and_preserves_multi_exam_links() -> None:
    package = ContentPackage.model_validate(synthetic_content_package())

    async with session_factory() as database:
        first = await import_content_package(package, database)
    async with session_factory() as database:
        second = await import_content_package(package, database)
        relevance_count = await database.scalar(
            select(func.count()).select_from(ProblemExamRelevance)
        )
        skill_count = await database.scalar(select(func.count()).select_from(Skill))

    assert first.status == "imported"
    assert second.status == "already_imported"
    assert second.content_hash == first.content_hash
    assert relevance_count == 2
    assert skill_count == 2


def _replace_value(value, replacements: dict[str, str]):
    if isinstance(value, dict):
        return {key: _replace_value(item, replacements) for key, item in value.items()}
    if isinstance(value, list):
        return [_replace_value(item, replacements) for item in value]
    if isinstance(value, str):
        return replacements.get(value, value)
    return value


async def test_conflicting_import_rolls_back_every_row_and_receipt() -> None:
    await seed_synthetic_content()
    conflicting = synthetic_content_package()
    replacements = {
        conflicting["packageId"]: str(uuid4()),
        conflicting["exams"][0]["id"]: str(uuid4()),
        conflicting["exams"][1]["id"]: str(uuid4()),
        conflicting["examCycles"][0]["id"]: str(uuid4()),
        conflicting["examCycles"][1]["id"]: str(uuid4()),
        "SYN-AURORA": "SYN-AURORA-CONFLICT",
        "SYN-HARBOR": "SYN-HARBOR-CONFLICT",
        "SYN-AURORA-2027": "SYN-AURORA-CONFLICT-2027",
        "SYN-HARBOR-2027": "SYN-HARBOR-CONFLICT-2027",
    }
    conflicting = _replace_value(conflicting, replacements)
    package = ContentPackage.model_validate(conflicting)

    async with session_factory() as database:
        with pytest.raises(ContentImportError, match="conflicts with an existing"):
            await import_content_package(package, database)

    async with session_factory() as database:
        exam_count = await database.scalar(select(func.count()).select_from(Exam))
        receipt_count = await database.scalar(select(func.count()).select_from(ContentImport))

    assert exam_count == 2
    assert receipt_count == 1


async def test_new_package_can_add_a_version_without_rewriting_the_old_version() -> None:
    await seed_synthetic_content()
    second_package = synthetic_content_package()
    second_package["packageId"] = str(uuid4())
    second_package["packageVersion"] = 2
    problem = second_package["problems"][0]
    old_version = problem["versions"][0]
    new_version = _replace_value(old_version, {})
    new_version["id"] = str(uuid4())
    new_version["version"] = 2
    new_version["statement"][1]["text"] = (
        "Find the squared length CM² and give a complete justification."
    )
    new_version["provenance"]["title"] = "Synthetic coordinate geometry problem version 2"
    for solution in new_version["referenceSolutions"]:
        solution["id"] = str(uuid4())
    for rubric in new_version["rubric"]:
        rubric["id"] = str(uuid4())
    for hint in new_version["hints"]:
        hint["id"] = str(uuid4())
    problem["versions"].append(new_version)
    problem["currentVersionId"] = new_version["id"]
    package = ContentPackage.model_validate(second_package)

    async with session_factory() as database:
        result = await import_content_package(package, database)
    async with session_factory() as database:
        stored_problem = await database.get(Problem, problem["id"])
        version_count = await database.scalar(select(func.count()).select_from(ProblemVersion))

    assert result.status == "imported"
    assert stored_problem is not None
    assert str(stored_problem.current_version_id) == new_version["id"]
    assert version_count == 2


async def test_seed_command_is_deterministic_and_idempotent() -> None:
    await seed_content(CONTENT_ROOT)
    await seed_content(CONTENT_ROOT)

    async with session_factory() as database:
        receipt_count = await database.scalar(select(func.count()).select_from(ContentImport))
        exam_count = await database.scalar(select(func.count()).select_from(Exam))

    assert receipt_count == 2
    assert exam_count == 2


@pytest.mark.parametrize(
    ("table_name", "row_id"),
    [
        ("geometry_scene_versions", "10000000-0000-4000-8000-000000000501"),
        ("concept_versions", "10000000-0000-4000-8000-000000000601"),
        ("problem_versions", PROBLEM_VERSION_ID),
    ],
)
async def test_database_rejects_immutable_content_version_updates_and_deletes(
    table_name: str,
    row_id: str,
) -> None:
    await seed_synthetic_content()
    for statement in (
        f"UPDATE {table_name} SET content_hash = repeat('0', 64) WHERE id = :row_id",
        f"DELETE FROM {table_name} WHERE id = :row_id",
    ):
        async with session_factory() as database:
            with pytest.raises(DBAPIError, match="immutable content rows"):
                await database.execute(text(statement), {"row_id": row_id})
                await database.commit()
            await database.rollback()


async def test_migration_exposes_attempt_version_fk_and_immutable_triggers() -> None:
    async with session_factory() as database:
        attempt_column = await database.scalar(
            text(
                "SELECT is_nullable FROM information_schema.columns "
                "WHERE table_schema = 'public' AND table_name = 'attempts' "
                "AND column_name = 'problem_version_id'"
            )
        )
        target_columns = list(
            await database.scalars(
                text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_schema = 'public' AND table_name = 'student_exam_targets'"
                )
            )
        )
        trigger_count = await database.scalar(
            text(
                "SELECT count(*) FROM pg_trigger "
                "WHERE NOT tgisinternal AND tgname LIKE 'trg_%_immutable'"
            )
        )

    assert attempt_column == "NO"
    assert "exam_cycle_id" in target_columns
    assert "target_exam_id" not in target_columns
    assert trigger_count == 9


async def test_content_preview_requires_authentication_and_shows_two_supported_exams(
    client: httpx.AsyncClient,
) -> None:
    await seed_synthetic_content()

    unauthenticated = await client.get("/api/v1/internal/content-preview")
    await add_invite("PREVIEW-INTERNAL", "Preview reviewer")
    await login(client, "PREVIEW-INTERNAL")
    listing = await client.get("/api/v1/internal/content-preview")
    detail = await client.get(f"/api/v1/internal/content-preview/{PROBLEM_ID}")

    assert unauthenticated.status_code == 401
    assert listing.status_code == 200
    assert listing.json()["items"] == [
        {
            "problemId": PROBLEM_ID,
            "problemVersionId": PROBLEM_VERSION_ID,
            "externalCode": "SYN-M2-GEO-001",
            "version": 1,
            "supportedExamCount": 2,
        }
    ]
    body = detail.json()
    assert detail.status_code == 200
    assert [exam["examCode"] for exam in body["supportedExams"]] == [
        "SYN-AURORA",
        "SYN-HARBOR",
    ]
    assert body["referenceSolutions"][0]["nonExhaustive"] is True
    assert len(body["hints"]) == 5
    assert body["geometryScene"]["fallbackImageAssetId"]
    assert body["provenance"]["sourceKind"] == "original_synthetic"


async def test_all_milestone_two_user_and_preview_routes_require_authentication(
    client: httpx.AsyncClient,
) -> None:
    responses = [
        await client.get("/api/v1/study-profile"),
        await client.post(
            "/api/v1/study-profile",
            json={"name": "Unauthorized", "weeklyStudyMinutes": 120},
        ),
        await client.get("/api/v1/exam-targets"),
        await client.post(
            "/api/v1/exam-targets",
            json={"examCycleId": FIRST_CYCLE_ID, "targetScore": "10.00", "priorityRank": 1},
        ),
        await client.post(
            "/api/v1/attempts",
            json={"problemVersionId": PROBLEM_VERSION_ID},
        ),
        await client.get(f"/api/v1/internal/content-preview/{PROBLEM_ID}"),
    ]

    assert {response.status_code for response in responses} == {401}


async def test_one_profile_can_hold_two_active_exam_targets_without_cross_user_access(
    client: httpx.AsyncClient,
) -> None:
    await seed_synthetic_content()
    await add_invite("PROFILE-OWNER", "Profile owner")
    await add_invite("PROFILE-OTHER", "Other learner")
    await login(client, "PROFILE-OWNER")

    created_profile = await client.post(
        "/api/v1/study-profile",
        json={"name": "Synthetic preparation", "weeklyStudyMinutes": 240},
    )
    first = await client.post(
        "/api/v1/exam-targets",
        json={"examCycleId": FIRST_CYCLE_ID, "targetScore": "16.00", "priorityRank": 1},
    )
    second = await client.post(
        "/api/v1/exam-targets",
        json={"examCycleId": SECOND_CYCLE_ID, "targetScore": "15.00", "priorityRank": 2},
    )
    profile = await client.get("/api/v1/study-profile")
    conflicting_rank = await client.post(
        "/api/v1/exam-targets",
        json={"examCycleId": FIRST_CYCLE_ID, "targetScore": "12.00", "priorityRank": 2},
    )

    assert created_profile.status_code == 201
    assert first.status_code == 201
    assert second.status_code == 201
    assert conflicting_rank.status_code == 409
    assert len(profile.json()["studentExamTargets"]) == 2
    assert "targetExamId" not in profile.json()
    assert {target["examCode"] for target in profile.json()["studentExamTargets"]} == {
        "SYN-AURORA",
        "SYN-HARBOR",
    }

    other_client = httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    )
    try:
        await login(other_client, "PROFILE-OTHER")
        hidden_profile = await other_client.get("/api/v1/study-profile")
        hidden_target = await other_client.patch(
            f"/api/v1/exam-targets/{first.json()['id']}",
            json={"priorityRank": 3},
        )
    finally:
        await other_client.aclose()

    assert hidden_profile.status_code == 404
    assert hidden_target.status_code == 404


async def test_attempt_api_requires_an_owned_profile_and_exact_problem_version(
    client: httpx.AsyncClient,
) -> None:
    await seed_synthetic_content()
    await add_invite("ATTEMPT-OWNER", "Attempt owner")
    await add_invite("ATTEMPT-OTHER", "Attempt other")
    await login(client, "ATTEMPT-OWNER")
    profile = await client.post(
        "/api/v1/study-profile",
        json={"name": "Attempt preparation", "weeklyStudyMinutes": 180},
    )

    created = await client.post(
        "/api/v1/attempts",
        json={"problemVersionId": PROBLEM_VERSION_ID},
    )
    attempt_id = created.json().get("id")
    fetched = await client.get(f"/api/v1/attempts/{attempt_id}")
    unknown = await client.post(
        "/api/v1/attempts",
        json={"problemVersionId": "20000000-0000-4000-8000-000000000001"},
    )

    async with session_factory() as database:
        old_version = await database.get(ProblemVersion, PROBLEM_VERSION_ID)
        stored_problem = await database.get(Problem, PROBLEM_ID)
        assert old_version is not None
        assert stored_problem is not None
        next_version_id = uuid4()
        database.add(
            ProblemVersion(
                id=next_version_id,
                problem_id=stored_problem.id,
                version=2,
                statement_json=old_version.statement_json,
                maximum_score=old_version.maximum_score,
                difficulty_band=old_version.difficulty_band,
                estimated_minutes=old_version.estimated_minutes,
                geometry_scene_version_id=old_version.geometry_scene_version_id,
                content_hash="f" * 64,
                provenance_json=old_version.provenance_json,
            )
        )
        await database.flush()
        stored_problem.current_version_id = next_version_id
        await database.commit()
    pinned_prior_version = await client.post(
        "/api/v1/attempts",
        json={"problemVersionId": PROBLEM_VERSION_ID},
    )

    assert profile.status_code == 201
    assert created.status_code == 201
    assert created.json()["problemVersionId"] == PROBLEM_VERSION_ID
    assert fetched.json() == created.json()
    assert unknown.status_code == 404
    assert pinned_prior_version.status_code == 201
    assert pinned_prior_version.json()["problemVersionId"] == PROBLEM_VERSION_ID

    other_client = httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    )
    try:
        await login(other_client, "ATTEMPT-OTHER")
        hidden = await other_client.get(f"/api/v1/attempts/{attempt_id}")
    finally:
        await other_client.aclose()
    assert hidden.status_code == 404
