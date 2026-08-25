# Release-quality gates

## Status

- Milestone: 0 — Scope, governance, and evaluation contract
- Gate-set status: DRAFT — numeric and ownership decisions remain `DECISION REQUIRED`
- Release owner: DECISION REQUIRED
- Evaluation owner: DECISION REQUIRED
- Last updated: 2026-08-25

This document defines the evidence required to advance engineering milestones and begin or continue the closed pilot. It distinguishes requirements already fixed by the MVP plan from thresholds that accountable stakeholders must approve.

## Gate rule

A gate passes only when it has:

1. a stable metric and evaluation method;
2. an approved threshold;
3. a minimum sample size or coverage definition;
4. a named owner and approver;
5. versioned, reproducible evidence;
6. no unresolved critical failure or undocumented exception.

`DECISION REQUIRED` is a blocking state, not a provisional pass. An accepted exception must name its owner, rationale, scope, mitigation, expiry or review date, and rollback trigger.

## Milestone 0 exit gates

| Deliverable | Pass condition | Owner | Evidence | Status |
|---|---|---|---|---|
| Supported exam list | Finite non-empty set and applicable cycles approved with content ownership | DECISION REQUIRED | [`PILOT_SCOPE.md`](../product/PILOT_SCOPE.md) | DECISION REQUIRED |
| Pilot cohort | Grade/age, count, location, language, invitation, consent applicability, and operation criteria approved | DECISION REQUIRED | [`PILOT_SCOPE.md`](../product/PILOT_SCOPE.md) | DECISION REQUIRED |
| Supported-device matrix | Required phones/tablets, OS/browser versions, viewports, and camera/upload paths approved | DECISION REQUIRED | [`PILOT_SCOPE.md`](../product/PILOT_SCOPE.md) | DECISION REQUIRED |
| AI benchmark specification | Corpus, protocol, metrics, thresholds, reviewers, and selection authority approved | DECISION REQUIRED | [`AI_PROVIDER_BENCHMARK.md`](AI_PROVIDER_BENCHMARK.md) | DECISION REQUIRED |
| Privacy and consent action list | All blocking actions resolved or explicitly found not applicable by qualified reviewers | DECISION REQUIRED | [`PRIVACY_AND_CONSENT_ACTION_LIST.md`](../privacy/PRIVACY_AND_CONSENT_ACTION_LIST.md) | DECISION REQUIRED |
| Content provenance policy | Source/rights rules, owners, evidence system, publication, and withdrawal controls approved | DECISION REQUIRED | [`CONTENT_PROVENANCE_POLICY.md`](../content/CONTENT_PROVENANCE_POLICY.md) | DECISION REQUIRED |
| Release-quality gates | Thresholds, sample definitions, owners, stop conditions, and approval process approved | DECISION REQUIRED | This document | DECISION REQUIRED |

Milestone 1 is not authorized while any row remains unresolved.

## Requirements fixed by the MVP plan

These are pass/fail constraints and must not be weakened during threshold approval:

| Area | Fixed pass condition | Intended evidence milestone |
|---|---|---|
| Multi-exam model | A profile can have multiple active targets; no contract assumes exactly one | M2 and later contract, migration, component, and end-to-end tests |
| Immutable content | Attempts reference exact immutable content versions | M2 integration and migration tests |
| Invalid content | Invalid content cannot be imported | M2 content-schema tests |
| Raw TeX leakage | Zero raw-TeX leaks in the committed math regression suite | M3 math-render regression suite |
| Geometry safety | No executable AI geometry code; actions reference only existing curated IDs | M4 schema/action tests |
| Static student loop | Complete mocked journey works on every supported phone/tablet class | M5 browser tests and manual device report |
| AI output boundary | No unvalidated AI output reaches the UI; schema failure is retried at most once | M6/M7 contract and failure-path tests |
| Transcription authority | Only the student-confirmed transcript is graded | M6/M7 integration and end-to-end tests |
| Reference solutions | Correct alternatives are not rejected merely for differing from stored references | M7 gold evaluation regression |
| Failure integrity | No transcript, score, or hint is fabricated after provider failure | M6/M7 failure-path tests |
| Learner-state rebuild | Aggregate state rebuild from evidence is deterministic | M8 recomputation tests |
| Planner determinism | Identical inputs and configuration produce the same plan | M9 planner regression tests |
| Planner auditability | Every planned item records supported targets and an explainable selection reason | M9 contract and regression tests |
| Predicted outcomes | No predicted score or admission probability is shown without a separately approved calibrated model | Frontend/API tests through M10 |
| Pilot security/privacy | All approved security, privacy, consent, retention, deletion, and incident requirements pass | M11 checklist and tests |

## AI quality gates

The benchmark method is defined in [`AI_PROVIDER_BENCHMARK.md`](AI_PROVIDER_BENCHMARK.md). The following thresholds must be approved before the benchmark is used for selection or release.

| Gate | Metric and reporting | Threshold | Minimum evidence | Owner |
|---|---|---|---|---|
| Transcription schema validity | First-pass and post-single-retry valid rates | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Transcription correction burden | Correction completion, time, edit actions, text and math errors by stratum | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Silent mathematical correction | Critical-case rate and individual review | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Step segmentation | Agreement with adjudicated step boundaries | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Score agreement | Exact agreement and absolute rubric-score difference | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Root-error agreement | Agreement with adjudicated root error | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Dependent-error handling | Reviewed downstream over-penalization rate | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| False criticism | Valid-step false criticism rate, with severe cases listed | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Alternative-solution acceptance | Acceptance rate for adjudicated valid alternative methods | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Uncertainty routing | Safe uncertainty/manual-review behavior on ambiguous cases | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Feedback correctness | Expert-reviewed mathematical correctness and transcript support | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Hint quality | Correctness, usefulness, progressive disclosure, and harmful-hint rates | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Geometry-action validity | Schema-valid actions referencing approved scene IDs only | No invalid action may execute | DECISION REQUIRED | DECISION REQUIRED |
| Provider latency | Median and upper percentiles for transcription, grading, and hints | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Provider reliability | Timeouts and terminal provider-error rates | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Provider cost | Cost per operation, attempt, session, and approved pilot projection | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Provider data handling | All applicable privacy/security actions approved | No unresolved blocking action | Approved review evidence | DECISION REQUIRED |

