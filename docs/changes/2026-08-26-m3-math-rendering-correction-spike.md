# Milestone 3 mathematical rendering and correction spike

## Metadata

- Status: complete
- Owner: Codex implementation; project owner approval
- Branch: `feat/m3-math-rendering-correction-spike`
- Base commit: `984da70f7fb0e51446054f7dea3c852fca08dac0`
- Related milestone: Milestone 3 — Mathematical rendering and correction spike
- Related issue/ticket: None
- Started: 2026-08-26
- Last updated: 2026-08-27

## Context

Milestone 2 is the current `origin/main` tip at `984da70` and supplies strict versioned typed content,
multi-exam records, immutable problem versions, an authenticated content preview, generated API
contracts, and five Playwright phone/tablet projects. Its preview deliberately exposes math source as
plain text because KaTeX and MathLive were deferred to Milestone 3. The repository has no controlled
math-rendering boundary, visual mathematics editor, typed transcript-state module, transcript
correction operations, confirmation snapshot, correction-spike route, or math/device regression
report.

Milestone 3 must prove the correction interaction using only clearly synthetic deterministic
fixtures. It must not introduce AI output, grading, a transcript API, learner-state changes, or a
database migration. Future transcription payloads are untrusted even though this spike's fixture is
local and deterministic.

## Goal

Deliver an authenticated internal correction spike in which:

- typed problem and preview mathematics render through one controlled KaTeX boundary;
- invalid or unsafe mathematics produces a concise accessible placeholder without exposing source;
- every mathematics transcript block remains visually editable with MathLive;
- typed text/math blocks and steps support deterministic add, delete, reorder, split, and merge
  operations with stable IDs and enforced ownership invariants;
- confirmation serializes the exact visible order as the future authoritative grading input;
- phone projects use PHOTO/TRANSCRIPT tabs and tablet projects use a simultaneous photo/transcript
  split without document-level horizontal overflow;
- the committed rendering corpus, component tests, state tests, browser tests, and device report
  cover the Milestone 3 regression contract.

## Non-goals

- AI transcription, evaluation, grading, hints, uncertainty decisions, or provider integration.
- Persisting transcript drafts or confirmed snapshots through an API or database.
- Changing the Milestone 2 content schema or generated OpenAPI/TypeScript contracts.
- Camera capture, direct pen input, voice input, raw-LaTeX editing, or a generic rich-text editor.
- Markdown or HTML rendering, sanitization frameworks, executable geometry, generated scripts, or
  arbitrary code execution.
- Interactive geometry, learner state, daily planning, RAG, vector storage, or real exam content.
- Drag-and-drop as a required or exclusive interaction.

## User-visible behavior

- An authenticated internal learner can open **Correction spike** from the existing workspace.
- A clearly labelled synthetic paper image and deterministic transcript are shown side by side at
  tablet widths.
- Phone widths expose an accessible PHOTO/TRANSCRIPT tab list and keep only the chosen panel active.
- The transcript contains ordered steps made of explicit text and mathematics block variants.
- Text blocks use ordinary text inputs. Mathematics blocks expose MathLive's visual editor and a
  separate controlled KaTeX preview; students never see or edit a raw-LaTeX field.
- Valid mathematics is typeset. Empty, malformed, unsupported, untrusted-command, over-expansion,
  or source-length failures show **Math needs correction** and keep the visual editor available.
- Labelled buttons add text/math blocks, delete blocks, move blocks up/down, split before a block,
  merge adjacent steps, and move steps up/down. All operations work without drag-and-drop.
- Confirming shows a typed ordered snapshot and identifies it as the future authoritative grading
  input. It performs no grading and makes no AI claim.
- Existing content-preview problem, solution, rubric, hint, callout, and rich-line math moves from
  source-text preview styling to the same controlled read-only renderer.

## Current-state findings

- `git fetch origin main` resolved `origin/main` to
  `984da70f7fb0e51446054f7dea3c852fca08dac0`; `git merge-base --is-ancestor 984da70 origin/main`
  succeeded. Milestone 2 is therefore present at the required commit and is the fetched tip.
- The shared checkout is on `chore/bootstrap-chuyen-toan-corpus`, is ahead/behind `origin/main`, and
  has an unrelated tracked ChangePlan modification. Its unrelated/untracked corpus work was not
  inspected, formatted, staged, stashed, or discarded. This branch instead uses the clean separate
  worktree `/home/minh/dev/math-coach-m3` created directly from `origin/main`.
- No remote branch is ahead of or unmerged with the fetched `origin/main` at inspection time.
- The web app is Next.js `16.3.2`, React `19.2.8`, strict TypeScript `5.9.3`, Vitest `4.1.11`, and
  Testing Library. The current App Router pages are Server Components that compose focused Client
  Components for session and interaction state.
- Repository-local Next.js guidance requires reading the installed `node_modules/next/dist/docs/`
  rather than relying on remembered APIs. Relevant App Router page/layout, Server/Client Component,
  global/external CSS, client-only third-party library, lazy-loading, and accessibility guidance was
  read before this plan.
- External package stylesheets may be imported from the App Router, and browser-only third-party
  components should live behind a focused Client Component. `next/dynamic` with `ssr: false` must
  itself be declared in a Client Component.
