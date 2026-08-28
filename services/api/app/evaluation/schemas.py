import re
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic.alias_generators import to_camel

from app.content.schemas import ContentBlock, GeometryAction


class EvaluationModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        extra="forbid",
        populate_by_name=True,
    )


PlainText = Annotated[str, Field(min_length=1, max_length=2_000)]
StepJudgment = Literal["correct", "incorrect", "uncertain", "not_assessable"]
ErrorKind = Literal["none", "root", "dependent"]


class ProviderReasoningStep(EvaluationModel):
    step_key: Annotated[str, Field(pattern=r"^step-[1-9][0-9]{0,2}$")]
    transcript_block_ids: Annotated[list[str], Field(min_length=1, max_length=500)]
    summary: PlainText
    judgment: StepJudgment
    error_kind: ErrorKind
    depends_on_step_keys: Annotated[list[str], Field(max_length=100)] = []
    feedback: PlainText

    @field_validator("summary", "feedback")
    @classmethod
    def visible_plain_text_only(cls, value: str) -> str:
        lowered = value.lower()
        if (
            any(
                token in lowered
                for token in (
                    "`",
                    "**",
                    "__",
                    "~~",
                    "http://",
                    "https://",
                    "www.",
                    "mailto:",
                    "javascript:",
                    "![",
                )
            )
            or re.search(r"<\s*/?\s*[a-z][^>]*>", value, re.IGNORECASE)
            or re.search(r"^\s{0,3}#{1,6}\s", value, re.MULTILINE)
            or re.search(r"^\s{0,3}(?:>|[-+*]|\d+[.)])\s", value, re.MULTILINE)
            or re.search(r"\[[^\]]+\]\([^)]*\)", value)
            or re.search(r"(?<!\w)[*_][^\n*_]+[*_](?!\w)", value)
        ):
            raise ValueError("Evaluation text must be concise plain visible content")
        return value

    @model_validator(mode="after")
    def judgment_matches_error_kind(self) -> Self:
        if self.judgment == "incorrect" and self.error_kind == "none":
            raise ValueError("Incorrect steps must identify a root or dependent error")
        if self.judgment != "incorrect" and self.error_kind != "none":
            raise ValueError("Only incorrect steps may identify an error relationship")
        if self.error_kind == "root" and self.depends_on_step_keys:
            raise ValueError("A root error cannot depend on another step")
        if self.error_kind != "dependent" and self.depends_on_step_keys:
            raise ValueError("Only dependent errors may reference dependency steps")
        if self.error_kind == "dependent" and not self.depends_on_step_keys:
            raise ValueError("A dependent error must reference an earlier step")
        if len(self.transcript_block_ids) != len(set(self.transcript_block_ids)):
            raise ValueError("Transcript block references must be unique")
        if len(self.depends_on_step_keys) != len(set(self.depends_on_step_keys)):
            raise ValueError("Step dependencies must be unique")
        return self


class ProviderRubricAward(EvaluationModel):
    rubric_code: Annotated[str, Field(min_length=1, max_length=100)]
    awarded_score: Annotated[Decimal, Field(ge=0, max_digits=8, decimal_places=2)]
    explanation: PlainText

    @field_validator("explanation")
    @classmethod
    def visible_plain_text_only(cls, value: str) -> str:
        return ProviderReasoningStep.visible_plain_text_only(value)


class ProviderReadyEvaluation(EvaluationModel):
    outcome: Literal["ready"]
    reasoning_steps: Annotated[list[ProviderReasoningStep], Field(min_length=1, max_length=100)]
    rubric_awards: Annotated[list[ProviderRubricAward], Field(min_length=1, max_length=100)]
    overall_feedback: PlainText
    next_action: PlainText

    @field_validator("overall_feedback", "next_action")
    @classmethod
    def visible_plain_text_only(cls, value: str) -> str:
        return ProviderReasoningStep.visible_plain_text_only(value)

    @model_validator(mode="after")
    def relationships_are_ordered_and_rooted(self) -> Self:
        keys = [step.step_key for step in self.reasoning_steps]
        if len(keys) != len(set(keys)):
            raise ValueError("Reasoning step keys must be unique")
        positions = {key: index for index, key in enumerate(keys)}
        roots = {step.step_key for step in self.reasoning_steps if step.error_kind == "root"}
        for index, step in enumerate(self.reasoning_steps):
            if any(dependency not in positions for dependency in step.depends_on_step_keys):
                raise ValueError("A reasoning step references an unknown dependency")
            if any(positions[dependency] >= index for dependency in step.depends_on_step_keys):
                raise ValueError("Reasoning step dependencies must point to earlier steps")
            if step.error_kind == "dependent":
                pending = list(step.depends_on_step_keys)
                visited: set[str] = set()
                reaches_root = False
                while pending:
                    key = pending.pop()
                    if key in visited:
                        continue
                    visited.add(key)
                    if key in roots:
                        reaches_root = True
                        break
                    pending.extend(self.reasoning_steps[positions[key]].depends_on_step_keys)
                if not reaches_root:
                    raise ValueError("Every dependent error must trace to a root error")
        rubric_codes = [award.rubric_code for award in self.rubric_awards]
        if len(rubric_codes) != len(set(rubric_codes)):
            raise ValueError("Rubric award codes must be unique")
        return self


