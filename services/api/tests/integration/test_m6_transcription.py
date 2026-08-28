import asyncio
import subprocess
import uuid
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

import httpx
import pytest
from app.database import session_factory
from app.main import app
from app.models import PilotInvite
from app.scripts.seed_content import seed_content
from app.security import digest_secret, utc_now
from app.transcription.fake_provider import DeterministicFakeTranscriptionProvider
from app.transcription.models import (
    AIModelRun,
    AttemptAsset,
    TranscriptConfirmation,
    TranscriptVersion,
)
from app.transcription.provider import (
    ConfiguredProviderIdentity,
    ProviderCall,
    ProviderPermanentError,
    ProviderRequest,
    ProviderTransportError,
    StrictTranscriptionProvider,
)
from app.transcription.service import get_transcription_provider
from sqlalchemy import func, select, text
from sqlalchemy.exc import DBAPIError

pytestmark = pytest.mark.integration

CONTENT_ROOT = Path(__file__).resolve().parents[4] / "content"
API_ROOT = Path(__file__).resolve().parents[2]
M4_PROBLEM_VERSION_ID = "40000000-0000-4000-8000-000000000701"
AURORA_CYCLE_ID = "10000000-0000-4000-8000-000000000201"
HARBOR_CYCLE_ID = "10000000-0000-4000-8000-000000000202"


async def add_invite(code: str) -> None:
    async with session_factory() as database:
        database.add(
            PilotInvite(
                code_digest=digest_secret(code),
                display_name="Synthetic M6 learner",
                max_uses=1,
                expires_at=utc_now() + timedelta(hours=1),
            )
        )
        await database.commit()


async def login(client: httpx.AsyncClient, code: str) -> None:
    assert (
        await client.post("/api/v1/auth/pilot-login", json={"inviteCode": code})
    ).status_code == 200


async def create_attempt(client: httpx.AsyncClient) -> str:
    await seed_content(CONTENT_ROOT)
    await client.post(
        "/api/v1/study-profile",
        json={"name": "Synthetic M6 preparation", "weeklyStudyMinutes": 240},
    )
    for rank, cycle_id in enumerate((AURORA_CYCLE_ID, HARBOR_CYCLE_ID), start=1):
        await client.post(
            "/api/v1/exam-targets",
            json={"examCycleId": cycle_id, "targetScore": "16.00", "priorityRank": rank},
        )
    response = await client.post(
        "/api/v1/attempts",
        json={"problemVersionId": M4_PROBLEM_VERSION_ID},
    )
    assert response.status_code == 201
    return response.json()["id"]


async def upload_image(client: httpx.AsyncClient, image: bytes, *, complete: bool = True) -> str:
    signed = await client.post(
        "/api/v1/uploads/presign",
        json={
            "contentType": "image/png",
            "fileName": "synthetic-m6-solution.png",
            "sizeBytes": len(image),
        },
    )
    async with httpx.AsyncClient() as storage_client:
        stored = await storage_client.put(
            signed.json()["uploadUrl"],
            content=image,
            headers={"Content-Type": "image/png"},
        )
    assert stored.status_code == 200
    if complete:
        completed = await client.post(f"/api/v1/uploads/{signed.json()['uploadId']}/complete")
        assert completed.status_code == 200
    return signed.json()["uploadId"]


