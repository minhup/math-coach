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


def test_benchmark_requires_exact_real_identity_and_explicit_cost_approval() -> None:
    provider = GeminiTranscriptionProvider(api_key="server-only-test-secret")
    estimate = estimated_maximum_cost(provider, fixture_count=11)

    assert estimate == Decimal("0.924000")
    assert_benchmark_approval(
        provider=provider,
        approved_provider="google-gemini",
        approved_model="gemini-3.5-flash",
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
            approved_model="gemini-3.5-flash",
            approved_fixture_count=11,
            actual_fixture_count=11,
            approved_max_cost_usd=Decimal("0.92"),
            acknowledge_synthetic_only=True,
            acknowledge_paid_network_calls=True,
        )
