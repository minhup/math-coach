# Milestone 1 engineering foundation

## Metadata

- Status: complete
- Owner: Project owner
- Branch: `feat/m1-engineering-foundation`
- Base commit: `94bb36c41263b6ea6e7b8a13185b001ed7a3f318`
- Related milestone: Milestone 1 — Repository and engineering foundation
- Related issue/ticket: None
- Started: 2026-08-25
- Last updated: 2026-08-25

## Context

Milestone 0 is merged into `origin/main` and authorizes internal implementation with synthetic/non-personal fixtures. The repository contains product and governance documentation but no application code, dependency manifests, database migration, object-storage setup, tests, CI, or root development commands. Milestone 1 must establish a testable web/API foundation and exit with an internal user able to sign in, open the responsive interaction shell, and upload a synthetic image.

## Goal

Deliver one locally reproducible and CI-verified foundation containing:

- a Next.js responsive interaction shell;
- a FastAPI/Pydantic API;
- PostgreSQL schema migrations for invite-only users, sessions, and uploads;
- S3-compatible object storage with short-lived signed upload URLs;
- database-backed invite login and authorization;
- structured request logging;
- generated TypeScript API types from FastAPI OpenAPI;
- the complete root `make` command contract;
- unit, integration, migration, component, and browser tests.

An internal test user must be able to authenticate with the documented development invite, select a synthetic/non-personal image, preview it, upload it directly to local object storage through a signed URL, and see a verified completion state on all approved emulated device classes.

## Non-goals

- Implement study profiles, exam targets, exam configuration, or multi-target planning.
- Import or publish real examination content.
- Implement attempts, transcription, grading, hints, learner state, reviews, rewards, MathLive, KaTeX, or JSXGraph.
- Integrate an AI provider.
- Collect real student or minor data.
- Implement production deployment, production secret management, rate limiting, EXIF removal, deletion/export, full PWA behavior, or external-pilot operations.
- Implement direct camera-permission testing, Android Emulator setup, Apple Simulator setup, or physical-device testing.

## User-visible behavior

- A concise invite-code login screen explains that the environment uses synthetic/non-personal work only.
- A valid development invite establishes an HTTP-only application session and opens the interaction shell.
- Invalid or expired invites produce a stable, retryable error without exposing internal details.
- The shell presents the photo-to-feedback workflow and clearly identifies which later steps are not yet active.
- A user can choose JPEG, PNG, or WebP input, see a local preview, replace it, and upload it.
- Loading, retryable failure, permanent validation failure, and upload success are distinct UI states.
- The shell is usable at the approved compact phone, Pixel 7, iPhone 13, and iPad Pro 11 emulation sizes.

## Current-state findings

- Milestone 0 was fast-forwarded to `origin/main` at `94bb36c` before this branch was created.
- `feat/m1-engineering-foundation` was created from that exact `origin/main`; the working tree was clean.
- The repository has documentation only. There are no application directories, manifests, migrations, tests, CI workflows, root `Makefile`, or validation commands.
- No active remote implementation branch or overlapping ChangePlan was found. The only non-main remote branch is the already-merged Milestone 0 documentation branch.
- Available local tooling: Node `24.14.0`, npm `11.9.0`, Python `3.12.12`, uv `0.11.30`, Docker `29.6.2`, Docker Compose `5.3.1`, Make `4.3`, Git, and ripgrep.
- No pnpm, Yarn, local `psql`, Playwright CLI/browser, Chromium, or Apple simulator is installed.
- The Docker daemon is available, so PostgreSQL and MinIO-compatible development services can run without a host `psql` installation.
- Current Next.js documentation requires Node 20.9 or newer; the installed Node version satisfies it.
- Playwright requires version-matched browser binaries and can install Chromium and WebKit for the approved emulation matrix.
- No existing test command can be run because the repository has no application or test tooling yet.

## Design

### Repository and dependency management

