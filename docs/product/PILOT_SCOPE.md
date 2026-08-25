# Pilot scope and supported examinations

## Status

- Milestone: 0 — Scope, governance, and evaluation contract
- Readiness: BLOCKED — `DECISION REQUIRED` items remain
- Decision owner: DECISION REQUIRED
- Required approvers: product, mathematics content, pilot operations, and privacy/legal owners — named people are DECISION REQUIRED
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

**Decision:** DECISION REQUIRED

Do not copy the example examination codes from the MVP plan into implementation. Product and mathematics-content owners must approve a finite, non-empty list before Milestone 0 can exit.

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
| Mathematics-content owner | DECISION REQUIRED |
| Approval evidence and date | DECISION REQUIRED |

The approved list must answer:

- whether several cycles of the same examination are supported;
- how changed formats or scoring systems are versioned;
- which exam-specific skill weights and relevance links are available;
- whether a target can remain selectable when its content coverage is incomplete;
- how an examination is retired without changing historical attempts.

## Pilot cohort

| Decision | Approved value | Owner | Evidence |
|---|---|---|---|
| Student grade range | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Student age range | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Number of invited students | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Geographic location | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Supported interface language | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Supported mathematical response language(s) | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Parent/guardian consent requirement | DECISION REQUIRED following qualified review | DECISION REQUIRED | DECISION REQUIRED |
| Student assent requirement | DECISION REQUIRED following qualified review | DECISION REQUIRED | DECISION REQUIRED |
| Recruitment channel | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Account invitation and identity-verification process | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Pilot support contact and hours | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |

No participant may be invited until the applicable privacy and consent actions in [`PRIVACY_AND_CONSENT_ACTION_LIST.md`](../privacy/PRIVACY_AND_CONSENT_ACTION_LIST.md) are approved.

## Supported-device matrix

The MVP must support phones and tablets through a responsive PWA. Exact devices and browser versions require pilot-owner approval.

| Coverage class | Device and OS | Browser and minimum version | Viewport or orientation | Camera capture | Existing-photo upload | Approval status |
|---|---|---|---|---|---|---|
| Smallest supported phone | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Representative Android phone | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Representative iOS phone | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Representative Android tablet, if supported | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Representative iPad, if supported | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |

For every supported class, the device report must cover:

- invitation login;
- portrait and landscape layouts where applicable;
- mathematical rendering and visual editing;
- touch interaction with curated geometry;
- camera permission denial and recovery;
- photo capture, preview, replacement, upload, retry, and existing-photo fallback;
- transcript correction without raw-LaTeX input;
- loading, retryable failure, permanent failure, and uncertainty states;
- accessibility descriptions and geometry fallback images.

Native wrappers, direct pen input, and full offline behavior remain outside the MVP.

## Pilot start criteria

The pilot may start only after all of the following are true:

- supported examination set is approved;
- cohort and supported-device matrix are approved;
- privacy, consent, provider-processing, retention, deletion, and incident actions are approved;
- content rights and provenance evidence exists for every released item;
- AI benchmark and release-quality gates have the approvals required by Milestone 0;
- Milestones 1–11 meet their documented exit criteria;
- pilot operations owner signs the release record.

Additional start criteria: DECISION REQUIRED.

## Pilot completion and stop criteria

| Decision | Approved value |
|---|---|
| Planned pilot start date or triggering condition | DECISION REQUIRED |
| Planned pilot end date or sample-completion condition | DECISION REQUIRED |
| Minimum participation needed for evaluation | DECISION REQUIRED |
| Safety or privacy condition requiring immediate pause | DECISION REQUIRED |
| Reliability condition requiring pause | DECISION REQUIRED |
| AI quality condition requiring pause | DECISION REQUIRED |
| Content issue requiring pause or withdrawal | DECISION REQUIRED |
| Authority to pause or stop the pilot | DECISION REQUIRED |

## Go/no-go decision

The closed pilot must measure the outcomes listed in Milestone 12, including upload reliability, correction burden, rendering failures, AI quality, latency, cost, alternative-solution acceptance, hint usefulness, learning behavior, and preference versus a free-form general AI workflow.

- Decision framework: [`RELEASE_QUALITY_GATES.md`](../evaluation/RELEASE_QUALITY_GATES.md)
- Go/no-go decision owner: DECISION REQUIRED
- Required evidence window and sample size: DECISION REQUIRED
- Approval record location: DECISION REQUIRED

## Approval record

| Role | Named approver | Decision | Date | Evidence link |
|---|---|---|---|---|
| Product | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Mathematics content | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Pilot operations | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Privacy/legal | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |

Milestone 0 remains blocked until every required decision in this document is approved and the milestone index is updated.
