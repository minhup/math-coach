# Milestone 5 static end-to-end student slice

## Metadata

- Status: proposed; implementation awaits project-owner seam approval
- Owner: Codex implementation; project owner approval required
- Branch: `feat/m5-static-end-to-end-student-slice`
- Base commit: `756af3719ff8b68db43c69c0edf1b73a0b96129b`
- Related milestone: Milestone 5 — Static end-to-end student slice
- Related issue/ticket: User request dated 2026-08-27
- Started: 2026-08-27
- Last updated: 2026-08-27

## Context

Milestones 1–4 are complete on `origin/main`. The repository already provides invite/session
authentication, authorized direct-to-object-storage image uploads, one active user-owned study
profile with a `studentExamTargets[]` collection, immutable versioned content and attempts, strict
typed content blocks, KaTeX rendering, visual MathLive correction over a flat transcript document,
and a deterministic curated JSXGraph renderer with finite validated actions.

The pieces are currently exposed as foundation or internal spike routes rather than one student
journey. There is no student onboarding UI, combined plan response, server-authoritative structured
mock transcript/evaluation schema, journey state machine, progressive runtime hint endpoint, concept
view, retry flow, or session summary. Milestone 5 must connect the existing boundaries with
deterministic application-owned mocks while deliberately stopping before real transcription,
production grading, learner-state aggregation, or the full planner.

## Goal

Deliver one authenticated, deterministic, responsive static journey that lets an invited internal
learner:

1. create or load one study profile;
2. add and view at least two active target-examination records;
3. receive one combined static daily plan whose items explicitly name the target records they
   support;
4. open a typed mathematics/geometry problem and create an attempt pinned to its immutable problem
   version;
5. use the existing curated geometry renderer;
6. upload a clearly synthetic image through the existing signed authorized upload flow;
7. receive a strictly validated deterministic mock transcript;
8. correct text and mathematics through the existing continuous MathLive correction editor;
9. explicitly confirm the exact transcript used by the mock evaluation boundary;
10. receive strictly validated deterministic structured mock feedback, including safe failure and
    uncertainty states;
11. request ordered typed hints and apply only existing curated geometry actions;
12. start a distinct retry attempt against the same immutable problem version;
13. open relevant typed concept content; and
14. complete the session with a summary derived only from application-owned state.

The full flow must pass the existing five-project phone/tablet matrix with touch, keyboard, and
horizontal-containment coverage.

## Non-goals

- Add a real AI provider, provider SDK, network AI call, prompt orchestration framework, or workflow
  engine.
- Implement Milestone 6 multimodal transcription or persist a real transcription pipeline.
- Implement Milestone 7 production grading, generalized mathematical judgment, calibrated scoring,
  or production hint generation.
- Implement Milestone 8 evidence events, learner-state aggregation, mastery transitions, or review
  scheduling.
- Implement Milestone 9 target balancing, adaptive selection, weekly coverage, or a generalized
  planner. The M5 plan is a narrow deterministic fixture-backed selection.
- Add predicted scores, admission probability, a leaderboard, RAG, a vector database, Markdown,
  arbitrary HTML, executable geometry, a drawing language, a native wrapper, direct pen input, or
  voice conversation.
- Add real examination, provider, student, or personal data.
- Add transcript, evaluation, hint, plan, or session persistence merely to simulate later
  milestones.
- Add a new state-management, rich-text, canvas, analytics, AI, or Markdown dependency.

## User-visible behavior

- Invite sign-in remains the only entry to the student journey. Authentication checking, retryable
  access failure, rejected invite, and sign-out remain explicit.
- Onboarding shows one profile and every active target as a collection. A profile with fewer than two
  active targets stays in the add-target state for this representative M5 journey; it never invents
  a primary target.
- The static daily plan shows a stable ordered list. One item is intentionally assigned to both
  active targets and one is intentionally assigned to the highest-priority active target, proving
  both multi-target and single-target session-item support without duplicating shared skills.
- Every plan item displays its immutable problem-version identity and the target records it is
  intended to support. The UI shows no predicted outcome.
- Opening the primary item creates an owned attempt against the exact planned problem version. Typed
  problem content renders through the existing renderer and the existing M4 interactive scene can
  be manipulated by touch, pointer, and keyboard.
- The upload phase uses the existing signed-upload component. A successful upload remains visible
  until the learner explicitly continues; a retryable transfer failure retains the selected image,
  while invalid file input is a permanent correctable failure.
- Mock transcription is visibly synthetic. Loading, retryable failure, and terminal invalid-payload
  failure are distinct. No transcript is shown after a terminal mock failure.
- Correction reuses the M3 continuous document and visual MathLive field. Raw LaTeX is never a
  learner input or failure fallback.
- Confirmation replaces the editable document with a read-only typed snapshot. Editing after
  confirmation is rejected because the correction component is no longer mounted; M5 provides no
  implicit unconfirm path.
- Mock evaluation can start only from the confirmation state and receives only the exact confirmed
  transcript. It displays typed fixture feedback, identifies stored references as non-exhaustive,
  and distinguishes ready, retryable failure, permanent failure, and uncertainty. It never presents
  the fixture as a real grade.
- Each hint request advances exactly one level. Hint content remains typed; configured geometry
  actions pass through the current curated-ID validation and renderer controls. Arbitrary action
  input is never accepted.
- Retry creates a new owned attempt ID while retaining the original problem and problem-version IDs.
- Relevant concept content renders as typed blocks and an optional existing curated scene.
- Completion shows deterministic counts and labels derived from journey state, not generated prose.
  The incomplete summary is also defined for safe early/session-interruption presentation.
- Reload re-authenticates, reloads the persistent profile/targets, and rebuilds the same static plan.
  Transient correction, confirmation, evaluation, hint, retry, and completion state intentionally
  resets to planning; existing attempts and ready uploads remain stored and are not fabricated into
  a resumed session.

## Current-state findings

