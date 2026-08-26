# Milestone 2 versioned content and multi-exam schema

## Metadata

- Status: in-progress
- Owner: Project owner
- Branch: `feat/m2-versioned-content-schema`
- Base commit: `88b77350948c5d190208457bf8c8bac5ca5952ee`
- Related milestone: Milestone 2 — Versioned content and multi-exam schema
- Related issue/ticket: None
- Started: 2026-08-26
- Last updated: 2026-08-26

## Context

Milestone 1 is merged into `origin/main` and provides the Next.js/FastAPI/PostgreSQL
foundation, database-backed invite authentication, generated OpenAPI client, reversible
migrations, object storage, root checks, and responsive interaction shell. The repository has no
study profile, exam target, exam configuration, skill graph, versioned concept/problem/geometry
content, content schema, importer, content preview, or attempt record. The existing content gate
intentionally rejects every file except `content/README.md`.

Milestone 2 must establish the complete synthetic-content schema and transactional import boundary
needed by later milestones. It exits only when invalid content cannot be imported and every attempt
is tied to an immutable problem version.

## Goal

Deliver a strict and documented Milestone 2 contract in which:

- one user-owned study profile exposes `studentExamTargets` as an array and supports multiple active
  exam-cycle targets without an implicit primary target;
- exams, cycles, skills, skill relationships, versioned exam-skill weights, immutable concept,
  problem, and curated geometry versions, multi-exam problem relevance, skill links, non-exhaustive
  reference solutions, rubrics, and progressive hints are represented in PostgreSQL;
- original synthetic YAML and JSON packages are parsed without duplicate keys, strictly schema- and
  graph-validated, and imported in one database transaction;
- re-importing an identical package is idempotent while a conflicting immutable version is rejected;
- internal authenticated users can inspect validated content through a typed preview API and UI;
- attempts can be created only against a concrete immutable `problem_version_id`, and the database
  prevents mutation or deletion of immutable content versions.

## Non-goals

- Import or publication of real examination or third-party content.
- Decide the supported real examination set, rights vocabulary, rights-review personnel, or evidence
  system. These remain `DECISION REQUIRED` before real content is imported or published.
- Mathematical rendering with KaTeX, visual editing with MathLive, or interactive JSXGraph rendering;
  those belong to Milestones 3 and 4.
- Student onboarding UI, a daily planner, learner-state computation, exam-progress prediction, AI
  transcription/grading, runtime hint generation, RAG, or a vector database.
- A general CMS or public administrative interface.
- Executable geometry or AI-authored runtime content.

## User-visible behavior

- An authenticated internal user can open a content-preview page from the interaction shell and
  inspect the seeded synthetic problem's typed statement, supported exam cycles, skills, reference
  solutions, rubric, progressive hints, curated scene metadata, and provenance.
- The preview explicitly identifies reference solutions as non-exhaustive and identifies the content
  as original synthetic fixture material.
- Preview loading, empty, retryable failure, authentication failure, and loaded states are explicit.
- Study-profile, exam-target, and attempt contracts are API-only in this milestone; the student-facing
  onboarding and attempt journey remain later work.

## Current-state findings

- `origin/main` is at `88b77350948c5d190208457bf8c8bac5ca5952ee`; the seven Milestone 1 commits and completed ChangePlan
  are present. Local `main` matched `origin/main` at inspection time.
- The feature branch was created directly from that commit and tracks `origin/main`.
- The worktree contained unrelated untracked owner files under `docs/`; they were not inspected and
  are outside this branch's ownership. No unrelated dataset will be read, staged, or imported.
- The only database revision is `20260825_0001`; it creates users, invites, sessions, and solution
  upload metadata and has a tested downgrade to base.
- SQLAlchemy models currently live in `services/api/app/models.py`; Alembic reads `Base.metadata` from
  that module. Milestone 2 domain tables can share that base while living in focused modules imported
  by Alembic.
- FastAPI/Pydantic and generated OpenAPI declarations are the existing API boundary. All protected
  resources use the opaque session dependency in `app.auth.CurrentUser`.
