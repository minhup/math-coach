# Milestone 6 transcription device and regression report

## Run metadata

- Date: 2026-08-28
- Branch: `feat/m6-multimodal-transcription`
- Application build: Next.js 16.3.2 production build from this branch
- Browser runtime: `mcr.microsoft.com/playwright:v1.62.1-noble`
- API/database/storage: this branch's FastAPI, a task-specific `math_coach_m6_e2e` PostgreSQL
  database, and an ephemeral MinIO container on API/console ports 9100/9101
- Web/API ports: 3100/8100, isolated from unrelated M3 processes on 3000/8000
- Provider: `application-owned-deterministic-fake`
- Model: `m6-transcription-fixture-v1`
- Prompt: `m6-faithful-transcription-v1`, SHA-256
  `d487b2f47b769380002a80fa31316bf8e238b3db15f34a7cff0c560473e0ad89`
- Provider/application schemas: `m6-provider-transcript-v1` / `3.0.0`
- Uploaded fixture: repository-owned `warnings-source-regions.png`, SHA-256
  `f0ba3a02b35369a27c2f0f08a53ba89522a6a4c7f014593ae00e3dd22e0eb592`

The run used only seeded synthetic invitation identities and the committed synthetic image corpus.
No real examination, learner, handwriting, personal data, provider response, provider credential, or
paid provider call was involved. The temporary database and MinIO container held only run-specific
synthetic data and were removed after verification.

## Exact automated result

The final production-build browser suite passed **15 tests in 22.7 seconds** across all five required
projects. It includes the complete M6 journey, the standalone Milestone 3 native-caret/MathLive
regression, and the Milestone 4 curated-geometry regression in every project.

| Project                        | Engine   | CSS viewport | M6 journey | Math regression | Geometry regression |
| ------------------------------ | -------- | ------------ | ---------- | --------------- | ------------------- |
| `compact-chromium`             | Chromium | 360 × 640    | 3.1 s      | 1.9 s           | 2.4 s               |
| `pixel-7-chromium`             | Chromium | 412 × 839    | 4.3 s      | 2.9 s           | 2.9 s               |
| `iphone-13-webkit`             | WebKit   | 390 × 664    | 12.9 s     | 8.6 s           | 6.4 s               |
| `ipad-pro-11-portrait-webkit`  | WebKit   | 834 × 1194   | 11.7 s     | 7.5 s           | 4.6 s               |
| `ipad-pro-11-landscape-webkit` | WebKit   | 1194 × 834   | 9.4 s      | 5.4 s           | 4.7 s               |

The final pre-merge root `make check` also passed the same 15 cases in **17.4 seconds**, after 146
frontend unit tests, 103 backend unit tests, 39 PostgreSQL/MinIO integration tests, two full migration
downgrade/upgrade cycles, contract generation verification, type checks, lint, formatting, content
validation, and the production build.

## Complete journey assertions in every project

- Authenticate through the invitation/session boundary and create or reload one study profile with
  two independent active examination targets.
- Reproduce the unchanged deterministic M5 plan, including one-target and two-target support arrays,
  and open an attempt pinned to immutable problem version
  `40000000-0000-4000-8000-000000000701`.
- Upload the clearly labeled synthetic source through presign, browser PUT, and server verification;
  attach only the owned ready upload to the owned attempt.
- Request the deterministic fake through the same authenticated production service used by real
  adapters and render nothing until the nested response passes the browser's strict runtime guards.
- Show finite warning text, keyboard/touch source-region controls, a normalized overlay on the owned
  source image, configured provider/model/schema identity, and the malformed mathematical statement
  exactly as returned rather than silently correcting it.
- Correct prose with a native caret, focus and edit the formula through MathLive, save immutable
  transcript version 2, and confirm its exact server-computed SHA-256 identity.
- Permit the downstream action only after confirmation and label its feedback as deterministic,
  synthetic, mocked, and not a real grade.
- Continue through existing curated hints, geometry actions, retry on the same immutable problem
  version, concept review, and an application-owned two-target session summary.
- Exercise touch and keyboard activation and require no raw provider HTML, Markdown, URLs, arbitrary
  data, raw TeX learner control, executable geometry, predicted scores, or production-grading claim.
- Require `documentElement.scrollWidth <= documentElement.clientWidth + 1` and zero audited journey,
  geometry, transcript, and math elements outside the viewport.
- Reload after completion and verify the existing SPA boundary: the owned profile and both targets
  reload, while the in-browser completion phase resets. Integration coverage separately proves the
  durable run, transcript versions, and confirmation reload through the authenticated attempt API.

## Manual screenshot inspection

