from copy import deepcopy
from pathlib import Path

import pytest
from app.content.loader import canonical_content_hash, load_content_package
from app.content.schemas import ContentPackage, GeometrySceneVersion
from pydantic import ValidationError
from tests.fixtures.geometry import (
    synthetic_geometry_content_package,
    synthetic_geometry_scene_version,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]


def test_all_approved_primitives_and_explicit_interactions_validate() -> None:
    scene = GeometrySceneVersion.model_validate(synthetic_geometry_scene_version())

    objects = {item.id: item for item in scene.objects}
    assert set(item.type for item in scene.objects) == {
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
    }
    assert objects["A"].draggable is True
    assert objects["A"].selectable is True
    assert objects["I"].intersection_index == 0


@pytest.mark.parametrize("field", ["javascript", "script", "expression", "html", "svg", "onClick"])
def test_executable_or_arbitrary_markup_fields_are_rejected(field: str) -> None:
    payload = synthetic_geometry_scene_version()
    payload["objects"][0][field] = "alert('unsafe')"

    with pytest.raises(ValidationError, match=field):
        GeometrySceneVersion.model_validate(payload)


def _object(payload: dict, object_id: str) -> dict:
    return next(item for item in payload["objects"] if item["id"] == object_id)


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda payload: payload["initialVisibleObjectIds"].append("A"),
            "initially visible geometry object IDs must be unique",
        ),
        (
            lambda payload: payload["initialVisibleObjectIds"].append("UNKNOWN"),
            "unknown initially visible geometry objects",
        ),
        (
            lambda payload: payload["objects"].append(deepcopy(payload["objects"][0])),
            "geometry object IDs must be unique",
        ),
        (
            lambda payload: _object(payload, "segmentAB").update({"parents": ["A", "UNKNOWN"]}),
            "unknown parents",
        ),
        (
            lambda payload: _object(payload, "base").update({"parents": ["parallelC", "B"]}),
            "construction graph contains a cycle",
        ),
        (
            lambda payload: _object(payload, "base").update({"parents": ["base", "B"]}),
            "construction graph contains a cycle",
        ),
        (
            lambda payload: _object(payload, "segmentAB").update({"parents": ["base", "B"]}),
            "segment parents must be point objects",
        ),
        (
            lambda payload: _object(payload, "I").update({"parents": ["A", "circleA"]}),
            "intersection parents must be curves",
        ),
        (
            lambda payload: _object(payload, "perpendicularC").update({"parents": ["A", "C"]}),
            "perpendicular requires a line parent followed by a point parent",
        ),
        (
            lambda payload: _object(payload, "labelM").update({"parents": ["base"]}),
            "label parents must be point objects",
        ),
        (
            lambda payload: _object(payload, "M").update({"draggable": True}),
            "only free points may be draggable",
        ),
        (
            lambda payload: _object(payload, "labelM").update({"selectable": True}),
            "labels may not be selectable",
        ),
        (
            lambda payload: _object(payload, "I").pop("intersectionIndex"),
            "intersection requires intersectionIndex",
        ),
        (
            lambda payload: _object(payload, "A").update({"intersectionIndex": 0}),
            "only intersections may contain intersectionIndex",
        ),
        (
            lambda payload: payload.update({"accessibilityDescription": "   "}),
            "accessibilityDescription must not be blank",
        ),
    ],
)
def test_malformed_scene_graphs_are_rejected(mutate, message: str) -> None:
    payload = synthetic_geometry_scene_version()
    mutate(payload)

    with pytest.raises(ValidationError, match=message):
        GeometrySceneVersion.model_validate(payload)


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda payload: payload["viewport"].update({"xMin": float("nan")}), "finite number"),
        (lambda payload: payload["viewport"].update({"xMax": float("inf")}), "finite number"),
        (lambda payload: payload["viewport"].update({"xMin": "-5"}), "valid number"),
        (lambda payload: payload["viewport"].update({"xMin": True}), "valid number"),
        (lambda payload: _object(payload, "A").update({"x": float("nan")}), "finite number"),
        (lambda payload: _object(payload, "A").update({"y": float("inf")}), "finite number"),
        (lambda payload: _object(payload, "A").pop("x"), "free points require x and y"),
        (
            lambda payload: payload["viewport"].update({"xMin": 8}),
            "viewport bounds must be ordered",
        ),
        (lambda payload: _object(payload, "base").update({"x": 1}), "only free points"),
        (
            lambda payload: _object(payload, "triangle").update({"parents": ["A", "B"]}),
            "polygon requires",
        ),
        (lambda payload: _object(payload, "A").update({"type": "bezier"}), "type"),
    ],
)
def test_malformed_geometry_properties_are_rejected(mutate, message: str) -> None:
    payload = synthetic_geometry_scene_version()
    mutate(payload)

    with pytest.raises(ValidationError, match=message):
        GeometrySceneVersion.model_validate(payload)


