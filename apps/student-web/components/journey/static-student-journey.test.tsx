import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { syntheticGeometryScene } from "../../features/geometry/synthetic-fixtures";
import { ApiError } from "../../lib/api";
import type { StaticJourneyApi } from "./static-student-journey";
import { StaticStudentJourney } from "./static-student-journey";

const profile = {
  createdAt: "2026-08-27T00:00:00Z",
  id: "profile-1",
  name: "Synthetic preparation",
  status: "active" as const,
  studentExamTargets: [
    {
      createdAt: "2026-08-27T00:00:00Z",
      examCode: "SYN-AURORA",
      examCycleId: "cycle-1",
      examDate: "2027-06-01",
      examId: "exam-1",
      examName: "Synthetic Aurora Mathematics Examination",
      id: "target-1",
      priorityRank: 1,
      status: "active" as const,
      targetScore: "16.00",
    },
    {
      createdAt: "2026-08-27T00:00:00Z",
      examCode: "SYN-HARBOR",
      examCycleId: "cycle-2",
      examDate: "2027-06-08",
      examId: "exam-2",
      examName: "Synthetic Harbor Mathematics Examination",
      id: "target-2",
      priorityRank: 2,
      status: "active" as const,
      targetScore: "15.00",
    },
  ],
  updatedAt: "2026-08-27T00:00:00Z",
  weeklyStudyMinutes: 240,
};

const plan = {
  items: [
    {
      conceptVersionId: "concept-version-1",
      position: 1,
      problem: {
        estimatedMinutes: 15,
        externalCode: "SYN-M4-GEO-001",
        geometryScene: syntheticGeometryScene,
        problemId: "problem-1",
        problemVersionId: "problem-version-1",
        statement: [
          { id: "statement", text: "Find the synthetic midpoint.", type: "text" as const },
          {
            id: "geometry",
            sceneVersionId: syntheticGeometryScene.id,
            type: "geometry" as const,
          },
        ],
        version: 1,
      },
      selectionReason: "shared_target_foundation" as const,
      supportedTargetIds: ["target-1", "target-2"],
    },
    {
      conceptVersionId: "concept-version-1",
      position: 2,
      problem: {
        estimatedMinutes: 10,
        externalCode: "SYN-M2-GEO-001",
        geometryScene: null,
        problemId: "problem-2",
        problemVersionId: "problem-version-2",
        statement: [{ id: "follow-up", text: "Synthetic follow-up.", type: "text" as const }],
        version: 1,
      },
      selectionReason: "priority_target_follow_up" as const,
      supportedTargetIds: ["target-1"],
    },
  ],
  planDate: "2026-08-27",
  planId: "plan-1",
  profileId: profile.id,
  schemaVersion: "1.0.0" as const,
  targets: profile.studentExamTargets.map((target) => ({
    cycleCode: `${target.examCode}-2027`,
    examCycleId: target.examCycleId,
    examName: target.examName,
    priorityRank: target.priorityRank,
    targetId: target.id,
  })),
};

const evaluationRun = {
  completedAt: "2026-08-27T00:00:03Z",
  costUsd: "0.000000",
  errorCode: null,
  id: "evaluation-run-1",
  inputTokens: 0 as const,
  latencyMs: 0,
  modelSnapshot: "m7-evaluation-fixture-v1",
  outputTokens: 0 as const,
  pricingVersion: "fake-zero-v1",
  promptHash: "c".repeat(64),
  promptVersion: "m7-evaluation-v1",
  provider: "application-owned-deterministic-fake",
  retryCount: 0,
  schemaAttempts: 1,
  schemaVersion: "m7-provider-evaluation-v1",
  startedAt: "2026-08-27T00:00:02Z",
  status: "succeeded" as const,
};

const transcriptDocument = {
  schemaVersion: "3.0.0" as const,
  attemptId: "attempt-1",
  blocks: [
    {
      id: "text-1",
      sourceRegion: {
        attemptAssetId: "asset-1",
        height: 0.1,
        units: "normalized" as const,
        width: 0.4,
        x: 0.1,
        y: 0.2,
      },
      text: "The synthetic midpoint is ",
      type: "text" as const,
    },
    { id: "math-1", latex: "M=(2,0", type: "math" as const },
  ],
  warnings: [
    {
      blockId: "math-1",
      code: "low_confidence_math" as const,
      message: "A formula may need review.",
    },
  ],
};

