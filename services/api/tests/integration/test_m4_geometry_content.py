from datetime import timedelta
from pathlib import Path

import httpx
import pytest
from app.content.importer import import_content_package
from app.content.loader import canonical_content_hash, load_content_package
from app.content.models import ContentImport, Exam, GeometryScene, Problem, Skill
from app.content.schemas import ContentPackage
from app.database import session_factory
from app.models import PilotInvite
from app.security import digest_secret, utc_now
from sqlalchemy import func, select
from tests.fixtures.content import synthetic_content_package
from tests.fixtures.geometry import synthetic_m4_content_package

pytestmark = pytest.mark.integration

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
CONTENT_ROOT = REPOSITORY_ROOT / "content"
M4_PACKAGE_PATH = CONTENT_ROOT / "packages/synthetic-m4-geometry-v1/package.yaml"
M4_PROBLEM_ID = "40000000-0000-4000-8000-000000000700"


async def import_m2_and_m4() -> None:
    packages = [
        ContentPackage.model_validate(synthetic_content_package()),
        ContentPackage.model_validate(synthetic_m4_content_package()),
    ]
    for package in packages:
        async with session_factory() as database:
            await import_content_package(package, database)


async def add_invite(code: str) -> None:
    async with session_factory() as database:
        database.add(
            PilotInvite(
                code_digest=digest_secret(code),
                display_name="Geometry reviewer",
                max_uses=1,
                expires_at=utc_now() + timedelta(hours=1),
            )
        )
        await database.commit()


async def login(client: httpx.AsyncClient, code: str) -> None:
    response = await client.post("/api/v1/auth/pilot-login", json={"inviteCode": code})
    assert response.status_code == 200


async def test_committed_m4_package_matches_the_strict_fixture_contract() -> None:
    committed = load_content_package(M4_PACKAGE_PATH)
    expected = ContentPackage.model_validate(synthetic_m4_content_package())

    assert canonical_content_hash(committed) == canonical_content_hash(expected)
    scene = committed.geometry_scenes[0].versions[0]
    assert {item.type for item in scene.objects} == {
        "point",
        "segment",
        "line",
        "ray",
        "circle",
        "arc",
        "polygon",
        "angle",
        "midpoint",
        "intersection",
        "perpendicular",
        "parallel",
        "circumcircle",
        "label",
    }
    assert len(committed.problems[0].versions[0].exam_relevance) == 2


async def test_every_committed_scene_has_a_repository_owned_static_fallback() -> None:
    fallback_root = REPOSITORY_ROOT / "apps/student-web/public/fixtures"
    package_paths = sorted((CONTENT_ROOT / "packages").glob("*/package.yaml"))

    missing = []
    for package_path in package_paths:
        package = load_content_package(package_path)
        for scene in package.geometry_scenes:
            for version in scene.versions:
                fallback = fallback_root / f"{version.fallback_image_asset_id}.svg"
                if not fallback.is_file():
                    missing.append(str(fallback.relative_to(REPOSITORY_ROOT)))

    assert missing == []


async def test_incremental_package_import_is_idempotent_and_preserves_shared_records() -> None:
    await import_m2_and_m4()
    package = ContentPackage.model_validate(synthetic_m4_content_package())
    async with session_factory() as database:
        repeated = await import_content_package(package, database)
        receipt_count = await database.scalar(select(func.count()).select_from(ContentImport))
        exam_count = await database.scalar(select(func.count()).select_from(Exam))
        skill_count = await database.scalar(select(func.count()).select_from(Skill))
        scene_count = await database.scalar(select(func.count()).select_from(GeometryScene))
        problem_count = await database.scalar(select(func.count()).select_from(Problem))

    assert repeated.status == "already_imported"
    assert receipt_count == 2
    assert exam_count == 2
    assert skill_count == 2
    assert scene_count == 2
    assert problem_count == 2


async def test_authenticated_preview_returns_all_primitives_actions_and_two_exams(
    client: httpx.AsyncClient,
) -> None:
    await import_m2_and_m4()
    unauthenticated = await client.get(f"/api/v1/internal/content-preview/{M4_PROBLEM_ID}")
    await add_invite("M4-GEOMETRY-PREVIEW")
    await login(client, "M4-GEOMETRY-PREVIEW")
    response = await client.get(f"/api/v1/internal/content-preview/{M4_PROBLEM_ID}")

    assert unauthenticated.status_code == 401
    assert response.status_code == 200
    body = response.json()
    scene = body["geometryScene"]
    assert body["externalCode"] == "SYN-M4-GEO-001"
    assert len(body["supportedExams"]) == 2
    assert scene["fallbackImageAssetId"] == "synthetic-m4-geometry-fallback"
    assert next(item for item in scene["objects"] if item["id"] == "A")["draggable"] is True
    assert next(item for item in scene["objects"] if item["id"] == "I")["intersectionIndex"] == 0
    action_types = {action["type"] for hint in body["hints"] for action in hint["geometryActions"]}
    assert action_types == {
        "show",
        "hide",
        "highlight",
        "clear_highlight",
        "focus",
        "animate",
        "ask_select",
    }
