# Milestone 4 interactive geometry engine

## Metadata

- Status: active
- Owner: Codex implementation; project owner approval
- Branch: `feat/m4-interactive-geometry-engine`
- Base commit: `3bc9206c1adc0ee3b11a2adb016d8196a64cd58e`
- Related milestone: Milestone 4 — Interactive geometry engine
- Related issue/ticket: None
- Started: 2026-08-27
- Last updated: 2026-08-27

## Context

Milestone 3 is present on `origin/main` at the exact requested commit `3bc9206`. The repository has
strict, versioned, curated geometry-scene and geometry-action data from Milestone 2, generated
OpenAPI/TypeScript contracts, an authenticated content preview, controlled KaTeX rendering, and five
Playwright phone/tablet projects. It does not yet render a scene, derive a construction order,
enforce object-specific parent types, preserve constructions during dragging, execute approved typed
actions, ask selection questions, resolve fallback assets, or provide a geometry device report.

Milestone 4 must turn the existing declarative data into one safe interactive boundary. Geometry
remains curated application data. The renderer may translate validated object records into a finite
set of application-authored JSXGraph calls, but it may never evaluate scene strings or accept
JavaScript, functions, expressions, handlers, HTML, Markdown, SVG markup, or another drawing
language.

## Goal

Deliver a deterministic JSXGraph renderer for validated versioned scenes that:

- implements point, segment, line, ray, circle, arc, polygon, angle, midpoint, intersection,
  perpendicular, parallel, circumcircle, and label;
- orders out-of-order declarations from explicit parent relationships and rejects invalid graphs as
  a whole;
- allows dragging only for free points explicitly marked draggable and leaves constructed objects
  derived from their parents;
- supports configured pointer/touch selection plus a keyboard-accessible selection path;
- validates and applies show, hide, highlight, clear-highlight, focus, animate, and ask-select actions
  only against existing compatible object IDs;
- exposes every released scene's accessibility description and repository-owned static fallback;
- integrates the typed geometry `ContentBlock` and internal content-preview path;
- supplies an authenticated synthetic geometry spike, regression fixtures, and exact five-project
  phone/tablet evidence.

## Non-goals

- Student-authored constructions, arbitrary drawing tools, direct pen input, or geometry authoring.
- Runtime AI scene generation, executable geometry code, JessieCode, JavaScript expressions,
  callbacks from content, script tags, event-handler attributes, AI HTML/Markdown/SVG, or `eval`.
- Sliders; the MVP plan mentions configured sliders generally, but Milestone 4's requested primitive
  and action scope does not include a slider schema or UI.
- A generic canvas/SVG framework, JSXGraph React wrapper, rich-text framework, Markdown renderer,
  AI SDK, RAG system, vector database, grading, transcription, learner state, or planning.
- Real examination content, third-party content, participant data, or production asset delivery.
- Database schema changes, backfills, or a geometry mutation API.
- Predicted scores, admission probabilities, or any singular-examination assumption.

## User-visible behavior

- An authenticated internal learner can open **Geometry spike** from the workspace.
- The spike visibly identifies its scene as original synthetic fixture data and shows the scene's
  accessibility description.
- The scene initially shows only configured object IDs. Clearly labelled controls demonstrate each
  approved action without exposing technical JSON.
- Explicitly permitted free points can be dragged with pointer or touch. Locked free points and all
  constructed points remain fixed as independent inputs; midpoint, intersection, perpendicular,
  parallel, and circumcircle objects update from their parents.
- Selectable objects can be tapped/clicked on the board or chosen through a keyboard-operable object
  list. During ask-select, only the action allowlist can create a response.
- Selection response state is concise and deterministic: no response, selected object, and one of
  correct, incorrect, or ungraded when no answer key is curated.
- A static fallback is available for the valid scene and becomes the primary presentation if scene
  validation, JSXGraph loading, or construction fails.
- The internal content preview renders its typed geometry block with the same scene boundary rather
  than printing only the scene-version UUID. Preview hint actions can operate on that rendered scene.
- Phones use a contained single-column scene/control layout. Tablets use a scene/control split. No
  configured viewport creates document-level horizontal overflow.

## Current-state findings

- `git fetch origin main` resolved `origin/main` to
  `3bc9206c1adc0ee3b11a2adb016d8196a64cd58e`; `git merge-base --is-ancestor 3bc9206
origin/main` exited successfully. Milestone 3 is therefore present at the exact required commit.
- The shared checkout is dirty on `main`. Its unrelated and untracked corpus/data paths were not
  listed, opened, formatted, staged, stashed, or discarded. Work is isolated in the clean worktree
  `/home/minh/dev/math-coach-m4`, created from `origin/main` on this branch.
- No remote branch was reported as unmerged from the fetched `origin/main` during inspection.
- The root command contract exists: setup, format, format-check, lint, typecheck, unit, integration,
  E2E, content validation, build, test, and check. `make check` runs every non-destructive review
  gate, including generated API drift and all five Playwright projects.
- FastAPI/Pydantic is already authoritative for `ContentBlock`, `GeometrySceneVersion`,
  `GeometryObject`, and the seven geometry actions. Models use `extra="forbid"`; YAML and JSON
  loaders reject duplicate keys; generated content JSON Schema and OpenAPI/TypeScript files are
  checked for byte-for-byte drift.
- The existing scene schema already contains the 15 approved object type names, stable IDs, parent
  ID arrays, free-point coordinates, a numeric viewport, initial visibility, animation IDs,
  fallback asset ID, accessibility description, and provenance.
