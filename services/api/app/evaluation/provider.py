from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal

from pydantic import TypeAdapter, ValidationError

from app.evaluation.schemas import (
    ProviderEvaluationPayload,
    ProviderReadyEvaluation,
    ProviderUncertainEvaluation,
)

provider_payload_adapter: TypeAdapter[ProviderEvaluationPayload] = TypeAdapter(
    ProviderEvaluationPayload
)


@dataclass(frozen=True)
class EvaluationProviderIdentity:
    provider: str
    model_snapshot: str
    prompt_version: str
    prompt_hash: str
    schema_version: str
    pricing_version: str
    input_usd_per_million: Decimal
    output_usd_per_million: Decimal


@dataclass(frozen=True)
class EvaluationProviderRequest:
    attempt_id: uuid.UUID
    transcript_block_ids: tuple[str, ...]
    rubric_limits: tuple[tuple[str, Decimal], ...]
    context_json: str


@dataclass(frozen=True)
class EvaluationProviderCall:
    payload: object
    latency_ms: int
    input_tokens: int
    output_tokens: int


@dataclass(frozen=True)
class EvaluationProviderResult:
    outcome: Literal["ready", "uncertain"]
    identity: EvaluationProviderIdentity
    payload: ProviderReadyEvaluation | ProviderUncertainEvaluation
    schema_attempts: int
    latency_ms: int
    input_tokens: int
    output_tokens: int
    cost_usd: Decimal


class EvaluationProviderSchemaError(Exception):
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
        super().__init__("Evaluation payload remained invalid after one schema repair")


class EvaluationProviderTransportError(Exception):
    def __init__(self, code: Literal["timeout", "rate_limited", "transport_failed"]) -> None:
        self.code = code
        super().__init__(code)


class EvaluationProviderPermanentError(Exception):
    def __init__(self, code: Literal["provider_rejected"]) -> None:
        self.code = code
        super().__init__(code)


class StrictEvaluationProvider(ABC):
    def __init__(self, identity: EvaluationProviderIdentity) -> None:
        self._identity = identity

    @property
    def identity(self) -> EvaluationProviderIdentity:
        return self._identity

    def cost(self, *, input_tokens: int, output_tokens: int) -> Decimal:
        raw = (
            Decimal(input_tokens) * self.identity.input_usd_per_million
            + Decimal(output_tokens) * self.identity.output_usd_per_million
        ) / Decimal(1_000_000)
        return raw.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)

    @abstractmethod
    async def _invoke(
        self, request: EvaluationProviderRequest, *, repair_schema: bool
    ) -> EvaluationProviderCall: ...

    @staticmethod
    def _validate_against_request(
        payload: ProviderReadyEvaluation | ProviderUncertainEvaluation,
        request: EvaluationProviderRequest,
    ) -> None:
        if isinstance(payload, ProviderUncertainEvaluation):
            return
        actual_blocks = [
            block_id for step in payload.reasoning_steps for block_id in step.transcript_block_ids
        ]
        if len(actual_blocks) != len(set(actual_blocks)):
            raise ValueError("Each transcript block must belong to exactly one reasoning step")
        if set(actual_blocks) != set(request.transcript_block_ids):
            raise ValueError("Reasoning steps must cover exactly the confirmed transcript blocks")
        limits = dict(request.rubric_limits)
        if {award.rubric_code for award in payload.rubric_awards} != set(limits):
            raise ValueError("Rubric awards must cover the immutable rubric exactly")
        if any(award.awarded_score > limits[award.rubric_code] for award in payload.rubric_awards):
            raise ValueError("A rubric award cannot exceed its immutable maximum")

    async def evaluate(self, request: EvaluationProviderRequest) -> EvaluationProviderResult:
        latency_ms = 0
        input_tokens = 0
        output_tokens = 0
        last_error: Exception | None = None
        for index in range(2):
            call = await self._invoke(request, repair_schema=index == 1)
            latency_ms += call.latency_ms
            input_tokens += call.input_tokens
            output_tokens += call.output_tokens
            try:
                payload = provider_payload_adapter.validate_python(call.payload)
                self._validate_against_request(payload, request)
            except (ValidationError, ValueError) as error:
                last_error = error
                continue
            return EvaluationProviderResult(
                outcome=payload.outcome,
                identity=self.identity,
                payload=payload,
                schema_attempts=index + 1,
                latency_ms=latency_ms,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=self.cost(input_tokens=input_tokens, output_tokens=output_tokens),
            )
        raise EvaluationProviderSchemaError(
            schema_attempts=2,
            latency_ms=latency_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        ) from last_error