- The current content validator rejects all files below `content/` other than `README.md`; no content
  schema or import dependency exists.
- The current root command contract includes setup, formatting, lint, types, unit, integration,
  migration, content, build, and five-project browser checks. `make seed` currently seeds only the
  development invite.
- The installed Next.js version is 16.3.2. Its repository-local guidance was read, including current
  App Router page/layout, Server/Client Component, data-fetching, and route-parameter behavior.
- Baseline `make check` passed on 2026-08-26: formatting, lint, types, API contract, the Milestone 1
  empty-content gate, production build, 15 frontend tests, 14 backend unit tests, 7 integration tests
  with two full migration cycles, and 5 Playwright device projects.
- The supported real exam set and real-content rights/provenance decisions are explicitly deferred.
  Milestone 2 therefore uses only clearly labeled original synthetic exams and mathematical content.

## Design

### Database boundary

Add focused SQLAlchemy modules for profile, content, and attempt records while preserving the
Milestone 1 identity models. The migration creates relational identity and relationship columns,
uses JSONB only for already validated typed blocks, geometry scenes/actions, and provenance, and adds
documented indexes for actual profile ownership, current-version, relevance, and attempt lookup
queries.

`student_exam_targets` references an exact `exam_cycle_id`; the exam identity and cycle date are
derived through that relationship rather than duplicated. A PostgreSQL partial unique index enforces
unique priority ranks among active targets in a profile. There is no singular target field on the
profile or user.

Stable `concepts`, `problems`, and `geometry_scenes` point to current immutable version rows. Importing
a correction inserts a new version and advances the stable record's pointer; existing version rows
are never updated. PostgreSQL triggers reject update or delete operations on immutable concept,
problem, and geometry version rows. Attempts have a non-null, restrictive foreign key to
`problem_versions` and a user-owned study profile.

### Content contract

Pydantic models use forbidden extra fields, constrained values, discriminated typed `ContentBlock`
unions, a finite relevance scale, finite skill-link roles, progressive hint levels, and curated
geometry object/action vocabularies. Semantic validation rejects duplicate identifiers, unknown
cross-references, geometry parent cycles, unknown visibility/action targets, rubric totals that do
not match the problem maximum, an invalid hint ladder, and reference solutions that do not declare
themselves non-exhaustive.

The first schema accepts only `original_synthetic` provenance and `synthetic_only` publication. This
is deliberately narrower than a future real-content vocabulary: adding real sources is
`DECISION REQUIRED` and must be a reviewed schema change. Every imported content/config row carries
validated version-level source and provenance data.

YAML is parsed with a safe loader that rejects duplicate mapping keys. JSON uses an object-pairs hook
that rejects duplicate keys. Both formats validate into the same package model. Canonical sorted JSON
produces deterministic package and item hashes. A committed JSON Schema is generated from the same
Pydantic contract and checked for drift.

### Import and seed flow

The validator loads every recognized package completely before opening a write transaction. The
importer then records all rows and the `content_imports` receipt in one PostgreSQL transaction. A
schema, graph, immutable-content, or database failure rolls the whole transaction back. An identical
package ID/version/hash is a no-op; a reused package version with different bytes or an existing
immutable row with different canonical content fails safely.

`make content-validate` checks package discovery, strict validation, deterministic hashes, and the
committed JSON Schema without a database. `make seed` continues to seed the development invite and
then imports packages in deterministic path order. It is safe to run repeatedly.

### API and preview

Authenticated APIs create/read/update the current user's study profile and its exam-target array,
create/archive target records, and create/read attempts. Ownership failures return the existing safe
404 behavior.

The internal preview collection and detail endpoints return only published validated content through
explicit Pydantic responses. A small authenticated Next.js page consumes the generated OpenAPI types,
validates the runtime payload, and renders only typed blocks and curated scene metadata. Mathematical
source is labeled as preview data; KaTeX and geometry execution are not introduced early.

### Dependency decision

