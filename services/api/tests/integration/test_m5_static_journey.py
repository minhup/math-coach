from datetime import timedelta
from pathlib import Path

import httpx
import pytest

from app.database import session_factory
from app.main import app
from app.models import PilotInvite
from app.scripts.seed_content import seed_content
from app.security import digest_secret, utc_now
from app.static_journey.mocks import (
    DeterministicMockBoundary,
    FailedFixtureSource,
    UncertainFixtureSource,
    get_mock_boundary,
)

pytestmark = pytest.mark.integration

CONTENT_ROOT = Path(__file__).resolve().parents[4] / "content"
AURORA_CYCLE_ID = "10000000-0000-4000-8000-000000000201"
HARBOR_CYCLE_ID = "10000000-0000-4000-8000-000000000202"
M4_PROBLEM_VERSION_ID = "40000000-0000-4000-8000-000000000701"
CONCEPT_VERSION_ID = "10000000-0000-4000-8000-000000000601"


async def add_invite(code: str) -> None:
    async with session_factory() as database:
        database.add(
            PilotInvite(
                code_digest=digest_secret(code),
                display_name="Synthetic M5 learner",
                max_uses=1,
                expires_at=utc_now() + timedelta(hours=1),
            )
        )
        await database.commit()


async def login(client: httpx.AsyncClient, code: str) -> None:
    response = await client.post("/api/v1/auth/pilot-login", json={"inviteCode": code})
    assert response.status_code == 200


async def create_profile_with_two_targets(client: httpx.AsyncClient) -> list[dict[str, object]]:
    profile = await client.post(
        "/api/v1/study-profile",
        json={"name": "Synthetic M5 preparation", "weeklyStudyMinutes": 240},
    )
    assert profile.status_code == 201
    targets = []
    for rank, cycle_id in enumerate((AURORA_CYCLE_ID, HARBOR_CYCLE_ID), start=1):
        target = await client.post(
            "/api/v1/exam-targets",
            json={"examCycleId": cycle_id, "targetScore": "16.00", "priorityRank": rank},
        )
        assert target.status_code == 201
        targets.append(target.json())
    return targets


async def test_authenticated_static_plan_is_deterministic_and_explicitly_multi_target(
    client: httpx.AsyncClient,
) -> None:
    await seed_content(CONTENT_ROOT)
    await add_invite("M5-PLAN")

    unauthorized_cycles = await client.get("/api/v1/exam-cycles")
    unauthorized_plan = await client.get("/api/v1/plans/today")
    await login(client, "M5-PLAN")
    targets = await create_profile_with_two_targets(client)

    cycles = await client.get("/api/v1/exam-cycles")
    first = await client.get("/api/v1/plans/today")
    second = await client.get("/api/v1/plans/today")

    assert unauthorized_cycles.status_code == 401
    assert unauthorized_plan.status_code == 401
    assert [item["cycleCode"] for item in cycles.json()["items"]] == [
        "SYN-AURORA-2027",
        "SYN-HARBOR-2027",
    ]
    assert first.status_code == 200
    assert first.json() == second.json()
    body = first.json()
    target_ids = [target["id"] for target in targets]
    assert [item["problem"]["externalCode"] for item in body["items"]] == [
        "SYN-M4-GEO-001",
        "SYN-M2-GEO-001",
    ]
    assert body["items"][0]["supportedTargetIds"] == target_ids
    assert body["items"][1]["supportedTargetIds"] == [target_ids[0]]
    assert body["items"][0]["problem"]["problemVersionId"] == M4_PROBLEM_VERSION_ID
    assert "referenceSolutions" not in body["items"][0]["problem"]
    assert "rubric" not in body["items"][0]["problem"]


async def test_static_plan_requires_two_active_target_records(
    client: httpx.AsyncClient,
) -> None:
    await seed_content(CONTENT_ROOT)
    await add_invite("M5-TWO-TARGETS")
    await login(client, "M5-TWO-TARGETS")
    await client.post(
        "/api/v1/study-profile",
        json={"name": "Synthetic M5 preparation", "weeklyStudyMinutes": 240},
    )
    await client.post(
        "/api/v1/exam-targets",
        json={
            "examCycleId": AURORA_CYCLE_ID,
            "targetScore": "16.00",
            "priorityRank": 1,
        },
    )

    response = await client.get("/api/v1/plans/today")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "two_active_targets_required"


