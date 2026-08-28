# Milestone 7 evaluation, scoring, and progressive hints

## Metadata

- Status: in-progress
- Owner: project owner and Codex
- Branch: `feat/m7-evaluation-scoring-hints`
- Base commit: `e3e6d13f9913d94b851c8f5b149eaf8482b65173`
- Related milestone: Milestone 7 — Evaluation, scoring, and progressive hints
- Related issue/ticket: None supplied
- Started: 2026-08-28
- Last updated: 2026-08-28

## Context

Current `origin/main` is exactly the completed Milestone 6 commit
`e3e6d13f9913d94b851c8f5b149eaf8482b65173`. M6 persists one flat, ordered, correctable
text/math transcript, an immutable learner confirmation, and transcription run metadata. The exact
confirmed transcript version and SHA-256 are authoritative downstream input.

The downstream path is still the Milestone 5 deterministic mock. It returns two top-level typed
content arrays but has no post-confirmation reasoning-step identification, rubric breakdown,
root/dependent error relationships, production-shaped evaluation-provider boundary, durable
evaluation run/result, or durable server-owned hint progression. The existing hint endpoint accepts
`previousHintLevel` from the browser and does not persist release events.

Milestone 7 replaces only those mock evaluation and transient hint seams. It must not introduce
reasoning steps into M6 transcription or correction, repair a learner's mathematical mistake,
update learner state, or choose plans.

## Goal

An authenticated learner can confirm the exact M6 flat transcript and request an idempotent,
server-owned evaluation. Only after confirmation, a separate strict evaluation adapter identifies
application-facing reasoning steps, classifies correct/incorrect/uncertain/not-assessable work,
records root and dependent error relationships, awards every stored rubric item, and returns a
server-calculated score plus concise typed feedback. A valid overall uncertainty produces no score
or fabricated steps. The learner can then release the immutable curated hint ladder exactly one
level per request; every release is durable and geometry actions are revalidated against existing
curated object IDs before persistence or rendering.

All automated and gold evaluation uses a deterministic production-shaped fake and original
synthetic fixtures. A separately configured Gemini adapter may use only the exact model snapshots
already approved by M6, but this change will make no paid provider call.

## Non-goals

- Reasoning-step cards, groups, IDs, or rubric data in the OCR/transcription correction editor.
- Changing the M6 flat transcript schema, authoritative confirmation hash, or correction behavior.
- Learner evidence, mastery, mistake events, review scheduling, or state recomputation from M8.
- Adaptive planning, target prioritization, or daily-plan changes from M9.
- Runtime hint generation, full-solution generation, general chat, RAG, vectors, or a generic AI
  client.
- Raw Markdown/HTML/URLs, executable geometry, provider reasoning, hidden chain-of-thought, or AI
  content publication.
- Real learner/minor data, a paid benchmark, provider-production approval, or numeric release gates.
- Production grading-quality claims.

## User-visible behavior

- The M6 correction editor remains one continuous flat document. No reasoning steps appear until
  after exact confirmation.
- The confirmation screen offers **Evaluate confirmed transcript** and describes the locked version
  as the sole evaluation input.
- Evaluation has distinct loading, retryable failure, permanent failure, invalid-schema, explicit
  uncertainty, and ready result states. Failure and uncertainty never show a fabricated score.
- A ready result shows the rubric score/max, ordered post-confirmation steps, per-step judgment,
  concise typed feedback, root/dependent error labels and dependency links, rubric breakdown, next
  action, and validated provider/model/schema metadata.
- An uncertain result explains the safe uncertainty route through typed content, contains no score
  or steps, and recommends manual review or a curated hint without criticizing the learner.
- Reference solutions are visibly described as non-exhaustive and valid alternative methods are
  accepted in the committed regression corpus.
- The hint button releases only the next level. The UI cannot choose or skip a level. Released hints
  remain ordered, final disclosure is explicit, and an exhausted ladder has no further action.
- Geometry-assisted hints expose only the existing finite controls for already-curated scene IDs.
  Invalid stored or network actions produce a safe terminal error and are never applied.
- Retry continues to create a new attempt pinned to the same immutable problem version. M8 learner
  state remains absent.

## Current-state findings

- `git fetch origin main` resolved `origin/main` to
  `e3e6d13f9913d94b851c8f5b149eaf8482b65173`; the required M6 commit is the remote tip and is an
  ancestor of it.
- Work is isolated in `/home/minh/dev/math-coach-m7-evaluation`, created from that exact remote tip.
  The original checkout and its unrelated untracked corpus/data work were not opened, formatted,
  staged, stashed, overwritten, or discarded.
