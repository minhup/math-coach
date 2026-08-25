# Milestone 0 scope, governance, and evaluation contract

## Metadata

- Status: ready-for-review
- Owner: Project owner; implementation support by Codex
- Branch: `docs/m0-scope-governance`
- Base commit: `b8c884ef082e9966f3a14ae124720cbf4d7dbf42`
- Related milestone: Milestone 0 — Internal MVP direction and deferred-gate register
- Related issue/ticket: None
- Started: 2026-08-25
- Last updated: 2026-08-25

## Context

The repository contains the implementation plan and agent workflow documents but no application code, Milestone 0 decision records, active ChangePlans, or test tooling. The implementation plan prohibits agents from inventing the supported examination set, pilot cohort, provider benchmark outcome, legal conclusions, or release thresholds. During review, the project owner established that all MVP product decisions are made by the project owner and that internal engineering should prioritize the human–AI interaction experience. Multi-role governance and external-pilot validation must not block building the internal MVP, although required safeguards still apply before real minors or their data enter the system.

## Goal

Create the permanent Milestone 0 decision records, center the immediate roadmap on the paper-photo-to-feedback human–AI interaction loop, and distinguish internal-build decisions from pre-pilot and release gates. Use the project owner as the sole MVP decision authority. Adopt a practical emulator-first phone/tablet test matrix that does not require owning a tablet.

## Non-goals

- Resolve decisions that require product, content, evaluation, privacy, or legal authority.
- Scaffold the Next.js or FastAPI applications.
- Add dependencies, CI, root development commands, schemas, migrations, infrastructure, or tests for application behavior.
- Select or integrate an AI provider.
- Declare an external pilot ready while pre-pilot decisions remain.
- Define multi-role product governance for a later public release.
- Treat the project owner's decision authority as a substitute for qualified legal, privacy, rights, security, or mathematics evidence where that evidence is required.
- Make external-pilot privacy, content-rights, or release validation block internal UI/UX implementation.

## User-visible behavior

None. This change adds project governance and evaluation documentation only.

## Current-state findings

- `main` and `origin/main` both pointed to `b8c884ef082e9966f3a14ae124720cbf4d7dbf42` after `git fetch origin --prune`.
- The working tree was clean before the branch was created.
- The repository contained only `AGENTS.md`, `CODEX.md`, `PLANS.md`, `IMPLEMENTATION_HANDOVER_PROMPT.md`, and `docs/MVP_IMPLEMENTATION_PLAN.md`.
- No `docs/changes/` files, application directories, test suites, root `Makefile`, package manifests, schemas, migrations, or CI configuration existed.
- The MVP plan defines seven Milestone 0 deliverables and says the milestone exits only when none remain unresolved.
- The supported exam set, pilot cohort, device matrix, numeric release thresholds, and legal/privacy conclusions cannot be inferred safely from the repository.
- No root validation command contract exists yet; that is a Milestone 1 deliverable.
- On 2026-08-25, the project owner confirmed that all MVP decisions are made by the project owner and requested removal of separate decision-owner and approver assignments.
- On 2026-08-25, the project owner directed the project to prioritize the human–AI interaction UI/UX and defer external-pilot governance and statistical validation until they are relevant.
- The development environment is Linux x86_64 and currently has no browser, Playwright, Android Emulator, or Apple simulator installed.
- Playwright supports repeatable mobile/tablet browser emulation on Linux; Android Emulator can be added for deeper Android checks; Apple's iOS/iPadOS Simulator requires Xcode on macOS and is unavailable in the current environment.

## Design

Use a small set of permanent documents organized by concern:

- a Milestone 0 index tracks the exit gates and links to evidence;
- a pilot-scope record owns supported exams, cohort, devices, and pilot criteria;
- evaluation documents define the provider benchmark and release gates;
- a privacy action list tracks required specialist evidence without making legal claims;
- a content provenance policy defines the minimum publication controls.

Each unresolved field uses the exact marker `DECISION REQUIRED`. The project owner confirms every MVP product decision. The milestone index records the exact `Required before` stage for each gate so later safeguards remain visible without holding up internal product learning. A document may still require qualified review evidence without turning the reviewer into a separate decision authority or pretending that legal, rights, security, or mathematics validation has occurred.