Use npm workspaces for TypeScript packages because npm is already installed and an additional JavaScript package manager would add no product value. Use a service-local uv project and lockfile for Python. Commit both lockfiles.

Use current stable releases resolved on the implementation date and record the exact versions after lock generation. Required dependency groups and rationale:

| Group                                                 | Need                                               | License/size/alternatives                                                                                               |
| ----------------------------------------------------- | -------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| Next.js, React, React DOM                             | Product-plan web stack and App Router              | MIT; framework-sized client/server dependency; a custom React/Vite stack would duplicate routing and server integration |
| FastAPI, Pydantic, pydantic-settings, Uvicorn         | Product-plan API and strict boundary validation    | MIT/BSD; small-to-moderate Python runtime; Flask/Django would conflict with the approved FastAPI contract               |
| SQLAlchemy asyncio, asyncpg, Alembic                  | Typed persistence and migration contract           | MIT/Apache-2.0; moderate server-only dependencies; raw SQL would duplicate transaction and migration plumbing           |
| MinIO Python SDK                                      | S3-compatible bucket operations and signed URLs    | Apache-2.0; server-only; boto3 is broader and larger than the MVP needs                                                 |
| Ruff, mypy, pytest, pytest-asyncio, HTTPX             | Python format, lint, types, unit/integration tests | permissive licenses; development-only                                                                                   |
| TypeScript, ESLint, Prettier, Vitest, Testing Library | Frontend types, format, lint, and component tests  | permissive licenses; development-only                                                                                   |
| Playwright                                            | Chromium/WebKit end-to-end and device emulation    | Apache-2.0; large version-matched Docker image justified by the approved device matrix                                  |
| openapi-typescript                                    | Generated frontend contract from FastAPI OpenAPI   | MIT; development-only; avoids incompatible hand-maintained duplicate request/response types                             |

Do not add a component framework, CSS framework, state-management library, authentication framework, ORM wrapper, or generic monorepo orchestrator in this milestone.

### Runtime boundaries

```text
Browser
  ├─ same-origin /api requests through Next.js rewrite
  └─ short-lived signed PUT directly to object storage

Next.js
  └─ responsive shell and API proxy only

FastAPI
  ├─ Pydantic request/response validation
  ├─ invite/session authorization
  ├─ upload ownership and completion verification
  ├─ async SQLAlchemy boundary
  └─ MinIO object-storage boundary

PostgreSQL
  └─ users, pilot_invites, user_sessions, solution_uploads

S3-compatible storage
  └─ image bytes only; PostgreSQL stores metadata and object keys
```

### Authentication

- Seed a documented development-only invite from environment configuration.
- Store only invite-code and session-token SHA-256 digests.
- Link an invite to one user on first use; repeated development login returns the same internal user.
- Store opaque random sessions in PostgreSQL with expiry and revocation timestamps.
- Send the raw session only in an HTTP-only, SameSite=Lax cookie; `Secure` is configurable and must be enabled outside local HTTP.
- Every upload endpoint resolves and authorizes the current user.
- Return stable error codes and concise messages through one API error envelope.

### Upload lifecycle

1. The authenticated browser requests a signed upload with file name, MIME type, and byte size.
2. FastAPI validates the request, records a `pending` upload owned by the user, and returns a five-minute signed PUT URL.
3. The browser uploads bytes directly to object storage.
4. The browser calls completion.
5. FastAPI checks object existence, size, and content type before marking the upload `ready`.
6. A mismatch deletes the object when possible, marks the record `rejected`, and returns a stable error.

Only JPEG, PNG, and WebP files from 1 byte through 10 MiB are accepted. Image bytes never enter PostgreSQL. EXIF removal and production retention are explicitly Milestone 11 work; only synthetic/non-personal fixtures are permitted now.

### Responsive interaction shell

Use semantic HTML and repository-owned CSS. The shell keeps the photo workflow central, shows the future transcript/feedback steps without pretending they work, and avoids desktop-only interaction. The compact phone uses a single column; tablet widths use a workflow rail plus upload workspace. All state transitions have text labels in addition to color.

