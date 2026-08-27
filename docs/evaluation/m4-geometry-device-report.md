# Milestone 4 geometry device and regression report

## Run metadata

- Date: 2026-08-27
- Branch: feat/m4-interactive-geometry-engine
- Application build: Next.js 16.3.2 production build from this branch
- Geometry runtime: exact jsxgraph 1.13.2, dynamically loaded from the local production bundle
- Browser runtime: mcr.microsoft.com/playwright:v1.62.1-noble
- Fixture: repository-owned synthetic all-primitives scene and static fallback; no examination,
  student, AI, or provider data

Ports 3000 and 8000 were already owned by the completed Milestone 3 worktree. Those processes were
not stopped or changed. The committed Playwright configuration and E2E helper retain the normal
defaults while accepting optional isolated ports. This branch's production web/API servers ran on
3104/8104:

    PLAYWRIGHT_WEB_PORT=3104 PLAYWRIGHT_API_PORT=8104 VISUAL_QA=1 \
      ./scripts/run_e2e.sh tests/e2e/geometry.spec.ts

The helper started this branch's production servers and ran the unchanged five projects inside the
version-matched browser container. Generated screenshots and test results were inspected locally and
remain ignored build artifacts.

## Exact automated result

Final production-build visual run: **5 passed in 5.6 seconds**.

| Project                      | Engine   | CSS viewport | Layout              | Result | Test time |
| ---------------------------- | -------- | ------------ | ------------------- | ------ | --------- |
| compact-chromium             | Chromium | 360 × 640    | stacked phone       | PASS   | 2.2 s     |
| pixel-7-chromium             | Chromium | 412 × 839    | stacked phone       | PASS   | 2.7 s     |
| iphone-13-webkit             | WebKit   | 390 × 664    | stacked phone       | PASS   | 4.9 s     |
| ipad-pro-11-portrait-webkit  | WebKit   | 834 × 1194   | board/control split | PASS   | 4.7 s     |
| ipad-pro-11-landscape-webkit | WebKit   | 1194 × 834   | board/control split | PASS   | 4.6 s     |

## Regression assertions exercised in every project

- Authenticate through the real local invite session and enter the internal geometry route from the
  workspace.
- Render the real JSXGraph board from declarations deliberately placed out of dependency order.
- Assert the board becomes an ARIA-labelled region using the curated accessibility description.
- Capture the initial point/constraint snapshot, reload, and require identical output for identical
  scene/action input.
- Exercise the committed scene containing point, segment, line, ray, circle, arc, polygon, angle,
  midpoint, intersection, perpendicular, parallel, circumcircle, and label.
- Drag only free point A and require its coordinates plus midpoint M to change while locked point B
  remains fixed.
- Require every midpoint, intersection, perpendicular, parallel, and circumcircle residual after
  pointer release to be below 1e-7.
- Attempt to drag constructed midpoint M and locked free point B; require both final coordinates to
  remain unchanged.
- Select a configured object through a real touch tap.
- Start ask-select, disable selectable objects outside its curated allowlist, record an incorrect
  allowed response deterministically, then submit the correct response with keyboard Enter.
- Apply show, hide, highlight, clear-highlight, focus, and approved point-animation actions through
  the real control surface.
- Require the geometry shell, board, controls, action/selection lists, and diagnostic output to stay
  inside the viewport.
- Require document scroll width to remain within one CSS pixel of client width.

Schema, unit, integration, and component coverage separately rejects duplicate IDs, unknown
parents, direct/indirect cycles, unsupported types, malformed viewports/properties, missing
accessibility/fallback data, unknown initial-visible IDs, unknown action targets, target-type and
allowlist violations, extra executable/markup fields, and renderer/load failures.

## Real-browser refinements

The red-to-green browser sequence found issues that mock construction tests could not expose:

1. Another worktree's servers occupied the default ports. The committed config/helper now accept
   isolated ports without changing default CI behavior or stopping shared processes.
2. A long SVG label intercepted a phone touch near point B. JSXGraph text is now non-interactive,
   and the synthetic label is short and offset from its parent.
3. The first fixture placed selectable intersection I inside phone touch precision around B. Moving
   locked B farther away made the selection question unambiguous without weakening the allowlist.
4. Mid-drag callbacks observed JSXGraph before every dependent renderer update. The final pointer-up
   callback now records the settled canonical constraint snapshot.
5. A point-endpoint metric was unsuitable for JSXGraph's internally constructed parallel line.
   Constraint diagnostics now use normalized line equations and correctly report zero residual.
6. A fourth authenticated-header action exceeded the Pixel 7 width. Header actions now wrap without
   overlap or document overflow.
7. JSXGraph replaced the initial React role and blanked the board label during initialization. The
   curated description is now passed as the board title and verified in the real DOM.

No scene rule, action allowlist, fixed-object rule, or safety assertion was weakened to obtain the
passing run.

## Manual screenshot inspection

Full-page screenshots from the passing production run were inspected for all five projects.

| Area                   | Phone result                                                         | Tablet result                                          |
| ---------------------- | -------------------------------------------------------------------- | ------------------------------------------------------ |
| Fixture identification | Internal-only and synthetic-content labels remain above the board    | Same labels remain prominent in the wide header        |
| Geometry board         | Full bounded viewport is visible; free/selected A is distinct        | Board remains large and readable beside controls       |
| Dense construction     | All line/curve/polygon examples remain contained                     | Extra width improves separation of points and labels   |
| Actions                | One column at compact/iPhone widths; two columns where space permits | Bounded control panel beside the board                 |
| Ask-select             | Prompt, disabled disallowed choices, and result are readable         | Prompt and choices remain grouped in the control panel |
| Constraint output      | Long JSON wraps inside its own dark output surface                   | Output stays below the split and within the card       |
| Static fallback        | Discoverable after the live scene without duplicating the main board | Same disclosure remains within the scene card          |
| Horizontal overflow    | None observed or reported by automation                              | None observed or reported by automation                |

The screenshots show the post-drag construction, approved animation/selection styling, active
ask-select state, and near-zero settled constraint residuals. Touch targets remain comfortably
spaced, and non-selectable labels do not intercept the board.

## Outcome and remaining device work

Milestone 4 meets its emulator-first phone/tablet exit condition. Curated scenes render
deterministically, every approved construction remains parent-derived, only a configured free point
moves, actions and selection questions remain inside curated ID allowlists, the real board is
accessibly described, static fallback assets exist, and all five projects pass without horizontal
overflow.

Physical Android/iPhone/iPad testing and true iOS/iPadOS Simulator validation remain pre-pilot work
under the MVP plan. The route is authenticated and synthetic-only; no student-authored construction,
AI geometry generation, grading, persistence, or external content was exercised.
