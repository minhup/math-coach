# Versioned content and multi-exam architecture

Milestone 2 establishes the application-owned contracts for learner targets, reviewed content, and
attempt-to-content reproducibility. The implementation deliberately supports only clearly original
synthetic content. Selecting real examinations and approving their rights/provenance vocabulary is
`DECISION REQUIRED` before any real content is added.

## Domain boundaries

### Study profiles and targets

The learner relationship is:

```text
user
  └── study_profile
        └── student_exam_targets[]
              └── exam_cycle ── exam
```

A user may have one active study profile and that profile may have zero, one, or many active exam
targets. Each target references an exact exam cycle, stores its own target score and priority rank,
and has no singular or implicit primary-exam field. Partial unique indexes prevent two active targets
from using the same cycle or priority rank within one profile. Archived targets remain historical
records.

Exams and cycles are shared configuration. Skills are also shared: targeting two exams does not copy
learner state or create exam-specific versions of a skill. Versioned exam-skill weights describe how
shared skills contribute to a particular cycle. Every weight configuration must total exactly one
per cycle and version.

### Stable content and immutable versions

Concepts, problems, and geometry scenes have stable identity rows and immutable version rows:

```text
problem.current_version_id ──> problem_version
                                  ├── problem_exam_relevance[] ──> exam_cycle
                                  ├── problem_skill_links[] ─────> skill
                                  ├── reference_solutions[]
                                  ├── rubric_items[]
                                  └── problem_hints[]

attempt.problem_version_id ──> problem_version
```

Publishing a correction inserts another version and advances only the stable row's current-version
pointer. Existing version rows and their relevance, skill-link, solution, rubric, and hint records are
not rewritten. PostgreSQL triggers reject `UPDATE` and `DELETE` on these immutable rows. Restrictive,
non-null foreign keys require every attempt to reference a concrete problem version and prevent that
version from being removed. A new attempt may pin any retained version of an available synthetic
problem, including a version that stopped being current after the learner opened it.

A problem version may have explicit relevance links to several exam cycles. The seeded synthetic
problem proves this with two distinct exams while using one shared set of skill records.

## Typed content

Problem statements, concepts, skill descriptions, solutions, rubric descriptions, hints, and
selection prompts use the discriminated `ContentBlock` union:

- text;
- inline mathematics;
- display mathematics;
- a rich line made from typed text/math spans;
- a curated geometry-scene-version reference;
- an image asset reference with alternative text;
- a typed callout containing more content blocks.

Arbitrary Markdown and HTML are not package fields and are rejected as unknown data. Preview code
switches on the generated union and never injects HTML. Milestone 3 routes preview mathematics through
the [controlled KaTeX and visual-correction boundary](math-rendering-and-transcript-state.md).
Milestone 4 resolves geometry blocks through the current versioned scene in the preview response and
passes them through the
[strict interactive-geometry boundary](interactive-geometry-engine.md). Missing or invalid scene
references produce a concise unavailable state rather than partially rendering untrusted content.
Milestone 5 exposes a separate student-safe deterministic plan response containing only the exact
immutable problem version, typed statement, optional validated scene, and explicit supporting target
record IDs. It does not expose the preview's reference solutions or rubric to the learner surface.

Geometry scene versions are declarative JSON. Their finite object vocabulary contains IDs,
construction parents, free-point coordinates, explicit drag/select capabilities, intersection
branches, labels, viewport, initial visibility, approved animation IDs, an accessibility
description, and a static fallback asset ID. Hint actions use a separate finite union for show,
hide, highlight, focus, clear, animate, and select operations. The validator rejects unknown
parents, cycles, malformed parent/type combinations, unknown visibility/action targets, unknown
animations, and executable fields. JavaScript or other generated geometry code is never evaluated.

Reference solutions must declare both expert verification and `nonExhaustive: true`. They are
examples, not an exhaustive list of valid mathematical reasoning. Rubric scores must total the
problem maximum. Every problem version contains exactly the ordered hint ladder 1 through 5; only
the final level declares a complete-solution reveal.

## Package contract and validation

Each directory below `content/packages/` contains exactly one `package.yaml`, `package.yml`, or
`package.json`. Schema version `1.0.0` requires:

- package identity and version;
- exams, cycles, skills, relationships, and versioned weights;
- zero or more curated scene and concept records with immutable versions;
- at least one problem with immutable versions and all version-owned relationships;
- source and provenance on every content/configuration record.

