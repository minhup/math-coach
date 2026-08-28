# Static end-to-end student journey

Milestone 5 connected the authenticated profile, multi-exam, immutable content, upload,
mathematical correction, and curated geometry boundaries into one synthetic student journey.
Milestones 6 and 7 replace its mock transcription/evaluation seams with durable production-shaped
server boundaries while preserving the application-owned state machine. Automated journeys still
use deterministic synthetic providers. Learner-state aggregation and adaptive planning are absent.

## Journey and state ownership

The browser owns one explicit transient state machine with these phases:

```text
onboarding → planning → problem_work → upload → transcription → correction
           → confirmation → evaluation → hint → retry → concept → completion
```

Each phase also has an applicable `loading`, `ready`, `profile_required`, `targets_required`,
`empty`, `retryable_failure`, `permanent_failure`, or `uncertain` status. The pure transition
function returns `invalid_transition` without changing state when a caller tries to skip a required
phase, use an attempt for another profile/version, receive a transcript for another attempt, skip a
hint level, reuse an attempt ID for retry, or load a different concept version.

Confirmation leaves the correction phase and stores an immutable exact transcript version. The
editor is no longer mounted, so confirmed content cannot change implicitly. Evaluation can be
requested only from confirmation and accepts only that version UUID plus an idempotency UUID.
Post-confirmation reasoning steps never enter the correction editor. A retry
creates a distinct database attempt whose `problemVersionId` equals the first attempt's immutable
version. Completion follows concept review. The deterministic summary is derived from state fields,
not generated prose.

Profile, target, attempt, upload metadata, immutable content, M6 transcripts/confirmations, M7
evaluation runs/results/steps, and M7 hint releases are persistent. The plan and browser navigation
state remain recreatable/transient: a reload returns to onboarding and reloads the owned profile and
targets, but exact grading and hint records remain durable.

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

## Strict provider-shaped boundaries

FastAPI/Pydantic owns the transcript, confirmation, evaluation, metadata, plan, hint, and concept
schemas. Models use camel-case aliases, `extra="forbid"`, discriminated unions, bounded values, and
cross-field validation. OpenAPI and the generated TypeScript declarations are committed from those
models. The browser validates exact response keys and nested typed content again before rendering.

M6 owns image-to-flat-document transcription. M7 owns exact-confirmed-document-to-evaluation. Their
provider adapters, prompts, schemas, configurations, run tables, and deterministic fixtures remain
separate. Both retry a schema failure once and expose retryable, permanent, invalid-schema, and
uncertainty states without fabrication.

M7 labels references non-exhaustive, validates post-confirmation step/error relationships, computes
rubric totals in application code, and persists only application-facing judgments, dependencies,
and typed feedback. It never stores raw provider payloads or hidden reasoning. Details are in the
[evaluation architecture](evaluation-scoring-and-progressive-hints.md).

## Authenticated API surface

The current journey uses these authenticated endpoints:

```text
GET  /api/v1/exam-cycles
GET  /api/v1/plans/today
POST /api/v1/attempts/{attempt_id}/transcribe
GET  /api/v1/attempts/{attempt_id}/transcription
POST /api/v1/attempts/{attempt_id}/transcripts
POST /api/v1/attempts/{attempt_id}/confirm-transcript
POST /api/v1/attempts/{attempt_id}/evaluation
GET  /api/v1/attempts/{attempt_id}/evaluation
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

The journey sends only a hint idempotency UUID. The server reads the highest durable release and
selects exactly level `previous + 1`; the browser never submits a level. The API reports
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

M5 required no migration. M6 added immutable transcription records; M7 migration `20260828_0004`
adds evaluation runs, post-confirmation steps, evaluations, and hint events without changing older
rows or introducing mastery state. Downgrading M7 removes only M7 records and preserves M6.

No dependency is added. The implementation reuses the locked React/Next.js, FastAPI/Pydantic,
PostgreSQL/MinIO, KaTeX/MathLive, JSXGraph, Vitest/pytest, and Playwright stack.

Rolling back only M7 requires its Alembic downgrade before reverting the API/generated contract;
this deletes M7 evaluation and hint-event records while retaining earlier synthetic profile, target,
attempt, upload, transcript, and confirmation records. No content re-import is required.

Verification covers pure plan/state/summary determinism, strict provider schemas and one-retry behavior,
authorization and ownership, immutable retry pinning, frontend boundary rejection, every journey
state, and the complete production-build journey on all five configured Chromium/WebKit
phone/tablet projects. Exact browser evidence is in the
[Milestone 5 device report](../evaluation/m5-static-journey-device-report.md) and current
[Milestone 7 device report](../evaluation/m7-evaluation-device-report.md).

## Milestone 6 and 7 replacements

Milestone 6 removes `POST /mock-transcription` and routes the same M5 journey through the production-
shaped authenticated transcription endpoint. The deterministic fake remains the browser/test source,
but it reads the verified owned upload and persists the same model-run and transcript records as a
configured real adapter. Correction and confirmation are now durable. Milestone 7 subsequently
removes the mock evaluator and transient client-driven hints: evaluation accepts only the exact
confirmed version and idempotency key, while hints are durable and server-progressed.

The plan, `study_profile -> student_exam_targets[]`, supported-target arrays, immutable problem
version, curated hints, retry, concept review, and summary remain unchanged. See the
[multimodal transcription architecture](multimodal-transcription.md),
[evaluation architecture](evaluation-scoring-and-progressive-hints.md), and M7
[device report](../evaluation/m7-evaluation-device-report.md).
