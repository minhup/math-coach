from copy import deepcopy
from typing import Any


def synthetic_provenance(title: str) -> dict[str, Any]:
    return {
        "sourceKind": "original_synthetic",
        "title": title,
        "creator": "Math Coach fixture author",
        "sourceReference": "repo://content/synthetic-m2-foundations-v1",
        "acquisitionDate": "2026-08-26",
        "acquiredBy": "Math Coach development",
        "rightsBasis": "original_fixture",
        "rightsEvidence": "Created solely for Milestone 2 automated testing.",
        "permittedUses": ["internal_development", "automated_testing"],
        "restrictions": ["not_real_exam_content"],
        "attributionText": "Original synthetic Math Coach fixture.",
        "adaptationDescription": None,
        "translationDescription": None,
        "derivativeOf": [],
        "mathematicsReviewer": "Synthetic fixture reviewer",
        "mathematicsReviewedAt": "2026-08-26",
        "rightsReviewer": "Synthetic fixture reviewer",
        "rightsReviewedAt": "2026-08-26",
        "publicationStatus": "synthetic_only",
        "publicationDate": "2026-08-26",
    }


def synthetic_content_package() -> dict[str, Any]:
    provenance = synthetic_provenance
    package: dict[str, Any] = {
        "schemaVersion": "1.0.0",
        "packageId": "10000000-0000-4000-8000-000000000001",
        "packageVersion": 1,
        "title": "Milestone 2 synthetic foundations",
        "publicationStatus": "synthetic_only",
        "provenance": provenance("Milestone 2 synthetic package"),
        "exams": [
            {
                "id": "10000000-0000-4000-8000-000000000101",
                "code": "SYN-AURORA",
                "name": "Synthetic Aurora Mathematics Examination",
                "region": "Fictional North Region",
                "status": "synthetic",
                "provenance": provenance("Synthetic Aurora examination"),
            },
            {
                "id": "10000000-0000-4000-8000-000000000102",
                "code": "SYN-HARBOR",
                "name": "Synthetic Harbor Mathematics Examination",
                "region": "Fictional South Region",
                "status": "synthetic",
                "provenance": provenance("Synthetic Harbor examination"),
            },
        ],
        "examCycles": [
            {
                "id": "10000000-0000-4000-8000-000000000201",
                "examId": "10000000-0000-4000-8000-000000000101",
                "cycleCode": "SYN-AURORA-2027",
                "year": 2027,
                "examDate": "2027-06-01",
                "maximumScore": "20.00",
                "contentVersion": 1,
                "status": "synthetic",
                "provenance": provenance("Synthetic Aurora 2027 cycle"),
            },
            {
                "id": "10000000-0000-4000-8000-000000000202",
                "examId": "10000000-0000-4000-8000-000000000102",
                "cycleCode": "SYN-HARBOR-2027",
                "year": 2027,
                "examDate": "2027-06-15",
                "maximumScore": "20.00",
                "contentVersion": 1,
                "status": "synthetic",
                "provenance": provenance("Synthetic Harbor 2027 cycle"),
            },
        ],
        "skills": [
            {
                "id": "10000000-0000-4000-8000-000000000301",
                "code": "SYN-COORDINATE-DISTANCE",
                "name": "Coordinate distance reasoning",
                "description": [
                    {
                        "id": "skill-distance-text",
                        "type": "text",
                        "text": "Use coordinate differences to reason about squared distances.",
                    }
                ],
                "domain": "geometry",
                "status": "synthetic",
                "provenance": provenance("Synthetic coordinate distance skill"),
            },
            {
                "id": "10000000-0000-4000-8000-000000000302",
                "code": "SYN-MIDPOINT",
                "name": "Midpoint reasoning",
                "description": [
                    {
                        "id": "skill-midpoint-text",
                        "type": "text",
                        "text": "Use the midpoint definition in geometric and coordinate settings.",
                    }
                ],
                "domain": "geometry",
                "status": "synthetic",
                "provenance": provenance("Synthetic midpoint skill"),
            },
        ],
        "skillRelationships": [
            {
                "id": "10000000-0000-4000-8000-000000000310",
                "parentSkillId": "10000000-0000-4000-8000-000000000302",
                "childSkillId": "10000000-0000-4000-8000-000000000301",
                "relationType": "related",
                "provenance": provenance("Synthetic shared-skill relationship"),
            }
        ],
        "examSkillWeights": [
            {
                "id": "10000000-0000-4000-8000-000000000401",
                "examCycleId": "10000000-0000-4000-8000-000000000201",
                "skillId": "10000000-0000-4000-8000-000000000301",
                "weight": "0.60",
                "sourceNote": "Synthetic expert configuration; not a statistical claim.",
                "version": 1,
                "provenance": provenance("Synthetic Aurora distance weight"),
            },
            {
                "id": "10000000-0000-4000-8000-000000000402",
                "examCycleId": "10000000-0000-4000-8000-000000000201",
                "skillId": "10000000-0000-4000-8000-000000000302",
                "weight": "0.40",
                "sourceNote": "Synthetic expert configuration; not a statistical claim.",
                "version": 1,
                "provenance": provenance("Synthetic Aurora midpoint weight"),
            },
            {
                "id": "10000000-0000-4000-8000-000000000403",
                "examCycleId": "10000000-0000-4000-8000-000000000202",
                "skillId": "10000000-0000-4000-8000-000000000301",
                "weight": "0.50",
                "sourceNote": "Synthetic expert configuration; not a statistical claim.",
                "version": 1,
                "provenance": provenance("Synthetic Harbor distance weight"),
            },
            {
                "id": "10000000-0000-4000-8000-000000000404",
                "examCycleId": "10000000-0000-4000-8000-000000000202",
                "skillId": "10000000-0000-4000-8000-000000000302",
                "weight": "0.50",
                "sourceNote": "Synthetic expert configuration; not a statistical claim.",
                "version": 1,
                "provenance": provenance("Synthetic Harbor midpoint weight"),
            },
        ],
        "geometryScenes": [
            {
                "id": "10000000-0000-4000-8000-000000000500",
                "code": "SYN-TRIANGLE-MIDPOINT",
                "name": "Synthetic coordinate triangle and midpoint",
                "currentVersionId": "10000000-0000-4000-8000-000000000501",
                "status": "synthetic",
                "versions": [
                    {
                        "id": "10000000-0000-4000-8000-000000000501",
                        "version": 1,
                        "viewport": {"xMin": -1, "xMax": 7, "yMin": -1, "yMax": 5},
                        "objects": [
                            {"id": "A", "type": "point", "x": 0, "y": 0, "label": "A"},
                            {"id": "B", "type": "point", "x": 6, "y": 0, "label": "B"},
                            {"id": "C", "type": "point", "x": 2, "y": 4, "label": "C"},
                            {"id": "AB", "type": "segment", "parents": ["A", "B"]},
                            {"id": "BC", "type": "segment", "parents": ["B", "C"]},
                            {"id": "CA", "type": "segment", "parents": ["C", "A"]},
                            {"id": "M", "type": "midpoint", "parents": ["A", "B"], "label": "M"},
                            {"id": "CM", "type": "segment", "parents": ["C", "M"]},
                        ],
                        "initialVisibleObjectIds": ["A", "B", "C", "AB", "BC", "CA", "M"],
                        "animationIds": [],
                        "fallbackImageAssetId": "synthetic-triangle-midpoint-fallback",
                        "accessibilityDescription": (
                            "A coordinate triangle with A at zero and B at six on the horizontal "
                            "axis, C above the axis, and M at the midpoint of AB."
                        ),
                        "provenance": provenance("Synthetic coordinate triangle scene"),
                    }
                ],
            }
        ],
        "concepts": [
            {
                "id": "10000000-0000-4000-8000-000000000600",
                "code": "SYN-MIDPOINT-COORDINATES",
                "name": "Midpoint coordinates",
                "currentVersionId": "10000000-0000-4000-8000-000000000601",
                "status": "synthetic",
                "versions": [
                    {
                        "id": "10000000-0000-4000-8000-000000000601",
                        "version": 1,
                        "content": [
                            {
                                "id": "concept-line",
                                "type": "rich_line",
                                "spans": [
                                    {"type": "text", "text": "The midpoint of "},
                                    {"type": "math", "latex": "(x_1,y_1)"},
                                    {"type": "text", "text": " and "},
                                    {"type": "math", "latex": "(x_2,y_2)"},
                                    {
                                        "type": "text",
                                        "text": " averages corresponding coordinates.",
                                    },
                                ],
                            },
                            {
                                "id": "concept-formula",
                                "type": "display_math",
                                "latex": "M=\\left(\\frac{x_1+x_2}{2},\\frac{y_1+y_2}{2}\\right)",
                            },
                        ],
                        "geometrySceneVersionId": "10000000-0000-4000-8000-000000000501",
                        "provenance": provenance("Synthetic midpoint concept"),
                    }
                ],
            }
        ],
        "problems": [
            {
                "id": "10000000-0000-4000-8000-000000000700",
                "externalCode": "SYN-M2-GEO-001",
                "originExamCycleId": None,
                "year": None,
                "problemNumber": "Synthetic 1",
                "currentVersionId": "10000000-0000-4000-8000-000000000701",
                "status": "synthetic",
                "versions": [
                    {
                        "id": "10000000-0000-4000-8000-000000000701",
                        "version": 1,
                        "statement": [
                            {
                                "id": "problem-intro",
                                "type": "rich_line",
                                "spans": [
                                    {"type": "text", "text": "Let "},
                                    {"type": "math", "latex": "A(0,0), B(6,0), C(2,4)"},
                                    {"type": "text", "text": ", and let M be the midpoint of AB."},
                                ],
                            },
                            {
                                "id": "problem-question",
                                "type": "text",
                                "text": "Find the squared length CM² and justify the result.",
                            },
                            {
                                "id": "problem-scene",
                                "type": "geometry",
                                "sceneVersionId": "10000000-0000-4000-8000-000000000501",
                            },
                        ],
                        "maximumScore": "4.00",
                        "difficultyBand": "core",
                        "estimatedMinutes": 12,
                        "geometrySceneVersionId": "10000000-0000-4000-8000-000000000501",
                        "examRelevance": [
                            {
                                "examCycleId": "10000000-0000-4000-8000-000000000201",
                                "relevanceLevel": "high",
                                "relevanceNote": "Synthetic shared coordinate-geometry practice.",
                                "provenance": provenance("Synthetic Aurora problem relevance"),
                            },
                            {
                                "examCycleId": "10000000-0000-4000-8000-000000000202",
                                "relevanceLevel": "high",
                                "relevanceNote": "Synthetic shared coordinate-geometry practice.",
                                "provenance": provenance("Synthetic Harbor problem relevance"),
                            },
                        ],
                        "skillLinks": [
                            {
                                "skillId": "10000000-0000-4000-8000-000000000301",
                                "role": "primary",
                                "importance": "0.60",
                                "provenance": provenance("Synthetic distance skill link"),
                            },
                            {
                                "skillId": "10000000-0000-4000-8000-000000000302",
                                "role": "secondary",
                                "importance": "0.40",
                                "provenance": provenance("Synthetic midpoint skill link"),
                            },
                        ],
                        "referenceSolutions": [
                            {
                                "id": "10000000-0000-4000-8000-000000000801",
                                "solutionCode": "coordinate-method",
                                "content": [
                                    {
                                        "id": "solution-midpoint",
                                        "type": "rich_line",
                                        "spans": [
                                            {"type": "text", "text": "The midpoint is "},
                                            {"type": "math", "latex": "M(3,0)"},
                                            {"type": "text", "text": "."},
                                        ],
                                    },
                                    {
                                        "id": "solution-distance",
                                        "type": "display_math",
                                        "latex": "CM^2=(3-2)^2+(0-4)^2=17",
                                    },
                                ],
                                "methodLabel": "Coordinate midpoint and distance",
                                "expertVerified": True,
                                "nonExhaustive": True,
                                "provenance": provenance("Synthetic coordinate reference solution"),
                            }
                        ],
                        "rubric": [
                            {
                                "id": "10000000-0000-4000-8000-000000000901",
                                "rubricCode": "midpoint",
                                "description": [
                                    {
                                        "id": "rubric-midpoint-text",
                                        "type": "text",
                                        "text": "Correctly determines the midpoint M as (3,0).",
                                    }
                                ],
                                "maximumScore": "2.00",
                                "skillId": "10000000-0000-4000-8000-000000000302",
                                "orderIndex": 1,
                                "provenance": provenance("Synthetic midpoint rubric item"),
                            },
                            {
                                "id": "10000000-0000-4000-8000-000000000902",
                                "rubricCode": "distance",
                                "description": [
                                    {
                                        "id": "rubric-distance-text",
                                        "type": "text",
                                        "text": "Correctly computes and justifies CM² as 17.",
                                    }
                                ],
                                "maximumScore": "2.00",
                                "skillId": "10000000-0000-4000-8000-000000000301",
                                "orderIndex": 2,
                                "provenance": provenance("Synthetic distance rubric item"),
                            },
                        ],
                        "hints": [
                            {
                                "id": f"10000000-0000-4000-8000-000000000a0{level}",
                                "hintLevel": level,
                                "content": [
                                    {
                                        "id": f"hint-{level}-text",
                                        "type": "text",
                                        "text": text,
                                    }
                                ],
                                "geometryActions": actions,
                                "revealsCompleteSolution": level == 5,
                                "conceptId": (
                                    "10000000-0000-4000-8000-000000000600"
                                    if level in {2, 3}
                                    else None
                                ),
                                "provenance": provenance(f"Synthetic hint level {level}"),
                            }
                            for level, text, actions in [
                                (
                                    1,
                                    "Identify the point whose coordinates are available from the "
                                    "midpoint definition.",
                                    [],
                                ),
                                (
                                    2,
                                    "Use the midpoint formula for A and B.",
                                    [{"type": "highlight", "objectIds": ["A", "B", "M"]}],
                                ),
                                (
                                    3,
                                    "First compute M, then compare the coordinates of C and M.",
                                    [{"type": "show", "objectIds": ["CM"]}],
                                ),
                                (
                                    4,
                                    "The midpoint is M(3,0); substitute C(2,4) into the "
                                    "squared-distance formula.",
                                    [],
                                ),
                                (
                                    5,
                                    "M=(3,0), so CM²=(3-2)²+(0-4)²=17.",
                                    [{"type": "highlight", "objectIds": ["CM"]}],
                                ),
                            ]
                        ],
                        "provenance": provenance("Synthetic coordinate geometry problem version"),
                    }
                ],
            }
        ],
    }
    return deepcopy(package)
