# Math Coach

Math Coach is an interaction-first MVP for helping students move from a photographed paper solution to a confirmed transcript and useful mathematical feedback. Milestones 1 and 2 supply the internal engineering foundation, invite login, responsive phone/tablet shell, verified synthetic-image upload, multi-exam study-profile contracts, and strictly validated versioned synthetic content. Transcription, grading, learner state, and student-facing practice arrive in later milestones.

Use synthetic or non-personal images only. The local credentials are development defaults, not production configuration.

## Architecture

The Next.js web app sends same-origin API requests through a rewrite to FastAPI. FastAPI owns authentication, profile/target/attempt authorization, typed content preview, and upload authorization. PostgreSQL stores relational learner/content metadata, while image bytes go directly to MinIO-compatible object storage and never enter PostgreSQL. TypeScript API declarations are generated from FastAPI's OpenAPI document.

Milestone 2 implements `study_profile -> student_exam_targets[]`, shared exam/skill configuration, immutable concept/problem/geometry versions, and attempts pinned to exact problem versions. Strict YAML/JSON packages are imported transactionally and only original synthetic provenance is accepted. See [the versioned content and multi-exam architecture](docs/architecture/versioned-content-and-multi-exam.md).

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

Open `http://localhost:3000`. MinIO's local console is at `http://localhost:9001`. Stop infrastructure without deleting its volumes with `make services-down`.

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

## Repository map

- `apps/student-web/` — Next.js interaction shell and component tests.
- `services/api/` — FastAPI service, Alembic migration, and Python tests.
- `packages/api-client/` — committed OpenAPI and generated TypeScript contract.
- `packages/content-schema/` and `content/packages/` — generated package schema and original synthetic versioned fixtures.
- `tests/e2e/` — Playwright phone/tablet-emulated workflow.
- `compose.yaml` and `infra/` — local PostgreSQL and object storage.
- `docs/MVP_IMPLEMENTATION_PLAN.md` — milestone sequence and product constraints.
- `docs/changes/` — branch-specific ChangePlans and verification evidence.

All future changes must follow `AGENTS.md` and create a ChangePlan before implementation.
