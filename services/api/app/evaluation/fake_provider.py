import json
from decimal import Decimal

from app.evaluation.prompt import PROMPT_HASH, PROMPT_VERSION, PROVIDER_SCHEMA_VERSION
from app.evaluation.provider import (
    EvaluationProviderCall,
    EvaluationProviderIdentity,
    EvaluationProviderRequest,
    StrictEvaluationProvider,
)

FAKE_MODEL = "m7-evaluation-fixture-v1"


class DeterministicFakeEvaluationProvider(StrictEvaluationProvider):
    def __init__(self) -> None:
        super().__init__(
            EvaluationProviderIdentity(
                provider="application-owned-deterministic-fake",
                model_snapshot=FAKE_MODEL,
                prompt_version=PROMPT_VERSION,
                prompt_hash=PROMPT_HASH,
                schema_version=PROVIDER_SCHEMA_VERSION,
                pricing_version="fake-zero-v1",
                input_usd_per_million=Decimal("0"),
                output_usd_per_million=Decimal("0"),
            )
        )

    @staticmethod
    def _awards(
        request: EvaluationProviderRequest, *, fraction: Decimal
    ) -> list[dict[str, object]]:
        return [
            {
                "rubricCode": code,
                "awardedScore": str((maximum * fraction).quantize(Decimal("0.01"))),
                "explanation": (
                    "The confirmed work supports this rubric item."
                    if fraction == Decimal("1")
                    else "The confirmed work does not yet support this rubric item."
                ),
            }
            for code, maximum in request.rubric_limits
        ]

    @staticmethod
    def _steps(request: EvaluationProviderRequest, *, scenario: str) -> list[dict[str, object]]:
        blocks = list(request.transcript_block_ids)
        if scenario in {"correct-standard", "correct-alternative"}:
            return [
                {
                    "stepKey": "step-1",
                    "transcriptBlockIds": blocks,
                    "summary": "The confirmed work uses a valid mathematical method.",
                    "judgment": "correct",
                    "errorKind": "none",
                    "dependsOnStepKeys": [],
                    "feedback": (
                        "This alternative method is mathematically valid."
                        if scenario == "correct-alternative"
                        else "The method and conclusion are correct."
                    ),
                }
            ]
        if scenario == "subtle-error" and len(blocks) > 1:
            return [
                {
                    "stepKey": "step-1",
                    "transcriptBlockIds": blocks[:-1],
                    "summary": "The midpoint coordinate is computed incorrectly.",
                    "judgment": "incorrect",
                    "errorKind": "root",
                    "dependsOnStepKeys": [],
                    "feedback": "Average each coordinate of the two endpoints.",
                },
                {
                    "stepKey": "step-2",
                    "transcriptBlockIds": [blocks[-1]],
                    "summary": "The later distance conclusion uses that midpoint.",
                    "judgment": "incorrect",
                    "errorKind": "dependent",
                    "dependsOnStepKeys": ["step-1"],
                    "feedback": "Recompute this after correcting the midpoint.",
                },
            ]
        if scenario == "subtle-error":
            return [
                {
                    "stepKey": "step-1",
                    "transcriptBlockIds": blocks,
                    "summary": "The confirmed calculation contains a mathematical error.",
                    "judgment": "incorrect",
                    "errorKind": "root",
                    "dependsOnStepKeys": [],
                    "feedback": "Check the coordinate calculation from its first operation.",
                }
            ]
        return [
            {
                "stepKey": "step-1",
                "transcriptBlockIds": blocks,
                "summary": "The confirmed work begins a relevant method but does not finish it.",
                "judgment": "not_assessable",
                "errorKind": "none",
                "dependsOnStepKeys": [],
                "feedback": "Continue far enough to support the requested conclusion.",
            }
        ]

    async def _invoke(
        self, request: EvaluationProviderRequest, *, repair_schema: bool
    ) -> EvaluationProviderCall:
        context = json.loads(request.context_json)
        serialized = json.dumps(context, ensure_ascii=False).lower()
        if "synthetic-eval:contradictory" in serialized:
            payload: object = {
                "outcome": "uncertain",
                "reason": "The confirmed work contains contradictory conclusions.",
                "recommendedAction": "manual_review",
            }
        elif "synthetic-eval:unreadable" in serialized:
            payload = {
                "outcome": "uncertain",
                "reason": "The confirmed content is insufficiently clear for a fair evaluation.",
                "recommendedAction": "manual_review",
            }
        else:
            scenario = "incomplete"
            if "synthetic-eval:correct-standard" in serialized:
                scenario = "correct-standard"
            elif "synthetic-eval:correct-alternative" in serialized:
                scenario = "correct-alternative"
            elif "synthetic-eval:subtle-error" in serialized or "m=(3,0)" in serialized:
                scenario = "subtle-error"
            fraction = Decimal("1") if scenario.startswith("correct-") else Decimal("0")
            payload = {
                "outcome": "ready",
                "reasoningSteps": self._steps(request, scenario=scenario),
                "rubricAwards": self._awards(request, fraction=fraction),
                "overallFeedback": (
                    "The confirmed solution is mathematically valid."
                    if fraction == Decimal("1")
                    else "Use the step feedback to revise the confirmed reasoning."
                ),
                "nextAction": (
                    "Compare this valid method with another solution."
                    if fraction == Decimal("1")
                    else "Request the first progressive hint when you are ready."
                ),
            }
        return EvaluationProviderCall(
            payload=payload,
            latency_ms=0,
            input_tokens=0,
            output_tokens=0,
        )