### API contract generation

Export FastAPI OpenAPI deterministically, generate TypeScript declarations with `openapi-typescript`, and fail `make check` when regenerated output differs. Frontend API functions consume those generated types rather than redeclaring backend payloads.

### Logging

Use Python standard-library JSON logging plus request middleware. Record request ID, method, route, status, and duration. Do not log invite codes, session tokens, signed URLs, cookies, or image bytes.

### Alternatives rejected

- In-memory authentication would not verify the PostgreSQL/session foundation.
- Uploading image bytes through Next.js or PostgreSQL would violate the object-storage boundary.
- A hand-maintained TypeScript API model would risk divergence from Pydantic/OpenAPI.
- Tailwind or a component library is unnecessary for one focused shell and would add framework surface before two concrete uses.
- Full application containers are not needed for the local development exit criterion; Docker Compose owns PostgreSQL and object storage while the web/API run with native toolchains.

## Multi-exam impact

This milestone does not create study profiles, exam targets, exam progress, shared skill state, or daily-plan balancing. It must not introduce a singular `target`, `target_exam_id`, or implicit primary-exam field. The shell may describe future combined planning but does not persist or fabricate exam data. Milestone 2 will add `study_profile -> student_exam_targets[]` on this foundation.

## Files and components

Owned by this branch:

- `docs/changes/2026-08-25-m1-engineering-foundation.md` — this execution record.
- `README.md` — setup, commands, architecture, and development-only data boundaries.
- `.env.example`, `.gitignore`, `.dockerignore` — local configuration and generated-file boundaries.
- `.github/workflows/ci.yml` — pull-request/push validation.
- `Makefile` — required root command contract plus documented development helpers.
- `compose.yaml`, `infra/postgres/init.sql` — PostgreSQL and S3-compatible local dependencies.
- `package.json`, `package-lock.json`, root TypeScript/format/lint/Playwright configuration — npm workspace and shared frontend tooling.
- `apps/student-web/AGENTS.md` and `CLAUDE.md` — version-generated Next.js agent guidance retained per the installed framework.
- `apps/student-web/**` — Next.js shell, styles, API boundary, and component tests.
- `services/api/**` — FastAPI app, auth, uploads, logging, database, migration, seed/export scripts, and tests.
- `packages/api-client/**` — generated OpenAPI TypeScript declarations.
- `tests/e2e/**` — device-emulated login and signed-upload journeys.
- `content/README.md` and `scripts/validate_content.py` — explicit Milestone 1 no-content validation contract pending Milestone 2 schemas.

No existing shared schema or implementation component exists. Future Milestone 2 branches must rebase after this foundation before modifying database models, migrations, generated API types, or root configuration.

## API and schema changes

Planned API surface under `/api/v1`:

```text
GET    /health
POST   /auth/pilot-login
POST   /auth/logout
GET    /auth/me
POST   /uploads/presign
POST   /uploads/{upload_id}/complete
GET    /uploads/{upload_id}
```

All non-health responses use explicit Pydantic models. Errors use:

```json
{
  "error": {
    "code": "stable_code",
    "message": "Concise safe message",
    "requestId": "optional-request-id"
  }
}
```

The generated TypeScript client schema is derived from the committed OpenAPI document. No AI or content schema is introduced.

## Database and migration

Create one Alembic migration for:

- `users`: internal account identity and status;
- `pilot_invites`: invite digest, linked user, usage policy, expiry, and status;
- `user_sessions`: session digest, user, expiry, revocation, and timestamps;
- `solution_uploads`: owner, object key, original name, expected/verified metadata, state, and timestamps.

Indexes support invite lookup, active session lookup, upload ownership, and upload status. All identifiers are UUIDs generated by the application. The migration starts from an empty database, has a tested downgrade, and has no backfill or existing-data risk. Rollback removes only these new empty-foundation tables; image objects must be removed separately if rollback follows manual use.

