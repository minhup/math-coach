from decimal import Decimal

import pytest
from app.evaluation.schemas import ProviderReadyEvaluation, ProviderUncertainEvaluation
from pydantic import ValidationError


def valid_ready_payload() -> dict[str, object]:
    return {
        "outcome": "ready",
        "reasoningSteps": [
            {
                "stepKey": "step-1",
                "transcriptBlockIds": ["block-1"],
                "summary": "The first calculation is incorrect.",
                "judgment": "incorrect",
                "errorKind": "root",
                "dependsOnStepKeys": [],
                "feedback": "Check the first coordinate average.",
            },
            {
                "stepKey": "step-2",
                "transcriptBlockIds": ["block-2"],
                "summary": "The conclusion depends on the first calculation.",
                "judgment": "incorrect",
                "errorKind": "dependent",
                "dependsOnStepKeys": ["step-1"],
                "feedback": "Recompute after fixing the root error.",
            },
        ],
        "rubricAwards": [
            {
                "rubricCode": "method",
                "awardedScore": "0",
                "explanation": "The method begins with an incorrect value.",
            }
        ],
        "overallFeedback": "Correct the earliest error first.",
        "nextAction": "Request the first hint if needed.",
    }


def test_ready_schema_rejects_unknown_provider_fields() -> None:
    payload = valid_ready_payload()
    payload["hiddenReasoning"] = "must never cross the boundary"

    with pytest.raises(ValidationError):
        ProviderReadyEvaluation.model_validate(payload)


@pytest.mark.parametrize(
    "unsafe_text",
    [
        "**bold**",
        "_emphasis_",
        "`code`",
        "- list item",
        "> quoted provider text",
        "<script>alert(1)</script>",
        "https://example.test",
        "www.example.test",
        "javascript:alert(1)",
        "[link](bad)",
    ],
)
def test_ready_schema_rejects_markup_urls_and_executable_content(unsafe_text: str) -> None:
    payload = valid_ready_payload()
    payload["overallFeedback"] = unsafe_text

    with pytest.raises(ValidationError):
        ProviderReadyEvaluation.model_validate(payload)


def test_dependent_error_must_point_backward_and_reach_a_root() -> None:
    payload = valid_ready_payload()
    steps = payload["reasoningSteps"]
    assert isinstance(steps, list)
    assert isinstance(steps[1], dict)
    steps[1]["dependsOnStepKeys"] = ["step-3"]

    with pytest.raises(ValidationError):
        ProviderReadyEvaluation.model_validate(payload)


def test_non_incorrect_step_cannot_claim_an_error_relationship() -> None:
    payload = valid_ready_payload()
    steps = payload["reasoningSteps"]
    assert isinstance(steps, list)
    assert isinstance(steps[0], dict)
    steps[0]["judgment"] = "uncertain"

    with pytest.raises(ValidationError):
        ProviderReadyEvaluation.model_validate(payload)


def test_uncertainty_contains_no_score_steps_or_feedback_result() -> None:
    result = ProviderUncertainEvaluation.model_validate(
        {
            "outcome": "uncertain",
            "reason": "There is not enough coherent work for fair scoring.",
            "recommendedAction": "manual_review",
        }
    )

    assert result.outcome == "uncertain"
    assert not hasattr(result, "reasoning_steps")
    assert not hasattr(result, "score")


def test_decimal_rubric_awards_remain_exact() -> None:
    result = ProviderReadyEvaluation.model_validate(valid_ready_payload())

    assert result.rubric_awards[0].awarded_score == Decimal("0")
