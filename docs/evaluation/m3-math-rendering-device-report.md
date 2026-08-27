# Milestone 3 mathematical rendering device and regression report

## Run metadata

- Date: 2026-08-27
- Branch: `feat/m3-math-rendering-correction-spike`
- Application build: Next.js 16.3.2 production build from this branch
- Browser runtime: `mcr.microsoft.com/playwright:v1.62.1-noble`
- API: compatible existing local FastAPI service on `127.0.0.1:8000`; the test used only the
  existing pilot login/session contract
- Fixture: repository-owned synthetic uploaded algebra sheet and deterministic flat typed transcript
  presented as simulated OCR; no student data or AI/provider output

Ports 3000 and 8000 were already owned by services from the original shared checkout. They were not
stopped or changed. This branch's production frontend ran on port 3100. A temporary, uncommitted
Playwright config changed only `baseURL` to `http://localhost:3100`, disabled Playwright-managed
servers, and inherited the repository's five projects unchanged. The browser run used Docker with
host networking:

```text
docker run --rm --network host --user 1000:1000 --env HOME=/tmp \
  --env PLAYWRIGHT_EXTERNAL_SERVERS=1 --env VISUAL_QA=1 \
  --volume /home/minh/dev/math-coach-m3:/work --workdir /work \
  mcr.microsoft.com/playwright:v1.62.1-noble \
  npx playwright test tests/e2e/math-correction.spec.ts \
  --config playwright.m3.local.config.ts
```

The temporary config, generated screenshots, traces, and test-result directory were removed after
inspection and are not product artifacts. The spec itself runs unchanged through the repository's
normal `playwright.config.ts` and `make test-e2e` commands.

## Exact automated result

Final production-build visual run: **5 passed in 6.6 seconds**.

| Project                        | Engine   | Viewport   | Required layout           | Result | Test time |
| ------------------------------ | -------- | ---------- | ------------------------- | ------ | --------- |
| `compact-chromium`             | Chromium | 360 × 640  | PHOTO/TRANSCRIPT document | PASS   | 1.2 s     |
| `pixel-7-chromium`             | Chromium | 412 × 839  | PHOTO/TRANSCRIPT document | PASS   | 1.7 s     |
| `iphone-13-webkit`             | WebKit   | 390 × 664  | PHOTO/TRANSCRIPT document | PASS   | 5.1 s     |
| `ipad-pro-11-portrait-webkit`  | WebKit   | 834 × 1194 | photo/document split      | PASS   | 5.3 s     |
| `ipad-pro-11-landscape-webkit` | WebKit   | 1194 × 834 | photo/document split      | PASS   | 5.9 s     |

Two earlier red runs are not passing evidence. The first reached the new page in all projects and
exposed an ambiguous text locator; the second exercised the correction and block operations in all
projects before exposing a Testing-Library-only locator accidentally used in Playwright. Both test
issues were corrected without weakening product assertions before the passing run.

## Regression assertions exercised in every project

- Authenticate through the real local pilot session and enter from the workspace link.
- Identify the image as a synthetic uploaded solution and the flat document as simulated OCR output.
- On phones, expose PHOTO/TRANSCRIPT tabs, move selection/focus with arrow keys, and activate the
  transcript with a touch event.
- On tablets, omit the phone tabs and show photo plus continuous document simultaneously.
- Assert one accessible editable document with no reasoning-step heading, boundary, split/merge
  control, move-step control, `stepId`, or synthetic step identifier.
- Render valid inline/display mathematics through controlled KaTeX while no MathLive field is
  permanently mounted.
- Show `Math needs correction` for malformed input; assert raw source and forbidden executable or
  external elements are absent.
- Activate the invalid formula, correct it through the real MathLive keyboard path, finish editing,
  and return to one KaTeX display.
- Edit text naturally in place.
- Open contextual block options, move a block globally, add a temporary text block, delete it, and
  confirm the visible transcript.
- Verify the confirmed snapshot has the exact content order, identifies the future authoritative
  grading input, and exposes no block IDs, schema details, arrows, or step structure.
- Assert `documentElement.scrollWidth <= documentElement.clientWidth + 1`.
- Assert correction shell/panels, document, blocks, menus, renderers, editor, control rows, and
  confirmed document remain inside the viewport.

## Manual screenshot inspection

Full-page screenshots from the passing production run were inspected at original detail for all five
projects.

| Area                         | Phone result                                                         | Tablet result                                        |
| ---------------------------- | -------------------------------------------------------------------- | ---------------------------------------------------- |
| Fixture identification       | Synthetic upload/simulated OCR label remains prominent               | Same label remains prominent                         |
| Photo/transcript navigation  | Tabs remain clear and do not cover document controls                 | Both panels visible; no phone tablist                |
| Synthetic uploaded solution  | Available in PHOTO before the automated switch                       | Visible and legible beside the document              |
| Continuous document          | One paper surface; no step cards or headings                         | One paper surface in the transcript column           |
| Text editing presentation    | Borderless paragraph-like text remains readable                      | Document-like text remains readable                  |
| Formula presentation         | One KaTeX result per idle formula; local math scrolling is contained | Formulas fit or remain locally contained             |
| Contextual controls          | Subtle ellipsis affordances and 44 px add/confirm controls fit       | Menus/add controls remain aligned                    |
| Confirmation                 | Reviewed content appears without IDs or type/schema summaries        | Content-only confirmation fits the transcript column |
| Horizontal document overflow | None observed or reported by automation                              | None observed or reported by automation              |

The automated flow finishes with the first text block moved below the first formula, deliberately
proving that the confirmation document follows visible flat array order rather than hidden grouping.
Compact phone screenshots show long formulas clipped only inside their explicitly scrollable math
container; no page or document surface expands horizontally.

## Outcome

The clarified Milestone 3 correction spike meets its configured phone/tablet exit condition. The
correction-stage model and UI are flat, the transcript reads as one editable document, invalid math
is source-free and directly correctable, MathLive appears only for the activated formula, and the
confirmed content matches the exact visible order without technical structure. Reasoning-step
detection remains deferred. No real OCR, grading, persistence, AI integration, or student-data flow
was exercised.