## Security and privacy

- Use development-only synthetic/non-personal images.
- Commit no real invite, provider key, database password, or object-storage secret.
- `.env.example` contains conspicuous local-only placeholders; CI supplies isolated test values.
- Hash invite codes and session tokens before persistence.
- Keep sessions HTTP-only and authorize each user-owned upload.
- Validate declared and stored file size/type.
- Use five-minute signed upload URLs.
- Keep credentials and signing server-side.
- Redact authentication and signed-upload material from logs.
- Do not claim production privacy, retention, malware, EXIF, rate-limit, or incident readiness in Milestone 1.

## Test plan

### Unit

- Invite/session digest behavior and session expiry/revocation.
- Upload request validation and object-key construction.
- Stable API error envelope.
- Frontend login/upload state transitions with mocked API and object-storage calls.

### Integration and API contract

- Apply Alembic upgrade, downgrade, and re-upgrade against PostgreSQL.
- Seed and reuse the development invite without storing its raw code.
- Valid login creates an authorized session; invalid invite fails safely; logout revokes it.
- Unauthenticated upload requests are rejected.
- Presign creates an owned pending record.
- Completion verifies a real MinIO object and moves it to `ready`.
- Wrong user cannot read or complete another user's upload.
- Invalid type/size is rejected and object bytes are not stored in PostgreSQL.
- OpenAPI export is stable and the generated TypeScript declaration is current.

### Frontend component

- Invite form loading and error behavior.
- File selection, preview metadata, replacement, validation, upload progress, retry, and success.
- Future workflow steps are visibly inactive rather than falsely successful.

### Browser/end-to-end

Run the authenticated synthetic-image upload journey on:

- compact Chromium at `360 × 640` with touch;
- Playwright Pixel 7 Chromium;
- Playwright iPhone 13 WebKit;
- Playwright iPad Pro 11 WebKit in portrait and landscape.

Assert login, shell visibility, file preview, signed PUT, completion, success state, no horizontal overflow, and usable primary controls.

### Content validation

`make content-validate` confirms that no publishable content package is present in Milestone 1 and explains that schema validation begins in Milestone 2. It must reject unexpected content files rather than silently accepting them.

### Acceptance criteria

- Every required root `make` target exists and is documented.
- `make check` runs all non-destructive format, lint, type, unit, integration, content, and browser checks.
- A clean setup can start PostgreSQL and object storage, migrate, seed, and run the web/API.
- The full signed-upload journey passes on every approved emulation project.
- The frontend builds for production and the API OpenAPI schema exports deterministically.
- No raw secret, image byte payload, singular exam-target assumption, or application-code change outside the owned paths appears in the diff.

## Manual QA

1. Copy `.env.example` to `.env` if local overrides are needed; otherwise use documented development defaults.
2. Run `make setup`.
3. Start the API and web using the documented commands.
4. Open `http://localhost:3000` at `360 × 640`.
5. Enter the documented development invite code.
6. Confirm the responsive shell opens and labels the upload step active while later steps remain upcoming.
7. Select a synthetic JPEG/PNG/WebP under 10 MiB; confirm preview and metadata.
8. Replace it once, then upload it.
9. Confirm loading and verified-success states are clear.
10. Try an unsupported or oversized file and confirm a concise correctable message.
11. Log out and confirm the shell is no longer accessible.
12. Repeat layout checks at Pixel 7, iPhone 13, and iPad Pro 11 portrait/landscape through Playwright.

Expected outcome: the complete Milestone 1 login-and-upload exit journey works with synthetic data and never claims that transcription or feedback is active.

## Rollout and rollback

This is an internal development foundation with no production rollout or existing data migration. Merge order: Milestone 0, then this branch, then Milestone 2. Roll back by reverting this branch and removing the local Compose volumes only when local development data may be discarded. Never point the provided development defaults at production services.

## Branch and commit plan

