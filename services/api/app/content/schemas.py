from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from datetime import date
from decimal import Decimal
from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel

NonEmptyText = Annotated[str, Field(min_length=1)]
Identifier = Annotated[str, Field(min_length=1, pattern=r"^[A-Za-z][A-Za-z0-9_-]*$")]
PositiveVersion = Annotated[int, Field(strict=True, ge=1)]
PositiveMinutes = Annotated[int, Field(strict=True, ge=1, le=180)]
Score = Annotated[Decimal, Field(ge=Decimal("0"), max_digits=8, decimal_places=2)]
PositiveScore = Annotated[Decimal, Field(gt=Decimal("0"), max_digits=8, decimal_places=2)]
Weight = Annotated[
    Decimal,
    Field(gt=Decimal("0"), le=Decimal("1"), max_digits=6, decimal_places=5),
]


class ContentModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        extra="forbid",
        populate_by_name=True,
    )


class Provenance(ContentModel):
    source_kind: Literal["original_synthetic"]
    title: NonEmptyText
    creator: NonEmptyText
    source_reference: NonEmptyText
    acquisition_date: date
    acquired_by: NonEmptyText
    rights_basis: Literal["original_fixture"]
    rights_evidence: NonEmptyText
    permitted_uses: Annotated[list[NonEmptyText], Field(min_length=1)]
    restrictions: list[NonEmptyText]
    attribution_text: NonEmptyText
    adaptation_description: NonEmptyText | None
    translation_description: NonEmptyText | None
    derivative_of: list[UUID]
    mathematics_reviewer: NonEmptyText
    mathematics_reviewed_at: date
    rights_reviewer: NonEmptyText
    rights_reviewed_at: date
    publication_status: Literal["synthetic_only"]
    publication_date: date


class TextSpan(ContentModel):
    type: Literal["text"]
    text: NonEmptyText


class MathSpan(ContentModel):
    type: Literal["math"]
    latex: NonEmptyText


RichSpan = Annotated[TextSpan | MathSpan, Field(discriminator="type")]


class TextBlock(ContentModel):
    id: Identifier
    type: Literal["text"]
    text: NonEmptyText


class InlineMathBlock(ContentModel):
    id: Identifier
    type: Literal["inline_math"]
    latex: NonEmptyText


class DisplayMathBlock(ContentModel):
    id: Identifier
    type: Literal["display_math"]
    latex: NonEmptyText


class RichLineBlock(ContentModel):
    id: Identifier
    type: Literal["rich_line"]
    spans: Annotated[list[RichSpan], Field(min_length=1)]


class GeometryBlock(ContentModel):
    id: Identifier
    type: Literal["geometry"]
    scene_version_id: UUID


class ImageBlock(ContentModel):
    id: Identifier
    type: Literal["image"]
    asset_id: Identifier
    alt: NonEmptyText


class CalloutBlock(ContentModel):
    id: Identifier
    type: Literal["callout"]
    kind: Literal["note", "warning", "hint", "success"]
    content: Annotated[list[ContentBlock], Field(min_length=1)]


ContentBlock = Annotated[
    TextBlock
    | InlineMathBlock
    | DisplayMathBlock
    | RichLineBlock
    | GeometryBlock
    | ImageBlock
    | CalloutBlock,
    Field(discriminator="type"),
]


class Viewport(ContentModel):
    x_min: float
    x_max: float
    y_min: float
    y_max: float

    @model_validator(mode="after")
    def bounds_are_ordered(self) -> Self:
        if self.x_min >= self.x_max or self.y_min >= self.y_max:
            raise ValueError("geometry viewport bounds must be ordered")
        return self


GeometryObjectType = Literal[
    "point",
    "segment",
    "line",
    "ray",
    "circle",
    "arc",
    "polygon",
    "angle",
    "midpoint",
    "intersection",
    "perpendicular",
    "parallel",
    "circumcircle",
    "label",
]

PARENT_COUNTS: dict[str, tuple[int, int]] = {
    "point": (0, 0),
    "segment": (2, 2),
    "line": (2, 2),
    "ray": (2, 2),
    "circle": (2, 2),
    "arc": (3, 3),
    "polygon": (3, 32),
    "angle": (3, 3),
    "midpoint": (2, 2),
    "intersection": (2, 2),
    "perpendicular": (2, 2),
    "parallel": (2, 2),
    "circumcircle": (3, 3),
    "label": (1, 1),
}


