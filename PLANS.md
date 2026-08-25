# Change Plans

Every repository change requires a written ChangePlan before implementation begins. This applies to features, fixes, refactors, tests, documentation, migrations, dependency updates, and build changes.

The plan is a living execution record, not a one-time proposal. Update it while the work proceeds.

## File location

```text
docs/changes/YYYY-MM-DD-<short-slug>.md
```

Use one ChangePlan per branch. Do not reuse a plan for unrelated work.

## Required template

```markdown
# <Change title>

## Metadata

- Status: proposed | in-progress | blocked | ready-for-review | complete
- Owner:
- Branch:
- Base commit:
- Related milestone:
- Related issue/ticket:
- Started:
- Last updated:

## Context

Describe the current behavior and why this change is needed.

## Goal

State the observable result of the change.

## Non-goals

List behavior intentionally excluded.

## User-visible behavior

Describe every user-visible change. Write `None` when there is none.

## Current-state findings

Record the relevant repository structure, existing code paths, constraints, and test coverage discovered before editing.

## Design

Describe the selected design, data flow, boundaries, and important alternatives rejected.

## Multi-exam impact

State explicitly whether the change affects:

- study profiles;
- exam targets;
- exam-specific progress;
- shared skill state;
- daily-plan balancing.

Never assume a student has only one target examination.

## Files and components

List files to add, modify, move, or delete and explain why.

## API and schema changes

Document request/response, shared type, content schema, or AI schema changes. Write `None` when there are none.

## Database and migration

Document tables, columns, indexes, backfill, compatibility, rollback, and data-loss risk. Write `None` when there are none.

## Security and privacy

Document effects on authentication, authorization, student data, images, logs, retention, secrets, or provider processing.

## Test plan

List exact tests to add or update:

- unit;
- integration;
- contract/schema;
- migration;
- frontend component;
- browser/end-to-end;
- content validation;
- AI evaluation/regression;
- manual device QA.

## Manual QA

Provide exact steps and expected outcomes.

## Rollout and rollback

Describe feature flags, release order, compatibility, monitoring, and rollback procedure.

## Branch and commit plan

List the intended small commits in order. Each commit must be independently understandable and keep the branch in a testable state.

## Conflict coordination

List owned files/directories and known overlap with other active branches. State the planned integration order for overlaps.

## Risks

List technical, product, content, AI, privacy, and schedule risks with mitigations.

## Progress

- [ ] Repository inspected
- [ ] Plan reviewed
- [ ] Branch created from current main
- [ ] Tests written or updated
- [ ] Implementation complete
- [ ] Documentation updated
- [ ] Relevant checks pass
- [ ] Diff reviewed
- [ ] Branch rebased on current main
- [ ] Conflict resolution re-tested
- [ ] Handoff summary written

## Decisions

Record decisions made during implementation with date and rationale.

## Discoveries

Record unexpected repository facts or behavior that changed the plan.

## Verification evidence

Record the exact commands run and their results. Do not write “tests pass” without naming the commands.

## Result

Summarize the final implementation, remaining limitations, and follow-up work.
```

## Plan rules

1. Create the ChangePlan before changing implementation files.
2. Inspect the repository before claiming a design matches existing code.
3. Keep the plan synchronized with the actual diff.
4. Record deviations instead of silently implementing a different design.
5. Do not mark the plan complete until tests, documentation, rebase, and diff review are complete.
6. A small change may have a short plan, but every required section must exist.
7. Never claim a command succeeded unless it was actually run.
8. Never hide a failing test, skipped test, migration risk, or unresolved conflict.
