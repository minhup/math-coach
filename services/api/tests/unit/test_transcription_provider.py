import uuid
from collections.abc import Sequence
from decimal import Decimal

import pytest
from app.transcription.provider import (
    ConfiguredProviderIdentity,
    ProviderCall,
    ProviderRequest,
    ProviderSchemaError,
    StrictTranscriptionProvider,
)

ATTEMPT_ID = uuid.UUID("60000000-0000-4000-8000-000000000001")
ASSET_ID = uuid.UUID("60000000-0000-4000-8000-000000000002")


class SequenceProvider(StrictTranscriptionProvider):
    def __init__(self, payloads: Sequence[object]) -> None:
        super().__init__(
            ConfiguredProviderIdentity(
                provider="application-owned-deterministic-fake",
                model_snapshot="m6-transcription-fixture-v1",
                prompt_version="m6-faithful-transcription-v1",
                prompt_hash="a" * 64,
                schema_version="m6-provider-transcript-v1",
                pricing_version="fake-zero-v1",
                input_usd_per_million=Decimal("0"),
                output_usd_per_million=Decimal("0"),
            )
        )
        self.payloads = iter(payloads)
        self.repair_flags: list[bool] = []

    async def _invoke(self, request: ProviderRequest, *, repair_schema: bool) -> ProviderCall:
        self.repair_flags.append(repair_schema)
        return ProviderCall(
            payload=next(self.payloads),
            latency_ms=7,
            input_tokens=11,
            output_tokens=13,
        )


def request() -> ProviderRequest:
    return ProviderRequest(
        attempt_id=ATTEMPT_ID,
        attempt_asset_id=ASSET_ID,
        content_type="image/png",
        image_bytes=b"clearly-synthetic-image",
        problem_context="Synthetic problem version 1.",
    )


@pytest.mark.asyncio
async def test_provider_retries_one_schema_failure_and_returns_only_application_types() -> None:
    provider = SequenceProvider(
        [
            {"outcome": "ready", "blocks": [], "warnings": []},
            {
                "outcome": "ready",
                "blocks": [
                    {"type": "text", "text": "The learner wrote "},
                    {
                        "type": "math",
                        "latex": "x=-2",
                        "sourceRegion": {"x": 0.2, "y": 0.3, "width": 0.3, "height": 0.1},
                    },
                ],
                "warnings": [{"code": "low_confidence_math", "blockIndex": 1}],
            },
        ]
    )

    result = await provider.transcribe(request())

    assert provider.repair_flags == [False, True]
    assert result.schema_attempts == 2
    assert result.input_tokens == 22
    assert result.output_tokens == 26
    assert result.latency_ms == 14
    assert result.cost_usd == Decimal("0.000000")
    assert result.transcript is not None
    assert result.transcript.blocks[1].latex == "x=-2"
    assert result.transcript.blocks[1].source_region is not None
    assert result.transcript.blocks[1].source_region.attempt_asset_id == ASSET_ID
    assert result.identity.model_snapshot == "m6-transcription-fixture-v1"


@pytest.mark.asyncio
async def test_provider_stops_after_exactly_one_schema_retry_without_fabrication() -> None:
    provider = SequenceProvider(
        [
            {"outcome": "ready", "blocks": [], "warnings": []},
            {
                "outcome": "ready",
                "blocks": [{"type": "html", "html": "<b>no</b>"}],
                "warnings": [],
            },
            {"outcome": "ready", "blocks": [{"type": "text", "text": "too late"}]},
        ]
    )

    with pytest.raises(ProviderSchemaError) as caught:
        await provider.transcribe(request())

    assert caught.value.schema_attempts == 2
    assert provider.repair_flags == [False, True]


@pytest.mark.asyncio
async def test_uncertainty_has_no_transcript_and_does_not_retry() -> None:
    provider = SequenceProvider(
        [
            {
                "outcome": "uncertain",
                "warnings": [{"code": "ordering_uncertain"}],
            }
        ]
    )

    result = await provider.transcribe(request())

    assert result.outcome == "uncertain"
    assert result.transcript is None
    assert provider.repair_flags == [False]


@pytest.mark.asyncio
async def test_provider_cannot_override_configured_run_metadata() -> None:
    provider = SequenceProvider(
        [
            {
                "outcome": "ready",
                "provider": "malicious-provider-claim",
                "blocks": [{"type": "text", "text": "Visible work"}],
                "warnings": [],
            },
            {
                "outcome": "ready",
                "provider": "malicious-provider-claim",
                "blocks": [{"type": "text", "text": "Visible work"}],
                "warnings": [],
            },
        ]
    )

    with pytest.raises(ProviderSchemaError):
        await provider.transcribe(request())

    assert provider.repair_flags == [False, True]
