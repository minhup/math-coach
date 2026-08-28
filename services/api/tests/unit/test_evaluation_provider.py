import json
import uuid
from collections.abc import Sequence
from decimal import Decimal
from pathlib import Path

import pytest
from app.evaluation.provider import (
    EvaluationProviderCall,
    EvaluationProviderIdentity,
    EvaluationProviderRequest,
    EvaluationProviderSchemaError,
    StrictEvaluationProvider,
)

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures/evaluation/recorded-provider-shapes.json"


class SequenceEvaluationProvider(StrictEvaluationProvider):
    def __init__(self, payloads: Sequence[object]) -> None:
        super().__init__(
            EvaluationProviderIdentity(
                provider="application-owned-recorded-shape",
                model_snapshot="m7-evaluation-fixture-v1",
                prompt_version="m7-evaluation-v1",
                prompt_hash="a" * 64,
                schema_version="m7-provider-evaluation-v1",
                pricing_version="fake-zero-v1",
                input_usd_per_million=Decimal("0"),
                output_usd_per_million=Decimal("0"),
            )
        )
        self.payloads = iter(payloads)
        self.repair_flags: list[bool] = []

    async def _invoke(
        self, request: EvaluationProviderRequest, *, repair_schema: bool
    ) -> EvaluationProviderCall:
        self.repair_flags.append(repair_schema)
        return EvaluationProviderCall(
            payload=next(self.payloads), latency_ms=3, input_tokens=5, output_tokens=7
        )


def request() -> EvaluationProviderRequest:
    return EvaluationProviderRequest(
        attempt_id=uuid.UUID("70000000-0000-4000-8000-000000000001"),
        transcript_block_ids=("block-1", "block-2"),
        rubric_limits=(("method", Decimal("2")), ("conclusion", Decimal("2"))),
        context_json="{}",
    )


def shapes() -> dict[str, object]:
    value = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


@pytest.mark.asyncio
async def test_recorded_production_shape_is_validated_and_metadata_is_server_owned() -> None:
    provider = SequenceEvaluationProvider([shapes()["readyAlternative"]])

    result = await provider.evaluate(request())

    assert result.outcome == "ready"
    assert result.identity.provider == "application-owned-recorded-shape"
    assert result.schema_attempts == 1
    assert result.cost_usd == Decimal("0.000000")
    assert provider.repair_flags == [False]


@pytest.mark.asyncio
async def test_provider_performs_exactly_one_schema_repair_attempt() -> None:
    invalid = {"outcome": "ready", "reasoningSteps": []}
    provider = SequenceEvaluationProvider([invalid, shapes()["readyAlternative"]])

    result = await provider.evaluate(request())

    assert result.schema_attempts == 2
    assert result.latency_ms == 6
    assert result.input_tokens == 10
    assert result.output_tokens == 14
    assert provider.repair_flags == [False, True]


@pytest.mark.asyncio
async def test_provider_stops_after_one_failed_repair_without_fabricating_result() -> None:
    invalid = {"outcome": "ready", "reasoningSteps": []}
    provider = SequenceEvaluationProvider([invalid, invalid, shapes()["readyAlternative"]])

    with pytest.raises(EvaluationProviderSchemaError) as caught:
        await provider.evaluate(request())

    assert caught.value.schema_attempts == 2
    assert provider.repair_flags == [False, True]


@pytest.mark.asyncio
async def test_provider_rejects_missing_transcript_coverage_and_excess_rubric_award() -> None:
    payload = shapes()["readyAlternative"]
    assert isinstance(payload, dict)
    awards = payload["rubricAwards"]
    assert isinstance(awards, list)
    assert isinstance(awards[0], dict)
    awards[0]["awardedScore"] = "3.00"
    provider = SequenceEvaluationProvider([payload, payload])

    with pytest.raises(EvaluationProviderSchemaError):
        await provider.evaluate(request())


@pytest.mark.asyncio
async def test_uncertain_recorded_shape_returns_no_fabricated_ready_payload() -> None:
    provider = SequenceEvaluationProvider([shapes()["uncertain"]])

    result = await provider.evaluate(request())

    assert result.outcome == "uncertain"
    assert result.payload.outcome == "uncertain"
