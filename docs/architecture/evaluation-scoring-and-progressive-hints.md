# Evaluation, scoring, and progressive hints

Milestone 7 adds post-confirmation reasoning analysis, rubric scoring, explicit uncertainty, and
durable progressive hints. It does not change the M6 correction editor: the confirmed flat
`TranscriptDocument` remains the only grading input, and reasoning steps do not exist until a valid
evaluation result is persisted.

## Ownership and workflow

The application owns the workflow:

```text
owned verified image
  -> M6 flat transcription
  -> learner visual correction
  -> exact immutable confirmation
  -> M7 evaluation run
  -> typed result or scoreless uncertainty
  -> one server-selected curated hint at a time
```

`POST /api/v1/attempts/{attempt_id}/evaluation` accepts only an exact confirmed transcript version
UUID and an idempotency UUID. The service reloads the owned attempt, confirmation, immutable
transcript document, and canonical hash. A draft, an earlier version, a transcript from another
attempt, or another learner's attempt is rejected before the provider boundary.

The provider never owns learner state, score totals, hint level, target progress, or daily planning.
M7 creates no mastery evidence; that remains Milestone 8. Evaluation records belong to an attempt
and immutable problem version, not to a singular examination target, so the existing
`study_profile -> student_exam_targets[]` model is unchanged.

## Provider boundary

`StrictEvaluationProvider` is deliberately separate from `StrictTranscriptionProvider`. Its only
operation accepts application-owned structured context containing:

- the exact confirmed flat transcript;
- the exact immutable typed problem statement;
- all expert-verified reference examples, explicitly labeled non-exhaustive;
- every ordered immutable rubric item, code, skill ID, and maximum.

The prompt requires mathematically valid alternative methods to be accepted and forbids
reference-string comparison. It asks only for application-facing steps, judgments, dependency
relationships, rubric awards, concise feedback, and a next action. It does not request or store
hidden chain-of-thought.

The strict provider union is:

- `ready`: ordered reasoning steps, exact rubric awards, overall feedback, and next action;
- `uncertain`: a concise reason plus `manual_review`, with no steps, rubric, or score.

Unknown fields, unknown enums, missing confirmed-block coverage, duplicate block assignments,
unknown rubric codes, excessive awards, unsafe markup/HTML/URLs, forward dependencies, cycles, and
dependent errors that do not trace to a root all fail validation. One invalid payload receives one
schema-repair call. A second invalid payload terminates as `invalid_schema`; no evaluation, score,
steps, or hints are fabricated.

Automated/local work uses `application-owned-deterministic-fake` with exact model snapshot
`m7-evaluation-fixture-v1` and zero tokens/cost. The optional real adapter is server-only Gemini and
accepts only the repository-approved exact `gemini-3.5-flash-lite` or `gemini-3.5-flash` model IDs.
Provider keys never cross the API boundary. M7 made no paid provider call.

## Reasoning steps, dependencies, and scoring

Reasoning steps are derived only after confirmation. Each persisted step has:

- an application-generated UUID and contiguous position;
- one or more existing confirmed transcript block IDs, with every block assigned exactly once;
- typed `ContentBlock[]` summary and feedback created from validated plain provider prose;
- `correct`, `incorrect`, `uncertain`, or `not_assessable` judgment;
- `none`, `root`, or `dependent` error kind;
- application UUID dependencies that point only to earlier steps.

Every incorrect step is root or dependent. Roots have no dependency. Every dependent error reaches
an earlier root. Other judgments have no error relationship. The response therefore exposes useful
error structure without exposing hidden reasoning.

The provider supplies awards by immutable rubric code, never a final total. The application checks
every code exactly once, bounds each award by the stored maximum, maps it to the immutable rubric
item, and sums exact `Decimal` values. The stored/returned maximum is the immutable problem maximum
and must equal the rubric maxima. An uncertain outcome has no score or breakdown.

## Persistence and concurrency

Migration `20260828_0004` adds:

- `evaluation_runs`: provider/model/prompt/schema/pricing identity, exact confirmed version,
  idempotency/fingerprint, terminal state, schema attempts/retry count, latency, tokens, cost, and
  safe error code;
- `attempt_steps`: immutable post-confirmation steps and dependency UUIDs;
- `evaluations`: immutable ready or uncertain result, application score/breakdown, typed feedback,
  or typed uncertainty reason;
- `hint_events`: immutable attempt/evaluation/hint/level/idempotency release records.

An attempt row lock and partial unique processing index serialize run creation without holding a
database lock across a provider call. Repeating an idempotency key returns the same terminal result;
a conflicting use is rejected. A completed semantic fingerprint is reused without another call.
Concurrent requests receive `evaluation_in_progress`. Retryable provider failures may be retried
with a new key; permanent, invalid-schema, ready, and uncertain outcomes are terminal for the same
fingerprint.

Completed runs and all result/event tables are protected by database triggers. There is no backfill:
pre-M7 attempts and confirmed transcripts remain valid and have no evaluation until requested. The
downgrade drops only M7 records and preserves M6 confirmations and all earlier data.

## Progressive hints and geometry

`POST /api/v1/attempts/{attempt_id}/hints/next` accepts only an idempotency UUID. The browser cannot
submit a level. After an owned terminal evaluation, the server locks the attempt, reads the highest
released event, and selects only the next immutable `ProblemHint`. Repeating the same key returns
the same event. Levels are unique per attempt; after level 5, `hint_ladder_exhausted` creates no row.

Before persistence, hint content and finite geometry actions are parsed again. Every action must
refer to objects and animations in the attempt's exact curated scene. Animation targets must be
point-like. Ask-select allowlists contain only selectable objects and correct IDs must be inside the
allowed finite set. Problems without a scene cannot release geometry actions. The browser validates
the exact action keys again and passes them to the existing curated geometry reducer. M7 never
executes provider code or creates geometry objects at runtime.

## API and UI states

The authenticated surface is:

```text
POST /api/v1/attempts/{attempt_id}/evaluation
GET  /api/v1/attempts/{attempt_id}/evaluation
POST /api/v1/attempts/{attempt_id}/hints/next
```

The GET state union is `not_started`, `processing`, `ready`, `uncertain`, `retryable_failure`,
`permanent_failure`, or `invalid_schema`. The frontend strictly validates response keys and nested
typed content before rendering. Ready UI shows score/max, ordered steps, root/dependent labels,
rubric breakdown, feedback, and next action. Uncertainty explicitly states that no correctness claim
or score was fabricated. Only retryable failures expose retry controls.

## Privacy, testing, and limitations

Evaluation context is limited to immutable problem content and the confirmed transcript. No image,
profile name, target list, invite, key, hidden reasoning, or real learner data is included in the
M7 gold/e2e fixtures. Operational metadata and safe application-facing results are stored; provider
raw responses are not.

The committed gold corpus measures six deterministic synthetic behaviors with no release threshold.
It proves contract/regression behavior, not production grading quality. Production calibration,
real/minor data use, learner mastery updates, adaptive planning, RAG, vector storage, chat, and
automatic content publication remain outside M7.
