# Milestone 6 multimodal transcription

## Metadata

- Status: blocked
- Owner: project owner and Codex
- Branch: `feat/m6-multimodal-transcription`
- Base commit: `dbfd8162a27f2f63fecfcdbe63759d64eab56c24`
- Related milestone: Milestone 6 — Multimodal transcription
- Related issue/ticket: None supplied
- Started: 2026-08-27
- Last updated: 2026-08-27

## Context

Milestone 5 is published on `origin/main` at commit
`dbfd8162a27f2f63fecfcdbe63759d64eab56c24`. It connects invitation authentication, one study
profile with multiple active examination targets, a deterministic plan, attempts pinned to immutable
problem versions, verified object-storage uploads, a deterministic in-memory mock transcript,
Milestone 3 visual correction, local confirmation, and clearly synthetic downstream evaluation and
hints.

The current transcript is not durable. The browser submits the complete transcript while claiming it
is confirmed, and the server has no transcript-version, confirmation, attempt-asset, prompt-version,
or model-run records. The mock transcription boundary does not read image bytes. It therefore cannot
provide the authenticated, auditable, provider-backed transcription and exact confirmation required
by Milestone 6.

Repository provider documentation deliberately leaves the real provider, exact model, candidate
count, fixture count, and budget as `DECISION REQUIRED`. The project owner must select the provider
and exact model before provider-specific implementation, and must separately approve fixture count
and maximum spend before a real network call. This ChangePlan records the inspected options and the
provider-independent design but remains blocked at that gate.

## Goal

An invited learner can use the existing multi-target M5 plan, open an attempt pinned to its immutable
problem version, upload a clearly synthetic image, request server-owned multimodal transcription,
receive only a completely validated flat ordered text/math document, correct it with a native caret
and MathLive, and explicitly confirm an exact durable transcript version and hash. A configured real
provider and a deterministic fake share one narrow production-shaped adapter. Every run records
validated provider/model/prompt/schema/latency/token/cost metadata, and the existing downstream
evaluation remains conspicuously synthetic and unavailable until confirmation.

## Non-goals

- Production evaluation, scoring, reasoning-step analysis, or generalized hint generation from
  Milestone 7.
- Learner-evidence events, skill-state aggregation, or mastery updates from Milestone 8.
- Adaptive planning or planner changes from Milestone 9.
- Reasoning-step IDs, reasoning grouping, chain-of-thought, or raw provider reasoning.
- General prompt orchestration, workflow engines, RAG, vector databases, analytics, Markdown, raw AI
  HTML, executable geometry, arbitrary provider URLs, WebSockets, or SSE.
- Native wrappers, direct pen input, camera capture, or voice conversation.
- Real learner, minor, examination, or personal data in development, tests, or benchmarks.
- Provider-production approval, privacy suitability claims, or numerical release gates.
- Any change to the deterministic multi-target plan or shared learner state.

## User-visible behavior

- The upload screen continues to accept JPEG, PNG, and WebP images up to the existing 10 MB limit
  and continues to label development and test fixtures as synthetic.
- After an owned upload is verified, the learner sees an explicit transcription loading state.
- A fully validated transcript appears as one continuous document in canonical array order. Typed
  text and math alternate inline; no reasoning steps or raw source format are shown.
- Safe finite warnings appear above the correction surface. When a warning names a source region,
  the owned source image shows a CSS overlay and an accessible text description; no canvas or
  executable geometry is introduced.
- Valid but malformed mathematics renders as the existing source-free “Math needs correction”
  placeholder and can be corrected visually with MathLive. Raw LaTeX is never required or exposed.
- Loading, warnings, uncertainty, retryable provider failure, permanent provider failure, and
  terminal invalid-schema exhaustion are distinct states. None renders a fabricated transcript.
- A retryable transport/provider run can be retried explicitly. Duplicate clicks with the same
  idempotency key do not create duplicate paid calls.
- Correction saves a new immutable transcript version. Confirmation names the exact version and
  SHA-256 document hash. Repeating the same confirmation is idempotent; editing or confirming a
  different version after confirmation is rejected.
- Reload resets the current in-browser M5 navigation, as it does today, but the authenticated API can
  reload the persisted run, transcript versions, and confirmation for the owned attempt. The device
  report will state this boundary explicitly.
- Only the confirmed server-loaded transcript version can enter the M5 mock evaluation. The UI will
  say that the evaluation remains a deterministic synthetic demonstration and is not production
  grading, even when the transcript came from a real provider.

## Current-state findings

- The shared checkout was on `main` with unrelated untracked `docs/research/` and
  `student_exam_targets[]` paths. They were not opened, formatted, staged, stashed, or discarded.
  This branch therefore uses the separate clean worktree
  `/home/minh/dev/math-coach-m6-transcription`.
- The configured SSH remote could not authenticate in this environment. A read-only HTTPS
  `ls-remote` and HTTPS fetch both resolved `refs/heads/main` to
  `dbfd8162a27f2f63fecfcdbe63759d64eab56c24`; the required M5 commit is the current remote tip.
- The only applicable nested repository instructions are `apps/student-web/AGENTS.md`. Relevant
  bundled Next 16 documentation for client boundaries, data fetching, expected errors, and CSS was
  inspected before planning frontend changes.
- Root commands required by Milestone 1 exist. `make check` runs formatting, linting, TypeScript and
  Python type checking, generated-contract checks, content validation, unit tests, integration tests,
  and the containerized Playwright suite.