- Current backend validation rejects duplicate object IDs, unknown initial-visible IDs, unknown
  parents, parent-count errors, direct/indirect cycles, unknown action IDs, unknown animation IDs,
  and ask-select correct IDs outside its allowed IDs. Unsupported types and executable extra fields
  are rejected by Pydantic.
- The current object model is intentionally shallow. It does not reject non-finite coordinates,
  validate parent object types, distinguish an intersection branch, configure drag/select
  permission, reject duplicate target lists, or constrain animate/ask-select targets by capability.
- The frontend runtime API guard duplicates only the current shallow generated shape and does not
  validate graph semantics, exact keys, finite viewport values, action references, or capabilities.
- Content preview revalidates stored JSONB through Pydantic before responding. The web preview then
  validates nested payloads again, but `TypedContentBlocks` currently renders geometry as a UUID
  reference and the preview shows only description/version/object-count/fallback-ID metadata.
- Geometry scene versions and action arrays are already stored as validated JSONB. Adding optional
  declarative fields and new immutable content versions does not require a table or column change.
- Existing immutable content hashes serialize Pydantic models including defaults. New optional
  compatibility defaults must be omitted from serialization when inactive so previously imported
  immutable versions retain the same canonical JSON and item hash.
- The committed Milestone 2 package has one locked triangle/midpoint scene and a fallback asset ID,
  but no corresponding static web asset. A separate incremental synthetic Milestone 4 package can
  reuse identical shared exam/skill records while adding new scene/problem identities without
  rewriting old immutable rows.
- The existing five projects are compact Chromium `360x640`, Pixel 7 Chromium `412x839`, iPhone 13
  WebKit `390x664`, iPad Pro 11 portrait WebKit `834x1194`, and iPad Pro 11 landscape WebKit
  `1194x834`.
- Repository-local Next.js 16.3.2 guidance says browser-only interactive libraries belong behind a
  focused Client Component; a package that depends on browser APIs may be loaded with a client-side
  dynamic import; `ssr: false` is valid only from a Client Component; and package stylesheets may be
  imported from the App Router. Local public images use root-relative `/...` paths and explicit
  dimensions or aspect ratio.
- JSXGraph is the renderer selected in the MVP architecture. Official 1.13.2 docs describe
  `JXG.JSXGraph.initBoard`, `board.create`, `JXG.JSXGraph.freeBoard`, responsive resize handling,
  multi-touch support, point `fixed` behavior, element events/ARIA, and native dependent
  constructions for the required primitives.
- Registry metadata on 2026-08-27 reports `jsxgraph@1.13.2`, published seven days earlier, with
  built-in TypeScript declarations, package exports, one self-reference dependency satisfied by the
  same installed package, Node `>=20.19.0`, dual MIT/LGPL-3.0-or-later licensing, a 10,982,285-byte
  tarball, and 78,187,672 unpacked bytes. The exact lock installs to 76 MiB on this filesystem; the
  dynamically loaded production chunk is 1,151,137 bytes (262,447 bytes with gzip), and the final
  production-only npm audit reports zero vulnerabilities.
- The final Milestone 3 `make check` evidence on `origin/main` passed formatting, lint, type checks,
  generated-contract drift, content validation, production build, 66 frontend tests, 25 backend
  tests, two complete migration cycles, 19 integration tests, and all 10 browser cases. A fresh
  pre-change baseline `make check` on this isolated branch reproduced those passing counts.

## Design

### Authoritative scene and action contract

Extend the existing models rather than introduce a parallel schema:

- finite floats for viewport and point coordinates;
- `draggable: true` only on a parentless `point`; omission means locked;
- `selectable: true` only where content review permits direct learner selection;
- `intersectionIndex: 0 | 1`, legal only on `intersection`, with deterministic default zero;
- concise plain geometry labels/descriptions rendered as text, never markup;
- unique initial-visible, action-target, animation, allowed-object, and correct-object ID lists;
- object-specific parent types matching the renderer constructor contract;
- animate targets restricted to points and animation IDs restricted to the current scene allowlist;
- ask-select allowed IDs restricted to scene objects explicitly marked selectable, with correct IDs
  a unique subset of that allowlist.

Inactive compatibility defaults are excluded from canonical serialization. Existing Milestone 2
scene JSON therefore remains valid and hash-stable, with its points locked and non-selectable. The
incremental Milestone 4 package adds new immutable scene/problem identities and explicit
capabilities; it does not rewrite an old scene version.

The scene object remains the canonical state. Runtime coordinates are a renderer view and are never
serialized back over curated content.

### Deterministic validation and construction order

The frontend geometry boundary consumes generated API types and validates unknown payloads against
the same finite keys and semantic rules before JSXGraph is imported. It does not define an
incompatible handwritten geometry type.

Construction order uses Kahn topological sorting over explicit parent IDs. The ready queue is sorted
by stable object ID, so parent-first output is deterministic even when declarations are shuffled.
Unknown parents, duplicate IDs, unsupported types, malformed properties, and direct or indirect
cycles reject the entire scene. No partial board is retained after an error.

Parent capabilities are:

```text
point                     no parents; finite x/y
segment | line | ray      two point-like parents
circle                    center point + radius point
arc                       center point + radius point + angle point
polygon                   3–32 point-like parents
angle                     point + vertex point + point
midpoint                  two point-like parents
intersection              two line/circle-like parents + branch index
perpendicular | parallel  line-like parent + point-like parent
circumcircle              three point-like parents
label                     one point-like parent + plain label text
```