- `ContentBlock` is generated from FastAPI/Pydantic and already discriminates text, inline math,
  display math, rich-line spans, geometry, image, and recursive callout content. The client validates
  nested preview payloads at runtime, but `content-preview.tsx` currently renders every `latex` value
  as text.
- The Milestone 2 synthetic package already supplies inline/rich-line/display expressions and is the
  appropriate existing typed-content migration target. No schema widening is needed.
- The existing internal route pattern checks the same-origin authenticated session through FastAPI.
  The correction route can reuse `getCurrentUser()` and expose no new endpoint.
- The root command contract exists: setup, format, format-check, lint, typecheck, unit, integration,
  E2E, content validation, build, test, and check. `make check` includes production build, all unit and
  integration tests, content/API drift checks, and every Playwright project.
- Vitest coverage currently includes `components/**/*.tsx` and `lib/**/*.ts`; it must include the new
  pure `features/transcription` state module rather than leaving the core invariant logic outside the
  coverage gate.
- The Playwright matrix is compact Chromium `360x640`, Pixel 7 Chromium `412x839`, iPhone 13 WebKit
  `390x664`, iPad Pro 11 portrait WebKit `834x1194`, and iPad Pro 11 landscape WebKit `1194x834`.
- Baseline `make check` passed formatting, lint, type checks, API drift, content validation,
  production build, 24 frontend tests, 25 backend unit tests, two complete migration cycles, and 19
  integration tests. Its final E2E phase failed all five projects because ports 3000/8000 were already
  occupied by the original shared worktree's running Next/FastAPI processes. The launcher treated
  those existing processes as ready, so the browser saw that other branch and timed out looking for
  Milestone 2's content-preview link. A non-conflicting diagnostic run on 3100/8100 reached this
  branch but direct object-storage upload failed from the alternate browser origin; it is not claimed
  as an E2E pass. The standard-port five-project baseline must be rerun when the owner processes are
  no longer occupying those ports, without stopping or disturbing them here.

## Design

### Controlled KaTeX boundary

`MathRenderer` is the only read-only mathematics entry point. It accepts a source string and an
explicit inline/display mode, calls the KaTeX DOM renderer without React
`dangerouslySetInnerHTML`, and never puts the source or thrown error message in failure-state DOM. It
renders into a detached staging node and commits that output only after all safety checks pass. It
uses:

```text
throwOnError: true
trust: callback that records an attempt and always returns false
strict: "error"
maxExpand: 100
maxSize: 10
output: "htmlAndMathml"
fresh empty macros per render
maximum input length: 2,000 UTF-16 code units
```

Empty/whitespace-only or over-length input fails before KaTeX. KaTeX parse errors, unsupported
commands, trust failures, and expansion-limit failures converge on one safe placeholder. KaTeX's
official guidance warns that both built-in `throwOnError: false` rendering and thrown error messages
may expose source; this boundary deliberately catches with `throwOnError: true` and discards details
from user-facing output. The always-false trust callback prohibits link/image/HTML commands and lets
the boundary reject KaTeX's otherwise source-revealing unsupported-command rendering. A fresh macro
map and `globalGroup: false` prevent one block from changing another block's rendering. CSS contains
every renderer to the available width; large display output may scroll inside its labelled math
container, but may never expand the document.

The existing typed-content preview delegates inline math, display math, rich-line math spans, and
nested callout math to this renderer. Text stays ordinary React text nodes; arbitrary HTML and
Markdown are never accepted or rendered.

### MathLive visual editor

`MathLiveEditor` is a small Client Component around the official `<math-field>` custom element. The
browser-only package is loaded from the locked local dependency, not a CDN. The wrapper sets and
reads the element's `value` property and handles its public `input` event; it does not place the
source string in children, an input field, a data attribute, or visible fallback text. It gives each
field a concise accessible label, leaves the built-in touch virtual-keyboard policy enabled, and
supports physical-keyboard correction. A loading fallback describes the visual editor without
showing source. Package font styles/assets are integrated through the supported local package CSS
entry and production build; no external runtime asset host is introduced.

Each math transcript block always renders the MathLive field, including when its KaTeX preview is in
a failure state. This makes the failure correctable without asking the student to understand or edit
raw LaTeX.

### Transcript state and invariants

The local canonical state uses a closed union and stable caller-supplied IDs:

```typescript
type TranscriptBlock =
  | { id: string; stepId: string; type: "text"; text: string }
  | { id: string; stepId: string; type: "math"; latex: string };

type TranscriptStep = { id: string; blockIds: string[] };

type TranscriptState = {
  schemaVersion: "1.0.0";
  attemptId: string;
  blocks: TranscriptBlock[];
  steps: TranscriptStep[];
};
```

Pure operations accept explicit IDs rather than time/randomness, return a new immutable state, and
validate their result. Invariants require unique non-empty block/step IDs, at least one step, at least
one block per step, exactly one step reference per block, matching `block.stepId`, no unknown block
references, and no unreferenced block. Array order is canonical.

