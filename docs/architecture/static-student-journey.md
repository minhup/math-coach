# Static end-to-end student journey

Milestone 5 connects the existing authenticated profile, multi-exam, immutable content, upload,
mathematical correction, and curated geometry boundaries into one synthetic student journey. The
transcription and evaluation are deterministic application-owned fixtures. No provider, production
grading pipeline, learner-state aggregation, or general planner is present.

## Journey and state ownership

The browser owns one explicit transient state machine with these phases:

```text
onboarding → planning → problem_work → upload → mock_transcription → correction
           → confirmation → mock_evaluation → hint → retry → concept → completion
```

Each phase also has an applicable `loading`, `ready`, `profile_required`, `targets_required`,
`empty`, `retryable_failure`, `permanent_failure`, or `uncertain` status. The pure transition
function returns `invalid_transition` without changing state when a caller tries to skip a required
phase, use an attempt for another profile/version, receive a transcript for another attempt, skip a
hint level, reuse an attempt ID for retry, or load a different concept version.

Confirmation leaves the correction phase and stores an independent validated snapshot. The editor
is no longer mounted, so confirmed content cannot change implicitly. Evaluation can be requested
only from the confirmation phase and the API accepts only a `ConfirmedTranscript` wrapper. A retry
creates a distinct database attempt whose `problemVersionId` equals the first attempt's immutable
version. Completion follows concept review. The deterministic summary is derived from state fields,
not generated prose.

Profile, target, attempt, upload metadata, and immutable content remain persistent through their
existing tables. The plan can be recreated from those records. Transcript, evaluation, hints, and
session progress are intentionally transient in M5: a reload returns to onboarding, reloads the
owned profile and targets, and recreates the same plan. The UI says that temporary practice progress
was reset; it does not pretend to restore an unpersisted session.

## Multi-target plan

`GET /api/v1/plans/today` loads the current user's one active study profile and its ordered
`student_exam_targets[]`. The representative M5 journey requires at least two active synthetic
targets and otherwise returns the stable `two_active_targets_required` conflict.

The planner is a narrow pure composition over the existing M2 and M4 fixtures:

- `SYN-M4-GEO-001` is the shared-target foundation item and supports every active target whose exact
  exam-cycle record is listed by that immutable problem version;
- `SYN-M2-GEO-001` is a priority-target follow-up and supports the first relevant target by priority;
- targets are sorted by priority rank and stable ID, and items have contiguous explicit positions;
- every item contains `supportedTargetIds`, and all IDs must be target records in the returned plan;
- the semantic plan ID is UUIDv5 over the date, profile, ordered target IDs, and ordered immutable
  problem-version IDs.

Identical stored records and date therefore produce byte-equivalent ordered plan semantics and the
same plan ID. The student-safe problem payload contains typed statement blocks, the exact immutable
problem version, and an optional validated curated scene. It deliberately omits reference solutions
and rubrics. Shared skills remain the existing shared rows and are not copied per examination. This
is not the adaptive Milestone 9 planner and does not predict scores or admission outcomes.

## Strict synthetic mock boundary

FastAPI/Pydantic owns the transcript, confirmation, evaluation, metadata, plan, hint, and concept
schemas. Models use camel-case aliases, `extra="forbid"`, discriminated unions, bounded values, and
cross-field validation. OpenAPI and the generated TypeScript declarations are committed from those
models. The browser validates exact response keys and nested typed content again before rendering.

The application-owned mock source produces fixed synthetic payloads. Its adapter treats those
payloads as untrusted and validates the complete object through Pydantic. A schema failure is retried
exactly once; another invalid payload becomes `mock_payload_invalid`. Source failures retain an
explicit retryable or permanent state and never receive a fabricated transcript or evaluation.
Tests inject ready, invalid, retryable, permanent, and uncertain fixture sources without exposing a
product endpoint that lets a client select an outcome.

Synthetic run metadata records:

```text
provider: application-owned-synthetic-mock
model snapshot: m5-static-fixture-v1
prompt version: m5-no-provider-prompt-v1
schema version: 1.0.0
latency/tokens/cost: zero
```