Line-like includes line, segment, ray, perpendicular, and parallel. Circle-like includes circle and
circumcircle. Point-like includes point, midpoint, and intersection.

### JSXGraph boundary

`GeometryBoard` is a focused Client Component. After validated props reach the browser it dynamically
imports locked local JSXGraph, initializes one SVG board with the curated viewport and application
owned attributes, and creates only the finite constructors above. Scene values provide numbers,
plain strings, stable IDs, and references only. They never choose a constructor name outside the
validated enum and are never compiled or evaluated.

Ray is represented by JSXGraph's line constructor with application-owned
`straightFirst: false, straightLast: true`; label is application-authored text anchored to the
parent's live geometry with markup parsing disabled. All non-free and locked elements use fixed
interaction attributes. Free points use JSXGraph native dependency updates, so downstream midpoint,
intersection, perpendicular, parallel, and circumcircle constructions stay constrained.

The component registers application-owned `up`/touch handlers on selectable elements and emits
stable scene IDs. A keyboard-accessible object list provides equivalent selection without requiring
SVG navigation. Board cleanup always calls `freeBoard`; construction failure frees any partial board
before switching to fallback.

The renderer emits an application-owned, read-only geometric snapshot after initialization and
movement. The internal spike displays this snapshot as a constraint monitor; it is not canonical
content or persistence. It provides an observable public seam for device regression without a test
only global or private JSXGraph introspection.

### Pure interaction state and actions

One immutable state holds ordered visible IDs, highlighted IDs, focused IDs, the active animation,
the active ask-select question, and its response. State creation uses the scene's initial visibility.
Every transition revalidates the action against the scene and returns deterministically ordered ID
arrays.

- show/hide changes only visibility;
- highlight adds targets without changing visibility;
- clear-highlight clears all or the specified subset;
- focus replaces the focused set and applies a visible app-owned focus treatment;
- animate records the allowlisted animation request and applies one fixed app-owned pulse effect;
- ask-select installs the typed prompt and exact allowed-ID set, clearing the prior response;
- selecting outside the active allowlist has no effect; selecting an allowed object records one
  stable response and derives correct/incorrect/ungraded from curated `correctObjectIds`.

No action mutates construction parents or curated coordinates. Animation IDs select only the fixed
renderer effect; they do not name source code, CSS supplied by content, or an expression.

### Accessibility and fallback

Every valid scene renders inside a labelled figure with the required accessibility description,
board title, visible interaction instructions, current selection status, and keyboard selection
controls. Touch targets are at least 44 CSS pixels. Motion respects `prefers-reduced-motion`.

Synthetic fallback asset IDs resolve through the existing safe identifier vocabulary to committed
root-relative `/fixtures/<asset-id>.svg` files. The fallback is available from a disclosure during
normal rendering and is shown directly when validation, dynamic import, board creation, or renderer
updates fail. Missing description/fallback makes a scene invalid; if invalid input lacks enough data
for its curated image, the boundary shows only the concise accessible message **Geometry unavailable**
and never attempts partial rendering.

Fallback SVG is a repository-owned static build asset. Scene payloads cannot contain SVG markup,
URLs, HTML, scripts, or event handlers.

### Content preview and authenticated spike

`TypedContentBlocks` accepts an already validated scene resolver. A matching geometry block renders
the shared geometry experience at its content position; an unresolved version reference uses the
safe fallback state. The content preview passes its one versioned scene and grouped hint actions to
that experience. Other typed text/math/image/callout behavior remains unchanged.

`/internal/geometry-spike` reuses the existing authenticated-session gate and explicit checking,
authorization-required, retryable-failure, and ready states. Its comprehensive versioned fixture is
clearly synthetic, uses all approved primitives, declares objects out of dependency order, exposes
one draggable point plus locked/constructed controls, and supplies all actions and ask-select
outcomes. It calls no new API and stores nothing.

### Approved public test seams and TDD slices

The project owner confirmed these seams before the first test was written:

1. `GeometrySceneVersion`/`ContentPackage` Pydantic validation and generated OpenAPI/TypeScript
   output at the backend contract boundary.
2. Frontend `validateAndOrderGeometryScene(unknown)` returning one validated generated scene plus a
   known-literal stable object-ID order, or one safe validation error.
3. Pure `createGeometryInteractionState`, `applyGeometryAction`, and `selectGeometryObject`
   transitions using known-literal states.
4. `GeometryScene` component DOM: loading, ready, actions, selection, accessibility, and static
   fallback behavior; JSXGraph is mocked only as the external browser-library boundary in jsdom.
5. `ContentPreview` rendering the existing generated geometry `ContentBlock` through the shared
   scene boundary.
6. `/internal/geometry-spike` authenticated real-browser behavior across the unchanged five-project
   Playwright matrix, including native JSXGraph drag/selection and constraint snapshots.

Implementation proceeds as vertical red/green slices in that order: one failing behavior test, the
minimum implementation, then the next behavior. Tests assert public outputs and known mathematical
literals rather than private call counts or implementation-shaped snapshots.

## Multi-exam impact

- Study profiles: no change.
- Exam targets: no change; the new synthetic problem retains explicit relevance to two exam cycles.
- Exam-specific progress: no change.
- Shared skill state: no change; the incremental fixture reuses shared skills rather than copying
  learner state per exam.
- Daily-plan balancing: no change.

No type, query, fixture, or UI introduces a singular examination target.

## Files and components

Proposed and owned by this branch:

- `docs/changes/2026-08-27-m4-interactive-geometry-engine.md` — living execution record.
- `docs/architecture/interactive-geometry-engine.md` — durable canonical scene, construction,
  interaction, safety, fallback, and rollback contract.
