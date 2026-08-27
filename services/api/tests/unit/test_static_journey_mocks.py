import uuid

import pytest

from app.static_journey.mocks import (
    DeterministicMockBoundary,
    MockPayloadInvalidError,
    MockSourceError,
    RawMockSource,
)
from app.static_journey.schemas import ConfirmedTranscript, TranscriptDocument

ATTEMPT_ID = uuid.UUID("50000000-0000-4000-8000-000000000001")


class TranscriptSequenceSource(RawMockSource):
    def __init__(self, payloads: list[object]) -> None:
        self.payloads = iter(payloads)

    def transcript_payload(self, attempt_id: uuid.UUID) -> object:
        return next(self.payloads)

    def evaluation_payload(self, transcript_fingerprint: str) -> object:
        raise AssertionError("Evaluation is outside this test")


class UncertainEvaluationSource(RawMockSource):
    def transcript_payload(self, attempt_id: uuid.UUID) -> object:
        raise AssertionError("Transcription is outside this test")

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
    def transcript_payload(self, attempt_id: uuid.UUID) -> object:
        raise MockSourceError(retryable=True)

    def evaluation_payload(self, transcript_fingerprint: str) -> object:
        raise MockSourceError(retryable=False)


def test_mock_transcription_validates_unknown_output_and_retries_one_schema_failure() -> None:
    source = TranscriptSequenceSource(
        [
            {"schemaVersion": "2.0.0", "attemptId": str(ATTEMPT_ID), "blocks": []},
            {
                "schemaVersion": "2.0.0",
                "attemptId": str(ATTEMPT_ID),
                "blocks": [
                    {
                        "id": "synthetic-text-1",
                        "type": "text",
                        "text": "Let M be the midpoint. ",
                    },
                    {"id": "synthetic-math-1", "type": "math", "latex": "M=(2,0"},
                ],
            },
        ]
    )

    response = DeterministicMockBoundary(source).transcribe(ATTEMPT_ID)

    assert response.transcript.attempt_id == ATTEMPT_ID
    assert response.transcript.blocks[1].type == "math"
    assert response.metadata.provider == "application-owned-synthetic-mock"


def test_mock_transcription_stops_after_one_schema_retry_without_fabricating_output() -> None:
    source = TranscriptSequenceSource(
        [
            {"schemaVersion": "2.0.0", "attemptId": str(ATTEMPT_ID), "blocks": []},
            {"schemaVersion": "2.0.0", "attemptId": str(ATTEMPT_ID), "blocks": []},
            {
                "schemaVersion": "2.0.0",
                "attemptId": str(ATTEMPT_ID),
                "blocks": [{"id": "too-late", "type": "text", "text": "Do not use."}],
            },
        ]
    )

    with pytest.raises(MockPayloadInvalidError):
        DeterministicMockBoundary(source).transcribe(ATTEMPT_ID)


def test_mock_evaluation_fingerprints_only_the_confirmed_transcript_and_preserves_uncertainty() -> (
    None
):
    transcript = TranscriptDocument.model_validate(
        {
            "schemaVersion": "2.0.0",
            "attemptId": str(ATTEMPT_ID),
            "blocks": [{"id": "synthetic-text-1", "type": "text", "text": "Reviewed."}],
        }
    )
    confirmed = ConfirmedTranscript(
        confirmation_status="confirmed",
        transcript=transcript,
    )

    response = DeterministicMockBoundary(UncertainEvaluationSource()).evaluate(confirmed)

    assert response.outcome == "uncertain"
    assert response.transcript_fingerprint == (
        "f9e5bc3312a24cb01007b1ff5b7b84bb3ffcb3f71c4f040a521ee6137a9d4400"
    )


def test_mock_evaluation_rejects_a_payload_for_a_different_confirmed_transcript() -> None:
    transcript = TranscriptDocument.model_validate(
        {
            "schemaVersion": "2.0.0",
            "attemptId": str(ATTEMPT_ID),
            "blocks": [{"id": "synthetic-text-1", "type": "text", "text": "Reviewed."}],
        }
    )
    confirmed = ConfirmedTranscript(
        confirmation_status="confirmed",
        transcript=transcript,
    )

    with pytest.raises(MockPayloadInvalidError):
        DeterministicMockBoundary(WrongFingerprintSource()).evaluate(confirmed)


def test_mock_source_failure_never_turns_into_a_fixture_success() -> None:
    boundary = DeterministicMockBoundary(FailedSource())

    with pytest.raises(MockSourceError, match="retryable"):
        boundary.transcribe(ATTEMPT_ID)