- `git fetch origin main --prune` on 2026-08-27 returned
  `756af3719ff8b68db43c69c0edf1b73a0b96129b`. That is exactly the required completed Milestone 4
  commit, and `git merge-base --is-ancestor 756af3719ff8b68db43c69c0edf1b73a0b96129b
origin/main` exited successfully.
- The shared checkout was on local `main`, behind `origin/main`, and contained unrelated untracked
  work under `docs/research/`. Its contents were not inspected, formatted, staged, stashed, or
  discarded.
- A clean worktree was created at `/home/minh/dev/math-coach-m5-static-slice` from current
  `origin/main`, on the required branch `feat/m5-static-end-to-end-student-slice`. The worktree was
  clean before this ChangePlan was added.
- The only repository-local `AGENTS.md` is `apps/student-web/AGENTS.md`. Root and local instructions,
  `PLANS.md`, the complete MVP plan, the complete M4 ChangePlan, permanent M2–M4 architecture docs,
  relevant earlier ChangePlans and device/release reports, installed Next.js 16.3.2 client/error/CSS
  and test guidance, and the applicable source/tests/configuration were inspected before this plan.
- The database already has `study_profiles`, plural `student_exam_targets`, immutable versioned
  content, attempts with a restrictive non-null `problem_version_id`, and user-owned solution-upload
  metadata. It has no session-plan/transcript/evaluation/hint persistence.
- One active profile per user is enforced, while its active target collection may contain zero, one,
  or many exam-cycle records. Current authenticated profile and target CRUD APIs enforce ownership.
- Both committed synthetic problems are relevant to the two committed synthetic exam cycles. A plan
  item may intentionally support a subset of the relevant active targets, so the existing immutable
  problems can produce one single-target and one multi-target planned item without changing content
  or duplicating skills.
- The M4 `SYN-M4-GEO-001` problem is suitable as the primary static item: it is version-pinned,
  supports both synthetic cycles, exercises the interactive M4 geometry engine, and has ordered
  typed hints with validated geometry actions from level 1 onward.
- The M2 midpoint concept is relevant to the primary M4 problem's shared midpoint skill and already
  contains typed content plus a curated geometry scene. M5 can map that known synthetic concept
  version explicitly rather than introducing content search or RAG.
- Current internal content preview exposes reference solutions and rubrics and is therefore not a
  suitable student problem response. The M5 daily-plan schema must expose only student-safe problem
  statement, version, geometry, target support, and concept identity.
- The current transcript schema is frontend-local version `2.0.0`. Its flat block shape already fits
  M5, but Pydantic must become authoritative for mock structured output; the TypeScript correction
  state will consume the generated schema rather than retain an incompatible duplicate.
- `TranscriptEditor` already returns an independent exact confirmed snapshot through `onConfirm`.
  It can be reused without a new editor; the journey owns the post-confirmation lock.
- `GeometryScene` already revalidates unknown scene/action data, constructs parent-first, constrains
  interaction, and rejects actions outside curated IDs/capabilities. It needs no new action language.
- `UploadWorkspace` already performs file validation, presign, direct PUT, completion verification,
  retryable failure, and authorized success. It needs only a callback/continue seam so the journey
  can consume the ready upload ID after success remains visible.
- Existing OpenAPI generation is byte-for-byte checked. Current OpenAPI exposes 14 paths and no
  transcript, evaluation, plan, hint, concept, or exam-cycle option schema.
- Current named test inventory contains 44 backend test functions and 87 frontend/browser test
  declarations. Because of parameterization, the exact final M4 `make check` on this same commit
  passed 122 frontend tests, 67 backend unit tests, 23 integration tests, two full migration cycles,
  and 15 browser cases in 11.8 seconds.
- The root command contract is complete. `make check` runs format-check, lint, typecheck,
  API-contract drift, content validation, production build, unit tests, two migration cycles plus
  integration tests, and all five Playwright projects. `scripts/run_e2e.sh` supports isolated ports.
- Locked toolchain versions are Node 24.14.0, npm 11.9.0, Python 3.12.12, uv 0.11.30, Next.js 16.3.2,
  React 19.2.4, Pydantic 2.13.4, FastAPI 0.141.1, MathLive 0.110.0, KaTeX 0.18.4, JSXGraph 1.13.2,
  Vitest 4.1.11, and Playwright 1.62.1.
- Pre-change hashes are: `package-lock.json`
  `6dbc57fa9fb169ee41d4d0620a08bfc45646b1bebb534ba0e65cc5dfca128bde`, `uv.lock`
  `60357067a09fcfe5adbaacbb18b21c7d3e799761a38bb06260b8e5b0c7f4b442`, OpenAPI
  `351c0d380b1df68ca93ebe2efc9858b612d418cb3281d88558f5c8dd75e46b5c`, generated TypeScript
  `d6adf5e1b15a6cb254b566da34db51cc530ee3762e90e9e350d17df2aa6de5eb`, M2 package
  `cc91397357a8a29a0b97c268e8e65ae0c4b5acf2e8ac8bb7b18c0d17973c4408`, and M4 package
  `9de10a0854acb701cc60a66d1e34a8154d9d29046893ac13ce637da127e9c1d8`.

## Design

### Public seams approved before TDD

Implementation will not begin until the project owner approves these observable seams:

1. Strict Pydantic/OpenAPI models for available exam cycles, the student-safe static daily plan,
   flat transcript blocks/document, confirmed transcript, mock run metadata, structured mock
   evaluation, next hint, and typed concept content.
2. Authenticated HTTP endpoints:

   ```text
   GET  /api/v1/exam-cycles
   GET  /api/v1/plans/today
   POST /api/v1/attempts/{attempt_id}/mock-transcription
   POST /api/v1/attempts/{attempt_id}/mock-evaluation
   POST /api/v1/attempts/{attempt_id}/hints/next
   GET  /api/v1/concept-versions/{concept_version_id}
   ```

   Existing profile, target, attempt, upload, authentication, and internal-preview endpoints remain
   the persistence and authorization seams.

3. A pure Python `build_static_daily_plan(profile, active_targets, published_content)` function that
   selects the known M4 primary problem for all relevant active target records and the known M2
   follow-up problem for the highest-priority relevant active target. Ordering and IDs are derived
   from canonical input, not random output or mock prose.
