# Milestone 3 mathematical rendering and correction spike

## Metadata

- Status: complete
- Owner: Codex implementation; project owner approval
- Branch: `feat/m3-math-rendering-correction-spike`
- Base commit: `3753cd94bbc83ddeb284870600db9809524f0a82`
- Related milestone: Milestone 3 — Mathematical rendering and correction spike
- Related issue/ticket: Flat and inline correction clarifications received 2026-08-27
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

A second clarification makes “continuous document” more precise. Text and formulas must flow inline
like a conventional word processor, not appear as separate editable rows. The learner places a
native caret directly in the document, types with the physical or platform virtual keyboard, inserts
a formula at that caret, and activates an existing formula in place. Removing a formula is the one
destructive editing action that always requires confirmation.

## Goal

Deliver an authenticated internal correction spike in which a synthetic uploaded solution appears
beside one continuous word-processor-like transcript. The canonical correction state remains a flat
ordered sequence of stable typed text/math blocks, while presentation flows those variants inline.
The document owns a native text caret, existing or newly inserted formulas activate MathLive in
place, formula removal requires confirmation, and confirmation returns an independent flat snapshot
in exact visible order without exposing IDs or technical structure in the UI.

## Non-goals

- Real OCR, multimodal-provider calls, AI-generated transcript data, or provider selection.
- Reasoning-step detection, grouping, step boundaries, step editing, or downstream step mapping.
- Evaluation, grading, hints, scores, learner-state updates, or fabricated AI output.
- Transcript persistence, HTTP endpoints, OpenAPI changes, database tables, or migrations.
- A generic rich-text framework, Markdown/HTML renderer, arbitrary AI HTML, or executable code.
- Camera work, direct pen input, geometry, RAG, vector storage, or real student/exam content.
- A general-purpose rich-text engine, formatting toolbar, drag-and-drop, collaborative editing,
  comments, revision history, or arbitrary pasted HTML.

## User-visible behavior

- The photo panel identifies the image as an uploaded-solution simulation using a synthetic,
  non-student fixture; the transcript panel identifies its content as simulated OCR output.
- The transcript is one continuous editable surface with no `Step 1/2/3`, block rows/cards,
  boundaries, or split/merge/move-step controls.
- Text and formulas share the same visual line and wrap naturally. The browser caret is visible
  directly in text; physical and platform virtual keyboards use the native editable surface.
- There is no add-text action. The sole insertion action adds a formula at the saved caret, splits
  the surrounding typed text deterministically, activates MathLive, and focuses it.
- An idle valid formula is shown inline once through controlled KaTeX. Activating it replaces that
  token with one visual MathLive field; completing the edit returns to controlled KaTeX. No
  permanent formula-editor/preview pair and no raw-LaTeX control is shown.
- An invalid formula shows only `Math needs correction`; activating the placeholder opens the same
  visual MathLive correction path.
- Formula actions are contextual to the active token. Removing a formula through its action,
  keyboard Delete, or adjacent Backspace/Delete always opens an accessible confirmation dialog;
  cancellation leaves the document unchanged. Formula reorder actions remain contextual and
  keyboard/touch accessible without exposing text/math block structure.
- Confirmation flows the reviewed text and inline mathematics in order. It does not show block IDs,
  schema versions, variant names, arrows, JSON, scores, or reasoning steps.
- The confirmation copy identifies the flat snapshot as the future authoritative grading input and
  states that reasoning analysis happens later; no downstream processing runs.
- Phones keep PHOTO/TRANSCRIPT tabs. Tablets keep the photo and document side by side.

## Current-state findings

- Revision work began from the merged Milestone 3 commit
  `f899a11614784d21b365ad31ff271b7be7e0385c`. During implementation `origin/main` advanced to
  `3753cd94bbc83ddeb284870600db9809524f0a82`; the branch rebased onto that commit without conflict.
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
- The flat revision still renders every block inside a separate row, uses one textarea per text
  block, places mathematics in display mode, and exposes add-text plus block menus. It is structurally
  flat but does not yet behave like one editor.
