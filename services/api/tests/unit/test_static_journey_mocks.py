import uuid

import pytest
from app.static_journey.mocks import (
    DeterministicMockBoundary,
    MockPayloadInvalidError,
    MockSourceError,
    RawMockSource,
)
from app.transcription.schemas import TranscriptDocument

ATTEMPT_ID = uuid.UUID("50000000-0000-4000-8000-000000000001")


class UncertainEvaluationSource(RawMockSource):
    def evaluation_payload(self, transcript_fingerprint: str) -> object:
        return {
            "outcome": "uncertain",
            "feedback": [
                {
                    "id": "uncertain-feedback",
                    "type": "text",
                    "text": "The synthetic fixture cannot make a confident judgment.",
                }
            ],
            "nextSteps": [
                {
                    "id": "uncertain-next",
                    "type": "text",
                    "text": "Review the confirmed work before retrying.",
                }
            ],
            "referenceSolutionsNonExhaustive": True,
            "transcriptFingerprint": transcript_fingerprint,
            "metadata": {
                "provider": "application-owned-synthetic-mock",
                "modelSnapshot": "m5-static-fixture-v1",
                "promptVersion": "m5-no-provider-prompt-v1",
                "schemaVersion": "1.0.0",
                "latencyMs": 0,
                "inputTokens": 0,
                "outputTokens": 0,
                "costUsd": "0.000000",
            },
        }


class WrongFingerprintSource(UncertainEvaluationSource):
    def evaluation_payload(self, transcript_fingerprint: str) -> object:
        payload = super().evaluation_payload(transcript_fingerprint)
        assert isinstance(payload, dict)
        payload["transcriptFingerprint"] = "0" * 64
        return payload


class FailedSource(RawMockSource):
    def evaluation_payload(self, transcript_fingerprint: str) -> object:
        raise MockSourceError(retryable=False)


def test_mock_evaluation_fingerprints_only_the_confirmed_transcript_and_preserves_uncertainty() -> (
    None
):
    transcript = TranscriptDocument.model_validate(
        {
            "schemaVersion": "3.0.0",
            "attemptId": str(ATTEMPT_ID),
            "blocks": [{"id": "synthetic-text-1", "type": "text", "text": "Reviewed."}],
            "warnings": [],
        }
    )

    response = DeterministicMockBoundary(UncertainEvaluationSource()).evaluate(transcript)

    assert response.outcome == "uncertain"
    assert response.transcript_fingerprint == (
        "3a2bac73909692637259bf7b7fbbfa942c03f87416321b5c3806ffbbed2b66e8"
    )


def test_mock_evaluation_rejects_a_payload_for_a_different_confirmed_transcript() -> None:
    transcript = TranscriptDocument.model_validate(
        {
            "schemaVersion": "3.0.0",
            "attemptId": str(ATTEMPT_ID),
            "blocks": [{"id": "synthetic-text-1", "type": "text", "text": "Reviewed."}],
            "warnings": [],
        }
    )

    with pytest.raises(MockPayloadInvalidError):
        DeterministicMockBoundary(WrongFingerprintSource()).evaluate(transcript)


def test_mock_source_failure_never_turns_into_a_fixture_success() -> None:
    boundary = DeterministicMockBoundary(FailedSource())
    transcript = TranscriptDocument.model_validate(
        {
            "schemaVersion": "3.0.0",
            "attemptId": str(ATTEMPT_ID),
            "blocks": [{"id": "visible", "type": "text", "text": "Visible work"}],
            "warnings": [],
        }
    )

    with pytest.raises(MockSourceError, match="permanent"):
        boundary.evaluate(transcript)
