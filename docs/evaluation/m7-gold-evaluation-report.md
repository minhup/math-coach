# Milestone 7 gold evaluation report

- Date: 2026-08-28
- Data classification: original synthetic, non-personal
- Provider: `application-owned-deterministic-fake`
- Model snapshot: `m7-evaluation-fixture-v1`
- Network/paid calls: none
- Release threshold: not defined

## Scope

The regression uses [the committed corpus](../../evals/grading/m7-gold-corpus.json) through the same
strict `StrictEvaluationProvider` validation path used by the application. It measures contract and
application behavior only. It is not evidence of production grading quality, provider suitability,
or calibration on learner work.

## Measured result

Command:

```text
make evaluation-gold
```

Six of six fixtures matched their recorded expected application behavior. Every fixture used one
schema attempt and recorded zero tokens and `0.000000` USD cost.

| Fixture                   | Coverage category          | Outcome   |     Score | Step judgments       | Error kinds     | Match |
| ------------------------- | -------------------------- | --------- | --------: | -------------------- | --------------- | ----- |
| correct-standard          | correct standard solution  | ready     | 4.00/4.00 | correct              | none            | yes   |
| correct-alternative       | valid alternative solution | ready     | 4.00/4.00 | correct              | none            | yes   |
| subtle-midpoint-error     | subtle mathematical error  | ready     | 0.00/4.00 | incorrect, incorrect | root, dependent | yes   |
| incomplete-solution       | incomplete solution        | ready     | 0.00/4.00 | not assessable       | none            | yes   |
| contradictory-work        | contradictory work         | uncertain |      none | none                 | none            | yes   |
| unreadable-confirmed-work | unreadable work            | uncertain |      none | none                 | none            | yes   |

The alternative fixture intentionally differs from the curated coordinate reference method and
receives full credit. Contradictory and unreadable fixtures contain neither score nor fabricated
reasoning steps.

## Interpretation and limitation

No numeric release gate was invented. The six fixtures are deterministic regression oracles for
schema enforcement, alternative-method acceptance, root/dependent representation, rubric total
consistency, incomplete work, and safe uncertainty. A separately authorized real-provider
benchmark with a reviewed synthetic corpus is still required before any claim about grading
quality, accuracy, calibration, or external-pilot readiness.