4. A small deterministic mock boundary whose raw transcript/evaluation fixture payloads are treated
   as unknown, validated with `extra="forbid"`, retried once only after a schema failure, and never
   returned after provider-style failure. The boundary has no SDK, prompt, network call, or general
   grading logic.
5. A pure TypeScript `transitionStaticJourney(state, event)` discriminated-union state machine that
   returns an explicit rejected transition instead of skipping phases, plus
   `summarizeStaticJourney(state)` for known-literal incomplete and complete summaries.
6. The existing `UploadWorkspace` gains an optional ready-upload continuation callback; the existing
   `TranscriptEditor` confirmation callback, `TypedContentBlocks`, `MathRenderer`, `MathLiveEditor`,
   and `GeometryScene` remain the visual/content seams.
7. One `StaticStudentJourney` client orchestrator renders every state through accessible controls and
   generated API types. Internal M2–M4 review routes remain linked but are not canonical student flow.
8. One real-browser static journey spec runs unchanged across all five configured Playwright
   projects and measures both document and critical-element containment.

### Deterministic plan

The plan builder receives the active profile/target rows and published content rows in an explicit
order. It uses only committed stable synthetic content IDs and exact current immutable version IDs:

- primary geometry item: M4 `SYN-M4-GEO-001`, intended to support every active target whose cycle is
  present in its explicit relevance links;
- follow-up item: M2 `SYN-M2-GEO-001`, intentionally assigned only to the highest-priority relevant
  active target record;
- concept: exact current M2 `SYN-MIDPOINT-COORDINATES` concept version, a static M5 mapping to the
  shared midpoint skill.

The response includes plan ID/date/version, profile ID, ordered active target IDs, and ordered items.
Each item includes position, stable problem ID, immutable problem-version ID/version, typed statement,
optional validated scene, estimated time, exact supported target record IDs, a finite selection-reason
code, and optional relevant concept-version ID. A plan-level validator rejects empty support,
duplicate positions/IDs, target IDs outside the plan, and content/support mismatches.

The plan date is an explicit service input (the `/today` endpoint supplies the application date), so
identical profile, targets, content, date, and configuration yield byte-identical semantic output.
This is a fixed M5 composition, not the Milestone 9 planner.

### Strict deterministic mocks

Committed application fixtures cover:

- a valid flat text/math transcript with clearly synthetic block IDs and one deliberately
  correctable mathematical expression;
- an invalid transcript with an extra/invalid nested field;
- a valid structured evaluation with typed feedback, no generated score, a confirmed-transcript
  fingerprint, and `referenceSolutionsNonExhaustive: true`;
- an invalid evaluation payload;
- a valid uncertainty response; and
- retryable and permanent mock failures that contain no fabricated transcript/evaluation body.

Mock metadata uses conspicuously synthetic values such as provider
`application-owned-synthetic-mock`, model snapshot `m5-static-fixture-v1`, prompt version
`m5-no-provider-prompt-v1`, schema versions, zero token usage, zero cost, and deterministic measured
latency `0`. Hidden reasoning is absent.

The mock service validates raw fixture output into strict Pydantic models. A schema failure performs
exactly one retry, then returns stable `mock_payload_invalid` terminal failure. A configured fixture
failure returns its stable retryable/permanent error and no content. Evaluation accepts only a
`ConfirmedTranscript` wrapper. It hashes the canonical confirmed blocks and returns that fingerprint,
proving which snapshot was consumed without storing chain-of-thought or pretending to grade by exact
reference matching.

### State machine

The discriminated state union has explicit top-level phases:

```text
onboarding
planning
problem_work
upload
mock_transcription
correction
confirmation
mock_evaluation
hint
retry
concept
completion
```

Async phases carry finite loading, empty where applicable, retryable-failure, permanent-failure, and
uncertainty substates. Events include profile/target readiness, plan load, attempt creation, upload
readiness, transcript receipt, transcript confirmation, evaluation request/result, next-hint receipt,
retry-attempt creation, concept load, and completion.

Every transition checks required owned data. In particular:

- planning requires a loaded profile and the representative two-active-target condition;
- problem work requires a plan item and attempt whose problem-version IDs match;
- transcription requires an owned ready upload ID;
- correction requires a schema-valid transcript whose attempt ID matches the current attempt;
- evaluation before confirmation is rejected;
- editing events outside correction, including after confirmation, are rejected;
- hints advance only from level `n` to `n + 1` for the current immutable problem;
- retry requires a new attempt ID, the same profile ID, and the same problem-version ID;
- concept content must match the planned concept-version ID; and
- completion requires the retry state and loaded relevant concept.

Rejected transitions retain the prior state and expose a stable internal error code. The UI does not
silently jump ahead.

### Rendering and responsive composition

The authenticated root becomes the static journey. The current invite/login shell remains outside
the journey state machine. A focused client orchestrator owns transient navigation, while API and
database calls remain the application-owned resource boundaries.

Problem, hint, evaluation, concept, and summary copy are rendered from typed variants through React
and `TypedContentBlocks`; there is no Markdown/HTML renderer. KaTeX failure remains source-free.
Geometry uses the exact existing M4 renderer and static fallback. Correction uses the exact M3
continuous document/MathLive model. The journey uses a CSS Module for scoped layout and retains
root global styles only for existing shared components.

At phone widths the current phase is one column with bounded controls and a concise progress list.
Tablet portrait/landscape may use two columns where the existing photo/transcript or geometry/content
surfaces benefit. Buttons remain at least the existing touch target size; all actions are ordinary
buttons/forms with keyboard focus and no gesture-only requirement.

### Refresh boundary

M5 adds no client storage or session table. Refresh performs the following deterministic behavior:

1. re-check the HTTP-only authenticated session;
2. reload the current profile and its plural target collection;
3. request the same static plan from current persisted inputs; and
4. return to the plan state with no claim that a transient upload/transcript/evaluation session was
   restored.

Previously created attempts and ready upload metadata remain persisted through their existing APIs,
but are not automatically attached to the new transient run. This limitation is explicit and avoids
inventing M6–M10 persistence early.