Add only PyYAML as a small runtime dependency to support the required YAML package format. It is MIT
licensed. JSON-only packages would fail the milestone contract, and a larger YAML framework provides
no second use. Existing Pydantic supplies schema generation and validation, so no JSON Schema runtime
dependency is needed.

### Alternatives rejected

- A singular `target_exam_id` on users or study profiles violates the multi-exam invariant.
- Mutable problem JSON on `problems` would make historical attempts non-reproducible.
- Application-only immutability would allow direct SQL or later code to rewrite attempt content.
- Best-effort row-by-row import could leave partially imported packages.
- Arbitrary Markdown/HTML or executable scene code would bypass typed rendering and geometry safety.
- Real exam fixtures would invent unsupported product and rights decisions.
- A general CMS, RAG layer, or vector index is not needed for deterministic ID-based content access.

## Multi-exam impact

- Study profiles: added as user-owned preparation-cycle records.
- Exam targets: added only as the collection `study_profile -> student_exam_targets[]`; zero, one, or
  many active targets are valid.
- Exam-specific progress: not computed in this milestone. Exam cycles, weights, and problem relevance
  establish its future inputs.
- Shared skill state: skills are modeled once and reused across every exam configuration. No
  per-exam learner-state copy is added.
- Daily-plan balancing: not implemented. The schema preserves deterministic future inputs and allows
  one problem version to support several exam cycles.

## Files and components

Planned and owned by this branch:

- `docs/changes/2026-08-26-m2-versioned-content-schema.md` — living execution record.
- `docs/architecture/versioned-content-and-multi-exam.md` — permanent schema, import, immutability,
  provenance, API, and rollback documentation.
- `README.md`, `content/README.md` — developer commands and synthetic package workflow.
- `Makefile`, `package.json` — content schema/validation/import integration and formatting coverage.
- `services/api/pyproject.toml`, `services/api/uv.lock` — locked PyYAML dependency.
- `services/api/app/models.py` — unchanged Milestone 1 base consumed by new model modules if no import
  registration change is required.
- `services/api/app/profile_models.py`, `services/api/app/content/models.py`,
  `services/api/app/attempt_models.py` — relational Milestone 2 models.
- `services/api/app/content/schemas.py`, `loader.py`, `importer.py`, `preview.py` — strict content
  contract, file boundary, transactional importer, and preview queries.
- `services/api/app/profiles.py`, `services/api/app/attempts.py`, `services/api/app/schemas.py`,
  `services/api/app/api.py` — authenticated profile/target/attempt contracts and routes.
- `services/api/app/scripts/seed_content.py`, `validate_content.py`, `export_content_schema.py`,
  `seed_dev.py` — deterministic validation, import, schema export, and development seed entry points.
- `scripts/validate_content.py` — replaced by the service-owned validator entry point.
- `services/api/migrations/env.py`,
  `services/api/migrations/versions/20260826_0002_versioned_content.py` — model registration and
  reversible Milestone 2 schema.
- `packages/content-schema/content-package.schema.json`, `packages/content-schema/README.md` —
  committed machine-readable schema and usage contract.
- `content/packages/synthetic-m2-foundations-v1/package.yaml` — clearly original synthetic two-exam,
  shared-skill, concept, problem, solution, rubric, hint, and curated-geometry fixture.
- `services/api/tests/unit/test_content_schema.py`,
  `services/api/tests/integration/test_m2_content.py`, and existing integration fixtures — schema,
  migration contract, import, multi-exam, authorization, preview, idempotency, and immutability tests.
- `packages/api-client/openapi.json`, `packages/api-client/src/schema.d.ts` — regenerated FastAPI
  contract.
- `apps/student-web/app/internal/content-preview/page.tsx`,
  `apps/student-web/components/content-preview-app.tsx`, `content-preview.tsx` and tests,
  `apps/student-web/lib/api.ts` and tests, `interaction-shell.tsx`, and `app/globals.css` — authenticated
  internal preview and safe typed response parsing.
- `tests/e2e/foundation.spec.ts` — extend the existing authenticated device journey to verify the
  synthetic content preview without dropping upload coverage.

