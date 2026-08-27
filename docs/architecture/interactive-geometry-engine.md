# Interactive geometry engine

Milestone 4 renders reviewed, versioned geometry scenes without introducing an executable drawing
language. A geometry scene remains canonical Pydantic-owned content; JSXGraph is a presentation and
constraint runtime behind an application-owned exhaustive adapter.

## Canonical scene contract

GeometrySceneVersion extends the Milestone 2 contract without changing content schema version
1.0.0. Every scene contains:

- an immutable UUID and positive version;
- a finite viewport with strictly increasing x and y bounds;
- unique stable object IDs and explicit parent IDs;
- unique initially visible object IDs and approved animation IDs;
- a non-empty accessibility description;
- a repository-owned static fallback asset ID; and
- reviewed original-synthetic provenance.

Only these object types are accepted:

| Type                    | Required parents             | Additional curated data                        |
| ----------------------- | ---------------------------- | ---------------------------------------------- |
| point                   | none                         | finite x, y; optional draggable and selectable |
| segment, line, ray      | two points                   | optional label/selectable capability           |
| circle                  | center point, radius point   | optional label/selectable capability           |
| arc, angle              | three points                 | optional label/selectable capability           |
| polygon                 | 3–32 points                  | optional label/selectable capability           |
| midpoint                | two points                   | optional label/selectable capability           |
| intersection            | two line/circle-like objects | required branch intersectionIndex 0 or 1       |
| perpendicular, parallel | line-like object, point      | optional label/selectable capability           |
| circumcircle            | three points                 | optional label/selectable capability           |
| label                   | one point                    | non-empty application-rendered text            |

Constructed objects cannot carry coordinates or be draggable. Labels cannot be selectable. Only a
free point with draggable enabled is movable; all other JSXGraph elements are created as fixed. The
optional capabilities default to false, preserving already committed Milestone 2 scene hashes.

Pydantic is authoritative. The generated content JSON Schema, OpenAPI document, and TypeScript
declarations are committed from that model. The frontend still performs strict exact-key and
semantic validation because API, future AI, cached, or external payloads are untrusted at runtime.
The web boundary does not accept additional object types, properties, URLs, style maps, markup,
handlers, expressions, functions, or source programs.

## Validation and deterministic construction

Validation rejects the whole scene before renderer import when it finds:

- a duplicate object, visibility, or animation ID;
- an unknown parent or initially visible object;
- a direct or indirect construction cycle;
- an unsupported type or unknown field;
- a malformed viewport, coordinate, parent count, parent type, or intersection branch;
- a draggable constructed object or selectable label; or
- a missing accessibility description or fallback asset ID.

Construction order is derived from parent relationships, not declaration order. At each step the
validator takes the lexicographically first object whose parents have already been constructed.
Identical scene input therefore produces the same complete order. If no object is ready while any
remain, validation rejects the cycle; no partial trusted scene is returned.

The JSXGraph adapter receives only a validated scene and switches exhaustively over the approved
types. It passes already-created parent objects rather than source strings. Labels use
application-owned coordinate closures with parsing and MathJax disabled; no content-provided
function is possible. The board disables pan, wheel zoom, navigation controls, and remote resources.
A setup or update exception frees the partial board and replaces it with a concise accessible
fallback.

## Typed actions and interaction state

The finite action union is:

    show(objectIds[])
    hide(objectIds[])
    highlight(objectIds[])
    clear_highlight(objectIds[] or null)
    focus(objectIds[])
    animate(objectId, animationId)
    ask_select(prompt[], allowedObjectIds[], correctObjectIds[] or null)

Every action is exact-key validated against the current scene. Object targets must exist. Animate
additionally requires an approved animation ID and a point-like target. An ask-select allowlist may
contain only objects explicitly marked selectable, and every correct object must be in that
allowlist. Its prompt is recursively validated typed ContentBlock data, not Markdown or HTML.

The pure interaction reducer stores construction-ordered visible, highlighted, and focused IDs, one
point animation sequence, and deterministic selection state. Invalid actions and selections return
the unchanged state plus one safe error. A configured object may be selected with pointer, touch, or
the labelled button path. While an ask-select question is active, objects outside its allowlist are
rejected and their buttons are disabled. Correct, incorrect, ungraded, and pending results are
derived only from the curated IDs.

Dragging updates only a permitted free point. JSXGraph maintains midpoint, intersection,
perpendicular, parallel, and circumcircle dependencies from the parent objects. The internal spike
publishes a test-only constraint snapshot after drag and pointer release; the browser regression
verifies every normalized residual remains below 1e-7 and that attempts to drag a locked free point
or constructed midpoint do not change coordinates.

## Content and authenticated surfaces

Typed geometry ContentBlock records resolve a scene version through the existing authenticated
content-preview response. Missing or invalid references render a concise unavailable state. Valid
references render the shared geometry experience, and hint actions are validated again against that
scene before a control is exposed.

/internal/geometry-spike checks the existing invite session before exposing the comprehensive
synthetic fixture. It exercises every approved primitive and action, selection allowlists,
free-point movement, constraint monitoring, accessibility copy, and fallback image. It does not add
an API endpoint or load student data.

Phone layouts stack the board and controls; tablet layouts use a bounded split. Controls retain
touch-sized targets, labels do not intercept point touches, long diagnostic output wraps, and the
document must not overflow horizontally. JSXGraph's board title is set to the curated accessibility
description. Every valid scene also exposes its static fallback in a details element; invalid or
failed scenes fall back immediately when safe asset metadata is available.

## Security boundary

Geometry content is data, never code. The application does not call eval, Function, JessieCode,
JSXGraph readers/parsers, dangerouslySetInnerHTML, a Markdown renderer, or an SVG/HTML injection
path. Runtime AI may eventually request only one of the typed actions above against IDs in an
already validated curated scene. It may not create objects, publish scenes, supply markup, or change
construction parents.

The only new dependency is exact jsxgraph@1.13.2, dynamically imported on the client and locked
locally. The package's CSS is not an exported package subpath, so the application owns the small
required board/text/infobox styles instead of importing an unsupported path. No generic canvas
framework, wrapper, code interpreter, rich-text framework, AI SDK, RAG system, or vector database is
introduced.

## Persistence, verification, and rollback

No database migration or API route is required. Existing immutable geometry-version and hint-action
JSONB fields store the backward-compatible capability fields. The incremental M4 synthetic package
uses new immutable IDs, references two explicit exam cycles, and imports transactionally beside the
M2 package.

Unit and schema tests cover all primitives, exact validation failures, topological order, typed
actions, reducer behavior, and constraint residual calculation. Component tests cover construction,
capability mapping, selection, actions, accessibility, partial-render cleanup, safe fallback, and
content-preview integration. The Playwright regression runs the real production renderer in all
five configured phone/tablet projects. Exact device results are in
[the Milestone 4 report](../evaluation/m4-geometry-device-report.md).

Rollback reverts this milestone, removes the synthetic M4 package, internal route, frontend adapter,
and JSXGraph dependency. Existing Milestone 2 scenes remain valid because inactive optional fields
are excluded from canonical serialization. No database downgrade, backfill, AI/provider cleanup, or
student-state recovery is involved.
