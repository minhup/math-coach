# Pilot scope and supported examinations

## Status

- Milestone: 0 — Internal MVP direction and deferred-gate register
- Internal device readiness: APPROVED
- External pilot scope: DEFERRED — `DECISION REQUIRED` items remain
- Decision authority: Project owner
- Specialist evidence: mathematics-content and privacy/legal review where applicable
- Last updated: 2026-08-25

This document is the decision record for the finite MVP release scope. It does not broaden the architecture beyond the boundaries in [`docs/MVP_IMPLEMENTATION_PLAN.md`](../MVP_IMPLEMENTATION_PLAN.md).

## Product invariants

- One student has one study profile for a preparation cycle.
- A study profile may contain zero, one, or many active target examinations.
- The supported-exam list is finite for the pilot, but a student may select any permitted subset of it.
- No exam is implicitly primary. User priority rank and exam date inform planning.
- Shared mathematical skill state is stored once. Exam-specific progress is derived from shared skill state and approved exam-specific configuration.
- A target score is a student goal, not a predicted score or admission probability.

## Supported examination set

**Decision:** DEFERRED until real exam content is imported or published in Milestone 2

Do not copy the example examination codes from the MVP plan into implementation. The project owner must confirm a finite, non-empty list after checking the examination details, available content, and rights evidence.

Record each approved examination using this table:

| Field | Required value |
|---|---|
| Stable exam code | DECISION REQUIRED |
| Official display name | DECISION REQUIRED |
| Region or administering body | DECISION REQUIRED |
| Eligible student grade(s) | DECISION REQUIRED |
| Supported exam cycle or year | DECISION REQUIRED |
| Maximum score and scoring basis | DECISION REQUIRED |
| Content coverage available for the pilot | DECISION REQUIRED |
| Mathematics-content review evidence | DECISION REQUIRED |
| Approval evidence and date | DECISION REQUIRED |

The approved list must answer:

- whether several cycles of the same examination are supported;
- how changed formats or scoring systems are versioned;
- which exam-specific skill weights and relevance links are available;
- whether a target can remain selectable when its content coverage is incomplete;
- how an examination is retired without changing historical attempts.

## Pilot cohort

**Decision timing:** DEFERRED until preparation for an external pilot. These values do not block internal implementation with synthetic/non-personal fixtures.

| Decision | Project-owner decision | Evidence or rationale |
|---|---|---|
| Student grade range | DECISION REQUIRED | DECISION REQUIRED |
| Student age range | DECISION REQUIRED | DECISION REQUIRED |
| Number of invited students | DECISION REQUIRED | DECISION REQUIRED |
| Geographic location | DECISION REQUIRED | DECISION REQUIRED |
| Supported interface language | DECISION REQUIRED | DECISION REQUIRED |
| Supported mathematical response language(s) | DECISION REQUIRED | DECISION REQUIRED |
| Parent/guardian consent requirement | DECISION REQUIRED following qualified review | DECISION REQUIRED |
| Student assent requirement | DECISION REQUIRED following qualified review | DECISION REQUIRED |
| Recruitment channel | DECISION REQUIRED | DECISION REQUIRED |
| Account invitation and identity-verification process | DECISION REQUIRED | DECISION REQUIRED |
| Pilot support contact and hours | DECISION REQUIRED | DECISION REQUIRED |

No participant may be invited until the applicable privacy and consent actions in [`PRIVACY_AND_CONSENT_ACTION_LIST.md`](../privacy/PRIVACY_AND_CONSENT_ACTION_LIST.md) are approved.

## Supported-device matrix

The MVP supports phones and tablets through a responsive PWA. The project owner approved this emulator-first internal development matrix:

| Coverage | Tool and browser | Viewport or descriptor | Orientation | Required stage | Status |
|---|---|---|---|---|---|
| Compact phone boundary | Playwright Chromium | Custom `360 × 640` CSS viewport with touch | Portrait; targeted landscape checks | Milestones 1–5 | APPROVED |
| Android phone | Playwright Chromium | `Pixel 7` device descriptor | Portrait and landscape | Milestones 1–5 | APPROVED |
| iPhone browser behavior | Playwright WebKit | `iPhone 13` device descriptor | Portrait and landscape | Milestones 1–5 | APPROVED |
| Tablet browser behavior | Playwright WebKit | `iPad Pro 11` device descriptor | Portrait and landscape | Milestones 1–5 | APPROVED |
| Android camera/permission behavior | Android Emulator with a stable phone AVD and Chrome | Exact API image selected when installed | Portrait and landscape | Before Milestone 11 exits | DEFERRED |
| True iOS/iPadOS simulator behavior | Xcode Simulator on macOS | Supported iPhone and iPad simulator selected when available | Portrait and landscape | Before external pilot | DEFERRED — current environment is Linux |
| Physical hardware | At least one representative phone; tablet based on pilot availability | Exact devices selected with the cohort | Relevant orientations | Before external pilot | DEFERRED |

