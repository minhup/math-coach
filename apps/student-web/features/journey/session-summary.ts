import type { StaticJourneyState } from "./static-journey-state";

export type StaticSessionSummary = {
  attemptCount: number;
  completionStatus: "complete" | "incomplete";
  evaluationOutcome: "ready" | "uncertain" | null;
  hintLevelsUsed: number[];
  plannedItemCount: number;
  problemVersionId: string | null;
  schemaVersion: "1.0.0";
  targetCount: number;
};

export function summarizeStaticJourney(state: StaticJourneyState): StaticSessionSummary {
  return {
    attemptCount: state.data.attempts.length,
    completionStatus:
      state.phase === "completion" && state.status === "ready" ? "complete" : "incomplete",
    evaluationOutcome: state.data.evaluation?.outcome ?? null,
    hintLevelsUsed: state.data.hints.map(({ hintLevel }) => hintLevel),
    plannedItemCount: state.data.plan?.items.length ?? 0,
    problemVersionId: state.data.selectedItem?.problemVersionId ?? null,
    schemaVersion: "1.0.0",
    targetCount: state.data.profile?.targetIds.length ?? 0,
  };
}