- `contenteditable="plaintext-only"` provides a browser caret and strips pasted formatting where
  supported; the Selection/Range APIs provide stable character offsets for formula insertion. Text
  remains canonical only after synchronizing the editing host back to typed blocks; browser HTML is
  never accepted as content.
- Official MathLive documentation confirms that `MathfieldElement.focus()` begins keyboard input and
  `mathVirtualKeyboardPolicy = "auto"` opens its keyboard on touch-capable devices. The existing
  wrapper already uses the latter and needs only opt-in focus after registration.
- Baseline for this refinement:
  `npx vitest run features/transcription/transcript-state.test.ts
components/transcription/transcript-editor.test.tsx components/math/mathlive-editor.test.tsx
--coverage=false` passed 3 files and 13 tests in 946 ms.
- `origin/main` remains `3753cd94bbc83ddeb284870600db9809524f0a82`; both Milestone 2 commit
  `984da70` and merged Milestone 3 commit `f899a11` are ancestors. The branch is clean and six commits
  ahead before this refinement.

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

Inline insertion adds one math block at a character offset in a text block. A middle insertion keeps
the original text ID for the leading text, uses caller-supplied IDs for the formula and trailing
text, and preserves every character in order. Boundary insertion avoids redundant empty leading
segments while retaining a trailing caret position. Confirmed formula deletion removes only a math
variant, merges adjacent text variants in reading order, and creates one caller-identified empty
text block only when deleting the document's sole token.

### Continuous correction document

`TranscriptEditor` renders the typed block array as inline runs inside one plaintext-editable host.
The browser supplies the visible caret, native selection, physical-keyboard input, touch keyboard,
and line wrapping. Input events copy only text content from known text runs back into typed state;
DOM markup is never serialized. Paste cannot introduce canonical formatting or HTML.

Selection/Range inspection records a collapsed character offset inside the current text run. The
single **Insert formula** action retains that selection when pointer/touch moves to the toolbar,
calls the pure split operation, activates the inserted formula, and focuses MathLive. If no saved
caret exists it uses the end of the last text run. There is no add-text action.

Each idle math block is a non-editable inline token containing only `MathRenderer`. Activating it
swaps that token for `MathLiveEditor` plus contextual finish, reorder, and delete actions. The
renderer and editor are never shown together. Invalid renderers use the same source-free placeholder
inside the activation control, so malformed math is immediately correctable. The editor remains
visual and never exposes a raw source field.

Explicit formula deletion and boundary Backspace/Delete identify the adjacent math token, prevent
the browser mutation, and open an accessible modal confirmation. Confirming invokes the pure
delete/merge operation and restores a text caret; cancelling preserves typed state. Deletion within
a non-empty MathLive expression remains ordinary formula editing, while
Backspace/Delete on an empty active formula requests token deletion. Drag-and-drop is unnecessary.

Confirmation synchronizes all known text runs, calls the pure flat serializer, and renders a
read-only inline copy of the reviewed document: text through React text nodes and mathematics through
`MathRenderer`. Stable IDs remain in typed state for future identity but never appear in
confirmation copy or user-facing labels.

### Simulated OCR fixture and responsive route

The deterministic fixture is explicitly described as simulated OCR output. It contains seven flat
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
- `apps/student-web/components/math/mathlive-editor.tsx` and test — opt-in focus for inserted or
  activated formulas.
- `apps/student-web/components/transcription/correction-spike-app.tsx` and test — clarified framing.
- `apps/student-web/app/globals.css` — paper/document and contextual-control styles.
- `apps/student-web/public/fixtures/synthetic-correction-sheet.svg` — remove synthetic step cues.
- `tests/e2e/math-correction.spec.ts` — revised five-project regression.

No package manifest/lock, renderer implementation, correction-route access state, API, generated
contract, backend, database, migration, or content-package file is expected to change.

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
- The browser editing host synchronizes only `textContent` from application-owned text runs; it
  never promotes DOM structure to canonical content. Arbitrary HTML, Markdown, scripts, generated
  code, external resources, and `dangerouslySetInnerHTML` are not introduced.
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
- Insert a formula at start, middle, and end text offsets with caller-supplied IDs; preserve exact
  character and block order without input mutation.