- The only nested instructions are `apps/student-web/AGENTS.md`. The bundled Next 16.3.2 client
  boundary, server/client component, fetching, expected-error, and CSS guidance was inspected; the
  journey remains an interactive client component with explicit event-handler error state.
- Root commands exist. `make check` covers formatting, lint, TypeScript/Python type checking,
  generated OpenAPI comparison, content validation, production build, unit, migration/integration,
  and five-project Playwright checks.
- FastAPI/Pydantic is authoritative. OpenAPI and `schema.d.ts` are generated and byte-compared by
  `scripts/check_api_contract.sh`; browser modules additionally perform exact-key nested runtime
  validation.
- The inspected baseline contains 186 discovered Python/TypeScript/Playwright test declarations.
- `study_profile -> student_exam_targets[]` is present. Plan items carry arrays of exact target
  record IDs. Evaluation is attempt/problem-version scoped and needs no exam-target foreign key.
- Attempts are authorized through their study profile and remain pinned to immutable
  `problem_versions`. Reference solutions, rubric items, hints, geometry scene versions, and skill
  links are immutable version-owned records.
- M6 `TranscriptDocument` schema `3.0.0` is a strict flat text/math union. The only authoritative
  grading input is `transcript_confirmations -> transcript_versions`, checked by attempt, version,
  canonical hash, and owner.
- `prompt_versions` is operation-scoped and immutable, so M7 can add a distinct evaluation prompt
  identity without changing the transcription adapter. `ai_model_runs` is tied to image assets and
  remains transcription-only; M7 needs a separate run table.
- M5 `POST /mock-evaluation` accepts only the confirmed transcript version ID but returns transient
  fixture feedback. Its mock boundary retries invalid fixture data once and contains no durable
  evaluation result.
- M5 `POST /hints/next` accepts client-owned `previousHintLevel`, reads stored hint JSON, and does not
  record releases. Imported package validation checks geometry action IDs, but the hint service does
  not revalidate stored JSON against the exact scene on every read.
- The representative M4 problem has a 4-point rubric: midpoint (2) and squared distance (2), one
  non-exhaustive coordinate reference, two shared skills, and five curated hints. The scene includes
  reviewed highlight/show/focus/animate/hide/ask-select actions against existing IDs.
- Typed `ContentBlock` rendering and bounded KaTeX, MathLive correction, and curated geometry
  validation/action reducers already exist. No dependency is needed for M7.
- The five configured Playwright projects are compact Chromium 360×640, Pixel 7 Chromium, iPhone 13
  WebKit, iPad Pro 11 portrait WebKit, and iPad Pro 11 landscape WebKit.

## Design

### Workflow and authoritative input

The application flow is:

```text
owned upload
  -> M6 flat transcription
  -> learner correction
  -> immutable exact confirmation
  -> M7 evaluation run
  -> post-confirmation attempt steps + rubric result
  -> one durable curated hint release per request
```

`POST /evaluation` accepts only the exact confirmed transcript version ID plus an idempotency UUID.
The server reloads the immutable confirmation and document, verifies all three stored/canonical
hashes, and loads the exact attempt problem version. The browser never sends reasoning steps,
reference solutions, rubric awards, provider/model/prompt/schema selection, score, or hint level.

### Evaluation schemas

Provider input is an immutable application-owned value containing the stored typed problem
statement, exact confirmed flat transcript, all expert-verified non-exhaustive reference examples,
and ordered rubric items with codes, maxima, descriptions, method labels, and linked skills.

Provider output is a strict discriminated union with `extra="forbid"`:

- `ready`: ordered `reasoningSteps`, one award for every rubric code, concise overall feedback, and
  a finite next action;
- `uncertain`: one finite uncertainty reason and `manual_review`, with no steps, rubric awards, or
  score.

Each provider reasoning step contains an application-neutral step key, one or more existing
confirmed transcript block IDs, a concise plain-text summary and feedback, one judgment from
`correct | incorrect | uncertain | not_assessable`, one error kind from
`none | root | dependent`, and earlier dependency step keys. Every confirmed block is assigned once
and only once. Correct, uncertain, and not-assessable steps have no error relationship. Every
incorrect step is classified root or dependent; roots have no dependency, and dependent errors
must reach an earlier root through an acyclic dependency graph.

Provider rubric awards name stored rubric codes and concise explanations. Application code
requires every stored rubric exactly once, checks `0 <= award <= stored maximum`, maps it to the
immutable rubric item/skill IDs, and calculates score and maximum itself with Decimal arithmetic.
The model never supplies the final total or a maximum. Application-generated UUID step IDs replace
provider keys before persistence/response.

