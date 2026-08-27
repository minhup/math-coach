import { describe, expect, it } from "vitest";

import type { StaticJourneyState } from "./static-journey-state";
import { summarizeStaticJourney } from "./session-summary";

const completed: StaticJourneyState = {
  data: {
    attempts: [
      {
        id: "attempt-1",
        problemVersionId: "problem-version-1",
        studyProfileId: "profile-1",
      },
      {
        id: "attempt-2",
        problemVersionId: "problem-version-1",
        studyProfileId: "profile-1",
      },
    ],
    concept: { conceptVersionId: "concept-version-1" },
    evaluation: { outcome: "ready", transcriptFingerprint: "a".repeat(64) },
    hints: [{ hintLevel: 1 }, { hintLevel: 2 }],
    plan: {
      id: "plan-1",
      items: [
        {
          conceptVersionId: "concept-version-1",
          problemVersionId: "problem-version-1",
          supportedTargetIds: ["target-1", "target-2"],
        },
        {
          conceptVersionId: "concept-version-1",
          problemVersionId: "problem-version-2",
          supportedTargetIds: ["target-1"],
        },
      ],
    },
    profile: { id: "profile-1", targetIds: ["target-1", "target-2"] },
    selectedItem: {
      conceptVersionId: "concept-version-1",
      problemVersionId: "problem-version-1",
      supportedTargetIds: ["target-1", "target-2"],
    },
  },
  phase: "completion",
  status: "ready",
};

describe("static session summary", () => {
  it("derives complete and incomplete known values without generated prose", () => {
    expect(summarizeStaticJourney(completed)).toEqual({
      attemptCount: 2,
      completionStatus: "complete",
      evaluationOutcome: "ready",
      hintLevelsUsed: [1, 2],
      plannedItemCount: 2,
      problemVersionId: "problem-version-1",
      schemaVersion: "1.0.0",
      targetCount: 2,
    });
    expect(summarizeStaticJourney({ ...completed, phase: "retry" })).toEqual({
      attemptCount: 2,
      completionStatus: "incomplete",
      evaluationOutcome: "ready",
      hintLevelsUsed: [1, 2],
      plannedItemCount: 2,
      problemVersionId: "problem-version-1",
      schemaVersion: "1.0.0",
      targetCount: 2,
    });
  });
});