- Delete a math token only through the confirmed pure operation; merge adjacent text in order and
  replace a sole formula with one empty text run.

### Component: correction document

- Red: assert one plaintext-editable textbox with native caret behavior and no textarea, add-text
  action, block row/card, step UI, or permanent block controls.
- Place the selection inside text and type through the editable surface; confirm the typed state
  contains the exact edit.
- Retain the saved caret when activating **Insert formula**, split the text at that character, focus
  the new MathLive field, and confirm the resulting text/math/text order.
- Assert a valid idle formula shows KaTeX and no MathLive field; activate it and assert one MathLive
  field with no simultaneous preview; finish editing and return to KaTeX.
- Activate an invalid placeholder, correct it through the MathLive public value/input boundary, and
  assert raw source never appears in failure DOM.
- Exercise contextual formula reorder actions without exposing text blocks.
- Request formula deletion through its action, idle-token Delete, adjacent text Backspace/Delete,
  and empty MathLive Backspace/Delete; assert the modal blocks mutation until explicit confirmation
  and cancellation preserves state.
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
single inline editable document and absence of step/block UI; type at a native caret; insert and
focus a formula at that caret; activate and correct invalid math with real MathLive; require and
exercise formula-deletion confirmation; use contextual formula reorder; confirm exact visual content
without IDs/technical structure; reject raw source/forbidden elements; and measure document plus
element horizontal containment.

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
- Text edits through one native caret on a continuous document; text and formulas share lines and
  wrap naturally. No textarea or add-text action remains.
- Formula insertion occurs at the saved caret and immediately focuses MathLive. Idle math uses the
  controlled inline renderer; activated math uses MathLive; preview and editor are never permanently
  displayed together.
- Invalid math is source-free and directly correctable; all existing KaTeX safety limits remain.
- Formula deletion never occurs without explicit confirmation, including keyboard boundary paths.
  Formula insertion/reorder actions are deterministic, accessible, contextual, and require no drag.
- Confirmation serializes and displays exactly the visible ordered content and identifies it as the
  future authoritative grading input.
- Phone tabs and tablet split pass all five projects with no document-level horizontal overflow.
- No real OCR, grading, persistence, or step detection is added; all applicable root checks pass.

## Manual QA

1. Sign in with the local invite and open **Correction spike**.
2. At 360 × 640, verify the PHOTO view identifies the synthetic uploaded solution, switch to
   TRANSCRIPT by pointer and arrow-key navigation, and verify simulated OCR copy.
3. Read the transcript as one uninterrupted inline document; verify no step/block rows or textareas.
4. Tap/click between two text characters, type with the available keyboard, and observe the native
   caret. Keep the caret in the sentence, activate **Insert formula**, and verify focused MathLive
   appears exactly there with a touch virtual keyboard on a touch device.
5. Activate valid and invalid formulas, edit visually, finish, and see one inline KaTeX result with
   no source leak. Exercise contextual reorder.
6. Request deletion through the formula action and adjacent Backspace/Delete. Cancel once, then
   confirm; verify no formula disappears before confirmation and surrounding text joins in order.
7. Confirm; compare the read-only confirmation content to the document and verify no IDs/types/steps.
8. Repeat visual/overflow inspection for Pixel 7, iPhone 13, iPad portrait, and iPad landscape.
9. Reopen content preview and confirm its controlled math rendering remains unchanged.

## Rollout and rollback

The revision remains an authenticated local-state route with no feature flag or persistence. Deploy
after `3753cd9`. Rollback reverts only the clarification commits, restoring the obsolete step-based
spike without a database action. Because the old shape conflicts with the clarified product flow,
rollback is an engineering contingency, not an endorsed product state.

## Branch and commit plan