All provider prose is bounded plain visible text. Markdown markers, HTML tags, URLs, executable
content, arbitrary dictionaries, and unknown fields/enums fail validation. Application code converts
validated prose to text `ContentBlock[]` with application-owned IDs. No hidden reasoning is requested,
stored, or exposed.

The application response is another strict union:

- ready: evaluation/run identity, confirmed version, decimal score/max, ordered typed steps,
  typed rubric breakdown, typed overall feedback, non-exhaustive-reference literal, and next action;
- uncertain: evaluation/run identity, confirmed version, typed uncertainty explanation and
  `manual_review`, with score/steps/rubric absent.

### Provider boundary and repair policy

`StrictEvaluationProvider` is a new narrow adapter with one `evaluate` operation. It does not import,
wrap, or widen `StrictTranscriptionProvider`, and the transcription adapter remains image-to-flat-
document only.

The default fake records provider `application-owned-deterministic-fake`, model
`m7-evaluation-fixture-v1`, zero usage/cost, and traverses the same service/persistence/schema path.
Its outcomes are keyed only by exact synthetic transcript content, never by browser outcome flags.

The separately configurable real adapter is Google Gemini with only the already approved exact
`gemini-3.5-flash-lite` and `gemini-3.5-flash` model IDs and existing application-owned pricing
identities. Configuration is server-only. Tests use hand-authored synthetic Gemini envelopes through
`httpx.MockTransport`; no live call is authorized. The provider receives minimal structured-output
guidance compatible with the M6 decision, followed by authoritative strict Pydantic validation.

One schema-invalid payload causes exactly one repair request. A second schema failure is terminal
`evaluation_invalid_schema`. Transport/provider failures are not automatically retried. Safe states
are `processing`, `succeeded`, `uncertain`, `retryable_failure`, `permanent_failure`, and
`invalid_schema`. Timeout, rate-limit, and transport failure are retryable; provider rejection is
permanent. No terminal failure persists or returns a score, steps, evaluation, or hint.

### Idempotency and concurrency

`POST /evaluation` uses a globally unique idempotency UUID and an application fingerprint over attempt,
exact confirmation/hash, provider/model, prompt hash, and schema. Repeating the same key returns the
same terminal result or in-progress conflict. A new key replays a completed success/uncertainty/
permanent/invalid-schema result for the same fingerprint without another provider call. A new key
may retry only a retryable failure. An attempt row lock plus a partial unique processing index
prevents concurrent calls.

The stale-processing ambiguity remains explicit: M7 will not guess whether an accepted provider
call completed or silently start another call after a process crash.

### Progressive hints and geometry

`POST /hints/next` changes to `{idempotencyKey}`. The server verifies ownership, exact confirmed
transcript, and a terminal ready or uncertain M7 evaluation. It locks the attempt, finds the highest
durably released level, and selects only `level + 1` from the attempt's immutable problem version.
The browser cannot submit a level. Repeating a key returns the same hint event; each release stores
the exact hint ID/level and evaluation ID. Level 5 exhausts the ladder and a later request returns
`hint_ladder_exhausted` without a row.

Before a hint event is committed, content blocks are strictly parsed and geometry actions are
revalidated against the exact curated scene version: object existence, selection capability,
animation ID, point-like animation target, and ask-select allow/correct relationships. A problem
without a scene must have no actions. The frontend validates exact action keys and scene IDs again
before rendering. No runtime object creation or executable code is possible.

### UI state

The existing transient journey state is renamed from mock evaluation to evaluation and stores only
validated response references. Provider calls and hint progression remain server-owned. The result
component exhaustively renders ready and uncertain unions with typed content. Generic operation
failure state retains distinct retryable/permanent/invalid-schema presentation. Buttons are disabled
by phase/loading transitions so one UI action releases one hint.

## Multi-exam impact

- Study profiles: unchanged; ownership still roots at one active profile.
- Exam targets: unchanged; all active targets remain independent records and plan arrays remain
  intact.
- Exam-specific progress: unchanged and not introduced.
- Shared skill state: unchanged; rubric skill IDs are reported only as immutable content references,
  not learner evidence.
- Daily-plan balancing: unchanged; the M5 deterministic plan and exact supported-target arrays are
  preserved.

Evaluation, steps, and hint releases belong to an attempt and immutable problem version, never to one
singular examination target.

## Files and components

Owned files are recorded before shared-contract edits.

### Add

- `services/api/migrations/versions/20260828_0004_evaluation_scoring_hints.py` — M7 durable tables,
  constraints, indexes, and immutable/status triggers.