- `docs/architecture/versioned-content-and-multi-exam.md` — replace the stale future-geometry note
  with the implemented Milestone 4 boundary.
- `docs/MVP_IMPLEMENTATION_PLAN.md` — document the final implemented geometry semantics and exit
  evidence without broadening the milestone.
- `docs/evaluation/m4-geometry-device-report.md` — committed exact regression/device results.
- `README.md` and `content/README.md` — internal route, focused commands, incremental synthetic
  package, and fallback-asset convention.
- `package.json` — include owned Milestone 4 documentation in formatting checks and align the Node
  engine with the locked renderer's `>=20.19` requirement.
- `package-lock.json` and `apps/student-web/package.json` — exact `jsxgraph@1.13.2` production lock.
- `services/api/app/content/schemas.py` — finite/object-specific scene and action validation.
- `services/api/tests/fixtures/geometry.py` — reusable original synthetic all-primitives scene and
  action records for contract tests.
- `services/api/tests/unit/test_geometry_schema.py` — scene graph, property, parent-type, and action
  regressions.
- `services/api/tests/integration/test_m4_geometry_content.py` — incremental import and authenticated
  preview of the new immutable scene/problem.
- `services/api/tests/integration/test_m2_content.py` — update the content-root seed receipt
  expectation for two committed packages; no Milestone 2 behavior is weakened.
- `content/packages/synthetic-m4-geometry-v1/package.yaml` — versioned original synthetic scene,
  multi-exam problem, all primitives, configured interaction capabilities, and approved actions.
- `packages/content-schema/content-package.schema.json` — generated Pydantic content contract.
- `packages/api-client/openapi.json` and `packages/api-client/src/schema.d.ts` — generated FastAPI
  API and TypeScript geometry contract.
- `apps/student-web/lib/api.ts` and `apps/student-web/lib/api.test.ts` — strict nested geometry
  boundary using generated types.
- `apps/student-web/features/geometry/geometry-scene.ts` and test — exact-key validation,
  object-specific graph validation, and deterministic topological order.
- `apps/student-web/features/geometry/interaction-state.ts` and test — pure typed actions and
  deterministic selection response state.
- `apps/student-web/features/geometry/synthetic-fixtures.ts` — comprehensive versioned UI fixture
  corresponding to original synthetic content semantics.
- `apps/student-web/components/geometry/geometry-board.tsx` and test — client-only JSXGraph board,
  primitive translation, cleanup, movement snapshot, and renderer failure boundary.
- `apps/student-web/components/geometry/geometry-scene.tsx` and test — accessibility, fallback,
  action controls, selection, and interaction-state orchestration.
- `apps/student-web/components/geometry/geometry-spike-app.tsx` and test — authenticated synthetic
  route states and responsive fixture surface.
- `apps/student-web/app/internal/geometry-spike/page.tsx` — App Router entry.
- `apps/student-web/public/fixtures/synthetic-triangle-midpoint-fallback.svg` — missing static
  fallback for the already released Milestone 2 scene.
- `apps/student-web/public/fixtures/synthetic-m4-geometry-fallback.svg` — all-primitives synthetic
  scene fallback.
- `apps/student-web/components/math/content-blocks.tsx`,
  `apps/student-web/components/content-preview.tsx`, and existing content-preview tests — render
  typed geometry content and operate preview actions without regressing math/multi-exam content.
- `apps/student-web/components/interaction-shell.tsx` and its existing app test — authenticated
  navigation to the geometry spike.
- `apps/student-web/app/globals.css` — contained board, fallback, action, selection, phone, tablet,
  focus, touch-target, reduced-motion, and minimal JSXGraph integration styles. Package inspection
  proved the dependency stylesheet subpath is not exported, so `app/layout.tsx` remains unchanged.
- `tests/e2e/geometry.spec.ts` — unchanged five-project browser regression.
- `tests/e2e/foundation.spec.ts` — scope the existing content-preview description assertion after
  the typed geometry block correctly introduces a second visible copy inside the live scene.
- `playwright.config.ts` — allow isolated worktrees to select non-conflicting local web/API ports
  while retaining the existing defaults and five device projects. The first real-browser red run
  discovered live Milestone 3 servers owned by another worktree on ports 3000/8000; those processes
  remain untouched.
- `scripts/run_e2e.sh` — pass the same optional isolated ports through production-server and
  container execution so the root E2E/check contract can run without stopping another worktree.
- `apps/student-web/next.config.ts` — derive the production API rewrite from the optional isolated
  Playwright API port when an explicit `API_PROXY_TARGET` is absent. The first full-root run proved
  the runtime server target alone cannot change a rewrite already captured by `next build`.

`services/api/app/content/preview.py`, `preview_schemas.py`, database models/migrations,
`vitest.config.ts` and existing correction code are not expected to change.
If installation or the first red slice proves another file necessary, this list will be updated
before that file changes.

## API and schema changes

- Extend the existing Pydantic `GeometryObject` JSON shape with optional generated fields for
  explicit drag/select capability and intersection branch selection. Defaults preserve old scene
  behavior and are excluded from inactive canonical serialization.
- Tighten existing scene and action semantic validation as described in **Design**.
- Regenerate the content-package JSON Schema, OpenAPI document, and TypeScript declarations through
  the existing commands. No handwritten duplicate TypeScript scene contract is introduced.
- The existing authenticated content-preview response carries the extended scene shape through its
  current `geometryScene` field. No endpoint, HTTP method, error code, or request body is added.