Block moves are within their owning step and use explicit up/down controls. Adding inserts at an
explicit location. Deleting the only block of a step is rejected, keeping the state correctable and
structurally valid. Splitting before a non-first block creates two non-empty steps, keeps the original
step ID for the leading segment, assigns the explicit new step ID to the trailing segment, and updates
only moved blocks' `stepId`. Merging a step into its previous step concatenates block IDs in visible
order and updates ownership. Step movement swaps adjacent steps only. Invalid IDs, impossible
boundaries, and duplicate IDs fail explicitly without mutating input.

Confirmation first validates invariants and then emits a deeply independent, ordered typed snapshot
with the schema version, attempt ID, step array, and blocks in visible step/block order. It includes
no timestamp, score, grading result, hidden reasoning, or AI metadata, so identical visible inputs
serialize identically. The confirmation UI labels this snapshot as the future authoritative grading
input.

### Authenticated synthetic correction route

`/internal/math-correction` is a static App Router page composing a Client Component that checks the
existing authenticated session before exposing fixtures. Checking, authentication-required,
retryable failure, and ready states are explicit. The fixture uses synthetic IDs and a committed
original synthetic paper illustration with a prominent synthetic label. No participant image or
provider payload is used.

At widths below `768px`, the route renders an accessible PHOTO/TRANSCRIPT tablist with correct
selected/tab-panel state and keyboard focusable controls. At `768px` and above, both panels are
visible in a two-column split and the phone tablist is hidden. All reorder operations use labelled
minimum-touch-target buttons and disabled boundary states rather than drag-and-drop.

### Test seams and TDD slices

The proposed public seams, which require project-owner confirmation before the first test, are:

1. `MathRenderer` DOM output: rendered accessible math or source-free correctable placeholder.
2. Pure transcript-state exports: operation result, invariant validation, and confirmation snapshot.
3. `MathLiveEditor` public `value`/`onInput` interaction through the rendered custom element.
4. `TranscriptEditor` user controls and visible ordered state, including confirmation.
5. `/internal/math-correction` authenticated browser behavior and responsive layout across the five
   existing Playwright projects.
6. `ContentPreview` typed-content output proving existing preview mathematics crosses the renderer.

Implementation will proceed in vertical red/green slices at those seams: one failing behavior test,
the minimum implementation to pass it, then the next behavior. Internal KaTeX calls, React state
setters, and module implementation details will not be mocked or asserted. MathLive itself is a
browser boundary in component tests; jsdom will use a minimal public custom-element test double,
while Playwright exercises the real locked package.

### Dependency decisions

Registry metadata and current official documentation were checked on 2026-08-26. Versions will be
exactly locked in `package.json` and `package-lock.json`:

- `katex@0.18.4`: production read-only typesetting boundary; MIT. Registry unpacked size is
  4,034,233 bytes plus locked `commander@8.3.0` at 151,267 bytes (4,185,500 bytes / 3.99 MiB total
  installed production tree before npm filesystem overhead). KaTeX is required by the milestone.
  MathJax was considered but rejected because the specified renderer is KaTeX and a second math
  rendering engine would enlarge and split the safety boundary. Hand-built formula HTML/SVG was
  rejected as incomplete and inaccessible.
- `mathlive@0.110.0`: production visual mathematics editor and touch virtual keyboard; MIT. Registry
  unpacked size is 5,748,726 bytes. Its locked production tree adds
  `@cortex-js/compute-engine@0.58.0`, `decimal.js@10.6.0`, `complex-esm@2.1.1-esm1`, and
  `@arnog/colors@0.5.0`, for 27,079,799 bytes / 25.83 MiB unpacked before npm filesystem overhead.
  MathLive is required by the milestone. MathQuill was considered but rejected because it is not the
  selected product contract and would require a separate integration/accessibility assessment. A
  generic rich-text framework was rejected because transcript structure is a small typed domain and
  mathematics must remain in a purpose-built visual editor.

The combined registry-reported installed production tree is 31,265,299 bytes / 29.82 MiB before npm
filesystem overhead. Actual locked `node_modules` disk usage and route/build output will be measured
after installation and recorded in verification evidence. Package size is not equivalent to bytes
sent to the browser; the production build and browser behavior will verify the integration.

Official references used for the design:

- <https://katex.org/docs/options>
- <https://katex.org/docs/security>
- <https://katex.org/docs/error>
- <https://mathlive.io/mathfield/guides/react/>
- <https://mathlive.io/mathlive/guides/integration/>
- <https://mathlive.io/mathfield/guides/virtual-keyboard/>
- <https://mathlive.io/mathfield/api/>

## Multi-exam impact

- Study profiles: no change.
- Exam targets: no change; no singular target field or rendering is introduced.
- Exam-specific progress: no change.
- Shared skill state: no change.
- Daily-plan balancing: no change.

The route is an internal attempt-correction fixture and makes no assumption about a learner having one
target examination. Existing multi-exam content preview behavior remains covered.

## Files and components

Proposed and owned by this branch:

- `docs/changes/2026-08-26-m3-math-rendering-correction-spike.md` — living execution record.
- `docs/architecture/math-rendering-and-transcript-state.md` — permanent controlled-renderer,
  MathLive, transcript-state, confirmation, security, and rollback contract.
- `docs/architecture/versioned-content-and-multi-exam.md` — replace its now-stale statement that
  KaTeX and MathLive are future milestones with a link to the Milestone 3 boundary.
