# Milestone 3 mathematical rendering and correction spike

## Metadata

- Status: in-progress
- Owner: Codex implementation; project owner approval
- Branch: `feat/m3-math-rendering-correction-spike`
- Base commit: `f899a11614784d21b365ad31ff271b7be7e0385c`
- Related milestone: Milestone 3 — Mathematical rendering and correction spike
- Related issue/ticket: Product clarification received 2026-08-27
- Started: 2026-08-26
- Last updated: 2026-08-27

## Context

Milestone 3 was first implemented with a transcript model that assigned every text/math block to a
learner-visible reasoning step and exposed split, merge, and step-reorder controls. That
implementation was merged to `origin/main` at `f899a11`. The project owner has now clarified that
correction happens before reasoning-step detection: the system transcribes an uploaded solution into
one continuous document, the learner corrects and confirms that document, and only later processing
may identify reasoning steps.

The existing KaTeX and MathLive safety boundaries remain valid. The correction-stage model and UI do
not: hiding step headings would leave the wrong canonical state, confirmation shape, controls, and
product contract. This revision must remove steps structurally and present the deterministic fixture
as simulated OCR output without claiming real OCR.

## Goal

Deliver an authenticated internal correction spike in which a synthetic uploaded solution appears
beside one continuous paper-like, editable transcript. The canonical correction state is a flat
ordered sequence of stable typed text/math blocks. Text edits in place, idle mathematics uses the
controlled KaTeX renderer, clicking mathematics activates MathLive, and confirmation returns an
independent flat snapshot in the exact visible order without exposing IDs or technical structure in
the UI.

## Non-goals

- Real OCR, multimodal-provider calls, AI-generated transcript data, or provider selection.
- Reasoning-step detection, grouping, step boundaries, step editing, or downstream step mapping.
- Evaluation, grading, hints, scores, learner-state updates, or fabricated AI output.
- Transcript persistence, HTTP endpoints, OpenAPI changes, database tables, or migrations.
- A generic rich-text framework, Markdown/HTML renderer, arbitrary AI HTML, or executable code.
- Camera work, direct pen input, geometry, RAG, vector storage, or real student/exam content.
- Drag-and-drop as a required interaction.

## User-visible behavior

- The photo panel identifies the image as an uploaded-solution simulation using a synthetic,
  non-student fixture; the transcript panel identifies its content as simulated OCR output.
- The transcript is one continuous document surface with no `Step 1/2/3`, step cards, boundaries, or
  split/merge/move-step controls.
- Text is edited directly in borderless, document-like multiline fields.
- An idle valid formula is shown once through controlled KaTeX. Activating it replaces that display
  with one visual MathLive field; completing the edit returns to controlled KaTeX. No permanent
  formula-editor/preview pair and no raw-LaTeX control is shown.
- An invalid formula shows only `Math needs correction`; activating the placeholder opens the same
  visual MathLive correction path.
- Add controls sit at the document end. Move/delete operations are accessible through a contextual
  block menu with labelled keyboard/touch controls and deterministic boundary states.
- Confirmation displays the reviewed text and mathematics in order. It does not show block IDs,
  schema versions, variant names, arrows, JSON, scores, or reasoning steps.
- The confirmation copy identifies the flat snapshot as the future authoritative grading input and
  states that reasoning analysis happens later; no downstream processing runs.
- Phones keep PHOTO/TRANSCRIPT tabs. Tablets keep the photo and document side by side.

## Current-state findings

- `git fetch origin main` on 2026-08-27 resolved both `HEAD` and `origin/main` to
  `f899a11614784d21b365ad31ff271b7be7e0385c`; the feature worktree is clean.
- The original shared checkout still contains unrelated corpus/data work. This revision continues
  only in `/home/minh/dev/math-coach-m3`; the shared checkout and corpus/data paths are not inspected,
  formatted, staged, stashed, or discarded.
- The current frontend-local `TranscriptState` duplicates order across `blocks[]`, `steps[]`,
  `step.blockIds[]`, and `block.stepId`. Its validator and operations are designed around step
  ownership, and confirmation serializes those steps.
- `TranscriptEditor` renders separate step cards, persistent KaTeX preview plus MathLive editor for
  every formula, visible block-type labels, and direct rows of block/step controls. Its confirmation
  view exposes step IDs and type names.