## Multi-exam impact

- Study profile: reuse the existing one-active-profile-per-user contract.
- Exam targets: always load, mutate, plan, and render `studentExamTargets[]`; the representative
  journey requires at least two active records but no schema assumes exactly two or a primary exam.
- Plan support: every item carries a non-empty array of exact `student_exam_targets.id` values. One
  item supports multiple records and one supports one record.
- Content relevance: supported target IDs must correspond to explicit problem-to-exam-cycle
  relevance; the plan cannot claim an unrelated target.
- Shared skills: content continues to reference the single shared skill rows. M5 adds no exam-scoped
  learner state or duplicated skill evidence.
- Exam-specific progress: not computed or displayed.
- Planner: a fixed deterministic composition only; adaptive priority, balancing, and audit
  explanations beyond finite fixture reason codes remain Milestone 9.
- Predicted scores and admission probability remain absent.

## Files and components

Proposed and owned by this branch before implementation:

### Documentation and root configuration

- `docs/changes/2026-08-27-m5-static-end-to-end-student-slice.md` — living plan and exact evidence.
- `docs/architecture/static-student-journey.md` — durable state, mock, API, refresh, and ownership
  contract.
- `docs/architecture/versioned-content-and-multi-exam.md` — document exact per-item target-record
  support and static plan reuse.
- `docs/architecture/math-rendering-and-transcript-state.md` — promote flat transcript `2.0.0` to the
  generated Pydantic/OpenAPI contract and record confirmation locking.
- `docs/architecture/interactive-geometry-engine.md` — record reuse by student problems/hints.
- `docs/MVP_IMPLEMENTATION_PLAN.md` — record final M5 implementation without changing later
  milestone scope.
- `docs/evaluation/m5-static-student-journey-device-report.md` — exact five-project commands,
  timings, screenshot inspection, interaction, and overflow results.
- `README.md` — static journey, deterministic mock, refresh, and focused command documentation.
- `package.json` — include new/updated documentation in existing Prettier checks only; no dependency
  entry change.

### Backend and generated contracts

- `services/api/app/static_journey/__init__.py` — focused package boundary.
- `services/api/app/static_journey/schemas.py` — strict Pydantic request/response/mock schemas.
- `services/api/app/static_journey/planning.py` — pure deterministic plan composition and student-safe
  content queries.
- `services/api/app/static_journey/mocks.py` — deterministic raw fixtures, validation, one schema
  retry, failure/uncertainty behavior, and metadata.
- `services/api/app/static_journey/service.py` — authenticated attempt/upload/hint/concept ownership
  orchestration.
- `services/api/app/api.py` — add the six approved authenticated endpoints.
- `packages/api-client/openapi.json`, `packages/api-client/src/schema.d.ts` — generated authoritative
  contract updates.
- `services/api/tests/unit/test_static_journey_schemas.py` — strict transcript/evaluation fixture and
  invalid-payload tests.
- `services/api/tests/unit/test_static_journey_planning.py` — pure multi-target plan ordering,
  support, and determinism tests.
- `services/api/tests/unit/test_static_journey_mocks.py` — valid, invalid, retry-once, failed, and
  uncertain mock behavior.
- `services/api/tests/integration/test_m5_static_journey.py` — authenticated full boundary,
  isolation, immutable attempt, upload, hint, concept, and mock tests.
- Existing integration fixtures only if an explicit dependency override is needed for deterministic
  failure scenarios.

### Frontend and browser coverage

- `apps/student-web/features/journey/static-journey-state.ts` and test — pure transition contract.
- `apps/student-web/features/journey/session-summary.ts` and test — deterministic complete/incomplete
  summary derivation.
- `apps/student-web/lib/api-transport.ts` — extract the existing shared fetch/error boundary for the
  existing and new generated clients; no renaming-only wrapper.
- `apps/student-web/lib/api.ts` and test — retain auth/upload/content behavior and add profile, target,
  attempt, and exam-cycle calls where shared.
- `apps/student-web/lib/static-journey-api.ts` and test — strict runtime parsing for plan,
  transcript, evaluation, hint, and concept responses using generated types.
- `apps/student-web/components/journey/static-student-journey.tsx` and test — async orchestration,
  error states, reload boundary, and public journey behavior.
- `apps/student-web/components/journey/journey-panels.tsx` and test — accessible presentation for
  onboarding, plan, problem, confirmation/evaluation, hints, retry, concept, and summary.
- `apps/student-web/components/journey/static-student-journey.module.css` — phone/tablet scoped
  layout and containment.
- `apps/student-web/components/upload-workspace.tsx` and test — optional post-success continue seam.
- `apps/student-web/features/transcription/transcript-state.ts` and test — consume the generated
  transcript shapes while preserving existing pure operations.
- `apps/student-web/components/transcription/transcript-editor.tsx` and test only if a small labeling
  prop is required; visual editing and confirmation behavior remain intact.
- `apps/student-web/components/math-coach-app.tsx` and test — mount the static journey after invite
  authentication.
- `apps/student-web/components/interaction-shell.tsx` — remove only if it becomes dead after the M5
  root replaces the placeholder shell; internal review links remain in the journey.
- `tests/e2e/static-student-journey.spec.ts` — full journey across all five projects, including
  refresh and containment.
- Existing `tests/e2e/foundation.spec.ts`, `math-correction.spec.ts`, and `geometry.spec.ts` only for
  selector/navigation updates needed after the authenticated root changes; their behavior coverage
  will not be weakened.

No content package, content JSON Schema, SQLAlchemy model, Alembic migration, Python/JavaScript
dependency manifest entry, lockfile, object-storage contract, or geometry executable boundary is
expected to change. If implementation proves any excluded shared contract necessary, work stops and
this plan is updated for approval before that change.

## API and schema changes

All new models extend a strict M5 API base with camel-case aliases and `extra="forbid"`. Generated
TypeScript types remain derived from FastAPI. The frontend may add runtime type guards because HTTP
JSON is untrusted, but it will not redeclare incompatible canonical types.

