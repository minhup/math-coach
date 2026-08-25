# Milestone 0 scope, governance, and evaluation contract

## Metadata

- Status: in-progress
- Owner: Codex implementation agent; stakeholder decision owners are `DECISION REQUIRED`
- Branch: `docs/m0-scope-governance`
- Base commit: `b8c884ef082e9966f3a14ae124720cbf4d7dbf42`
- Related milestone: Milestone 0 — Scope, governance, and evaluation contract
- Related issue/ticket: None
- Started: 2026-08-25
- Last updated: 2026-08-25

## Context

The repository contains the implementation plan and agent workflow documents but no application code, Milestone 0 decision records, active ChangePlans, or test tooling. The implementation plan prohibits agents from inventing the supported examination set, pilot cohort, provider benchmark outcome, legal conclusions, or release thresholds. Milestone 1 must not begin until every Milestone 0 exit item is resolved.

## Goal

Create the permanent Milestone 0 document set needed to collect, review, and approve the supported-exam scope, pilot definition, device support, AI benchmark, privacy and consent work, content provenance rules, and release-quality gates. Every unresolved stakeholder-owned value must be labeled `DECISION REQUIRED`.

## Non-goals

- Resolve decisions that require product, content, evaluation, privacy, or legal authority.
- Scaffold the Next.js or FastAPI applications.
- Add dependencies, CI, root development commands, schemas, migrations, infrastructure, or tests for application behavior.
- Select or integrate an AI provider.
- Declare the repository ready for Milestone 1 while blocking decisions remain.

## User-visible behavior

None. This change adds project governance and evaluation documentation only.

## Current-state findings

- `main` and `origin/main` both pointed to `b8c884ef082e9966f3a14ae124720cbf4d7dbf42` after `git fetch origin --prune`.
- The working tree was clean before the branch was created.
- The repository contained only `AGENTS.md`, `CODEX.md`, `PLANS.md`, `IMPLEMENTATION_HANDOVER_PROMPT.md`, and `docs/MVP_IMPLEMENTATION_PLAN.md`.
- No `docs/changes/` files, application directories, test suites, root `Makefile`, package manifests, schemas, migrations, or CI configuration existed.
- The MVP plan defines seven Milestone 0 deliverables and says the milestone exits only when none remain unresolved.
- The supported exam set, pilot cohort, device matrix, numeric release thresholds, decision owners, and legal/privacy conclusions cannot be inferred safely from the repository.
- No root validation command contract exists yet; that is a Milestone 1 deliverable.

## Design

Use a small set of permanent documents organized by accountable concern:

- a Milestone 0 index tracks the exit gates and links to evidence;
- a pilot-scope record owns supported exams, cohort, devices, and pilot criteria;
- evaluation documents define the provider benchmark and release gates;
- a privacy action list tracks required review without making legal claims;
- a content provenance policy defines the minimum publication controls.

Each unresolved field uses the exact marker `DECISION REQUIRED`. A document may define required process or evidence from the approved MVP plan without pretending that stakeholder approval has occurred. The index remains the authoritative Milestone 0 readiness summary.

Alternatives rejected:

- One large decision document would mix owners and make independent review difficult.
- Filling example exams or speculative thresholds would violate the implementation plan.
- Starting Milestone 1 scaffolding in the same branch would mix governance and engineering-foundation work.

## Multi-exam impact

This change establishes the decision record for the finite MVP-supported exam set while preserving the architectural rule that one study profile can contain zero, one, or many active targets. It does not change study profiles, exam targets, exam-specific progress, shared skill state, or daily-plan balancing in code. The documents prohibit treating any selected exam as an implicit singular or primary target.

## Files and components

Owned by this branch:

- `docs/changes/2026-08-25-m0-scope-governance.md` — execution record for this change.
- `docs/milestone-0/README.md` — milestone index and readiness status.
- `docs/product/PILOT_SCOPE.md` — supported exams, pilot cohort, device matrix, and pilot criteria.
- `docs/evaluation/AI_PROVIDER_BENCHMARK.md` — benchmark corpus, procedure, metrics, and selection record.
- `docs/evaluation/RELEASE_QUALITY_GATES.md` — release metrics, thresholds, evidence, and approval state.
- `docs/privacy/PRIVACY_AND_CONSENT_ACTION_LIST.md` — pre-pilot privacy and consent actions.
- `docs/content/CONTENT_PROVENANCE_POLICY.md` — content rights, provenance, review, and versioning controls.

