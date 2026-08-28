import json
import uuid
from pathlib import Path

import httpx
import pytest
from app.config import Settings
from app.transcription import service as transcription_service
from app.transcription.anthropic_provider import AnthropicTranscriptionProvider
from app.transcription.fake_provider import DeterministicFakeTranscriptionProvider
from app.transcription.gemini_provider import GeminiTranscriptionProvider
from app.transcription.openai_provider import OpenAITranscriptionProvider
from app.transcription.provider import ProviderRequest, ProviderTransportError

ATTEMPT_ID = uuid.UUID("60000000-0000-4000-8000-000000000001")
ASSET_ID = uuid.UUID("60000000-0000-4000-8000-000000000002")
SHAPES_PATH = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "transcription"
    / "recorded-provider-shapes.json"
)


def recorded_shapes() -> dict[str, object]:
    value = json.loads(SHAPES_PATH.read_text(encoding="utf-8"))
    assert value["provenance"]["containsRealProviderResponse"] is False
    return value


def request() -> ProviderRequest:
    return ProviderRequest(
        attempt_id=ATTEMPT_ID,
        attempt_asset_id=ASSET_ID,
        content_type="image/png",
        image_bytes=b"\x89PNG\r\n\x1a\nclearly-synthetic",
        problem_context="Synthetic immutable problem version.",
    )


def schema_keywords(value: object, *, schema_map: bool = False) -> set[str]:
    if isinstance(value, dict):
        if schema_map:
            return {keyword for child in value.values() for keyword in schema_keywords(child)}
        keywords = set(value)
        for key, child in value.items():
            keywords |= schema_keywords(
                child,
                schema_map=key in {"$defs", "properties"},
            )
        return keywords
    if isinstance(value, list):
        return {keyword for child in value for keyword in schema_keywords(child)}
    return set()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("model_snapshot", "pricing_version", "expected_cost"),
    [
        (
            "gemini-3.5-flash-lite",
            "gemini-3.5-flash-lite-2026-08-28",
            "0.010500",
        ),
        ("gemini-3.5-flash", "gemini-3.5-flash-2026-08-27", "0.042000"),
    ],
)
async def test_gemini_uses_selected_exact_server_model_image_and_structured_schema(
    model_snapshot: str,
    pricing_version: str,
    expected_cost: str,
) -> None:
    seen: list[httpx.Request] = []

    def handler(http_request: httpx.Request) -> httpx.Response:
        seen.append(http_request)
        return httpx.Response(200, json=recorded_shapes()["providerEnvelopes"]["gemini"])

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = GeminiTranscriptionProvider(
            api_key="server-secret",
            model_snapshot=model_snapshot,
            client=client,
        )
        result = await provider.transcribe(request())

    assert result.identity.model_snapshot == model_snapshot
    assert result.identity.pricing_version == pricing_version
    assert str(provider.cost(input_tokens=10_000, output_tokens=3_000)) == expected_cost
    assert result.transcript is not None
    assert result.transcript.blocks[1].latex == "x=-2"
    assert len(seen) == 1
    assert f"/models/{model_snapshot}:generateContent" in str(seen[0].url)
    assert seen[0].headers["x-goog-api-key"] == "server-secret"
    assert "server-secret" not in str(seen[0].url)
    body = json.loads(seen[0].content)
    assert body["generationConfig"]["responseMimeType"] == "application/json"
    assert "responseSchema" not in body["generationConfig"]
    response_schema = body["generationConfig"]["responseJsonSchema"]
    assert schema_keywords(response_schema) <= {
        "enum",
        "items",
        "properties",
        "required",
        "type",
    }
    assert response_schema["type"] == "object"
    assert response_schema["required"] == ["outcome"]
    assert response_schema["properties"]["outcome"]["enum"] == ["ready", "uncertain"]
    block_schema = response_schema["properties"]["blocks"]["items"]
    assert block_schema["type"] == "object"
    assert block_schema["required"] == ["type"]
    assert block_schema["properties"]["type"]["enum"] == ["text", "math"]
    assert body["generationConfig"]["maxOutputTokens"] == 3_000
    assert body["contents"][0]["parts"][1]["inlineData"]["mimeType"] == "image/png"
    assert body["contents"][0]["parts"][1]["inlineData"]["data"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("provider_type", "response", "model"),
    [
        (
            OpenAITranscriptionProvider,
            recorded_shapes()["providerEnvelopes"]["openai"],
            "gpt-5.4-2026-03-05",
        ),
        (
            AnthropicTranscriptionProvider,
            recorded_shapes()["providerEnvelopes"]["anthropic"],
            "claude-sonnet-5",
        ),
    ],
)
async def test_optional_real_adapters_use_exact_server_owned_models(
    provider_type: type[OpenAITranscriptionProvider] | type[AnthropicTranscriptionProvider],
    response: dict[str, object],
    model: str,
) -> None:
    requests: list[httpx.Request] = []

    def handler(http_request: httpx.Request) -> httpx.Response:
        requests.append(http_request)
        return httpx.Response(200, json=response)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = provider_type(api_key="server-secret", client=client)
        result = await provider.transcribe(request())

    assert result.identity.model_snapshot == model
    assert result.transcript is not None
    body = json.loads(requests[0].content)
    assert body["model"] == model
    assert "provider" not in body
    if model == "gpt-5.4-2026-03-05":
        assert body["max_output_tokens"] == 3_000
        assert body["reasoning"] == {"effort": "none"}
        assert body["store"] is False
    else:
        assert body["max_tokens"] == 3_000
        assert body["thinking"] == {"type": "disabled"}