- `services/api/app/evaluation/` — strict schemas, models, provider protocol, fake, Gemini adapter,
  prompt/schema guidance, evaluation service, and hint service.
- `services/api/app/evaluation/prompts/m7-evaluation-v1.txt` — reviewed fixed prompt.
- `services/api/tests/fixtures/evaluation/recorded-provider-shapes.json` — hand-authored synthetic
  envelope shapes with no real provider data.
- `services/api/tests/unit/test_evaluation_schemas.py`, `test_evaluation_provider.py`,
  `test_evaluation_adapters.py`, `test_evaluation_geometry_hints.py`, and
  `test_evaluation_gold.py` — strict, retry, adapter, geometry, and fake/gold
  coverage.
- `services/api/tests/integration/test_m7_evaluation.py` — auth, confirmation, idempotency,
  persistence, scoring, hints, geometry, and migration coverage.
- `apps/student-web/lib/evaluation-api.ts` and test — generated types plus strict runtime guards.
- `evals/grading/m7-gold-corpus.json` — original synthetic confirmed-transcript evaluation cases.
- `services/api/app/scripts/evaluate_gold_corpus.py` — deterministic, no-network gold runner.
- `docs/architecture/evaluation-scoring-and-progressive-hints.md` — permanent final architecture.
- `docs/evaluation/m7-gold-evaluation-report.md` — measured deterministic corpus results without a
  release threshold.
- `docs/evaluation/m7-evaluation-device-report.md` — five-project automated/manual evidence.

### Modify

- `.env.example` — independent server-only evaluation adapter/model settings.
- `Makefile`, `package.json`, and `README.md` — focused gold command, root check integration,
  formatting coverage, architecture/configuration documentation.
- `services/api/app/config.py` — finite evaluation provider/model settings and production safety.
- `services/api/app/api.py` — replace mock evaluation, add evaluation state, and change next-hint
  request seam.
- `services/api/migrations/env.py` and the migration trigger-count regression — M7 model
  registration and schema accounting.
- `services/api/app/static_journey/schemas.py` and `service.py` — remove obsolete mock evaluation
  while retaining plan/concept behavior; hint ownership moves to M7.
- `services/api/tests/integration/test_m5_static_journey.py` and M5 unit tests — preserve plan/retry/
  concept regressions through M7 production-shaped fake.
- `packages/api-client/openapi.json` and `packages/api-client/src/schema.d.ts` — generated only.
- `apps/student-web/lib/static-journey-api.ts` and test — remove mock evaluation and old
  client-owned hint-level APIs.
- `apps/student-web/features/journey/static-journey-state.ts` and test — M7 evaluation/hint states.
- `apps/student-web/components/journey/static-student-journey.tsx` and test — result, uncertainty,
  failure, scoring, steps, relationships, and persisted hint progression UI.
- `apps/student-web/app/globals.css` — responsive M7 score/step/rubric/error presentation.
- `tests/e2e/foundation.spec.ts` — complete M6→M7 journey and layout assertions in five projects.
- `docs/MVP_IMPLEMENTATION_PLAN.md`, M6/static journey/transcript/content/geometry architecture docs
  where their future-boundary text is superseded, and this ChangePlan.

### Delete

- `services/api/app/static_journey/mocks.py` and
  `services/api/tests/unit/test_static_journey_mocks.py` — obsolete M5 mock-evaluation boundary and
  its superseded boundary-only test. Historical documentation remains intact.

No dependency or content-package change is planned. Existing immutable rubric/reference/hint/scene
records are sufficient.

## API and schema changes

- Replace `POST /api/v1/attempts/{attempt_id}/mock-evaluation` with
  `POST /api/v1/attempts/{attempt_id}/evaluation`.
- Evaluation request: strict `{confirmedTranscriptVersionId: UUID, idempotencyKey: UUID}`.
- Evaluation response: strict ready/uncertain discriminated union described in Design.
- Add `GET /api/v1/attempts/{attempt_id}/evaluation` returning not-started, processing, ready,
  uncertain, retryable-failure, permanent-failure, or invalid-schema state.
- Change `POST /api/v1/attempts/{attempt_id}/hints/next` request from
  `{previousHintLevel}` to `{idempotencyKey}`.
- Hint response adds durable `hintEventId` and `evaluationId` while retaining hint ID/level, typed
  content/actions, disclosure flag, and concept version.
- All request/response/provider models forbid unknown fields and unsupported enums.
- FastAPI OpenAPI remains authoritative; TypeScript is regenerated, not duplicated manually.
- Browser guards reject malformed nested feedback, steps, dependencies, score arithmetic, run
  metadata, content blocks, and geometry actions before UI use.