No files below unrelated untracked owner directories are owned. The exact list will be synchronized
with the final diff before handoff.

## API and schema changes

Planned authenticated endpoints under `/api/v1`:

```text
GET    /study-profile
POST   /study-profile
PATCH  /study-profile
GET    /exam-targets
POST   /exam-targets
PATCH  /exam-targets/{target_id}
DELETE /exam-targets/{target_id}

POST   /attempts
GET    /attempts/{attempt_id}

GET    /internal/content-preview
GET    /internal/content-preview/{problem_id}
```

The study-profile response contains `studentExamTargets: []`; no singular target response field is
introduced. Attempt create/response payloads expose a required `problemVersionId`. Preview responses
use typed content-block unions and arrays of supported exams, skill links, non-exhaustive solutions,
rubric items, hints, and optional curated geometry.

The generated OpenAPI document and TypeScript declarations will be updated and drift-checked. The
content package has a separate generated JSON Schema because it is a version-controlled import
contract rather than an API request.

## Database and migration

Create revision `20260826_0002` after `20260825_0001` with:

- `study_profiles` and `student_exam_targets`;
- `exams`, `exam_cycles`, and versioned `exam_skill_weights`;
- `skills` and `skill_edges`;
- `geometry_scenes` and immutable `geometry_scene_versions`;
- `concepts` and immutable `concept_versions`;
- `problems` and immutable `problem_versions`;
- `problem_exam_relevance` and `problem_skill_links`;
- `reference_solutions`, `rubric_items`, and `problem_hints` tied to exact problem versions;
- `content_imports` receipts;
- minimum `attempts` with non-null `study_profile_id` and `problem_version_id`.

Forward migration starts with no Milestone 2 data, so no backfill is required. Foundation user/auth
and upload tables remain compatible. Version tables use restrictive foreign keys and PostgreSQL
immutability triggers; attempts cannot reference a stable problem without a version. Partial indexes
support one active profile per user, unique active target priority ranks, and one active instance of a
cycle per profile. Other indexes correspond to preview, ownership, relevance, and content-version
lookup queries.

Downgrade removes Milestone 2 triggers and tables in dependency order and leaves all Milestone 1
tables/data intact. Downgrade is destructive to Milestone 2 profiles, imported synthetic content, and
attempts; it is for pre-release rollback only. Content source packages remain in Git and may be
re-imported after re-upgrade. The migration cycle and retained foundation tables will be tested.

## Security and privacy

- Only invite-authenticated users may access profile, target, attempt, and internal preview APIs.
- Profile/target/attempt reads and writes verify ownership and return safe not-found responses across
  users.
- Content import is a local operator command, not a public HTTP mutation endpoint.
- Only original synthetic/non-personal fixture content is committed or imported.
- Raw YAML/JSON, unknown fields, Markdown/HTML, executable geometry fields, and invalid graph/action
  references are rejected before persistence.
- No secrets, images, student solutions, AI data, real minor data, or new retention behavior is added.
- Preview responses expose reviewed synthetic content/provenance only and no user-owned records.

## Test plan

### Unit

- Validate every supported `ContentBlock`, finite enum, provenance, geometry object, and geometry
  action shape; reject extra keys and executable fields.
- Parse both YAML and JSON; reject duplicate keys, unsupported files, malformed versions, empty
  packages, and non-synthetic publication/source values.
- Reject duplicate IDs/codes, unknown exam/skill/concept/scene refs, geometry cycles/parents/actions,
  inconsistent current versions, invalid rubric totals, invalid hint progression, and exhaustive
  reference-solution claims.
- Prove canonical package hashes are deterministic across YAML/JSON key order.
- Validate profile/target/attempt request constraints and typed preview runtime parsing.

### Integration and API contract

- Apply upgrade, downgrade to the Milestone 1 revision, and re-upgrade; inspect required tables,
  constraints, indexes, triggers, and retained foundation tables.
- Import the synthetic package, assert all relationship counts, and prove one problem version supports
  two exam cycles and shares one skill record.
