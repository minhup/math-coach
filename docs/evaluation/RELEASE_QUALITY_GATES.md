# Release-quality gates

## Status

- Milestone: 0 — Internal MVP direction and deferred-gate register
- Internal implementation: NOT BLOCKED
- External pilot gate set: DEFERRED — numeric and evidence decisions remain `DECISION REQUIRED`
- Decision authority: Project owner
- Last updated: 2026-08-25

This document defines the evidence required at later engineering and external-pilot gates. It does not block internal product iteration with deterministic mocks, synthetic/non-personal fixtures, or an internally selected development provider. It distinguishes requirements already fixed by the MVP plan from thresholds that the project owner must confirm when their named gate becomes relevant.

## Gate rule

A gate passes only when it has:

1. a stable metric and evaluation method;
2. an approved threshold;
3. a minimum sample size or coverage definition;
4. a dated project-owner decision;
5. versioned, reproducible evidence;
6. no unresolved critical failure or undocumented exception.

`DECISION REQUIRED` is a blocking state, not a provisional pass. An accepted exception must record the project owner's decision, rationale, scope, mitigation, expiry or review date, and rollback trigger.

## Stage-gate register

| Deliverable | Pass condition | Evidence | Required before | Status |
|---|---|---|---|---|
| Supported exam list | Finite non-empty set and applicable cycles confirmed with content review evidence | [`PILOT_SCOPE.md`](../product/PILOT_SCOPE.md) | Real exam content import/publication in Milestone 2 | DEFERRED |
| Pilot cohort | Grade/age, count, location, language, invitation, consent applicability, and operation criteria confirmed | [`PILOT_SCOPE.md`](../product/PILOT_SCOPE.md) | External pilot in Milestone 12 | DEFERRED |
| Internal development-device matrix | Browser emulation targets and limitations confirmed | [`PILOT_SCOPE.md`](../product/PILOT_SCOPE.md) | Milestone 1 | APPROVED |
| AI benchmark specification | Corpus, protocol, metrics, thresholds, reviewers, and production selection method confirmed | [`AI_PROVIDER_BENCHMARK.md`](AI_PROVIDER_BENCHMARK.md) | Real participant data or external pilot | DEFERRED |
| Privacy and consent action list | All pre-pilot actions resolved or explicitly found not applicable using qualified review evidence | [`PRIVACY_AND_CONSENT_ACTION_LIST.md`](../privacy/PRIVACY_AND_CONSENT_ACTION_LIST.md) | Real minors' data or external pilot | DEFERRED |
| Content provenance policy | Source/rights rules, evidence system, publication, and withdrawal controls confirmed | [`CONTENT_PROVENANCE_POLICY.md`](../content/CONTENT_PROVENANCE_POLICY.md) | Real third-party content import/publication | DEFERRED |
| Release-quality gates | Thresholds, sample definitions, stop conditions, evidence, and confirmation process approved | This document | External pilot in Milestone 12 | DEFERRED |

Milestone 1 is authorized with synthetic/non-personal fixtures and a deterministic fake provider. Later internal provider-adapter trials may also use synthetic/non-personal inputs before the pre-pilot benchmark is confirmed. A deferred row blocks only the stage named in its `Required before` column.

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

The benchmark method is defined in [`AI_PROVIDER_BENCHMARK.md`](AI_PROVIDER_BENCHMARK.md). The following thresholds must be confirmed before production-provider commitment or the external pilot; they do not block mocked interaction development or internal provider experiments using synthetic/non-personal inputs.

| Gate | Metric and reporting | Threshold | Minimum evidence |
|---|---|---|---|
| Transcription schema validity | First-pass and post-single-retry valid rates | DECISION REQUIRED | DECISION REQUIRED |
| Transcription correction burden | Correction completion, time, edit actions, text and math errors by stratum | DECISION REQUIRED | DECISION REQUIRED |
| Silent mathematical correction | Critical-case rate and individual review | DECISION REQUIRED | DECISION REQUIRED |
| Step segmentation | Agreement with adjudicated step boundaries | DECISION REQUIRED | DECISION REQUIRED |
| Score agreement | Exact agreement and absolute rubric-score difference | DECISION REQUIRED | DECISION REQUIRED |
| Root-error agreement | Agreement with adjudicated root error | DECISION REQUIRED | DECISION REQUIRED |
| Dependent-error handling | Reviewed downstream over-penalization rate | DECISION REQUIRED | DECISION REQUIRED |
| False criticism | Valid-step false criticism rate, with severe cases listed | DECISION REQUIRED | DECISION REQUIRED |
| Alternative-solution acceptance | Acceptance rate for adjudicated valid alternative methods | DECISION REQUIRED | DECISION REQUIRED |
| Uncertainty routing | Safe uncertainty/manual-review behavior on ambiguous cases | DECISION REQUIRED | DECISION REQUIRED |
| Feedback correctness | Expert-reviewed mathematical correctness and transcript support | DECISION REQUIRED | DECISION REQUIRED |
| Hint quality | Correctness, usefulness, progressive disclosure, and harmful-hint rates | DECISION REQUIRED | DECISION REQUIRED |
| Geometry-action validity | Schema-valid actions referencing approved scene IDs only | No invalid action may execute | DECISION REQUIRED |
| Provider latency | Median and upper percentiles for transcription, grading, and hints | DECISION REQUIRED | DECISION REQUIRED |
| Provider reliability | Timeouts and terminal provider-error rates | DECISION REQUIRED | DECISION REQUIRED |
| Provider cost | Cost per operation, attempt, session, and approved pilot projection | DECISION REQUIRED | DECISION REQUIRED |
| Provider data handling | All applicable privacy/security actions approved | No unresolved pre-pilot action | Approved review evidence |

Results must be reported by corpus stratum and supported examination, not only as aggregate averages.

## Device and workflow gates

| Gate | Metric | Threshold | Evidence |
|---|---|---|---|
| Invitation login | Successful login and safe failure/recovery on supported classes | DECISION REQUIRED | Browser tests and device report |
| Camera and upload reliability | Capture/upload completion, retry recovery, and existing-photo fallback | DECISION REQUIRED | Browser tests, device report, pilot telemetry |
| Math rendering | Render failures and raw-TeX leakage across the committed corpus | Zero raw-TeX leaks; other threshold DECISION REQUIRED | Math-render suite and device report |
| Visual math correction | Task completion without requiring raw LaTeX | DECISION REQUIRED | Usability protocol and device report |
| Geometry rendering | Determinism, constraint preservation, touch use, fallback, and accessibility | DECISION REQUIRED beyond fixed safety constraints | Geometry tests and device report |
| Responsive journey | Complete static and provider-backed journey on every supported class | DECISION REQUIRED | End-to-end tests and manual QA |
| Failure-state coverage | Loading, retryable, permanent, and uncertainty states are reachable and understandable | DECISION REQUIRED | Component/end-to-end tests and review |
| Accessibility | Approved target and conformance protocol | DECISION REQUIRED | Automated and manual report |

The internal browser-emulation classes are approved in [`PILOT_SCOPE.md`](../product/PILOT_SCOPE.md). Exact later emulator, simulator, and physical-device targets are selected before their named pre-pilot gates.

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

Severity definitions, allowed counts, and escalation timing are DECISION REQUIRED. Restart authority remains with the project owner. At minimum, the policy must explicitly address:

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

## External-pilot confirmation

| Decision | Date | Evidence link | Exceptions or review date |
|---|---|---|---|
| DEFERRED | DECISION REQUIRED | DECISION REQUIRED | Revisit before Milestone 12 |

External-pilot quality-gate confirmation: DEFERRED.
