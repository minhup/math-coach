import json
import uuid
from decimal import Decimal
from pathlib import Path

import httpx
import pytest
from app.config import Settings
from app.evaluation import service as evaluation_service
from app.evaluation.gemini_provider import GeminiEvaluationProvider
from app.evaluation.provider import EvaluationProviderRequest, EvaluationProviderTransportError

SHAPES = Path(__file__).resolve().parents[1] / "fixtures/evaluation/recorded-provider-shapes.json"


def ready_shape() -> object:
    value = json.loads(SHAPES.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value["readyAlternative"]


def request() -> EvaluationProviderRequest:
    return EvaluationProviderRequest(
        attempt_id=uuid.UUID("70000000-0000-4000-8000-000000000001"),
        transcript_block_ids=("block-1", "block-2"),
        rubric_limits=(("method", Decimal("2")), ("conclusion", Decimal("2"))),
        context_json='{"confirmedTranscript":"synthetic"}',
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("model_snapshot", "pricing_version", "expected_cost"),
    [
        ("gemini-3.5-flash-lite", "gemini-3.5-flash-lite-2026-08-28", "0.013000"),
        ("gemini-3.5-flash", "gemini-3.5-flash-2026-08-27", "0.051000"),
    ],
)
async def test_gemini_evaluation_uses_exact_server_model_and_structured_json(
    model_snapshot: str, pricing_version: str, expected_cost: str
) -> None:
    requests: list[httpx.Request] = []

    def handler(http_request: httpx.Request) -> httpx.Response:
        requests.append(http_request)
        return httpx.Response(
            200,
            json={
                "candidates": [{"content": {"parts": [{"text": json.dumps(ready_shape())}]}}],
                "usageMetadata": {"promptTokenCount": 10_000, "candidatesTokenCount": 4_000},
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = GeminiEvaluationProvider(
            api_key="server-secret", model_snapshot=model_snapshot, client=client
        )
        result = await provider.evaluate(request())

    assert result.outcome == "ready"
    assert result.identity.model_snapshot == model_snapshot
    assert result.identity.pricing_version == pricing_version
    assert str(provider.cost(input_tokens=10_000, output_tokens=4_000)) == expected_cost
    assert len(requests) == 1
    assert f"/models/{model_snapshot}:generateContent" in str(requests[0].url)
    assert requests[0].headers["x-goog-api-key"] == "server-secret"
    assert "server-secret" not in str(requests[0].url)
    body = json.loads(requests[0].content)
    assert body["generationConfig"]["responseMimeType"] == "application/json"
    assert body["generationConfig"]["maxOutputTokens"] == 4_000
    assert body["generationConfig"]["responseJsonSchema"]["required"] == ["outcome"]
    prompt = body["contents"][0]["parts"][0]["text"]
    assert "non-exhaustive" in prompt
    assert "confirmedTranscript" in prompt


@pytest.mark.asyncio
async def test_rate_limit_is_retryable_and_not_automatically_retried() -> None:
    calls = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(429, json={"error": {"message": "unsafe provider detail"}})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = GeminiEvaluationProvider(
            api_key="server-secret", model_snapshot="gemini-3.5-flash-lite", client=client
        )
        with pytest.raises(EvaluationProviderTransportError) as caught:
            await provider.evaluate(request())

    assert caught.value.code == "rate_limited"
    assert "unsafe provider" not in str(caught.value)
    assert calls == 1


def test_evaluation_configuration_requires_exact_model_and_server_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("MATH_COACH_GEMINI_API_KEY", raising=False)
    settings = Settings(
        _env_file=None,
        evaluation_provider="gemini",
        evaluation_model_snapshot="gemini-3.5-flash-lite",
        gemini_api_key="secret",
    )
    assert settings.evaluation_model_snapshot == "gemini-3.5-flash-lite"

    with pytest.raises(ValueError, match="exact model"):
        Settings(
            _env_file=None,
            evaluation_provider="gemini",
            evaluation_model_snapshot="gemini-latest",
            gemini_api_key="secret",
        )
    with pytest.raises(ValueError, match="API key"):
        Settings(
            _env_file=None,
            evaluation_provider="gemini",
            evaluation_model_snapshot="gemini-3.5-flash",
        )


def test_evaluation_factory_is_independent_from_transcription_selection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = Settings(
        _env_file=None,
        transcription_provider="fake",
        evaluation_provider="gemini",
        evaluation_model_snapshot="gemini-3.5-flash",
        gemini_api_key="secret",
    )
    monkeypatch.setattr(evaluation_service, "get_settings", lambda: settings)
    evaluation_service.get_evaluation_provider.cache_clear()
    try:
        provider = evaluation_service.get_evaluation_provider()
    finally:
        evaluation_service.get_evaluation_provider.cache_clear()

    assert provider.identity.model_snapshot == "gemini-3.5-flash"
    assert provider.identity.pricing_version == "gemini-3.5-flash-2026-08-27"
