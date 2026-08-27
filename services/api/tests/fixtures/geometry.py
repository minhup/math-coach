from copy import deepcopy
from typing import Any

from tests.fixtures.content import synthetic_content_package, synthetic_provenance


def synthetic_geometry_scene_version() -> dict[str, Any]:
    """Return one deliberately out-of-order scene using every Milestone 4 primitive."""
    return {
        "id": "40000000-0000-4000-8000-000000000501",
        "version": 1,
        "viewport": {"xMin": -5, "xMax": 8, "yMin": -5, "yMax": 7},
        "objects": [
            {"id": "labelM", "type": "label", "parents": ["M"], "label": "Midpoint M"},
            {"id": "circumABC", "type": "circumcircle", "parents": ["A", "B", "C"]},
            {"id": "parallelC", "type": "parallel", "parents": ["base", "C"]},
            {"id": "perpendicularC", "type": "perpendicular", "parents": ["base", "C"]},
            {
                "id": "I",
                "type": "intersection",
                "parents": ["base", "circleA"],
                "intersectionIndex": 0,
                "label": "I",
                "selectable": True,
            },
            {"id": "M", "type": "midpoint", "parents": ["A", "B"], "label": "M"},
            {"id": "angleBAC", "type": "angle", "parents": ["B", "A", "C"]},
            {"id": "triangle", "type": "polygon", "parents": ["A", "B", "C"]},
            {"id": "arcABC", "type": "arc", "parents": ["A", "B", "C"]},
            {"id": "circleA", "type": "circle", "parents": ["A", "C"]},
            {"id": "rayAC", "type": "ray", "parents": ["A", "C"]},
            {"id": "base", "type": "line", "parents": ["A", "B"]},
            {"id": "segmentAB", "type": "segment", "parents": ["A", "B"]},
            {"id": "C", "type": "point", "x": 1, "y": 3, "label": "C", "selectable": True},
            {"id": "B", "type": "point", "x": 4, "y": 0, "label": "B", "selectable": True},
            {
                "id": "A",
                "type": "point",
                "x": 0,
                "y": 0,
                "label": "A",
                "draggable": True,
                "selectable": True,
            },
        ],
        "initialVisibleObjectIds": [
            "A",
            "B",
            "C",
            "segmentAB",
            "base",
            "rayAC",
            "circleA",
            "arcABC",
            "triangle",
            "angleBAC",
            "M",
            "I",
            "perpendicularC",
            "parallelC",
            "circumABC",
            "labelM",
        ],
        "animationIds": ["pulse-A"],
        "fallbackImageAssetId": "synthetic-m4-geometry-fallback",
        "accessibilityDescription": (
            "A synthetic coordinate construction containing three free points and examples of "
            "every approved geometry primitive."
        ),
        "provenance": synthetic_provenance("Synthetic Milestone 4 geometry scene"),
    }


def geometry_scene_variant() -> dict[str, Any]:
    return deepcopy(synthetic_geometry_scene_version())


def synthetic_geometry_content_package() -> dict[str, Any]:
    package = synthetic_content_package()
    scene_version = synthetic_geometry_scene_version()
    scene_version["id"] = package["geometryScenes"][0]["currentVersionId"]
    package["geometryScenes"][0]["versions"] = [scene_version]
    for hint in package["problems"][0]["versions"][0]["hints"]:
        hint["geometryActions"] = []
    return package
