import uuid

import pytest
from app.transcription.schemas import (
    ProviderReadyPayload,
    ProviderUncertainPayload,
    SourceRegion,
    TranscriptDocument,
    TranscriptWarning,
    canonical_transcript_hash,
)
from pydantic import ValidationError

ATTEMPT_ID = uuid.UUID("60000000-0000-4000-8000-000000000001")
ASSET_ID = uuid.UUID("60000000-0000-4000-8000-000000000002")


def test_provider_payload_is_a_strict_flat_text_math_document() -> None:
    payload = ProviderReadyPayload.model_validate(
        {
            "outcome": "ready",
            "blocks": [
                {
                    "type": "text",
                    "text": "Em giữ nguyên lỗi dấu: ",
                    "sourceRegion": {"x": 0.1, "y": 0.2, "width": 0.4, "height": 0.1},
                },
                {"type": "math", "latex": "x=-2"},
            ],
            "warnings": [{"code": "low_confidence_math", "blockIndex": 1}],
        }
    )

    assert [block.type for block in payload.blocks] == ["text", "math"]
    assert payload.blocks[1].latex == "x=-2"

    invalid = payload.model_dump(by_alias=True)
    invalid["markdown"] = "**do not render**"
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        ProviderReadyPayload.model_validate(invalid)


@pytest.mark.parametrize(
    "block",
    [
        {"type": "text", "text": "**provider markdown**"},
        {"type": "text", "text": "<script>provider code</script>"},
        {"type": "text", "text": "https://unsupported.example/student"},
        {"type": "math", "latex": r"\href{https://unsupported.example}{x}"},
    ],
)
def test_provider_blocks_reject_markup_code_and_urls_embedded_in_strings(block: object) -> None:
    with pytest.raises(ValidationError, match="plain visible content"):
        ProviderReadyPayload.model_validate({"outcome": "ready", "blocks": [block], "warnings": []})


def test_uncertain_payload_cannot_reference_nonexistent_blocks() -> None:
    with pytest.raises(ValidationError, match="cannot reference a block"):
        ProviderUncertainPayload.model_validate(
            {
                "outcome": "uncertain",
                "warnings": [{"code": "ordering_uncertain", "blockIndex": 0}],
            }
        )


@pytest.mark.parametrize(
    "region",
    [
        {"x": -0.1, "y": 0, "width": 0.2, "height": 0.2},
        {"x": 0.9, "y": 0, "width": 0.2, "height": 0.2},
        {"x": 0, "y": 0.9, "width": 0.2, "height": 0.2},
        {"x": 0, "y": 0, "width": 0, "height": 0.2},
    ],
)
def test_source_regions_are_finite_normalized_and_inside_one_owned_image(region: object) -> None:
    with pytest.raises(ValidationError):
        SourceRegion.model_validate(
            {"attemptAssetId": str(ASSET_ID), "units": "normalized", **region}  # type: ignore[arg-type]
        )


def test_application_warning_message_is_fixed_by_its_finite_code() -> None:
    warning = TranscriptWarning.from_provider_code(
        code="ambiguous_cross_out",
        block_id="m6-block-0001",
    )

    assert warning.message == "A crossed-out part may need review."
    with pytest.raises(ValidationError, match="does not match"):
        TranscriptWarning.model_validate(
            {
                "code": "ambiguous_cross_out",
                "message": "Provider-controlled arbitrary prose",
                "blockId": "m6-block-0001",
            }
        )


def test_transcript_hash_covers_exact_canonical_order_and_preserved_error() -> None:
    transcript = TranscriptDocument.model_validate(
        {
            "schemaVersion": "3.0.0",
            "attemptId": str(ATTEMPT_ID),
            "blocks": [
                {"id": "m6-block-0001", "type": "text", "text": "Therefore "},
                {"id": "m6-block-0002", "type": "math", "latex": "x=-2"},
            ],
            "warnings": [],
        }
    )

    first = canonical_transcript_hash(transcript)
    reordered = transcript.model_copy(update={"blocks": list(reversed(transcript.blocks))})

    assert len(first) == 64
    assert first != canonical_transcript_hash(reordered)
    assert transcript.blocks[1].latex == "x=-2"


def test_transcript_rejects_duplicate_ids_unsupported_variants_and_unknown_fields() -> None:
    base = {
        "schemaVersion": "3.0.0",
        "attemptId": str(ATTEMPT_ID),
        "warnings": [],
    }
    with pytest.raises(ValidationError, match="unique"):
        TranscriptDocument.model_validate(
            {
                **base,
                "blocks": [
                    {"id": "same", "type": "text", "text": "A"},
                    {"id": "same", "type": "math", "latex": "x"},
                ],
            }
        )
    with pytest.raises(ValidationError):
        TranscriptDocument.model_validate(
            {**base, "blocks": [{"id": "raw", "type": "markdown", "markdown": "# no"}]}
        )
    with pytest.raises(ValidationError, match="Extra inputs"):
        TranscriptDocument.model_validate(
            {
                **base,
                "blocks": [
                    {
                        "id": "html",
                        "type": "text",
                        "text": "safe",
                        "html": "<script>bad()</script>",
                    }
                ],
            }
        )