1. `e26052e docs: add Milestone 1 change plan`
2. `75d2b80 feat: add invite authentication and signed uploads`
3. `d44b86f feat: add responsive interaction shell`
4. `fc8ce07 chore: add root validation and CI workflow`
5. `e7d5d50 docs: record Milestone 1 implementation`
6. `docs: record final Milestone 1 verification`

## Conflict coordination

This branch owns all new root application configuration plus `apps/student-web/`, `services/api/`, `packages/api-client/`, `tests/e2e/`, `infra/postgres/`, `scripts/validate_content.py`, `content/README.md`, and this ChangePlan. No overlapping active implementation branch was visible after fetching. Root configuration, the first migration, and generated OpenAPI types become shared contracts after merge; Milestone 2 must branch from this work rather than editing parallel copies. Integration order is Milestone 0 → Milestone 1 → Milestone 2.

## Risks

- The milestone breadth could create an oversized first commit. Mitigation: keep the planned commits independently testable and avoid later-domain behavior.
- Browser-signed uploads may fail because of object-storage hostname or CORS differences. Mitigation: separate internal/public endpoints, configure explicit local CORS, and exercise the real PUT in browser tests.
- Session-cookie behavior may differ through the Next.js proxy. Mitigation: use same-origin browser requests and verify cookie login/logout through Playwright.
- WebKit system dependencies may be unavailable on developer machines without administrator access. Mitigation: run Chromium and WebKit from Playwright's version-matched Docker image while the application servers run locally.
- Generated OpenAPI types may drift. Mitigation: regenerate and compare them in `make check`.
- Local development credentials may be mistaken for production configuration. Mitigation: conspicuous names, startup validation outside development, and README warnings.
- Migration/integration tests could mutate a developer database. Mitigation: use a dedicated `math_coach_test` database created by the Compose initialization script.

## Progress

- [x] Repository inspected
- [x] Plan reviewed
- [x] Branch created from current main
- [x] Tests written or updated
- [x] Implementation complete
- [x] Documentation updated
- [x] Relevant checks pass
- [x] Diff reviewed
- [x] Branch rebased on current main
- [x] Conflict resolution re-tested
- [x] Handoff summary written

## Decisions

- 2026-08-25: Use npm workspaces and uv because both are available in the approved environment and avoid an unnecessary monorepo orchestrator.
- 2026-08-25: Run PostgreSQL and MinIO-compatible storage in Docker Compose while running Next.js/FastAPI through native locked toolchains.
- 2026-08-25: Use database-backed opaque sessions instead of JWTs so revocation is explicit and no client-held authorization state becomes authoritative.
- 2026-08-25: Use a signed PUT followed by server-side completion verification so image bytes remain outside the API and PostgreSQL.
- 2026-08-25: Keep the interaction shell application-owned and deterministic; do not add AI or pretend future transcript/feedback states are available.
- 2026-08-25: Use the official Playwright `v1.62.1-noble` image for browser execution so the approved Chromium/WebKit matrix does not require workstation-level package installation.

## Discoveries