- Run the seed twice and assert content rows and import receipts do not change.
- Reject a validly parsed but conflicting immutable package and prove the transaction leaves no
  partial rows or receipt.
- Attempt to update/delete immutable problem, concept, and geometry version rows and assert PostgreSQL
  rejects the mutation.
- Create one profile with two active targets; reject duplicate active priority rank/cycle; ensure each
  user sees only their profile and targets.
- Require authentication for profile, target, attempt, and preview endpoints; return safe not-found
  responses for cross-user target/attempt access.
- Create an attempt through the API and assert its non-null foreign key references the exact immutable
  problem version; reject missing/unknown version IDs.
- Preview a published problem and assert typed blocks, both supported exams, skills, non-exhaustive
  solutions, rubric, hints, curated geometry metadata, and provenance.
- Regenerate OpenAPI/TypeScript declarations and assert the committed contract is stable.

### Frontend component

- Render preview loading, loaded, empty, retryable error, and authentication-required states.
- Render every supported typed block without arbitrary HTML/Markdown execution.
- Show multiple exam badges, non-exhaustive reference wording, hint levels, geometry accessibility text,
  and synthetic provenance.
- Reject malformed nested preview payloads at the client API boundary.

### Browser/end-to-end

- Preserve the five-project invite/login and synthetic upload journey.
- From the authenticated shell, open the internal preview and assert the seeded problem, two supported
  synthetic targets, non-exhaustive reference label, and no horizontal overflow on each project.

### Content validation

- `make content-validate` validates every committed package and confirms the generated JSON Schema is
  current.
- Focused negative tests prove invalid packages never reach the importer.

### Acceptance criteria

- The schema expresses `study_profile -> student_exam_targets[]` with multiple active targets and no
  implicit primary exam.
- One imported immutable problem version has explicit relevance links to two synthetic exam cycles
  and shared skill links.
- Every canonical rich-content value is a validated typed `ContentBlock`; raw Markdown/HTML is absent.
- Geometry is curated declarative JSON with finite objects/actions, validated references,
  accessibility text, and fallback asset ID; executable fields are rejected.
- Every problem version has source/provenance and at least one reference solution marked
  non-exhaustive, a score-consistent rubric, and a progressive hint ladder.
- Invalid, conflicting, or partially failing packages leave no imported rows or receipt.
- Re-running seed is deterministic and idempotent.
- Attempts cannot exist without a concrete immutable problem version, and that version cannot be
  updated or deleted.
- Authenticated preview and ownership checks pass.
- All focused commands and final `make check` pass before and after rebase.

## Manual QA

1. Run `make setup`; run `make seed` a second time and confirm it reports the synthetic package as
   already imported.
2. Start `make dev-api` and `make dev-web` in separate terminals.
3. Log in at `http://localhost:3000` with the documented local invite.
4. Open the internal content preview from the shell.
5. Confirm the original synthetic problem shows two supported synthetic exam cycles, shared skills,
   typed text/math blocks, non-exhaustive reference solutions, score-consistent rubric items,
   progressive hints, scene accessibility/fallback metadata, and provenance.
6. Narrow to `360 x 640` and then use an iPad portrait viewport; confirm readable content and no
   horizontal overflow.
7. Run the content validator against a temporary invalid package used by the tests and confirm the
   command exits non-zero without changing the database.

Expected outcome: internal operators can inspect only validated synthetic versioned content, while
student profile/target and attempt contracts remain authenticated and immutable-version-safe.

## Rollout and rollback

This is an internal pre-release schema. Merge after Milestone 1 and before Milestones 3–5. Apply the
migration before running content seed. The package importer is idempotent, so application deploy and
content seed may be retried safely.

Rollback requires stopping application writes, downgrading one revision to `20260825_0001`, and
reverting this branch. This discards Milestone 2 profiles, targets, imported content, and attempts but
preserves Milestone 1 accounts, sessions, uploads, and object storage. No real/user content is expected
at this stage. After a rollback/re-upgrade, deterministic synthetic packages can be imported again.

## Branch and commit plan