Alternatives rejected:

- One large decision document would mix concerns and make focused review difficult.
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
- `docs/MVP_IMPLEMENTATION_PLAN.md` — milestone gating and critical-path wording updated to prioritize the internal interaction MVP.

The seven Milestone 0 documents and the permanent MVP plan are modified by the review-driven sequencing update. No application or tooling file is changed.

## API and schema changes

None.

## Database and migration

None.

## Security and privacy

No student data, images, credentials, provider data, or runtime behavior are introduced. Privacy/legal review no longer blocks internal implementation with synthetic fixtures, but remains mandatory before collecting real minors' data or inviting external pilot participants. Legal conclusions, retention periods, and consent language remain `DECISION REQUIRED` until that pre-pilot review.

## Test plan

There is no application or documentation test framework. Validate the documentation with the available repository tools:

- confirm the expected files exist;
- confirm every Milestone 0 deliverable is represented in the index;
- confirm each deferred decision names the stage it blocks and does not block Milestone 1;
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
4. Confirm the documents authorize internal Milestone 1 work while keeping real-content, provider, privacy, and external-pilot gates attached to their later stages.
5. Compare the documents with sections 3, 15, and 17 of `docs/MVP_IMPLEMENTATION_PLAN.md`.

Expected outcome: the internal interaction MVP is authorized, no deferred product decision is fabricated, and each remaining gate states exactly which later stage it blocks.

## Rollout and rollback

These documents take effect when merged. There is no runtime rollout, data migration, or compatibility concern. Roll back by reverting the documentation commits. Project-owner decisions should be added through later reviewed changes that update the relevant document and Milestone 0 index together.

## Branch and commit plan

1. `docs: add Milestone 0 change plan`
2. `docs: define pilot scope and governance controls`
3. `docs: specify AI benchmark and release gates`
4. `docs: record Milestone 0 verification`
5. `docs: prioritize internal interaction MVP`
6. `docs: record interaction MVP verification`

## Conflict coordination

This branch owns the seven new documentation files and `docs/MVP_IMPLEMENTATION_PLAN.md`. No active ChangePlans or implementation branches were visible in the fetched repository. The permanent plan is a shared file; future milestone branches must rebase after this branch and follow its revised gate timing. Integration order: merge this Milestone 0 baseline before branches that resolve individual gates or begin Milestone 1.

## Risks

- Stakeholders may mistake a process specification for an approved decision. Mitigation: use explicit readiness states and `DECISION REQUIRED` markers.
- Numeric gates could be invented for convenience. Mitigation: define metric semantics now but leave thresholds unresolved.
- Legal or consent text could be treated as legal advice or ignored because it is deferred. Mitigation: maintain the pre-pilot action list and require qualified supporting evidence before real minors' data is collected.
- The benchmark could favor a provider through an unrepresentative dataset. Mitigation: define corpus strata, blinded review, and auditable per-case results.
- Real third-party content could be imported without sufficient rights evidence. Mitigation: make provenance and publication review mandatory before that import.
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
- [x] Conflict resolution re-tested — no conflicts occurred; all documentation checks passed after rebase
- [x] Handoff summary written

## Decisions

- 2026-08-25: Keep Milestone 0 documentation separate from Milestone 1 application scaffolding so this branch remains one coherent governance change.
- 2026-08-25: Use `DECISION REQUIRED` for values that the repository does not establish.
- 2026-08-25: Organize permanent documents by concern and use the milestone index as the readiness summary.
- 2026-08-25: Following project-owner review, use the project owner as the sole MVP decision authority and defer multi-role governance until product-release preparation. Preserve specialist validation as evidence where required.
- 2026-08-25: External-pilot governance and statistical validation do not block Milestone 1. Internal development uses synthetic fixtures and focuses first on the human–AI interaction loop.
- 2026-08-25: Use Playwright device emulation as the default phone/tablet development matrix. Add Android Emulator checks later; defer true iOS/iPadOS Simulator checks until a macOS/Xcode environment is available.