- Content package schema version remains `1.0.0` because the extension is backward compatible for
  previously valid scenes; unsupported or semantically unsafe inputs that were never renderer-safe
  become explicitly rejected.

## Database and migration

None expected. Geometry scenes and actions already live in version-owned JSONB columns, and the new
fixture uses new immutable IDs. Forward deployment reuses the existing importer; existing scene
versions stay readable through compatibility defaults. There is no backfill, table/index change, or
data-loss risk.

Rollback reverts the branch and removes the new package/route/dependency. If the incremental
synthetic package was imported locally, its extra pre-release rows may remain inert; destructive row
deletion is not part of rollback. A clean development database can be recreated through the existing
migration/seed flow.

## Security and privacy

- The spike remains behind the existing same-origin invite session. Content preview authorization is
  unchanged.
- Fixtures and fallback images are original, synthetic, and non-personal. No student image, real
  exam, provider, external URL, telemetry, retention, or research use is introduced.
- Pydantic and the frontend boundary reject unknown fields/types before renderer import. Content
  never supplies functions, constructor calls, source strings, style maps, URLs, event handlers, or
  DOM markup.
- Application code owns the exhaustive constructor switch, JSXGraph attributes, event callbacks,
  animations, colors, labels-as-text behavior, and asset path convention.
- No `eval`, `Function`, JSXGraph JessieCode/parser, script injection, `dangerouslySetInnerHTML`, raw
  AI HTML/Markdown/SVG, or AI-generated JavaScript is used.
- Dynamic library failure and construction exceptions are caught, partial boards are freed, and a
  concise accessible fallback is shown without leaking exception details.
- Selection is limited by curated `selectable` capability and active ask-select allowlists. Actions
  cannot address an object outside the current scene.

## Dependency decisions

Add exactly `jsxgraph@1.13.2` as a direct production dependency of `@math-coach/student-web`.

- Purpose: selected MVP interactive-geometry renderer with native dependent constructions,
  pointer/multi-touch behavior, SVG output, ARIA attributes, and TypeScript declarations.
- Version/lock: exact version in `package.json` and `package-lock.json`; no CDN or runtime download.
- License: dual `(MIT OR LGPL-3.0-or-later)`; this project will use the MIT option and retain package
  notices through the lock/source distribution.
- Registry size: 10,982,285-byte tarball and 78,187,672 unpacked bytes before filesystem overhead.
  The package includes extensive source/docs, so installed size is not browser transfer size. It
  occupies 76 MiB in `node_modules`; the dynamically loaded production JavaScript chunk is
  1,151,137 bytes and 262,447 bytes when gzipped.
- Security: geometry content never reaches a parser/interpreter; the app uses only `initBoard`, the
  finite `board.create` switch, element attributes/events, and `freeBoard`. `npm audit --omit=dev`,
  exact-lock inspection, executable-path searches, and renderer failure tests all pass. The final
  production-only audit reports zero vulnerabilities. The official changelog notes recent
  source-output hardening; no safety claim relies on it.
- Compatibility: package metadata requires Node `>=20.19.0`. The root engine/setup contract now
  states `>=20.19`; verification used Node `24.14.0`.
- Alternatives rejected: GeoGebra embeds introduce an external product/runtime and broader authoring
  surface; a custom SVG/canvas engine would reimplement mathematical constraints and accessibility;
  generic canvas frameworks are expressly prohibited; `jsxgraph-react` adds an unnecessary wrapper
  and separate maintenance boundary. JSXGraph is already the approved architecture choice.

Official references inspected on 2026-08-27:

- <https://www.npmjs.com/package/jsxgraph>
- <https://jsxgraph.org/home/start/gettingstarted/>
- <https://jsxgraph.org/docs/symbols/JXG.JSXGraph.html>
- <https://jsxgraph.org/docs/symbols/JXG.Board.html>
- <https://jsxgraph.org/docs/symbols/JXG.GeometryElement.html>
- official element pages for Point, Segment, Line, Circle, Arc, Polygon, Angle, Midpoint,
  Intersection, Perpendicular, Parallel, Circumcircle, and Label.

## Test plan

### Unit: backend scene and action contract

- Accept representative valid scenes using every approved primitive and out-of-order declarations.
- Reject duplicate object IDs and duplicate initial-visible/animation/action/allowlist IDs.
- Reject unknown initial-visible IDs and unknown parents.
- Reject direct self-cycles and indirect multi-object cycles.
- Reject unsupported types and extra executable/markup fields such as `javascript`, `script`,
  `expression`, `html`, `svg`, and `onClick`.
- Reject non-finite/reversed viewport values, non-finite coordinates, missing point coordinates,
  coordinates on constructed objects, malformed parent counts, and invalid intersection branches.
- Reject each object-specific parent-type violation.
- Reject missing/blank accessibility descriptions and fallback asset IDs.
- Accept `draggable: true` only for free points; reject it on constructed/locked-capability objects.
- Reject unknown action targets, unknown animation IDs, non-point animate targets, duplicate target
  lists, ask-select IDs that are not selectable, and correct IDs outside the unique allowed set.
- Prove old Milestone 2 scene serialization/hash remains compatible when new capabilities are
  omitted.

### Unit: frontend validation and order

- Mirror every backend malformed-scene/action case at the unknown JSON boundary.
- Return the exact known-literal parent-first ID order for shuffled declarations.
- Return the same order for repeated identical inputs and for equivalent declaration permutations.
- Reject rather than return a partial order on direct or indirect cycles.
- Preserve generated contract types; compile-time checks fail if OpenAPI drifts.

