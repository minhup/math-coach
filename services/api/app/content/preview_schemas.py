import uuid
from datetime import date
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import Field

from app.content.schemas import ContentBlock, GeometryAction, GeometrySceneVersion, Provenance
from app.schemas import ApiModel


class ContentPreviewSummary(ApiModel):
    problem_id: uuid.UUID
    problem_version_id: uuid.UUID
    external_code: str
    version: int
    supported_exam_count: int


class ContentPreviewListResponse(ApiModel):
    items: list[ContentPreviewSummary]


class PreviewExamRelevance(ApiModel):
    exam_cycle_id: uuid.UUID
    exam_id: uuid.UUID
    exam_code: str
    exam_name: str
    cycle_code: str
    exam_date: date
    relevance_level: Literal["low", "medium", "high"]
    relevance_note: str


class PreviewSkillLink(ApiModel):
    skill_id: uuid.UUID
    skill_code: str
    skill_name: str
    role: Literal["primary", "secondary", "prerequisite", "diagnostic"]
    importance: Decimal


class PreviewReferenceSolution(ApiModel):
    id: uuid.UUID
    solution_code: str
    method_label: str
    content: list[ContentBlock]
    expert_verified: Literal[True]
    non_exhaustive: Literal[True]


class PreviewRubricItem(ApiModel):
    id: uuid.UUID
    rubric_code: str
    description: list[ContentBlock]
    maximum_score: Decimal
    skill_id: uuid.UUID
    order_index: int


class PreviewHint(ApiModel):
    id: uuid.UUID
    hint_level: Annotated[int, Field(ge=1, le=5)]
    content: list[ContentBlock]
    geometry_actions: list[GeometryAction]
    reveals_complete_solution: bool
    concept_id: uuid.UUID | None


class ContentPreviewResponse(ApiModel):
    problem_id: uuid.UUID
    problem_version_id: uuid.UUID
    external_code: str
    version: int
    statement: list[ContentBlock]
    maximum_score: Decimal
    difficulty_band: Literal["introductory", "core", "advanced", "challenge"]
    estimated_minutes: Annotated[int, Field(ge=1, le=180)]
    supported_exams: list[PreviewExamRelevance]
    skills: list[PreviewSkillLink]
    reference_solutions: list[PreviewReferenceSolution]
    rubric: list[PreviewRubricItem]
    hints: list[PreviewHint]
    geometry_scene: GeometrySceneVersion | None
    provenance: Provenance