## Discoveries

- The repository is an initial documentation-only handover with no validation tooling.
- The initial plan treated every pilot/release decision as a Milestone 1 blocker; project-owner review established that this sequencing obscured the MVP's interaction-learning goal.
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
    docs/MVP_IMPLEMENTATION_PLAN.md
    docs/changes/2026-08-25-m0-scope-governance.md
    docs/milestone-0/README.md
    docs/product/PILOT_SCOPE.md
    docs/evaluation/AI_PROVIDER_BENCHMARK.md
    docs/evaluation/RELEASE_QUALITY_GATES.md
    docs/privacy/PRIVACY_AND_CONSENT_ACTION_LIST.md
    docs/content/CONTENT_PROVENANCE_POLICY.md
  )
  decision_documents=(
    docs/milestone-0/README.md
    docs/product/PILOT_SCOPE.md
    docs/evaluation/AI_PROVIDER_BENCHMARK.md
    docs/evaluation/RELEASE_QUALITY_GATES.md
    docs/privacy/PRIVACY_AND_CONSENT_ACTION_LIST.md
    docs/content/CONTENT_PROVENANCE_POLICY.md
  )
  for expected_file in "${expected_files[@]}"; do
    test -f "$expected_file"
  done
  test "$(rg -l 'DECISION REQUIRED' "${expected_files[@]}" | wc -l)" -eq 7
  test "$(rg -n '^\| (Supported exam list|Pilot cohort definition|Internal development-device matrix|AI benchmark specification|Privacy and consent action list|Content provenance policy|Release-quality gates) \|' docs/milestone-0/README.md | wc -l)" -eq 7
  if rg -n 'PTNK|HCMC_Specialized' "${decision_documents[@]}"; then
    exit 1
  fi
  ```

  The first post-commit run failed only because the example-exam search included this ChangePlan's copy of the command. After correcting the scope to `decision_documents`, the baseline result was seven expected files, seven files with explicit decision markers, seven indexed exit-gate rows, and zero copied example exam identifiers in the permanent decision documents.

- The review-driven validation passed before commit with these results: eight expected and changed documentation files; seven files with explicit deferred decisions; seven stage-gate rows; zero legacy Milestone 1 blockers or multi-owner markers; both minor-pilot safety constraints preserved; two explicit Milestone 1 authorization statements; all approved emulator targets present; 23 relative Markdown links resolved; and `git diff --check origin/main` passed.
- `git fetch origin --prune` immediately before the review-driven commit confirmed that `origin/main` remains at `b8c884e`.
- After commit, `git fetch origin --prune && git rebase origin/main` reported that the branch was current and produced no conflicts. The complete review-driven validation then passed again against `origin/main...HEAD` with the same counts and a clean `git diff --check`.

- Relative-link validation extracted every local `.md` link with `rg`, resolved it from the source document's directory, and asserted the target exists. Result: 23 links checked; all passed.
- `sed -n '1,$p'` was run across all seven new documents for manual review against sections 3, 15, and 17 of the MVP plan.
- `git diff --name-status origin/main...HEAD` and `git diff --stat origin/main...HEAD` — reviewed seven added documentation files totaling 1,034 lines before the final ChangePlan update; no application, schema, migration, dependency, CI, infrastructure, or root-command file was changed.
- The final branch diff is limited to the permanent MVP plan and seven Milestone 0 documents: eight files, 1,202 insertions, and 19 deletions before this closing ChangePlan update.
- No application tests or root `make` commands were run because neither exists and this change introduces no application behavior.

## Result

Revised the permanent MVP plan and Milestone 0 records to authorize an interaction-first internal build with synthetic/non-personal fixtures and a deterministic fake provider. The project owner is the sole MVP decision authority. Playwright phone/tablet emulation is approved for daily development; deeper Android, Apple, and physical-device checks are scheduled for later gates. Unresolved exam, provider, privacy, content-rights, release, and pilot-operation decisions remain explicit and block only the real-content, real-provider, real-data, or external-pilot stage that requires them. No application code or tooling was added.
