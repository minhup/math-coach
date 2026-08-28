import uuid

import pytest
from app.evaluation.schemas import EvaluationRequest
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


def test_evaluation_request_requires_confirmation_identity_and_server_owned_fields() -> None:
    version_id = uuid.uuid4()
    request = EvaluationRequest.model_validate(
        {
            "confirmedTranscriptVersionId": str(version_id),
            "idempotencyKey": str(uuid.uuid4()),
        }
    )

    assert request.confirmed_transcript_version_id == version_id
    with pytest.raises(ValidationError):
        EvaluationRequest.model_validate(
            {
                **request.model_dump(by_alias=True, mode="json"),
                "score": "4.00",
            }
        )