- The current environment has Docker Compose as a Docker CLI plugin even though the legacy `docker-compose` executable is absent.
- A host `psql` client is unnecessary because migration tooling uses asyncpg and database administration can run inside the PostgreSQL container.
- The approved phone/tablet browser matrix requires both Chromium and WebKit binaries; no browser is preinstalled.
- npm's current TypeScript 7 release is outside `openapi-typescript`'s declared TypeScript 5 peer range. Use TypeScript 5.9.3 and preserve peer-dependency enforcement instead of bypassing it.
- ESLint 10 is outside several current `eslint-config-next` plugin peer ranges, and jsdom 30 requires Node 24.15 while the environment has Node 24.14. Pin ESLint 9.39.5 and jsdom 29.1.1 instead of accepting invalid or unsupported dependency trees.
- Next.js 16 generates app-local `AGENTS.md` and `CLAUDE.md` guidance and requires agents to read the version-bundled documentation before edits. The generated files are retained; `next-env.d.ts` is generated but ignored as the bundled documentation directs.
- The workstation cannot install Playwright's Linux browser libraries without an interactive sudo password. Browser execution therefore moved to the matching official Docker image; no emulation project was dropped.
- Parallel browser startup against `next dev` produced transient 403 responses for Turbopack HMR chunks. End-to-end validation now builds once and uses `next start`, which validates the production artifact and removed the race.
- The first browser upload attempt used `127.0.0.1`, which correctly failed the deliberately narrow MinIO CORS origin. The test base URL now uses the documented `http://localhost:3000` origin instead of broadening CORS.
- Component testing exposed an invisible unsupported-file error caused by rendering the alert only inside the valid-preview branch. The alert now renders at the shared upload-panel boundary.
- Visual QA exposed a descendant CSS selector overriding the header brand mark. Narrowing the selector to the tagline restored the ∑ mark across phone and tablet layouts.

## Verification evidence

- `git fetch origin --prune` confirmed Milestone 0 at `94bb36c` on `origin/main` before branch creation.
- `git status --short --branch` showed a clean `feat/m1-engineering-foundation` tracking `origin/main`.
- Tool discovery recorded Node, npm, Python, uv, Docker, Docker Compose, Make, Git, and ripgrep versions in current-state findings.
- `docker info --format '{{.ServerVersion}}'` returned `29.6.2`; the Docker daemon is available.
- `npm install` completed with zero reported audit vulnerabilities and generated the committed npm lockfile.
- `uv sync --all-groups` generated the committed uv lockfile with the exact dependencies recorded above.
- `make test-unit` passed 15 frontend component/boundary tests and 14 backend unit tests. Frontend coverage was 91.92% statements, 88.09% branches, 95.12% functions, and 91.77% lines.
- `make test-integration` applied upgrade → downgrade → upgrade → downgrade → upgrade against `math_coach_test`, then passed 7 API/PostgreSQL/MinIO integration tests.
- `make api-contract-check` confirmed the committed OpenAPI document and generated TypeScript declarations reproduce exactly.
- `make content-validate` confirmed no publishable content package is present.
- `make build` produced the optimized Next.js production build with `/` and `/_not-found` prerendered as static routes.
- `make test-e2e` passed the authenticated 68-byte synthetic PNG upload and logout journey on all 5 projects: compact Chromium, Pixel 7 Chromium, iPhone 13 WebKit, and iPad Pro 11 WebKit portrait/landscape.
- `VISUAL_QA=1 make test-e2e` captured all 5 successful layouts. Direct inspection of compact phone and iPad portrait/landscape confirmed readable hierarchy, usable controls, the corrected brand mark, success feedback, and no horizontal overflow.
- `make check` passed the complete root command contract before commit: formatting, lint, TypeScript/Python types, generated contract, content gate, production build, unit, integration, migration, and browser checks.
- `git diff --check` passed, and the complete 71-file implementation diff was reviewed before logical commits. The unrelated untracked `docs/vietnam_chuyen_toan_competitive_dataset.xlsx` was not inspected, modified, or staged.
- The required final `git fetch origin --prune` confirmed `origin/main` remained at `94bb36c`; `git rebase origin/main` reported the branch was already up to date, with no conflicts.
- The post-rebase `make check` passed again with the same production build, generated-contract/content results, 15 frontend tests, 14 backend unit tests, 7 integration tests with two complete migration downgrade/upgrade cycles, and 5 Playwright emulation projects.

## Result

Milestone 1 is complete. An internal learner can authenticate with a database-backed invite/session, open the responsive interaction shell, upload a synthetic image through a five-minute signed object-storage URL, receive server-verified completion, and sign out. The root command contract, reversible migration, generated API contract, structured logging, CI, explicit failure states, and approved phone/tablet emulation matrix are implemented and verified. No Milestone 2 domain model, real content, AI integration, or real student data was introduced.
