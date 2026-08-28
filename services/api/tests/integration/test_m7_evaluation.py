import asyncio
import subprocess
import uuid
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

import httpx
import pytest
from app.database import session_factory
from app.evaluation.fake_provider import DeterministicFakeEvaluationProvider
from app.evaluation.models import AttemptStep, Evaluation, EvaluationRun, HintEvent
from app.evaluation.provider import (
    EvaluationProviderCall,
    EvaluationProviderPermanentError,
    EvaluationProviderRequest,
    EvaluationProviderTransportError,
)
from app.evaluation.service import get_evaluation_provider
from app.main import app
from app.models import PilotInvite
from app.scripts.seed_content import seed_content
from app.security import digest_secret, utc_now
from sqlalchemy import func, select, text
from sqlalchemy.exc import DBAPIError

pytestmark = pytest.mark.integration

CONTENT_ROOT = Path(__file__).resolve().parents[4] / "content"
API_ROOT = Path(__file__).resolve().parents[2]
M4_PROBLEM_VERSION_ID = "40000000-0000-4000-8000-000000000701"


async def add_invite(code: str) -> None:
    async with session_factory() as database:
        database.add(
            PilotInvite(
                code_digest=digest_secret(code),
                display_name="Synthetic M7 learner",
                max_uses=1,
                expires_at=utc_now() + timedelta(hours=1),
            )
        )
        await database.commit()


async def login(client: httpx.AsyncClient, code: str) -> None:
    response = await client.post("/api/v1/auth/pilot-login", json={"inviteCode": code})
    assert response.status_code == 200


async def create_attempt(client: httpx.AsyncClient) -> str:
    await seed_content(CONTENT_ROOT)
    profile = await client.post(
        "/api/v1/study-profile",
        json={"name": "Synthetic M7 profile", "weeklyStudyMinutes": 180},
    )
    assert profile.status_code == 201
    attempt = await client.post(
        "/api/v1/attempts", json={"problemVersionId": M4_PROBLEM_VERSION_ID}
    )
    assert attempt.status_code == 201
    return str(attempt.json()["id"])


async def confirmed_transcript(
    client: httpx.AsyncClient, attempt_id: str, marker: str
) -> tuple[str, str]:
    image = b"\x89PNG\r\n\x1a\nsynthetic-m7-" + marker.encode()
    signed = await client.post(
        "/api/v1/uploads/presign",
        json={"contentType": "image/png", "fileName": "m7.png", "sizeBytes": len(image)},
    )
    async with httpx.AsyncClient() as storage:
        stored = await storage.put(
            signed.json()["uploadUrl"], content=image, headers={"Content-Type": "image/png"}
        )
    assert stored.status_code == 200
    completed = await client.post(f"/api/v1/uploads/{signed.json()['uploadId']}/complete")
    transcribed = await client.post(
        f"/api/v1/attempts/{attempt_id}/transcribe",
        json={"uploadId": completed.json()["id"], "idempotencyKey": str(uuid.uuid4())},
    )
    assert transcribed.status_code == 200
    initial = transcribed.json()["transcriptVersion"]
    document = initial["document"]
    document["blocks"][0]["text"] += f" SYNTHETIC-EVAL:{marker}"
    corrected = await client.post(
        f"/api/v1/attempts/{attempt_id}/transcripts",
        json={"baseTranscriptVersionId": initial["id"], "document": document},
    )
    assert corrected.status_code == 201
    confirmed = await client.post(
        f"/api/v1/attempts/{attempt_id}/confirm-transcript",
        json={
            "transcriptVersionId": corrected.json()["id"],
            "transcriptHash": corrected.json()["transcriptHash"],
        },
    )
    assert confirmed.status_code == 200
    return str(initial["id"]), str(corrected.json()["id"])


async def request_evaluation(
    client: httpx.AsyncClient,
    attempt_id: str,
    transcript_version_id: str,
    *,
    idempotency_key: str | None = None,
) -> httpx.Response:
    return await client.post(
        f"/api/v1/attempts/{attempt_id}/evaluation",
        json={
            "confirmedTranscriptVersionId": transcript_version_id,
            "idempotencyKey": idempotency_key or str(uuid.uuid4()),
        },
    )


async def test_evaluation_and_hints_require_authentication(client: httpx.AsyncClient) -> None:
    attempt_id = str(uuid.uuid4())
    transcript_version_id = str(uuid.uuid4())

    requested = await request_evaluation(client, attempt_id, transcript_version_id)
    state = await client.get(f"/api/v1/attempts/{attempt_id}/evaluation")
    hint = await client.post(
        f"/api/v1/attempts/{attempt_id}/hints/next",
        json={"idempotencyKey": str(uuid.uuid4())},
    )

    assert requested.status_code == state.status_code == hint.status_code == 401


