import pytest
from app.content.schemas import GeometryAction, GeometrySceneVersion
from app.evaluation.service import validate_geometry_actions_against_scene
from pydantic import TypeAdapter
from tests.fixtures.geometry import synthetic_geometry_scene_version

actions_adapter = TypeAdapter(list[GeometryAction])


def scene() -> GeometrySceneVersion:
    return GeometrySceneVersion.model_validate(synthetic_geometry_scene_version())


def action_list(value: list[dict[str, object]]) -> list[GeometryAction]:
    return actions_adapter.validate_python(value)


def test_curated_geometry_hint_actions_accept_existing_capable_ids() -> None:
    actions = action_list(
        [
            {"type": "highlight", "objectIds": ["A", "M"]},
            {"type": "animate", "objectId": "A", "animationId": "pulse-A"},
            {
                "type": "ask_select",
                "prompt": [{"id": "select-a", "type": "text", "text": "Select A."}],
                "allowedObjectIds": ["A", "B"],
                "correctObjectIds": ["A"],
            },
        ]
    )

    validate_geometry_actions_against_scene(actions, scene())


@pytest.mark.parametrize(
    "payload",
    [
        [{"type": "highlight", "objectIds": ["UNKNOWN"]}],
        [{"type": "animate", "objectId": "segmentAB", "animationId": "pulse-A"}],
        [
            {
                "type": "ask_select",
                "prompt": [{"id": "select-m", "type": "text", "text": "Select M."}],
                "allowedObjectIds": ["M"],
                "correctObjectIds": ["M"],
            }
        ],
        [
            {
                "type": "ask_select",
                "prompt": [{"id": "select-a", "type": "text", "text": "Select A."}],
                "allowedObjectIds": ["A"],
                "correctObjectIds": ["B"],
            }
        ],
    ],
)
def test_geometry_hint_actions_reject_unknown_or_incapable_curated_ids(
    payload: list[dict[str, object]],
) -> None:
    with pytest.raises(ValueError):
        validate_geometry_actions_against_scene(action_list(payload), scene())
