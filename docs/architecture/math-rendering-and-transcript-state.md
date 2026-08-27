# Mathematical rendering and transcript-state architecture

Milestone 3 establishes the frontend boundary for safe mathematical display and visual correction.
It is an authenticated internal spike built from deterministic synthetic fixtures. It does not
transcribe an image, call an AI provider, grade work, persist a transcript, or update learner state.

## Controlled read-only rendering

`MathRenderer` is the only read-only mathematics renderer. Existing typed problem previews delegate
inline math, display math, rich-line math spans, and nested typed callout content to it. Text remains
an ordinary React text node. The generated `ContentBlock` union remains the canonical problem-content
model; the renderer changes presentation only.

Each source string is untrusted, including future strings received from transcription or AI. The
renderer:

1. rejects empty/whitespace-only input and input longer than 2,000 characters;
2. creates a detached DOM staging node;
3. calls KaTeX's DOM renderer with `throwOnError: true`, `strict: "error"`, `maxExpand: 100`,
   `maxSize: 10`, `globalGroup: false`, a fresh empty macro map, and HTML plus MathML output;
4. supplies a trust callback that records every trusted-command attempt and always returns `false`;
5. commits the staged children only when parsing succeeded and no trusted command was attempted;
6. otherwise replaces the mounted host with the source-free accessible label `Math needs
correction`.

The detached node is important. KaTeX can produce source-revealing output for rejected trusted
commands even when trust is false, and exception messages can include the source. Neither staged
output nor exception details enter failure-state DOM. Link, external-image, and HTML commands are
therefore rejected as a whole rather than partially rendered. Recursive expansion fails at the
finite expansion limit; explicit element sizes are capped. Every renderer is bounded to its parent,
and display math may scroll inside its own labelled region without expanding the document.

React does not use `dangerouslySetInnerHTML` for this boundary. Arbitrary HTML or Markdown is never a
content type, and no generated script, event handler, executable geometry, external resource, AI
HTML, or code is accepted or run. KaTeX alone writes its documented generated DOM into the dedicated
empty host.

The implementation follows KaTeX's official
[options](https://katex.org/docs/options), [security](https://katex.org/docs/security), and
[error-handling](https://katex.org/docs/error) guidance.

## Visual mathematics editing

`MathLiveEditor` wraps MathLive's `<math-field>` custom element. The wrapper dynamically registers
the element in the browser, loads the package's local font CSS, assigns mathematics through the
element's `value` property, and consumes its public `input` event. Source is not rendered as a text
child, input/textarea value, HTML attribute, loading message, or error message. Students interact
with a visual formula field through physical keyboard and touch virtual-keyboard affordances; they
are never required to read or edit raw LaTeX.

An idle mathematics transcript block shows only the controlled KaTeX result. Activating that result
replaces it with the visual editor; completing the edit returns to the controlled renderer. The
preview and editor are not permanently displayed as separate areas. A failed render shows the safe
placeholder inside the same activation control, so invalid mathematics remains directly correctable.
Correcting the field updates typed transcript state. A local-package load failure has an explicit
source-free failure message and does not fabricate a corrected expression.

The integration uses MathLive's official
[React integration](https://mathlive.io/mathfield/guides/integration/),
[mathfield API](https://mathlive.io/mathfield/api/), and
[virtual keyboard](https://mathlive.io/mathfield/guides/virtual-keyboards/) contracts. MathLive's
transitive compute engine is bundled by the package but is not called by this spike.

## Typed transcript state

The frontend-local correction model is deliberately smaller than problem `ContentBlock` content:

```typescript
type TranscriptBlock =
  { id: string; type: "text"; text: string } | { id: string; type: "math"; latex: string };

type TranscriptState = {
  schemaVersion: "2.0.0";
  attemptId: string;
  blocks: TranscriptBlock[];
};
```

It is not an HTTP or database schema. Future transcription work must define and validate a server
contract before accepting provider payloads.

The validator enforces:

- a supported schema version and non-empty attempt ID;
- at least one block; and
- unique, non-empty block IDs.

Pure operations accept caller-supplied IDs, never use time or randomness, do not mutate their input,
and validate every result. The `blocks` array is the sole canonical order, so no ownership/reference
array can orphan or multiply reference a block. Add inserts at an explicit global index, delete
removes a non-final block, and up/down movement swaps adjacent blocks across the continuous document.
There are no correction-stage step types or split/merge/move-step operations. Controls live in
labelled contextual menus with disabled boundary states, so drag-and-drop is unnecessary.

Confirmation validates once more and produces a deeply independent snapshot whose flat block array
matches the exact visible order. It contains no timestamp, score, grade, provider record, AI
metadata, or reasoning grouping, so identical visible state serializes identically. The UI renders
the reviewed content without IDs, schema details, or variant labels and identifies it as the future
authoritative grading input. No grading or reasoning-step pipeline exists in Milestone 3.

## Authenticated correction route and responsive layout

`/internal/math-correction` calls the existing authenticated-session endpoint before rendering its
fixture. Checking, authentication-required, retryable-unavailable, and ready states are explicit.
The ready state uses only a repository-owned SVG labelled as synthetic/non-student work and a local
deterministic transcript explicitly presented as simulated OCR output. No OCR service runs.

Below 768 px, PHOTO and TRANSCRIPT are keyboard-operable tabs and only the selected tab panel is
exposed. At 768 px and above, the phone tablist is absent and the photo plus transcript are visible in
a two-column split. The transcript is one paper-like document surface: text edits in place, formulas
switch between idle KaTeX and active MathLive, and block actions are contextual. Controls have
labelled minimum 44 px targets, wrap at narrow widths, and remain inside the viewport. Long display
formulas may scroll only within their own bounded renderer.

## Contracts unchanged

Milestone 3 adds no database table, migration, HTTP route, OpenAPI declaration, generated API type,
AI contract, content-package schema, geometry engine, Markdown renderer, rich-text framework, RAG
system, or vector database. It reuses `GET /api/v1/auth/me` solely as an internal access gate.

The spike also makes no singular-exam assumption. Existing multi-exam content and learner-target
contracts remain unchanged.

## Verification and rollback

Unit tests cover flat transcript invariants and immutable operations. Component tests cover the
complete render corpus, source-free adversarial failures, MathLive property/event behavior,
click-to-edit correction, mixed blocks, contextual operations, authentication states, and
content-only confirmation. The browser regression runs in all five configured phone/tablet projects
and checks real MathLive keyboard correction, touch/keyboard tab controls, absence of reasoning-step
UI/state, exact flat confirmation order, source absence, forbidden elements, and horizontal
containment.
Exact results are in
[the Milestone 3 device report](../evaluation/m3-math-rendering-device-report.md).

Rollback reverts this milestone, removes the internal route and its two locked dependencies, and
restores the prior preview presentation. There is no database downgrade, data backfill, transcript
recovery, or provider cleanup because the spike creates no persistent or external state.
