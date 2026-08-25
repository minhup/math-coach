# Milestone 0 — Internal MVP direction and deferred-gate register

## Readiness

**Internal implementation: APPROVED**

**External pilot: NOT APPROVED — deferred decisions remain**

Milestone 0 establishes the internal product direction, decision timing, development-device matrix, and future gate register for the Personalized Chuyên Toán Coach MVP. It is complete for starting internal implementation. Items needed only for real exam content, production AI, external participants, or release remain visible without blocking Milestone 1.

For the MVP, the project owner is the sole decision authority. Multi-role governance is deferred until product-release preparation. Qualified specialist review may still be required as evidence for legal, privacy, rights, security, or mathematical claims.

This document is the authoritative readiness summary. The detailed product architecture and milestone sequence remain in [`docs/MVP_IMPLEMENTATION_PLAN.md`](../MVP_IMPLEMENTATION_PLAN.md). Execution of this documentation change is recorded in [`docs/changes/2026-08-25-m0-scope-governance.md`](../changes/2026-08-25-m0-scope-governance.md).

## Immediate product focus

The MVP's first value test is the quality of the human–AI learning interaction:

```text
paper solution photo
        ↓
clear processing/recovery state
        ↓
visual transcript correction
        ↓
student confirmation
        ↓
step feedback and uncertainty
        ↓
progressive hint or retry
```

Milestones 1–5 should make this loop feel clear, fast, trustworthy, and useful with deterministic mocks before real-provider integration.

## Exit-gate register

| Deliverable | Record | Current status | Required before |
|---|---|---|---|
| Supported exam list | [`PILOT_SCOPE.md`](../product/PILOT_SCOPE.md) | DEFERRED | Importing or publishing real exam content in Milestone 2 |
| Pilot cohort definition | [`PILOT_SCOPE.md`](../product/PILOT_SCOPE.md) | DEFERRED | Inviting external participants in Milestone 12 |
| Internal development-device matrix | [`PILOT_SCOPE.md`](../product/PILOT_SCOPE.md) | APPROVED | Milestone 1 implementation |
| AI benchmark specification | [`AI_PROVIDER_BENCHMARK.md`](../evaluation/AI_PROVIDER_BENCHMARK.md) | DRAFTED; execution deferred | Real-provider integration in Milestone 6 |
| Privacy and consent action list | [`PRIVACY_AND_CONSENT_ACTION_LIST.md`](../privacy/PRIVACY_AND_CONSENT_ACTION_LIST.md) | DEFERRED | Collecting real minors' data or starting an external pilot |
| Content provenance policy | [`CONTENT_PROVENANCE_POLICY.md`](../content/CONTENT_PROVENANCE_POLICY.md) | BASELINE DRAFTED | Importing or publishing real third-party content |
| Release-quality gates | [`RELEASE_QUALITY_GATES.md`](../evaluation/RELEASE_QUALITY_GATES.md) | FRAMEWORK DRAFTED | Starting an external pilot |

## Decision notation

- `DECISION REQUIRED` means the repository does not establish the value and an implementation agent must not invent it.
- `DEFERRED` means the value is not needed for internal implementation and names the milestone or external action it blocks.
- `APPROVED` means the project owner recorded the decision, date, rationale, and durable evidence link.
- `NOT APPLICABLE` means the project owner recorded the rationale, scope, evidence, and decision date; it is not an empty field.
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

## Milestone 0 internal-build decision

- Product focus: human–AI interaction UI/UX
- Decision authority: project owner
- Test data: synthetic or non-personal fixtures only
- AI during internal slice: deterministic fake provider
- Device strategy: Playwright browser emulation first; Android Emulator later; iOS/iPadOS Simulator when macOS/Xcode is available
- Decision date: 2026-08-25
- Decision: APPROVED FOR INTERNAL IMPLEMENTATION

## Deferred work

Before each listed gate becomes relevant, replace its remaining `DECISION REQUIRED` entries with the project owner's dated decision and supporting evidence. Privacy/legal and content-rights evidence remains mandatory before external participant data or third-party content is used.

## Milestone 1 boundary

Milestone 1 application work is authorized after this documentation branch is reviewed and merged. Start it in a new short-lived branch and a new ChangePlan. Milestone 1 must provide the Next.js and FastAPI foundations, PostgreSQL migrations, object storage, invite-only authentication, CI, logging, root development commands, and a responsive interaction shell. It exits when an internal test user can log in and upload a synthetic or non-personal test image in the development-device matrix.

No application code, schema, migration, dependency, CI, infrastructure, or root command is part of the current Milestone 0 documentation change.

## Project-owner confirmation

| Decision | Date | Evidence link | Notes or review date |
|---|---|---|---|
| Internal implementation may begin with deferred pre-pilot gates | 2026-08-25 | [`ChangePlan`](../changes/2026-08-25-m0-scope-governance.md) | Revisit each deferred item at its named gate |

Milestone 0 internal-build confirmation: APPROVED.