Planned response/request families:

- `AvailableExamCycleResponse` / `AvailableExamCycleListResponse`;
- `StaticDailyPlanResponse`, `StaticPlanItem`, `StaticPlanTarget`, and finite
  `StaticSelectionReason`;
- `TranscriptTextBlock`, `TranscriptMathBlock`, `TranscriptDocument` schema `2.0.0`,
  `ConfirmedTranscript`, `MockTranscriptionRequest`, and `MockTranscriptionResponse`;
- `MockRunMetadata`, typed evaluation feedback/outcome, `MockEvaluationRequest`, and
  `MockEvaluationResponse` with an explicit non-exhaustive-reference flag and transcript
  fingerprint;
- `NextHintRequest` / `NextHintResponse` with typed content and the existing `GeometryAction` union;
- `ConceptVersionResponse` with typed content and optional existing `GeometrySceneVersion`.

Authorization rules:

- every endpoint requires `CurrentUser`;
- plan and exam-cycle reads expose only published synthetic configuration and the current user's
  target record IDs;
- attempt mock/hint endpoints use `owned_attempt`;
- transcription additionally uses `owned_upload` and requires status `ready`;
- transcript attempt ID must equal the path attempt ID;
- evaluation accepts no draft transcript field, only `confirmedTranscript`;
- concept reads are limited to published synthetic content and the exact requested immutable
  version;
- cross-user attempt/upload combinations return the existing safe not-found envelope.

Stable errors distinguish authentication, owned-resource not found, invalid transition/request,
mock schema terminal failure, retryable mock failure, permanent mock failure, exhausted hint ladder,
and unavailable/empty static plan. No failure response includes a fabricated success body.

## Database and migration

No migration is planned or justified.

Existing persistent fields already cover the M5 requirements:

- `study_profiles` and `student_exam_targets` own onboarding and plural active targets;
- immutable `problem_versions`, relevance, skills, hints, concepts, and curated scene versions own
  content;
- `attempts.problem_version_id` pins original and retry attempts;
- `solution_uploads` and object storage own authorized synthetic images without PostgreSQL bytes.

The static daily plan, correction state, confirmation wrapper, mock evaluation, hint cursor, concept
view, and summary are transient M5 application state. Persisting them now would invent later
session/transcription/evidence contracts without a demonstrated M5 need. Therefore there is no
forward migration, backfill, index, compatibility change, rollback SQL, or schema data-loss risk.

Rollback reverts application/API changes only. Existing profiles, targets, attempts, uploads, and
immutable content remain intact. Refresh behavior explicitly does not claim transient recovery.

## Security and privacy

- Existing invite sessions gate the complete journey; every user-owned profile, target, attempt, and
  upload read/write remains authorized.
- Cross-user IDs return safe not-found responses and never reveal ownership.
- Only original repository-owned synthetic exam/content identifiers, synthetic mock payloads, and
  synthetic image bytes are used.
- Image bytes remain in object storage. The database retains metadata/object keys only.
- Mock transcript/evaluation payloads are untrusted until strict Pydantic validation and frontend
  runtime validation both succeed.
- The mock boundary records only application-facing typed output and synthetic run metadata; it has
  no hidden chain-of-thought, key, provider credential, network target, or SDK.
- React renders typed content. No raw HTML, Markdown, `dangerouslySetInnerHTML`, external executable
  content, or AI-generated code is introduced.
- Math failure DOM remains source-free and correctable through MathLive.
- Geometry actions retain the existing curated object-ID and capability checks.
- No real content rights, consent, retention, research use, deletion/export, or external-pilot claim
  is introduced.

## Test plan

All implementation uses vertical red-green-refactor slices. For each slice, one public-behavior test
is added and observed failing for the intended reason, the minimum implementation makes it pass, and
focused green is restored before the next slice. Tests mock only system boundaries such as HTTP,
object storage, or the deterministic raw-fixture source; they do not mock the state machine or
components under test.

### Unit: pure journey, plan, summary, and strict mocks

1. Red/green strict transcript schemas: accept exact flat text/math fixtures; reject wrong version,
   duplicate/empty IDs, empty documents, unsupported variants, raw HTML/Markdown/code keys, extra
   nested keys, and invalid attempt IDs.
2. Red/green strict evaluation schemas: accept ready and uncertain typed feedback; reject invalid
   outcome, raw prose/Markdown/HTML dictionaries, unknown keys, missing non-exhaustive-reference
   policy, and malformed metadata.
3. Red/green mock validation: valid output is deterministic; invalid raw output is attempted exactly
   twice then fails terminally; retryable/permanent source failures return no fixture body; uncertain
   output remains a valid explicit state.
4. Red/green pure plan: zero/one/many target support is modeled as arrays; representative two-target
   fixture yields stable primary/follow-up order; primary supports both target record IDs; follow-up
   supports exactly the highest-priority relevant record; unsupported targets and duplicate/empty
   support reject; repeated identical inputs serialize identically.
5. Red/green state machine phase by phase: onboarding, planning, problem work, upload, mock
   transcription, correction, confirmation, mock evaluation, hint, retry, concept, and completion.
   Assert every invalid skip is rejected and prior state remains unchanged.
6. Specifically reject evaluation before explicit confirmation, edits after confirmation, transcript
   attempt mismatch, non-ready upload, skipped hint levels, arbitrary geometry action state, retry
   with the same attempt ID or changed problem version, wrong concept version, and premature
   completion.
7. Red/green summary: known-literal incomplete and complete summaries, identical state yields
   identical output, and summary contains no provider/generated prose or predicted outcome.

### Backend integration and API contract

- Authenticate before every M5 endpoint; reject unauthenticated access.
- Create and then load one profile; add two active target records; render/list both as a collection;
  reject cross-user target/profile access.
- List available synthetic cycles through a strict authenticated contract.
- Return a deterministic plan twice and compare exact semantic output/order.
- Assert every item has non-empty exact target record IDs; one item supports both and one supports one;
  all support is backed by explicit exam-cycle relevance; shared skill rows remain singular.