- FastAPI/Pydantic is the authoritative API boundary. `scripts/check_api_contract.sh` exports
  OpenAPI, generates TypeScript declarations with `openapi-typescript`, and byte-compares both
  committed files. Current SHA-256 values are
  `6b2ae0913ba724fbb59cf91273cef41e783bf4a571ec2396767049ba073dc913` for
  `packages/api-client/openapi.json` and
  `291477c868b25f61f7f88cabcbe40d5dc17f4b6c0dd10fa31774a3ea40251f75` for
  `packages/api-client/src/schema.d.ts`.
- The backend currently has 15 tracked Python test files and 58 Python test functions. The frontend
  and browser suites have 23 tracked test/spec files and 102 JavaScript/TypeScript test cases.
- Existing integration tests exercise real PostgreSQL migrations and real MinIO-compatible object
  storage. They verify invitation authentication, upload ownership, object-size/MIME verification,
  profile/target isolation, immutable content, and attempt version pinning.
- `solution_uploads` stores only object metadata. Image bytes remain in object storage. `ObjectStorage`
  supports presign, stat, and remove but not an internal bounded read or short-lived download URL.
- `attempts.problem_version_id` is non-null and references an immutable `problem_versions` row.
- `study_profile -> student_exam_targets[]` is implemented throughout the M5 plan. Plan items carry
  arrays of `supportedTargetIds`; M6 must not change this contract.
- M5 `TranscriptDocument` schema `2.0.0` is a strict, flat, non-empty discriminated union of text and
  math blocks with unique IDs. It has no durable version identity, warnings, or source regions.
- M5 schema validation retries a malformed mock payload exactly once. The current deterministic fake
  records zero-cost synthetic metadata but does not use image bytes or production-shaped persistence.
- The M5 browser performs strict nested runtime checks before correction. The M3 editor uses one
  `contentEditable="plaintext-only"` document, native text caret, MathLive formula editing, and a
  bounded KaTeX renderer that hides raw source on failure.
- The current browser confirmation is only a local clone. `POST /mock-evaluation` accepts a complete
  browser-supplied `ConfirmedTranscript`, so the server does not prove which durable version was
  confirmed.
- The five Playwright projects already match the required matrix and run in parallel: compact
  Chromium 360 × 640, Pixel 7 Chromium 412 × 839, iPhone 13 WebKit 390 × 664, iPad Pro 11 portrait
  WebKit 834 × 1194, and iPad Pro 11 landscape WebKit 1194 × 834.
- No real AI provider implementation or provider configuration exists. The only provider/model IDs
  are visibly fake M5 identifiers. `docs/evaluation/AI_PROVIDER_BENCHMARK.md` leaves provider and
  exact model selection explicitly undecided.
- `httpx==0.28.1` is already locked in the backend development group and used by tests. It is not a
  production dependency. Its wheel is 73,517 bytes and its installed distribution is 295,877 bytes;
  its direct dependencies are AnyIO, Certifi, HTTP Core, and IDNA. The inspected installed set is
  1,683,540 bytes, with some transitive packages already required by the existing runtime stack.

## Design

### TDD order and public seams

Implementation will follow red-green-refactor at public seams. Each slice starts with one failing
test, proves the expected failure, adds only enough implementation to pass, and refactors while green.
Mocks are limited to the external provider transport/object boundary; domain/database behavior uses
real application schemas and integration infrastructure.

1. Strict provider payload to application transcript: adapter contract test, then schema and fake.
2. Owned verified upload to idempotent durable run: integration test, then migration/repository/service.
3. Durable correction and exact confirmation: integration test, then version/confirmation endpoints.
4. Strict browser parser to correction UI: boundary/component test, then client state and UI.
5. Confirmed-version-only M5 mock evaluation: integration/browser regression, then endpoint migration.
6. Approved real transport: recorded provider-shape tests first, then direct HTTP implementation.
7. Full fake-provider journey across all five browser projects, then the separately approved real
   synthetic benchmark.

The public HTTP seams follow the endpoint names already specified by the MVP plan:

- `POST /api/v1/attempts/{attempt_id}/transcribe`
- `GET /api/v1/attempts/{attempt_id}/transcription`
- `POST /api/v1/attempts/{attempt_id}/transcripts`
- `POST /api/v1/attempts/{attempt_id}/confirm-transcript`
- `POST /api/v1/attempts/{attempt_id}/mock-evaluation`, changed to accept only a confirmed transcript
  version ID rather than a browser-supplied document
- `POST /api/v1/uploads/{upload_id}/download-url` for a short-lived, authenticated source-image URL

Ordinary authenticated HTTP is sufficient. No inspected requirement needs one-way streamed progress,
so SSE is rejected.

### Provider-owned and application-owned boundaries

`TranscriptionProvider` is the only provider seam. It accepts an application-owned immutable input:
verified image bytes and MIME, an exact immutable problem statement/version reference, and the
configured prompt/schema identities. It exposes one `transcribe` operation and no evaluation, hint,
workflow, or generic completion method.

The adapter owns all provider request/response types. Provider payloads are parsed with strict
Pydantic models that forbid unknown fields before the adapter returns an application
`TranscriptionProviderResult`. Domain/service code never receives raw provider dictionaries, raw
errors, Markdown, HTML, URLs, executable content, or provider control-flow instructions.