- `docs/evaluation/m3-math-rendering-device-report.md` — committed corpus and exact five-project
  phone/tablet regression results.
- `README.md` — internal correction route and focused verification commands.
- `package.json` — include new owned documentation in root formatting checks only.
- `package-lock.json`, `apps/student-web/package.json` — exact KaTeX and MathLive production locks.
- `apps/student-web/app/layout.tsx` — supported package CSS/font entry imports.
- `apps/student-web/app/globals.css` — contained math, visual-editor, transcript controls, phone tabs,
  tablet split, touch targets, failure, and snapshot styles.
- `apps/student-web/app/internal/math-correction/page.tsx` — internal App Router entry.
- `apps/student-web/public/fixtures/synthetic-correction-sheet.svg` — clearly labelled original
  synthetic/non-personal paper illustration with no executable content.
- `apps/student-web/components/interaction-shell.tsx` — link to the internal correction spike.
- `apps/student-web/components/content-preview.tsx` and its test — migrate all applicable typed math
  to the controlled renderer and prove no source fallback.
- `apps/student-web/components/math/math-renderer.tsx` and test — single bounded KaTeX boundary and
  regression corpus.
- `apps/student-web/components/math/content-blocks.tsx` — reusable generated-`ContentBlock`
  renderer for preview content.
- `apps/student-web/components/math/mathlive-editor.tsx` and test — client-only visual editor wrapper
  and public event interaction.
- `apps/student-web/features/transcription/transcript-state.ts` and test — closed types, invariants,
  pure immutable operations, and confirmation serialization.
- `apps/student-web/features/transcription/synthetic-fixture.ts` — deterministic fixture state and
  ID allocation inputs.
- `apps/student-web/components/transcription/correction-spike-app.tsx` and test — session gate,
  explicit route states, fixture orchestration, and responsive panel selection.
- `apps/student-web/components/transcription/transcript-editor.tsx` and test — mixed block editing,
  accessible operations, correction, and confirmation workflow.
- `apps/student-web/vitest.config.ts` — include the pure transcription feature in coverage.
- `apps/student-web/vitest.setup.ts` — only if required for a reusable standards-shaped math-field
  jsdom test double; no application behavior will be hidden here.
- `tests/e2e/math-correction.spec.ts` — authenticated real-browser correction, layout, accessibility,
  overflow, source-leak, and confirmation checks in every configured project.

`playwright.config.ts`, FastAPI code, migrations, content packages/schema, OpenAPI, and generated API
declarations are not expected to change. If implementation proves a listed file unnecessary or a new
owned file necessary, this section will be updated before that file is changed.

No unrelated files in the original shared worktree or corpus/data paths are owned, read, formatted,
staged, stashed, or discarded.

## API and schema changes

No HTTP API, OpenAPI, generated API client, content-package schema, or AI schema change. The
transcript union and confirmed snapshot are frontend-local Milestone 3 spike types. They are designed
to inform the future authoritative transcript API but are not presented as a server contract.

## Database and migration

None. No table, column, index, data backfill, migration, or persistent transcript is introduced.
Rollback has no data-loss risk because all correction state is local synthetic fixture state.

## Security and privacy

- The internal correction component requires the existing invite-authenticated same-origin session
  before rendering fixture content; unauthenticated and unavailable states are explicit.
- Only clearly labelled original synthetic/non-personal fixtures are committed. No image upload,
  student work, real exam content, personal data, AI provider, retention, or logging behavior changes.
- Every source string is treated as untrusted at the renderer boundary. KaTeX trusted commands are
  disabled; strict mode, macro expansion, element size, and input length are bounded.
- Neither source nor KaTeX exception text is placed in failure-state DOM, ARIA labels, titles, data
  attributes, logs, snapshots, or user messages.
- React never uses `dangerouslySetInnerHTML` for arbitrary or AI-provided content. KaTeX writes only
  to its dedicated empty DOM host through its documented renderer.
- No arbitrary AI HTML/Markdown, scripts, event-handler attributes, external images, URLs, executable
  geometry, or generated code is accepted or run.
- MathLive is installed and bundled locally. No runtime CDN request or new external data processor is
  introduced.
- Confirmation is visibly labelled as future authoritative grading input but remains local and
  performs no grading.

## Test plan

### Unit: transcript state

- Reject duplicate block IDs, duplicate step IDs, empty steps, unknown references, multiply
  referenced blocks, orphaned blocks, and mismatched `stepId` ownership.
- Add text and math at explicit positions without mutating input; reject duplicate/new-unknown IDs.
- Delete a block and remove its one reference; reject deleting the only block in a step.
- Move blocks up/down deterministically and preserve disabled boundaries.
- Split before a middle block, preserve order, ownership, IDs, and non-empty steps; reject invalid
  split boundaries.
- Merge with the previous step, preserve leading/trailing block order, update ownership, and remove
  only the merged step; reject the first-step merge.
- Move steps up/down deterministically without changing internal block order.
- Serialize an independent confirmation snapshot whose blocks match exact visible step/block order
  and whose JSON is identical for identical state.

### Component: controlled renderer

- Render inline and display mathematics with accessible MathML/visual KaTeX output.
- Cover fractions, nested fractions, powers, subscripts, roots, systems, cases, inequalities,
  congruences, sets, logic, matrices, geometry symbols, Vietnamese mixed inline math, and multi-line
  derivations.