@pytest.mark.parametrize(
    ("action", "message"),
    [
        ({"type": "show", "objectIds": ["A", "A"]}, "objectIds must be unique"),
        ({"type": "hide", "objectIds": ["UNKNOWN"]}, "unknown geometry objects"),
        (
            {"type": "animate", "objectId": "base", "animationId": "pulse-A"},
            "animate target must be a point object",
        ),
        (
            {"type": "animate", "objectId": "A", "animationId": "unknown-animation"},
            "unknown animation",
        ),
        (
            {
                "type": "ask_select",
                "prompt": [{"id": "select-prompt", "type": "text", "text": "Select A."}],
                "allowedObjectIds": ["A", "A"],
                "correctObjectIds": ["A"],
            },
            "allowedObjectIds must be unique",
        ),
        (
            {
                "type": "ask_select",
                "prompt": [{"id": "select-prompt", "type": "text", "text": "Select M."}],
                "allowedObjectIds": ["M"],
                "correctObjectIds": ["M"],
            },
            "ask_select allowed objects must be selectable",
        ),
        (
            {
                "type": "ask_select",
                "prompt": [{"id": "select-prompt", "type": "text", "text": "Select A."}],
                "allowedObjectIds": ["A"],
                "correctObjectIds": ["B"],
            },
            "correct objects must be allowed objects",
        ),
    ],
)
def test_geometry_actions_are_strict_and_capability_checked(action: dict, message: str) -> None:
    package = synthetic_geometry_content_package()
    package["problems"][0]["versions"][0]["hints"][0]["geometryActions"] = [action]

    with pytest.raises(ValidationError, match=message):
        ContentPackage.model_validate(package)


def test_valid_typed_actions_reference_only_curated_capabilities() -> None:
    package = synthetic_geometry_content_package()
    package["problems"][0]["versions"][0]["hints"][0]["geometryActions"] = [
        {"type": "show", "objectIds": ["segmentAB"]},
        {"type": "hide", "objectIds": ["labelM"]},
        {"type": "highlight", "objectIds": ["A", "B"]},
        {"type": "clear_highlight", "objectIds": ["A"]},
        {"type": "focus", "objectIds": ["triangle"]},
        {"type": "animate", "objectId": "A", "animationId": "pulse-A"},
        {
            "type": "ask_select",
            "prompt": [{"id": "select-prompt", "type": "text", "text": "Select A."}],
            "allowedObjectIds": ["A", "B"],
            "correctObjectIds": ["A"],
        },
    ]

    loaded = ContentPackage.model_validate(package)

    assert len(loaded.problems[0].versions[0].hints[0].geometry_actions) == 7


def test_inactive_interaction_defaults_preserve_the_released_m2_hash() -> None:
    package = load_content_package(
        REPOSITORY_ROOT / "content/packages/synthetic-m2-foundations-v1/package.yaml"
    )

    assert canonical_content_hash(package) == (
        "59f9572fb526842cbdddf438db2468c8d578a637fe814102f5bfbb95118ce7db"
    )
    assert package.geometry_scenes[0].versions[0].objects[0].model_dump(
        by_alias=True,
        mode="json",
    ) == {
        "id": "A",
        "type": "point",
        "parents": [],
        "x": 0.0,
        "y": 0.0,
        "label": "A",
    }