## Database and migration

Migration `20260828_0004` adds only M7 tables:

- `evaluation_runs`: attempt/confirmed-version/prompt foreign keys; configured provider/model/
  prompt/schema/pricing identity; unique idempotency key; request fingerprint; bounded state,
  schema-attempt, latency/token/cost/error metadata; processing partial unique index; terminal
  transition trigger.
- `attempt_steps`: immutable run-bound contiguous position, validated transcript block IDs JSON,
  typed summary/feedback JSON, judgments/dependencies, and unique run/position. Attempt and exact
  confirmed-version identity remain normalized on the referenced run.
- `evaluations`: immutable one-to-one run, ready/uncertain outcome,
  nullable score/max constrained together, complete validated application result JSON, and timestamp.
- `hint_events`: immutable attempt/evaluation/hint identity, unique idempotency key, unique
  attempt/level, level 1–5 constraint, and timestamp.

Existing rows need no backfill. Existing users/profiles/targets/content/attempts/uploads/M6 records
remain compatible and all M7 tables begin empty. Query-driven indexes support run fingerprint replay,
single in-flight evaluation, ordered step load, latest owned evaluation state, and ordered hint
release. No target, learner-state, vector, or speculative index is added.

Forward deployment applies the additive migration before M7 code. Application rollback can restore
M6 code while leaving additive tables unused. Database downgrade removes M7 hint/evaluation/step/run
records in dependency order and leaves M6 confirmation/transcript records intact. A populated
downgrade permanently deletes M7 audit/results/hint history and therefore requires backup/export and
owner authorization in production. Automated tests will exercise upgrade, populated downgrade,
existing-data survival, and empty re-upgrade; tests use disposable synthetic data only.

Retention for evaluation text/results remains unresolved with the broader owner privacy policy. M7
does not invent a deletion period.

## Security and privacy

- Every evaluation state/request and hint release requires invitation authentication and joins
  `evaluation/hint -> attempt -> study_profile -> user`; cross-user resources use safe not-found.
- The service evaluates only the exact immutable confirmed transcript version/hash and exact
  immutable problem version. It never reopens the image or accepts a browser transcript.
- Provider/model/prompt/schema/pricing/retry fields are server settings and cannot be submitted by
  the browser. Keys remain `SecretStr`, server-only, and absent from OpenAPI/client/logs/docs.
- No raw provider response/error, provider URL, signed URL, image bytes, hidden reasoning,
  chain-of-thought, or arbitrary metadata is persisted or returned.
- Persisted JSON contains only validated typed application-facing steps, dependencies, rubric
  judgments, concise explanations, and uncertainty data.
- Gold, unit, integration, and browser fixtures are original synthetic/non-personal data. No real
  learner, minor, examination, or personal data is used.
- No paid call is authorized. Recorded adapter shapes use `httpx.MockTransport` only.
- Provider retention/production suitability remains unapproved; M6's documented Gemini facts are
  reused without expanding the claim.
- Logs may contain only internal run IDs and safe status/error/latency/token/cost metadata, never
  transcript or feedback content.

## Test plan

### Unit

- Strict provider/application unions; exact keys; unknown enum/field/HTML/Markdown/URL/code rejection.
- Post-confirmation block partitioning, unique ordered steps, valid root/dependent graph, and
  invalid/missing/forward/cyclic dependency rejection.
- Correct, incorrect, uncertain, and not-assessable judgment invariants.
- Exactly one schema repair, recovery on call two, exhaustion after call two, and no third call.
- Timeout, rate limit, transport, provider rejection, uncertainty, and metadata mismatch without
  fabricated result.
- Stored-rubric mapping, all-and-only rubric codes, Decimal bounds, server-calculated total/max, and
  score consistency.
- Deterministic fake cases for standard, valid alternative, subtle error, incomplete, contradictory,
  unreadable, root, and dependent work.
- Gemini recorded envelope, exact model/pricing/request URL, minimal structured guidance, safe error,
  and absence of browser/provider identity fields.
- Hint geometry revalidation for every finite action plus unknown objects, animations, selection
  capability, and no-scene failures.

### Integration and migration

- Authentication required and cross-user attempt/confirmation/evaluation/hint isolation.
- Evaluation rejected before confirmation, for another attempt/version/hash, and for a non-exact
  confirmed version.
- Success persists run, post-confirmation steps, evaluation result, exact metadata, and no target FK.
- Same idempotency key replay, completed fingerprint replay, distinct concurrent key exclusion,
  retry only after retryable failure, and one fake provider call.
