import uuid
from datetime import date
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel

from app.content.schemas import ContentBlock, GeometrySceneVersion


class StaticJourneyModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        extra="forbid",
        populate_by_name=True,
    )


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


class ConceptVersionResponse(StaticJourneyModel):
    concept_id: uuid.UUID
    concept_version_id: uuid.UUID
    code: Annotated[str, Field(min_length=1, max_length=100)]
    name: Annotated[str, Field(min_length=1, max_length=200)]
    version: Annotated[int, Field(ge=1)]
    content: Annotated[list[ContentBlock], Field(min_length=1)]
    geometry_scene: GeometrySceneVersion | None
