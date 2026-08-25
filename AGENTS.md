# Repository Rules for Coding Agents

These instructions apply to the entire repository.

## Required reading

Before any change, read in this order:

1. `AGENTS.md`
2. `PLANS.md`
3. `docs/MVP_IMPLEMENTATION_PLAN.md`
4. the ChangePlan for the active branch
5. relevant local documentation and tests

Do not begin implementation until the repository and relevant docs have been inspected.

## Core product constraints

- A student profile may have multiple active target examinations.
- Never model, query, or render the target as a singular value unless the field is explicitly one exam record.
- The application, not the LLM, owns learner state and daily planning.
- Use typed content blocks; do not use arbitrary AI Markdown as canonical UI content.
- Students edit mathematics visually; do not require raw LaTeX.
- Geometry scenes are curated JSON; AI-generated executable geometry code is forbidden.
- The confirmed transcript is the authoritative grading input.
- Reference solutions are non-exhaustive; valid alternative solutions must be accepted.
- No general RAG or vector database is part of the MVP.
- No native wrapper, direct pen input, voice conversation, public leaderboard, or full admin product is part of the MVP.

## Mandatory change workflow

For every change:

1. Fetch and inspect the latest `main`.
2. Create a short-lived branch from the current `origin/main`.
3. Create `docs/changes/YYYY-MM-DD-<slug>.md` from `PLANS.md`.
4. Record current-state findings before editing code.
5. Define tests and acceptance criteria.
6. Implement one coherent change only.
7. Keep code, tests, schemas, migrations, and docs in the same branch.
8. Run all relevant checks.
9. Review the complete diff.
10. Rebase on current `origin/main` before handoff.
11. Resolve conflicts deliberately and rerun affected checks.
12. Update the ChangePlan with verification evidence and result.

Do not skip the ChangePlan because a task looks small.

## Branching and team-conflict policy

### Branch names

Use:

```text
feat/<ticket-or-milestone>-<short-slug>
fix/<ticket>-<short-slug>
refactor/<ticket>-<short-slug>
test/<ticket>-<short-slug>
docs/<ticket>-<short-slug>
chore/<ticket>-<short-slug>
```

### Rules

- Never commit directly to `main`.
- One branch and one ChangePlan per logical change.
- Do not mix cleanup with a feature unless the cleanup is required and documented.
- Keep branches short-lived.
- Rebase rather than create avoidable merge commits.
- Never force-push a shared branch.
- Do not run `git reset --hard`, `git clean -fd`, or discard another developer's work without explicit authorization.
- Before editing shared schemas, migrations, root configuration, or common components, list owned files in the ChangePlan.
- If two active branches must modify the same contract, coordinate the contract change first and document integration order.
- If a conflict changes behavior or a public contract, stop, update the ChangePlan, and rerun all affected tests after resolution.
- Do not resolve a conflict by choosing one side blindly.
- Use an integration branch only when the team explicitly assigns one.

## Commit policy

- Make small, logical commits.
- Every commit should leave the branch buildable and testable when practical.
- Do not commit unrelated formatting or generated files.
- Use concise conventional messages:

```text
feat: add multi-exam target model
fix: preserve confirmed math block order
refactor: isolate geometry action validation
test: cover alternative proof acceptance
docs: record transcription contract
chore: add root check command
```

- Do not squash locally until review policy requires it.
- Never claim a commit contains tests when it does not.

## Documentation policy

Every change must include a complete ChangePlan.

Update permanent documentation when a change affects:

- architecture;
- public API;
- shared schema;
- database model;
- migration behavior;
- content format;
- AI contract;
- security/privacy;
- developer commands;
- product behavior.

Documentation must describe the final implementation, not the intended design only.

## Testing policy

### General

- Add or update tests for every behavior change.
- A bug fix requires a regression test that fails before the fix.
- Do not weaken assertions to make tests pass.
- Do not delete a test without documenting why its behavior is obsolete.
- Do not leave skipped tests without a tracked reason.
- Test public behavior, not private implementation detail, unless the implementation is itself a contract.

### Required test categories by change

Use the relevant subset:

```text
unit
integration
API contract/schema
database migration and backfill
frontend component
browser/end-to-end
math-render regression
geometry-scene/action validation
content-schema validation
AI structured-output validation
AI evaluation regression
manual phone/tablet QA
```

### Root command contract

Milestone 1 must expose these commands at repository root and keep them documented:

