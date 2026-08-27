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
            {"id": "B", "type": "point", "x": 6, "y": 0, "label": "B", "selectable": True},
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


def _m4_provenance(title: str) -> dict[str, Any]:
    provenance = synthetic_provenance(title)
    provenance.update(
        {
            "sourceReference": "repo://content/synthetic-m4-geometry-v1",
            "acquisitionDate": "2026-08-27",
            "rightsEvidence": "Created solely for Milestone 4 automated testing.",
            "mathematicsReviewedAt": "2026-08-27",
            "rightsReviewedAt": "2026-08-27",
            "publicationDate": "2026-08-27",
        }
    )
    return provenance


def _refresh_nested_provenance(value: Any) -> None:
    if isinstance(value, dict):
        provenance = value.get("provenance")
        if isinstance(provenance, dict):
            value["provenance"] = _m4_provenance(str(provenance["title"]))
        for nested in value.values():
            _refresh_nested_provenance(nested)
    elif isinstance(value, list):
        for nested in value:
            _refresh_nested_provenance(nested)


def synthetic_m4_content_package() -> dict[str, Any]:
    """Build the incremental M4 package while retaining exact shared M2 skill records."""
    package = synthetic_content_package()
    package.update(
        {
            "packageId": "40000000-0000-4000-8000-000000000001",
            "packageVersion": 1,
            "title": "Milestone 4 synthetic interactive geometry",
            "provenance": _m4_provenance("Milestone 4 synthetic geometry package"),
            "concepts": [],
        }
    )
    scene_version = synthetic_geometry_scene_version()
    scene_version["provenance"] = _m4_provenance("Synthetic Milestone 4 geometry scene")
    package["geometryScenes"] = [
        {
            "id": "40000000-0000-4000-8000-000000000500",
            "code": "SYN-M4-ALL-PRIMITIVES",
            "name": "Synthetic interactive all-primitives construction",
            "currentVersionId": scene_version["id"],
            "status": "synthetic",
            "versions": [scene_version],
        }
    ]

    problem = package["problems"][0]
    version = problem["versions"][0]
    problem.update(
        {
            "id": "40000000-0000-4000-8000-000000000700",
            "externalCode": "SYN-M4-GEO-001",
            "problemNumber": "Synthetic geometry 1",
            "currentVersionId": "40000000-0000-4000-8000-000000000701",
        }
    )
    version.update(
        {
            "id": problem["currentVersionId"],
            "geometrySceneVersionId": scene_version["id"],
            "estimatedMinutes": 15,
        }
    )
    version["statement"] = [
        {
            "id": "m4-problem-intro",
            "type": "rich_line",
            "spans": [
                {"type": "text", "text": "In the synthetic scene, let "},
                {"type": "math", "latex": "A(0,0), B(4,0), C(1,3)"},
                {"type": "text", "text": ", and let M be the midpoint of AB."},
            ],
        },
        {
            "id": "m4-problem-question",
            "type": "text",
            "text": "Move A if useful, then find CM² for the initial configuration and justify the result.",
        },
        {
            "id": "m4-problem-geometry",
            "type": "geometry",
            "sceneVersionId": scene_version["id"],
        },
    ]
    version["referenceSolutions"][0].update(
        {
            "id": "40000000-0000-4000-8000-000000000801",
            "solutionCode": "m4-coordinate-method",
            "content": [
                {
                    "id": "m4-solution-midpoint",
                    "type": "rich_line",
                    "spans": [
                        {"type": "text", "text": "Initially, the midpoint is "},
                        {"type": "math", "latex": "M(2,0)"},
                        {"type": "text", "text": "."},
                    ],
                },
                {
                    "id": "m4-solution-distance",
                    "type": "display_math",
                    "latex": "CM^2=(2-1)^2+(0-3)^2=10",
                },
            ],
        }
    )
    version["rubric"][0].update(
        {
            "id": "40000000-0000-4000-8000-000000000901",
            "description": [
                {
                    "id": "m4-rubric-midpoint",
                    "type": "text",
                    "text": "Correctly determines the initial midpoint M as (2,0).",
                }
            ],
        }
    )
    version["rubric"][1].update(
        {
            "id": "40000000-0000-4000-8000-000000000902",
            "description": [
                {
                    "id": "m4-rubric-distance",
                    "type": "text",
                    "text": "Correctly computes and justifies the initial value CM²=10.",
                }
            ],
        }
    )
    hint_specs = [
        (
            "Identify the free and constructed points.",
            [{"type": "highlight", "objectIds": ["A", "B", "C", "M"]}],
        ),
        (
            "Use the midpoint definition before computing a distance.",
            [
                {"type": "show", "objectIds": ["labelM"]},
                {
                    "type": "ask_select",
                    "prompt": [
                        {
                            "id": "m4-select-prompt",
                            "type": "text",
                            "text": "Select point A.",
                        }
                    ],
                    "allowedObjectIds": ["A", "B"],
                    "correctObjectIds": ["A"],
                },
            ],
        ),
        (
            "Focus on triangle ABC and midpoint M.",
            [{"type": "focus", "objectIds": ["triangle", "M"]}],
        ),
        (
            "The initial midpoint is M(2,0); compare M with C(1,3).",
            [
                {"type": "animate", "objectId": "A", "animationId": "pulse-A"},
                {"type": "clear_highlight", "objectIds": None},
            ],
        ),
        (
            "M=(2,0), so CM²=(2-1)²+(0-3)²=10.",
            [{"type": "hide", "objectIds": ["labelM"]}],
        ),
    ]
    for level, (text, actions) in enumerate(hint_specs, start=1):
        hint = version["hints"][level - 1]
        hint.update(
            {
                "id": f"40000000-0000-4000-8000-000000000a0{level}",
                "content": [
                    {
                        "id": f"m4-hint-{level}",
                        "type": "text",
                        "text": text,
                    }
                ],
                "geometryActions": actions,
                "conceptId": None,
            }
        )

    _refresh_nested_provenance(package["geometryScenes"])
    _refresh_nested_provenance(package["problems"])
    return deepcopy(package)