async def test_owned_attempt_upload_confirmation_hint_retry_and_concept_form_one_typed_boundary(
    client: httpx.AsyncClient,
) -> None:
    await seed_content(CONTENT_ROOT)
    await add_invite("M5-JOURNEY")
    await login(client, "M5-JOURNEY")
    await create_profile_with_two_targets(client)
    attempt = await client.post(
        "/api/v1/attempts",
        json={"problemVersionId": M4_PROBLEM_VERSION_ID},
    )
    attempt_id = attempt.json()["id"]

    image_bytes = b"\x89PNG\r\n\x1a\nsynthetic-m5-only"
    signed = await client.post(
        "/api/v1/uploads/presign",
        json={
            "contentType": "image/png",
            "fileName": "synthetic-m5-solution.png",
            "sizeBytes": len(image_bytes),
        },
    )
    async with httpx.AsyncClient() as storage_client:
        stored = await storage_client.put(
            signed.json()["uploadUrl"],
            content=image_bytes,
            headers={"Content-Type": "image/png"},
        )
    completed = await client.post(f"/api/v1/uploads/{signed.json()['uploadId']}/complete")

    transcription = await client.post(
        f"/api/v1/attempts/{attempt_id}/mock-transcription",
        json={"uploadId": completed.json()["id"]},
    )
    transcript = transcription.json()["transcript"]
    unconfirmed = await client.post(
        f"/api/v1/attempts/{attempt_id}/mock-evaluation",
        json={"transcript": transcript},
    )
    transcript["blocks"][0]["text"] += " Corrected by the synthetic learner."
    evaluation = await client.post(
        f"/api/v1/attempts/{attempt_id}/mock-evaluation",
        json={
            "confirmedTranscript": {
                "confirmationStatus": "confirmed",
                "transcript": transcript,
            }
        },
    )
    hint = await client.post(
        f"/api/v1/attempts/{attempt_id}/hints/next",
        json={"previousHintLevel": 0},
    )
    second_hint = await client.post(
        f"/api/v1/attempts/{attempt_id}/hints/next",
        json={"previousHintLevel": 1},
    )
    concept = await client.get(f"/api/v1/concept-versions/{CONCEPT_VERSION_ID}")
    retry = await client.post(
        "/api/v1/attempts",
        json={"problemVersionId": M4_PROBLEM_VERSION_ID},
    )

    assert stored.status_code == 200
    assert completed.json()["status"] == "ready"
    assert transcription.status_code == 200
    assert transcript["attemptId"] == attempt_id
    assert transcription.json()["metadata"]["provider"] == "application-owned-synthetic-mock"
    assert unconfirmed.status_code == 422
    assert evaluation.status_code == 200
    assert evaluation.json()["outcome"] == "ready"
    assert evaluation.json()["referenceSolutionsNonExhaustive"] is True
    assert len(evaluation.json()["transcriptFingerprint"]) == 64
    assert hint.status_code == 200
    assert hint.json()["hintLevel"] == 1
    assert hint.json()["geometryActions"][0]["type"] == "highlight"
    assert second_hint.json()["hintLevel"] == 2
    assert [action["type"] for action in second_hint.json()["geometryActions"]] == [
        "show",
        "ask_select",
    ]
    assert concept.status_code == 200
    assert concept.json()["conceptVersionId"] == CONCEPT_VERSION_ID
    assert {block["type"] for block in concept.json()["content"]} == {
        "rich_line",
        "display_math",
    }
    assert retry.status_code == 201
    assert retry.json()["id"] != attempt_id
    assert retry.json()["problemVersionId"] == M4_PROBLEM_VERSION_ID


async def test_mock_evaluation_failure_and_uncertainty_never_fabricate_ready_feedback(
    client: httpx.AsyncClient,
) -> None:
    await seed_content(CONTENT_ROOT)
    await add_invite("M5-EVALUATION-STATES")
    await login(client, "M5-EVALUATION-STATES")
    await create_profile_with_two_targets(client)
    attempt = await client.post(
        "/api/v1/attempts",
        json={"problemVersionId": M4_PROBLEM_VERSION_ID},
    )
    attempt_id = attempt.json()["id"]
    request = {
        "confirmedTranscript": {
            "confirmationStatus": "confirmed",
            "transcript": {
                "schemaVersion": "2.0.0",
                "attemptId": attempt_id,
                "blocks": [{"id": "reviewed", "type": "text", "text": "Reviewed."}],
            },
        }
    }

    try:
        app.dependency_overrides[get_mock_boundary] = lambda: DeterministicMockBoundary(
            UncertainFixtureSource()
        )
        uncertain = await client.post(
            f"/api/v1/attempts/{attempt_id}/mock-evaluation",
            json=request,
        )
        app.dependency_overrides[get_mock_boundary] = lambda: DeterministicMockBoundary(
            FailedFixtureSource(retryable=True)
        )
        failed = await client.post(
            f"/api/v1/attempts/{attempt_id}/mock-evaluation",
            json=request,
        )
    finally:
        app.dependency_overrides.pop(get_mock_boundary, None)

    assert uncertain.status_code == 200
    assert uncertain.json()["outcome"] == "uncertain"
    assert failed.status_code == 503
    assert failed.json()["error"]["code"] == "mock_temporarily_unavailable"
    assert "feedback" not in failed.json()


async def test_mock_journey_resources_are_isolated_between_authenticated_learners(
    client: httpx.AsyncClient,
) -> None:
    await seed_content(CONTENT_ROOT)
    await add_invite("M5-OWNER")
    await add_invite("M5-OTHER")
    await login(client, "M5-OWNER")
    await create_profile_with_two_targets(client)
    attempt = await client.post(
        "/api/v1/attempts",
        json={"problemVersionId": M4_PROBLEM_VERSION_ID},
    )
    attempt_id = attempt.json()["id"]

    other_client = httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    )
    try:
        await login(other_client, "M5-OTHER")
        transcript = {
            "schemaVersion": "2.0.0",
            "attemptId": attempt_id,
            "blocks": [{"id": "reviewed", "type": "text", "text": "Reviewed."}],
        }
        hidden_transcription = await other_client.post(
            f"/api/v1/attempts/{attempt_id}/mock-transcription",
            json={"uploadId": "50000000-0000-4000-8000-000000000099"},
        )
        hidden_evaluation = await other_client.post(
            f"/api/v1/attempts/{attempt_id}/mock-evaluation",
            json={
                "confirmedTranscript": {
                    "confirmationStatus": "confirmed",
                    "transcript": transcript,
                }
            },
        )
        hidden_hint = await other_client.post(
            f"/api/v1/attempts/{attempt_id}/hints/next",
            json={"previousHintLevel": 0},
        )
        hidden_plan = await other_client.get("/api/v1/plans/today")
    finally:
        await other_client.aclose()

    assert hidden_transcription.status_code == 404
    assert hidden_evaluation.status_code == 404
    assert hidden_hint.status_code == 404
    assert hidden_plan.status_code == 404
