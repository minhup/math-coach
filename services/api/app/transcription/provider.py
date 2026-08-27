import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal

from pydantic import TypeAdapter, ValidationError

from app.transcription.schemas import (
    ProviderPayload,
    ProviderReadyPayload,
    ProviderUncertainPayload,
    SourceRegion,
    TranscriptDocument,
    TranscriptMathBlock,
    TranscriptTextBlock,
    TranscriptWarning,
)

provider_payload_adapter: TypeAdapter[ProviderPayload] = TypeAdapter(ProviderPayload)


@dataclass(frozen=True)
class ConfiguredProviderIdentity:
    provider: str
    model_snapshot: str
    prompt_version: str
    prompt_hash: str
    schema_version: str
    pricing_version: str
    input_usd_per_million: Decimal
    output_usd_per_million: Decimal


@dataclass(frozen=True)
class ProviderRequest:
    attempt_id: uuid.UUID
    attempt_asset_id: uuid.UUID
    content_type: Literal["image/jpeg", "image/png", "image/webp"]
    image_bytes: bytes
    problem_context: str


@dataclass(frozen=True)
class ProviderCall:
    payload: object
    latency_ms: int
    input_tokens: int
    output_tokens: int


@dataclass(frozen=True)
class ProviderResult:
    outcome: Literal["ready", "uncertain"]
    identity: ConfiguredProviderIdentity
    transcript: TranscriptDocument | None
    warnings: tuple[TranscriptWarning, ...]
    schema_attempts: int
    latency_ms: int
    input_tokens: int
    output_tokens: int
    cost_usd: Decimal


class ProviderSchemaError(Exception):
    def __init__(
        self,
        *,
        schema_attempts: int,
        latency_ms: int,
        input_tokens: int,
        output_tokens: int,
    ) -> None:
        self.schema_attempts = schema_attempts
        self.latency_ms = latency_ms
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        super().__init__("Provider payload remained invalid after one schema repair")


class ProviderTransportError(Exception):
    def __init__(self, code: Literal["timeout", "rate_limited", "transport_failed"]) -> None:
        self.code = code
        super().__init__(code)


class ProviderPermanentError(Exception):
    def __init__(self, code: Literal["invalid_media", "provider_rejected"]) -> None:
        self.code = code
        super().__init__(code)


def _cost(
    identity: ConfiguredProviderIdentity,
    *,
    input_tokens: int,
    output_tokens: int,
) -> Decimal:
    raw = (
        Decimal(input_tokens) * identity.input_usd_per_million
        + Decimal(output_tokens) * identity.output_usd_per_million
    ) / Decimal(1_000_000)
    return raw.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)


def _block_id(asset_id: uuid.UUID, index: int) -> str:
    return f"m6-{asset_id.hex[:12]}-{index + 1:04d}"


def _warnings(
    payload: ProviderReadyPayload | ProviderUncertainPayload,
    block_ids: list[str],
) -> tuple[TranscriptWarning, ...]:
    return tuple(
        TranscriptWarning.from_provider_code(
            code=warning.code,
            block_id=None if warning.block_index is None else block_ids[warning.block_index],
        )
        for warning in payload.warnings
    )


def _document(payload: ProviderReadyPayload, request: ProviderRequest) -> TranscriptDocument:
    block_ids = [_block_id(request.attempt_asset_id, index) for index in range(len(payload.blocks))]
    blocks: list[TranscriptTextBlock | TranscriptMathBlock] = []
    for index, source in enumerate(payload.blocks):
        region = (
            None
            if source.source_region is None
            else SourceRegion(
                attempt_asset_id=request.attempt_asset_id,
                x=source.source_region.x,
                y=source.source_region.y,
                width=source.source_region.width,
                height=source.source_region.height,
            )
        )
        if source.type == "text":
            blocks.append(
                TranscriptTextBlock(
                    id=block_ids[index],
                    type="text",
                    text=source.text,
                    source_region=region,
                )
            )
        else:
            blocks.append(
                TranscriptMathBlock(
                    id=block_ids[index],
                    type="math",
                    latex=source.latex,
                    source_region=region,
                )
            )
    return TranscriptDocument(
        schema_version="3.0.0",
        attempt_id=request.attempt_id,
        blocks=blocks,
        warnings=list(_warnings(payload, block_ids)),
    )


class StrictTranscriptionProvider(ABC):
    def __init__(self, identity: ConfiguredProviderIdentity) -> None:
        self._identity = identity

    @property
    def identity(self) -> ConfiguredProviderIdentity:
        return self._identity

    def cost(self, *, input_tokens: int, output_tokens: int) -> Decimal:
        return _cost(
            self.identity,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

    @abstractmethod
    async def _invoke(self, request: ProviderRequest, *, repair_schema: bool) -> ProviderCall: ...

    async def transcribe(self, request: ProviderRequest) -> ProviderResult:
        latency_ms = 0
        input_tokens = 0
        output_tokens = 0
        last_error: ValidationError | None = None
        for index in range(2):
            call = await self._invoke(request, repair_schema=index == 1)
            latency_ms += call.latency_ms
            input_tokens += call.input_tokens
            output_tokens += call.output_tokens
            try:
                payload = provider_payload_adapter.validate_python(call.payload)
            except ValidationError as error:
                last_error = error
                continue

            if isinstance(payload, ProviderReadyPayload):
                transcript = _document(payload, request)
                warnings = tuple(transcript.warnings)
                outcome: Literal["ready", "uncertain"] = "ready"
            else:
                transcript = None
                warnings = _warnings(payload, [])
                outcome = "uncertain"
            return ProviderResult(
                outcome=outcome,
                identity=self.identity,
                transcript=transcript,
                warnings=warnings,
                schema_attempts=index + 1,
                latency_ms=latency_ms,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=self.cost(input_tokens=input_tokens, output_tokens=output_tokens),
            )

        raise ProviderSchemaError(
            schema_attempts=2,
            latency_ms=latency_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        ) from last_error
