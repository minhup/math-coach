import { describe, expect, it } from "vitest";

import {
  createInitialStaticJourneyState,
  transitionStaticJourney,
  type StaticJourneyEvent,
} from "./static-journey-state";

const profile = {
  id: "50000000-0000-4000-8000-000000000010",
  targetIds: ["50000000-0000-4000-8000-000000000011", "50000000-0000-4000-8000-000000000012"],
};

const plan = {
  id: "50000000-0000-4000-8000-000000000020",
  items: [
    {
      conceptVersionId: "10000000-0000-4000-8000-000000000601",
      problemVersionId: "40000000-0000-4000-8000-000000000701",
      supportedTargetIds: profile.targetIds,
    },
  ],
};

const attempt = {
  id: "50000000-0000-4000-8000-000000000030",
  problemVersionId: plan.items[0].problemVersionId,
  studyProfileId: profile.id,
};

const transcript = {
  attemptId: attempt.id,
  blocks: [{ id: "text-1", text: "Reviewed.", type: "text" as const }],
  schemaVersion: "2.0.0" as const,
};

function accepted(
  state: ReturnType<typeof createInitialStaticJourneyState>,
  event: StaticJourneyEvent,
) {
  const result = transitionStaticJourney(state, event);
  expect(result.accepted).toBe(true);
  if (!result.accepted) {
    throw new Error(result.errorCode);
  }
  return result.state;
}

describe("static student journey state", () => {
  it("accepts the complete required sequence and keeps immutable retry identity", () => {
    let state = createInitialStaticJourneyState();
    state = accepted(state, { type: "onboarding_loaded", profile });
    state = accepted(state, { type: "start_planning" });
    state = accepted(state, { plan, type: "plan_loaded" });
    state = accepted(state, { attempt, itemIndex: 0, type: "problem_started" });
    state = accepted(state, { type: "upload_started" });
    state = accepted(state, {
      type: "upload_ready",
      upload: { id: "50000000-0000-4000-8000-000000000040", status: "ready" },
    });
    state = accepted(state, { transcript, type: "transcript_received" });
    state = accepted(state, { transcript, type: "transcript_confirmed" });
    state = accepted(state, { type: "evaluation_requested" });
    state = accepted(state, {
      evaluation: { outcome: "ready", transcriptFingerprint: "a".repeat(64) },
      type: "evaluation_received",
    });
    state = accepted(state, { type: "hint_requested" });
    state = accepted(state, {
      hint: { hintLevel: 1 },
      type: "hint_received",
    });
    state = accepted(state, {
      attempt: {
        ...attempt,
        id: "50000000-0000-4000-8000-000000000031",
      },
      type: "retry_started",
    });
    state = accepted(state, { type: "concept_requested" });
    state = accepted(state, {
      concept: { conceptVersionId: plan.items[0].conceptVersionId },
      type: "concept_received",
    });
    state = accepted(state, { type: "session_completed" });

    expect(state.phase).toBe("completion");
    expect(state.data.attempts.map(({ id }) => id)).toEqual([
      "50000000-0000-4000-8000-000000000030",
      "50000000-0000-4000-8000-000000000031",
    ]);
    expect(state.data.selectedItem?.problemVersionId).toBe("40000000-0000-4000-8000-000000000701");
  });

  it("rejects evaluation before confirmation without mutating state", () => {
    const state = createInitialStaticJourneyState();
    const result = transitionStaticJourney(state, { type: "evaluation_requested" });

    expect(result).toEqual({
      accepted: false,
      errorCode: "invalid_transition",
      state,
    });
  });

  it("advances hints in order and rejects retrying a permanent failure", () => {
    let state = createInitialStaticJourneyState();
    state = accepted(state, { profile, type: "onboarding_loaded" });
    state = accepted(state, { type: "start_planning" });
    state = accepted(state, { plan, type: "plan_loaded" });
    state = accepted(state, { attempt, itemIndex: 0, type: "problem_started" });
    state = accepted(state, { type: "upload_started" });
    state = accepted(state, {
      type: "upload_ready",
      upload: { id: "upload-1", status: "ready" },
    });
    state = accepted(state, { transcript, type: "transcript_received" });
    state = accepted(state, { transcript, type: "transcript_confirmed" });
    state = accepted(state, { type: "evaluation_requested" });
    state = accepted(state, {
      evaluation: { outcome: "ready", transcriptFingerprint: "a".repeat(64) },
      type: "evaluation_received",
    });
    state = accepted(state, { type: "hint_requested" });
    state = accepted(state, { hint: { hintLevel: 1 }, type: "hint_received" });
    state = accepted(state, { type: "hint_requested" });
    state = accepted(state, { hint: { hintLevel: 2 }, type: "hint_received" });

    expect(state.data.hints).toEqual([{ hintLevel: 1 }, { hintLevel: 2 }]);

    const failed = transitionStaticJourney(state, {
      failure: "permanent",
      type: "operation_failed",
    });
    expect(failed.accepted).toBe(true);
    if (!failed.accepted) {
      return;
    }
    expect(transitionStaticJourney(failed.state, { type: "operation_retried" })).toMatchObject({
      accepted: false,
      errorCode: "invalid_transition",
    });
  });
});