Server settings select exactly one adapter: deterministic fake or the owner-approved real provider.
Requests cannot contain provider, model, prompt, schema, pricing, retry, or test-outcome selectors.
The configured adapter stamps provider and exact model metadata; provider output cannot claim a
different provider/model/prompt/schema identity. Provider-returned usage is validated and cost is
calculated by application-owned pricing configuration.

The initial application prompt identity is proposed as `m6-faithful-transcription-v1`, paired with
application transcript schema `3.0.0` and provider-output schema `m6-provider-transcript-v1`. Its
reviewable committed text will require only faithful visible transcription, preservation of every
written mathematical error, one flat reading order, explicit uncertainty rather than invention, and
the strict allowed JSON shape. The exact prompt text and SHA-256 hash will be committed and recorded
for every run after the provider choice is approved; no generalized prompt system will be added.

The deterministic fake uses provider `application-owned-deterministic-fake`, model snapshot
`m6-transcription-fixture-v1`, the same prompt/schema identities, the same service and persistence
path, and zero usage/cost. Test-only outcome selection is injected server-side in test setup and is
not accepted from the browser.

### Strict transcript schema

`TranscriptDocument` is compatibly extended and versioned as `3.0.0`; it is not copied into a manual
frontend type. Its `blocks` remain the canonical single flat order. Each block is a strict
discriminated union:

- `{id, type: "text", text, sourceRegion?}`
- `{id, type: "math", latex, sourceRegion?}`

Block IDs are non-empty, unique, and stable once persisted. Provider block positions are converted
to application-owned IDs; corrections preserve existing IDs and create new client IDs only for
learner-inserted blocks. The document forbids reasoning steps, arbitrary dictionaries, Markdown,
HTML, URLs, code variants, and unknown keys.

A source region is optional and strict: `{attemptAssetId, units: "normalized", x, y, width,
height}`. The coordinate origin is the image's top-left. Each decimal is finite and in `[0, 1]`,
width and height are greater than zero, and `x + width <= 1` and `y + height <= 1`. The referenced
asset must belong to the route attempt and current user.

Warnings use the finite codes `low_confidence_text`, `low_confidence_math`,
`ambiguous_cross_out`, `ambiguous_insertion`, `ordering_uncertain`, and
`source_region_unavailable`. Provider output supplies only a code and optional block position;
application code maps it to one fixed concise safe message and a persisted block ID. Unknown codes,
arbitrary provider prose, and references to missing blocks fail validation.

The provider result is a strict discriminated union:

- `ready`: non-empty blocks and validated warnings/source regions;
- `uncertain`: no transcript document and finite safe warnings.

An empty output, unknown field/variant, invalid region, invalid warning reference, or malformed
structured payload triggers exactly one schema-repair provider call. A second schema failure becomes
the terminal `transcription_invalid_schema` error and persists no transcript. Network/timeout/rate
limit failures are not schema-retried. Syntactically invalid but bounded math source may remain in a
valid document so the existing source-free KaTeX placeholder and MathLive correction flow can repair
what was written; empty or over-limit math values fail the boundary.

### Error mapping

- `transcription_timeout`, `transcription_rate_limited`, and `transcription_transport_failed` are
  retryable and return a safe 503 response.
- `transcription_provider_rejected` is permanent and returns a safe 502 response.
- `transcription_invalid_media` is permanent and returns 422.
- `transcription_empty_output` and `transcription_invalid_schema` are terminal invalid-schema states
  and return 502 after at most one schema repair.
- A valid provider uncertainty result returns an explicit `uncertain` application outcome with no
  transcript.
- `transcription_in_progress` returns 409 without starting a duplicate call.
- Raw provider response/error bodies and secrets are never logged or returned.

### Idempotency and concurrency

`POST /transcribe` accepts only `{uploadId, idempotencyKey}`. A repeated key returns the same terminal
result or the same in-progress run without a new paid call. At most one run may be processing for one
attempt asset. A second click with another key while processing returns
`transcription_in_progress`. A new key may start a manual retry only after a retryable terminal
failure. Successful, uncertain, permanent, and invalid-schema terminal runs are replayed rather than
silently charged again; a new verified upload creates a new attempt asset and may start a new run.
There is no automatic transport retry and no unbounded provider retry.

Correction inserts a new immutable transcript version using `{baseTranscriptVersionId, document}`.
Repeating the same base-version/document-hash request returns the same version. Confirmation accepts
`{transcriptVersionId, transcriptHash}`. Repeating the exact pair returns the same immutable
confirmation; a different pair after confirmation returns `transcript_already_confirmed`. Any later
correction returns `transcript_confirmed_locked`. M6 deliberately chooses rejection instead of a
return-to-correction transition.

### Synthetic fixtures and benchmark

Ten deterministic repository-owned image fixtures are proposed, each with an expected flat
transcript and provenance manifest:

1. clean handwritten mathematics;
2. messy but readable mathematics;
3. mixed Vietnamese text and mathematics;
4. cross-outs and insertions;
5. a correct standard solution;
6. a correct alternative solution;
7. a subtle mathematical sign error that must remain unchanged;
8. an incomplete solution;
9. a geometry solution;
10. alternating text and mathematics on one visual line.

Warnings and source regions are represented within this set. Separate recorded JSON shapes cover
valid output, unknown fields/variants, empty output, invalid regions, one-retry recovery, retry
exhaustion, timeout, rate limit, permanent rejection, uncertainty, and fake/real metadata mismatch.
Upload tests cover invalid MIME, size, status, and ownership. Every fixture is labeled original
synthetic, generated deterministically for this repository, and carries no real examination,
learner, handwriting, provider response, or personal metadata.