- Invalid schema calls provider exactly twice and persists no evaluation/steps; transport/permanent
  failure and uncertainty persist no fabricated score.
- Standard and alternative solutions receive rubric-consistent full credit without reference-string
  equality; subtle error records root/dependent relationships; incomplete work is not assessable;
  contradictory/unreadable work routes to score-free uncertainty.
- Server-owned ordered hints 1–5, duplicate request replay, exhausted ladder, ready/uncertain
  evaluation prerequisite, and no browser-selected level.
- Valid geometry hint actions persist/reload; focused action validation rejects unknown curated IDs,
  invalid animation targets, non-selectable choices, and invalid correct/allowed subsets.
- Upgrade/downgrade/re-upgrade and existing M6 row compatibility.

### API/generated contract

- Exact evaluation/hint requests, response/state discriminators, score fields, enums, dependency IDs,
  typed content, metadata, forbidden provider selectors, and stable safe errors.
- `make api-generate` followed by byte-clean `scripts/check_api_contract.sh`.
- Browser runtime guards reject every malformed nested result before render.

### Frontend component/state

- Evaluation loading, retryable, permanent, invalid-schema, ready, and score-free uncertainty states.
- Ready score/rubric arithmetic, ordered step judgments, root/dependent labels/links, typed feedback,
  next action, metadata, and non-exhaustive-reference copy.
- No step UI in correction/confirmation before the evaluation response.
- Hint release order, disabled loading action, levels 1–5, final disclosure, exhausted UI, and safe
  invalid geometry action handling.
- Existing M3 native-caret/MathLive, M4 geometry, M5 multi-target plan/retry/concept, and M6 exact
  confirmation regressions.

### Browser/end-to-end and five-project device matrix

The complete invite/profile/two-target/plan/problem/geometry/upload/fake-transcribe/correct/confirm/
evaluate/hint/retry/concept/summary journey runs in all five configured projects:

1. compact Chromium at 360×640;
2. Pixel 7 Chromium;
3. iPhone 13 WebKit;
4. iPad Pro 11 portrait WebKit;
5. iPad Pro 11 landscape WebKit.

Every project asserts no step UI before confirmation/evaluation, exact transcript version/hash,
evaluation loading then score/rubric/step/root/dependent presentation, non-exhaustive reference copy,
ordered server-owned hints with valid geometry controls, keyboard/touch operation, and document-level
horizontal containment. A visual run captures confirmation, ready evaluation, progressive hint, and
uncertainty/failure evidence where deterministic test setup permits; screenshots are inspected at
high detail and hashes/results recorded. Physical devices and true Apple simulators remain pre-pilot.

### Gold evaluation/regression

`evals/grading/m7-gold-corpus.json` contains only original synthetic flat confirmed transcripts and
expected application-facing outcomes for:

1. correct standard solution;
2. mathematically valid alternative solution not present as a reference string;
3. subtle mathematical root error with a dependent consequence;
4. incomplete solution;
5. contradictory work;
6. unreadable/not faithfully assessable work;
7. explicit root/dependent classification coverage;
8. rubric maximum/score consistency coverage.

The deterministic no-network runner validates every fake provider payload through the same strict
boundary and reports exact fixture count, ready/uncertain counts, outcome agreement, score agreement,
judgment agreement, root/dependent agreement, alternative acceptance, schema failures, latency,
tokens, and cost. The report records measured values only. No pass threshold, production quality,
provider comparison, or release gate is invented.

## Manual QA

1. Start isolated synthetic services in fake transcription and fake evaluation mode; seed only the
   repository fixtures and five synthetic invites.
2. In each configured project, authenticate, confirm two independent active targets, and verify the
   unchanged plan support arrays and immutable problem version.
3. Upload the committed synthetic M6 fixture, correct text with the native caret, correct math with
   MathLive, and confirm exact version/hash. Verify no step heading exists in correction.
4. Start evaluation and inspect loading. Verify ready output shows a 4-point rubric maximum, ordered
   application-facing steps, status labels, root/dependent relationship, typed feedback, exact run
   metadata, and no raw provider content/source.
5. Exercise injected uncertainty, retryable failure, permanent failure, and two-invalid-schema
   variants. Verify uncertainty has no score/steps and failures have no result/hint.
6. Request hints sequentially, operate highlight/show/ask-select actions by touch and keyboard, and
   verify no level can be skipped. Continue to final disclosure and verify exhaustion.
7. Inspect the retry's distinct attempt ID and identical immutable problem version, concept, and
   two-target summary. Verify no learner mastery/progress update appears.