1. `docs: revise Milestone 3 correction plan`
2. `refactor: flatten correction transcript state`
3. `feat: present transcript as continuous document`
4. `test: update correction device regressions`
5. `docs: record flat transcript correction contract`
6. `docs: refine inline correction plan`
7. `feat: add inline caret mathematics editing`
8. `test: cover inline correction devices`
9. `docs: record inline correction contract`

Tests are committed with the behavior they drive where practical. Each implementation slice must
reach focused green before the next slice.

## Conflict coordination

Owned files are exactly those in **Files and components**. `docs/MVP_IMPLEMENTATION_PLAN.md`, README,
global CSS, and correction components are shared surfaces. The original corpus branch is out of
scope. This refinement begins on the already rebased branch at `777e529`; any later behavioral
conflict must be documented and followed by affected focused tests and `make check`.

## Risks

- Removing only UI labels could leave hidden step semantics. Mitigation: delete step fields, types,
  exports, fixtures, and confirmation data; add source/DOM absence assertions.
- Swapping between KaTeX and MathLive could expose raw source or lose edits. Mitigation: preserve the
  property/event-only MathLive boundary and test invalid/valid round trips at component and browser
  seams.
- Contextual formula controls can become undiscoverable or inaccessible. Mitigation: expose them
  beside the active formula with explicit labels, 44 px targets, focus-visible styles, and
  phone/touch browser coverage.
- React reconciliation can disturb a native caret or browser editing can introduce untracked DOM.
  Mitigation: make only application-owned text runs editable, synchronize text content rather than
  markup, save/restore typed offsets around structural operations, and cover real Chromium/WebKit.
- Native deletion can bypass formula confirmation. Mitigation: keep formula tokens non-editable,
  intercept backward/forward boundary deletion before mutation, and cover explicit, cancelled, and
  confirmed paths in component and browser tests.
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
- [x] Tests written or updated
- [x] Implementation complete
- [x] Documentation updated
- [x] Relevant checks pass
- [x] Diff reviewed
- [x] Branch rebased on current main
- [x] Conflict resolution re-tested
- [x] Handoff summary written

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
- 2026-08-27: Treat the second clarification as the precise Milestone 3 correction contract on the
  same branch and ChangePlan. Keep typed blocks canonical while presenting them as inline runs; do
  not add a generic rich-text dependency.
- 2026-08-27: Use browser-native plaintext editing and Selection/Range offsets for the caret. Formula
  insertion/deletion remains a pure typed-state operation rather than accepting edited DOM markup.
- 2026-08-27: Require an application confirmation dialog for every whole-formula deletion. Ordinary
  deletion within non-empty MathLive content remains visual expression editing.
- 2026-08-27: Initial deletion-dialog focus goes to the safe **Keep formula** action. Escape cancels
  deletion without mutation; keyboard and touch users never need to accept the destructive action
  merely to dismiss the dialog.

## Discoveries

- The merged SVG fixture itself contains synthetic 1/2/3 numbering, not only the React step UI.
- The existing confirmed UI exposes step IDs and variant names solely to demonstrate serialization;
  the callback seam can prove typed order without exposing those details to a learner.
- The generated API client has no transcription result. Flattening this frontend-local spike does
  not create generated-contract drift or a compatibility obligation.
- The first real-browser inline run exposed reversed character input because React reconciliation
  reset the native caret after each keystroke. Keeping live text in the canonical ref without
  rerendering the editable host fixed the product behavior; structural edits and confirmation still
  commit a validated state.
- A production Next.js rewrite is compiled into the build, and object-storage CORS expects the
  standard localhost web origin. The first current isolated `make check` attempt used ports
  3101/8100: all five correction cases passed, but all five unrelated foundation uploads correctly
  failed at the signed storage request. The passing harness ran the branch frontend at port 3000
  inside the Playwright container, proxied its branch API on host port 8100 and host storage on
  container port 9000, then restored the tracked runner byte-for-byte. No temporary harness file or
  test artifact remains.

## Verification evidence

- `git fetch origin main` completed before implementation and again before handoff. The branch was
  rebased from the original Milestone 3 base `f899a11` onto current `origin/main` at `3753cd9`; there
  were no conflicts.
