import hashlib
import json
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal, Protocol, cast

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.content.loader import canonical_content_hash
from app.content.models import (
    Concept,
    ConceptVersion,
    ContentImport,
    Exam,
    ExamCycle,
    ExamSkillWeight,
    GeometryScene,
    GeometrySceneVersion,
    Problem,
    ProblemExamRelevance,
    ProblemHint,
    ProblemSkillLink,
    ProblemVersion,
    ReferenceSolution,
    RubricItem,
    Skill,
    SkillEdge,
)
from app.content.schemas import ContentPackage, Provenance


class ContentImportError(RuntimeError):
    pass


@dataclass(frozen=True)
class ImportResult:
    package_id: uuid.UUID
    package_version: int
    content_hash: str
    status: Literal["imported", "already_imported"]


class HasContentHash(Protocol):
    content_hash: str


def _json_object(value: BaseModel) -> dict[str, object]:
    return cast(dict[str, object], value.model_dump(mode="json", by_alias=True))


def _json_array(values: Sequence[BaseModel]) -> list[object]:
    return cast(
        list[object],
        [value.model_dump(mode="json", by_alias=True) for value in values],
    )


def _provenance(value: Provenance) -> dict[str, object]:
    return _json_object(value)


def _item_hash(value: BaseModel) -> str:
    payload = json.dumps(
        value.model_dump(mode="json", by_alias=True),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


async def _add_immutable[Row: HasContentHash](
    database: AsyncSession,
    model: type[Row],
    identity: object | tuple[object, ...],
    candidate: Row,
    label: str,
) -> None:
    existing = await database.get(model, identity)
    if existing is None:
        database.add(candidate)
    elif existing.content_hash != candidate.content_hash:
        raise ContentImportError(f"{label} conflicts with an existing immutable row")


async def _import_exams(package: ContentPackage, database: AsyncSession) -> None:
    for exam in package.exams:
        provenance_json = _provenance(exam.provenance)
        stored = await database.get(Exam, exam.id)
        if stored is None:
            database.add(
                Exam(
                    id=exam.id,
                    code=exam.code,
                    name=exam.name,
                    region=exam.region,
                    status=exam.status,
                    provenance_json=provenance_json,
                )
            )
        elif (
            stored.code,
            stored.name,
            stored.region,
            stored.status,
            stored.provenance_json,
        ) != (exam.code, exam.name, exam.region, exam.status, provenance_json):
            raise ContentImportError("exam conflicts with an existing stable record")
    await database.flush()
    for cycle in package.exam_cycles:
        await _add_immutable(
            database,
            ExamCycle,
            cycle.id,
            ExamCycle(
                id=cycle.id,
                exam_id=cycle.exam_id,
                cycle_code=cycle.cycle_code,
                year=cycle.year,
                exam_date=cycle.exam_date,
                maximum_score=cycle.maximum_score,
                content_version=cycle.content_version,
                status=cycle.status,
                content_hash=_item_hash(cycle),
                provenance_json=_provenance(cycle.provenance),
            ),
            "exam cycle",
        )
    await database.flush()


async def _import_skills(package: ContentPackage, database: AsyncSession) -> None:
    for skill in package.skills:
        await _add_immutable(
            database,
            Skill,
            skill.id,
            Skill(
                id=skill.id,
                code=skill.code,
                name=skill.name,
                description_json=_json_array(skill.description),
                domain=skill.domain,
                status=skill.status,
                content_hash=_item_hash(skill),
                provenance_json=_provenance(skill.provenance),
            ),
            "skill",
        )
    await database.flush()
    for relationship in package.skill_relationships:
        await _add_immutable(
            database,
            SkillEdge,
            relationship.id,
            SkillEdge(
                id=relationship.id,
                parent_skill_id=relationship.parent_skill_id,
                child_skill_id=relationship.child_skill_id,
                relation_type=relationship.relation_type,
                content_hash=_item_hash(relationship),
                provenance_json=_provenance(relationship.provenance),
            ),
            "skill relationship",
        )
    for weight in package.exam_skill_weights:
        await _add_immutable(
            database,
            ExamSkillWeight,
            weight.id,
            ExamSkillWeight(
                id=weight.id,
                exam_cycle_id=weight.exam_cycle_id,
                skill_id=weight.skill_id,
                weight=weight.weight,
                source_note=weight.source_note,
                version=weight.version,
                content_hash=_item_hash(weight),
                provenance_json=_provenance(weight.provenance),
            ),
            "exam skill weight",
        )
    await database.flush()


async def _import_scenes(package: ContentPackage, database: AsyncSession) -> None:
    for scene in package.geometry_scenes:
        stored = await database.get(GeometryScene, scene.id)
        if stored is None:
            database.add(
                GeometryScene(
                    id=scene.id,
                    code=scene.code,
                    name=scene.name,
                    current_version_id=scene.current_version_id,
                    status=scene.status,
                )
            )
        elif (stored.code, stored.name, stored.status) != (
            scene.code,
            scene.name,
            scene.status,
        ):
            raise ContentImportError("geometry scene conflicts with an existing stable record")
        else:
            stored.current_version_id = scene.current_version_id
        for version in scene.versions:
            await _add_immutable(
                database,
                GeometrySceneVersion,
                version.id,
                GeometrySceneVersion(
                    id=version.id,
                    geometry_scene_id=scene.id,
                    version=version.version,
                    scene_json=_json_object(version),
                    content_hash=_item_hash(version),
                    provenance_json=_provenance(version.provenance),
                ),
                "geometry scene version",
            )
    await database.flush()


async def _import_concepts(package: ContentPackage, database: AsyncSession) -> None:
    for concept in package.concepts:
        stored = await database.get(Concept, concept.id)
        if stored is None:
            database.add(
                Concept(
                    id=concept.id,
                    code=concept.code,
                    name=concept.name,
                    current_version_id=concept.current_version_id,
                    status=concept.status,
                )
            )
        elif (stored.code, stored.name, stored.status) != (
            concept.code,
            concept.name,
            concept.status,
        ):
            raise ContentImportError("concept conflicts with an existing stable record")
        else:
            stored.current_version_id = concept.current_version_id
        for version in concept.versions:
            await _add_immutable(
                database,
                ConceptVersion,
                version.id,
                ConceptVersion(
                    id=version.id,
                    concept_id=concept.id,
                    version=version.version,
                    content_json=_json_array(version.content),
                    geometry_scene_version_id=version.geometry_scene_version_id,
                    content_hash=_item_hash(version),
                    provenance_json=_provenance(version.provenance),
                ),
                "concept version",
            )
    await database.flush()


async def _import_problem_children(package: ContentPackage, database: AsyncSession) -> None:
    for problem in package.problems:
        for version in problem.versions:
            for relevance in version.exam_relevance:
                await _add_immutable(
                    database,
                    ProblemExamRelevance,
                    (version.id, relevance.exam_cycle_id),
                    ProblemExamRelevance(
                        problem_version_id=version.id,
                        exam_cycle_id=relevance.exam_cycle_id,
                        relevance_level=relevance.relevance_level,
                        relevance_note=relevance.relevance_note,
                        content_hash=_item_hash(relevance),
                        provenance_json=_provenance(relevance.provenance),
                    ),
                    "problem exam relevance",
                )
            for link in version.skill_links:
                await _add_immutable(
                    database,
                    ProblemSkillLink,
                    (version.id, link.skill_id),
                    ProblemSkillLink(
                        problem_version_id=version.id,
                        skill_id=link.skill_id,
                        role=link.role,
                        importance=link.importance,
                        content_hash=_item_hash(link),
                        provenance_json=_provenance(link.provenance),
                    ),
                    "problem skill link",
                )
            for solution in version.reference_solutions:
                await _add_immutable(
                    database,
                    ReferenceSolution,
                    solution.id,
                    ReferenceSolution(
                        id=solution.id,
                        problem_version_id=version.id,
                        solution_code=solution.solution_code,
                        content_json=_json_array(solution.content),
                        method_label=solution.method_label,
                        expert_verified=solution.expert_verified,
                        non_exhaustive=solution.non_exhaustive,
                        content_hash=_item_hash(solution),
                        provenance_json=_provenance(solution.provenance),
                    ),
                    "reference solution",
                )
            for rubric in version.rubric:
                await _add_immutable(
                    database,
                    RubricItem,
                    rubric.id,
                    RubricItem(
                        id=rubric.id,
                        problem_version_id=version.id,
                        rubric_code=rubric.rubric_code,
                        description_json=_json_array(rubric.description),
                        maximum_score=rubric.maximum_score,
                        skill_id=rubric.skill_id,
                        order_index=rubric.order_index,
                        content_hash=_item_hash(rubric),
                        provenance_json=_provenance(rubric.provenance),
                    ),
                    "rubric item",
                )
            for hint in version.hints:
                await _add_immutable(
                    database,
                    ProblemHint,
                    hint.id,
                    ProblemHint(
                        id=hint.id,
                        problem_version_id=version.id,
                        hint_level=hint.hint_level,
                        content_json=_json_array(hint.content),
                        geometry_actions_json=_json_array(hint.geometry_actions),
                        reveals_complete_solution=hint.reveals_complete_solution,
                        concept_id=hint.concept_id,
                        content_hash=_item_hash(hint),
                        provenance_json=_provenance(hint.provenance),
                    ),
                    "problem hint",
                )
    await database.flush()


async def _import_problems(package: ContentPackage, database: AsyncSession) -> None:
    for problem in package.problems:
        stored = await database.get(Problem, problem.id)
        if stored is None:
            database.add(
                Problem(
                    id=problem.id,
                    external_code=problem.external_code,
                    origin_exam_cycle_id=problem.origin_exam_cycle_id,
                    year=problem.year,
                    problem_number=problem.problem_number,
                    current_version_id=problem.current_version_id,
                    status=problem.status,
                )
            )
        elif (
            stored.external_code,
            stored.origin_exam_cycle_id,
            stored.year,
            stored.problem_number,
            stored.status,
        ) != (
            problem.external_code,
            problem.origin_exam_cycle_id,
            problem.year,
            problem.problem_number,
            problem.status,
        ):
            raise ContentImportError("problem conflicts with an existing stable record")
        else:
            stored.current_version_id = problem.current_version_id
        for version in problem.versions:
            await _add_immutable(
                database,
                ProblemVersion,
                version.id,
                ProblemVersion(
                    id=version.id,
                    problem_id=problem.id,
                    version=version.version,
                    statement_json=_json_array(version.statement),
                    maximum_score=version.maximum_score,
                    difficulty_band=version.difficulty_band,
                    estimated_minutes=version.estimated_minutes,
                    geometry_scene_version_id=version.geometry_scene_version_id,
                    content_hash=_item_hash(version),
                    provenance_json=_provenance(version.provenance),
                ),
                "problem version",
            )
    await database.flush()
    await _import_problem_children(package, database)


async def import_content_package(
    package: ContentPackage,
    database: AsyncSession,
    *,
    source_path: str = "<validated-memory-package>",
) -> ImportResult:
    package_hash = canonical_content_hash(package)
    try:
        async with database.begin():
            receipt = await database.scalar(
                select(ContentImport).where(
                    ContentImport.package_id == package.package_id,
                    ContentImport.package_version == package.package_version,
                )
            )
            if receipt is not None:
                if receipt.content_hash != package_hash:
                    raise ContentImportError(
                        "package ID and version already exist with different validated content"
                    )
                return ImportResult(
                    package_id=package.package_id,
                    package_version=package.package_version,
                    content_hash=package_hash,
                    status="already_imported",
                )

            await _import_exams(package, database)
            await _import_skills(package, database)
            await _import_scenes(package, database)
            await _import_concepts(package, database)
            await _import_problems(package, database)
            database.add(
                ContentImport(
                    package_id=package.package_id,
                    package_version=package.package_version,
                    schema_version=package.schema_version,
                    content_hash=package_hash,
                    source_path=source_path,
                )
            )
    except IntegrityError as error:
        raise ContentImportError("content package conflicts with existing database rows") from error

    return ImportResult(
        package_id=package.package_id,
        package_version=package.package_version,
        content_hash=package_hash,
        status="imported",
    )
