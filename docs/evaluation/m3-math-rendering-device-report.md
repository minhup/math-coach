# Milestone 3 mathematical rendering device and regression report

## Run metadata

- Date: 2026-08-27
- Branch: `feat/m3-math-rendering-correction-spike`
- Application build: Next.js 16.3.2 production build from this branch
- Browser runtime: `mcr.microsoft.com/playwright:v1.62.1-noble`
- API: existing local FastAPI service on `127.0.0.1:8000`; the test used only the existing pilot
  login/session contract
- Fixture: repository-owned synthetic algebra sheet and deterministic typed transcript; no student
  data or AI/provider output

Ports 3000 and 8000 were already owned by services from the original shared checkout. They were not
stopped or changed. For isolated evidence, this branch's production frontend ran on port 3100 and a
temporary, uncommitted Playwright config changed only `baseURL` to `http://localhost:3100`; it
inherited the repository's five projects unchanged. The browser run used Docker with host networking:

```text
docker run --rm --network host --user <uid>:<gid> --env HOME=/tmp \
  --env PLAYWRIGHT_EXTERNAL_SERVERS=1 --env VISUAL_QA=1 \
  --volume /home/minh/dev/math-coach-m3:/work --workdir /work \
  mcr.microsoft.com/playwright:v1.62.1-noble \
  npx playwright test tests/e2e/math-correction.spec.ts \
  --config playwright.m3.local.config.ts
```

The temporary config and generated screenshots are not product artifacts and are not committed.
The spec itself runs unchanged through the repository's normal `playwright.config.ts` and
`make test-e2e` commands.

## Exact automated result

Final production-build visual run: **5 passed in 6.5 seconds**.

| Project                        | Engine   | Viewport   | Required layout       | Result | Test time |
| ------------------------------ | -------- | ---------- | --------------------- | ------ | --------- |
| `compact-chromium`             | Chromium | 360 × 640  | PHOTO/TRANSCRIPT tabs | PASS   | 1.3 s     |
| `pixel-7-chromium`             | Chromium | 412 × 839  | PHOTO/TRANSCRIPT tabs | PASS   | 1.8 s     |
| `iphone-13-webkit`             | WebKit   | 390 × 664  | PHOTO/TRANSCRIPT tabs | PASS   | 5.2 s     |
| `ipad-pro-11-portrait-webkit`  | WebKit   | 834 × 1194 | simultaneous split    | PASS   | 5.3 s     |
| `ipad-pro-11-landscape-webkit` | WebKit   | 1194 × 834 | simultaneous split    | PASS   | 5.7 s     |

A final non-visual rerun after adding explicit photo visibility and forbidden-element assertions also
passed all five projects in 5.5 seconds. The visual run above was captured after removing sticky
phone-tab positioning so the tab control never covers transcript controls.

## Regression assertions exercised in every project

- Authenticate through the real local pilot session and enter the route from the workspace link.
- Identify the fixture as synthetic and not student work.
- On phones, expose PHOTO/TRANSCRIPT tabs, move selection/focus with arrow keys, and activate the
  transcript with a touch event.
- On tablets, omit the phone tabs and show photo plus transcript simultaneously.
- Render valid inline and display mathematics through KaTeX.
- Show the concise `Math needs correction` placeholder for the malformed fixture.
- Assert that the complete malformed source string is absent from `body.innerHTML`.
- Keep the real MathLive field visible, focus it, select its contents with the keyboard, and enter a
  correction; then verify the failure placeholder disappears.
- Move a block, split and merge a step, reorder steps, and confirm the visible transcript.
- Verify the confirmation summary records the exact resulting typed order and identifies the future
  authoritative grading input.
- Assert `documentElement.scrollWidth <= documentElement.clientWidth + 1`.
- Assert every correction shell, panel, transcript step/block, controlled renderer, MathLive editor,
  and control row remains inside the viewport bounds.

## Manual screenshot inspection

Full-page screenshots from the final production run were inspected at high detail for all five
projects.

| Area                         | Phone result                                                       | Tablet result                                       |
| ---------------------------- | ------------------------------------------------------------------ | --------------------------------------------------- |
| Fixture identification       | Synthetic label remains prominent                                  | Synthetic label remains prominent                   |
| Photo/transcript navigation  | Tabs are visible, separate from content, and do not cover controls | Both panels are visible with no phone tablist       |
| Synthetic photo              | Visible in the PHOTO panel before the automated tab switch         | Visible and legible in the left column              |
| KaTeX preview                | Readable; long math stays inside its own bounded scroll area       | Readable within the transcript column               |
| MathLive visual editor       | Visible with keyboard/menu affordances and no raw-source field     | Visible at a usable width in portrait and landscape |
| Reorder/correction controls  | Labels remain legible and touch targets remain at least 44 px      | Controls wrap without overlap or clipping           |
| Confirmation                 | Ordered typed summary fits the phone width                         | Ordered typed summary fits the transcript column    |
| Horizontal document overflow | None observed or reported by automation                            | None observed or reported by automation             |

## Outcome

The Milestone 3 correction spike meets its configured phone/tablet exit condition. The safe failure
state never exposes source LaTeX, valid mathematics uses the controlled renderer, invalid
mathematics remains visually correctable, typed block/step operations preserve order, and the
confirmed summary reflects the exact visible state. No grading, persistence, AI integration, or
student-data flow was exercised.