async def test_evaluation_requires_exact_confirmation_and_persists_root_dependencies_and_score(
    client: httpx.AsyncClient,
) -> None:
    await add_invite("M7-ROOT")
    await login(client, "M7-ROOT")
    attempt_id = await create_attempt(client)
    initial_id, confirmed_id = await confirmed_transcript(client, attempt_id, "subtle-error")
    unconfirmed = await request_evaluation(client, attempt_id, initial_id)
    key = str(uuid.uuid4())
    evaluated = await request_evaluation(client, attempt_id, confirmed_id, idempotency_key=key)
    duplicate = await request_evaluation(client, attempt_id, confirmed_id, idempotency_key=key)
    state = await client.get(f"/api/v1/attempts/{attempt_id}/evaluation")

    assert unconfirmed.status_code == 409
    assert unconfirmed.json()["error"]["code"] == "transcript_not_confirmed"
    assert evaluated.status_code == 200
    assert duplicate.json() == evaluated.json()
    result = evaluated.json()
    assert result["outcome"] == "ready"
    assert result["score"] == "0.00"
    assert result["maximumScore"] == "4.00"
    assert result["referenceSolutionsNonExhaustive"] is True
    assert [step["errorKind"] for step in result["reasoningSteps"]] == ["root", "dependent"]
    assert result["reasoningSteps"][1]["dependsOnStepIds"] == [result["reasoningSteps"][0]["id"]]
    assert sum(Decimal(item["awardedScore"]) for item in result["rubricBreakdown"]) == Decimal(
        result["score"]
    )
    assert sum(Decimal(item["maximumScore"]) for item in result["rubricBreakdown"]) == Decimal(
        result["maximumScore"]
    )
    assert state.json()["state"] == "ready"
    async with session_factory() as database:
        assert await database.scalar(select(func.count()).select_from(EvaluationRun)) == 1
        assert await database.scalar(select(func.count()).select_from(Evaluation)) == 1
        assert await database.scalar(select(func.count()).select_from(AttemptStep)) == 2


@pytest.mark.parametrize("marker", ["correct-standard", "correct-alternative"])
async def test_valid_standard_and_alternative_solutions_receive_full_rubric_credit(
    client: httpx.AsyncClient, marker: str
) -> None:
    await add_invite(f"M7-{marker.upper()}")
    await login(client, f"M7-{marker.upper()}")
    attempt_id = await create_attempt(client)
    _, confirmed_id = await confirmed_transcript(client, attempt_id, marker)

    response = await request_evaluation(client, attempt_id, confirmed_id)

    assert response.status_code == 200
    assert response.json()["outcome"] == "ready"
    assert response.json()["score"] == response.json()["maximumScore"] == "4.00"
    assert response.json()["reasoningSteps"][0]["judgment"] == "correct"


@pytest.mark.parametrize("marker", ["contradictory", "unreadable"])
async def test_insufficient_confidence_is_uncertain_without_fabricated_scoring(
    client: httpx.AsyncClient, marker: str
) -> None:
    await add_invite(f"M7-{marker.upper()}")
    await login(client, f"M7-{marker.upper()}")
    attempt_id = await create_attempt(client)
    _, confirmed_id = await confirmed_transcript(client, attempt_id, marker)

    response = await request_evaluation(client, attempt_id, confirmed_id)
    state = await client.get(f"/api/v1/attempts/{attempt_id}/evaluation")

    assert response.status_code == 200
    assert response.json()["outcome"] == "uncertain"
    assert response.json()["recommendedAction"] == "manual_review"
    assert "score" not in response.json()
    assert "reasoningSteps" not in response.json()
    assert state.json()["state"] == "uncertain"


async def test_hint_ladder_is_server_ordered_idempotent_and_exhaustible(
    client: httpx.AsyncClient,
) -> None:
    await add_invite("M7-HINTS")
    await login(client, "M7-HINTS")
    attempt_id = await create_attempt(client)
    before = await client.post(
        f"/api/v1/attempts/{attempt_id}/hints/next",
        json={"idempotencyKey": str(uuid.uuid4())},
    )
    _, confirmed_id = await confirmed_transcript(client, attempt_id, "incomplete")
    await request_evaluation(client, attempt_id, confirmed_id)
    key = str(uuid.uuid4())
    first = await client.post(
        f"/api/v1/attempts/{attempt_id}/hints/next", json={"idempotencyKey": key}
    )
    repeated = await client.post(
        f"/api/v1/attempts/{attempt_id}/hints/next", json={"idempotencyKey": key}
    )
    released = [first.json()]
    for _level in range(2, 6):
        response = await client.post(
            f"/api/v1/attempts/{attempt_id}/hints/next",
            json={"idempotencyKey": str(uuid.uuid4())},
        )
        assert response.status_code == 200
        released.append(response.json())
    exhausted = await client.post(
        f"/api/v1/attempts/{attempt_id}/hints/next",
        json={"idempotencyKey": str(uuid.uuid4())},
    )

    assert before.status_code == 409
    assert before.json()["error"]["code"] == "evaluation_required"
    assert repeated.json() == first.json()
    assert released[0]["evaluationId"] == released[-1]["evaluationId"]
    assert [hint["hintLevel"] for hint in released] == [1, 2, 3, 4, 5]
    assert released[0]["geometryActions"][0]["type"] == "highlight"
    assert released[-1]["revealsCompleteSolution"] is True
    assert exhausted.status_code == 409
    assert exhausted.json()["error"]["code"] == "hint_ladder_exhausted"
    async with session_factory() as database:
        assert await database.scalar(select(func.count()).select_from(HintEvent)) == 5