- The synthetic transcript has six blocks across three synthetic steps. The SVG also numbers three
  lines as 1/2/3 and describes them as steps, reinforcing the obsolete grouping.
- The correction route already has explicit authentication/checking/retry states, a clearly
  synthetic fixture, phone tab semantics, and tablet split behavior that can be retained.
- `MathRenderer` already uses detached staging, `throwOnError: true`, `strict: "error"`,
  `maxExpand: 100`, `maxSize: 10`, fresh macros, a rejecting trust callback, and a 2,000-character
  input limit. Failure DOM is source-free. These controls do not need a contract change.
- `MathLiveEditor` already transfers source only through the custom element's `value` property and
  reports public `input` events. It can be mounted only while a formula is active.
- The current component/browser suite covers invalid-to-valid MathLive correction, mixed blocks,
  block operations, step operations, confirmation, authentication, five responsive projects,
  source absence, and horizontal containment. Step assertions must be replaced, not hidden.
- Baseline focused command
  `npx vitest run features/transcription/transcript-state.test.ts
components/transcription/transcript-editor.test.tsx
components/transcription/correction-spike-app.test.tsx components/math/mathlive-editor.test.tsx
components/math/math-renderer.test.tsx --coverage=false` passed 37/37 tests in 941 ms.
- The root validation contract remains `make format-check`, `make lint`, `make typecheck`,
  `make test-unit`, `make test-integration`, `make test-e2e`, `make content-validate`, `make test`,
  and `make check`. The unchanged Playwright matrix has three phone and two tablet projects.
- Repository-local Next.js 16.3.2 Server/Client Component and CSS guidance was reread. Interactive
  state remains in focused Client Components; application global CSS remains imported at the root;
  MathLive remains isolated behind the existing browser-only wrapper.
- Generated OpenAPI/TypeScript contracts contain typed problem `ContentBlock` data but no transcript
  contract. This revision remains frontend-local and does not change generated artifacts.

## Design

### Flat transcript state

The correction model becomes:

```typescript
type TranscriptBlock =
  { id: string; type: "text"; text: string } | { id: string; type: "math"; latex: string };

type TranscriptState = {
  schemaVersion: "2.0.0";
  attemptId: string;
  blocks: TranscriptBlock[];
};
```

The version changes because removing step ownership is a breaking change even though this type is
not persisted or public. Array position is the only canonical order. A block is present exactly once
by construction; validation requires a supported version, non-empty attempt ID, at least one block,
and unique non-empty block IDs. There is no reference array that can orphan or multiply own a block.

Pure immutable operations accept caller-supplied stable IDs: add at an explicit index, delete a
non-final block, move an adjacent block up/down, and update only the matching typed value. Splitting,
merging, and moving steps cease to exist as exports. Confirmation validates and deep-clones the flat
blocks in visible order, with no timestamp or downstream metadata.

### Continuous correction document

`TranscriptEditor` iterates `transcript.blocks` directly inside one `transcript-document` surface.
Text blocks use controlled multiline textareas styled as ordinary document paragraphs, with
accessible names but no persistent type label or card border. `field-sizing: content` provides
natural height where supported; a safe minimum-height fallback remains.

Each idle math block is an accessible activation button containing only `MathRenderer`. Activating
it swaps that one display for `MathLiveEditor` and a concise `Done editing` action. The renderer and
editor are never shown together. Invalid renderers use the same source-free placeholder inside the
activation control, so malformed math is immediately correctable. The editor remains visual and
never exposes a raw source field.

Each block has a contextual native `details` menu whose summary has an accessible `Block options`
name. Move up/down and delete remain at least 44 px, work by keyboard/touch, and disable impossible
boundaries. Add-text and add-math actions remain at the document end. Drag-and-drop is unnecessary.

Confirmation calls the pure flat serializer and renders a read-only copy of the reviewed document:
text through React text nodes and mathematics through `MathRenderer`. Stable IDs remain in the typed
snapshot for future identity but never appear in confirmation copy or user-facing labels.

### Simulated OCR fixture and responsive route

The deterministic fixture is explicitly described as simulated OCR output. It contains six flat
blocks in source order and still includes one deliberately malformed formula to exercise correction.
The synthetic SVG removes artificial step numbering and describes a continuous solution. It remains
original non-personal data and does not imply real OCR.