8. Check 44 px controls, focus order, screen-reader labels, KaTeX fallbacks, wrapping, and
   `scrollWidth <= clientWidth + 1` in all projects.

## Rollout and rollback

- Default local/test mode is deterministic fake evaluation. Real evaluation mode requires explicit
  server-only provider, exact approved Gemini model, key, and timeout. There is no browser switch.
- Production startup rejects fake evaluation, missing key, unapproved model alias, insecure sessions,
  and the existing unsafe development defaults. This is configuration safety, not provider/privacy
  approval.
- Apply M7 migration before application deployment. M6 clients do not call the new endpoints; M7
  code no longer depends on the old mock evaluation contract.
- Monitor aggregate stable evaluation status/error/latency/usage/cost and hint release counts by
  internal IDs only. Do not log student content.
- Application rollback returns to M6 and ignores additive M7 tables. Database downgrade is
  destructive to M7 audit/result/hint records and requires backup/export plus explicit authorization.

## Branch and commit plan

1. `docs: add Milestone 7 change plan`
2. `test: specify evaluation provider and score contracts`
3. `feat: persist strict evaluation runs and results`
4. `test: specify server-owned progressive hints`
5. `feat: persist and validate progressive hints`
6. `feat: connect evaluation and hint journey`
7. `test: add Milestone 7 gold and device regressions`
8. `docs: record Milestone 7 architecture and evidence`

Commits may be split further to keep them coherent and testable; they will not be squashed locally.

## Conflict coordination

Owned shared files are the migration head, Alembic model imports, `config.py`, `api.py`, the M5
static-journey schemas/service and retired mock boundary, migration regressions, generated API artifacts, root
Makefile/package/README, static journey API/state/component/CSS, foundation E2E, MVP and permanent
architecture docs. The new evaluation package, tests, fixtures, eval corpus, and M7 documents are
exclusive to this branch.

Integration order for overlapping contracts is current `origin/main` first, then M7 migration and
FastAPI schema, generated clients, frontend consumers, E2E, and documentation. Before handoff the
branch will fetch/rebase current `origin/main`. A conflict that changes behavior or a public contract
will stop automatic resolution, be documented, resolved deliberately, and trigger all affected
checks.

## Risks

- Model grading can falsely criticize valid alternatives. Mitigation: prompt literal, non-exhaustive
  references, alternative fixture, strict uncertainty route, and no production-quality claim.
- Provider output can expose hidden reasoning or unsafe content. Mitigation: request only concise
  application judgments, strict plain-text fields, typed conversion, unknown-field rejection, and no
  raw persistence/logging.
- Model score arithmetic can drift from the rubric. Mitigation: provider supplies bounded awards
  only; application maps immutable rubric items and computes total/max.
- Step grouping can mutate the authoritative transcript. Mitigation: post-confirmation steps contain
  only references to immutable block IDs; transcript JSON remains unchanged.
- Duplicate evaluation clicks can incur cost. Mitigation: database idempotency, fingerprint replay,
  one in-flight partial index, and no transport retry.
- Hint clients can skip levels or apply corrupt actions. Mitigation: server derives the next level,
  persists unique release events, and revalidates exact scene IDs before commit and render.
- JSONB can contain corrupt legacy/manual data. Mitigation: strict validation on every read and safe
  terminal errors; no shared database is edited manually.
- Migration downgrade destroys M7 records. Mitigation: additive deployment, explicit destructive
  rollback warning, backup/export, and populated downgrade test.
- Large UI changes can regress M3–M6 phone/tablet behavior. Mitigation: preserve existing editor and
  renderer modules, focused component tests, full five-project production-build run, and screenshot
  inspection.
- A live provider run could incur cost or process real data. Mitigation: fake default, recorded shapes,
  separate settings, no key inspection, and no paid call in this change.

## Progress

- [x] Repository inspected
- [x] Plan reviewed and authorized by the project owner
- [x] Branch created from current main
- [x] Tests written or updated
- [x] Implementation complete
- [x] Documentation updated
- [x] Relevant checks pass
- [ ] Diff reviewed
- [ ] Branch rebased on current main
- [ ] Conflict resolution re-tested
- [ ] Handoff summary written

## Decisions

- The M5 mock-evaluation endpoint, boundary module, schemas, and boundary-only unit test are removed
  because M7 replaces that public/product seam with the durable strict evaluation adapter. Keeping
  the unreachable mock would create a second incompatible grading contract; its obsolete behavior
  is covered by the new evaluation provider, schema, integration, frontend, and gold tests.