const transcriptionRun = {
  completedAt: "2026-08-27T00:00:01Z",
  costUsd: "0.000000",
  errorCode: null,
  id: "run-1",
  inputTokens: 0,
  latencyMs: 0,
  modelSnapshot: "m6-transcription-fixture-v1",
  outputTokens: 0,
  pricingVersion: "fake-zero-v1",
  promptHash: "a".repeat(64),
  promptVersion: "m6-faithful-transcription-v1",
  provider: "application-owned-deterministic-fake",
  schemaAttempts: 1,
  schemaVersion: "m6-provider-transcript-v1",
  startedAt: "2026-08-27T00:00:00Z",
  status: "succeeded" as const,
};

const transcriptVersion = {
  attemptId: "attempt-1",
  createdAt: "2026-08-27T00:00:01Z",
  document: transcriptDocument,
  id: "transcript-version-1",
  origin: "provider" as const,
  parentTranscriptVersionId: null,
  sourceRunId: transcriptionRun.id,
  transcriptHash: "b".repeat(64),
  version: 1,
};

function createApi(): StaticJourneyApi {
  return {
    addExamTarget: vi.fn(),
    createAttempt: vi
      .fn()
      .mockResolvedValueOnce({
        createdAt: "2026-08-27T00:00:00Z",
        id: "attempt-1",
        problemVersionId: "problem-version-1",
        status: "draft",
        studyProfileId: profile.id,
      })
      .mockResolvedValueOnce({
        createdAt: "2026-08-27T00:05:00Z",
        id: "attempt-2",
        problemVersionId: "problem-version-1",
        status: "draft",
        studyProfileId: profile.id,
      }),
    createStudyProfile: vi.fn(),
    getAvailableExamCycles: vi.fn().mockResolvedValue({ items: [] }),
    getConceptVersion: vi.fn().mockResolvedValue({
      code: "SYN-MIDPOINT-COORDINATES",
      conceptId: "concept-1",
      conceptVersionId: "concept-version-1",
      content: [{ id: "concept", text: "Average the two endpoint coordinates.", type: "text" }],
      geometryScene: null,
      name: "Midpoint coordinates",
      version: 1,
    }),
    getStaticPlan: vi.fn().mockResolvedValue(plan),
    getStudyProfile: vi.fn().mockResolvedValue(profile),
    getUploadDownload: vi.fn().mockResolvedValue({
      downloadUrl: "http://storage.test/synthetic-source.png?signature=safe",
      expiresAt: "2026-08-27T00:05:00Z",
      uploadId: "upload-1",
    }),
    requestEvaluation: vi.fn().mockResolvedValue({
      confirmedTranscriptVersionId: transcriptVersion.id,
      evaluationId: "evaluation-1",
      feedback: [{ id: "feedback", text: "Deterministic synthetic feedback.", type: "text" }],
      maximumScore: "4.00",
      nextSteps: [{ id: "next", text: "Request a curated hint.", type: "text" }],
      outcome: "ready",
      reasoningSteps: [
        {
          dependsOnStepIds: [],
          errorKind: "root",
          feedback: [{ id: "step-feedback-1", text: "Average the endpoints.", type: "text" }],
          id: "step-1",
          judgment: "incorrect",
          position: 1,
          summary: [{ id: "step-summary-1", text: "The midpoint is incorrect.", type: "text" }],
          transcriptBlockIds: ["text-1"],
        },
        {
          dependsOnStepIds: ["step-1"],
          errorKind: "dependent",
          feedback: [
            { id: "step-feedback-2", text: "Recompute after the midpoint.", type: "text" },
          ],
          id: "step-2",
          judgment: "incorrect",
          position: 2,
          summary: [
            { id: "step-summary-2", text: "The conclusion depends on that value.", type: "text" },
          ],
          transcriptBlockIds: ["math-1"],
        },
      ],
      referenceSolutionsNonExhaustive: true,
      rubricBreakdown: [
        {
          awardedScore: "0.00",
          explanation: [{ id: "rubric-1", text: "Not supported yet.", type: "text" }],
          maximumScore: "2.00",
          rubricCode: "midpoint",
          rubricItemId: "rubric-1",
        },
        {
          awardedScore: "0.00",
          explanation: [{ id: "rubric-2", text: "Not supported yet.", type: "text" }],
          maximumScore: "2.00",
          rubricCode: "distance",
          rubricItemId: "rubric-2",
        },
      ],
      run: evaluationRun,
      score: "0.00",
    }),
    requestTranscription: vi.fn().mockResolvedValue({
      outcome: "ready",
      run: transcriptionRun,
      transcriptVersion,
    }),
    createTranscriptVersion: vi.fn().mockResolvedValue(transcriptVersion),
    confirmTranscriptVersion: vi.fn().mockResolvedValue({
      attemptId: "attempt-1",
      confirmedAt: "2026-08-27T00:00:02Z",
      id: "confirmation-1",
      transcriptHash: transcriptVersion.transcriptHash,
      transcriptVersionId: transcriptVersion.id,
    }),
    requestNextHint: vi
      .fn()
      .mockResolvedValueOnce({
        conceptVersionId: "concept-version-1",
        content: [{ id: "hint-1", text: "Inspect point A.", type: "text" }],
        evaluationId: "evaluation-1",
        geometryActions: [{ objectIds: ["A"], type: "highlight" }],
        hintEventId: "hint-event-1",
        hintId: "hint-1",
        hintLevel: 1,
        releasedAt: "2026-08-27T00:00:04Z",
        revealsCompleteSolution: false,
      })
      .mockResolvedValueOnce({
        conceptVersionId: "concept-version-1",
        content: [{ id: "hint-2", latex: "M=\\frac{A+B}{2}", type: "display_math" }],
        evaluationId: "evaluation-1",
        geometryActions: [{ objectIds: ["M"], type: "focus" }],
        hintEventId: "hint-event-2",
        hintId: "hint-2",
        hintLevel: 2,
        releasedAt: "2026-08-27T00:00:05Z",
        revealsCompleteSolution: true,
      }),
  };
}