The existing authenticated access states, phone tab implementation, and tablet split remain. The
tablet transcript panel is styled as a document viewer/editor rather than nested cards. Phone and
tablet checks continue to bound all editor, renderer, menu, and confirmation surfaces.

### Confirmed public test seams and TDD slices

The project owner's clarification directly confirms these observable seams:

1. Pure `TranscriptState` exports: flat validation, typed immutable operations, and exact snapshot.
2. `TranscriptEditor`: continuous document DOM, natural text edit, click-to-activate MathLive,
   contextual operations, source-free invalid correction, and non-technical confirmation.
3. `CorrectionSpikeApp`: simulated-OCR framing plus authenticated phone/tablet layout.
4. The existing real `MathRenderer`/`MathLiveEditor` boundaries, whose safety behavior must not
   regress.
5. `tests/e2e/math-correction.spec.ts` across all configured projects.

Work proceeds in vertical red/green slices: first flat state, then document editing/confirmation,
then responsive browser regression. Tests use public exports and accessible user behavior, with
known literal expected snapshots; implementation internals are not mocked.

## Multi-exam impact

- Study profiles: no change.
- Exam targets: no change; no singular-target assumption is introduced.
- Exam-specific progress: no change.
- Shared skill state: no change.
- Daily-plan balancing: no change.

## Files and components

Owned for this revision:

- `docs/changes/2026-08-26-m3-math-rendering-correction-spike.md` — living revision plan/evidence.
- `docs/MVP_IMPLEMENTATION_PLAN.md` — move reasoning-step detection after confirmation and correct
  the Milestone 3/transcription requirements.
- `docs/architecture/math-rendering-and-transcript-state.md` — durable flat correction contract.
- `docs/evaluation/m3-math-rendering-device-report.md` — fresh five-project results.
- `README.md` — describe flat simulated-OCR correction behavior.
- `apps/student-web/features/transcription/transcript-state.ts` and test — flat state/invariants.
- `apps/student-web/features/transcription/synthetic-fixture.ts` — flat simulated OCR blocks.
- `apps/student-web/components/transcription/transcript-editor.tsx` and test — continuous editor.
- `apps/student-web/components/transcription/correction-spike-app.tsx` and test — clarified framing.
- `apps/student-web/app/globals.css` — paper/document and contextual-control styles.
- `apps/student-web/public/fixtures/synthetic-correction-sheet.svg` — remove synthetic step cues.
- `tests/e2e/math-correction.spec.ts` — revised five-project regression.

No package manifest/lock, renderer implementation, MathLive wrapper, API, generated contract,
backend, database, migration, or content-package file is expected to change.

## API and schema changes

No HTTP API, OpenAPI, generated TypeScript client, content schema, or AI schema changes. The
frontend-local transcript spike changes incompatibly from version `1.0.0` step-based state to
version `2.0.0` flat state. Nothing persists or consumes version `1.0.0`, so no compatibility adapter
is needed; accepting both would preserve the explicitly rejected step model.

## Database and migration

None. There is no transcript table, backfill, persistent draft, or data-loss risk.

## Security and privacy

- Existing invite-session authorization remains the route gate.
- Fixture data remains original, synthetic, and non-personal; no upload/provider call is added.
- Future OCR/transcription content remains untrusted at the rendering boundary.
- KaTeX trusted commands remain disabled; parsing, expansion, size, and source length remain bounded.
- Failure DOM never receives raw source or exception text, while MathLive remains available on
  activation for correction.
- Text renders through React/text controls. Arbitrary HTML, Markdown, scripts, generated code,
  external resources, and `dangerouslySetInnerHTML` are not introduced.
- Confirmation stays local and performs no grading or downstream analysis.

## Dependency decisions

No dependency changes. Retain the exact production locks already approved for Milestone 3:

- `katex@0.18.4` — controlled read-only rendering; MIT; 4,185,500 bytes for its locked production
  tree. MathJax and hand-built output remain rejected as duplicate/incomplete rendering boundaries.
- `mathlive@0.110.0` — visual formula editing; MIT; 27,079,799 bytes for its locked production tree.
  MathQuill remains rejected because MathLive is the selected product contract. A generic rich-text
  framework remains unnecessary for the small typed document model.

## Test plan

### Unit: flat transcript state

- Red: old step-shaped fixture/type and step operations no longer satisfy the public state contract.
- Accept a flat mixed text/math array with stable unique IDs and reject unsupported version, empty
  attempt ID, empty block list, empty block ID, and duplicate block ID.