### Unit: pure interaction state

- Create exact initial visible state in deterministic ID order.
- Cover show, hide, highlight, targeted/all clear-highlight, focus, and animate transitions.
- Reject unknown or capability-invalid targets without mutating prior state.
- Start ask-select with its exact allowlist and typed prompt.
- Ignore disallowed selections; accept pointer/touch/keyboard sources identically.
- Produce exact correct, incorrect, and ungraded response literals and deterministic JSON for
  identical scene/action/selection input.

### Component: renderer and geometry experience

- Show a labelled loading state, then an accessible ready scene with description and fallback
  disclosure.
- Translate every approved primitive in deterministic order at the external JSXGraph boundary.
- Configure only explicit free points as draggable; keep locked and constructed points fixed.
- Apply initial visibility and every typed action to DOM-visible state.
- Exercise click/touch callbacks and keyboard object controls through accessible names.
- Enforce ask-select allowlists and display deterministic response state.
- Emit a known geometric snapshot after permitted movement.
- Switch atomically to the static fallback for invalid input, import failure, board creation failure,
  and update failure; never leave a partial trusted board.
- Assert fallback `src` is the safe root-relative identifier path and `alt` uses the curated
  accessibility description.
- Assert no script, iframe, foreign object, arbitrary HTML/SVG markup, inline event attribute,
  external URL, or source-code field reaches rendered DOM.
- Render a typed geometry `ContentBlock` through content preview and preserve KaTeX, nested typed
  content, two-exam relevance, non-exhaustive solution wording, and safe API failure states.

### Integration/content validation

- Validate both committed synthetic packages and generated content schema.
- Import the incremental M4 package transactionally and idempotently after M2.
- Prove old immutable content remains unchanged and the new problem references an exact immutable
  scene version plus two exam relevance records.
- Authenticate and fetch the new preview; assert every primitive, interaction capability,
  accessibility/fallback field, and action survives JSONB revalidation.
- Assert each committed fallback asset exists for every committed scene asset ID.
- Regenerate and drift-check OpenAPI, TypeScript, and content JSON Schema.
- Run the existing two full migration downgrade/upgrade cycles; no new revision is expected.

### Browser/end-to-end

The new spec runs unchanged in all five projects. It will:

1. authenticate through FastAPI and enter **Geometry spike** from the workspace;
2. verify synthetic-only framing, required accessibility description, and fallback availability;
3. assert all primitive IDs exist after deterministic out-of-order construction;
4. use touch/click board selection and keyboard object selection;
5. start ask-select, prove a disallowed object cannot answer, then record allowed correct and
   incorrect deterministic responses;
6. exercise show, hide, highlight, clear, focus, and fixed pulse animation behavior;
7. drag the explicitly permitted free point and compare before/after constraint snapshots;
8. prove midpoint averaging, intersection incidence, perpendicular dot product, parallel cross
   product, and equal circumradii after movement within a documented numeric tolerance;
9. attempt pointer movement of a locked free point and constructed midpoint and prove coordinates do
   not change;
10. open the M4 content preview and prove its typed geometry block uses the same live renderer;
11. assert forbidden executable/external elements are absent; and
12. assert document width and every board/control/fallback/snapshot surface remain within the
    viewport.

### Exact device matrix

| Project                        | Engine          |   Viewport | Layout expectation                 |
| ------------------------------ | --------------- | ---------: | ---------------------------------- |
| `compact-chromium`             | Chromium, touch |  360 × 640 | single-column board/actions        |
| `pixel-7-chromium`             | Chromium, touch |  412 × 839 | single-column board/actions        |
| `iphone-13-webkit`             | WebKit, touch   |  390 × 664 | single-column board/actions        |
| `ipad-pro-11-portrait-webkit`  | WebKit, touch   | 834 × 1194 | scene/action split                 |
| `ipad-pro-11-landscape-webkit` | WebKit, touch   | 1194 × 834 | scene/action split + wide snapshot |

### Acceptance criteria

- Every approved primitive validates and renders from curated data only.
- Explicit parents produce one deterministic parent-first construction order.
- Duplicate IDs, unknown parents/targets, cycles, unsupported types, malformed fields, and invalid
  target capabilities reject safely before execution.
- No content-supplied executable code, expressions, handlers, HTML, Markdown, SVG, constructor name,
  URL, or style map is accepted or run.
- Only explicit draggable free points move; locked and constructed points cannot become independent.
- Midpoint, intersection, perpendicular, parallel, and circumcircle constraints remain true after
  permitted movement.
- All seven actions work through typed validated state and only existing compatible object IDs.
- Ask-select enforces its allowlist and returns deterministic response state.
- Every committed scene has a non-empty accessibility description and existing static fallback.
- Invalid/load/render failure shows a concise accessible fallback and no partial scene.
- Existing typed content preview uses the renderer without regressing multi-exam or math contracts.
- All five phone/tablet projects pass with no document-level horizontal overflow.
- `make check`, focused geometry commands, generated drift checks, audit, diff review, and final rebase
  evidence are recorded truthfully.

## Manual QA

1. Start the isolated branch API/web services and sign in with the local synthetic invite.
2. Open **Geometry spike** at 360 × 640. Read the description, open the static fallback, traverse all
   controls by keyboard, and confirm visible focus and at least 44 px touch targets.
3. Tap/click selectable board objects. Start ask-select, try one disallowed object, then submit allowed
   incorrect and correct objects; compare the response text to the action key.
