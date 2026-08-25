# AI provider benchmark specification

## Status

- Milestone: 0 — Internal MVP direction and deferred-gate register
- Internal provider integration: NOT BLOCKED when using synthetic/non-personal inputs
- Production-provider and external-pilot confirmation: DEFERRED — benchmark `DECISION REQUIRED` fields remain
- Decision authority: Project owner
- Mathematics review evidence: DECISION REQUIRED
- Privacy review evidence: DECISION REQUIRED
- Last updated: 2026-08-25

This specification defines how candidate multimodal providers and model snapshots will be compared. It does not select a production provider, approve student-data processing, or claim that a consumer chat product and its API behave identically. Benchmark execution does not block deterministic fake-provider work or internal integration of a project-owner-selected development provider with synthetic/non-personal inputs.

## Benchmark decisions

| Decision | Approved value |
|---|---|
| Candidate providers and model snapshots | DECISION REQUIRED |
| Mathematics adjudication panel | DECISION REQUIRED |
| Number of cases per corpus stratum | DECISION REQUIRED |
| Number of repeated runs per case | DECISION REQUIRED |
| Prompt and schema versions used for the comparison | DECISION REQUIRED |
| Candidate configuration constraints | DECISION REQUIRED |
| Pass thresholds | DECISION REQUIRED in [`RELEASE_QUALITY_GATES.md`](RELEASE_QUALITY_GATES.md) |
| Metric priority or trade-off rule | DECISION REQUIRED |
| Maximum acceptable cost | DECISION REQUIRED |
| Maximum acceptable latency | DECISION REQUIRED |
| Tie-breaking method | DECISION REQUIRED |
| Final selection authority | Project owner |
| Benchmark execution/production-provider confirmation gate | Sending real participant data or starting an external pilot; does not block internal provider integration |

A provider may be evaluated internally with synthetic/non-personal inputs before its data-handling review is complete. It must not receive real participant data until its terms have passed the applicable review in [`PRIVACY_AND_CONSENT_ACTION_LIST.md`](../privacy/PRIVACY_AND_CONSENT_ACTION_LIST.md).

## Questions the benchmark must answer

1. How much work is required for a student to correct the transcription?
2. Does the model preserve mistakes, cross-outs, insertions, and incomplete reasoning rather than silently repairing them?
3. Does it segment written work into useful logical steps?
4. Does grading identify valid, root-error, dependent-error, incomplete, and uncertain work reliably?
5. Does it avoid criticizing valid steps and accept correct alternative methods?
6. Are progressive hints mathematically sound, useful, and appropriately revealing?
7. Does every response satisfy the strict application schema and approved geometry-action vocabulary?
8. Are latency, cost, availability, and data-handling terms acceptable for the pilot?

## Corpus design

The corpus must include representative examples from every approved examination and relevant mathematical domain. It must contain all of these strata:

| Required stratum | Minimum cases | Coverage notes |
|---|---|---|
| Clean handwriting | DECISION REQUIRED | Varied layouts and notation |
| Messy but readable handwriting | DECISION REQUIRED | Natural variation, not artificial corruption alone |
| Mixed Vietnamese and mathematics | DECISION REQUIRED | Inline and multi-line mathematics |
| Cross-outs and insertions | DECISION REQUIRED | Preserve the final written state and visible errors |
| Correct standard solutions | DECISION REQUIRED | Several skills and difficulty bands |
| Correct alternative solutions | DECISION REQUIRED | Methods materially different from stored references |
| Subtle mathematical errors | DECISION REQUIRED | Include plausible local errors and dependency chains |
| Incomplete solutions | DECISION REQUIRED | Several stopping points and partial-credit cases |
| Geometry solutions | DECISION REQUIRED | Diagrams, prose, symbols, and curated-scene relevance |

The final composition must also cover fractions, nested fractions, powers, subscripts, roots, systems, cases, inequalities, congruences, sets, logic, matrices, geometry symbols, Vietnamese mixed with inline math, and multi-line derivations where relevant.

### Sampling rules

- Define the approved cohort and examinations before claiming representativeness.
- Include difficulty, legibility, device/camera, lighting, orientation, and image-quality variation expected in the pilot.
- Prevent the same student, writer, problem, or solution template from dominating a split.
- Keep a locked unseen set for release evaluation.
- Record whether each sample is synthetic, commissioned, licensed, donated with approved consent, or collected during an approved pilot.
- Do not place identifiable student work in Git.
- Do not use student work for research or model improvement without the separately approved consent path.

Dataset size, split ratios, demographic review, and the permitted source categories are DECISION REQUIRED.

## Case record and ground truth

Each benchmark case must record:

```text
case ID and dataset version
problem ID and immutable content version
supported examination links
image asset reference and provenance category
image-quality and handwriting tags
expert transcription with block and step boundaries
expert grading judgment and rubric allocation
root and dependent error labels where applicable
valid alternative-method annotation
expected uncertainty or manual-review outcome
approved hint-quality rubric where hinting is evaluated
adjudicators and agreement state
```

Ground truth must be reviewed by qualified mathematics evaluators. Disagreement must be adjudicated and retained as metadata rather than silently overwritten. Reference solutions are non-exhaustive and cannot serve as the only ground truth for validity.

## Benchmark protocol

