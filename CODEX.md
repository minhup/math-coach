# Codex Setup

Codex repository instructions are defined in [`AGENTS.md`](./AGENTS.md), which is the file Codex loads automatically for repository-level guidance.

Before implementation, Codex must read:

1. [`AGENTS.md`](./AGENTS.md)
2. [`PLANS.md`](./PLANS.md)
3. [`docs/MVP_IMPLEMENTATION_PLAN.md`](./docs/MVP_IMPLEMENTATION_PLAN.md)
4. the active file under `docs/changes/`

Use [`IMPLEMENTATION_HANDOVER_PROMPT.md`](./IMPLEMENTATION_HANDOVER_PROMPT.md) to begin a new implementation session.

Do not duplicate operational rules in this file. Update `AGENTS.md` so humans and Codex use one source of truth.