function mockSuccessfulUpload() {
  return vi
    .spyOn(globalThis, "fetch")
    .mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          expiresAt: "2026-08-27T00:05:00Z",
          uploadId: "upload-1",
          uploadUrl: "http://storage.test/upload",
        }),
      ),
    )
    .mockResolvedValueOnce(new Response(null, { status: 200 }))
    .mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          contentType: "image/png",
          createdAt: "2026-08-27T00:00:00Z",
          fileName: "synthetic-solution.png",
          id: "upload-1",
          sizeBytes: 4,
          status: "ready",
        }),
      ),
    );
}

async function reachReadyUpload(user: ReturnType<typeof userEvent.setup>) {
  await user.click(await screen.findByRole("button", { name: "Build today's combined plan" }));
  await user.click(await screen.findByRole("button", { name: "Open SYN-M4-GEO-001" }));
  await user.click(screen.getByRole("button", { name: "Upload a synthetic solution" }));
  await user.upload(
    screen.getByLabelText("Choose image"),
    new File([new Uint8Array([1, 2, 3, 4])], "synthetic-solution.png", {
      type: "image/png",
    }),
  );
  await user.click(screen.getByRole("button", { name: "Upload solution" }));
  return screen.findByRole("button", { name: "Use this upload" });
}

async function reachConfirmedTranscript(user: ReturnType<typeof userEvent.setup>) {
  mockSuccessfulUpload();
  await user.click(await reachReadyUpload(user));
  await screen.findByRole("heading", { name: "Review the transcript" });
  await user.click(screen.getByRole("button", { name: "Confirm exact transcript" }));
  return screen.findByRole("heading", { name: "Authoritative evaluation input" });
}

beforeEach(() => {
  Object.defineProperty(URL, "createObjectURL", {
    configurable: true,
    value: vi.fn(() => "blob:synthetic-preview"),
  });
  Object.defineProperty(URL, "revokeObjectURL", { configurable: true, value: vi.fn() });
});

afterEach(() => vi.restoreAllMocks());