Playwright emulation is the default automated development path. It covers viewport, user agent, touch, and browser-engine behavior, but it is not a complete hardware simulator. Existing-photo upload can be automated with synthetic fixtures. Camera permission and capture behavior require Android Emulator, Xcode Simulator on macOS, or later physical-device checks.

At the Milestone 0 decision date, the current Linux environment has none of these tools installed. Milestone 1 must install Playwright and its browser dependencies through the documented root setup command. Android Emulator installation may wait until camera-specific validation is needed. Apple Simulator cannot run on this Linux environment.

Tool references:

- [Playwright device emulation](https://playwright.dev/docs/emulation)
- [Android Emulator](https://developer.android.com/studio/run/emulator-commandline)
- [Apple simulated and physical devices](https://developer.apple.com/documentation/Xcode/running-your-app-on-simulated-or-physical-devices)

For every approved internal browser-emulation class, automated or manual checks must cover:

- invitation login;
- portrait and landscape layouts where applicable;
- mathematical rendering and visual editing;
- touch interaction with curated geometry;
- photo preview, replacement, upload, retry, and existing-photo fallback using synthetic file fixtures;
- transcript correction without raw-LaTeX input;
- loading, retryable failure, permanent failure, and uncertainty states;
- accessibility descriptions and geometry fallback images.

Camera permission, direct capture, and hardware-specific behavior are checked when the Android Emulator, Apple Simulator, or physical-device stages become due. They do not block the browser-emulated interaction loop.

Native wrappers, direct pen input, and full offline behavior remain outside the MVP. Lack of a physical tablet does not block internal implementation.

## Pilot start criteria

This section is intentionally deferred and does not block Milestone 1.

The pilot may start only after all of the following are true:

- supported examination set is approved;
- cohort and supported-device matrix are approved;
- privacy, consent, provider-processing, retention, deletion, and incident actions are approved;
- content rights and provenance evidence exists for every released item;
- AI benchmark and release-quality gates have the approvals required by the pre-pilot stage-gate register;
- Milestones 1–11 meet their documented exit criteria;
- the project owner confirms the release record.

Additional start criteria: DECISION REQUIRED.

## Pilot completion and stop criteria

This section is intentionally deferred and does not block internal implementation.

| Decision | Approved value |
|---|---|
| Planned pilot start date or triggering condition | DECISION REQUIRED |
| Planned pilot end date or sample-completion condition | DECISION REQUIRED |
| Minimum participation needed for evaluation | DECISION REQUIRED |
| Safety or privacy condition requiring immediate pause | DECISION REQUIRED |
| Reliability condition requiring pause | DECISION REQUIRED |
| AI quality condition requiring pause | DECISION REQUIRED |
| Content issue requiring pause or withdrawal | DECISION REQUIRED |
| Authority to pause or stop the pilot | Project owner |

## Go/no-go decision

The closed pilot must measure the outcomes listed in Milestone 12, including upload reliability, correction burden, rendering failures, AI quality, latency, cost, alternative-solution acceptance, hint usefulness, learning behavior, and preference versus a free-form general AI workflow.

- Decision framework: [`RELEASE_QUALITY_GATES.md`](../evaluation/RELEASE_QUALITY_GATES.md)
- Go/no-go decision authority: Project owner
- Required evidence window and sample size: DECISION REQUIRED
- Approval record location: DECISION REQUIRED

## Project-owner confirmation

| Decision | Date | Evidence link | Notes or limitations |
|---|---|---|---|
| Emulator-first internal device matrix approved | 2026-08-25 | This document | True iOS/iPadOS simulation requires macOS/Xcode; physical checks are pre-pilot |
| Supported exams and external pilot cohort | DECISION REQUIRED | DECISION REQUIRED | Deferred to their named gates |

Internal implementation is unblocked. External pilot readiness remains blocked until the deferred scope, evidence, and pre-pilot checks are confirmed.