async def test_owned_verified_image_creates_durable_version_and_exact_confirmation(
    client: httpx.AsyncClient,
) -> None:
    await add_invite("M6-DURABLE")
    await login(client, "M6-DURABLE")
    attempt_id = await create_attempt(client)
    upload_id = await upload_image(client, b"\x89PNG\r\n\x1a\nsynthetic-m6-only")
    idempotency_key = str(uuid.uuid4())

    first = await client.post(
        f"/api/v1/attempts/{attempt_id}/transcribe",
        json={"uploadId": upload_id, "idempotencyKey": idempotency_key},
    )
    duplicate = await client.post(
        f"/api/v1/attempts/{attempt_id}/transcribe",
        json={"uploadId": upload_id, "idempotencyKey": idempotency_key},
    )

    assert first.status_code == 200
    assert duplicate.json() == first.json()
    body = first.json()
    assert body["outcome"] == "ready"
    assert body["run"]["provider"] == "application-owned-deterministic-fake"
    assert body["run"]["modelSnapshot"] == "m6-transcription-fixture-v1"
    assert body["run"]["schemaAttempts"] == 1
    assert body["transcriptVersion"]["document"]["blocks"][1]["latex"] == "M=(2,0"
    assert body["transcriptVersion"]["document"]["warnings"][0]["code"] == "low_confidence_math"
    assert len(body["transcriptVersion"]["transcriptHash"]) == 64

    tampered_document = body["transcriptVersion"]["document"] | {
        "blocks": [block.copy() for block in body["transcriptVersion"]["document"]["blocks"]]
    }
    tampered_document["blocks"][0]["sourceRegion"] = {
        **tampered_document["blocks"][0]["sourceRegion"],
        "x": 0.09,
    }
    tampered = await client.post(
        f"/api/v1/attempts/{attempt_id}/transcripts",
        json={
            "baseTranscriptVersionId": body["transcriptVersion"]["id"],
            "document": tampered_document,
        },
    )
    assert tampered.status_code == 422
    assert tampered.json()["error"]["code"] == "transcript_structure_invalid"

    document = body["transcriptVersion"]["document"]
    document["blocks"][0]["text"] += " Corrected by the synthetic learner."
    corrected = await client.post(
        f"/api/v1/attempts/{attempt_id}/transcripts",
        json={
            "baseTranscriptVersionId": body["transcriptVersion"]["id"],
            "document": document,
        },
    )
    repeated_correction = await client.post(
        f"/api/v1/attempts/{attempt_id}/transcripts",
        json={
            "baseTranscriptVersionId": body["transcriptVersion"]["id"],
            "document": document,
        },
    )
    assert corrected.status_code == 201
    assert corrected.json()["version"] == 2
    assert repeated_correction.status_code == 201
    assert repeated_correction.json() == corrected.json()
    confirmed = await client.post(
        f"/api/v1/attempts/{attempt_id}/confirm-transcript",
        json={
            "transcriptVersionId": corrected.json()["id"],
            "transcriptHash": corrected.json()["transcriptHash"],
        },
    )
    repeated_confirmation = await client.post(
        f"/api/v1/attempts/{attempt_id}/confirm-transcript",
        json={
            "transcriptVersionId": corrected.json()["id"],
            "transcriptHash": corrected.json()["transcriptHash"],
        },
    )
    locked_edit = await client.post(
        f"/api/v1/attempts/{attempt_id}/transcripts",
        json={
            "baseTranscriptVersionId": corrected.json()["id"],
            "document": document,
        },
    )
    state = await client.get(f"/api/v1/attempts/{attempt_id}/transcription")
    evaluation = await client.post(
        f"/api/v1/attempts/{attempt_id}/evaluation",
        json={
            "confirmedTranscriptVersionId": corrected.json()["id"],
            "idempotencyKey": str(uuid.uuid4()),
        },
    )

    assert confirmed.status_code == 200
    assert repeated_confirmation.json() == confirmed.json()
    assert confirmed.json()["transcriptHash"] == corrected.json()["transcriptHash"]
    assert locked_edit.status_code == 409
    assert locked_edit.json()["error"]["code"] == "transcript_confirmed_locked"
    assert state.json()["status"] == "ready"
    assert state.json()["confirmation"]["transcriptVersionId"] == corrected.json()["id"]
    assert evaluation.status_code == 200
    assert evaluation.json()["run"]["provider"] == "application-owned-deterministic-fake"

    async with session_factory() as database:
        assert await database.scalar(select(func.count()).select_from(AttemptAsset)) == 1
        assert await database.scalar(select(func.count()).select_from(AIModelRun)) == 1
        assert await database.scalar(select(func.count()).select_from(TranscriptVersion)) == 2
        assert await database.scalar(select(func.count()).select_from(TranscriptConfirmation)) == 1
        run_id = await database.scalar(select(AIModelRun.id))
        with pytest.raises(DBAPIError):
            await database.execute(
                text("UPDATE ai_model_runs SET provider = 'tampered' WHERE id = :run_id"),
                {"run_id": run_id},
            )
        await database.rollback()