class GeometryObject(ContentModel):
    id: Identifier
    type: GeometryObjectType
    parents: list[Identifier] = Field(default_factory=list)
    x: float | None = None
    y: float | None = None
    label: NonEmptyText | None = None

    @model_validator(mode="after")
    def fields_match_object_type(self) -> Self:
        minimum, maximum = PARENT_COUNTS[self.type]
        if not minimum <= len(self.parents) <= maximum:
            raise ValueError(f"{self.type} requires between {minimum} and {maximum} parents")
        if self.type == "point":
            if self.x is None or self.y is None:
                raise ValueError("free points require x and y coordinates")
        elif self.x is not None or self.y is not None:
            raise ValueError("only free points may contain x or y coordinates")
        if len(self.parents) != len(set(self.parents)):
            raise ValueError("geometry object parents must be unique")
        return self


class ShowAction(ContentModel):
    type: Literal["show"]
    object_ids: Annotated[list[Identifier], Field(min_length=1)]


class HideAction(ContentModel):
    type: Literal["hide"]
    object_ids: Annotated[list[Identifier], Field(min_length=1)]


class HighlightAction(ContentModel):
    type: Literal["highlight"]
    object_ids: Annotated[list[Identifier], Field(min_length=1)]


class ClearHighlightAction(ContentModel):
    type: Literal["clear_highlight"]
    object_ids: list[Identifier] | None = None


class FocusAction(ContentModel):
    type: Literal["focus"]
    object_ids: Annotated[list[Identifier], Field(min_length=1)]


class AnimateAction(ContentModel):
    type: Literal["animate"]
    object_id: Identifier
    animation_id: Identifier


class AskSelectAction(ContentModel):
    type: Literal["ask_select"]
    prompt: Annotated[list[ContentBlock], Field(min_length=1)]
    allowed_object_ids: Annotated[list[Identifier], Field(min_length=1)]
    correct_object_ids: list[Identifier] | None = None


GeometryAction = Annotated[
    ShowAction
    | HideAction
    | HighlightAction
    | ClearHighlightAction
    | FocusAction
    | AnimateAction
    | AskSelectAction,
    Field(discriminator="type"),
]


class GeometrySceneVersion(ContentModel):
    id: UUID
    version: PositiveVersion
    viewport: Viewport
    objects: Annotated[list[GeometryObject], Field(min_length=1)]
    initial_visible_object_ids: Annotated[list[Identifier], Field(min_length=1)]
    animation_ids: list[Identifier]
    fallback_image_asset_id: Identifier
    accessibility_description: NonEmptyText
    provenance: Provenance

    @model_validator(mode="after")
    def object_graph_is_valid(self) -> Self:
        object_ids = [item.id for item in self.objects]
        if len(object_ids) != len(set(object_ids)):
            raise ValueError("geometry object IDs must be unique within a scene")
        known = set(object_ids)
        unknown_visible = set(self.initial_visible_object_ids) - known
        if unknown_visible:
            raise ValueError(
                f"unknown initially visible geometry objects: {sorted(unknown_visible)}"
            )
        if len(self.animation_ids) != len(set(self.animation_ids)):
            raise ValueError("geometry animation IDs must be unique")
        parents_by_id = {item.id: item.parents for item in self.objects}
        for item in self.objects:
            unknown_parents = set(item.parents) - known
            if unknown_parents:
                raise ValueError(
                    f"geometry object {item.id} has unknown parents: {sorted(unknown_parents)}"
                )
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(object_id: str) -> None:
            if object_id in visiting:
                raise ValueError("geometry construction graph contains a cycle")
            if object_id in visited:
                return
            visiting.add(object_id)
            for parent_id in parents_by_id[object_id]:
                visit(parent_id)
            visiting.remove(object_id)
            visited.add(object_id)

        for object_id in object_ids:
            visit(object_id)
        return self


class GeometryScene(ContentModel):
    id: UUID
    code: NonEmptyText
    name: NonEmptyText
    current_version_id: UUID
    status: Literal["synthetic"]
    versions: Annotated[list[GeometrySceneVersion], Field(min_length=1)]

    @model_validator(mode="after")
    def current_version_exists(self) -> Self:
        if self.current_version_id not in {version.id for version in self.versions}:
            raise ValueError("geometry scene currentVersionId must identify one of its versions")
        return self


class Exam(ContentModel):
    id: UUID
    code: NonEmptyText
    name: NonEmptyText
    region: NonEmptyText
    status: Literal["synthetic"]
    provenance: Provenance


