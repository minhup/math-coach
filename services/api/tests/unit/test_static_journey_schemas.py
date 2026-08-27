import uuid

import pytest
from app.static_journey.schemas import (
    MockEvaluationRequest,
    MockEvaluationResponse,
)
from app.transcription.schemas import TranscriptDocument
from pydantic import ValidationError

ATTEMPT_ID = uuid.UUID("50000000-0000-4000-8000-000000000001")


def test_transcript_document_accepts_only_the_flat_strict_correction_contract() -> None:
    transcript = TranscriptDocument.model_validate(
        {
            "schemaVersion": "3.0.0",
            "attemptId": str(ATTEMPT_ID),
            "blocks": [
                {"id": "synthetic-text-1", "type": "text", "text": "Let M be the midpoint. "},
                {"id": "synthetic-math-1", "type": "math", "latex": "M=(2,0)"},
            ],
            "warnings": [],
        }
    )

    assert transcript.attempt_id == ATTEMPT_ID
    assert [block.type for block in transcript.blocks] == ["text", "math"]

    invalid = transcript.model_dump(by_alias=True)
    invalid["blocks"][0]["html"] = "<script>unsafe()</script>"
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        TranscriptDocument.model_validate(invalid)


def test_evaluation_contract_requires_an_explicit_confirmation_and_typed_feedback() -> None:
    version_id = uuid.uuid4()
    request = MockEvaluationRequest(confirmed_transcript_version_id=version_id)
    response = MockEvaluationResponse.model_validate(
        {
            "outcome": "ready",
            "feedback": [
                {"id": "feedback-1", "type": "text", "text": "Synthetic structured feedback."}
            ],
            "nextSteps": [
                {"id": "next-1", "type": "text", "text": "Request a hint before retrying."}
            ],
            "referenceSolutionsNonExhaustive": True,
            "transcriptFingerprint": "a" * 64,
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
    )

    assert request.confirmed_transcript_version_id == version_id
    assert response.reference_solutions_non_exhaustive is True
    assert response.feedback[0].type == "text"

    invalid = response.model_dump(by_alias=True)
    invalid["feedback"] = [{"markdown": "**unvalidated**"}]
    with pytest.raises(ValidationError):
        MockEvaluationResponse.model_validate(invalid)