- Assert plan statement/geometry data is typed and student-safe: no reference solution/rubric/raw
  HTML/Markdown/executable fields.
- Create the primary attempt and assert exact immutable problem-version pinning.
- Presign, PUT, complete, and retrieve a clearly synthetic image; reject an unready, missing, or
  other-user upload at mock transcription.
- Return the exact deterministic validated transcript for the owned attempt/upload; inject invalid
  raw transcript and assert one retry plus terminal safe failure.
- Reject evaluation payloads without the `confirmedTranscript` wrapper and attempt mismatches.
- Prove the exact confirmed transcript fingerprint reaches evaluation. Inject ready, invalid,
  retryable-failed, permanent-failed, and uncertain mock outcomes without fabricating content.
- Assert evaluation wording/policy treats reference solutions as non-exhaustive and does not require
  exact stored-reference matching.
- Request hints from zero upward; assert exact +1 ordering, typed content, exhaustion handling, and
  existing geometry actions validated against the current scene's IDs/capabilities.
- Fetch the exact published concept version and validate typed math plus curated scene.
- Create retry attempt two; assert distinct ID, same owner/profile/problem/problem-version, and no
  content mutation.
- Reject every cross-user attempt/upload/hint/evaluation/concept combination as applicable.
- Regenerate OpenAPI and TypeScript declarations; `make api-contract-check` must be byte-clean.
- No migration/backfill test is added because no migration exists; existing two-cycle migration gate
  remains required.

### Frontend API and components

- Strictly parse valid profile/target/cycle/plan/transcript/evaluation/hint/concept responses; reject
  malformed nested unions, extra mock payload fields, raw dictionaries, and mismatched identities.
- Preserve existing login, upload, content preview, correction, math, and geometry component suites.
- Cover authenticated root checking, invite sign-in, retryable access failure, and sign-out.
- Cover onboarding loading, profile-required, targets-required, ready, retryable failure, and
  permanent failure; cover both create and load paths.
- Render two or more active target records as a collection with no singular/primary-exam copy.
- Cover plan loading, empty, ready, retryable failure, and permanent failure; assert stable ordering,
  immutable version labels, and target-support badges on every item.
- Render typed problem math source-free, live curated geometry/fallback, and create the matching
  attempt before upload.
- Reuse upload idle/selected/loading/success/failure/retry and assert the ready upload continuation
  callback receives the validated owned upload.
- Cover mock transcription loading/retryable/permanent states and reject malformed responses before
  rendering.
- Correct text by native caret, correct mathematics through MathLive, and confirm the exact visible
  typed order through the existing editor.
- Assert confirmation is read-only, evaluation cannot be called before it, and the exact snapshot is
  the request input afterward.
- Cover ready, retryable failure, permanent failure, invalid-payload failure, and uncertainty
  evaluation states; render only typed feedback and non-exhaustive reference wording.
- Request levels 1 then 2 without skipping, show the current/all-used hint order, pass configured
  actions to the existing geometry scene, and reject malformed/unknown actions.
- Assert retry creates a distinct displayed attempt while content version remains unchanged.
- Render relevant concept typed content and curated fallback without raw TeX/HTML/Markdown.
- Render exact incomplete/complete deterministic summaries.
- Parameterize every explicit journey phase and assert invalid transitions remain visibly safe.
- Assert all controls work through standard pointer/touch and keyboard activation and critical
  containers use bounded responsive styles.

### Browser/end-to-end

Run one full production-build spec unchanged across:

| Project                        | Engine          | Viewport   | Required behavior                         |
| ------------------------------ | --------------- | ---------- | ----------------------------------------- |
| `compact-chromium`             | Chromium, touch | 360 × 640  | one-column journey, bounded math/geometry |
| `pixel-7-chromium`             | Chromium, touch | 412 × 839  | one-column journey, touch controls        |
| `iphone-13-webkit`             | WebKit, touch   | 390 × 664  | one-column journey, visual MathLive       |
| `ipad-pro-11-portrait-webkit`  | WebKit, touch   | 834 × 1194 | readable split surfaces where applicable  |
| `ipad-pro-11-landscape-webkit` | WebKit, touch   | 1194 × 834 | bounded wide composition and keyboard     |

Each project will:

- sign in through the real invite/session boundary;
- create or load the profile and ensure two active target records;
- assert the deterministic plan, one/multiple target support, and immutable version IDs;
- open the primary problem, create an attempt, and interact with the real M4 board by touch/pointer;
- upload a generated clearly synthetic PNG through real PostgreSQL/MinIO authorization, including a
  forced transfer failure/retry in focused browser coverage;
- receive the deterministic mock transcript, edit text at the caret, correct math through real
  MathLive, and confirm;
- assert no evaluation request is made before confirmation, then receive typed mock evaluation;
- request progressive hints and exercise a configured real geometry action/control;
- create a retry attempt against the same version, open concept content, and complete the summary;
- exercise keyboard activation of plan, hint, retry, concept, and completion controls;
- reload at the documented boundary and require profile/targets/same plan to reload while transient
  state resets honestly;
- assert absence of raw TeX source, raw AI HTML/Markdown, scripts/iframes/inline executable handlers,
  predicted scores, and admission probability; and
- assert `documentElement.scrollWidth <= documentElement.clientWidth + 1` plus containment of headers,
  target chips, plan cards, math, board/fallback, upload, transcript, evaluation, hint, concept, and
  summary surfaces.

Existing foundation, M3 correction, and M4 geometry specs continue in all five projects after any
required navigation-selector update. The committed device report records total and per-project
timings, screenshots inspected, exact viewport/engine results, and refinements.

### Synthetic fixtures

- Existing M2 and M4 original-synthetic versioned content packages remain canonical and unchanged.
- Profile fixture: one synthetic internal user profile with two active target records for
  `SYN-AURORA-2027` and `SYN-HARBOR-2027`.
- Plan fixture: current M4 immutable problem version for both targets plus current M2 immutable problem
  version for one exact target record.
- Upload fixture: a generated tiny PNG named and described as synthetic; no personal metadata.
- Transcript fixtures: valid flat mixed blocks, invalid nested/extra-field output, correction, and
  confirmed snapshot.
