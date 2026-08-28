# Milestone 7 evaluation and hints device report

- Date: 2026-08-28
- Data: repository-owned synthetic image and transcript only
- Provider: deterministic production-shaped fake; no network or paid provider call

## Matrix and journey

The production build runs the same authenticated upload-to-hints journey in all five configured
projects:

| Project                      | Engine / viewport                | Result |
| ---------------------------- | -------------------------------- | ------ |
| compact-chromium             | Chromium, 360×640 touch          | pass   |
| pixel-7-chromium             | Chromium, Pixel 7 device profile | pass   |
| iphone-13-webkit             | WebKit, iPhone 13 device profile | pass   |
| ipad-pro-11-portrait-webkit  | WebKit, iPad Pro 11 portrait     | pass   |
| ipad-pro-11-landscape-webkit | WebKit, iPad Pro 11 landscape    | pass   |

The journey uploads the synthetic M6 image, reviews the flat transcript, visually corrects the
formula, explicitly confirms the exact version, and only then requests M7 evaluation. The synthetic
confirmed mistake produces a 0.00/4.00 result with root and dependent errors, an earlier-step link,
rubric breakdown, typed feedback, and no raw provider content. It then releases hints 1 and 2 in
server order and exercises the stored highlight/show/ask-select geometry actions before retry and
concept review.

The automated layout audit reports no document horizontal overflow and no tested core surface
escaping the viewport. `VISUAL_QA=1 make test-e2e` passed all 15 browser cases. The five ready-result
and five progressive-hint screenshots were inspected at original resolution; score, dependency,
rubric, hint, geometry, selection, and next-level controls were visible without clipping or
horizontal overflow.

## Screenshot evidence

The screenshots are generated review artifacts under ignored `test-results/`; hashes make the exact
inspected output identifiable without committing browser artifacts.

| Project                      | Ready evaluation SHA-256                                           | Hints SHA-256                                                      |
| ---------------------------- | ------------------------------------------------------------------ | ------------------------------------------------------------------ |
| compact-chromium             | `55651a9b9782dc59c907974fa2d607d7c9b2f3eaabb56a19dd490dff3acdedaf` | `96163065392184a8225926b3e8a48fa2b30549d76d8e2fc1c8a13a5fe36c2b8f` |
| pixel-7-chromium             | `4c8413ba00e4dcf12acebde1210f3aed349d6ba00fcc2328b1341e9f7501fbb8` | `09c38f1acdab491f400845c9bf2f64f3a8560fc41cf37022a3000151df3f3224` |
| iphone-13-webkit             | `e5e3dca913833ace00464d06ef7d88dd4a269ecec047c8dc3c405cc0accff821` | `cc56cc6f6509066390e5758e9b4b769486812ce508761e51d65c3d5675b54fba` |
| ipad-pro-11-portrait-webkit  | `3a475e82227287152687509016b4fee9e600fa56a039e8b19f389bcc69568b9c` | `5a879506347b345ef693e3aacbed79559b46c5371172a5f461a7ab18a6612e4e` |
| ipad-pro-11-landscape-webkit | `faadf28199ce9269252dbf052ddf90a39204dc1959e0ca5f9d8df16c8183f8f7` | `973191030a1d5117223ce7de30fa9732dff074325fadf4b1fa42fb2974419b5c` |

## Limitations

This is emulator-style Playwright coverage, not physical-device or true iOS/iPadOS Simulator QA.
The data and provider are deterministic synthetic fixtures. The report establishes responsive
workflow behavior and typed rendering, not production grading quality or provider calibration.