```text
make setup
make format
make format-check
make lint
make typecheck
make test-unit
make test-integration
make test-e2e
make content-validate
make test
make check
```

`make check` must run all non-destructive checks required before review.

Until these commands exist, discover and record the actual commands in the ChangePlan. Never invent a successful command result.

## Code style

- Write concise, direct code.
- Prefer small focused functions and modules.
- Use names that remove the need for explanatory comments.
- Comment why a constraint exists, not what obvious code does.
- Avoid speculative abstractions and generic frameworks without two concrete uses.
- Avoid wrapper layers that only rename another API.
- Avoid duplicated validation or state.
- Delete dead code instead of commenting it out.
- Keep error handling explicit.
- Use strict types; avoid `any`, unchecked casts, and unvalidated dictionaries.
- Prefer immutable data at boundaries.
- Keep user-facing text concise.
- Do not add dependencies without documenting the need, license, size, and alternatives in the ChangePlan.

## Frontend rules

- Use typed `ContentBlock` data for problem, hint, feedback, and concept content.
- Never render raw AI HTML.
- Never use raw AI Markdown as the canonical model.
- Catch KaTeX errors and show a correctable placeholder; never leak raw TeX to students.
- Use MathLive for visual formula editing.
- Keep phone and tablet layouts usable; do not implement desktop-only interactions.
- Geometry actions may reference only existing curated object IDs.
- Do not execute AI-generated JavaScript.
- Preserve accessibility descriptions and static fallbacks for geometry.
- UI state must represent loading, retryable failure, permanent failure, and uncertainty explicitly.

## Backend and API rules

- FastAPI/Pydantic schemas are the backend contract.
- Generate or validate the TypeScript client from OpenAPI; do not maintain incompatible duplicate types manually.
- Validate every external and AI payload at the boundary.
- Return stable error codes and concise safe messages.
- Keep AI provider calls behind one adapter.
- Do not scatter provider SDK calls through domain code.
- Use SSE only for one-way long-running progress; do not add WebSockets without a documented need.

## Database rules

- Use migrations for every schema change.
- Never edit a shared database manually as part of a change.
- Document forward migration, existing-data handling, compatibility, and rollback.
- Add indexes only with a documented query need.
- Attempts must reference immutable content versions.
- Store learner evidence as events; aggregate state must be rebuildable.
- Store images in object storage, not PostgreSQL.
- Do not assume one exam target in foreign keys, uniqueness constraints, service methods, or UI types.

## Multi-exam rules

- Use `study_profile -> student_exam_targets[]`.
- A problem may support several exams through explicit relevance links.
- A session item must record which targets it is intended to support.
- Shared skill evidence updates one shared learner state, not duplicated per exam.
- Target progress is derived from shared skill state plus exam-specific skill weights.
- Do not display predicted scores or admission probability without a separately approved calibrated model.
- Planner behavior must remain deterministic and explainable for identical inputs.

## AI rules

- Treat AI output as untrusted.
- Require strict structured output and schema validation.
- Retry a schema failure at most once unless the ChangePlan approves another policy.
- Never fabricate a transcript, score, or hint after provider failure.
- Record provider, model snapshot, prompt version, schema version, latency, token use, and cost.
- Do not store hidden chain-of-thought.
- Store only application-facing structured judgments and concise explanations.
- The grading prompt must state that references are non-exhaustive.
- Preserve the student's written error during transcription; do not silently correct it.
- Route uncertain grading to a safe uncertainty state or internal review.

## Content rules

- Content files are versioned and schema-validated before import.
- Curated geometry and hints are reviewed before publication.
- Runtime AI may select or manipulate approved content; it may not publish new content automatically.
- Record source and provenance for each problem.
- Do not ingest or redistribute material without a documented right to use it.

## Security and privacy rules

- Never commit secrets.
- Keep provider keys server-side.
- Use short-lived signed upload/download URLs.
- Validate file type and size.
- Remove image metadata according to the retention policy.
- Minimize personal data.
- Keep operational retention separate from optional research retention.
- Do not use student work for model improvement without the approved consent path.
- Enforce authorization on every user-owned resource.
- Add audit events for sensitive operations.

## Completion and handoff

Before declaring a change complete, provide a concise handoff containing:

```text
branch
commits
ChangePlan path
files changed
behavior implemented
database/API/schema changes
tests added
commands run and results
manual QA performed
known limitations
conflicts or follow-up work
```

Do not say “done” when documentation, tests, rebase, conflict resolution, or verification is incomplete.