Pydantic models forbid extra fields and validate constrained values, typed unions, global UUID and
code uniqueness, current-version membership, cross-references, graph cycles, scoring, weight totals,
hint progression, and geometry references. YAML uses a safe loader that rejects duplicate explicit
keys while permitting intentional anchors. JSON uses an object-pairs hook that rejects duplicate
keys. Canonical sorted JSON produces deterministic SHA-256 package and item hashes.

The v1 provenance model accepts only:

```text
sourceKind: original_synthetic
rightsBasis: original_fixture
publicationStatus: synthetic_only
```

It also records creator, source reference, acquisition, rights evidence and review, permitted uses,
restrictions, attribution, derivation/adaptation/translation notes, mathematics review, and
publication date. The committed fixture contains invented exam names and original synthetic
mathematics. The contract intentionally cannot validate or import third-party or real-exam content.

`packages/content-schema/content-package.schema.json` is generated from the same Pydantic model.
Validation fails if that artifact is stale.

## Validation, import, and seed flow

```text
discover package files
  → parse with duplicate-key rejection
  → strict shape and semantic validation
  → canonical content hash
  → one PostgreSQL transaction
       ├── compare stable and immutable identities/hashes
       ├── insert complete package records
       └── insert content_import receipt
```

The importer accepts an already validated `ContentPackage`. Every package is written in one
transaction. A validation error occurs before that transaction; an immutable-ID conflict, relational
constraint error, or receipt conflict rolls the transaction back. A package therefore cannot leave
some of its records imported. An identical package ID/version/hash is an idempotent no-op. Reusing a
package ID/version with different content or reusing an immutable identity with a different hash is
rejected.

Package discovery and seed order are lexical and deterministic. Use:

```bash
make content-validate
make migrate
make seed
```

`make seed` seeds the local invite, validates/imports the M2 foundation and incremental M4 geometry
packages in lexical order, and may be run again safely. Both packages share the same two explicit
synthetic exam cycles and shared skills; the M4 package adds new immutable scene/problem records
rather than creating exam-specific learner state. Content seeding refuses to run when the
application environment is production.

## API and authorization

Authenticated API contracts expose:

```text
GET|POST|PATCH /api/v1/study-profile
GET|POST       /api/v1/exam-targets
PATCH|DELETE   /api/v1/exam-targets/{target_id}
POST           /api/v1/attempts
GET            /api/v1/attempts/{attempt_id}
GET            /api/v1/internal/content-preview
GET            /api/v1/internal/content-preview/{problem_id}
GET            /api/v1/exam-cycles
GET            /api/v1/plans/today
POST           /api/v1/attempts/{attempt_id}/mock-transcription
POST           /api/v1/attempts/{attempt_id}/mock-evaluation
POST           /api/v1/attempts/{attempt_id}/hints/next
GET            /api/v1/concept-versions/{concept_version_id}
```

Profile responses contain `studentExamTargets: []`. Profile, target, and attempt queries verify the
session user's ownership; cross-user resources return the same safe not-found response as missing
resources. Content preview requires an authenticated internal session and has no mutation endpoint.
The preview service revalidates stored JSONB through the typed content, action, scene, and provenance
adapters before producing a response.

FastAPI/Pydantic remains the backend contract. OpenAPI and the TypeScript client declarations are
generated together. The web client additionally validates nested response data at runtime before
rendering the internal preview. Loading, empty, authorization failure, retryable failure, and loaded
states are explicit on phone and tablet layouts.

Milestone 5's static plan still treats targets as a collection. Its shared-foundation item supports
all active target records that match the problem's explicit relevance links, while its follow-up
supports one exact priority target. UUIDv5 plan identity is derived from the plan date, profile,
ordered targets, and ordered immutable problem versions, so identical inputs remain deterministic.
This narrow fixture-backed composition does not duplicate skills, infer learner state, implement the
Milestone 9 planner, or predict an examination outcome. The complete boundary is documented in the
[static student journey architecture](static-student-journey.md).

## Migration and rollback

Alembic revision `20260826_0002` follows the Milestone 1 revision. Forward migration has no data
backfill because all Milestone 2 tables are new. It creates relational constraints, query-driven
indexes, deferred current-version foreign keys, and the immutable-row trigger function.

Downgrade removes triggers and Milestone 2 tables in dependency order, leaving Milestone 1 users,
sessions, invites, upload metadata, and object-storage data intact. It is destructive to study
profiles, exam targets, imported content, and attempts, so it is a pre-release rollback only. Source
packages remain in Git and can be deterministically re-imported after re-upgrade.

No RAG system, vector database, AI content publication, general CMS, predicted score, or admission
probability is part of this architecture.