describe("StaticStudentJourney", () => {
  it("renders every required phase and derives a deterministic complete summary", async () => {
    const api = createApi();
    const fetchMock = mockSuccessfulUpload();
    const user = userEvent.setup();
    render(<StaticStudentJourney api={api} />);

    expect(screen.getByText("Loading your study profile…")).toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: "Your study profile" })).toBeInTheDocument();
    expect(screen.getByText("Synthetic Aurora Mathematics Examination")).toBeInTheDocument();
    expect(screen.getByText("Synthetic Harbor Mathematics Examination")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Build today's combined plan" }));
    expect(
      await screen.findByRole("heading", { name: "Today's combined plan" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Supports 2 targets")).toBeInTheDocument();
    expect(screen.getByText("Supports 1 target")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Open SYN-M4-GEO-001" }));
    expect(await screen.findByRole("heading", { name: "SYN-M4-GEO-001" })).toBeInTheDocument();
    expect(screen.getByText("Pinned content version 1")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Upload a synthetic solution" }));

    await user.upload(
      screen.getByLabelText("Choose image"),
      new File([new Uint8Array([1, 2, 3, 4])], "synthetic-solution.png", { type: "image/png" }),
    );
    await user.click(screen.getByRole("button", { name: "Upload solution" }));
    await user.click(await screen.findByRole("button", { name: "Use this upload" }));

    expect(
      await screen.findByRole("heading", { name: "Review the transcript" }),
    ).toBeInTheDocument();
    expect(screen.getByText("A formula may need review.")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Show source region for block 1" }));
    expect(screen.getByRole("img", { name: "Selected transcript source region" })).toHaveStyle({
      height: "10%",
      left: "10%",
      top: "20%",
      width: "40%",
    });
    await user.click(screen.getByRole("button", { name: "Confirm exact transcript" }));
    expect(api.createTranscriptVersion).not.toHaveBeenCalled();

    expect(
      await screen.findByRole("heading", { name: "Authoritative evaluation input" }),
    ).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Evaluate confirmed work" }));
    expect(await screen.findByText("Deterministic synthetic feedback.")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Score 0.00 / 4.00" })).toBeInTheDocument();
    expect(screen.getByText("Root error")).toBeInTheDocument();
    expect(screen.getByText("Dependent error")).toBeInTheDocument();
    expect(screen.getByText(/Reference solutions are non-exhaustive/)).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Request hint 1" }));
    expect(await screen.findByRole("heading", { name: "Curated hints" })).toBeInTheDocument();
    expect(screen.getByText("Inspect point A.")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Request hint 2" }));
    expect(await screen.findByText("Hint 2")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Retry this problem" }));
    expect(await screen.findByRole("heading", { name: "New attempt ready" })).toBeInTheDocument();
    expect(screen.getByText("Attempt 2 · same immutable content version 1")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Study the linked concept" }));
    expect(
      await screen.findByRole("heading", { name: "Midpoint coordinates" }),
    ).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Complete session" }));

    expect(await screen.findByRole("heading", { name: "Session complete" })).toBeInTheDocument();
    expect(screen.getByText("2 active targets")).toBeInTheDocument();
    expect(screen.getByText("2 attempts")).toBeInTheDocument();
    expect(screen.getByText("Hints 1, 2")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });

  it("creates one profile and requires two active target records before planning", async () => {
    const api = createApi();
    api.getAvailableExamCycles = vi.fn().mockResolvedValue({
      items: profile.studentExamTargets.map((target) => ({
        cycleCode: `${target.examCode}-2027`,
        examCode: target.examCode,
        examDate: target.examDate,
        examId: target.examId,
        examName: target.examName,
        id: target.examCycleId,
        year: 2027,
      })),
    });
    api.getStudyProfile = vi
      .fn()
      .mockRejectedValue(new ApiError("profile_not_found", "Create a profile.", 404));
    api.createStudyProfile = vi.fn().mockResolvedValue({
      ...profile,
      studentExamTargets: [],
    });
    api.addExamTarget = vi
      .fn()
      .mockResolvedValueOnce(profile.studentExamTargets[0])
      .mockResolvedValueOnce(profile.studentExamTargets[1]);
    const user = userEvent.setup();
    render(<StaticStudentJourney api={api} />);

    await user.click(await screen.findByRole("button", { name: "Create study profile" }));
    expect(
      await screen.findByRole("heading", { name: "Add at least two active examination targets" }),
    ).toBeInTheDocument();
    await user.click(
      screen.getByRole("button", { name: "Add Synthetic Aurora Mathematics Examination" }),
    );
    expect(
      screen.queryByRole("button", { name: "Build today's combined plan" }),
    ).not.toBeInTheDocument();
    await user.click(
      screen.getByRole("button", { name: "Add Synthetic Harbor Mathematics Examination" }),
    );

    expect(
      await screen.findByRole("button", { name: "Build today's combined plan" }),
    ).toBeEnabled();
    expect(api.addExamTarget).toHaveBeenNthCalledWith(
      2,
      expect.objectContaining({ examCycleId: "cycle-2", priorityRank: 2 }),
    );
  });

  it("renders empty, retryable, and permanent states without inventing success", async () => {
    const retryApi = createApi();
    retryApi.getAvailableExamCycles = vi
      .fn()
      .mockRejectedValue(new ApiError("service_unavailable", "Try again soon.", 503));
    const { unmount } = render(<StaticStudentJourney api={retryApi} />);
    expect(await screen.findByText("Try again soon.")).toHaveAttribute("role", "alert");
    expect(screen.getByRole("button", { name: "Retry profile loading" })).toBeEnabled();
    unmount();

    const emptyApi = createApi();
    emptyApi.getStaticPlan = vi.fn().mockResolvedValue({ ...plan, items: [] });
    const user = userEvent.setup();
    const empty = render(<StaticStudentJourney api={emptyApi} />);
    await user.click(await screen.findByRole("button", { name: "Build today's combined plan" }));
    expect(
      await screen.findByRole("heading", { name: "No planned problems are available." }),
    ).toBeInTheDocument();
    empty.unmount();

    const permanentApi = createApi();
    permanentApi.getStaticPlan = vi
      .fn()
      .mockRejectedValue(
        new ApiError("evaluation_invalid_schema", "The payload remained invalid.", 502),
      );
    render(<StaticStudentJourney api={permanentApi} />);
    await user.click(await screen.findByRole("button", { name: "Build today's combined plan" }));
    expect(await screen.findByText("The payload remained invalid.")).toHaveAttribute(
      "role",
      "alert",
    );
    expect(
      screen.getByText("The application did not fabricate a replacement result."),
    ).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Retry this step" })).not.toBeInTheDocument();
  });

  it("shows complete-response loading and terminal uncertainty without a transcript", async () => {
    const api = createApi();
    type ApiTranscription = Awaited<ReturnType<StaticJourneyApi["requestTranscription"]>>;
    let resolveTranscription: ((value: ApiTranscription) => void) | undefined;
    api.requestTranscription = vi.fn<StaticJourneyApi["requestTranscription"]>(
      () =>
        new Promise<ApiTranscription>((resolve) => {
          resolveTranscription = resolve;
        }),
    );
    mockSuccessfulUpload();
    const user = userEvent.setup();
    render(<StaticStudentJourney api={api} />);

    await user.click(await reachReadyUpload(user));
    expect(
      await screen.findByText("Loading and validating the complete image transcription…"),
    ).toHaveAttribute("role", "status");

    resolveTranscription?.({
      outcome: "uncertain",
      run: { ...transcriptionRun, status: "uncertain" },
      warnings: [
        {
          blockId: null,
          code: "ordering_uncertain",
          message: "The reading order may need review.",
        },
      ],
    });

    expect(
      await screen.findByRole("heading", { name: "No transcript was created." }),
    ).toBeInTheDocument();
    expect(screen.getByText("The reading order may need review.")).toBeInTheDocument();
    expect(screen.queryByText("The synthetic midpoint is")).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Upload a clearer synthetic image" }));
    expect(screen.getByLabelText("Choose image")).toBeInTheDocument();
  });

  it("shows evaluation loading and a scoreless uncertainty result", async () => {
    const api = createApi();
    type ApiEvaluation = Awaited<ReturnType<StaticJourneyApi["requestEvaluation"]>>;
    let resolveEvaluation: ((value: ApiEvaluation) => void) | undefined;
    api.requestEvaluation = vi.fn<StaticJourneyApi["requestEvaluation"]>(
      () =>
        new Promise((resolve) => {
          resolveEvaluation = resolve;
        }),
    );
    const user = userEvent.setup();
    render(<StaticStudentJourney api={api} />);
    await reachConfirmedTranscript(user);

    await user.click(screen.getByRole("button", { name: "Evaluate confirmed work" }));
    expect(screen.getByText("Evaluating the confirmed transcript…")).toHaveAttribute(
      "role",
      "status",
    );
    resolveEvaluation?.({
      confirmedTranscriptVersionId: transcriptVersion.id,
      evaluationId: "evaluation-uncertain",
      outcome: "uncertain",
      reason: [{ id: "uncertain-reason", text: "The work is contradictory.", type: "text" }],
      recommendedAction: "manual_review",
      run: { ...evaluationRun, status: "uncertain" },
    });

    expect(
      await screen.findByRole("heading", { name: "Evaluation is uncertain" }),
    ).toBeInTheDocument();
    expect(screen.getByText("The work is contradictory.")).toBeInTheDocument();
    expect(screen.getByText(/No correctness claim or score was fabricated/)).toBeInTheDocument();
    expect(screen.queryByText(/Score /)).not.toBeInTheDocument();
  });

  it.each([
    {
      code: "evaluation_temporarily_unavailable",
      heading: "This step could not finish.",
      retryable: true,
      status: 503,
    },
    {
      code: "evaluation_permanent_failure",
      heading: "This step could not finish.",
      retryable: false,
      status: 502,
    },
    {
      code: "evaluation_invalid_schema",
      heading: "No evaluation result was accepted.",
      retryable: false,
      status: 502,
    },
  ])(
    "shows the terminal $code evaluation state without fabricated scoring",
    async ({ code, heading, retryable, status }) => {
      const api = createApi();
      api.requestEvaluation = vi
        .fn()
        .mockRejectedValue(new ApiError(code, "No evaluation result is available.", status));
      const user = userEvent.setup();
      render(<StaticStudentJourney api={api} />);
      await reachConfirmedTranscript(user);
      await user.click(screen.getByRole("button", { name: "Evaluate confirmed work" }));

      expect(await screen.findByRole("heading", { name: heading })).toBeInTheDocument();
      expect(screen.queryByText(/Score /)).not.toBeInTheDocument();
      if (retryable) {
        expect(screen.getByRole("button", { name: "Retry this step" })).toBeEnabled();
      } else {
        expect(
          screen.getByText("The application did not fabricate a replacement result."),
        ).toBeInTheDocument();
      }
    },
  );

  it.each([
    {
      code: "transcription_timeout",
      heading: "This step could not finish.",
      message: "Transcription timed out. Try again.",
      retryable: true,
      status: 503,
    },
    {
      code: "transcription_provider_rejected",
      heading: "This step could not finish.",
      message: "The transcription service rejected this image.",
      retryable: false,
      status: 502,
    },
    {
      code: "transcription_invalid_schema",
      heading: "No transcript was accepted.",
      message: "The transcription response was invalid after one retry.",
      retryable: false,
      status: 502,
    },
  ])(
    "renders the terminal $code transcription state without fabricated output",
    async ({ code, heading, message, retryable, status }) => {
      const api = createApi();
      api.requestTranscription = vi.fn().mockRejectedValue(new ApiError(code, message, status));
      mockSuccessfulUpload();
      const user = userEvent.setup();
      render(<StaticStudentJourney api={api} />);

      await user.click(await reachReadyUpload(user));

      expect(await screen.findByRole("heading", { name: heading })).toBeInTheDocument();
      expect(screen.getByText(message)).toHaveAttribute("role", "alert");
      expect(screen.queryByText("The synthetic midpoint is")).not.toBeInTheDocument();
      if (retryable) {
        expect(screen.getByRole("button", { name: "Retry this step" })).toBeEnabled();
      } else {
        expect(
          screen.getByText("The application did not fabricate a replacement result."),
        ).toBeInTheDocument();
      }
    },
  );
});