- Produce the same safe correctable placeholder for malformed input, unsupported commands,
  `\\href`/`\\includegraphics`/`\\html*` trusted-command attempts, deliberate over-expansion,
  over-length source, and empty mathematics.
- Cap a deliberate `\\rule` oversized element at the configured renderer bound and contain it within
  the math host.
- Assert failure DOM—including text, attributes, title, and accessible name—contains neither the raw
  fixture source nor a KaTeX error excerpt.
- Assert no script, arbitrary HTML, external resource element, or event-handler attribute is emitted.

### Component: MathLive and workflow

- Load the visual math field with an accessible label without source text children or raw-source
  form controls.
- Propagate the public MathLive `input` value to typed state.
- Correct the fixture's invalid expression through the visual editor and observe the controlled
  preview transition from placeholder to rendered mathematics.
- Edit mixed text/math lines while preserving block variants and order.
- Exercise add/delete/move block and split/merge/move step controls with keyboard/user events.
- Verify boundary buttons are disabled and every operation has an accessible name independent of an
  icon.
- Confirm and assert the exact known-good literal snapshot ordering and future-authoritative label.
- Verify authentication checking, required, retryable, and ready route states.
- Verify phone tab semantics and tablet simultaneous-panel classes without relying only on CSS
  snapshots.

### Existing typed-content regression

- Replace preview source-text assertions with rendered KaTeX assertions for inline, display,
  rich-line, solution, hint, rubric, and nested callout math where present.
- Supply invalid typed math and assert the source-free placeholder while surrounding typed text and
  multi-exam data remain intact.
- Preserve runtime rejection of malformed nested API payloads.

### Browser/end-to-end

The new spec runs unchanged in all five configured projects. It will:

1. authenticate through the real local FastAPI session;
2. open the correction route from the workspace and verify the synthetic-only label;
3. assert PHOTO/TRANSCRIPT tabs on the three phone projects or simultaneous split panels on the two
   iPad projects;
4. verify valid inline/display math has KaTeX output and invalid math has the source-free placeholder;
5. focus the real MathLive field and correct the invalid expression with keyboard input;
6. exercise at least one accessible block move, step split/merge/reorder, and touch/click operation;
7. confirm and compare the visible ordered state with the displayed typed snapshot summary;
8. inspect document width and every controlled math/editor/control container for horizontal overflow;
9. inspect failure-state body text, accessible attributes, and markup for the known raw source and
   forbidden executable/external elements;
10. preserve the existing foundation upload and content-preview journey.

### Exact device matrix

| Project                        | Engine          |   Viewport | Layout expectation     |
| ------------------------------ | --------------- | ---------: | ---------------------- |
| `compact-chromium`             | Chromium, touch |  360 × 640 | PHOTO/TRANSCRIPT tabs  |
| `pixel-7-chromium`             | Chromium, touch |  412 × 839 | PHOTO/TRANSCRIPT tabs  |
| `iphone-13-webkit`             | WebKit, touch   |  390 × 664 | PHOTO/TRANSCRIPT tabs  |
| `ipad-pro-11-portrait-webkit`  | WebKit, touch   | 834 × 1194 | photo/transcript split |
| `ipad-pro-11-landscape-webkit` | WebKit, touch   | 1194 × 834 | photo/transcript split |

The committed device report will record each project's exact result, correction behavior, control
method, overflow measurement, source-leak result, and screenshot/manual inspection status. Physical
devices and Apple Simulator are pre-pilot validation and are not claimed by this Linux milestone.

### Acceptance criteria

- Every read-only typed math path uses `MathRenderer`; no preview path prints source as fallback.
- Valid regression expressions render through KaTeX in correct inline/display mode.
- Invalid/unsafe/empty expressions always show a concise accessible correctable placeholder and keep
  the visual editor available.
- No raw source from a failure fixture appears anywhere in the complete failure-state DOM.
- KaTeX trust is false; strict mode, macro expansion, user size, and input length are finite.
- MathLive provides a keyboard/touch visual editor without a raw-LaTeX form field.
- Transcript state has stable unique IDs, explicit variants, exact one-step ownership, deterministic
  ordering, and no orphan/multiple references after any operation.
- Split/merge preserves block order; confirmation matches exact visible order and is identified as
  future authoritative grading input.
- The route is authenticated and uses only clearly synthetic fixtures.
- All three phone projects show tabs; both iPad projects show split layouts.
- No configured project has document-level horizontal overflow.
- Existing content validation, API drift, database integration, upload, auth, multi-exam preview, and
  all root checks remain green.

## Manual QA

After automated checks:

1. Start `make dev-api` and `make dev-web` in the clean worktree and sign in with the documented local
   invite.
2. Open **Correction spike** and verify the prominent synthetic fixture label.
3. At `360x640`, switch PHOTO and TRANSCRIPT using pointer and keyboard, then traverse every control
   with Tab/Shift+Tab and verify visible focus and concise names.
4. Focus each MathLive field, use its visual keyboard toggle where available, correct the invalid
   expression, and verify the placeholder becomes rendered math without any visible source string.