@pytest.mark.asyncio
async def test_deterministic_fake_uses_production_boundary_and_preserves_visible_error() -> None:
    result = await DeterministicFakeTranscriptionProvider().transcribe(request())

    assert result.identity.provider == "application-owned-deterministic-fake"
    assert result.cost_usd.is_zero()
    assert result.transcript is not None
    assert [block.type for block in result.transcript.blocks] == ["text", "math", "text"]
    assert result.transcript.blocks[1].latex == "M=(2,0"
    assert result.transcript.warnings[0].code == "low_confidence_math"


@pytest.mark.asyncio
async def test_rate_limit_is_safe_retryable_and_is_not_automatically_retried() -> None:
    calls = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(429, json={"error": {"message": "raw provider secret detail"}})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = GeminiTranscriptionProvider(
            api_key="server-secret",
            model_snapshot="gemini-3.5-flash-lite",
            client=client,
        )
        with pytest.raises(ProviderTransportError) as caught:
            await provider.transcribe(request())

    assert caught.value.code == "rate_limited"
    assert "raw provider" not in str(caught.value)
    assert calls == 1


def test_server_configuration_requires_exact_model_and_selected_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("MATH_COACH_GEMINI_API_KEY", raising=False)
    gemini = Settings(
        _env_file=None,
        transcription_provider="gemini",
        transcription_model_snapshot="gemini-3.5-flash",
        gemini_api_key="secret",
    )
    assert gemini.transcription_model_snapshot == "gemini-3.5-flash"

    flash_lite = Settings(
        _env_file=None,
        transcription_provider="gemini",
        transcription_model_snapshot="gemini-3.5-flash-lite",
        gemini_api_key="secret",
    )
    assert flash_lite.transcription_model_snapshot == "gemini-3.5-flash-lite"

    with pytest.raises(ValueError, match="exact model"):
        Settings(
            _env_file=None,
            transcription_provider="gemini",
            transcription_model_snapshot="gemini-latest",
            gemini_api_key="secret",
        )
    with pytest.raises(ValueError, match="API key"):
        Settings(
            _env_file=None,
            transcription_provider="gemini",
            transcription_model_snapshot="gemini-3.5-flash",
        )
    with pytest.raises(ValueError, match="API key"):
        Settings(
            _env_file=None,
            transcription_provider="gemini",
            transcription_model_snapshot="gemini-3.5-flash",
            gemini_api_key="   ",
        )


def test_provider_factory_uses_server_selected_gemini_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = Settings(
        _env_file=None,
        transcription_provider="gemini",
        transcription_model_snapshot="gemini-3.5-flash-lite",
        gemini_api_key="secret",
    )
    monkeypatch.setattr(transcription_service, "get_settings", lambda: settings)
    transcription_service.get_transcription_provider.cache_clear()

    try:
        provider = transcription_service.get_transcription_provider()
    finally:
        transcription_service.get_transcription_provider.cache_clear()

    assert provider.identity.model_snapshot == "gemini-3.5-flash-lite"
    assert provider.identity.pricing_version == "gemini-3.5-flash-lite-2026-08-28"
