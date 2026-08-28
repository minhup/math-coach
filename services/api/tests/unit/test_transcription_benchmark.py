from decimal import Decimal
from pathlib import Path

import pytest
from app.scripts.benchmark_transcription import (
    assert_benchmark_approval,
    estimated_maximum_cost,
    load_synthetic_manifest,
)
from app.transcription.fake_provider import DeterministicFakeTranscriptionProvider
from app.transcription.gemini_provider import GeminiTranscriptionProvider

FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "transcription"


def test_benchmark_manifest_is_strict_synthetic_and_hash_verified() -> None:
    manifest = load_synthetic_manifest(FIXTURE_ROOT)

    assert len(manifest.fixtures) == 11
    assert manifest.provenance.classification == "original_synthetic_non_personal"
    assert manifest.provenance.personal_data is False
    assert manifest.provenance.real_learner_work is False


@pytest.mark.parametrize(
    ("model_snapshot", "expected_estimate", "insufficient_approval"),
    [
        ("gemini-3.5-flash-lite", Decimal("0.231000"), Decimal("0.230999")),
        ("gemini-3.5-flash", Decimal("0.924000"), Decimal("0.923999")),
    ],
)
def test_benchmark_requires_exact_real_identity_and_explicit_cost_approval(
    model_snapshot: str,
    expected_estimate: Decimal,
    insufficient_approval: Decimal,
) -> None:
    provider = GeminiTranscriptionProvider(
        api_key="server-only-test-secret",
        model_snapshot=model_snapshot,
    )
    estimate = estimated_maximum_cost(provider, fixture_count=11)

    assert estimate == expected_estimate
    assert_benchmark_approval(
        provider=provider,
        approved_provider="google-gemini",
        approved_model=model_snapshot,
        approved_fixture_count=11,
        actual_fixture_count=11,
        approved_max_cost_usd=estimate,
        acknowledge_synthetic_only=True,
        acknowledge_paid_network_calls=True,
    )

    with pytest.raises(ValueError, match="real provider"):
        assert_benchmark_approval(
            provider=DeterministicFakeTranscriptionProvider(),
            approved_provider="application-owned-deterministic-fake",
            approved_model="m6-transcription-fixture-v1",
            approved_fixture_count=11,
            actual_fixture_count=11,
            approved_max_cost_usd=Decimal("1"),
            acknowledge_synthetic_only=True,
            acknowledge_paid_network_calls=True,
        )
    with pytest.raises(ValueError, match="maximum cost"):
        assert_benchmark_approval(
            provider=provider,
            approved_provider="google-gemini",
            approved_model=model_snapshot,
            approved_fixture_count=11,
            actual_fixture_count=11,
            approved_max_cost_usd=insufficient_approval,
            acknowledge_synthetic_only=True,
            acknowledge_paid_network_calls=True,
        )
