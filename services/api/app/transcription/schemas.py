import hashlib
import json
import re
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic.alias_generators import to_camel


class TranscriptionModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        extra="forbid",
        populate_by_name=True,
    )


WarningCode = Literal[
    "low_confidence_text",
    "low_confidence_math",
    "ambiguous_cross_out",
    "ambiguous_insertion",
    "ordering_uncertain",
    "source_region_unavailable",
]

WARNING_MESSAGES: dict[WarningCode, str] = {
    "low_confidence_text": "Some text may need review.",
    "low_confidence_math": "A formula may need review.",
    "ambiguous_cross_out": "A crossed-out part may need review.",
    "ambiguous_insertion": "An inserted part may need review.",
    "ordering_uncertain": "The reading order may need review.",
    "source_region_unavailable": "A source location is unavailable.",
}

NormalizedCoordinate = Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)]
PositiveNormalizedSize = Annotated[float, Field(gt=0, le=1, allow_inf_nan=False)]


class ProviderSourceRegion(TranscriptionModel):
    x: NormalizedCoordinate
    y: NormalizedCoordinate
    width: PositiveNormalizedSize
    height: PositiveNormalizedSize

    @model_validator(mode="after")
    def inside_image(self) -> Self:
        if self.x + self.width > 1 or self.y + self.height > 1:
            raise ValueError("Source region must stay inside the normalized image")
        return self


class SourceRegion(ProviderSourceRegion):
    attempt_asset_id: uuid.UUID
    units: Literal["normalized"] = "normalized"


class ProviderTextBlock(TranscriptionModel):
    type: Literal["text"]
    text: Annotated[str, Field(min_length=1, max_length=20_000)]
    source_region: ProviderSourceRegion | None = None

    @field_validator("text")
    @classmethod
    def plain_text_only(cls, value: str) -> str:
        lowered = value.lower()
        if (
            any(token in lowered for token in ("```", "**", "http://", "https://", "!["))
            or re.search(r"<\s*/?\s*[a-z][^>]*>", value, re.IGNORECASE)
            or re.search(r"^\s{0,3}#{1,6}\s", value, re.MULTILINE)
            or re.search(r"\[[^\]]+\]\([^)]*\)", value)
        ):
            raise ValueError("Provider text must be plain visible content")
        return value


class ProviderMathBlock(TranscriptionModel):
    type: Literal["math"]
    latex: Annotated[str, Field(min_length=1, max_length=2_000)]
    source_region: ProviderSourceRegion | None = None

    @field_validator("latex")
    @classmethod
    def safe_math_source_only(cls, value: str) -> str:
        lowered = value.lower()
        if any(
            token in lowered
            for token in ("http://", "https://", "javascript:", r"\href", r"\url", r"\html")
        ):
            raise ValueError("Provider mathematics must be plain visible content")
        return value


ProviderBlock = Annotated[
    ProviderTextBlock | ProviderMathBlock,
    Field(discriminator="type"),
]


class ProviderWarning(TranscriptionModel):
    code: WarningCode
    block_index: Annotated[int, Field(ge=0, le=499)] | None = None


class ProviderReadyPayload(TranscriptionModel):
    outcome: Literal["ready"]
    blocks: Annotated[list[ProviderBlock], Field(min_length=1, max_length=500)]
    warnings: Annotated[list[ProviderWarning], Field(max_length=100)] = []

    @model_validator(mode="after")
    def warning_references_exist(self) -> Self:
        if any(
            warning.block_index is not None and warning.block_index >= len(self.blocks)
            for warning in self.warnings
        ):
            raise ValueError("Provider warning references an unknown block")
        return self


class ProviderUncertainPayload(TranscriptionModel):
    outcome: Literal["uncertain"]
    warnings: Annotated[list[ProviderWarning], Field(min_length=1, max_length=100)]

    @model_validator(mode="after")
    def no_block_references_without_blocks(self) -> Self:
        if any(warning.block_index is not None for warning in self.warnings):
            raise ValueError("An uncertain payload cannot reference a block")
        return self


ProviderPayload = Annotated[
    ProviderReadyPayload | ProviderUncertainPayload,
    Field(discriminator="outcome"),
]


class TranscriptWarning(TranscriptionModel):
    code: WarningCode
    message: Annotated[str, Field(min_length=1, max_length=120)]
    block_id: Annotated[str, Field(min_length=1, max_length=120)] | None = None

    @classmethod
    def from_provider_code(cls, *, code: WarningCode, block_id: str | None) -> "TranscriptWarning":
        return cls(code=code, message=WARNING_MESSAGES[code], block_id=block_id)

    @model_validator(mode="after")
    def fixed_message(self) -> Self:
        if self.message != WARNING_MESSAGES[self.code]:
            raise ValueError("Warning message does not match its application-owned code")
        return self


class TranscriptTextBlock(TranscriptionModel):
    id: Annotated[str, Field(min_length=1, max_length=120)]
    type: Literal["text"]
    text: Annotated[str, Field(max_length=20_000)]
    source_region: SourceRegion | None = None