async def test_transcription_requires_auth_owned_attempt_and_ready_owned_upload(
    client: httpx.AsyncClient,
) -> None:
    await add_invite("M6-OWNER")
    await add_invite("M6-OTHER")
    await login(client, "M6-OWNER")
    attempt_id = await create_attempt(client)
    pending_upload_id = await upload_image(
        client,
        b"\x89PNG\r\n\x1a\npending-synthetic",
        complete=False,
    )
    ready_upload_id = await upload_image(client, b"\x89PNG\r\n\x1a\nowned-synthetic")

    pending = await client.post(
        f"/api/v1/attempts/{attempt_id}/transcribe",
        json={"uploadId": pending_upload_id, "idempotencyKey": str(uuid.uuid4())},
    )
    other = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver")
    try:
        await login(other, "M6-OTHER")
        other_attempt_id = await create_attempt(other)
        hidden_attempt = await other.post(
            f"/api/v1/attempts/{attempt_id}/transcribe",
            json={"uploadId": ready_upload_id, "idempotencyKey": str(uuid.uuid4())},
        )
        hidden_state = await other.get(f"/api/v1/attempts/{attempt_id}/transcription")
        hidden_upload = await other.post(
            f"/api/v1/attempts/{other_attempt_id}/transcribe",
            json={"uploadId": ready_upload_id, "idempotencyKey": str(uuid.uuid4())},
        )
    finally:
        await other.aclose()

    assert pending.status_code == 409
    assert pending.json()["error"]["code"] == "upload_not_ready"
    assert hidden_attempt.status_code == 404
    assert hidden_state.status_code == 404
    assert hidden_upload.status_code == 404
    assert hidden_upload.json()["error"]["code"] == "upload_not_found"


class RateLimitedProvider(StrictTranscriptionProvider):
    def __init__(self) -> None:
        super().__init__(
            ConfiguredProviderIdentity(
                provider="synthetic-rate-limit",
                model_snapshot="synthetic-rate-limit-v1",
                prompt_version="m6-faithful-transcription-v1",
                prompt_hash="a" * 64,
                schema_version="m6-provider-transcript-v1",
                pricing_version="synthetic-zero-v1",
                input_usd_per_million=Decimal("0"),
                output_usd_per_million=Decimal("0"),
            )
        )
        self.calls = 0

    async def _invoke(self, request: ProviderRequest, *, repair_schema: bool) -> ProviderCall:
        self.calls += 1
        raise ProviderTransportError("rate_limited")


class ScriptedProvider(StrictTranscriptionProvider):
    def __init__(self, behavior: str) -> None:
        super().__init__(
            ConfiguredProviderIdentity(
                provider=f"synthetic-{behavior}",
                model_snapshot=f"synthetic-{behavior}-v1",
                prompt_version="m6-faithful-transcription-v1",
                prompt_hash="a" * 64,
                schema_version="m6-provider-transcript-v1",
                pricing_version="synthetic-zero-v1",
                input_usd_per_million=Decimal("0"),
                output_usd_per_million=Decimal("0"),
            )
        )
        self.behavior = behavior
        self.calls = 0

    async def _invoke(self, request: ProviderRequest, *, repair_schema: bool) -> ProviderCall:
        self.calls += 1
        if self.behavior == "timeout":
            raise ProviderTransportError("timeout")
        if self.behavior == "rejected":
            raise ProviderPermanentError("provider_rejected")
        if self.behavior == "invalid-schema":
            return ProviderCall(
                payload={"outcome": "ready", "blocks": [], "warnings": []},
                latency_ms=4,
                input_tokens=3,
                output_tokens=2,
            )
        if self.behavior == "uncertain":
            return ProviderCall(
                payload={
                    "outcome": "uncertain",
                    "warnings": [{"code": "ordering_uncertain"}],
                },
                latency_ms=4,
                input_tokens=3,
                output_tokens=2,
            )
        raise AssertionError(f"Unknown scripted behavior: {self.behavior}")