Evaluation hashes the canonical, explicitly confirmed transcript with SHA-256. The strict response
must return that fingerprint and `referenceSolutionsNonExhaustive: true`. Feedback and next steps are
typed `ContentBlock[]`; no reference-string matcher defines correctness. An uncertain payload is a
visible uncertainty state, not a successful grade. No hidden reasoning, provider call, AI SDK,
prompt orchestration, Markdown, HTML, or arbitrary dictionary reaches the UI.

## Authenticated API surface

M5 adds these authenticated endpoints:

```text
GET  /api/v1/exam-cycles
GET  /api/v1/plans/today
POST /api/v1/attempts/{attempt_id}/mock-transcription
POST /api/v1/attempts/{attempt_id}/mock-evaluation
POST /api/v1/attempts/{attempt_id}/hints/next
GET  /api/v1/concept-versions/{concept_version_id}
```

Profile and target creation, attempt creation, and upload presign/transfer/verification reuse their
existing routes. Every M5 endpoint requires an invite session. Transcription verifies that both the
attempt and ready upload belong to the session user. Evaluation and hints verify attempt ownership.
The transcript attempt ID must equal the route attempt ID. Concept access remains authenticated and
is limited to existing synthetic immutable content. Cross-user attempts/uploads fail through the
same safe not-found behavior as missing resources.

The upload continues to send bytes directly to MinIO-compatible object storage through a short-lived
signed URL. PostgreSQL contains only upload metadata. M5 accepts only the existing validated
synthetic image flow and adds no image/transcript link or image-byte column.

## Typed rendering and interaction reuse

Problem, feedback, hint, and concept content use the existing exhaustive `ContentBlock` renderer.
KaTeX remains the bounded read-only math boundary and shows its source-free correctable placeholder
on failure. The correction phase reuses the Milestone 3 continuous transcript document and MathLive
formula field, so learners correct mathematics visually instead of editing raw TeX.

The problem and hint phases reuse the Milestone 4 `GeometryScene` component. A scene is validated
before JSXGraph loads. Hint actions come only from the stored immutable hint ladder, are revalidated
against existing curated object IDs, and are passed to the same finite interaction reducer. M5
cannot add scene objects or executable drawing instructions. The repository-owned accessibility
description and static fallback remain available.

The journey requests hint level `previous + 1`; the API returns no arbitrary level and reports
`hint_ladder_exhausted` after the curated ladder. The representative flow uses the first two existing
M4 hints, including their reviewed highlight, show, and ask-select actions.

## Responsive behavior and failure states

The full journey is the authenticated workspace's primary surface. Cards and controls form one
column on phone widths and use available tablet space without requiring a desktop interaction. Touch
targets, keyboard buttons, bounded math, the geometry board/fallback, transcript document, target
chips, and summary remain inside the viewport. The upload surface offers an explicit continuation
only after the existing verification response marks the object ready.

Loading, missing profile, insufficient targets, empty plan, retryable failure, permanent failure,
and evaluation uncertainty have separate copy and controls. Only retryable failures expose a retry
action. The application never advances its state machine when the API call or transition fails.

## Persistence, dependencies, and rollback

No migration is required. Existing profile, target, immutable content-version, attempt, upload, and
content-hint fields represent every persistent M5 record. Persisting transcript/evaluation/session
fields would prematurely introduce Milestones 6–8 contracts, so M5 documents the transient reload
boundary instead.

No dependency is added. The implementation reuses the locked React/Next.js, FastAPI/Pydantic,
PostgreSQL/MinIO, KaTeX/MathLive, JSXGraph, Vitest/pytest, and Playwright stack.

Rollback reverts the M5 API, generated contracts, state machine, UI, tests, and documentation. It
requires no database downgrade, backfill, provider cleanup, or content re-import. Existing synthetic
profile, target, attempt, and upload metadata may remain as valid pre-release records.

Verification covers pure plan/state/summary determinism, strict mock schemas and one-retry behavior,
authorization and ownership, immutable retry pinning, frontend boundary rejection, every journey
state, and the complete production-build journey on all five configured Chromium/WebKit
phone/tablet projects. Exact browser evidence is in the
[Milestone 5 device report](../evaluation/m5-static-journey-device-report.md).