class TranscriptMathBlock(TranscriptionModel):
    id: Annotated[str, Field(min_length=1, max_length=120)]
    type: Literal["math"]
    latex: Annotated[str, Field(max_length=2_000)]
    source_region: SourceRegion | None = None


TranscriptBlock = Annotated[
    TranscriptTextBlock | TranscriptMathBlock,
    Field(discriminator="type"),
]


class TranscriptDocument(TranscriptionModel):
    schema_version: Literal["3.0.0"]
    attempt_id: uuid.UUID
    blocks: Annotated[list[TranscriptBlock], Field(min_length=1, max_length=500)]
    warnings: Annotated[list[TranscriptWarning], Field(max_length=100)] = []

    @model_validator(mode="after")
    def valid_relationships(self) -> Self:
        ids = [block.id for block in self.blocks]
        if len(ids) != len(set(ids)):
            raise ValueError("Transcript block IDs must be unique")
        known_ids = set(ids)
        if any(
            warning.block_id is not None and warning.block_id not in known_ids
            for warning in self.warnings
        ):
            raise ValueError("Transcript warning references an unknown block")
        return self


def canonical_transcript_hash(transcript: TranscriptDocument) -> str:
    canonical = json.dumps(
        transcript.model_dump(by_alias=True, exclude_none=True, mode="json"),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    return hashlib.sha256(canonical).hexdigest()


class TranscribeRequest(TranscriptionModel):
    upload_id: uuid.UUID
    idempotency_key: uuid.UUID


class TranscriptionRunResponse(TranscriptionModel):
    id: uuid.UUID
    status: Literal[
        "processing",
        "succeeded",
        "uncertain",
        "retryable_failure",
        "permanent_failure",
        "invalid_schema",
    ]
    provider: Annotated[str, Field(min_length=1, max_length=80)]
    model_snapshot: Annotated[str, Field(min_length=1, max_length=120)]
    prompt_version: Annotated[str, Field(min_length=1, max_length=80)]
    prompt_hash: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    schema_version: Annotated[str, Field(min_length=1, max_length=80)]
    pricing_version: Annotated[str, Field(min_length=1, max_length=80)]
    schema_attempts: Annotated[int, Field(ge=0, le=2)]
    latency_ms: Annotated[int, Field(ge=0)] | None
    input_tokens: Annotated[int, Field(ge=0)] | None
    output_tokens: Annotated[int, Field(ge=0)] | None
    cost_usd: Annotated[Decimal, Field(ge=0)] | None
    error_code: Annotated[str, Field(min_length=1, max_length=80)] | None
    started_at: datetime
    completed_at: datetime | None


class TranscriptVersionResponse(TranscriptionModel):
    id: uuid.UUID
    attempt_id: uuid.UUID
    source_run_id: uuid.UUID
    parent_transcript_version_id: uuid.UUID | None
    version: Annotated[int, Field(ge=1)]
    transcript_hash: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    origin: Literal["provider", "learner"]
    document: TranscriptDocument
    created_at: datetime


class TranscriptVersionCreateRequest(TranscriptionModel):
    base_transcript_version_id: uuid.UUID
    document: TranscriptDocument


class TranscriptConfirmRequest(TranscriptionModel):
    transcript_version_id: uuid.UUID
    transcript_hash: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]


class TranscriptConfirmationResponse(TranscriptionModel):
    id: uuid.UUID
    attempt_id: uuid.UUID
    transcript_version_id: uuid.UUID
    transcript_hash: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    confirmed_at: datetime


class ReadyTranscriptionResponse(TranscriptionModel):
    outcome: Literal["ready"]
    run: TranscriptionRunResponse
    transcript_version: TranscriptVersionResponse


class UncertainTranscriptionResponse(TranscriptionModel):
    outcome: Literal["uncertain"]
    run: TranscriptionRunResponse
    warnings: list[TranscriptWarning]


TranscriptionResponse = Annotated[
    ReadyTranscriptionResponse | UncertainTranscriptionResponse,
    Field(discriminator="outcome"),
]


class TranscriptionNotStartedState(TranscriptionModel):
    status: Literal["not_started"]


class TranscriptionProcessingState(TranscriptionModel):
    status: Literal["processing"]
    run: TranscriptionRunResponse


class TranscriptionReadyState(TranscriptionModel):
    status: Literal["ready"]
    run: TranscriptionRunResponse
    transcript_version: TranscriptVersionResponse
    confirmation: TranscriptConfirmationResponse | None


class TranscriptionUncertainState(TranscriptionModel):
    status: Literal["uncertain"]
    run: TranscriptionRunResponse
    warnings: list[TranscriptWarning]


class TranscriptionFailureState(TranscriptionModel):
    status: Literal["retryable_failure", "permanent_failure", "invalid_schema"]
    run: TranscriptionRunResponse


TranscriptionStateResponse = Annotated[
    TranscriptionNotStartedState
    | TranscriptionProcessingState
    | TranscriptionReadyState
    | TranscriptionUncertainState
    | TranscriptionFailureState,
    Field(discriminator="status"),
]


class UploadDownloadResponse(TranscriptionModel):
    upload_id: uuid.UUID
    download_url: Annotated[str, Field(min_length=1)]
    expires_at: datetime