5. Add one text and one math block; delete a non-only block; move blocks; split, merge, and reorder
   steps; verify the visible order after each operation.
6. Confirm and compare the snapshot step/block order with the transcript above it. Verify no grade,
   score, or AI result appears.
7. Repeat visual inspection at Pixel 7, iPhone 13, iPad portrait, and iPad landscape emulations.
8. At every size, inspect the page and long/oversized math fixtures for horizontal overflow and make
   sure only the math container may scroll locally.
9. Inspect content preview to verify existing inline/display/rich-line and nested typed math is
   typeset through the same boundary.

Expected outcome: every fixture is visibly correctable without raw-LaTeX knowledge, ordered typed
state remains deterministic, and phone/tablet layouts remain accessible and contained.

## Rollout and rollback

This is an authenticated internal route with local deterministic state and no feature flag or
persistent data. Deploy after Milestone 2. Rollback reverts the branch, removes the route and its two
locked dependencies, and restores the content preview's source-labelled Milestone 2 behavior. No
database downgrade, backfill, or data recovery is required.

The permanent architecture document will make clear that this frontend-local snapshot is a spike
contract, not yet a persisted transcript API. Milestone 5 may consume the UI; Milestone 6 must define
and validate the server transcription contract before accepting provider data.

## Branch and commit plan

1. `docs: add Milestone 3 change plan`
2. `feat: add controlled mathematical renderer`
3. `feat: add deterministic transcript state`
4. `feat: add visual transcript correction spike`
5. `test: cover Milestone 3 device regressions`
6. `docs: record Milestone 3 implementation`
7. `docs: record final Milestone 3 verification`

Tests are committed with the behavior they drive where practical; the test-only device/report commit
records cross-slice regression evidence. Every implementation slice starts red at a confirmed public
seam and reaches green before the next slice.

## Conflict coordination

Owned files are exactly those in **Files and components**. Shared files are root/app package manifests
and lockfile, root formatting script, app layout/global CSS, interaction shell, content preview, and
existing preview test. No active remote branch is currently unmerged from `origin/main`; the original
shared worktree has unrelated corpus activity and will not be used.

Milestone 3 depends on Milestone 2's typed content. Milestone 4 should integrate after this renderer
when geometry content needs mixed typed blocks; Milestone 5 should integrate after this correction
state when building the static student slice. If another branch changes `ContentBlock`, common CSS,
or an internal route contract, integration order is Milestone 2 → this branch → later milestone,
unless the team explicitly coordinates a contract-first alternative.

Before handoff, fetch/rebase on current `origin/main`. Any conflict that changes behavior or a public
contract will be documented and resolved deliberately, followed by affected focused tests and
`make check`.

## Risks

- KaTeX can expose source through `throwOnError: false` or exception messages. Mitigation: throw,
  catch, discard details, and assert the full failure DOM against known source fixtures.
- Trusted or HTML extension commands can mutate markup or load resources. Mitigation: `trust: false`,
  `strict: "error"`, no auto-render extension, and malicious-command regression cases.
- Macros, explicit sizes, or very long source can consume resources or break layout. Mitigation:
  finite expansion/size/source bounds, fresh macro maps, container sizing, and browser overflow tests.
- React integration can briefly expose a MathLive source child before upgrade. Mitigation: create an
  empty custom element, set its value property only after package load, and inspect browser DOM.
- MathLive's production tree is substantial. Mitigation: use one focused client boundary, no generic
  editor framework, locked packages, local assets, route/build measurement, and documented footprint.
- jsdom does not implement MathLive layout/editing. Mitigation: component tests use only a minimal
  public-interface custom-element double; all real rendering, keyboard correction, touch controls,
  and layout claims run in Chromium/WebKit Playwright.
- Duplicate `stepId` plus `blockIds` can drift. Mitigation: one pure invariant gate after every
  operation and before confirmation, with adversarial tests for orphan/multiple references.
- Responsive CSS-only checks can miss hidden-but-focusable content. Mitigation: tab roles/visibility
  and focus traversal are asserted in real browsers across exact projects.
- A frontend fixture route could be mistaken for AI transcription. Mitigation: prominent synthetic
  labelling, deterministic local data, no processing claim, and explicit non-goals in UI/docs.
- The user requested a pre-implementation checkpoint. Mitigation: stop after this proposed plan and
  baseline inspection; write no test or implementation until the project owner confirms the seams
  and file set.

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

- 2026-08-27: The project owner confirmed the proposed public test seams and file set. Test-first
  implementation may proceed within this ChangePlan's owned scope.
- 2026-08-27: Keep phone tabs in normal document flow. A preliminary visual run showed that sticky
  positioning could cover transcript controls while scrolling; normal flow keeps the switch visible
  before the active panel and leaves every correction control unobstructed.
- 2026-08-26: Keep the spike frontend-local and reuse the existing authentication endpoint. A new
  transcript API or database contract would exceed Milestone 3 and falsely imply persistence.
- 2026-08-26: Use KaTeX's DOM renderer with `throwOnError: true`, not string injection or built-in
  error rendering, because both source and exception messages are forbidden from failure-state DOM.
- 2026-08-26: Model transcript blocks as text/math only even though problem content has a broader
  `ContentBlock` union. The Milestone 3 transcription contract specifies these two variants, and
  speculative geometry/image transcript blocks have no second use.
