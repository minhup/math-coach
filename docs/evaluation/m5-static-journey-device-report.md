# Milestone 5 static journey device and regression report

## Run metadata

- Date: 2026-08-27
- Branch: `feat/m5-static-end-to-end-student-slice`
- Application build: Next.js 16.3.2 production build from this branch
- Browser runtime: `mcr.microsoft.com/playwright:v1.62.1-noble`
- API/storage: this branch's FastAPI, PostgreSQL, and MinIO on isolated ports 8105, 5535, and 9105
- Fixture: repository-owned original-synthetic M2/M4 content, deterministic application mock
  payloads, generated synthetic PNGs, and five synthetic development invite identities

The original shared checkout and services were not changed. This clean worktree used Compose project
`math-coach-m5`, web port 3105, API port 8105, PostgreSQL port 5535, and MinIO API/console ports
9105/9106. Per-project synthetic invite codes keep each parallel browser's one profile and target
collection isolated. The fixture contains no real examination, learner, provider, or personal data.

Playwright is capped at five workers, one for each required project. The host volume was 99% full
during verification; eight concurrent browsers/uploads could make local MinIO return HTTP 507 even
though the UI exposed the transfer as retryable. Five workers preserves cross-device parallelism and
made earlier full runs stable without weakening an assertion. When the remaining disk later fell
below MinIO's safety threshold, even a 68-byte PNG correctly received 507 on its initial PUT and
retry. The final root check therefore used the same pinned MinIO image with a temporary 256 MB
memory-backed `/data` store at ports 9115/9116. It exercised the real presign/PUT/verification flow;
the exact temporary container and its synthetic data were removed after the run.

## Exact automated result

The focused full-journey production run passed **5 tests in 8.0 seconds**.

| Project                        | Engine   | CSS viewport | Result | Test time |
| ------------------------------ | -------- | ------------ | ------ | --------- |
| `compact-chromium`             | Chromium | 360 × 640    | PASS   | 2.8 s     |
| `pixel-7-chromium`             | Chromium | 412 × 839    | PASS   | 3.0 s     |
| `iphone-13-webkit`             | WebKit   | 390 × 664    | PASS   | 7.3 s     |
| `ipad-pro-11-portrait-webkit`  | WebKit   | 834 × 1194   | PASS   | 7.1 s     |
| `ipad-pro-11-landscape-webkit` | WebKit   | 1194 × 834   | PASS   | 7.3 s     |

An earlier stable full browser suite passed **15 tests in 16.4 seconds**. The final post-rebase root
check passed the same **15 tests in 16.7 seconds** using the memory-backed verification store
described above. It includes the complete M5 journey, the standalone Milestone 3 correction
regression, and the Milestone 4 all-primitives geometry regression in every project.

| Project                        | M5 journey | Math regression | Geometry regression |
| ------------------------------ | ---------- | --------------- | ------------------- |
| `compact-chromium`             | 2.2 s      | 1.3 s           | 2.3 s               |
| `pixel-7-chromium`             | 2.4 s      | 1.3 s           | 2.4 s               |
| `iphone-13-webkit`             | 8.9 s      | 7.1 s           | 5.0 s               |
| `ipad-pro-11-portrait-webkit`  | 8.5 s      | 5.8 s           | 4.8 s               |
| `ipad-pro-11-landscape-webkit` | 6.8 s      | 4.2 s           | 3.7 s               |

## Complete journey assertions in every project

- Authenticate through the real invite/session boundary and resume or create exactly one profile.
- Create/load and render two active synthetic examination-target records as a collection.
- Generate the same ordered combined plan and show exact support target records on every item,
  including one-target and two-target support.
- Open typed math/geometry content and display the immutable problem-version ID used to create the
  owned attempt.
- Interact with the existing live JSXGraph board through a real touch tap and retain the curated
  accessible static fallback.
- Upload a generated clearly synthetic PNG through presign, MinIO transfer, and verified ready
  metadata; expose a transfer failure as retryable rather than advancing or fabricating success.
- Receive only the strictly validated deterministic mock transcript for that attempt.
- Edit ordinary text at the native caret and correct mathematics through the real MathLive visual
  field, then confirm a read-only authoritative snapshot.
- Require the evaluation control to appear only after confirmation and render typed deterministic
  feedback with explicit non-exhaustive-reference wording.
- Request the first two curated hints in order and apply their validated geometry actions through the
  existing scene controls.
- Create a second attempt with a distinct attempt ID and the same immutable problem-version ID.
- Render the exact typed concept version and complete an application-owned deterministic summary.
- Exercise touch plus keyboard activation and require no scripts, iframes, inline executable event
  attributes, raw AI HTML/Markdown, raw TeX learner controls, predicted score, or admission
  probability.
- Require `documentElement.scrollWidth <= documentElement.clientWidth + 1` and audit the journey,
  plan, content, board, fallback, upload, transcript, evaluation, hint, retry, concept, and summary
  surfaces for viewport containment.

Backend/unit/component coverage separately verifies empty/loading/retryable/permanent/uncertain
states, strict transcript/evaluation rejection and one schema retry, confirmation-before-evaluation,
invalid state-transition rejection, ownership isolation, deterministic plan and summary values,
typed-content exact keys, and failed/incomplete summary behavior.

## Manual screenshot inspection

The following full-page ignored artifacts from the passing focused production run were inspected at
original detail:

```text
test-results/m5-static-journey-compact-chromium.png
test-results/m5-static-journey-pixel-7-chromium.png
test-results/m5-static-journey-iphone-13-webkit.png
test-results/m5-static-journey-ipad-pro-11-portrait-webkit.png
test-results/m5-static-journey-ipad-pro-11-landscape-webkit.png
```

| Area                | Phone result                                                          | Tablet result                                                    |
| ------------------- | --------------------------------------------------------------------- | ---------------------------------------------------------------- |
| Progress/navigation | Current phase stays visible and control rows wrap                     | Phase trail uses the available width without dominating content  |
| Target/plan cards   | Both targets and item support labels wrap within one column           | Collections remain easy to scan at portrait and landscape widths |
| Math/geometry       | Math is bounded; the live board and fallback fit the content card     | Board remains readable with generous control spacing             |
| Upload/correction   | Upload action, native text surface, and MathLive controls stay usable | Transcript has comfortable line length and no clipped controls   |
| Evaluation/hints    | Typed feedback and hint controls stack without overlap                | Feedback, actions, and selection remain grouped                  |
| Retry/concept       | Attempt/version evidence and concept blocks remain legible            | Version relationships remain clear in the wider card             |
| Summary             | All deterministic fields fit at 360 px                                | Definition grid remains balanced in both orientations            |
| Horizontal overflow | None observed or reported by automation                               | None observed or reported by automation                          |

The screenshots show a coherent phone-first card sequence, readable target badges, bounded formulas,
and stable tablet spacing. No document-level horizontal overflow, clipped control, accidental raw
source, or success-after-failure presentation was observed.

## Outcome and remaining device work

Milestone 5 meets its emulator-first exit condition. The full invite-to-summary journey works on all
five configured phone/tablet projects, uses one profile with two targets and explicit per-item target
support, retains immutable content pinning across retry, and connects the existing typed math,
curated geometry, authorized upload, correction, confirmation, hint, and concept boundaries. Only
the confirmed transcript reaches the synthetic evaluation fixture, and session completion is derived
from application-owned state.

Physical Android/iPhone/iPad testing and true iOS/iPadOS Simulator validation remain pre-pilot work
under the MVP plan. Real transcription, production evaluation, learner-state evidence, and adaptive
planning remain Milestones 6–9 and were not exercised or implemented here.