class CountingFakeProvider(DeterministicFakeTranscriptionProvider):
    def __init__(self) -> None:
        super().__init__()
        self.calls = 0

    async def _invoke(self, request: ProviderRequest, *, repair_schema: bool) -> ProviderCall:
        self.calls += 1
        return await super()._invoke(request, repair_schema=repair_schema)


class SlowFakeProvider(DeterministicFakeTranscriptionProvider):
    def __init__(self) -> None:
        super().__init__()
        self.started = asyncio.Event()
        self.release = asyncio.Event()
        self.calls = 0

    async def _invoke(self, request: ProviderRequest, *, repair_schema: bool) -> ProviderCall:
        self.calls += 1
        self.started.set()
        await self.release.wait()
        return await super()._invoke(request, repair_schema=repair_schema)


async def test_retryable_failure_persists_metadata_without_a_transcript(
    client: httpx.AsyncClient,
) -> None:
    await add_invite("M6-FAILURE")
    await login(client, "M6-FAILURE")
    attempt_id = await create_attempt(client)
    upload_id = await upload_image(client, b"\x89PNG\r\n\x1a\nfailure-synthetic")
    provider = RateLimitedProvider()
    app.dependency_overrides[get_transcription_provider] = lambda: provider
    try:
        failed = await client.post(
            f"/api/v1/attempts/{attempt_id}/transcribe",
            json={"uploadId": upload_id, "idempotencyKey": str(uuid.uuid4())},
        )
        state = await client.get(f"/api/v1/attempts/{attempt_id}/transcription")
    finally:
        app.dependency_overrides.pop(get_transcription_provider, None)

    assert failed.status_code == 503
    assert failed.json()["error"]["code"] == "transcription_rate_limited"
    assert provider.calls == 1
    assert state.json()["status"] == "retryable_failure"
    assert "transcriptVersion" not in state.json()
    async with session_factory() as database:
        assert await database.scalar(select(func.count()).select_from(TranscriptVersion)) == 0


async def test_completed_asset_is_reused_for_a_new_idempotency_key(
    client: httpx.AsyncClient,
) -> None:
    await add_invite("M6-REUSE")
    await login(client, "M6-REUSE")
    attempt_id = await create_attempt(client)
    upload_id = await upload_image(client, b"\x89PNG\r\n\x1a\nreuse-synthetic")
    provider = CountingFakeProvider()
    app.dependency_overrides[get_transcription_provider] = lambda: provider
    try:
        first = await client.post(
            f"/api/v1/attempts/{attempt_id}/transcribe",
            json={"uploadId": upload_id, "idempotencyKey": str(uuid.uuid4())},
        )
        reused = await client.post(
            f"/api/v1/attempts/{attempt_id}/transcribe",
            json={"uploadId": upload_id, "idempotencyKey": str(uuid.uuid4())},
        )
    finally:
        app.dependency_overrides.pop(get_transcription_provider, None)

    assert first.status_code == 200
    assert reused.status_code == 200
    assert reused.json() == first.json()
    assert provider.calls == 1
    async with session_factory() as database:
        assert await database.scalar(select(func.count()).select_from(AIModelRun)) == 1


