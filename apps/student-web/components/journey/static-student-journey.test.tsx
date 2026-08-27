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

const metadata = {
  costUsd: "0.000000",
  inputTokens: 0 as const,
  latencyMs: 0,
  modelSnapshot: "m5-static-fixture-v1" as const,
  outputTokens: 0 as const,
  promptVersion: "m5-no-provider-prompt-v1" as const,
  provider: "application-owned-synthetic-mock" as const,
  schemaVersion: "1.0.0" as const,
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
    requestMockEvaluation: vi.fn().mockResolvedValue({
      feedback: [{ id: "feedback", text: "Deterministic synthetic feedback.", type: "text" }],
      metadata,
      nextSteps: [{ id: "next", text: "Request a curated hint.", type: "text" }],
      outcome: "uncertain",
      referenceSolutionsNonExhaustive: true,
      transcriptFingerprint: "a".repeat(64),
    }),
    requestMockTranscription: vi.fn().mockResolvedValue({
      metadata,
      transcript: {
        attemptId: "attempt-1",
        blocks: [
          { id: "text-1", text: "The synthetic midpoint is ", type: "text" },
          { id: "math-1", latex: "M=(2,0", type: "math" },
        ],
        schemaVersion: "2.0.0",
      },
    }),
    requestNextHint: vi
      .fn()
      .mockResolvedValueOnce({
        conceptVersionId: "concept-version-1",
        content: [{ id: "hint-1", text: "Inspect point A.", type: "text" }],
        geometryActions: [{ objectIds: ["A"], type: "highlight" }],
        hintId: "hint-1",
        hintLevel: 1,
        revealsCompleteSolution: false,
      })
      .mockResolvedValueOnce({
        conceptVersionId: "concept-version-1",
        content: [{ id: "hint-2", latex: "M=\\frac{A+B}{2}", type: "display_math" }],
        geometryActions: [{ objectIds: ["M"], type: "focus" }],
        hintId: "hint-2",
        hintLevel: 2,
        revealsCompleteSolution: true,
      }),
  };
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
    const fetchMock = vi
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
    await user.click(screen.getByRole("button", { name: "Confirm transcript" }));

    expect(
      await screen.findByRole("heading", { name: "Authoritative evaluation input" }),
    ).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Evaluate confirmed transcript" }));
    expect(await screen.findByText("Deterministic synthetic feedback.")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Evaluation is uncertain" })).toBeInTheDocument();
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
        new ApiError("mock_payload_invalid", "The payload remained invalid.", 502),
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
});