1. `docs: add Milestone 2 change plan`
2. `feat: add versioned multi-exam database schema`
3. `feat: add strict content packages and importer`
4. `feat: add profile target and attempt contracts`
5. `feat: add authenticated content preview`
6. `test: cover Milestone 2 content guarantees`
7. `docs: record Milestone 2 implementation`
8. `docs: record final Milestone 2 verification`

Each implementation commit will include its directly applicable tests and remain buildable/testable
where practical. Generated artifacts will be committed with the contract change that produces them.

## Conflict coordination

Owned paths are the files listed in **Files and components**, including the shared migration/model/API
contracts, root Make/package commands, generated OpenAPI declarations, the content root, and the
internal preview UI. No active remote branch beyond already merged Milestone 0/1 branches was visible
after fetch. Milestones 3–5 must integrate after this schema because they will consume typed blocks,
problem versions, geometry scene versions, and attempt references.

The unrelated untracked `docs/` owner content is not owned, will not be inspected, and will not be
staged. If `origin/main` changes a public contract before handoff, the conflict will be documented and
affected checks rerun rather than resolved by choosing one side blindly.

## Risks

- The number of relational contracts could produce migration-order or cyclic-current-version issues.
  Mitigation: add current-version foreign keys after version tables exist and test both migration
  directions twice.
- JSONB can hide invalid content if any write bypasses the importer. Mitigation: expose no content
  mutation API, keep importer models strict, persist hashes, and test the only seed path.
- Trigger-enforced immutability could prevent schema rollback. Mitigation: drop triggers/functions
  before tables and exercise downgrade/re-upgrade against PostgreSQL.
- YAML loaders commonly accept duplicate keys. Mitigation: custom safe-loader mapping construction
  rejects duplicates before Pydantic validation.
- A content package could be internally valid but conflict with existing immutable IDs. Mitigation:
  compare canonical item hashes inside the transaction and roll back the complete import.
- Real-content fields could accidentally imply rights approval. Mitigation: schema v1 accepts only
  original synthetic provenance and labels real-content vocabulary/publication `DECISION REQUIRED`.
- Internal TeX preview could be mistaken for the Milestone 3 renderer. Mitigation: label math source
  explicitly and do not introduce KaTeX or claim student rendering support.
- Generated OpenAPI/content schema drift could produce incompatible consumers. Mitigation: generate
  both from Pydantic and fail `make check` on any diff.

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

- 2026-08-26: Use exact exam-cycle targets rather than duplicating an exam ID and date in a target;
  exam identity/date remain derivable and later planning inputs stay internally consistent.
- 2026-08-26: Restrict the first package schema to original synthetic content. Real source and rights
  vocabularies remain `DECISION REQUIRED` and are not guessed during schema development.
- 2026-08-26: Enforce content-version immutability in PostgreSQL as well as importer logic because the
  Milestone 2 exit condition must survive later application-code paths.
- 2026-08-26: Provide a small authenticated preview UI in addition to the specified preview API so
  internal reviewers can exercise the content contract without a general CMS.

## Discoveries

- The unrelated untracked owner content visible before branch creation changed paths while the
  baseline was being inspected, indicating concurrent owner activity. This branch will continue to
  stage only explicit owned files.

## Verification evidence

- `git fetch origin --prune` returned `origin/main` at
  `88b77350948c5d190208457bf8c8bac5ca5952ee` with the complete Milestone 1 commit sequence.
- `git switch -c feat/m2-versioned-content-schema origin/main` created the required branch from that
  exact commit.
- Baseline `make check` passed before Milestone 2 edits. It verified Prettier/Ruff formatting,
  ESLint/Ruff lint, TypeScript/mypy types, generated API contract, the Milestone 1 content gate,
  Next.js production build, 15 frontend unit/component tests, 14 backend unit tests, two full
  migration downgrade/upgrade cycles, 7 API/PostgreSQL/MinIO integration tests, and 5 Playwright
  browser projects.

## Result

Implementation has not started. The proposed design and owned-file set are recorded above for review.