4. Run each action and visually confirm visibility, highlight, clear, focus, and reduced-motion-safe
   pulse behavior.
5. Drag only the permitted point. Observe midpoint/intersection/line/circle dependencies and the
   constraint monitor update. Try to drag the locked point and constructed midpoint.
6. Repeat pointer/touch/keyboard interaction at Pixel 7 and iPhone 13 emulations.
7. At iPad portrait and landscape widths, verify the split layout, board aspect ratio, action tray,
   snapshot legibility, and absence of page overflow.
8. Open the M4 problem from content preview and verify its typed geometry block and validated hint
   actions use the same renderer.
9. Simulate the component's renderer-unavailable state in the documented test surface and verify the
   description plus static image remain useful.
10. Inspect final screenshots for label legibility, touch spacing, focus visibility, fallback quality,
    clipped lines/arcs, and horizontal containment.

Expected outcome: the same versioned scene and action inputs produce the same construction/state,
only reviewed interactions are possible, all dependent geometry remains constrained, and failure
never exposes a partial or executable scene.

## Rollout and rollback

Deploy after Milestone 3. The route and content are authenticated/internal and synthetic; no feature
flag or persistent learner state is needed. Seed the incremental package after the existing M2
package in deterministic lexical order.

Rollback reverts the UI, generated schemas, incremental package, static assets, and JSXGraph lock.
It requires no database downgrade or backfill. Imported pre-release M4 content can remain withdrawn
or be removed only through an explicitly approved development-database rebuild; this branch will not
manually delete shared database rows.

## Branch and commit plan

1. `docs: add Milestone 4 change plan`
2. `test: define strict geometry scene contract`
3. `feat: validate and order curated geometry scenes`
4. `feat: add deterministic geometry interaction state`
5. `feat: render curated JSXGraph scenes`
6. `feat: integrate geometry preview and spike`
7. `test: cover geometry device regressions`
8. `docs: record interactive geometry architecture`
9. `docs: record final Milestone 4 verification`

Tests are committed with the behavior they drive where practical. Each vertical slice begins with a
confirmed red failure and reaches focused green before the next slice.

## Conflict coordination

Owned files are exactly those in **Files and components**. Shared surfaces are Pydantic content
schemas, generated contracts, package/lock files, root formatting scripts, global CSS, typed content
rendering, content preview, interaction-shell navigation, and the committed content root. No remote
branch is currently unmerged from `origin/main`; the dirty shared checkout remains out of scope.

Integration order is Milestone 2 content → completed Milestone 3 → this Milestone 4 branch →
Milestone 5. If another active branch changes the geometry/content contract, generated files, common
CSS, or preview shape, coordinate the authoritative Pydantic contract first. Any rebase conflict that
changes behavior or a public contract stops implementation until this plan is updated; affected
tests and `make check` must then be rerun.

## Risks

- JSXGraph's package is large on disk and browser-only. Mitigation: one exact dependency, one focused
  client boundary, dynamic local import, no wrapper package, and final installed/bundle measurements.
- JSXGraph accepts functions and several code-oriented formats, but the application needs closures
  internally for dependent labels. Mitigation: content schema cannot express functions/source;
  application code owns the exhaustive constructor switch and all closures; parser/interpreter APIs
  are never imported or called.
- Incorrect parent typing could create a valid graph that fails at construction time. Mitigation:
  validate parent capabilities in both Pydantic and the frontend boundary before import, plus one
  representative primitive fixture and failure cleanup.
- Dragging can accidentally make a constructed point free. Mitigation: only parentless points may
  declare `draggable`, all others are fixed, and real-browser constraints/locked-drag attempts run in
  Chromium and WebKit.
- JSXGraph internal numeric tolerances may vary slightly by engine. Mitigation: assert mathematical
  invariants with documented tolerances, not pixel-perfect coordinates, while keeping scene/state
  ordering exact.
- Pointer handlers can differ across click/touch/WebKit. Mitigation: JSXGraph native element events,
  a parallel keyboard selection list, and the exact five-project matrix.
- Labels or fallback IDs could become markup/URL injection paths. Mitigation: bounded plain text,
  identifier-only root-relative asset paths, React text nodes/disabled text parsing, and adversarial
  DOM tests.
- A missing fallback asset is not currently a database relationship. Mitigation: committed-content
  validation tests resolve every synthetic scene ID to a real public file; permanent docs mark the
  convention until a later production asset service supplies signed URLs.
- New default fields could alter immutable hashes. Mitigation: exclude inactive compatibility fields
  from canonical serialization and regression-test the original M2 scene/item hash.
- The user requested a pre-implementation checkpoint and the TDD skill requires agreed seams.
  Mitigation: implementation began only after the project owner confirmed the recorded seams and
  file set with “process it.”

## Progress

- [x] Repository inspected
- [x] Plan reviewed
- [x] Branch created from current main
- [x] Tests written or updated
- [x] Implementation complete
- [x] Documentation updated
- [ ] Relevant checks pass
- [x] Diff reviewed
- [ ] Branch rebased on current main
- [ ] Conflict resolution re-tested
- [ ] Handoff summary written

## Decisions

- 2026-08-27: The project owner approved the proposed owned-file boundary and six public TDD seams
  with “process it”; implementation may proceed through the recorded red-green slices.
- 2026-08-27: Use the existing FastAPI/Pydantic geometry contract as authoritative and regenerate
  all downstream artifacts. A second frontend-owned canonical schema is rejected.
- 2026-08-27: Lock JSXGraph `1.13.2` exactly because the repository architecture selects JSXGraph,
  current official registry/docs identify this release, Node `24.14.0` satisfies its engine, and the
  production-only audit reports zero vulnerabilities.