- 2026-08-26: Accept explicit IDs in pure operations. This makes state transitions deterministic and
  testable while leaving future server/provider ID allocation outside the spike.
- 2026-08-26: Require every step to contain at least one block and reject deletion of its final block.
  This removes ambiguous empty-step UX and strengthens exact ownership invariants.
- 2026-08-26: Confirmation contains no timestamp so identical visible states serialize identically.
- 2026-08-26: Use accessible up/down/split/merge controls and no drag-and-drop dependency.
- 2026-08-26: Lock only `katex@0.18.4` and `mathlive@0.110.0` as direct production additions; no
  Markdown, rich-text, sanitization, AI, geometry, or persistence dependency is justified.

## Discoveries

- `origin/main` is exactly the requested Milestone 2 commit, rather than merely a later descendant.
- The original shared worktree contains active unrelated corpus work, so branch isolation is required
  rather than switching that checkout.
- The existing preview renderer is the only current source-leak path for typed mathematics and can be
  migrated without changing FastAPI or generated types.
- MathLive's current NPM package has a mandatory compute-engine production dependency even though the
  spike does not use symbolic computation; this transitive footprint is documented rather than
  hidden. No separate compute-engine API will be called.
- Current official MathLive guidance supports React through its `<math-field>` public element,
  property, and input event, and its default virtual-keyboard policy already targets touch devices.
- KaTeX `trust: false` alone does not throw for a trusted-command attempt: it renders the command name
  and includes the complete source in its MathML annotation. The controlled boundary therefore uses
  an always-false trust callback to record any attempt, renders into a detached node, and rejects the
  complete staged result before it can enter mounted failure-state DOM.

## Verification evidence

- `git fetch origin main` completed and fetched the current main reference.
- `git merge-base --is-ancestor 984da70 origin/main` exited 0.
- `git rev-parse origin/main` returned
  `984da70f7fb0e51446054f7dea3c852fca08dac0`.
- `git log -6 --oneline origin/main` showed the complete Milestone 2 sequence ending in
  `984da70 docs: record final Milestone 2 verification`.
- `git worktree add -b feat/m3-math-rendering-correction-spike
/home/minh/dev/math-coach-m3 origin/main` created this clean branch/worktree at the exact base.
- `npm view` on 2026-08-26 returned KaTeX `0.18.4` and MathLive `0.110.0`, both MIT, with the package
  and locked transitive sizes documented above.
- `npm pack --dry-run --json katex@0.18.4` and `mathlive@0.110.0` confirmed package contents without
  installing or changing tracked files.
- Current official KaTeX options/security/error documentation, MathLive integration/React/virtual
  keyboard/API documentation, and repository-local Next.js guidance listed above were read.
- Baseline `make check` reached the E2E phase after all non-browser gates passed. Exact passing
  evidence: Prettier and Ruff format checks; ESLint and Ruff lint; TypeScript and mypy; generated API
  contract; one content package at hash
  `59f9572fb526842cbdddf438db2468c8d578a637fe814102f5bfbb95118ce7db`; Next.js production build;
  24 frontend tests; 25 backend unit tests; two full downgrade/upgrade cycles; and 19 integration
  tests.
- The baseline `make check` E2E phase failed 5/5 because existing owner processes at 3000/8000 came
  from `/home/minh/dev/math-coach`, not this worktree. The browser saw the other branch and timed out
  at its missing content-preview link. Those owner processes were inspected only by PID/cwd metadata
  and were not stopped.
- A temporary untracked diagnostic Playwright config used ports 3100/8100, then was deleted. It
  confirmed this branch served the Milestone 2 content-preview link, but 5/5 uploads failed from the
  alternate origin before completion. This is recorded as environment evidence, not a passing
  substitute for `make test-e2e`.
- Renderer red/green evidence: the first focused run failed because `MathRenderer` did not exist;
  subsequent red runs exposed uncaught malformed input, trusted-command source output, empty
  rendering, over-length rendering, and the existing content preview's plain-source fallback before
  each behavior was implemented.
- `npx vitest run components/math/math-renderer.test.tsx
components/content-preview.test.tsx --coverage=false` passed 20 focused renderer/typed-content
  tests after the slice. The corpus includes inline/display math, fractions, nested fractions,
  powers, subscripts, roots, systems/cases, inequalities, congruences, sets, logic, matrices,
  geometry symbols, multi-line derivations, Vietnamese mixed content, malformed/unsupported/trusted
  commands, expansion/input/element bounds, empty math, and invalid-to-valid recovery.
- `npm run typecheck --workspace @math-coach/student-web` passed after the renderer slice.
- `npm run build --workspace @math-coach/student-web` passed and prerendered the existing `/` and
  `/internal/content-preview` routes with KaTeX CSS bundled.
- Actual `du -sb` package content sizes exactly matched registry metadata for direct/transitive
  production packages: KaTeX tree 4,185,500 bytes and MathLive tree 27,079,799 bytes.
- Transcript-state red/green evidence: the focused test first failed because the public state module
  did not exist, then passed 12 tests covering all documented invariants, typed updates, immutable
  add/delete/move operations, split/merge/move step operations, and deterministic independent
  confirmation serialization.