class InvalidSchemaProvider(DeterministicFakeEvaluationProvider):
    def __init__(self) -> None:
        super().__init__()
        self.calls = 0

    async def _invoke(
        self, request: EvaluationProviderRequest, *, repair_schema: bool
    ) -> EvaluationProviderCall:
        self.calls += 1
        return EvaluationProviderCall(
            payload={"outcome": "ready", "reasoningSteps": []},
            latency_ms=2,
            input_tokens=3,
            output_tokens=5,
        )


async def test_invalid_schema_stops_after_one_repair_and_persists_no_result(
    client: httpx.AsyncClient,
) -> None:
    await add_invite("M7-INVALID")
    await login(client, "M7-INVALID")
    attempt_id = await create_attempt(client)
    _, confirmed_id = await confirmed_transcript(client, attempt_id, "incomplete")
    provider = InvalidSchemaProvider()
    app.dependency_overrides[get_evaluation_provider] = lambda: provider
    try:
        response = await request_evaluation(client, attempt_id, confirmed_id)
        state = await client.get(f"/api/v1/attempts/{attempt_id}/evaluation")
    finally:
        app.dependency_overrides.pop(get_evaluation_provider, None)

    assert response.status_code == 502
    assert response.json()["error"]["code"] == "evaluation_invalid_schema"
    assert provider.calls == 2
    assert state.json()["state"] == "invalid_schema"
    assert state.json()["run"]["schemaAttempts"] == 2
    assert state.json()["run"]["retryCount"] == 1
    async with session_factory() as database:
        assert await database.scalar(select(func.count()).select_from(Evaluation)) == 0
        assert await database.scalar(select(func.count()).select_from(AttemptStep)) == 0


class BlockingEvaluationProvider(DeterministicFakeEvaluationProvider):
    def __init__(self) -> None:
        super().__init__()
        self.started = asyncio.Event()
        self.release = asyncio.Event()
        self.calls = 0

    async def _invoke(
        self, request: EvaluationProviderRequest, *, repair_schema: bool
    ) -> EvaluationProviderCall:
        self.calls += 1
        self.started.set()
        await self.release.wait()
        return await super()._invoke(request, repair_schema=repair_schema)


async def test_concurrent_requests_create_only_one_provider_run(client: httpx.AsyncClient) -> None:
    await add_invite("M7-CONCURRENT")
    await login(client, "M7-CONCURRENT")
    attempt_id = await create_attempt(client)
    _, confirmed_id = await confirmed_transcript(client, attempt_id, "incomplete")
    provider = BlockingEvaluationProvider()
    app.dependency_overrides[get_evaluation_provider] = lambda: provider
    first_task = asyncio.create_task(request_evaluation(client, attempt_id, confirmed_id))
    try:
        await asyncio.wait_for(provider.started.wait(), timeout=2)
        concurrent = await request_evaluation(client, attempt_id, confirmed_id)
        provider.release.set()
        first = await asyncio.wait_for(first_task, timeout=2)
    finally:
        provider.release.set()
        app.dependency_overrides.pop(get_evaluation_provider, None)

    assert first.status_code == 200
    assert concurrent.status_code == 409
    assert concurrent.json()["error"]["code"] == "evaluation_in_progress"
    assert provider.calls == 1


class TerminalFailureProvider(DeterministicFakeEvaluationProvider):
    def __init__(self, error: Exception) -> None:
        super().__init__()
        self.error = error
        self.calls = 0

    async def _invoke(
        self, request: EvaluationProviderRequest, *, repair_schema: bool
    ) -> EvaluationProviderCall:
        self.calls += 1
        raise self.error