- Evaluation fixtures: ready, invalid, retryable failure, permanent failure, and uncertainty, all
  with synthetic zero-cost metadata.
- Hint fixtures: existing ordered M4 hints and their existing validated highlight/show/ask-select
  actions.
- Retry fixture: two attempt records with distinct IDs and the same immutable problem-version ID.
- Concept fixture: existing M2 midpoint concept version with typed rich-line/display-math content and
  curated scene.
- Summary fixtures: exact incomplete and complete application-owned values.

No fixture contains a real exam, student, provider, upload, score prediction, or personal data.

### Acceptance criteria

- The complete invite-to-summary journey succeeds in every configured project.
- One user-owned profile creates/loads and renders at least two active target records as an array.
- The same inputs produce the same ordered plan and semantic plan ID; every item has explicit exact
  target-record support, with representative one-target and multi-target items.
- Attempts, including retry, remain pinned to the same immutable problem version.
- Typed math, visual MathLive correction, curated geometry interaction/fallback, authorized upload,
  confirmed transcript, typed mock evaluation, ordered hints, typed concept content, and deterministic
  summary all operate through existing or generated typed boundaries.
- Evaluation before confirmation and every other invalid state skip is rejected.
- Editing after confirmation is unavailable/rejected; no implicit stale confirmation exists.
- Mock payload schema failure retries no more than once and invalid/failed/uncertain states fail
  safely without fabricated output.
- Reference solutions remain explicitly non-exhaustive; no exact reference matching is encoded as
  correctness.
- No raw AI HTML/Markdown, raw TeX learner input/leakage, executable geometry, unvalidated dictionary,
  generalized AI/grading/planning, per-exam duplicate skill state, predicted outcome, or real data is
  introduced.
- Authentication and ownership isolation pass for all user-owned resources and M5 endpoints.
- Loading, empty, retryable failure, permanent failure, and uncertainty are explicit where
  applicable.
- Touch and keyboard paths pass with no document-level horizontal overflow at 360×640, 412×839,
  390×664, 834×1194, and 1194×834.
- Focused commands, regenerated contract checks, final `make check`, `git diff --check`, complete diff
  review, rebase, affected reruns, final documentation, and the AGENTS handoff are complete.

## Manual QA

1. Start isolated branch services with documented M5 ports and seed the unchanged synthetic content.
2. Open the production build at 360 × 640 and sign in with the development invite.
3. Create the synthetic profile if absent; add Aurora and Harbor target cycles; confirm both appear as
   equal collection members.
4. Inspect the plan order, version labels, support badges, and absence of predicted outcomes.
5. Open the primary item, verify its attempt/version, drag/select the curated scene, and inspect its
   static fallback.
6. Select the clearly synthetic PNG, force/cancel one retryable transfer where practical, upload,
   wait for verified success, then continue.
7. Confirm the mock transcript is labeled synthetic. Correct text with a native caret and mathematics
   visually with MathLive; confirm the read-only exact document.
8. Verify no evaluation action existed before confirmation. Request the deterministic evaluation and
   inspect typed feedback/non-exhaustive wording.
9. Request at least two hints in sequence, apply a configured geometry action, and confirm no level can
   be skipped.
10. Retry; compare the new attempt ID and unchanged problem-version ID. Open the relevant concept and
    complete the summary.
11. Reload during a second run and confirm profile/targets/plan recover while transient work resets to
    planning with honest copy.
12. Repeat visual/touch/keyboard/overflow inspection for Pixel 7 Chromium, iPhone 13 WebKit, and iPad
    Pro 11 portrait/landscape. Inspect full-page screenshots at original detail.
13. Exercise invalid mock response, retryable failure, permanent failure, and uncertainty through the
    deterministic test injection seam; confirm no success content is fabricated.

Expected outcome: the full student slice is coherent and responsive, but every transcription and
evaluation is unmistakably a deterministic synthetic M5 fixture rather than a real AI result.

## Rollout and rollback

This is an internal synthetic-only milestone. Merge order is M1 → M2 → M3 → M4 → M5. No production
feature flag, real content, provider key, or external pilot rollout is involved.

Before handoff, fetch current `origin/main`, rebase, document conflicts, and rerun every affected
check. Do not merge or push without explicit project-owner instruction.

Rollback reverts the M5 application/API/generated-contract/docs commits. There is no database
downgrade or content re-import. Existing profile/target/attempt/upload rows created during internal
testing may remain harmless synthetic records or be removed only through an explicitly authorized
test-environment cleanup; this branch will not issue destructive cleanup commands.

## Branch and commit plan

1. `docs: add Milestone 5 change plan`
2. `feat: add strict static journey contracts`
3. `feat: add deterministic multi-target plan`
4. `feat: add validated mock transcript and evaluation`
5. `feat: add static student journey state machine`
6. `feat: connect the authenticated student journey`
7. `test: cover static journey across device projects`
8. `docs: describe static student journey`
9. `docs: record Milestone 5 verification`

Each behavior commit includes the directly driving test(s) and leaves focused green where practical.
Generated OpenAPI artifacts are committed with the Pydantic contract change. No local squash is
planned.

## Conflict coordination

This branch owns only the proposed files listed above. Shared contracts requiring deliberate
coordination are `services/api/app/api.py`, generated OpenAPI files, `apps/student-web/lib/api.ts`,
`MathCoachApp`, `UploadWorkspace`, transcript state/editor if needed, root `package.json`, README,
MVP/architecture docs, global navigation selectors, and E2E configuration/specs.

No other active remote feature branch was visible after fetch. The original shared checkout and its
untracked `docs/research/` corpus/data work remain out of scope and untouched. This worktree will
stage only explicit owned files. If another branch changes an M5 public contract, behavior-changing
conflict resolution stops for plan update and project-owner coordination; neither side is chosen
blindly.

## Risks

- The full journey can turn into one oversized component. Mitigation: keep one pure state machine,
  one orchestration component, and focused stateless panels; put transport, rendering, and domain
  validation behind existing deep seams.