The real benchmark command is opt-in and refuses to run unless real mode, the exact approved model,
an explicit synthetic-only acknowledgement, a call ceiling, and a USD ceiling are configured. The
proposal is 10 fixtures, at most 20 paid calls (one initial and the worst-case one schema repair per
fixture), at most 10,000 billed input tokens and 3,000 output tokens per call, and no transport
retry. Estimated maximum model charges, before tax or regional adjustments, are:

| Candidate                                                                                   | Published input/output price per 1M tokens | Estimated maximum |
| ------------------------------------------------------------------------------------------- | ------------------------------------------ | ----------------: |
| [OpenAI `gpt-5.4-2026-03-05`](https://developers.openai.com/api/docs/models/gpt-5.4)        | $2.50 / $15.00                             |             $1.40 |
| [Anthropic `claude-sonnet-5`](https://platform.claude.com/docs/en/models/sonnet-5/overview) | $2.00 / $10.00                             |             $1.00 |
| [Google `gemini-3.5-flash`](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash)  | $1.50 / $9.00                              |             $0.84 |

Actual usage and cost will be recorded from validated usage metadata and application pricing; these
figures are conservative planning ceilings, not release gates or provider approval.

## Multi-exam impact

- Study profiles: unchanged; one owned active profile remains the attempt's authorization root.
- Exam targets: unchanged; every active target remains an independent `student_exam_targets` record.
- Exam-specific progress: unchanged and not introduced.
- Shared skill state: unchanged and not introduced.
- Daily-plan balancing: unchanged; M5 deterministic inputs, order, supported-target arrays, and
  selection reasons remain byte-for-byte compatible.

Transcription records belong to an attempt and its immutable problem version, not to one examination.
No target foreign key, singular target field, duplicated per-exam transcript, or per-exam learner
state is added.

## Files and components

Proposed owned files are listed before implementation. Exact additions may be narrowed, but any
expansion or contract change must be recorded here before editing.

### Add

- `services/api/migrations/versions/20260827_0003_multimodal_transcription.py` — M6 durable schema.
- `services/api/app/transcription/__init__.py` — package boundary.
- `services/api/app/transcription/schemas.py` — strict provider and application schemas.
- `services/api/app/transcription/models.py` — attempt asset, prompt, run, version, confirmation ORM.
- `services/api/app/transcription/provider.py` — narrow protocol, error taxonomy, configured factory.
- `services/api/app/transcription/fake_provider.py` — deterministic production-shaped fake.
- `services/api/app/transcription/<approved>_provider.py` — one owner-approved real HTTP adapter.
- `services/api/app/transcription/service.py` — ownership, idempotency, persistence, correction,
  confirmation, and error mapping.
- `services/api/app/transcription/prompts/m6-faithful-transcription-v1.txt` — exact reviewed prompt.
- `services/api/app/scripts/benchmark_transcription.py` — guarded approved synthetic benchmark.
- `services/api/tests/fixtures/transcription.py` — application and provider-shape builders.
- `services/api/tests/fixtures/transcription/recorded-<approved>-shapes.json` — synthetic recorded
  response shapes, never live learner/provider data.
- `services/api/tests/unit/test_transcription_schemas.py` — strict schema regressions.
- `services/api/tests/unit/test_transcription_provider.py` — retry/error/metadata/fake and recorded
  real-shape contract regressions.
- `services/api/tests/integration/test_m6_transcription.py` — auth, object storage, persistence,
  isolation, idempotency, correction, and confirmation.
- `apps/student-web/components/transcription/transcription-status.tsx` and test — complete state UI.
- `tests/fixtures/transcription/manifest.yaml` — provenance, expected document, fixture hashes.
- `tests/fixtures/transcription/images/*.png` — ten deterministic synthetic/non-personal images.
- `tests/e2e/multimodal-transcription.spec.ts` — fake-provider journey in all five projects.
- `docs/architecture/multimodal-transcription.md` — permanent boundary and persistence architecture.
- `docs/evaluation/m6-transcription-benchmark.md` — exact provider benchmark evidence.
- `docs/evaluation/m6-transcription-device-report.md` — five-project device/regression evidence.

### Modify

- `.env.example` — server-only adapter/provider/model/timeout and guarded benchmark settings.
- `Makefile` — focused fake checks and a separate explicit real benchmark command.
- `README.md` — M6 architecture, configuration, commands, and synthetic-data boundary.
- `package.json` — format-check coverage for M6 documents, without a frontend dependency.
- `services/api/pyproject.toml` and `services/api/uv.lock` — promote the already locked
  `httpx==0.28.1` HTTP client to server runtime if approved.
- `services/api/app/config.py` — strict server-only adapter/model/prompt/pricing configuration and
  production validation.
- `services/api/app/storage.py` — bounded internal object read and short-lived signed download URL.
- `services/api/app/api.py` — authenticated M6 endpoints and M5 mock-evaluation input change.
- `services/api/migrations/env.py` — import M6 metadata for Alembic.
- `services/api/app/static_journey/schemas.py`, `mocks.py`, and `service.py` — reuse the extended
  transcript schema and load only a confirmed durable version for the visibly fake evaluation.
- `services/api/tests/integration/conftest.py` — truncate M6 tables in dependency-safe order.
- `services/api/tests/integration/test_m5_static_journey.py` and M5 unit tests — unchanged plan and
  clearly mocked downstream regression through the new confirmation identity.
- `packages/api-client/openapi.json` and `packages/api-client/src/schema.d.ts` — generated contract.
- `apps/student-web/lib/static-journey-api.ts` and test — strict nested M6 runtime guards and calls.
- `apps/student-web/features/transcription/transcript-state.ts` and test — preserve M3 editor
  operations while carrying immutable transcript-version identity outside the flat document.
- `apps/student-web/features/journey/static-journey-state.ts` and test — explicit transcription
  state variants and server confirmation.
- `apps/student-web/components/transcription/transcript-editor.tsx` and test — save-before-confirm,
  warnings/regions, confirmed locking, and existing native-caret/MathLive behavior.
- `apps/student-web/components/journey/static-student-journey.tsx` and test — real-shaped fake/real
  flow and visibly synthetic M5 evaluation.
- `apps/student-web/components/upload-workspace.tsx` and test — retain the owned image reference for
  correction display.
- `apps/student-web/app/globals.css` — responsive warning/source-region/correction states.
- `tests/e2e/foundation.spec.ts` — preserve the complete M5 regression and exact confirmation.
- `docs/architecture/static-student-journey.md` and
  `docs/architecture/math-rendering-and-transcript-state.md` — final M6 replacement boundaries.
- `docs/evaluation/AI_PROVIDER_BENCHMARK.md` and
  `docs/privacy/PRIVACY_AND_CONSENT_ACTION_LIST.md` — owner decision and documented provider facts,
  without claiming production approval.
- This ChangePlan — progress, decisions, verification, hashes, costs, and result.

### Delete

- None proposed. The public `mock-transcription` route will be removed only after the production-shaped
  fake powers every M5/M6 test and client; its fixture logic will be adapted rather than discarded
  until regressions are green.

## API and schema changes

- `POST /transcribe` request: strict `{uploadId: UUID, idempotencyKey: UUID}`; route attempt ID is
  authoritative. Provider/model/prompt/test state fields are forbidden.
- `POST /transcribe` response: strict `ready` or `uncertain` discriminated union. Ready contains a
  validated run summary and immutable transcript version; uncertain contains run metadata and finite
  warnings but no transcript.
- `GET /transcription`: strict persisted state union for not-started, processing, ready, uncertain,
  retryable failure, permanent failure, and invalid-schema exhaustion.
- `POST /transcripts`: strict base transcript version ID plus a `TranscriptDocument`; route attempt,
  asset regions, block identities, schema version, base version, confirmation lock, and hash are
  validated server-side.
- `POST /confirm-transcript`: strict transcript version ID and client-observed SHA-256; response
  returns immutable confirmation ID/version/hash/timestamp.
- `POST /mock-evaluation`: request becomes `{confirmedTranscriptVersionId}`. The server loads the
  exact owned confirmation and document. Response remains visibly synthetic.
- All request/response/provider models forbid unknown fields and unsupported enums.
- OpenAPI is authoritative; TypeScript declarations are regenerated. Handwritten browser guards
  validate all nested runtime data before any transcript/warning/region is rendered.
- Stable errors use the existing safe envelope and the finite codes listed in Design.

## Database and migration

Migration `20260827_0003` is required because durable run metadata and exact confirmation are M6 exit
conditions. It will add only transcription-scope tables:

- `attempt_assets`: UUID primary key, `attempt_id` and `solution_upload_id` restrictive foreign keys,
  created time, unique `(attempt_id, solution_upload_id)`, an upload lookup index, and an immutable
  update/delete trigger. It stores no image bytes.
- `prompt_versions`: UUID primary key, operation, version, exact application prompt text,
  `prompt_sha256`, schema version, created time, unique operation/version and hash constraints, and an
  immutable trigger.
- `ai_model_runs`: UUID primary key, attempt-asset/prompt foreign keys, configured provider and exact
  model snapshot, schema and pricing versions, globally unique idempotency key, request fingerprint,
  status, schema-attempt count constrained to one or two, nullable terminal latency/token/cost/error
  metadata, and start/finish times. An `(attempt_asset_id, created_at)` index supports owned state
  reload; a partial unique index prevents two `processing` runs for one asset. Only controlled status
  updates occur; no raw response or error body is stored.
- `transcript_versions`: UUID primary key, attempt/source-run/optional-parent foreign keys, positive
  per-attempt version, strict validated JSON document, schema version, SHA-256, origin, optional
  learner creator, and created time. Unique attempt/version, attempt/hash, and source-run constraints
  support deterministic replay. Rows are append-only and immutable.
- `transcript_confirmations`: UUID primary key, unique attempt and transcript-version foreign keys,
  copied transcript SHA-256, confirming user, and confirmed time. Rows are append-only and immutable.

Existing attempts and uploads receive no backfill and remain valid. All new tables start empty; no
nullable M6 column is added to an existing table. Authorization follows
`confirmation/version -> attempt -> study_profile -> user` and
`attempt_asset -> solution_upload -> user`, with both paths required to match before provider access.
Attempts remain pinned to immutable problem versions.

Indexes correspond only to exact queries: owned attempt asset lookup, latest run for reload,
in-flight exclusion, per-attempt transcript version/hash lookup, and one confirmation per attempt.
No evaluation, learner-state, workflow, planner, vector, or per-exam table is added.

Rollback order is: stop M6 writes, export M6 audit records if retention is required, deploy the M5
application (which ignores additive M6 tables), remove immutable triggers/indexes in reverse
dependency order, then drop confirmations, transcript versions, model runs, prompt versions, and
attempt assets. Downgrade does not alter attempts, uploads, content, profiles, or targets, but it
permanently deletes all M6 transcripts/run metadata/confirmations; this is material data loss and is
not a safe production rollback without backup and owner authorization. Upgrade, existing-data,
populated downgrade, and re-upgrade tests will prove behavior.

Provider-run, transcript, and upload retention is not yet approved. M6 will not invent a deletion
window. Records and object references remain until the privacy action list receives an owner-approved
policy; the benchmark uses repository-owned synthetic data only.

## Security and privacy

- Every attempt, upload, source-image download, run, transcript version, confirmation, and mock
  evaluation route requires the existing invitation session and joins to the owning user.
- The backend loads bytes only after matching the owned attempt, owned upload, ready status, verified
  MIME, verified size, and attempt-asset relationship. A bounded object read uses the internal storage
  endpoint; the provider never receives a browser URL or object-storage credentials.
- Browser source-image display uses an owned, short-lived object-storage download URL. Provider API
  credentials never appear in it. The URL is not persisted in PostgreSQL or provider metadata.
- Provider keys are `SecretStr` server settings. They are never committed, returned, included in
  OpenAPI examples, logged, embedded in client bundles, or accepted from request payloads.
- No raw provider response/error, hidden reasoning, chain-of-thought, image bytes, or arbitrary
  provider metadata is stored. Logs use run IDs and stable safe application error codes.
- Development, tests, recorded response shapes, and benchmarking use only committed clearly
  synthetic/non-personal images. Real student/minor uploads are prohibited.
- Provider data handling is not approved for production. The benchmark report will cite facts and
  list account-level zero-retention controls separately from defaults; it will not claim that a
  provider configuration is active unless evidence exists.
- Current official facts for owner comparison:
  - OpenAI states API data is not used for training unless opted in, while default abuse-monitoring
    logs may retain content for up to 30 days; Zero Data Retention and Modified Abuse Monitoring
    require approval in its [API data controls documentation](https://developers.openai.com/api/docs/guides/your-data).
  - Anthropic states commercial API inputs/outputs are deleted within 30 days by default subject to
    exceptions, with Zero Data Retention available by agreement, and API data is not used for model
    training unless the organization opts into the Development Partner Program in its
    [retention](https://privacy.anthropic.com/en/articles/7996866-how-long-do-you-store-my-organization-s-data)
    and [training](https://privacy.anthropic.com/en/articles/7996885-how-do-you-use-personal-data-in-model-training)
    documentation.
  - Google states paid Gemini API prompts/responses are not used to improve products; default abuse
    monitoring and stateful features have documented retention caveats, while approved Zero Data
    Retention changes handling in its
    [Gemini API data-handling documentation](https://ai.google.dev/gemini-api/docs/zdr).

## Test plan

### Unit

- Strict ready/uncertain provider unions; text/math discrimination; canonical order; unique stable IDs;
  finite warning mappings; normalized region bounds/references; unknown field/variant/HTML/Markdown/
  URL/code/dictionary rejection; empty and over-limit values.
- Faithful preservation of the subtle synthetic mathematical error, cross-outs/insertions, Vietnamese
  text, same-line text/math alternation, incomplete work, and alternative valid method.
- Exactly one schema repair, success on the second payload, exhaustion after two payloads, and no
  third call.
- Timeout, rate limit, transport, provider rejection, invalid media, empty, malformed, uncertainty,
  and metadata mismatch mapping without fabricated transcripts or raw errors.
- Configured provider/model/prompt/schema/pricing identity overrides any raw provider claim.
- Deterministic fake and recorded approved-provider response shapes return the same application type.
- Idempotency/concurrency decision functions and application-owned cost calculation.

### Integration and database migration

- Upgrade from M2/M5 schema to M6 with existing users/profiles/targets/attempts/uploads unchanged;
  empty-table backfill behavior; all nullability/check/unique/FK/partial-index/trigger contracts;
  populated downgrade data-loss behavior and re-upgrade.
- Authentication required for every M6 endpoint.
- Attempt/upload same-user ownership, cross-user isolation without resource disclosure, verified
  upload requirement, actual internal object read, and immutable problem-version pinning.
- Attempt-asset, prompt-version, model-run, transcript-version, warning/region, metadata, and
  confirmation persistence and reload.
- Same idempotency key during/after a run, distinct concurrent key exclusion, completed replay,
  manual retry only after retryable failure, and zero duplicate fake calls.
- No transcript row after timeout, rate limit, provider rejection, uncertainty, empty output, or
  schema exhaustion.
- Correction creates a new version, repeated identical save deduplicates, editing after confirmation
  is rejected, exact confirmation is idempotent, and conflicting confirmation is rejected.
- Evaluation before confirmation, mismatched hash/version/attempt, and cross-user downstream access
  are rejected; the confirmed exact version drives only the synthetic M5 evaluator.

### API/OpenAPI contract

- Exact request/response/error schemas, discriminators, forbidden fields, stable enums, region bounds,
  confirmation identity, and no provider selection fields.
- Regenerated OpenAPI and generated TypeScript declarations compare cleanly.
- Browser guards reject every malformed nested state before mounting transcript UI.

### Frontend component and math regression

- Loading; warnings/regions; uncertainty; retryable; permanent; invalid-schema terminal; and ready
  states, with no transcript DOM before complete validation.
- Native-caret text correction, visual MathLive editing, formula insertion/deletion/reordering,
  alternating text/math, safe paste, unique IDs, save version, exact hash confirmation, and locked
  confirmed state.
- Source-free KaTeX failure for malformed/unsupported/trusted commands and recovery after correction.
- Phone tab/desktop split source-image presentation, keyboard/touch region selection, and accessible
  messages.
- M5 multi-target plan and explicit synthetic evaluation/hint/retry/concept/summary regressions.

### Browser/end-to-end and manual device QA

- Run the complete fake-provider invite/profile/two-target/plan/attempt/upload/transcribe/correct/
  confirm/mock-evaluate/hint/retry path across all five projects.
- Exercise touch and keyboard operation, source image/warning regions, visual math correction,
  confirmed version/hash, reload boundary, mock-evaluation labeling, and document-level horizontal
  overflow.
- Run a focused retryable fake failure followed by explicit retry without duplicate provider calls.
- Capture and inspect screenshots for every project at correction warnings, MathLive editing,
  confirmation, and synthetic evaluation labeling.

### Benchmark

- Run only after owner approval and credentials with the guarded command, exact 10-file manifest,
  SHA-256 fixture/prompt/schema hashes, exact model snapshot, and maximum 20-call/$approved cap.
- Record expected and validated flat transcripts, text edits, visual math edits, ordering errors,
  preserved mathematical errors, warnings/regions, schema retries/failures, latency, usage, per-run
  and total cost, documented data-handling facts, limitations, and observed failure modes.
- Report measurements without manufacturing a production pass/fail gate.

## Manual QA

1. Start isolated M6 services with deterministic fake mode and seed the five synthetic invitation
   identities.
2. In each Playwright viewport, authenticate, create/load one profile with the two existing target
   records, build the deterministic plan, and open the M4 problem. Confirm both supported-target IDs
   and the pinned problem version.
3. Upload the corresponding synthetic fixture, observe presign/upload/verification/transcription
   loading, and confirm the owned image remains visible in correction.
4. Inspect warning copy and source-region overlay; operate it by touch and keyboard.
5. Correct Vietnamese/plain text at the native caret and correct malformed mathematics in MathLive.
   Confirm raw LaTeX and provider data are absent from the rendered DOM.
6. Save the correction and confirm the displayed exact transcript version/hash. Repeat confirmation
   and verify idempotence; attempt another edit and verify the locked response.
7. Continue to the M5 evaluation and verify every heading/callout says deterministic/synthetic/mock,
   then request hints, retry the same immutable problem version, inspect the concept, and finish.
8. Exercise fake uncertainty, timeout/rate-limit retryable, permanent, empty, and two-invalid-schema
   states; verify no transcript appears and retry is offered only where allowed.
9. Reload after a persisted transcript and confirm the profile/targets reload while current SPA
   navigation resets; use the authenticated state API test/debug step to verify the exact persisted
   run/version/confirmation remains.
10. Check keyboard focus, 44 px minimum controls, touch operation, KaTeX fallbacks, screenshot output,
    and `scrollWidth <= clientWidth + 1` in every project.

## Rollout and rollback

- Default local/test mode uses the deterministic fake. Real mode requires explicit server-only
  provider, exact model, API key, timeout, pricing version, and synthetic-data acknowledgement.
- Production startup rejects fake mode, missing secrets, model aliases that are not the approved
  snapshot, development credentials, and benchmark enablement. This does not imply provider privacy
  approval; deployment remains blocked by the privacy action list.
- Apply migration before deploying M6 code. Existing M5 records are untouched and old M5 code ignores
  additive tables, permitting application rollback before database downgrade.
- Monitor only aggregate stable run status/error/latency/usage/cost fields keyed by internal run ID;
  do not log input image, transcript text/math, provider bodies, signed URLs, or secrets.
- Disable real mode and return to fake/internal testing to stop provider calls. A database downgrade
  requires owner authorization and backup because it deletes M6 audit/transcript data.

## Branch and commit plan

1. `docs: add Milestone 6 change plan`
2. `test: specify strict transcription provider boundary`
3. `feat: add deterministic transcription adapter`
4. `test: specify durable transcript lifecycle`
5. `feat: persist transcription runs and confirmations`
6. `test: specify transcription correction states`
7. `feat: connect multimodal correction journey`
8. `feat: add approved multimodal provider adapter`
9. `test: cover multimodal journey on phone and tablet`
10. `docs: record Milestone 6 benchmark and verification`

Commits may be split further to keep each green and understandable; they will not be squashed locally.

## Conflict coordination

Owned shared contracts/files are the migration head, Alembic model imports, `api.py`, settings,
storage, M5 static-journey schemas/service, generated OpenAPI/TypeScript declarations, root Makefile
and package formatting list, main journey component/state/API, transcript editor/state, global CSS,
M5 E2E spec, README, and permanent architecture/privacy/evaluation docs. Added M6 directories and
fixtures are exclusively owned by this branch.

No other active worktree/branch contract was inferred. Before each shared-contract edit and before
handoff, inspect current `origin/main`. If another branch changes these contracts, coordinate and
integrate its contract first. Any conflict that changes behavior/public schema will stop execution,
be documented here, be resolved deliberately, and trigger all affected tests. Integration order is
remote shared-contract change first, then M6 migration/API generation, then frontend consumers.

## Risks

- Provider/model remains unapproved. Mitigation: no provider implementation or call before explicit
  owner selection.
- Real handwriting transcription can silently correct mathematical mistakes. Mitigation: prompt,
  error-preservation fixtures, expected-transcript comparison, correction burden report, and no
  release gate claim.
- Strict provider schemas may not cover every response shape. Mitigation: narrow versioned schema,
  exactly one repair, terminal failure, and recorded real-shape contract tests.
- Duplicate clicks could incur cost. Mitigation: persisted idempotency key, partial in-flight unique
  constraint, terminal replay, and no transport retries.
- Synchronous provider calls may outlive client navigation. Mitigation: bounded timeout, persisted
  run lifecycle, duplicate replay, and authenticated status reload. SSE remains unnecessary.
- A process crash after a provider call but before final persistence can leave `processing`. Mitigation:
  mark stale processing runs safely retryable by bounded age without silently launching a new call;
  document that at-most-once billing cannot be guaranteed across an unknown provider/network result.
- JSONB could contain invalid legacy data. Mitigation: validate before write and every read, immutable
  hashes, migration constraints, and terminal safe error rather than render.
- Source regions can leak or reference another image. Mitigation: application-stamped attempt asset
  IDs and ownership/bounds validation at provider, persistence, API, and browser boundaries.
- Provider retention/configuration may not be suitable for minors. Mitigation: synthetic-only calls,
  documented official facts, no suitability claim, and separate owner privacy approval.
- Migration downgrade destroys M6 records. Mitigation: additive upgrade, explicit backup/export,
  owner-approved downgrade only, and populated downgrade tests.
- Frontend changes can regress M3 editing or M5 multi-target behavior. Mitigation: preserve existing
  public editor operations and run focused plus full five-project regressions.
- Benchmark costs can exceed estimates if image or output tokens are larger. Mitigation: fixed
  fixture manifest, per-call output cap, preflight budget, 20-call ceiling, and hard application USD
  ceiling.

## Progress

- [x] Repository inspected
- [ ] Plan reviewed
- [x] Branch created from current main
- [ ] Tests written or updated
- [ ] Implementation complete
- [ ] Documentation updated
- [ ] Relevant checks pass
- [ ] Diff reviewed
- [ ] Branch rebased on current main
- [ ] Conflict resolution re-tested
- [ ] Handoff summary written

## Decisions

- 2026-08-27: Published M5 is present on `origin/main` at the required commit, so M6 may be based on
  that remote commit.
- 2026-08-27: Use a separate clean worktree because the shared checkout contains unrelated untracked
  work that must not be inspected or changed.
- 2026-08-27: Ordinary HTTP is selected; current architecture does not justify SSE.
- 2026-08-27: Durable M6 persistence is required. Confirmation is a separate immutable row so exact
  confirmation does not mutate an append-only transcript version.
- 2026-08-27: Editing after confirmation is rejected rather than introducing a workflow transition.
- 2026-08-27: The M5 mock evaluator will accept only a confirmed durable transcript version ID and
  remain clearly synthetic.
- 2026-08-27: No frontend dependency is proposed. Direct provider HTTP through the already locked
  `httpx` client is preferred over a provider SDK, contingent on dependency approval.
- 2026-08-27: Provider and exact model remain an owner decision. Viable inspected options are OpenAI
  `gpt-5.4-2026-03-05`, Anthropic `claude-sonnet-5`, and Google `gemini-3.5-flash`. No option is
  selected by this plan.

## Discoveries

- The M5 final commit is exactly the current published `main` tip, not merely an unpublished local
  commit.
- The existing upload verification trusts object-storage MIME metadata and exact size; M6 needs a
  bounded internal byte read before provider invocation.
- M5 already demonstrates exactly-one schema retry, but it is tied to synthetic mock response models
  and does not persist attempts/runs.
- The existing API client combines generated declarations with manual strict runtime parsing. M6 must
  extend both, because generated TypeScript alone does not validate network values.
- Persisting a confirmed document inside an updated transcript row would violate append-only
  transcript versions; a separate confirmation table is the smaller auditable design.
- `httpx` is already version-locked for tests, so direct provider HTTP can avoid a provider SDK and a
  new transitive graph, although moving it into production requirements is still an approval-gated
  dependency change.

## Verification evidence

- `git ls-remote https://github.com/minhup/math-coach.git refs/heads/main` — returned
  `dbfd8162a27f2f63fecfcdbe63759d64eab56c24 refs/heads/main`.
- `git fetch https://github.com/minhup/math-coach.git +refs/heads/main:refs/remotes/origin/main` —
  succeeded after the configured SSH remote failed authentication.
- `git merge-base --is-ancestor dbfd8162a27f2f63fecfcdbe63759d64eab56c24 origin/main` — exit 0.
- `git worktree add -b feat/m6-multimodal-transcription
/home/minh/dev/math-coach-m6-transcription origin/main` — succeeded at the M5 commit.
- Read-only repository, documentation, migration, configuration, generated-contract, backend,
  frontend, package, test, and Playwright inspection completed as listed in Current-state findings.
- No test command, dependency change, fixture generation, provider implementation, or provider
  network call has been run yet. Existing M5 verification evidence is documented in its completed
  ChangePlan and device report; it is not restated as a new M6 test result.

## Result

Planning and repository verification are complete. Implementation is blocked exactly as required by
the provider decision gate: the project owner must select one provider and exact model, approve the
10-fixture/20-call benchmark ceiling and maximum model cost, and approve promoting
`httpx==0.28.1` to the server runtime. No implementation test/code, dependency, real fixture, or paid
provider call has been created.
