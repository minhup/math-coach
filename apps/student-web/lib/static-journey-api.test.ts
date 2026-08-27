import { afterEach, describe, expect, it, vi } from "vitest";

import {
  addExamTarget,
  createAttempt,
  createStudyProfile,
  getAvailableExamCycles,
  getConceptVersion,
  getStaticPlan,
  getStudyProfile,
  requestMockEvaluation,
  requestMockTranscription,
  requestNextHint,
} from "./static-journey-api";

function validPlanPayload() {
  return {
    items: [
      {
        conceptVersionId: "10000000-0000-4000-8000-000000000601",
        position: 1,
        problem: {
          estimatedMinutes: 15,
          externalCode: "SYN-M4-GEO-001",
          geometryScene: null,
          problemId: "40000000-0000-4000-8000-000000000700",
          problemVersionId: "40000000-0000-4000-8000-000000000701",
          statement: [{ id: "problem", text: "Synthetic problem.", type: "text" }],
          version: 1,
        },
        selectionReason: "shared_target_foundation",
        supportedTargetIds: ["target-1", "target-2"],
      },
    ],
    planDate: "2026-08-27",
    planId: "50000000-0000-4000-8000-000000000020",
    profileId: "50000000-0000-4000-8000-000000000010",
    schemaVersion: "1.0.0",
    targets: [
      {
        cycleCode: "SYN-AURORA-2027",
        examCycleId: "10000000-0000-4000-8000-000000000201",
        examName: "Synthetic Aurora Mathematics Examination",
        priorityRank: 1,
        targetId: "target-1",
      },
      {
        cycleCode: "SYN-HARBOR-2027",
        examCycleId: "10000000-0000-4000-8000-000000000202",
        examName: "Synthetic Harbor Mathematics Examination",
        priorityRank: 2,
        targetId: "target-2",
      },
    ],
  };
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("static journey API boundary", () => {
  it("accepts a strict deterministic plan and rejects support outside its target records", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(new Response(JSON.stringify(validPlanPayload())))
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            ...validPlanPayload(),
            items: [
              {
                ...validPlanPayload().items[0],
                supportedTargetIds: ["unknown-target"],
              },
            ],
          }),
        ),
      );

    await expect(getStaticPlan()).resolves.toMatchObject({
      items: [{ supportedTargetIds: ["target-1", "target-2"] }],
    });
    await expect(getStaticPlan()).rejects.toMatchObject({
      code: "invalid_response",
      status: 502,
    });
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/plans/today",
      expect.objectContaining({ credentials: "same-origin" }),
    );
  });

  it("sends only the explicitly confirmed transcript to mock evaluation", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          feedback: [{ id: "feedback", text: "Synthetic feedback.", type: "text" }],
          metadata: {
            costUsd: "0.000000",
            inputTokens: 0,
            latencyMs: 0,
            modelSnapshot: "m5-static-fixture-v1",
            outputTokens: 0,
            promptVersion: "m5-no-provider-prompt-v1",
            provider: "application-owned-synthetic-mock",
            schemaVersion: "1.0.0",
          },
          nextSteps: [{ id: "next", text: "Request a hint.", type: "text" }],
          outcome: "ready",
          referenceSolutionsNonExhaustive: true,
          transcriptFingerprint: "a".repeat(64),
        }),
      ),
    );
    const transcript = {
      attemptId: "attempt-1",
      blocks: [{ id: "text-1", text: "Reviewed.", type: "text" as const }],
      schemaVersion: "2.0.0" as const,
    };

    await requestMockEvaluation("attempt-1", transcript);

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/attempts/attempt-1/mock-evaluation",
      expect.objectContaining({
        body: JSON.stringify({
          confirmedTranscript: { confirmationStatus: "confirmed", transcript },
        }),
        method: "POST",
      }),
    );
  });

  it("validates onboarding, attempt, transcript, hint, and concept payloads", async () => {
    const target = {
      createdAt: "2026-08-27T00:00:00Z",
      examCode: "SYN-AURORA",
      examCycleId: "cycle-1",
      examDate: "2027-06-01",
      examId: "exam-1",
      examName: "Synthetic Aurora Mathematics Examination",
      id: "target-1",
      priorityRank: 1,
      status: "active",
      targetScore: "16.00",
    };
    const profile = {
      createdAt: "2026-08-27T00:00:00Z",
      id: "profile-1",
      name: "Synthetic preparation",
      status: "active",
      studentExamTargets: [target],
      updatedAt: "2026-08-27T00:00:00Z",
      weeklyStudyMinutes: 240,
    };
    const metadata = {
      costUsd: "0.000000",
      inputTokens: 0,
      latencyMs: 0,
      modelSnapshot: "m5-static-fixture-v1",
      outputTokens: 0,
      promptVersion: "m5-no-provider-prompt-v1",
      provider: "application-owned-synthetic-mock",
      schemaVersion: "1.0.0",
    };
    const fetchMock = vi.spyOn(globalThis, "fetch");
    for (const response of [
      profile,
      { ...profile, studentExamTargets: [] },
      target,
      {
        items: [
          {
            cycleCode: "SYN-AURORA-2027",
            examCode: "SYN-AURORA",
            examDate: "2027-06-01",
            examId: "exam-1",
            examName: "Synthetic Aurora Mathematics Examination",
            id: "cycle-1",
            year: 2027,
          },
        ],
      },
      {
        createdAt: "2026-08-27T00:00:00Z",
        id: "attempt-1",
        problemVersionId: "problem-version-1",
        status: "draft",
        studyProfileId: "profile-1",
      },
      {
        metadata,
        transcript: {
          attemptId: "attempt-1",
          blocks: [{ id: "text-1", text: "Synthetic transcript.", type: "text" }],
          schemaVersion: "2.0.0",
        },
      },
      {
        conceptVersionId: null,
        content: [{ id: "hint-1", text: "Inspect the midpoint.", type: "text" }],
        geometryActions: [],
        hintId: "hint-1",
        hintLevel: 1,
        revealsCompleteSolution: false,
      },
      {
        code: "SYN-MIDPOINT-COORDINATES",
        conceptId: "concept-1",
        conceptVersionId: "concept-version-1",
        content: [{ id: "concept-1", text: "Average the coordinates.", type: "text" }],
        geometryScene: null,
        name: "Midpoint coordinates",
        version: 1,
      },
    ]) {
      fetchMock.mockResolvedValueOnce(new Response(JSON.stringify(response)));
    }

    await expect(getStudyProfile()).resolves.toMatchObject({ id: "profile-1" });
    await expect(
      createStudyProfile({ name: "Synthetic preparation", weeklyStudyMinutes: 240 }),
    ).resolves.toMatchObject({ studentExamTargets: [] });
    await expect(
      addExamTarget({ examCycleId: "cycle-1", priorityRank: 1, targetScore: "16.00" }),
    ).resolves.toMatchObject({ id: "target-1" });
    await expect(getAvailableExamCycles()).resolves.toMatchObject({
      items: [{ cycleCode: "SYN-AURORA-2027" }],
    });
    await expect(createAttempt("problem-version-1")).resolves.toMatchObject({ id: "attempt-1" });
    await expect(requestMockTranscription("attempt-1", "upload-1")).resolves.toMatchObject({
      transcript: { attemptId: "attempt-1" },
    });
    await expect(requestNextHint("attempt-1", 0)).resolves.toMatchObject({ hintLevel: 1 });
    await expect(getConceptVersion("concept-version-1")).resolves.toMatchObject({
      code: "SYN-MIDPOINT-COORDINATES",
    });
  });

  it("rejects an invalid mock transcript before correction UI can use it", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          metadata: {
            costUsd: "0.000000",
            inputTokens: 0,
            latencyMs: 0,
            modelSnapshot: "m5-static-fixture-v1",
            outputTokens: 0,
            promptVersion: "m5-no-provider-prompt-v1",
            provider: "application-owned-synthetic-mock",
            schemaVersion: "1.0.0",
          },
          transcript: {
            attemptId: "attempt-1",
            blocks: [
              {
                html: "<script>unsafe()</script>",
                id: "text-1",
                text: "Synthetic transcript.",
                type: "text",
              },
            ],
            schemaVersion: "2.0.0",
          },
        }),
      ),
    );

    await expect(requestMockTranscription("attempt-1", "upload-1")).rejects.toMatchObject({
      code: "invalid_response",
      status: 502,
    });
  });
});
