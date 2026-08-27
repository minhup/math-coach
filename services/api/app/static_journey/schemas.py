import uuid
from datetime import date
from decimal import Decimal
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel

from app.content.schemas import ContentBlock, GeometryAction, GeometrySceneVersion


class StaticJourneyModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        extra="forbid",
        populate_by_name=True,
    )


class TranscriptTextBlock(StaticJourneyModel):
    id: Annotated[str, Field(min_length=1, max_length=120)]
    type: Literal["text"]
    text: Annotated[str, Field(max_length=20_000)]


class TranscriptMathBlock(StaticJourneyModel):
    id: Annotated[str, Field(min_length=1, max_length=120)]
    type: Literal["math"]
    latex: Annotated[str, Field(max_length=2_000)]


TranscriptBlock = Annotated[
    TranscriptTextBlock | TranscriptMathBlock,
    Field(discriminator="type"),
]


class TranscriptDocument(StaticJourneyModel):
    schema_version: Literal["2.0.0"]
    attempt_id: uuid.UUID
    blocks: Annotated[list[TranscriptBlock], Field(min_length=1, max_length=500)]

    @model_validator(mode="after")
    def unique_block_ids(self) -> Self:
        ids = [block.id for block in self.blocks]
        if len(ids) != len(set(ids)):
            raise ValueError("Transcript block IDs must be unique")
        return self


class ConfirmedTranscript(StaticJourneyModel):
    confirmation_status: Literal["confirmed"]
    transcript: TranscriptDocument


class MockRunMetadata(StaticJourneyModel):
    provider: Literal["application-owned-synthetic-mock"]
    model_snapshot: Literal["m5-static-fixture-v1"]
    prompt_version: Literal["m5-no-provider-prompt-v1"]
    schema_version: Literal["1.0.0"]
    latency_ms: Annotated[int, Field(ge=0)]
    input_tokens: Literal[0]
    output_tokens: Literal[0]
    cost_usd: Annotated[Decimal, Field(ge=0)]


class MockTranscriptionRequest(StaticJourneyModel):
    upload_id: uuid.UUID


class MockTranscriptionResponse(StaticJourneyModel):
    transcript: TranscriptDocument
    metadata: MockRunMetadata


class MockEvaluationRequest(StaticJourneyModel):
    confirmed_transcript: ConfirmedTranscript


class MockEvaluationResponse(StaticJourneyModel):
    outcome: Literal["ready", "uncertain"]
    feedback: Annotated[list[ContentBlock], Field(min_length=1)]
    next_steps: Annotated[list[ContentBlock], Field(min_length=1)]
    reference_solutions_non_exhaustive: Literal[True]
    transcript_fingerprint: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    metadata: MockRunMetadata


class StaticPlanTarget(StaticJourneyModel):
    target_id: uuid.UUID
    exam_cycle_id: uuid.UUID
    exam_name: Annotated[str, Field(min_length=1, max_length=200)]
    cycle_code: Annotated[str, Field(min_length=1, max_length=100)]
    priority_rank: Annotated[int, Field(ge=1)]


class AvailableExamCycleResponse(StaticJourneyModel):
    id: uuid.UUID
    exam_id: uuid.UUID
    exam_code: Annotated[str, Field(min_length=1, max_length=80)]
    exam_name: Annotated[str, Field(min_length=1, max_length=200)]
    cycle_code: Annotated[str, Field(min_length=1, max_length=100)]
    year: Annotated[int, Field(ge=2000, le=2200)]
    exam_date: date


class AvailableExamCycleListResponse(StaticJourneyModel):
    items: list[AvailableExamCycleResponse]


class StudentProblemContent(StaticJourneyModel):
    problem_id: uuid.UUID
    problem_version_id: uuid.UUID
    external_code: Annotated[str, Field(min_length=1, max_length=120)]
    version: Annotated[int, Field(ge=1)]
    estimated_minutes: Annotated[int, Field(ge=1, le=180)]
    statement: Annotated[list[ContentBlock], Field(min_length=1)]
    geometry_scene: GeometrySceneVersion | None


class StaticPlanItem(StaticJourneyModel):
    position: Annotated[int, Field(ge=1)]
    problem: StudentProblemContent
    supported_target_ids: Annotated[list[uuid.UUID], Field(min_length=1)]
    selection_reason: Literal["shared_target_foundation", "priority_target_follow_up"]
    concept_version_id: uuid.UUID | None


class StaticDailyPlanResponse(StaticJourneyModel):
    schema_version: Literal["1.0.0"]
    plan_id: uuid.UUID
    plan_date: date
    profile_id: uuid.UUID
    targets: list[StaticPlanTarget]
    items: list[StaticPlanItem]

    @model_validator(mode="after")
    def validate_plan_relationships(self) -> Self:
        target_ids = [target.target_id for target in self.targets]
        if len(target_ids) != len(set(target_ids)):
            raise ValueError("Plan target IDs must be unique")
        if [item.position for item in self.items] != list(range(1, len(self.items) + 1)):
            raise ValueError("Plan item positions must be contiguous")
        problem_versions = [item.problem.problem_version_id for item in self.items]
        if len(problem_versions) != len(set(problem_versions)):
            raise ValueError("Plan problem versions must be unique")
        known_targets = set(target_ids)
        for item in self.items:
            if len(item.supported_target_ids) != len(set(item.supported_target_ids)):
                raise ValueError("Plan item target support must be unique")
            if not set(item.supported_target_ids) <= known_targets:
                raise ValueError("Plan item support must reference plan target records")
        return self


class NextHintRequest(StaticJourneyModel):
    previous_hint_level: Annotated[int, Field(ge=0, le=5)]


class NextHintResponse(StaticJourneyModel):
    hint_id: uuid.UUID
    hint_level: Annotated[int, Field(ge=1, le=5)]
    content: Annotated[list[ContentBlock], Field(min_length=1)]
    geometry_actions: list[GeometryAction]
    reveals_complete_solution: bool
    concept_version_id: uuid.UUID | None


class ConceptVersionResponse(StaticJourneyModel):
    concept_id: uuid.UUID
    concept_version_id: uuid.UUID
    code: Annotated[str, Field(min_length=1, max_length=100)]
    name: Annotated[str, Field(min_length=1, max_length=200)]
    version: Annotated[int, Field(ge=1)]
    content: Annotated[list[ContentBlock], Field(min_length=1)]
    geometry_scene: GeometrySceneVersion | None
