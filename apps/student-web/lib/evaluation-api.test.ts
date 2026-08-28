import { afterEach, describe, expect, it, vi } from "vitest";

import { getEvaluationState, parseEvaluation, requestEvaluation } from "./evaluation-api";

const run = {
  completedAt: "2026-08-28T00:00:01Z",
  costUsd: "0.000000",
  errorCode: null,
  id: "70000000-0000-4000-8000-000000000001",
  inputTokens: 0,
  latencyMs: 0,
  modelSnapshot: "m7-evaluation-fixture-v1",
  outputTokens: 0,
  pricingVersion: "fake-zero-v1",
  promptHash: "a".repeat(64),
  promptVersion: "m7-evaluation-v1",
  provider: "application-owned-deterministic-fake",
  retryCount: 0,
  schemaAttempts: 1,
  schemaVersion: "m7-provider-evaluation-v1",
  startedAt: "2026-08-28T00:00:00Z",
  status: "succeeded",
};

function readyEvaluation() {
  return {
    confirmedTranscriptVersionId: "60000000-0000-4000-8000-000000000001",
    evaluationId: "70000000-0000-4000-8000-000000000002",
    feedback: [{ id: "feedback", text: "Correct the root error first.", type: "text" }],
    maximumScore: "4.00",
    nextSteps: [{ id: "next", text: "Request a curated hint.", type: "text" }],
    outcome: "ready",
    reasoningSteps: [
      {
        dependsOnStepIds: [],
        errorKind: "root",
        feedback: [{ id: "feedback-1", text: "Average the coordinates.", type: "text" }],
        id: "70000000-0000-4000-8000-000000000010",
        judgment: "incorrect",
        position: 1,
        summary: [{ id: "summary-1", text: "The midpoint is incorrect.", type: "text" }],
        transcriptBlockIds: ["block-1"],
      },
      {
        dependsOnStepIds: ["70000000-0000-4000-8000-000000000010"],
        errorKind: "dependent",
        feedback: [{ id: "feedback-2", text: "Recompute the distance.", type: "text" }],
        id: "70000000-0000-4000-8000-000000000011",
        judgment: "incorrect",
        position: 2,
        summary: [{ id: "summary-2", text: "The distance uses that midpoint.", type: "text" }],
        transcriptBlockIds: ["block-2"],
      },
    ],
    referenceSolutionsNonExhaustive: true,
    rubricBreakdown: [
      {
        awardedScore: "0.00",
        explanation: [{ id: "rubric-1", text: "Not supported.", type: "text" }],
        maximumScore: "2.00",
        rubricCode: "midpoint",
        rubricItemId: "70000000-0000-4000-8000-000000000020",
      },
      {
        awardedScore: "0.00",
        explanation: [{ id: "rubric-2", text: "Not supported.", type: "text" }],
        maximumScore: "2.00",
        rubricCode: "distance",
        rubricItemId: "70000000-0000-4000-8000-000000000021",
      },
    ],
    run,
    score: "0.00",
  };
}

afterEach(() => vi.restoreAllMocks());

describe("evaluation API boundary", () => {
  it("sends only exact confirmation identity plus application idempotency", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(new Response(JSON.stringify(readyEvaluation())));

    await requestEvaluation("attempt-1", "transcript-version-1", "evaluation-key-1");

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/attempts/attempt-1/evaluation",
      expect.objectContaining({
        body: JSON.stringify({
          confirmedTranscriptVersionId: "transcript-version-1",
          idempotencyKey: "evaluation-key-1",
        }),
        method: "POST",
      }),
    );
  });

  it("rejects unknown fields, inconsistent scores, and forward dependencies", () => {
    expect(() => parseEvaluation({ ...readyEvaluation(), hiddenReasoning: "never" })).toThrow();
    expect(() => parseEvaluation({ ...readyEvaluation(), score: "1.00" })).toThrow();
    const forward = readyEvaluation();
    forward.reasoningSteps[0].dependsOnStepIds = [forward.reasoningSteps[1].id];
    expect(() => parseEvaluation(forward)).toThrow();
  });

  it("accepts uncertainty only when score and steps are absent", () => {
    const uncertain = {
      confirmedTranscriptVersionId: "60000000-0000-4000-8000-000000000001",
      evaluationId: "70000000-0000-4000-8000-000000000002",
      outcome: "uncertain",
      reason: [{ id: "reason", text: "The work is contradictory.", type: "text" }],
      recommendedAction: "manual_review",
      run: { ...run, status: "uncertain" },
    };

    expect(parseEvaluation(uncertain)).toMatchObject({ outcome: "uncertain" });
    expect(() => parseEvaluation({ ...uncertain, score: "0.00" })).toThrow();
  });

  it("validates explicit processing and failure states", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            run: { ...run, completedAt: null, status: "processing" },
            state: "processing",
          }),
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            run: { ...run, errorCode: "invalid_schema", status: "invalid_schema" },
            state: "invalid_schema",
          }),
        ),
      );

    await expect(getEvaluationState("attempt-1")).resolves.toMatchObject({ state: "processing" });
    await expect(getEvaluationState("attempt-1")).resolves.toMatchObject({
      state: "invalid_schema",
    });
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });
});
