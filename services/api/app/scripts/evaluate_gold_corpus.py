import argparse
import asyncio
import json
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

from app.evaluation.fake_provider import DeterministicFakeEvaluationProvider
from app.evaluation.provider import EvaluationProviderRequest
from app.evaluation.schemas import ProviderReadyEvaluation

SYNTHETIC_ATTEMPT_ID = uuid.UUID("70000000-0000-4000-8000-000000000200")


class GoldModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class GoldProvenance(GoldModel):
    classification: Literal["original_synthetic_non_personal"]
    created_at: str = Field(alias="createdAt")
    personal_data: Literal[False] = Field(alias="personalData")
    real_learner_work: Literal[False] = Field(alias="realLearnerWork")
    provider_response: Literal[False] = Field(alias="providerResponse")


class GoldFixture(GoldModel):
    name: str
    category: str
    marker: str
    expected_outcome: Literal["ready", "uncertain"] = Field(alias="expectedOutcome")
    expected_score: Decimal | None = Field(alias="expectedScore")
    expected_judgments: list[str] = Field(alias="expectedJudgments")
    expected_error_kinds: list[str] = Field(alias="expectedErrorKinds")


class GoldCorpus(GoldModel):
    schema_version: Literal["1.0.0"] = Field(alias="schemaVersion")
    provenance: GoldProvenance
    fixtures: list[GoldFixture] = Field(min_length=1)


corpus_adapter = TypeAdapter(GoldCorpus)


async def evaluate_corpus(path: Path) -> dict[str, object]:
    corpus = corpus_adapter.validate_json(path.read_text(encoding="utf-8"))
    provider = DeterministicFakeEvaluationProvider()
    if provider.identity.provider != "application-owned-deterministic-fake":
        raise RuntimeError("The local gold check must never use a network provider")
    results: list[dict[str, object]] = []
    for fixture in corpus.fixtures:
        result = await provider.evaluate(
            EvaluationProviderRequest(
                attempt_id=SYNTHETIC_ATTEMPT_ID,
                transcript_block_ids=("block-1", "block-2", "block-3"),
                rubric_limits=(("midpoint", Decimal("2.00")), ("distance", Decimal("2.00"))),
                context_json=json.dumps(
                    {
                        "confirmedTranscript": {
                            "blocks": [
                                {
                                    "id": "block-1",
                                    "type": "text",
                                    "text": f"SYNTHETIC-EVAL:{fixture.marker}",
                                },
                                {
                                    "id": "block-2",
                                    "type": "math",
                                    "latex": "M=(3,0)"
                                    if fixture.marker == "subtle-error"
                                    else "M=(2,0)",
                                },
                                {"id": "block-3", "type": "text", "text": "Synthetic end."},
                            ]
                        }
                    },
                    ensure_ascii=False,
                ),
            )
        )
        if isinstance(result.payload, ProviderReadyEvaluation):
            score: Decimal | None = sum(
                (award.awarded_score for award in result.payload.rubric_awards), Decimal("0")
            )
            judgments = [step.judgment for step in result.payload.reasoning_steps]
            error_kinds = [step.error_kind for step in result.payload.reasoning_steps]
        else:
            score = None
            judgments = []
            error_kinds = []
        matches = (
            result.outcome == fixture.expected_outcome
            and score == fixture.expected_score
            and judgments == fixture.expected_judgments
            and error_kinds == fixture.expected_error_kinds
        )
        results.append(
            {
                "fixture": fixture.name,
                "category": fixture.category,
                "outcome": result.outcome,
                "score": None if score is None else str(score.quantize(Decimal("0.00"))),
                "judgments": judgments,
                "errorKinds": error_kinds,
                "schemaAttempts": result.schema_attempts,
                "costUsd": str(result.cost_usd),
                "matchesExpectedBehavior": matches,
            }
        )
    matched = sum(bool(item["matchesExpectedBehavior"]) for item in results)
    return {
        "schemaVersion": "1.0.0",
        "generatedAt": datetime.now(UTC).isoformat(),
        "provider": provider.identity.provider,
        "modelSnapshot": provider.identity.model_snapshot,
        "fixtureCount": len(results),
        "matchedExpectedBehaviorCount": matched,
        "allExpectedBehaviorsMatched": matched == len(results),
        "releaseThreshold": None,
        "results": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the no-network M7 synthetic gold evaluation regression."
    )
    parser.add_argument("corpus", type=Path)
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    report = asyncio.run(evaluate_corpus(arguments.corpus))
    serialized = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if arguments.output is None:
        print(serialized, end="")
    else:
        arguments.output.write_text(serialized, encoding="utf-8")
    if not report["allExpectedBehaviorsMatched"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