- Required root/local instructions, the MVP plan, prior complete ChangePlan, rendering/transcript
  architecture, device report, correction source/tests, package/validation configuration, relevant
  generated contracts, and repository-local Next.js Server/Client and CSS guides were read.
- Baseline for the second clarification: 3 focused files and 13 tests passed in 946 ms.
- Earlier flat-state TDD first failed against schema `1.0.0`, the old step exports/UI, and the old
  technical confirmation. For this refinement, formula-at-caret and formula-delete operation imports
  failed before implementation; MathLive focus behavior failed before `focusOnReady`; the continuous
  DOM/native-input/formula workflow assertions failed against block rows; and safe dialog focus
  failed while focus remained on the destructive trigger. Each slice reached focused green before
  the next.
- Final focused renderer/editor/transcript command:
  `npx vitest run features/transcription/transcript-state.test.ts
components/transcription/transcript-editor.test.tsx
components/transcription/correction-spike-app.test.tsx components/math/mathlive-editor.test.tsx
components/math/math-renderer.test.tsx components/content-preview.test.tsx --coverage=false` — 6
  files and 44 tests passed in 1.06 seconds before full verification, in 952 ms during diff review,
  and in 1.14 seconds after the final rebase freshness check.
- `make lint` and `make typecheck` passed independently during refactor. ESLint caught ref access in
  the first initializer; lazy validated state initialization corrected it without changing behavior.
- `make check` — passed after the isolated browser harness was corrected. It repeated every
  required gate and ran 10 Playwright cases across the five configured projects in 8.5 seconds.
  Prettier/Ruff formatting, ESLint/Ruff lint, TypeScript/mypy over 30 API source files, generated API
  drift, content validation, production build, 66 frontend tests, 25 backend tests, two complete
  migration downgrade/upgrade cycles, 19 integration tests, and all browser cases passed. Frontend
  coverage was 87.39% statements, 81.31% branches, 89.72% functions, and 87.65% lines. The content
  package hash remained
  `59f9572fb526842cbdddf438db2468c8d578a637fe814102f5bfbb95118ce7db`. Foundation/correction
  timings were compact Chromium 1.0/1.8 s, Pixel 7 Chromium 1.3/1.9 s, iPhone 13 WebKit 4.7/6.4 s,
  iPad portrait WebKit 3.8/7.2 s, and iPad landscape WebKit 2.8/6.2 s.
- Dedicated production-build correction visual run — 5 passed in 8.4 seconds: compact Chromium 1.8
  s, Pixel 7 Chromium 3.0 s, iPhone 13 WebKit 7.1 s, iPad portrait WebKit 6.9 s, and iPad landscape
  WebKit 7.7 s.
- Active-MathLive, delete-dialog, and final full-page screenshots for all five projects were
  inspected at original detail. Phone tabs, tablet split layout, one paper-like native-caret
  document, inline activation/insertion, safe-action dialog focus, contextual controls, content-only
  confirmation, and horizontal containment were correct. Long phone content remained locally
  contained without document/page overflow. Temporary configs, proxies, traces, screenshots, and
  test results were removed; the shared checkout and its corpus/data work were not touched.
- `git diff --check origin/main...HEAD`, the complete file-by-file diff review, and searches for
  correction-stage step exports/fields plus executable/unsafe HTML paths completed without an
  implementation finding. Intentional negative test and documentation references are retained.

## Result

The clarified Milestone 3 correction phase is complete on the same feature branch. It now presents
the canonical flat typed block array as one Word-like inline document with native text caret input,
exact-caret visual formula insertion, click-to-edit MathLive, controlled idle KaTeX, and confirmed
whole-formula deletion. Confirmation serializes exactly the reviewed ordered text/math content and
shows no technical structure. All renderer safety constraints remain, the five-project responsive
matrix has no horizontal overflow, and reasoning-step detection remains explicitly deferred. No
real OCR, grading, persistence, API/schema/database change, or added dependency is included.