- 2026-08-28: The required completed M6 commit is the current published `origin/main` tip, so M7 may
  proceed.
- 2026-08-28: Use a separate clean worktree and do not inspect or mutate unrelated corpus/data work
  in the shared checkout.
- 2026-08-28: Keep M6 transcription and M7 evaluation as separate strict provider packages. The M6
  image adapter will not become a generic AI gateway.
- 2026-08-28: Reuse only exact Gemini model IDs/pricing decisions already approved in M6 for the
  optional real M7 adapter; automated work remains on the fake and recorded envelopes.
- 2026-08-28: Persist a separate M7 run table because M6 model runs are correctly bound to attempt
  image assets.
- 2026-08-28: Application code, not the model, calculates the rubric total/max and owns step IDs,
  workflow transitions, idempotency, and hint progression.
- 2026-08-28: Overall provider uncertainty returns no score or reasoning steps. A provider failure
  returns no evaluation result at all.
- 2026-08-28: Runtime hints select reviewed immutable content; M7 does not ask the provider to
  generate a hint.
- 2026-08-28: No numeric release threshold or paid provider benchmark is authorized.
- 2026-08-28: Hint responses include both durable event and evaluation IDs so a browser cannot
  mistake a released level for an unbound transient hint.
- 2026-08-28: Provider-visible prose rejects Markdown constructs, HTML, common URL forms, and
  executable URI schemes before typed `TextBlock` conversion.

## Discoveries

- The existing `prompt_versions` table was intentionally operation-scoped and can safely hold a
  distinct immutable evaluation prompt without changing the transcription adapter.
- The existing `ai_model_runs` table cannot represent a content-only evaluation without weakening
  its non-null image-asset contract; a separate table is the deeper boundary.
- M5 already validates imported geometry actions, but server-owned progressive release needs
  validation against stored scene JSON again at request time.
- M5 hint progression is transient and client-level driven, so its request contract must change
  rather than be relabeled.
- The current M6 browser journey already supplies the exact confirmed version ID needed by M7 and
  has explicit generic failure variants that can be extended without altering the editor.
- Hint events already normalize the evaluation relationship, so attempt/confirmation identity does
  not need to be duplicated in step/evaluation rows; every read follows the immutable run.

## Verification evidence

- `git fetch origin main` — succeeded; fetched `main`.
- `git rev-parse origin/main` —
  `e3e6d13f9913d94b851c8f5b149eaf8482b65173`.
- `git merge-base --is-ancestor e3e6d13f9913d94b851c8f5b149eaf8482b65173 origin/main` — exit 0.
- `git worktree add -b feat/m7-evaluation-scoring-hints
/home/minh/dev/math-coach-m7-evaluation origin/main` — succeeded at the M6 commit.
- Required documentation, applicable instructions, authentication/profile/target/content/attempt/
  upload/transcription/mock-evaluation/hint/geometry/provider/API/database/migration/frontend/
  generated-contract/package/Playwright source and relevant tests were read before this file was
  created.
- `git status --short` before this ChangePlan — empty.
- `make format-check` — passed; Prettier and Ruff reported every configured file formatted.
- `make lint` — passed; ESLint and Ruff reported no issues.
- `make typecheck` — passed; both TypeScript workspaces passed and mypy reported no issues in 58
  backend source files.
- `make api-contract-check` — passed after generating OpenAPI and TypeScript declarations.
- Focused provider/schema/geometry/gold backend tests — passed before the final aggregate run.
- Focused `services/api/tests/integration/test_m7_evaluation.py` — 13 passed, including auth,
  ownership, exact confirmation, idempotency, concurrency, safe terminal failures, scoring,
  uncertainty, hints, and populated downgrade behavior.
- `make evaluation-gold` — six of six original synthetic fixtures matched; every case used one
  schema attempt, zero tokens, and `0.000000` USD; release threshold remained null.
- `VISUAL_QA=1 make test-e2e` — production build passed and all 15 cases passed across the five
  configured projects in 22.5 seconds. Ten M7 screenshots were inspected at original resolution;
  exact hashes are in the device report.
- `make check` before rebase — passed in full: formatting; ESLint/Ruff; TypeScript/mypy; generated
  API drift; two content packages; six-of-six gold fixtures; production build; 153 frontend unit
  tests; 131 backend non-integration tests; two base-to-head migration cycles; 52 backend integration
  tests; and 15 Playwright cases across all five projects.
- No provider key was read, no live or paid provider call was made, and every fixture was synthetic
  and non-personal.

## Result

In progress. No implementation file has been modified and no paid provider call has been made.