- Add text/math at explicit global positions; reject duplicates and invalid indexes; prove no input
  mutation.
- Delete one block, reject unknown IDs and deletion of the final block.
- Move blocks globally up/down in deterministic order and reject first/last boundaries.
- Update typed values without changing variants.
- Confirm an independent known-literal flat snapshot whose JSON is identical for identical state and
  has no `steps` or `stepId` fields.

### Component: correction document

- Red: assert one document and no step regions/headings or split/merge/move-step controls.
- Edit mixed text naturally through in-document fields.
- Assert a valid idle formula shows KaTeX and no MathLive field; activate it and assert one MathLive
  field with no simultaneous preview; finish editing and return to KaTeX.
- Activate an invalid placeholder, correct it through the MathLive public value/input boundary, and
  assert raw source never appears in failure DOM.
- Open contextual block options; exercise add/delete/global reorder and labelled boundary controls.
- Confirm a known-literal flat typed snapshot and assert confirmation UI displays reviewed content
  but no IDs, type labels, arrows, JSON, or step language.
- Preserve checking/authentication-required/retryable/ready route states and phone/tablet semantics.
- Assert simulated OCR and synthetic-upload framing.

### Math safety regression

- Rerun the unchanged renderer suite for valid inline/display math, mixed lines, malformed and
  unsupported source, trusted-command attempts, excessive expansion, oversized/over-length/empty
  math, invalid-to-valid recovery, forbidden elements, and failure-source absence.
- Rerun the unchanged MathLive wrapper suite for property-only source transfer and visual input.

### Browser/end-to-end

Run the revised spec unchanged in all five projects. It will authenticate; enter from the workspace;
verify synthetic uploaded-image and simulated-OCR labels; verify phone tabs/tablet split; assert a
single continuous document and absence of step UI/controls; activate and correct invalid math with
real MathLive; edit text; exercise contextual add/delete/reorder controls; confirm exact visual
content without IDs/technical structure; reject raw source/forbidden elements; and measure document
plus element horizontal containment.

### Exact device matrix

| Project                        | Engine          |   Viewport | Layout expectation               |
| ------------------------------ | --------------- | ---------: | -------------------------------- |
| `compact-chromium`             | Chromium, touch |  360 × 640 | PHOTO/TRANSCRIPT tabs + document |
| `pixel-7-chromium`             | Chromium, touch |  412 × 839 | PHOTO/TRANSCRIPT tabs + document |
| `iphone-13-webkit`             | WebKit, touch   |  390 × 664 | PHOTO/TRANSCRIPT tabs + document |
| `ipad-pro-11-portrait-webkit`  | WebKit, touch   | 834 × 1194 | photo/document split             |
| `ipad-pro-11-landscape-webkit` | WebKit, touch   | 1194 × 834 | photo/document split             |

### Acceptance criteria

- The correction state and confirmed snapshot are a flat ordered `blocks[]` sequence with stable
  explicit text/math variants and no step data.
- No step heading, boundary, split/merge/move-step control, internal ID, or technical structure is
  present in the correction/confirmation UI.
- The fixture is clearly simulated OCR from a synthetic uploaded solution, without claiming OCR ran.
- Text edits in place on one continuous paper-like document.
- Idle math uses the controlled renderer; activated math uses MathLive; preview and editor are never
  permanently displayed together.
- Invalid math is source-free and directly correctable; all existing KaTeX safety limits remain.
- Add/delete/reorder operations are deterministic, accessible, contextual, and do not require drag.
- Confirmation serializes and displays exactly the visible ordered content and identifies it as the
  future authoritative grading input.
- Phone tabs and tablet split pass all five projects with no document-level horizontal overflow.
- No real OCR, grading, persistence, or step detection is added; all applicable root checks pass.

## Manual QA

1. Sign in with the local invite and open **Correction spike**.
2. At 360 × 640, verify the PHOTO view identifies the synthetic uploaded solution, switch to
   TRANSCRIPT by pointer and arrow-key navigation, and verify simulated OCR copy.
3. Read the transcript as one uninterrupted paper document; verify no step headings/boundaries.
4. Edit text directly. Activate valid math, edit visually in MathLive, finish, and see one KaTeX
   display. Activate the invalid placeholder, correct it, and verify no source leak.