No existing file is modified except this living ChangePlan after its creation.

## API and schema changes

None.

## Database and migration

None.

## Security and privacy

No student data, images, credentials, provider data, or runtime behavior are introduced. The privacy document will identify reviews and evidence required before collecting minors' data. Legal conclusions, retention periods, consent language, and accountable approvers remain `DECISION REQUIRED` unless already fixed by the approved MVP plan.

## Test plan

There is no application or documentation test framework. Validate the documentation with the available repository tools:

- confirm the expected files exist;
- confirm every Milestone 0 deliverable is represented in the index;
- search for `DECISION REQUIRED` markers and verify every unresolved choice is explicit;
- search for accidental placeholder claims such as an approved provider or supported exam example;
- verify relative Markdown links in the new documents resolve;
- run `git diff --check`;
- inspect the complete branch diff and final working-tree status.

Application unit, integration, API/schema, migration, frontend, browser, content-schema, AI evaluation, and device tests are not applicable because this change adds documentation only.

## Manual QA

1. Open `docs/milestone-0/README.md` and follow every link.
2. Confirm all seven Milestone 0 deliverables have a document section and readiness state.
3. Confirm unresolved product-owned values visibly say `DECISION REQUIRED`.
4. Confirm no document claims Milestone 0 is complete or authorizes Milestone 1.
5. Compare the documents with sections 3, 15, and 17 of `docs/MVP_IMPLEMENTATION_PLAN.md`.

Expected outcome: the complete decision surface is documented, no decision is fabricated, and stakeholders can see exactly what blocks Milestone 1.

## Rollout and rollback

These documents take effect when merged. There is no runtime rollout, data migration, or compatibility concern. Roll back by reverting the documentation commits. Stakeholder decisions should be added through later reviewed changes that update the relevant document and Milestone 0 index together.

## Branch and commit plan

1. `docs: add Milestone 0 change plan`
2. `docs: define pilot scope and governance controls`
3. `docs: specify AI benchmark and release gates`
4. `docs: record Milestone 0 verification`

## Conflict coordination

This branch owns only the seven new documentation files listed above. No active ChangePlans or implementation branches were visible in the fetched repository. Possible future overlap is highest in `docs/evaluation/` and `docs/privacy/`; stakeholder decisions should build on these contracts after this branch merges. Integration order: merge this Milestone 0 baseline before branches that resolve individual gates or begin Milestone 1.

## Risks

- Stakeholders may mistake a process specification for an approved decision. Mitigation: use explicit readiness states and `DECISION REQUIRED` markers.
- Numeric gates could be invented for convenience. Mitigation: define metric semantics now but leave thresholds unresolved.
- Legal or consent text could be treated as legal advice. Mitigation: maintain an action list and require named qualified approval.
- The benchmark could favor a provider through an unrepresentative dataset. Mitigation: define corpus strata, blinded review, and auditable per-case results.
- Content could be imported without sufficient rights evidence. Mitigation: make provenance and publication review mandatory before content import.
- Parallel work could create competing project contracts. Mitigation: declare owned paths and merge this baseline before dependent work.

## Progress

- [x] Repository inspected
- [x] Plan reviewed
- [x] Branch created from current main
- [ ] Tests written or updated — not applicable; documentation validation remains pending
- [ ] Implementation complete
- [ ] Documentation updated
- [ ] Relevant checks pass
- [ ] Diff reviewed
- [ ] Branch rebased on current main
- [ ] Conflict resolution re-tested
- [ ] Handoff summary written

## Decisions

- 2026-08-25: Keep Milestone 0 documentation separate from Milestone 1 application scaffolding so this branch remains one coherent governance change.
- 2026-08-25: Use `DECISION REQUIRED` for stakeholder-owned values that the repository does not establish.
- 2026-08-25: Organize permanent documents by accountable concern and use the milestone index as the readiness summary.

## Discoveries

- The repository is an initial documentation-only handover with no validation tooling.
- Every Milestone 0 exit gate is unresolved in the current repository.

## Verification evidence

Pending implementation and validation.

## Result

In progress.