Twenty ignored full-page artifacts from the final passing run were inspected at high detail: review,
active MathLive correction, clearly mocked evaluation, and terminal M5 summary for each project.
Their exact SHA-256 values are:

| Project                        | Review                                                             | MathLive                                                           | Mock evaluation                                                    | Summary                                                            |
| ------------------------------ | ------------------------------------------------------------------ | ------------------------------------------------------------------ | ------------------------------------------------------------------ | ------------------------------------------------------------------ |
| `compact-chromium`             | `c823da6bb80d6e33838252ad425ebdd65410770b72bf0cccd0c2c43a79f14cc6` | `d71681e58d728bfa1d718c2135231b077c3661df4e10723928dae2f23554539d` | `9329c8dac129eec6b2383a44e91d39482f9f2750bfe2e132f884d9b894fad426` | `997f7c9a54d677a6a9f43ce74d9a2a482790bed33d7336f0ba65090589085586` |
| `pixel-7-chromium`             | `5aef7aeeeb9cf5ab594c8cb5d0dac23e6af7b2754a4a6096e4b7636c8d9265fb` | `60af0c26649f152e811a6fc64bb1946110e474de35f6d866d58d43eb51e5eef1` | `f84ef41b26e3ad4e68a7df2b2e72978ee5761c834bc39146be03f38957ef8c20` | `52146876b047946c5514f5729e074e63ca6e2bb1c0edecde6c2f3b89fdcfc93a` |
| `iphone-13-webkit`             | `d71b26cd03709a6cd6ee273fd4647e7335c9b9d677a379e4a9bd3b0f6aa1a902` | `0bbe278e2c64c7a614855547a5da7b86cb730b15017a30761fbfef0a247dbc37` | `67d086b47fc71432da46e3ac07cffe13ea2aa169249918839c8eb94cfaf8c56b` | `40c15f09e2e3b5cf8b115426779630d1e32081567cf3d61af35715745a4ab7a0` |
| `ipad-pro-11-portrait-webkit`  | `80ead051615540c684d34dff223f6623acd03091ce05ec1f96395002fa173cd1` | `975f10d7daff7a0ad70aa95483698d9af677c19b4df74df319f6c2c3f57218de` | `4609055a77568354fed92b084e54698e6e8bc582a976e4f62296cdcb52fd8b0f` | `6336fefd709eccd88ae79d9f03808e7857d1cbc21800d0245170ed9891a1fce9` |
| `ipad-pro-11-landscape-webkit` | `2eff820de2bd744a77d01ed3c8357f4faa3f76eaebdeabace62b0086a7834478` | `810d6660ea692d4115318861e3ddb108e673ad0dc1fcd1b39eaa3a9115852922` | `ce5f5b2158e65d2a56daa3f3bf3d248ee8193c3be78a7f3f52725852fd876e90` | `4ed239f46379dec9687a6165d72016751bef8a784f73adbe15a59e299031dd69` |

| Area                  | Phone result                                                               | Tablet result                                                               |
| --------------------- | -------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| Source comparison     | Image, warning, and selected region stack legibly above the editor         | Portrait stacks cleanly; landscape keeps source and transcript side by side |
| Transcript correction | Native text and MathLive controls stay inside the card with usable targets | Line length, formula popover, and ordering controls remain readable         |
| Uncertainty cues      | Warning and provider/schema note remain visible before confirmation        | Cues stay adjacent to the reviewed document without obscuring the source    |
| Mock evaluation       | Explicit synthetic/non-grade language is prominent and formulas are sound  | Feedback remains visibly separate from provider-backed transcription        |
| Summary/regression    | Both targets, attempts, hints, and problem version fit at 360 px           | Summary grid remains balanced in portrait and landscape                     |
| Horizontal overflow   | None observed or reported by automation                                    | None observed or reported by automation                                     |

No clipped controls, document-level horizontal overflow, raw math source, raw provider content,
misleading production-grade label, or success-after-failure presentation was observed.

## Outcome and remaining device work

The deterministic production-shaped M6 journey meets the emulator/browser matrix requirement. The
source image is visibly synthetic, source-region comparison works across layouts, prose and math are
correctable with the intended native/MathLive controls, exact confirmation is shown before the mock
evaluation, and the unchanged M5 multi-target path reaches completion in every project.

Physical Android/iPhone/iPad testing and true iOS/iPadOS Simulator validation remain pre-pilot work.
The owner-deferred real Gemini benchmark was not run: zero provider calls and zero provider spend
occurred. Consequently this report supplies no real-model visual or latency evidence and makes no
provider privacy, retention, quality, or production-suitability claim.
