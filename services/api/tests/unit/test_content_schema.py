import json
from copy import deepcopy
from pathlib import Path
from uuid import uuid4

import pytest
from app.content.loader import ContentValidationError, canonical_content_hash, load_content_package
from tests.fixtures.content import synthetic_content_package

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]


def test_yaml_and_json_packages_share_one_strict_versioned_contract(tmp_path) -> None:
    package = synthetic_content_package()
    json_path = tmp_path / "package.json"
    json_path.write_text(json.dumps(package), encoding="utf-8")

    loaded = load_content_package(json_path)

    assert loaded.schema_version == "1.0.0"
    assert loaded.package_version == 1
    assert len(loaded.exams) == 2
    assert len(loaded.problems[0].versions[0].exam_relevance) == 2
    assert canonical_content_hash(loaded) == canonical_content_hash(loaded)


def test_unknown_content_fields_are_rejected_before_import(tmp_path) -> None:
    package = synthetic_content_package()
    package["arbitraryHtml"] = "<script>unsafe()</script>"
    path = tmp_path / "package.json"
    path.write_text(json.dumps(package), encoding="utf-8")

    with pytest.raises(ContentValidationError, match="arbitraryHtml"):
        load_content_package(path)


def test_committed_yaml_matches_the_json_contract_and_rejects_duplicate_keys(tmp_path) -> None:
    yaml_package = load_content_package(
        REPOSITORY_ROOT / "content/packages/synthetic-m2-foundations-v1/package.yaml"
    )
    json_path = tmp_path / "package.json"
    json_path.write_text(json.dumps(synthetic_content_package()), encoding="utf-8")

    assert canonical_content_hash(yaml_package) == canonical_content_hash(
        load_content_package(json_path)
    )

    duplicate_path = tmp_path / "duplicate.yaml"
    duplicate_path.write_text(
        "schemaVersion: 1.0.0\nschemaVersion: 1.0.0\n",
        encoding="utf-8",
    )
    with pytest.raises(ContentValidationError, match="duplicate key 'schemaVersion'"):
        load_content_package(duplicate_path)

    duplicate_json_path = tmp_path / "duplicate.json"
    duplicate_json_path.write_text(
        '{"schemaVersion":"1.0.0","schemaVersion":"1.0.0"}',
        encoding="utf-8",
    )
    with pytest.raises(ContentValidationError, match="duplicate key 'schemaVersion'"):
        load_content_package(duplicate_json_path)


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda package: package["geometryScenes"][0]["versions"][0]["objects"][0].update(
                {"javascript": "alert('unsafe')"}
            ),
            "javascript",
        ),
        (
            lambda package: package["problems"][0]["versions"][0]["hints"][1]["geometryActions"][
                0
            ].update({"objectIds": ["UNKNOWN"]}),
            "unknown geometry objects",
        ),
        (
            lambda package: package["problems"][0]["versions"][0]["referenceSolutions"][0].update(
                {"nonExhaustive": False}
            ),
            "nonExhaustive",
        ),
        (
            lambda package: package["provenance"].update({"sourceKind": "third_party"}),
            "sourceKind",
        ),
    ],
)
def test_unsafe_or_unapproved_content_is_rejected(
    tmp_path,
    mutate,
    message: str,
) -> None:
    package = synthetic_content_package()
    mutate(package)
    path = tmp_path / "package.json"
    path.write_text(json.dumps(package), encoding="utf-8")

    with pytest.raises(ContentValidationError, match=message):
        load_content_package(path)


def test_skill_prerequisite_cycles_are_rejected(tmp_path) -> None:
    package = synthetic_content_package()
    first_skill = package["skills"][0]["id"]
    second_skill = package["skills"][1]["id"]
    provenance = package["provenance"]
    package["skillRelationships"] = [
        {
            "id": str(uuid4()),
            "parentSkillId": first_skill,
            "childSkillId": second_skill,
            "relationType": "prerequisite",
            "provenance": provenance,
        },
        {
            "id": str(uuid4()),
            "parentSkillId": second_skill,
            "childSkillId": first_skill,
            "relationType": "prerequisite",
            "provenance": provenance,
        },
    ]
    path = tmp_path / "package.json"
    path.write_text(json.dumps(package), encoding="utf-8")

    with pytest.raises(ContentValidationError, match="skill prerequisite graph contains a cycle"):
        load_content_package(path)


def test_each_exam_skill_weight_version_is_a_complete_configuration(tmp_path) -> None:
    package = synthetic_content_package()
    second_version = deepcopy(package["examSkillWeights"])
    for weight in second_version:
        weight["id"] = str(uuid4())
        weight["version"] = 2
    package["examSkillWeights"].extend(second_version)
    path = tmp_path / "package.json"
    path.write_text(json.dumps(package), encoding="utf-8")

    loaded = load_content_package(path)

    assert {weight.version for weight in loaded.exam_skill_weights} == {1, 2}


def test_duplicate_geometry_scene_version_numbers_are_rejected_before_import(tmp_path) -> None:
    package = synthetic_content_package()
    duplicate = deepcopy(package["geometryScenes"][0]["versions"][0])
    duplicate["id"] = str(uuid4())
    package["geometryScenes"][0]["versions"].append(duplicate)
    path = tmp_path / "package.json"
    path.write_text(json.dumps(package), encoding="utf-8")

    with pytest.raises(ContentValidationError, match="geometry scene version numbers"):
        load_content_package(path)


def test_duplicate_skill_relationship_keys_are_rejected_before_import(tmp_path) -> None:
    package = synthetic_content_package()
    duplicate = deepcopy(package["skillRelationships"][0])
    duplicate["id"] = str(uuid4())
    package["skillRelationships"].append(duplicate)
    path = tmp_path / "package.json"
    path.write_text(json.dumps(package), encoding="utf-8")

    with pytest.raises(ContentValidationError, match="skill relationship keys"):
        load_content_package(path)