1. Freeze and version the dataset, prompts, schemas, model snapshot, provider parameters, and scoring code before evaluating candidates.
2. Run each candidate through the same application-facing adapter contract.
3. Provide only the inputs that the production workflow will provide.
4. Validate every output against the strict schema.
5. Permit at most one schema-repair retry and record the original failure and retry separately.
6. Never manually repair a candidate response before automatic scoring.
7. Randomize provider labels and case order for human review where practical.
8. Keep reviewers blind to provider identity during mathematical and hint-quality judgments.
9. Capture cold and warm latency according to a predeclared protocol.
10. Record provider, model snapshot, prompt version, schema version, latency, tokens, cost, retry count, and terminal state for every run.
11. Report per-stratum results, distributions, confidence intervals where appropriate, and worst-case failures; do not report only a global average.
12. Have the adjudication panel review critical errors and a declared sample of non-critical outcomes.

Run concurrency, timeouts, region, retry behavior for non-schema failures, sampling seeds, and confidence method are DECISION REQUIRED.

## Transcription measures

| Measure | Definition | Threshold |
|---|---|---|
| Schema-valid response rate | Runs valid before and after the single permitted schema retry, reported separately | DECISION REQUIRED |
| Correction completion rate | Cases a reviewer can correct into the gold transcript using the intended UI | DECISION REQUIRED |
| Correction time | Median, upper percentile, and distribution of active correction time | DECISION REQUIRED |
| Block correction burden | Insertions, deletions, replacements, splits, merges, and reorder actions normalized per case | DECISION REQUIRED |
| Text transcription error | Versioned text-error metric with Vietnamese handling documented | DECISION REQUIRED |
| Mathematical transcription error | Symbol- and structure-aware error rubric, including semantic-impact severity | DECISION REQUIRED |
| Step-boundary agreement | Agreement between generated and adjudicated step segmentation | DECISION REQUIRED |
| Silent-correction rate | Cases where the provider changes a written mathematical error into a correct statement | DECISION REQUIRED; critical failures reported individually |
| Warning usefulness | Precision/recall or reviewed usefulness of uncertainty warnings | DECISION REQUIRED |

Automated string similarity alone is insufficient for mathematics. The project owner must confirm the normalization and semantic-error rubric using qualified mathematics review evidence.

## Evaluation and grading measures

| Measure | Definition | Threshold |
|---|---|---|
| Structured-output validity | Response conforms to the versioned evaluation schema and allowed enums | DECISION REQUIRED |
| Score agreement | Exact agreement and absolute difference from adjudicated rubric score | DECISION REQUIRED |
| Step-status agreement | Agreement for valid, valid implicit, minor gap, major gap, root error, dependent error, and uncertain | DECISION REQUIRED |
| Root-error agreement | Agreement on the earliest causative mathematical error | DECISION REQUIRED |
| Dependent-error handling | Downstream steps are not independently over-penalized for the same root error | DECISION REQUIRED |
| False criticism of valid steps | Valid steps incorrectly marked as flawed | DECISION REQUIRED |
| Alternative-solution acceptance | Correct alternatives accepted without relying on reference-method identity | DECISION REQUIRED |
| Partial-credit consistency | Rubric allocations agree across equivalent evidence | DECISION REQUIRED |
| Uncertainty safety | Ambiguous cases route to uncertainty/manual review without fabricated scores or claims | DECISION REQUIRED |
| Feedback correctness | Concise feedback is mathematically correct and supported by the confirmed transcript | DECISION REQUIRED |

The confirmed transcript, not the image or raw provider transcript, is authoritative for grading evaluation.

## Hint measures

Review each hint level for:

- mathematical correctness;
- relevance to the confirmed work and current root issue;
- consistency with a progressive ladder;
- premature method or solution disclosure;
- acceptance of alternative methods;
- use only of allowed curated geometry object IDs and actions;
- clarity and usefulness to the target learner.

The rating instrument, evaluator training, sample size, usefulness threshold, harmful-hint threshold, and inter-rater agreement threshold are DECISION REQUIRED.

## Operational and data-handling measures

Report:

- median and upper-percentile end-to-end latency by operation;
- timeouts, provider errors, schema failures, and retry outcomes;
- input/output token or unit consumption;
- cost per transcription, evaluation, hint, attempt, and representative session;
- projected pilot cost under the approved cohort and usage assumptions;
- model/version stability and provider snapshot guarantees;
- regional availability and rate limits;
- retention, training use, subprocessors, deletion, security, and incident terms.

Acceptance thresholds and usage assumptions are DECISION REQUIRED. A quality-leading provider is not eligible if its approved data-handling or operational requirements are unmet.

## Critical-failure review

Individually review and report at least:

- silent correction of a student's mathematical error;
- fabricated transcript, score, hint, or success state after failure;
- confident rejection of a valid alternative solution;
- unsafe or invalid geometry action;
- unvalidated output reaching an application-facing result;
- leakage of disallowed data;
- feedback unsupported by the confirmed transcript;
- failure to route material ambiguity to uncertainty or manual review.

The allowed count and severity policy are defined in the release gates; values not fixed by the MVP plan remain DECISION REQUIRED.

## Result and selection record

The benchmark report must include:

```text
dataset and split versions
provider and model snapshots
prompt and schema versions
execution dates and environment
aggregate and per-stratum metrics
confidence or uncertainty reporting
critical-failure case review
latency and cost model
data-handling review result
known limitations and validity threats
selected provider or no-selection decision
selection rationale and rejected alternatives
project-owner decision and date
specialist review evidence
```

Do not collapse materially different quality, safety, privacy, latency, and cost measures into an opaque score. Any weighting or trade-off rule must be approved before results are unblinded.

Selected provider and model snapshot: DECISION REQUIRED.

Production-provider benchmark confirmation: DEFERRED until preparation to use real participant data or start an external pilot.
