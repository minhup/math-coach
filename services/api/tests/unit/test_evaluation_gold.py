import asyncio
from pathlib import Path

from app.scripts.evaluate_gold_corpus import evaluate_corpus

CORPUS = Path(__file__).resolve().parents[4] / "evals/grading/m7-gold-corpus.json"


def test_synthetic_gold_corpus_matches_recorded_application_behavior_without_network() -> None:
    report = asyncio.run(evaluate_corpus(CORPUS))

    assert report["provider"] == "application-owned-deterministic-fake"
    assert report["fixtureCount"] == 6
    assert report["matchedExpectedBehaviorCount"] == 6
    assert report["allExpectedBehaviorsMatched"] is True
    assert report["releaseThreshold"] is None