@pytest.mark.parametrize(
    ("provider_error", "expected_code", "expected_state", "expected_calls"),
    [
        (
            EvaluationProviderTransportError("timeout"),
            "evaluation_temporarily_unavailable",
            "retryable_failure",
            2,
        ),
        (
            EvaluationProviderPermanentError("provider_rejected"),
            "evaluation_permanent_failure",
            "permanent_failure",
            1,
        ),
    ],
)
async def test_provider_failures_store_safe_terminal_state_without_fabricating_results(
    client: httpx.AsyncClient,
    provider_error: Exception,
    expected_code: str,
    expected_state: str,
    expected_calls: int,
) -> None:
    await add_invite(f"M7-{expected_state.upper()}")
    await login(client, f"M7-{expected_state.upper()}")
    attempt_id = await create_attempt(client)
    _, confirmed_id = await confirmed_transcript(client, attempt_id, "incomplete")
    provider = TerminalFailureProvider(provider_error)
    app.dependency_overrides[get_evaluation_provider] = lambda: provider
    try:
        first = await request_evaluation(client, attempt_id, confirmed_id)
        second = await request_evaluation(client, attempt_id, confirmed_id)
        state = await client.get(f"/api/v1/attempts/{attempt_id}/evaluation")
    finally:
        app.dependency_overrides.pop(get_evaluation_provider, None)

    assert first.status_code in {502, 503}
    assert second.status_code == first.status_code
    assert first.json()["error"]["code"] == second.json()["error"]["code"] == expected_code
    assert state.json()["state"] == expected_state
    assert state.json()["run"]["errorCode"] in {"timeout", "provider_rejected"}
    assert provider.calls == expected_calls
    async with session_factory() as database:
        assert await database.scalar(select(func.count()).select_from(Evaluation)) == 0
        assert await database.scalar(select(func.count()).select_from(AttemptStep)) == 0


async def test_evaluation_and_hint_resources_are_owner_isolated(client: httpx.AsyncClient) -> None:
    await add_invite("M7-OWNER")
    await add_invite("M7-OTHER")
    await login(client, "M7-OWNER")
    attempt_id = await create_attempt(client)
    _, confirmed_id = await confirmed_transcript(client, attempt_id, "incomplete")
    other = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver")
    try:
        await login(other, "M7-OTHER")
        hidden_evaluation = await request_evaluation(other, attempt_id, confirmed_id)
        hidden_state = await other.get(f"/api/v1/attempts/{attempt_id}/evaluation")
        hidden_hint = await other.post(
            f"/api/v1/attempts/{attempt_id}/hints/next",
            json={"idempotencyKey": str(uuid.uuid4())},
        )
    finally:
        await other.aclose()

    assert hidden_evaluation.status_code == 404
    assert hidden_state.status_code == 404
    assert hidden_hint.status_code == 404


async def test_m7_schema_relationships_triggers_and_populated_downgrade(
    client: httpx.AsyncClient,
) -> None:
    await add_invite("M7-MIGRATION")
    await login(client, "M7-MIGRATION")
    attempt_id = await create_attempt(client)
    _, confirmed_id = await confirmed_transcript(client, attempt_id, "subtle-error")
    evaluated = await request_evaluation(client, attempt_id, confirmed_id)
    assert evaluated.status_code == 200
    await client.post(
        f"/api/v1/attempts/{attempt_id}/hints/next",
        json={"idempotencyKey": str(uuid.uuid4())},
    )
    async with session_factory() as database:
        tables = set(
            await database.scalars(
                text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = 'public' AND table_name IN "
                    "('evaluation_runs','attempt_steps','evaluations','hint_events')"
                )
            )
        )
        trigger_count = await database.scalar(
            text(
                "SELECT count(*) FROM pg_trigger WHERE NOT tgisinternal "
                "AND tgname LIKE 'trg_m7_%_immutable'"
            )
        )
        run_id = await database.scalar(select(EvaluationRun.id))
        with pytest.raises(DBAPIError):
            await database.execute(
                text("UPDATE evaluation_runs SET provider = 'tampered' WHERE id = :run_id"),
                {"run_id": run_id},
            )
        await database.rollback()
    assert tables == {"evaluation_runs", "attempt_steps", "evaluations", "hint_events"}
    assert trigger_count == 3

    def migrate(revision: str) -> None:
        command = "upgrade" if revision == "head" else "downgrade"
        subprocess.run(["uv", "run", "alembic", command, revision], cwd=API_ROOT, check=True)

    try:
        await asyncio.to_thread(migrate, "20260827_0003")
        async with session_factory() as database:
            assert (
                await database.scalar(text("SELECT to_regclass('public.evaluation_runs')")) is None
            )
            assert (
                await database.scalar(
                    text("SELECT count(*) FROM transcript_confirmations WHERE attempt_id = :id"),
                    {"id": attempt_id},
                )
                == 1
            )
    finally:
        await asyncio.to_thread(migrate, "head")