class ExamCycle(ContentModel):
    id: UUID
    exam_id: UUID
    cycle_code: NonEmptyText
    year: Annotated[int, Field(strict=True, ge=2000, le=2200)]
    exam_date: date
    maximum_score: PositiveScore
    content_version: PositiveVersion
    status: Literal["synthetic"]
    provenance: Provenance


class Skill(ContentModel):
    id: UUID
    code: NonEmptyText
    name: NonEmptyText
    description: Annotated[list[ContentBlock], Field(min_length=1)]
    domain: NonEmptyText
    status: Literal["synthetic"]
    provenance: Provenance


class SkillRelationship(ContentModel):
    id: UUID
    parent_skill_id: UUID
    child_skill_id: UUID
    relation_type: Literal["prerequisite", "related", "subskill"]
    provenance: Provenance

    @model_validator(mode="after")
    def is_not_self_referential(self) -> Self:
        if self.parent_skill_id == self.child_skill_id:
            raise ValueError("a skill relationship cannot reference the same skill twice")
        return self


class ExamSkillWeight(ContentModel):
    id: UUID
    exam_cycle_id: UUID
    skill_id: UUID
    weight: Weight
    source_note: NonEmptyText
    version: PositiveVersion
    provenance: Provenance


class ConceptVersion(ContentModel):
    id: UUID
    version: PositiveVersion
    content: Annotated[list[ContentBlock], Field(min_length=1)]
    geometry_scene_version_id: UUID | None
    provenance: Provenance


class Concept(ContentModel):
    id: UUID
    code: NonEmptyText
    name: NonEmptyText
    current_version_id: UUID
    status: Literal["synthetic"]
    versions: Annotated[list[ConceptVersion], Field(min_length=1)]

    @model_validator(mode="after")
    def current_version_exists(self) -> Self:
        if self.current_version_id not in {version.id for version in self.versions}:
            raise ValueError("concept currentVersionId must identify one of its versions")
        return self


class ProblemExamRelevance(ContentModel):
    exam_cycle_id: UUID
    relevance_level: Literal["low", "medium", "high"]
    relevance_note: NonEmptyText
    provenance: Provenance


class ProblemSkillLink(ContentModel):
    skill_id: UUID
    role: Literal["primary", "secondary", "prerequisite", "diagnostic"]
    importance: Weight
    provenance: Provenance


class ReferenceSolution(ContentModel):
    id: UUID
    solution_code: NonEmptyText
    content: Annotated[list[ContentBlock], Field(min_length=1)]
    method_label: NonEmptyText
    expert_verified: Literal[True]
    non_exhaustive: Literal[True]
    provenance: Provenance


class RubricItem(ContentModel):
    id: UUID
    rubric_code: NonEmptyText
    description: Annotated[list[ContentBlock], Field(min_length=1)]
    maximum_score: PositiveScore
    skill_id: UUID
    order_index: Annotated[int, Field(strict=True, ge=1)]
    provenance: Provenance


class ProblemHint(ContentModel):
    id: UUID
    hint_level: Annotated[int, Field(strict=True, ge=1, le=5)]
    content: Annotated[list[ContentBlock], Field(min_length=1)]
    geometry_actions: list[GeometryAction]
    reveals_complete_solution: bool
    concept_id: UUID | None
    provenance: Provenance


class ProblemVersion(ContentModel):
    id: UUID
    version: PositiveVersion
    statement: Annotated[list[ContentBlock], Field(min_length=1)]
    maximum_score: PositiveScore
    difficulty_band: Literal["introductory", "core", "advanced", "challenge"]
    estimated_minutes: PositiveMinutes
    geometry_scene_version_id: UUID | None
    exam_relevance: Annotated[list[ProblemExamRelevance], Field(min_length=1)]
    skill_links: Annotated[list[ProblemSkillLink], Field(min_length=1)]
    reference_solutions: Annotated[list[ReferenceSolution], Field(min_length=1)]
    rubric: Annotated[list[RubricItem], Field(min_length=1)]
    hints: Annotated[list[ProblemHint], Field(min_length=5, max_length=5)]
    provenance: Provenance

    @model_validator(mode="after")
    def scoring_and_hints_are_consistent(self) -> Self:
        if sum((item.maximum_score for item in self.rubric), Decimal("0")) != self.maximum_score:
            raise ValueError("rubric item scores must total the problem maximumScore")
        rubric_order = [item.order_index for item in self.rubric]
        if rubric_order != list(range(1, len(self.rubric) + 1)):
            raise ValueError("rubric orderIndex values must be consecutive from 1")
        hint_levels = [hint.hint_level for hint in self.hints]
        if hint_levels != [1, 2, 3, 4, 5]:
            raise ValueError("hints must form the ordered progressive ladder 1 through 5")
        if any(hint.reveals_complete_solution for hint in self.hints[:-1]):
            raise ValueError("only the final hint may reveal the complete solution")
        if not self.hints[-1].reveals_complete_solution:
            raise ValueError("the final hint must declare complete-solution disclosure")
        return self


