# Milestone 0 scope, governance, and evaluation contract

## Metadata

- Status: ready-for-review
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
- [x] Tests written or updated — not applicable; this is a documentation-only change with no test framework
- [x] Implementation complete
- [x] Documentation updated
- [x] Relevant checks pass
- [x] Diff reviewed
- [x] Branch rebased on current main
- [x] Conflict resolution re-tested — not applicable; the rebase was already current and produced no conflicts
- [x] Handoff summary written

## Decisions

- 2026-08-25: Keep Milestone 0 documentation separate from Milestone 1 application scaffolding so this branch remains one coherent governance change.
- 2026-08-25: Use `DECISION REQUIRED` for stakeholder-owned values that the repository does not establish.
- 2026-08-25: Organize permanent documents by accountable concern and use the milestone index as the readiness summary.

## Discoveries

- The repository is an initial documentation-only handover with no validation tooling.
- Every Milestone 0 exit gate is unresolved in the current repository.
- No application test suite, documentation linter, root `Makefile`, or root command contract exists yet; the root command contract belongs to Milestone 1.
- The seven documents contain 23 relative Markdown file links, all of which resolve.
- Refreshing `origin/main` before handoff did not introduce new commits or conflicts.
- The first post-commit combined validation incorrectly included this ChangePlan in the example-exam search. It failed because the recorded command itself quoted those identifiers. The search was corrected to cover the six permanent decision documents; none contained either example.

## Verification evidence

- `git fetch origin --prune` — succeeded before branch creation and again before handoff.
- `git rebase origin/main` — reported `Current branch docs/m0-scope-governance is up to date.`; no conflicts occurred.
- `git diff --check origin/main...HEAD` — passed with no output before the final ChangePlan update.
- Expected-file and decision-marker assertions:

  ```bash
  expected_files=(
    docs/changes/2026-08-25-m0-scope-governance.md
    docs/milestone-0/README.md
    docs/product/PILOT_SCOPE.md
    docs/evaluation/AI_PROVIDER_BENCHMARK.md
    docs/evaluation/RELEASE_QUALITY_GATES.md
    docs/privacy/PRIVACY_AND_CONSENT_ACTION_LIST.md
    docs/content/CONTENT_PROVENANCE_POLICY.md
  )
  decision_documents=("${expected_files[@]:1}")
  for expected_file in "${expected_files[@]}"; do
    test -f "$expected_file"
  done
  test "$(rg -l 'DECISION REQUIRED' "${expected_files[@]}" | wc -l)" -eq 7
  test "$(rg -n '^\| (Supported exam list|Pilot cohort definition|Supported-device matrix|AI benchmark specification|Privacy and consent action list|Content provenance policy|Release-quality gates) \|' docs/milestone-0/README.md | wc -l)" -eq 7
  if rg -n 'PTNK|HCMC_Specialized' "${decision_documents[@]}"; then
    exit 1
  fi
  ```

  The first post-commit run failed only because the example-exam search included this ChangePlan's copy of the command. After correcting the scope to `decision_documents`, the result was seven expected files, seven files with explicit decision markers, seven indexed exit-gate rows, and zero copied example exam identifiers in the permanent decision documents.

- Relative-link validation extracted every local `.md` link with `rg`, resolved it from the source document's directory, and asserted the target exists. Result: 23 links checked; all passed.
- `sed -n '1,$p'` was run across all seven new documents for manual review against sections 3, 15, and 17 of the MVP plan.
- `git diff --name-status origin/main...HEAD` and `git diff --stat origin/main...HEAD` — reviewed seven added documentation files totaling 1,034 lines before the final ChangePlan update; no application, schema, migration, dependency, CI, infrastructure, or root-command file was changed.
- No application tests or root `make` commands were run because neither exists and this change introduces no application behavior.

## Result

Created a documentation-only Milestone 0 baseline covering all seven required deliverables. The documents define the required records, evidence, controls, metrics, and approval process while marking every unsupported product or stakeholder choice as `DECISION REQUIRED`. Milestone 0 remains blocked and Milestone 1 is not authorized until the named owners resolve and approve those decisions.
