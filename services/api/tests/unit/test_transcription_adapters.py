import json
import uuid
from pathlib import Path

import httpx
import pytest
from app.config import Settings
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


@pytest.mark.asyncio
async def test_gemini_uses_exact_server_model_image_and_structured_schema() -> None:
    seen: list[httpx.Request] = []

    def handler(http_request: httpx.Request) -> httpx.Response:
        seen.append(http_request)
        return httpx.Response(200, json=recorded_shapes()["providerEnvelopes"]["gemini"])

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = GeminiTranscriptionProvider(api_key="server-secret", client=client)
        result = await provider.transcribe(request())

    assert result.identity.model_snapshot == "gemini-3.5-flash"
    assert result.transcript is not None
    assert result.transcript.blocks[1].latex == "x=-2"
    assert len(seen) == 1
    assert seen[0].headers["x-goog-api-key"] == "server-secret"
    assert "server-secret" not in str(seen[0].url)
    body = json.loads(seen[0].content)
    assert body["generationConfig"]["responseMimeType"] == "application/json"
    assert body["generationConfig"]["responseJsonSchema"]["$defs"]
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
        provider = GeminiTranscriptionProvider(api_key="server-secret", client=client)
        with pytest.raises(ProviderTransportError) as caught:
            await provider.transcribe(request())

    assert caught.value.code == "rate_limited"
    assert "raw provider" not in str(caught.value)
    assert calls == 1


def test_server_configuration_requires_exact_model_and_selected_secret() -> None:
    gemini = Settings(
        transcription_provider="gemini",
        transcription_model_snapshot="gemini-3.5-flash",
        gemini_api_key="secret",
    )
    assert gemini.transcription_model_snapshot == "gemini-3.5-flash"

    with pytest.raises(ValueError, match="exact model"):
        Settings(
            transcription_provider="gemini",
            transcription_model_snapshot="gemini-latest",
            gemini_api_key="secret",
        )
    with pytest.raises(ValueError, match="API key"):
        Settings(
            transcription_provider="gemini",
            transcription_model_snapshot="gemini-3.5-flash",
        )
    with pytest.raises(ValueError, match="API key"):
        Settings(
            transcription_provider="gemini",
            transcription_model_snapshot="gemini-3.5-flash",
            gemini_api_key="   ",
        )
