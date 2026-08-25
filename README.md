# Math Coach

Math Coach is an interaction-first MVP for helping students move from a photographed paper solution to a confirmed transcript and useful mathematical feedback. Milestone 1 supplies the internal engineering foundation: invite login, a responsive phone/tablet shell, and verified synthetic-image upload. Transcription, grading, hints, learner state, and content arrive in later milestones.

Use synthetic or non-personal images only. The local credentials are development defaults, not production configuration.

## Architecture

The Next.js web app sends same-origin API requests through a rewrite to FastAPI. FastAPI owns authentication and upload authorization, persists metadata in PostgreSQL, and issues five-minute signed PUT URLs for MinIO-compatible object storage. Image bytes go directly from the browser to object storage and never enter PostgreSQL. TypeScript API declarations are generated from FastAPI's OpenAPI document.

The Milestone 1 tables cover internal users, invite codes, opaque sessions, and solution uploads only. No study-profile or exam-target model is introduced; Milestone 2 will implement the required `study_profile -> student_exam_targets[]` relationship.

## Local setup

Prerequisites are Node 20.9 or newer, npm, Python 3.12, uv, Docker with Compose, and Make.

```bash
make setup
```

This installs locked JavaScript and Python dependencies, pulls the version-matched Playwright browser image, starts PostgreSQL and MinIO, applies migrations, and seeds the development invite `MATH-COACH-LOCAL`. Defaults are documented in `.env.example`; copy it to `.env` only when an override is needed.

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
make content-validate      reject content packages before Milestone 2 schemas exist
make test                  run unit, integration, and browser tests
make check                 run every non-destructive review check
```

`make api-generate` deliberately updates the committed OpenAPI document and generated TypeScript declarations after an API change. `make api-contract-check` verifies those files without modifying the working tree. Run `make check` before review.

## Repository map

- `apps/student-web/` — Next.js interaction shell and component tests.
- `services/api/` — FastAPI service, Alembic migration, and Python tests.
- `packages/api-client/` — committed OpenAPI and generated TypeScript contract.
- `tests/e2e/` — Playwright phone/tablet-emulated workflow.
- `compose.yaml` and `infra/` — local PostgreSQL and object storage.
- `docs/MVP_IMPLEMENTATION_PLAN.md` — milestone sequence and product constraints.
- `docs/changes/` — branch-specific ChangePlans and verification evidence.

All future changes must follow `AGENTS.md` and create a ChangePlan before implementation.