- `npm run test:unit --workspace @math-coach/student-web` passed 54 tests after adding the pure
  transcript module to coverage. Aggregate coverage remained above every 80% gate: 93.19%
  statements, 90.42% branches, 94.91% functions, and 93.01% lines.
- `npm run typecheck --workspace @math-coach/student-web` passed after the transcript-state slice.
- MathLive/workflow red/green evidence: separate focused runs first failed for missing
  `MathLiveEditor`, `TranscriptEditor`, `CorrectionSpikeApp`, and workspace navigation, then passed
  after each public behavior was introduced.
- The post-refactor focused run passed 29 renderer, MathLive, mixed-block workflow, authentication,
  responsive-mode, and workspace-navigation component tests across five test files.
- `npm run lint --workspace @math-coach/student-web`, `npm run typecheck --workspace
@math-coach/student-web`, and `npm run build --workspace @math-coach/student-web` passed after the
  correction workflow. The production build includes `/internal/math-correction`.
- The isolated real-browser regression passed all five unchanged configured projects in Docker:
  `compact-chromium`, `pixel-7-chromium`, `iphone-13-webkit`,
  `ipad-pro-11-portrait-webkit`, and `ipad-pro-11-landscape-webkit` all passed in 7.4 seconds.
- The final production-build run with `VISUAL_QA=1` passed all five projects in 6.5 seconds after the
  phone-tab refinement. Per-project times were 1.3, 1.8, 5.2, 5.3, and 5.7 seconds in the order
  listed in the committed device report.
- A final non-visual rerun after explicit photo-visibility and forbidden-element assertions passed
  all five projects in 5.5 seconds.
- All five final screenshots were inspected at high detail. Phone tabs were clear of transcript
  controls; both tablet orientations kept simultaneous photo/transcript panels; MathLive, KaTeX,
  labelled operations, and confirmation stayed legible and inside the viewport. The automated
  document-width and element-bound checks reported no horizontal page overflow.
- `docs/evaluation/m3-math-rendering-device-report.md` records the exact environment, assertions,
  results, manual inspection, and isolated-port reason. The temporary base-URL config and generated
  screenshots were not committed.
- `npm run format` and `npm run format:check` passed after adding all Milestone 3 owned documents to
  the root formatting contract.
- The documented focused command `npx vitest run components/math components/transcription
features/transcription --coverage=false` passed 41 tests across six files.
- Final `make check` passed with this worktree isolated from the owner-run processes at 3000/8000.
  The temporary runner used this branch's FastAPI on 8100 and built/served this branch's Next.js app
  inside the version-matched Playwright container at the standard browser origin
  `http://localhost:3000`; a narrow in-container proxy preserved that origin for MinIO on 9000. The
  repository `scripts/run_e2e.sh`, Playwright config, and temporary proxy were restored/deleted
  immediately afterward and have no diff.
- Exact final `make check` results: Prettier and Ruff format passed; ESLint and Ruff lint passed;
  TypeScript and mypy passed; OpenAPI/generated TypeScript drift passed; the one versioned package
  validated at hash `59f9572fb526842cbdddf438db2468c8d578a637fe814102f5bfbb95118ce7db`;
  the production build generated `/`, `/internal/content-preview`, and
  `/internal/math-correction`; 63 frontend tests passed with 91.50% statements, 87.67% branches,
  92.13% functions, and 91.50% lines; 25 backend unit tests passed; two complete migration
  downgrade/upgrade cycles passed; 19 integration tests passed; and all 10 browser cases passed in
  7.0 seconds across the five projects.
- The first final-check E2E attempt intentionally reused the already-running 3100 server while the
  check rebuilt `.next`; this invalidated that process's loaded asset manifest, and the alternate
  origin also triggered the deliberately narrow MinIO CORS policy. The correction spec still passed
  5/5, but the existing upload spec failed 5/5. The isolated standard-origin rerun above removed both
  environmental causes and passed the complete suite without an application/test assertion change.
- `git fetch origin main` on 2026-08-27 confirmed `origin/main` remained
  `984da70f7fb0e51446054f7dea3c852fca08dac0`. `git rebase origin/main` reported the branch was
  already up to date; there were no conflicts and therefore no behavior or contract conflict to
  resolve.
- The complete `origin/main...HEAD` diff and every owned file were reviewed. Dead pre-KaTeX preview
  styles were removed, safety searches found no `dangerouslySetInnerHTML`, HTML assignment, `eval`,
  generated function, or Markdown renderer in application code, and `git diff --check` passed.

## Result

Complete. Milestone 3 now has one bounded read-only KaTeX boundary, source-free correctable failure
states, a MathLive visual editor, deterministic typed transcript operations and confirmation, an
authenticated synthetic correction route, phone tabs, tablet split layout, migrated typed-content
preview math, complete unit/component/browser regressions, permanent architecture documentation,
and exact five-project device evidence. The confirmed snapshot is explicitly the future
authoritative grading input, but the branch adds no grading, AI, persistence, database, HTTP,
OpenAPI, generated-contract, content-schema, geometry, RAG, or vector-database behavior. All final
checks pass, the complete diff is reviewed, the branch is rebased on unchanged `origin/main`, no
conflicts occurred, and the original shared worktree/data work was not touched.
