import hashlib
import json
import uuid
from collections.abc import Callable
from decimal import Decimal
from functools import lru_cache
from typing import Protocol

from pydantic import BaseModel, ValidationError

from app.static_journey.schemas import (
    ConfirmedTranscript,
    MockEvaluationResponse,
    MockRunMetadata,
    MockTranscriptionResponse,
    TranscriptDocument,
)


class RawMockSource(Protocol):
    def transcript_payload(self, attempt_id: uuid.UUID) -> object: ...

    def evaluation_payload(self, transcript_fingerprint: str) -> object: ...


class MockPayloadInvalidError(Exception):
    pass


class MockSourceError(Exception):
    def __init__(self, *, retryable: bool) -> None:
        self.retryable = retryable
        super().__init__(
            "retryable mock source failure" if retryable else "permanent mock source failure"
        )


class StaticFixtureSource:
    def transcript_payload(self, attempt_id: uuid.UUID) -> object:
        return {
            "schemaVersion": "2.0.0",
            "attemptId": str(attempt_id),
            "blocks": [
                {
                    "id": "m5-synthetic-text-1",
                    "type": "text",
                    "text": "The synthetic draft gives the midpoint as ",
                },
                {
                    "id": "m5-synthetic-math-1",
                    "type": "math",
                    "latex": "M=(2,0",
                },
                {
                    "id": "m5-synthetic-text-2",
                    "type": "text",
                    "text": ". Review both the wording and mathematics before confirmation.",
                },
            ],
        }

    def evaluation_payload(self, transcript_fingerprint: str) -> object:
        return {
            "outcome": "ready",
            "feedback": [
                {
                    "id": "m5-feedback-1",
                    "type": "text",
                    "text": (
                        "This is deterministic synthetic feedback for the confirmed document, "
                        "not a real grade."
                    ),
                },
                {
                    "id": "m5-feedback-2",
                    "type": "rich_line",
                    "spans": [
                        {"type": "text", "text": "Keep the midpoint relationship "},
                        {"type": "math", "latex": "M=\\frac{A+B}{2}"},
                        {"type": "text", "text": " explicit in the retry."},
                    ],
                },
            ],
            "nextSteps": [
                {
                    "id": "m5-next-1",
                    "type": "text",
                    "text": "Request the next curated hint, then begin a new attempt.",
                }
            ],
            "referenceSolutionsNonExhaustive": True,
            "transcriptFingerprint": transcript_fingerprint,
            "metadata": mock_metadata().model_dump(by_alias=True, mode="json"),
        }


class UncertainFixtureSource(StaticFixtureSource):
    def evaluation_payload(self, transcript_fingerprint: str) -> object:
        return {
            "outcome": "uncertain",
            "feedback": [
                {
                    "id": "m5-uncertain-feedback",
                    "type": "text",
                    "text": (
                        "The deterministic fixture cannot make a confident judgment from this "
                        "confirmed document."
                    ),
                }
            ],
            "nextSteps": [
                {
                    "id": "m5-uncertain-next",
                    "type": "text",
                    "text": "Review the confirmed work before requesting a curated hint.",
                }
            ],
            "referenceSolutionsNonExhaustive": True,
            "transcriptFingerprint": transcript_fingerprint,
            "metadata": mock_metadata().model_dump(by_alias=True, mode="json"),
        }


class FailedFixtureSource(StaticFixtureSource):
    def __init__(self, *, retryable: bool) -> None:
        self._retryable = retryable

    def transcript_payload(self, attempt_id: uuid.UUID) -> object:
        raise MockSourceError(retryable=self._retryable)

    def evaluation_payload(self, transcript_fingerprint: str) -> object:
        raise MockSourceError(retryable=self._retryable)


def mock_metadata() -> MockRunMetadata:
    return MockRunMetadata(
        provider="application-owned-synthetic-mock",
        model_snapshot="m5-static-fixture-v1",
        prompt_version="m5-no-provider-prompt-v1",
        schema_version="1.0.0",
        latency_ms=0,
        input_tokens=0,
        output_tokens=0,
        cost_usd=Decimal("0.000000"),
    )


def validate_mock_payload[ValidatedModel: BaseModel](
    model: type[ValidatedModel],
    load_payload: Callable[[], object],
    accept: Callable[[ValidatedModel], bool] | None = None,
) -> ValidatedModel:
    last_error: ValidationError | None = None
    for _attempt in range(2):
        try:
            validated = model.model_validate(load_payload())
            if accept is None or accept(validated):
                return validated
        except ValidationError as error:
            last_error = error
    raise MockPayloadInvalidError("Synthetic mock payload failed strict validation") from last_error


class DeterministicMockBoundary:
    def __init__(self, source: RawMockSource) -> None:
        self._source = source

    def transcribe(self, attempt_id: uuid.UUID) -> MockTranscriptionResponse:
        transcript = validate_mock_payload(
            TranscriptDocument,
            lambda: self._source.transcript_payload(attempt_id),
            lambda item: item.attempt_id == attempt_id,
        )
        return MockTranscriptionResponse(transcript=transcript, metadata=mock_metadata())

    def evaluate(self, confirmed: ConfirmedTranscript) -> MockEvaluationResponse:
        canonical = json.dumps(
            confirmed.transcript.model_dump(by_alias=True, mode="json"),
            separators=(",", ":"),
            sort_keys=True,
        ).encode()
        fingerprint = hashlib.sha256(canonical).hexdigest()
        return validate_mock_payload(
            MockEvaluationResponse,
            lambda: self._source.evaluation_payload(fingerprint),
            lambda item: item.transcript_fingerprint == fingerprint,
        )


@lru_cache
def get_mock_boundary() -> DeterministicMockBoundary:
    return DeterministicMockBoundary(StaticFixtureSource())