class Problem(ContentModel):
    id: UUID
    external_code: NonEmptyText
    origin_exam_cycle_id: UUID | None
    year: Annotated[int, Field(strict=True, ge=2000, le=2200)] | None
    problem_number: NonEmptyText
    current_version_id: UUID
    status: Literal["synthetic"]
    versions: Annotated[list[ProblemVersion], Field(min_length=1)]

    @model_validator(mode="after")
    def current_version_exists(self) -> Self:
        if self.current_version_id not in {version.id for version in self.versions}:
            raise ValueError("problem currentVersionId must identify one of its versions")
        return self


def _require_unique(values: Sequence[object], description: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{description} must be unique")


def _block_ids(blocks: list[ContentBlock]) -> list[str]:
    result: list[str] = []
    for block in blocks:
        result.append(block.id)
        if isinstance(block, CalloutBlock):
            result.extend(_block_ids(block.content))
    return result


def _geometry_block_scene_ids(blocks: list[ContentBlock]) -> set[UUID]:
    result: set[UUID] = set()
    for block in blocks:
        if isinstance(block, GeometryBlock):
            result.add(block.scene_version_id)
        elif isinstance(block, CalloutBlock):
            result.update(_geometry_block_scene_ids(block.content))
    return result


def _action_object_ids(action: GeometryAction) -> set[str]:
    if isinstance(action, AnimateAction):
        return {action.object_id}
    if isinstance(action, AskSelectAction):
        return set(action.allowed_object_ids) | set(action.correct_object_ids or [])
    return set(action.object_ids or [])


class ContentPackage(ContentModel):
    schema_version: Literal["1.0.0"]
    package_id: UUID
    package_version: PositiveVersion
    title: NonEmptyText
    publication_status: Literal["synthetic_only"]
    provenance: Provenance
    exams: Annotated[list[Exam], Field(min_length=1)]
    exam_cycles: Annotated[list[ExamCycle], Field(min_length=1)]
    skills: Annotated[list[Skill], Field(min_length=1)]
    skill_relationships: list[SkillRelationship]
    exam_skill_weights: Annotated[list[ExamSkillWeight], Field(min_length=1)]
    geometry_scenes: list[GeometryScene]
    concepts: list[Concept]
    problems: Annotated[list[Problem], Field(min_length=1)]

    @model_validator(mode="after")
    def references_and_identifiers_are_valid(self) -> Self:
        exam_ids = {item.id for item in self.exams}
        cycle_ids = {item.id for item in self.exam_cycles}
        skill_ids = {item.id for item in self.skills}
        scene_version_by_id = {
            version.id: version for scene in self.geometry_scenes for version in scene.versions
        }
        scene_version_ids = set(scene_version_by_id)
        concept_ids = {item.id for item in self.concepts}

        all_ids: list[UUID] = [self.package_id]
        all_ids.extend(item.id for item in self.exams)
        all_ids.extend(item.id for item in self.exam_cycles)
        all_ids.extend(item.id for item in self.skills)
        all_ids.extend(item.id for item in self.skill_relationships)
        all_ids.extend(item.id for item in self.exam_skill_weights)
        all_ids.extend(item.id for item in self.geometry_scenes)
        all_ids.extend(scene_version_ids)
        all_ids.extend(item.id for item in self.concepts)
        all_ids.extend(version.id for item in self.concepts for version in item.versions)
        all_ids.extend(item.id for item in self.problems)
        all_ids.extend(version.id for item in self.problems for version in item.versions)
        all_ids.extend(
            solution.id
            for item in self.problems
            for version in item.versions
            for solution in version.reference_solutions
        )
        all_ids.extend(
            rubric.id
            for item in self.problems
            for version in item.versions
            for rubric in version.rubric
        )
        all_ids.extend(
            hint.id for item in self.problems for version in item.versions for hint in version.hints
        )
        _require_unique(all_ids, "content UUIDs")
        _require_unique([item.code for item in self.exams], "exam codes")
        _require_unique([item.cycle_code for item in self.exam_cycles], "exam cycle codes")
        _require_unique([item.code for item in self.skills], "skill codes")
        _require_unique([item.code for item in self.geometry_scenes], "geometry scene codes")
        _require_unique([item.code for item in self.concepts], "concept codes")
        _require_unique([item.external_code for item in self.problems], "problem external codes")

        for cycle in self.exam_cycles:
            if cycle.exam_id not in exam_ids:
                raise ValueError(f"exam cycle {cycle.cycle_code} references an unknown exam")
        for relationship in self.skill_relationships:
            if (
                relationship.parent_skill_id not in skill_ids
                or relationship.child_skill_id not in skill_ids
            ):
                raise ValueError("skill relationships must reference skills in the same package")
        _require_unique(
            [
                (
                    relationship.parent_skill_id,
                    relationship.child_skill_id,
                    relationship.relation_type,
                )
                for relationship in self.skill_relationships
            ],
            "skill relationship keys",
        )
        prerequisite_children: dict[UUID, list[UUID]] = defaultdict(list)
        for relationship in self.skill_relationships:
            if relationship.relation_type == "prerequisite":
                prerequisite_children[relationship.parent_skill_id].append(
                    relationship.child_skill_id
                )
        visiting_skills: set[UUID] = set()
        visited_skills: set[UUID] = set()

        def visit_skill(skill_id: UUID) -> None:
            if skill_id in visiting_skills:
                raise ValueError("skill prerequisite graph contains a cycle")
            if skill_id in visited_skills:
                return
            visiting_skills.add(skill_id)
            for child_skill_id in prerequisite_children[skill_id]:
                visit_skill(child_skill_id)
            visiting_skills.remove(skill_id)
            visited_skills.add(skill_id)

        for skill_id in skill_ids:
            visit_skill(skill_id)

        weights_by_configuration: dict[tuple[UUID, int], Decimal] = defaultdict(
            lambda: Decimal("0")
        )
        weight_keys: list[tuple[UUID, UUID, int]] = []
        for weight in self.exam_skill_weights:
            if weight.exam_cycle_id not in cycle_ids or weight.skill_id not in skill_ids:
                raise ValueError("exam skill weights must reference known cycles and skills")
            weights_by_configuration[(weight.exam_cycle_id, weight.version)] += weight.weight
            weight_keys.append((weight.exam_cycle_id, weight.skill_id, weight.version))
        _require_unique(weight_keys, "exam cycle, skill, and weight version combinations")
        if {cycle_id for cycle_id, _version in weights_by_configuration} != cycle_ids:
            raise ValueError("every exam cycle must have exam skill weights")
        if any(total != Decimal("1") for total in weights_by_configuration.values()):
            raise ValueError("exam skill weights must total 1 for each cycle and version")

        for skill in self.skills:
            self._validate_blocks(skill.description, scene_version_ids, f"skill {skill.code}")
        for scene in self.geometry_scenes:
            _require_unique(
                [scene_version.version for scene_version in scene.versions],
                "geometry scene version numbers",
            )
        for concept in self.concepts:
            _require_unique(
                [concept_version.version for concept_version in concept.versions],
                "concept version numbers",
            )
            for concept_version in concept.versions:
                if (
                    concept_version.geometry_scene_version_id is not None
                    and concept_version.geometry_scene_version_id not in scene_version_ids
                ):
                    raise ValueError(f"concept {concept.code} references an unknown geometry scene")
                self._validate_blocks(
                    concept_version.content,
                    scene_version_ids,
                    f"concept {concept.code} version {concept_version.version}",
                )

        for problem in self.problems:
            if (
                problem.origin_exam_cycle_id is not None
                and problem.origin_exam_cycle_id not in cycle_ids
            ):
                raise ValueError(
                    f"problem {problem.external_code} has an unknown origin exam cycle"
                )
            _require_unique(
                [problem_version.version for problem_version in problem.versions],
                "problem version numbers",
            )
            for problem_version in problem.versions:
                self._validate_problem_version(
                    problem.external_code,
                    problem_version,
                    cycle_ids,
                    skill_ids,
                    concept_ids,
                    scene_version_by_id,
                )
        return self

    @staticmethod
    def _validate_blocks(
        blocks: list[ContentBlock],
        scene_version_ids: set[UUID],
        owner: str,
    ) -> None:
        _require_unique(_block_ids(blocks), f"content block IDs in {owner}")
        unknown_scenes = _geometry_block_scene_ids(blocks) - scene_version_ids
        if unknown_scenes:
            raise ValueError(f"{owner} contains geometry blocks with unknown scene versions")

    @classmethod
    def _validate_problem_version(
        cls,
        problem_code: str,
        version: ProblemVersion,
        cycle_ids: set[UUID],
        skill_ids: set[UUID],
        concept_ids: set[UUID],
        scene_version_by_id: dict[UUID, GeometrySceneVersion],
    ) -> None:
        scene_version_ids = set(scene_version_by_id)
        if (
            version.geometry_scene_version_id is not None
            and version.geometry_scene_version_id not in scene_version_ids
        ):
            raise ValueError(f"problem {problem_code} references an unknown geometry scene")
        cls._validate_blocks(version.statement, scene_version_ids, f"problem {problem_code}")
        statement_scenes = _geometry_block_scene_ids(version.statement)
        expected_scenes = (
            {version.geometry_scene_version_id}
            if version.geometry_scene_version_id is not None
            else set()
        )
        if statement_scenes != expected_scenes:
            raise ValueError(
                f"problem {problem_code} statement geometry must match geometrySceneVersionId"
            )
        relevance_cycles = [item.exam_cycle_id for item in version.exam_relevance]
        _require_unique(relevance_cycles, f"exam relevance cycles for problem {problem_code}")
        if not set(relevance_cycles) <= cycle_ids:
            raise ValueError(f"problem {problem_code} relevance references an unknown exam cycle")
        linked_skills = [item.skill_id for item in version.skill_links]
        _require_unique(linked_skills, f"skill links for problem {problem_code}")
        if not set(linked_skills) <= skill_ids:
            raise ValueError(f"problem {problem_code} links an unknown skill")
        if sum((item.importance for item in version.skill_links), Decimal("0")) != Decimal("1"):
            raise ValueError(f"problem {problem_code} skill-link importance must total 1")
        solution_codes = [item.solution_code for item in version.reference_solutions]
        _require_unique(solution_codes, f"solution codes for problem {problem_code}")
        for solution in version.reference_solutions:
            cls._validate_blocks(
                solution.content,
                scene_version_ids,
                f"reference solution {solution.solution_code}",
            )
        rubric_codes = [item.rubric_code for item in version.rubric]
        _require_unique(rubric_codes, f"rubric codes for problem {problem_code}")
        if not {item.skill_id for item in version.rubric} <= skill_ids:
            raise ValueError(f"problem {problem_code} rubric references an unknown skill")
        for rubric in version.rubric:
            cls._validate_blocks(
                rubric.description,
                scene_version_ids,
                f"rubric {rubric.rubric_code}",
            )
        scene = (
            scene_version_by_id[version.geometry_scene_version_id]
            if version.geometry_scene_version_id is not None
            else None
        )
        known_object_ids = {item.id for item in scene.objects} if scene is not None else set()
        known_animation_ids = set(scene.animation_ids) if scene is not None else set()
        for hint in version.hints:
            if hint.concept_id is not None and hint.concept_id not in concept_ids:
                raise ValueError(f"problem {problem_code} hint references an unknown concept")
            cls._validate_blocks(
                hint.content,
                scene_version_ids,
                f"hint level {hint.hint_level} for problem {problem_code}",
            )
            for action in hint.geometry_actions:
                if scene is None:
                    raise ValueError(f"problem {problem_code} has geometry actions without a scene")
                unknown_objects = _action_object_ids(action) - known_object_ids
                if unknown_objects:
                    raise ValueError(
                        f"problem {problem_code} hint action references unknown geometry objects"
                    )
                if (
                    isinstance(action, AnimateAction)
                    and action.animation_id not in known_animation_ids
                ):
                    raise ValueError(
                        f"problem {problem_code} hint action references an unknown animation"
                    )
                if isinstance(action, AskSelectAction):
                    if action.correct_object_ids is not None and not set(
                        action.correct_object_ids
                    ) <= set(action.allowed_object_ids):
                        raise ValueError("ask_select correct objects must be allowed objects")
                    cls._validate_blocks(
                        action.prompt,
                        scene_version_ids,
                        f"ask_select hint prompt for problem {problem_code}",
                    )


CalloutBlock.model_rebuild()
AskSelectAction.model_rebuild()