- 2026-08-27: Keep the database unchanged because scenes/actions are already immutable versioned
  JSONB. Add new content identities instead of modifying old immutable versions.
- 2026-08-27: Use stable-ID topological order with lexical ready-queue tie breaking so declaration
  permutation cannot change construction order.
- 2026-08-27: Treat omission of `draggable` and `selectable` as false. Only explicit true capability
  is interactive.
- 2026-08-27: Implement the existing animation action as one application-owned pulse effect selected
  by a scene allowlisted ID. Scene data cannot define motion code or CSS.
- 2026-08-27: Provide keyboard selection through a labelled object list in addition to direct board
  pointer/touch events; SVG internals are not the only accessible interaction path.
- 2026-08-27: Add an incremental synthetic M4 content package rather than rewriting the released M2
  package or importing real content.
- 2026-08-27: Raise the repository Node engine/setup contract from `>=20.9` to `>=20.19` rather than
  advertise a version rejected by the locked JSXGraph package.
- 2026-08-27: Use application-owned minimal JSXGraph integration styles because the package export
  map does not expose its stylesheet as a supported Next.js subpath.
- 2026-08-27: Keep Playwright's normal ports as defaults while allowing explicit isolated web/API
  ports. The shared Milestone 3 servers and dirty checkout remain untouched.
- 2026-08-27: Treat viewport and coordinate numbers as strict finite values at Pydantic and browser
  boundaries; numeric strings and booleans are malformed rather than coercible curated data.
- 2026-08-27: Bind JSXGraph teardown to its receiver and contain third-party cleanup exceptions so
  leaving a live preview cannot replace the workspace with a Next.js error boundary.

## Discoveries

- `origin/main` is exactly the requested completed Milestone 3 commit.
- The original shared checkout is dirty, making the user-requested clean worktree mandatory.
- Milestone 2 already anticipated almost the entire action vocabulary and all primitive names, so
  Milestone 4 is a compatible semantic deepening rather than a new geometry schema.
- The existing Pydantic graph traversal detects cycles but does not expose a construction order and
  does not validate object-type compatibility.
- Existing content names a fallback asset that is not present in the web public fixtures.
- JSXGraph 1.13.2 includes a much larger unpacked development/documentation tree than its browser
  core; installed size and delivered bundle size must be reported separately.
- JSXGraph natively provides the required midpoint, intersection, perpendicular, parallel, and
  circumcircle dependencies, so constraint preservation should remain within the selected engine
  rather than a second custom geometry solver.
- JSXGraph's stylesheet path is not exported by `jsxgraph@1.13.2`; unsupported package-subpath
  imports fail the Next.js build. The board needs only a small set of application-owned styles.
- JSXGraph's `freeBoard` uses its `JXG.JSXGraph` receiver internally. Storing the bare method passed
  unit mocks but failed real client navigation; a receiver-sensitive regression now protects the
  bound teardown path.
- JSXGraph creates one hidden empty `foreignObject` as internal board infrastructure. The safety
  contract rejects scene-provided SVG/markup before rendering; it does not ban locked renderer-owned
  SVG nodes.

## Verification evidence

- `git fetch origin main` completed on 2026-08-27.
- `git rev-parse origin/main` returned
  `3bc9206c1adc0ee3b11a2adb016d8196a64cd58e`.
- `git merge-base --is-ancestor 3bc9206 origin/main` exited 0.
- `git worktree add -b feat/m4-interactive-geometry-engine /home/minh/dev/math-coach-m4
origin/main` created a clean isolated branch/worktree at the exact base.
- Required root/local instructions, `PLANS.md`, the complete MVP plan, the authoritative completed
  Milestone 3 ChangePlan, both permanent architecture documents, existing geometry/content schemas,
  generated geometry contract sections and generation commands, fixtures, preview/runtime guards,
  relevant backend/frontend/browser tests, package configuration, device report, release/device
  docs, and installed Next.js client/CSS/image/lazy-loading/accessibility guidance were inspected.
- Current official JSXGraph package/getting-started/API/element documentation was inspected.
- `npm view jsxgraph@1.13.2 ... --json` and `npm pack --dry-run --json jsxgraph@1.13.2` produced the
  version, license, engine, dependency, tarball, and unpacked-size evidence recorded above without
  changing repository files.
- The pre-change `make check` baseline passed with 66 frontend tests, 25 backend unit tests, 19
  integration tests, two full migration cycles, and 10 E2E cases.
- Focused red-green commands exercised each contract, ordering, reducer, component, integration,
  and browser slice. The final receiver-sensitive board test passes 5/5; strict backend geometry
  tests pass 42/42; and the strengthened real-renderer geometry spec passes all five projects in
  5.4 seconds.
- `npm audit --omit=dev` reports zero vulnerabilities; `du -sh node_modules/jsxgraph` reports 76 MiB;
  the matching production chunk measures 1,151,137 bytes and 262,447 bytes with gzip.
- A pre-final isolated `make check` completed formatting, lint, type checks, contract/content drift,
  production build, 120 frontend tests, 65 backend unit tests, 23 integration tests, two migration
  cycles, and 15 E2E cases. The subsequent strict-number and expanded browser assertions require the
  final post-rebase root rerun before handoff.

## Result

Implementation, permanent documentation, synthetic fixtures, and focused regression/device
verification are complete. Final root verification, the required fetch/rebase, conflict audit, and
handoff evidence remain before this plan can be closed.