Results must be reported by corpus stratum and supported examination, not only as aggregate averages.

## Device and workflow gates

| Gate | Metric | Threshold | Evidence | Owner |
|---|---|---|---|---|
| Invitation login | Successful login and safe failure/recovery on supported classes | DECISION REQUIRED | Browser tests and device report | DECISION REQUIRED |
| Camera and upload reliability | Capture/upload completion, retry recovery, and existing-photo fallback | DECISION REQUIRED | Browser tests, device report, pilot telemetry | DECISION REQUIRED |
| Math rendering | Render failures and raw-TeX leakage across the committed corpus | Zero raw-TeX leaks; other threshold DECISION REQUIRED | Math-render suite and device report | DECISION REQUIRED |
| Visual math correction | Task completion without requiring raw LaTeX | DECISION REQUIRED | Usability protocol and device report | DECISION REQUIRED |
| Geometry rendering | Determinism, constraint preservation, touch use, fallback, and accessibility | DECISION REQUIRED beyond fixed safety constraints | Geometry tests and device report | DECISION REQUIRED |
| Responsive journey | Complete static and provider-backed journey on every supported class | DECISION REQUIRED | End-to-end tests and manual QA | DECISION REQUIRED |
| Failure-state coverage | Loading, retryable, permanent, and uncertainty states are reachable and understandable | DECISION REQUIRED | Component/end-to-end tests and review | DECISION REQUIRED |
| Accessibility | Approved target and conformance protocol | DECISION REQUIRED | Automated and manual report | DECISION REQUIRED |

The exact supported classes are blocking decisions in [`PILOT_SCOPE.md`](../product/PILOT_SCOPE.md).

## Security, privacy, and content gates

| Gate | Pass condition | Evidence | Status |
|---|---|---|---|
| Authorization | Every user-owned resource and internal tool enforces approved access policy | Threat model, API/integration tests, review | DECISION REQUIRED |
| Image security | Approved file validation, signed URL, metadata removal, access, and deletion controls pass | Tests and storage review | DECISION REQUIRED |
| Secrets and provider keys | No client exposure or repository secrets; approved secret-management path works | CI scan and deployment review | DECISION REQUIRED |
| Retention, deletion, and export | Approved schedules and user workflows pass, including failure paths | Jobs/API tests and manual evidence | DECISION REQUIRED |
| Consent and notices | Approved versioned flows and withdrawal behavior work for the cohort | Legal/privacy approval and end-to-end evidence | DECISION REQUIRED |
| Auditability | Approved sensitive events are complete, access-controlled, and retained correctly | Contract/integration tests and review | DECISION REQUIRED |
| Incident readiness | Named response team has exercised the approved procedure | Exercise record | DECISION REQUIRED |
| Content provenance | Every released item has approved rights and provenance evidence | Content validation/report | DECISION REQUIRED |
| Content quality | Mathematics, schema, render, geometry, accessibility, rubric, and hint reviews pass | Content release report | DECISION REQUIRED |

## Closed-pilot outcome gates

Before Milestone 12 begins, approve metric definitions, evidence windows, minimum sample sizes, and decision rules for:

| Outcome | Threshold |
|---|---|
| Camera/upload reliability | DECISION REQUIRED |
| Transcription correction burden | DECISION REQUIRED |
| Math and geometry rendering failures | DECISION REQUIRED |
| AI latency and cost | DECISION REQUIRED |
| Root-error agreement | DECISION REQUIRED |
| False criticism of valid steps | DECISION REQUIRED |
| Alternative-solution acceptance | DECISION REQUIRED |
| Hint usefulness | DECISION REQUIRED |
| Session completion | DECISION REQUIRED |
| Retry and scheduled-review behavior | DECISION REQUIRED |
| Independent solving | DECISION REQUIRED |
| Unseen-test improvement | DECISION REQUIRED |
| Student preference versus a free-form general AI workflow | DECISION REQUIRED |

The go/no-go rule must assess whether the structured coaching system demonstrates clear value beyond a general chat workflow. It must not be replaced by predicted entrance scores or admission probability.

## Severity and stop policy

Severity definitions, allowed counts, escalation timing, and restart authority are DECISION REQUIRED. At minimum, the policy must explicitly address:

- student safety or privacy breach;
- unauthorized access or data disclosure;
- invalid consent or continued processing after withdrawal;
- fabricated transcript, score, hint, or success state;
- systematic rejection of valid alternative methods;
- silent correction of student errors;
- executable or invalid geometry behavior;
- data loss or inability to honor deletion;
- unsupported-device failure that prevents the core learning loop;
- content-rights dispute or material mathematical error.

## Approval record

| Role | Named approver | Decision | Date | Evidence link |
|---|---|---|---|---|
| Product | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Evaluation | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Mathematics content | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Engineering | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Security | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Privacy/legal | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Pilot operations | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |

Final release-gate approval: DECISION REQUIRED.
