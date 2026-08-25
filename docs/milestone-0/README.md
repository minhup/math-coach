# Milestone 0 — Scope, governance, and evaluation contract

## Readiness

**Status: BLOCKED — DECISION REQUIRED**

Milestone 0 establishes the finite pilot scope, accountable governance, benchmark protocol, content controls, and measurable release contract for the Personalized Chuyên Toán Coach MVP. It exits only when every deliverable below is approved and no `DECISION REQUIRED` item remains open.

This document is the authoritative readiness summary. The detailed product architecture and milestone sequence remain in [`docs/MVP_IMPLEMENTATION_PLAN.md`](../MVP_IMPLEMENTATION_PLAN.md). Execution of this documentation change is recorded in [`docs/changes/2026-08-25-m0-scope-governance.md`](../changes/2026-08-25-m0-scope-governance.md).

## Exit-gate register

| Required deliverable | Record | Current status | Blocking reason |
|---|---|---|---|
| Supported exam list | [`PILOT_SCOPE.md`](../product/PILOT_SCOPE.md) | DECISION REQUIRED | No finite examination set, cycles, content owner, or approval is recorded |
| Pilot cohort definition | [`PILOT_SCOPE.md`](../product/PILOT_SCOPE.md) | DECISION REQUIRED | Grade/age, count, location, language, invitation, and consent applicability are unresolved |
| Supported-device matrix | [`PILOT_SCOPE.md`](../product/PILOT_SCOPE.md) | DECISION REQUIRED | Required devices, OS/browser versions, viewports, and capture/upload paths are unresolved |
| AI benchmark specification | [`AI_PROVIDER_BENCHMARK.md`](../evaluation/AI_PROVIDER_BENCHMARK.md) | DECISION REQUIRED | Candidates, dataset size, reviewers, thresholds, operations, and approval are unresolved |
| Privacy and consent action list | [`PRIVACY_AND_CONSENT_ACTION_LIST.md`](../privacy/PRIVACY_AND_CONSENT_ACTION_LIST.md) | DECISION REQUIRED | Qualified jurisdiction, consent, provider, retention, deletion, and security review is outstanding |
| Content provenance policy | [`CONTENT_PROVENANCE_POLICY.md`](../content/CONTENT_PROVENANCE_POLICY.md) | DECISION REQUIRED | Source/rights vocabulary, accountable owners, evidence system, and approval are unresolved |
| Release-quality gates | [`RELEASE_QUALITY_GATES.md`](../evaluation/RELEASE_QUALITY_GATES.md) | DECISION REQUIRED | Numeric thresholds, samples, owners, stop rules, and approval are unresolved |

## Decision notation

- `DECISION REQUIRED` means the repository does not establish the value and an implementation agent must not invent it.
- `APPROVED` must include a named accountable approver, date, decision, and durable evidence link.
- `NOT APPLICABLE` must include the qualified owner, rationale, scope, and approval date; it is not an empty field.
- A draft process does not make its gate complete.

## Established constraints

The following constraints already come from the approved MVP plan and remain binding while decisions are resolved:

- one study profile may contain multiple active target examinations;
- shared skill state is modeled once and target progress is derived;
- the application owns learner state and deterministic daily planning;
- typed content blocks are canonical; arbitrary AI Markdown and HTML are not;
- the confirmed transcript is the authoritative grading input;
- reference solutions are non-exhaustive and valid alternatives must be accepted;
- students edit mathematics visually without needing raw LaTeX;
- geometry is curated, versioned JSON and AI-generated executable code is forbidden;
- AI output is untrusted until strict schema validation succeeds;
- content must be versioned, reviewed, and supported by rights/provenance evidence;
- no native wrapper, direct pen input, voice conversation, public leaderboard, full admin product, general RAG, vector database, or predicted admission outcome is in the MVP.

## Work required to close Milestone 0

1. Assign named product, mathematics, evaluation, privacy/legal, security, content-rights, engineering, and pilot-operations owners.
2. Resolve and approve the finite examination set, cohort, language, device, and pilot-operation decisions.
3. Complete qualified privacy/legal review and link approved notices, policies, processor terms, retention, deletion/export, and incident evidence.
4. Approve the content source/rights vocabulary, evidence system, review roles, and withdrawal process.
5. Approve the benchmark candidates, corpus, protocol, adjudicators, data handling, thresholds, and selection authority.
6. Approve numeric release thresholds, evidence coverage, severity rules, pilot pause conditions, and go/no-go ownership.
7. Update each detailed record with names, dates, decisions, and evidence.
8. Review this index and change every gate to `APPROVED` only when its source record is complete.

## Milestone 1 boundary

Milestone 1 application work is not authorized by this documentation baseline. When all Milestone 0 gates are approved, start Milestone 1 in a new short-lived branch and a new ChangePlan. Milestone 1 must provide the Next.js and FastAPI foundations, PostgreSQL migrations, object storage, invite-only authentication, CI, logging, and root development commands, and must exit only when a pilot user can log in and upload a test image.

No application code, schema, migration, dependency, CI, infrastructure, or root command is part of the current Milestone 0 documentation change.

## Approval record

| Gate owner | Named approver | Decision | Date | Evidence link |
|---|---|---|---|---|
| Product scope | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Mathematics content | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Evaluation | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Privacy/legal | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Security | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Content rights | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |
| Pilot operations | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED | DECISION REQUIRED |

Milestone 0 final approval: DECISION REQUIRED.
