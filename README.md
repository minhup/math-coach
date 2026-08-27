# Math Coach

Math Coach is an interaction-first MVP for helping students move from a photographed paper solution to a confirmed transcript and useful mathematical feedback. Milestones 1 through 6 supply the internal engineering foundation, invite login, responsive phone/tablet shell, verified synthetic-image upload, multi-exam study-profile contracts, strictly validated versioned synthetic content, controlled mathematical rendering, the visual-correction editor, the curated interactive geometry engine, a complete deterministic student journey, and server-owned multimodal transcription. Production grading, learner state, and adaptive coaching arrive in later milestones.

Use synthetic or non-personal images only. The local credentials are development defaults, not production configuration.

## Architecture

The Next.js web app sends same-origin API requests through a rewrite to FastAPI. FastAPI owns authentication, profile/target/attempt authorization, typed content preview, and upload authorization. PostgreSQL stores relational learner/content metadata, while image bytes go directly to MinIO-compatible object storage and never enter PostgreSQL. TypeScript API declarations are generated from FastAPI's OpenAPI document.

Milestone 2 implements `study_profile -> student_exam_targets[]`, shared exam/skill configuration, immutable concept/problem/geometry versions, and attempts pinned to exact problem versions. Strict YAML/JSON packages are imported transactionally and only original synthetic provenance is accepted. See [the versioned content and multi-exam architecture](docs/architecture/versioned-content-and-multi-exam.md).

Milestone 3 routes read-only typed mathematics through a bounded, source-free KaTeX failure
boundary and uses MathLive for visual correction. Its authenticated `/internal/math-correction`
route presents deterministic simulated OCR as one continuous document: typed text/math blocks are
flat and ordered, a native caret edits text in place, and formulas can be inserted at that caret or
switch from KaTeX to MathLive when activated. Whole-formula deletion requires confirmation, and
transcript confirmation produces the future authoritative grading input. Reasoning grouping happens
only after confirmation in a later milestone. The spike does not run OCR, grade, or persist work. See
[the mathematical rendering and transcript-state architecture](docs/architecture/math-rendering-and-transcript-state.md)
and [the five-project device report](docs/evaluation/m3-math-rendering-device-report.md).

Milestone 4 validates parent-derived geometry graphs and typed actions at the authoritative Pydantic
boundary and again before the browser dynamically imports JSXGraph. The shared renderer supports
the approved point, line/curve, polygon/angle, dependent-construction, and text primitives; only
explicit free points move. It preserves derived midpoint, intersection, perpendicular, parallel,
and circumcircle relationships, enforces selection allowlists, and falls back to a repository-owned
static image on invalid data or renderer failure. See
[the interactive geometry architecture](docs/architecture/interactive-geometry-engine.md) and
[the five-project geometry report](docs/evaluation/m4-geometry-device-report.md).

Milestone 5 connects invitation sign-in, one profile with multiple active examination targets, a
deterministic combined plan, immutable problem attempts, geometry, synthetic upload, strict mock
transcription, visual correction, explicit confirmation, strict mock evaluation, progressive hints,
retry, concept review, and deterministic summary. Every plan item names its exact supporting target
records. The application owns the transition and summary state; the mocks supply only validated
synthetic transcript/evaluation payloads. See the
[static student journey architecture](docs/architecture/static-student-journey.md) and
[five-project journey report](docs/evaluation/m5-static-journey-device-report.md).

Milestone 6 loads only an owned verified image, validates one complete provider response through
strict Pydantic schemas, persists immutable run/transcript/confirmation records, and presents one
continuous text/math correction document with warnings and source regions. Gemini
`gemini-3.5-flash` is the first real adapter; exact OpenAI and Anthropic alternatives plus a
deterministic fake use the same server boundary. The existing evaluation remains clearly mocked.
See the [multimodal transcription architecture](docs/architecture/multimodal-transcription.md),
[deferred benchmark report](docs/evaluation/m6-transcription-benchmark-report.md), and
[five-project device report](docs/evaluation/m6-transcription-device-report.md).

## Local setup

Prerequisites are Node 20.19 or newer, npm, Python 3.12, uv, Docker with Compose, and Make.

```bash
make setup
```

This installs locked JavaScript and Python dependencies, pulls the version-matched Playwright browser image, starts PostgreSQL and MinIO, applies migrations, and seeds the development invite `MATH-COACH-LOCAL` plus the validated synthetic content package. Defaults are documented in `.env.example`; copy it to `.env` only when an override is needed.

Start the API and web app in separate terminals:

```bash
make dev-api
make dev-web
```

Open `http://localhost:3000`. After signing in, the workspace starts the Milestone 5 synthetic
student journey. Use **Correction spike** for the standalone Milestone 3 editor, **Geometry spike**
for the all-primitives Milestone 4 surface, or **Content preview** for the typed versioned-package
path. MinIO's local console is at
`http://localhost:9001`. Stop infrastructure without deleting its volumes with
`make services-down`.

Local development and every automated test default to the deterministic M6 fake. To use Gemini later,
create an untracked root `.env` (or use a deployment secret manager) with:

```dotenv
MATH_COACH_TRANSCRIPTION_PROVIDER=gemini
MATH_COACH_TRANSCRIPTION_MODEL_SNAPSHOT=gemini-3.5-flash
MATH_COACH_GEMINI_API_KEY=replace-with-your-server-secret
```

Never put the key in a `NEXT_PUBLIC_` variable, browser request, commit, screenshot, log, or chat
message. Restart the API after changing server settings. The two optional exact alternatives use
`openai` / `gpt-5.4-2026-03-05` / `MATH_COACH_OPENAI_API_KEY`, or `anthropic` /
`claude-sonnet-5` / `MATH_COACH_ANTHROPIC_API_KEY`. Configuration availability does not approve real
learner data; use only clearly synthetic/non-personal images until privacy and provider suitability
are separately approved.

## Root command contract

```text
make setup                 install dependencies and prepare local services
make format                format owned Python and TypeScript files
make format-check          verify formatting without changing files
make lint                  run ESLint and Ruff
make typecheck             run TypeScript and Python type checks
make test-unit             run backend unit and frontend component tests
make test-integration      test migrations, PostgreSQL, auth, and real MinIO uploads
make test-e2e              run the browser journey in containerized phone/tablet emulations
make content-validate      validate packages and generated content schema without importing
make transcription-benchmark  run the separately approved, paid synthetic benchmark with explicit arguments
make test                  run unit, integration, and browser tests
make check                 run every non-destructive review check
```

`make content-schema-generate` deliberately updates the committed JSON Schema after a content-contract change. `make api-generate` updates the committed OpenAPI document and generated TypeScript declarations after an API change. Their validation commands verify generated files without modifying the working tree. Run `make check` before review.

Focused Milestone 3 checks can be run with:

```bash
cd apps/student-web
npx vitest run components/math components/transcription features/transcription --coverage=false
cd ../..
npx playwright test tests/e2e/math-correction.spec.ts
```

The Playwright command runs the same correction regression in all five configured phone/tablet
projects.

Focused Milestone 4 checks can be run with:

```bash
cd apps/student-web
npx vitest run features/geometry components/geometry --coverage=false
cd ../..
make content-validate
./scripts/run_e2e.sh tests/e2e/geometry.spec.ts
```

The E2E helper accepts optional Playwright paths and preserves the default full-suite behavior when
called without arguments. `PLAYWRIGHT_WEB_PORT` and `PLAYWRIGHT_API_PORT` may select isolated
ports for a parallel worktree; the defaults remain 3000 and 8000.

Focused Milestone 5 checks can be run with:

```bash
cd apps/student-web
npx vitest run features/journey components/journey lib/static-journey-api.test.ts --coverage=false
cd ../..
uv run --project services/api pytest services/api/tests/unit/test_static_journey_*.py
./scripts/run_e2e.sh tests/e2e/foundation.spec.ts
```

The M5 E2E flow runs the complete invite-to-summary journey in all five configured projects. Each
project uses a separate synthetic development invite identity so its profile and target records can
run in parallel safely.

## Repository map

- `apps/student-web/` — Next.js interaction shell and component tests.
- `services/api/` — FastAPI service, Alembic migration, and Python tests.
- `packages/api-client/` — committed OpenAPI and generated TypeScript contract.
- `packages/content-schema/` and `content/packages/` — generated package schema and original synthetic versioned fixtures.
- `tests/e2e/` — Playwright phone/tablet-emulated workflow.
- `compose.yaml` and `infra/` — local PostgreSQL and object storage.
- `docs/MVP_IMPLEMENTATION_PLAN.md` — milestone sequence and product constraints.
- `docs/architecture/` — durable content, rendering, and transcript-state contracts.
- `docs/evaluation/` — committed regression/device evidence and evaluation specifications.
- `docs/changes/` — branch-specific ChangePlans and verification evidence.

All future changes must follow `AGENTS.md` and create a ChangePlan before implementation.