class ProviderUncertainEvaluation(EvaluationModel):
    outcome: Literal["uncertain"]
    reason: PlainText
    recommended_action: Literal["manual_review"]

    @field_validator("reason")
    @classmethod
    def visible_plain_text_only(cls, value: str) -> str:
        return ProviderReasoningStep.visible_plain_text_only(value)


ProviderEvaluationPayload = Annotated[
    ProviderReadyEvaluation | ProviderUncertainEvaluation,
    Field(discriminator="outcome"),
]


class EvaluationRequest(EvaluationModel):
    confirmed_transcript_version_id: uuid.UUID
    idempotency_key: uuid.UUID


class EvaluationRunResponse(EvaluationModel):
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
    retry_count: Annotated[int, Field(ge=0, le=1)]
    latency_ms: Annotated[int, Field(ge=0)] | None
    input_tokens: Annotated[int, Field(ge=0)] | None
    output_tokens: Annotated[int, Field(ge=0)] | None
    cost_usd: Annotated[Decimal, Field(ge=0)] | None
    error_code: Annotated[str, Field(min_length=1, max_length=80)] | None
    started_at: datetime
    completed_at: datetime | None


class ReasoningStepResponse(EvaluationModel):
    id: uuid.UUID
    position: Annotated[int, Field(ge=1)]
    transcript_block_ids: Annotated[list[str], Field(min_length=1)]
    summary: Annotated[list[ContentBlock], Field(min_length=1)]
    judgment: StepJudgment
    error_kind: ErrorKind
    depends_on_step_ids: list[uuid.UUID]
    feedback: Annotated[list[ContentBlock], Field(min_length=1)]


class RubricScoreResponse(EvaluationModel):
    rubric_item_id: uuid.UUID
    rubric_code: Annotated[str, Field(min_length=1, max_length=100)]
    awarded_score: Annotated[Decimal, Field(ge=0, max_digits=8, decimal_places=2)]
    maximum_score: Annotated[Decimal, Field(gt=0, max_digits=8, decimal_places=2)]
    explanation: Annotated[list[ContentBlock], Field(min_length=1)]


class ReadyEvaluationResponse(EvaluationModel):
    outcome: Literal["ready"]
    evaluation_id: uuid.UUID
    confirmed_transcript_version_id: uuid.UUID
    score: Annotated[Decimal, Field(ge=0, max_digits=8, decimal_places=2)]
    maximum_score: Annotated[Decimal, Field(gt=0, max_digits=8, decimal_places=2)]
    reasoning_steps: Annotated[list[ReasoningStepResponse], Field(min_length=1)]
    rubric_breakdown: Annotated[list[RubricScoreResponse], Field(min_length=1)]
    feedback: Annotated[list[ContentBlock], Field(min_length=1)]
    next_steps: Annotated[list[ContentBlock], Field(min_length=1)]
    reference_solutions_non_exhaustive: Literal[True]
    run: EvaluationRunResponse


class UncertainEvaluationResponse(EvaluationModel):
    outcome: Literal["uncertain"]
    evaluation_id: uuid.UUID
    confirmed_transcript_version_id: uuid.UUID
    reason: Annotated[list[ContentBlock], Field(min_length=1)]
    recommended_action: Literal["manual_review"]
    run: EvaluationRunResponse


EvaluationResponse = Annotated[
    ReadyEvaluationResponse | UncertainEvaluationResponse,
    Field(discriminator="outcome"),
]


class EvaluationNotStartedState(EvaluationModel):
    state: Literal["not_started"]


class EvaluationProcessingState(EvaluationModel):
    state: Literal["processing"]
    run: EvaluationRunResponse


class EvaluationReadyState(EvaluationModel):
    state: Literal["ready"]
    result: ReadyEvaluationResponse


class EvaluationUncertainState(EvaluationModel):
    state: Literal["uncertain"]
    result: UncertainEvaluationResponse


class EvaluationFailureState(EvaluationModel):
    state: Literal["retryable_failure", "permanent_failure", "invalid_schema"]
    run: EvaluationRunResponse


EvaluationStateResponse = Annotated[
    EvaluationNotStartedState
    | EvaluationProcessingState
    | EvaluationReadyState
    | EvaluationUncertainState
    | EvaluationFailureState,
    Field(discriminator="state"),
]


class NextHintRequest(EvaluationModel):
    idempotency_key: uuid.UUID


class NextHintResponse(EvaluationModel):
    hint_event_id: uuid.UUID
    evaluation_id: uuid.UUID
    hint_id: uuid.UUID
    hint_level: Annotated[int, Field(ge=1, le=5)]
    content: Annotated[list[ContentBlock], Field(min_length=1)]
    geometry_actions: list[GeometryAction]
    reveals_complete_solution: bool
    concept_version_id: uuid.UUID | None
    released_at: datetime