- A static plan could accidentally become a hidden singular-target planner. Mitigation: accept and
  return arrays everywhere, validate exact target-record support, and test one/many support plus two
  representative active targets.
- Embedding problem content in the plan could expose reference solutions/rubrics. Mitigation: define
  a student-safe response schema and negative integration/DOM assertions.
- Frontend/local transcript types could drift from Pydantic. Mitigation: generate TypeScript from the
  new authoritative schema and keep runtime guards at the HTTP boundary.
- A caller could try to invoke mock evaluation without using the UI. Mitigation: the API accepts only
  the strict `ConfirmedTranscript` wrapper; the application state machine is the M5 transition owner
  and rejects pre-confirmation invocation. Durable server-side confirmation persistence remains a
  later milestone, not silently simulated.
- Mock output could be mistaken for real judgment. Mitigation: synthetic labels/metadata, no score,
  no exact-reference correctness algorithm, and explicit non-exhaustive-reference wording.
- Concurrent five-project browsers share the development invite/profile. Mitigation: make the UI
  robust to create conflicts by refetching the one active profile/targets, and keep transient journey
  state browser-local. API tests separately prove creation and isolation.
- Reusing the upload component may hide success before the next phase. Mitigation: add an explicit
  optional continue callback rendered only after verified success.
- Existing M4 geometry controls may overflow inside the denser journey. Mitigation: scoped
  min-width/overflow containment, element audits, and real Chromium/WebKit screenshots.
- Reload may appear to lose work. Mitigation: define/test explicit transient reset copy and do not
  fabricate restoration without a persisted session contract.
- API parser growth could duplicate transport/error logic. Mitigation: extract one substantive shared
  transport seam used by both existing and M5 clients; keep domain parsers focused.
- Root validation is broad and browser-heavy. Mitigation: run focused red/green tests throughout,
  then production E2E on isolated ports and final post-rebase `make check`.

## Progress

- [x] Repository inspected
- [x] Plan reviewed
- [x] Branch created from current main
- [ ] Public seams approved by project owner
- [ ] Tests written or updated
- [ ] Implementation complete
- [ ] Documentation updated
- [ ] Relevant checks pass
- [ ] Diff reviewed
- [ ] Branch rebased on current main
- [ ] Conflict resolution re-tested
- [ ] Handoff summary written

## Decisions

- 2026-08-27: Use a separate clean worktree because the shared checkout contains unrelated untracked
  corpus/data work. Do not inspect or modify that work.
- 2026-08-27: Add no database migration. Existing persistent profile/target, immutable attempt,
  upload, and content records cover the M5 static journey; transient session state resets honestly on
  reload.
- 2026-08-27: Add no dependency. Existing React/Next.js, FastAPI/Pydantic, MathLive/KaTeX, JSXGraph,
  PostgreSQL/MinIO, Vitest/pytest, and Playwright boundaries cover the change.
- 2026-08-27: Reuse unchanged M2/M4 versioned synthetic content. Assign the M4 plan item to all
  relevant active target records and the M2 follow-up to one target record, proving plan support
  cardinality without mutating immutable content.
- 2026-08-27: Use the existing M4 primary problem for live geometry and map the existing M2 midpoint
  concept explicitly as the relevant static concept. Do not add search or inference.
- 2026-08-27: Promote the M3 flat transcript shape to strict Pydantic/OpenAPI ownership while
  retaining the current editor behavior and schema version `2.0.0`.
- 2026-08-27: Lock correction after confirmation by leaving the correction state. M5 offers no
  implicit return-to-correction transition; a new correction would require a deliberately specified
  transition in a later plan.
- 2026-08-27: Treat the mock boundary's raw fixture output as untrusted, validate it strictly, retry a
  schema failure exactly once, and return no fabricated body after any failure.
- 2026-08-27: Do not expose a request-controlled mock-outcome switch in the product API. Unit and
  integration dependency injection exercise invalid/failure/uncertainty fixtures; the ordinary static
  journey uses the deterministic ready fixture.
- 2026-08-27: Derive summary values from application state and use finite reason/status codes; no
  generated narrative becomes canonical.

## Discoveries

- The current M4 problem's first hint already contains a validated multi-object highlight action,
  and its second contains `show` plus `ask_select`; M5 can exercise progressive geometry-assisted
  hints without changing content.
- Existing M2/M4 problems are both relevant to both synthetic cycles. Session-item target intent is a
  subset of content relevance, so representative one-target and multi-target planned items do not
  require a new immutable content version.
- The current content preview response includes non-exhaustive solutions and rubrics; reusing it
  directly for a learner problem would leak answer material. A separate student-safe plan item is
  required.
- The M3 editor already supplies the exact independent confirmed snapshot needed for the evaluation
  boundary, but its type currently has no server/OpenAPI authority.
- Existing attempt creation permits retained immutable versions, which is exactly the retry contract;
  no attempt table change is required.
- The current upload is not linked persistently to an attempt. M5 can validate both owned resources
  at the mock-transcription request without inventing a durable attempt-asset/transcript model.
- All five Playwright projects run every spec, so one added full-journey spec produces five new browser
  cases while retaining M1/M3/M4 regression cases.

## Verification evidence

- Pre-change fetch and ancestry evidence is recorded in **Current-state findings**. Branch/worktree
  status after plan creation will be recorded before implementation.
- Required source, docs, tests, manifests, generated-contract workflow, validation commands, test
  inventory, device matrix, dependency versions, and pre-change hashes were inspected before this
  file was created.
- No baseline command has been claimed as newly executed in this worktree before approval. The exact
  completed M4 `make check` evidence applies to the identical base commit and is recorded above. A
  fresh focused/root baseline will be run after seam approval and before the first red implementation
  slice, with exact results appended here.
- Red/green commands, regenerated hashes, migration-cycle results, final package hashes, unit/
  integration/browser counts, device timings, screenshots, complete diff review, rebase/conflicts,
  `git diff --check`, and final outcome remain pending implementation.

## Result

Pending public-seam approval and implementation. No implementation test or product-code change has
been made.