async def test_concurrent_click_with_a_new_key_never_starts_a_second_provider_call(
    client: httpx.AsyncClient,
) -> None:
    await add_invite("M6-CONCURRENT")
    await login(client, "M6-CONCURRENT")
    attempt_id = await create_attempt(client)
    upload_id = await upload_image(client, b"\x89PNG\r\n\x1a\nconcurrent-synthetic")
    provider = SlowFakeProvider()
    app.dependency_overrides[get_transcription_provider] = lambda: provider
    first_task = asyncio.create_task(
        client.post(
            f"/api/v1/attempts/{attempt_id}/transcribe",
            json={"uploadId": upload_id, "idempotencyKey": str(uuid.uuid4())},
        )
    )
    try:
        await asyncio.wait_for(provider.started.wait(), timeout=2)
        duplicate = await client.post(
            f"/api/v1/attempts/{attempt_id}/transcribe",
            json={"uploadId": upload_id, "idempotencyKey": str(uuid.uuid4())},
        )
        provider.release.set()
        first = await asyncio.wait_for(first_task, timeout=2)
    finally:
        provider.release.set()
        app.dependency_overrides.pop(get_transcription_provider, None)

    assert first.status_code == 200
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "transcription_in_progress"
    assert provider.calls == 1


@pytest.mark.parametrize(
    ("behavior", "http_status", "error_code", "state_status", "expected_calls"),
    (
        ("timeout", 503, "transcription_timeout", "retryable_failure", 1),
        ("rejected", 502, "transcription_provider_rejected", "permanent_failure", 1),
        ("invalid-schema", 502, "transcription_invalid_schema", "invalid_schema", 2),
    ),
)
async def test_terminal_provider_failures_never_create_a_transcript(
    client: httpx.AsyncClient,
    behavior: str,
    http_status: int,
    error_code: str,
    state_status: str,
    expected_calls: int,
) -> None:
    invite = f"M6-{behavior.upper()}"
    await add_invite(invite)
    await login(client, invite)
    attempt_id = await create_attempt(client)
    upload_id = await upload_image(
        client,
        b"\x89PNG\r\n\x1a\n" + behavior.encode(),
    )
    provider = ScriptedProvider(behavior)
    app.dependency_overrides[get_transcription_provider] = lambda: provider
    try:
        response = await client.post(
            f"/api/v1/attempts/{attempt_id}/transcribe",
            json={"uploadId": upload_id, "idempotencyKey": str(uuid.uuid4())},
        )
        state = await client.get(f"/api/v1/attempts/{attempt_id}/transcription")
    finally:
        app.dependency_overrides.pop(get_transcription_provider, None)

    assert response.status_code == http_status
    assert response.json()["error"]["code"] == error_code
    assert provider.calls == expected_calls
    assert state.json()["status"] == state_status
    assert "transcriptVersion" not in state.json()
    if behavior == "invalid-schema":
        assert state.json()["run"]["schemaAttempts"] == 2
        assert state.json()["run"]["inputTokens"] == 6
        assert state.json()["run"]["outputTokens"] == 4
    async with session_factory() as database:
        assert await database.scalar(select(func.count()).select_from(TranscriptVersion)) == 0


async def test_uncertainty_is_terminal_and_contains_no_fabricated_transcript(
    client: httpx.AsyncClient,
) -> None:
    await add_invite("M6-UNCERTAIN")
    await login(client, "M6-UNCERTAIN")
    attempt_id = await create_attempt(client)
    upload_id = await upload_image(client, b"\x89PNG\r\n\x1a\nuncertain-synthetic")
    provider = ScriptedProvider("uncertain")
    app.dependency_overrides[get_transcription_provider] = lambda: provider
    try:
        response = await client.post(
            f"/api/v1/attempts/{attempt_id}/transcribe",
            json={"uploadId": upload_id, "idempotencyKey": str(uuid.uuid4())},
        )
        state = await client.get(f"/api/v1/attempts/{attempt_id}/transcription")
    finally:
        app.dependency_overrides.pop(get_transcription_provider, None)

    assert response.status_code == 200
    assert response.json()["outcome"] == "uncertain"
    assert response.json()["warnings"] == [
        {
            "blockId": None,
            "code": "ordering_uncertain",
            "message": "The reading order may need review.",
        }
    ]
    assert state.json()["status"] == "uncertain"
    assert "transcriptVersion" not in state.json()
    async with session_factory() as database:
        assert await database.scalar(select(func.count()).select_from(TranscriptVersion)) == 0


