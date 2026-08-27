# Math Coach

Math Coach is an interaction-first MVP for helping students move from a photographed paper solution to a confirmed transcript and useful mathematical feedback. Milestones 1 through 3 supply the internal engineering foundation, invite login, responsive phone/tablet shell, verified synthetic-image upload, multi-exam study-profile contracts, strictly validated versioned synthetic content, controlled mathematical rendering, and a synthetic visual-correction spike. AI transcription, grading, learner state, and student-facing practice arrive in later milestones.

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

## Local setup

Prerequisites are Node 20.9 or newer, npm, Python 3.12, uv, Docker with Compose, and Make.

```bash
make setup
```

This installs locked JavaScript and Python dependencies, pulls the version-matched Playwright browser image, starts PostgreSQL and MinIO, applies migrations, and seeds the development invite `MATH-COACH-LOCAL` plus the validated synthetic content package. Defaults are documented in `.env.example`; copy it to `.env` only when an override is needed.

Start the API and web app in separate terminals:

```bash
make dev-api
make dev-web
```

Open `http://localhost:3000`. After signing in, use **Correction spike** to open the authenticated synthetic Milestone 3 route. MinIO's local console is at `http://localhost:9001`. Stop infrastructure without deleting its volumes with `make services-down`.

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