5. Open block option menus by keyboard and touch; add, move, and delete blocks.
6. Confirm; compare the read-only confirmation content to the document and verify no IDs/types/steps.
7. Repeat visual/overflow inspection for Pixel 7, iPhone 13, iPad portrait, and iPad landscape.
8. Reopen content preview and confirm its controlled math rendering remains unchanged.

## Rollout and rollback

The revision remains an authenticated local-state route with no feature flag or persistence. Deploy
after `f899a11`. Rollback reverts only the clarification commits, restoring the obsolete step-based
spike without a database action. Because the old shape conflicts with the clarified product flow,
rollback is an engineering contingency, not an endorsed product state.

## Branch and commit plan

1. `docs: revise Milestone 3 correction plan`
2. `refactor: flatten correction transcript state`
3. `feat: present transcript as continuous document`
4. `test: update correction device regressions`
5. `docs: record flat transcript correction contract`

Tests are committed with the behavior they drive where practical. Each implementation slice must
reach focused green before the next slice.

## Conflict coordination

Owned files are exactly those in **Files and components**. `docs/MVP_IMPLEMENTATION_PLAN.md`, README,
global CSS, and correction components are shared surfaces. `origin/main` is the exact revision base
and has no commits absent from this worktree at inspection. The original corpus branch is out of
scope. Before handoff, fetch/rebase on current `origin/main`; any behavioral conflict must be
documented and followed by affected focused tests and `make check`.

## Risks

- Removing only UI labels could leave hidden step semantics. Mitigation: delete step fields, types,
  exports, fixtures, and confirmation data; add source/DOM absence assertions.
- Swapping between KaTeX and MathLive could expose raw source or lose edits. Mitigation: preserve the
  property/event-only MathLive boundary and test invalid/valid round trips at component and browser
  seams.
- Contextual controls can become undiscoverable or inaccessible. Mitigation: native details/summary,
  explicit labels, 44 px targets, focus-visible styles, and phone/touch browser coverage.
- Document-like controls can overflow or collapse on narrow screens. Mitigation: min-width zero,
  content sizing, contained math, and exact element/document measurements in all five projects.
- Confirmation could accidentally show IDs while proving order. Mitigation: assert the typed snapshot
  through the callback and independently assert a user-facing content-only confirmation.
- The SVG's handwritten numbering could be mistaken for system segmentation. Mitigation: make the
  synthetic sheet continuous and remove numbered step cues.

## Progress

- [x] Repository inspected
- [x] Plan reviewed
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

- 2026-08-27: Product clarification supersedes the original step-based correction design. Reasoning
  grouping belongs after confirmation and is explicitly absent from this spike.
- 2026-08-27: Bump the frontend-local snapshot version to `2.0.0`; silently retaining `1.0.0` for an
  incompatible shape would make future fixture/contract diagnosis ambiguous.
- 2026-08-27: Keep IDs inside typed state for stable identity but never show them in correction or
  confirmation UI.
- 2026-08-27: Use one idle KaTeX view or one active MathLive editor per formula, with an explicit
  finish action that remains reliable with touch virtual keyboards.
- 2026-08-27: Retain at least one transcript block. The last block cannot be deleted, keeping the
  document correctable and preventing accidental confirmation of a structurally absent transcript.
- 2026-08-27: Retain exactly the already approved KaTeX and MathLive dependencies; add no rich-text
  framework for a flat typed block document.

## Discoveries

- The merged SVG fixture itself contains synthetic 1/2/3 numbering, not only the React step UI.
- The existing confirmed UI exposes step IDs and variant names solely to demonstrate serialization;
  the callback seam can prove typed order without exposing those details to a learner.
- The generated API client has no transcription result. Flattening this frontend-local spike does
  not create generated-contract drift or a compatibility obligation.

## Verification evidence

- `git fetch origin main` completed on 2026-08-27.
- `git rev-parse HEAD` and `git rev-parse origin/main` both returned
  `f899a11614784d21b365ad31ff271b7be7e0385c` before revision edits.
- Required root/local instructions, the MVP plan, prior complete ChangePlan, rendering/transcript
  architecture, device report, correction source/tests, package/validation configuration, relevant
  generated contracts, and repository-local Next.js Server/Client and CSS guides were read.
- Baseline focused Vitest result: 5 files and 37 tests passed in 941 ms.

## Result

In progress. No implementation result or revised device claim is recorded yet.