async def test_m6_migration_has_exact_relationships_and_append_only_triggers() -> None:
    async with session_factory() as database:
        tables = set(
            await database.scalars(
                text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = 'public' AND table_name IN "
                    "('attempt_assets', 'prompt_versions', 'ai_model_runs', "
                    "'transcript_versions', 'transcript_confirmations')"
                )
            )
        )
        trigger_count = await database.scalar(
            text(
                "SELECT count(*) FROM pg_trigger WHERE NOT tgisinternal "
                "AND tgname LIKE 'trg_m6_%_immutable'"
            )
        )
        run_trigger_count = await database.scalar(
            text(
                "SELECT count(*) FROM pg_trigger WHERE NOT tgisinternal "
                "AND tgname = 'trg_m6_ai_model_runs_transition'"
            )
        )
        target_columns = list(
            await database.scalars(
                text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name = 'transcript_versions'"
                )
            )
        )
        query_indexes = set(
            await database.scalars(
                text(
                    "SELECT indexname FROM pg_indexes WHERE schemaname = 'public' "
                    "AND indexname IN ('ix_ai_model_runs_asset_fingerprint_created', "
                    "'uq_ai_model_runs_asset_processing', "
                    "'ix_transcript_versions_source_run_version')"
                )
            )
        )

    assert tables == {
        "attempt_assets",
        "prompt_versions",
        "ai_model_runs",
        "transcript_versions",
        "transcript_confirmations",
    }
    assert trigger_count == 4
    assert run_trigger_count == 1
    assert "exam_target_id" not in target_columns
    assert "attempt_id" in target_columns
    assert query_indexes == {
        "ix_ai_model_runs_asset_fingerprint_created",
        "uq_ai_model_runs_asset_processing",
        "ix_transcript_versions_source_run_version",
    }


async def test_m6_populated_downgrade_preserves_m5_rows_and_reupgrade_is_empty(
    client: httpx.AsyncClient,
) -> None:
    await add_invite("M6-MIGRATION")
    await login(client, "M6-MIGRATION")
    attempt_id = await create_attempt(client)
    upload_id = await upload_image(client, b"\x89PNG\r\n\x1a\npopulated-migration-synthetic")
    transcribed = await client.post(
        f"/api/v1/attempts/{attempt_id}/transcribe",
        json={"uploadId": upload_id, "idempotencyKey": str(uuid.uuid4())},
    )
    assert transcribed.status_code == 200

    async with session_factory() as database:
        assert await database.scalar(select(func.count()).select_from(AIModelRun)) == 1
        assert await database.scalar(select(func.count()).select_from(TranscriptVersion)) == 1

    def migrate(revision: str) -> None:
        subprocess.run(
            ["uv", "run", "alembic", "downgrade" if revision != "head" else "upgrade", revision],
            cwd=API_ROOT,
            check=True,
        )

    try:
        await asyncio.to_thread(migrate, "20260826_0002")
        async with session_factory() as database:
            assert (
                await database.scalar(
                    text("SELECT count(*) FROM attempts WHERE id = :attempt_id"),
                    {"attempt_id": attempt_id},
                )
                == 1
            )
            assert await database.scalar(text("SELECT to_regclass('public.ai_model_runs')")) is None
    finally:
        await asyncio.to_thread(migrate, "head")

    async with session_factory() as database:
        assert (
            await database.scalar(
                text("SELECT count(*) FROM attempts WHERE id = :attempt_id"),
                {"attempt_id": attempt_id},
            )
            == 1
        )
        assert await database.scalar(select(func.count()).select_from(AIModelRun)) == 0
        assert await database.scalar(select(func.count()).select_from(TranscriptVersion)) == 0
