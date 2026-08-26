import { afterEach, describe, expect, it, vi } from "vitest";

import {
  ApiError,
  getContentPreview,
  getContentPreviews,
  getCurrentUser,
  login,
  logout,
} from "./api";

const provenance = {
  acquiredBy: "Math Coach development",
  acquisitionDate: "2026-08-26",
  adaptationDescription: null,
  attributionText: "Original synthetic Math Coach fixture.",
  creator: "Math Coach fixture author",
  derivativeOf: [],
  mathematicsReviewedAt: "2026-08-26",
  mathematicsReviewer: "Synthetic fixture reviewer",
  permittedUses: ["internal_development"],
  publicationDate: "2026-08-26",
  publicationStatus: "synthetic_only",
  restrictions: ["not_real_exam_content"],
  rightsBasis: "original_fixture",
  rightsEvidence: "Created for testing.",
  rightsReviewedAt: "2026-08-26",
  rightsReviewer: "Synthetic fixture reviewer",
  sourceKind: "original_synthetic",
  sourceReference: "repo://synthetic",
  title: "Synthetic problem",
  translationDescription: null,
};

function validPreviewPayload(): object {
  return {
    difficultyBand: "core",
    estimatedMinutes: 12,
    externalCode: "SYN-M2-GEO-001",
    geometryScene: {
      accessibilityDescription: "A synthetic coordinate scene.",
      animationIds: ["move-M"],
      fallbackImageAssetId: "fallback-1",
      id: "scene-version-1",
      initialVisibleObjectIds: ["A", "B", "M"],
      objects: [
        { id: "A", label: "A", parents: [], type: "point", x: 0, y: 0 },
        { id: "B", label: null, parents: [], type: "point", x: 6, y: 0 },
        { id: "M", parents: ["A", "B"], type: "midpoint" },
      ],
      provenance,
      version: 1,
      viewport: { xMax: 7, xMin: -1, yMax: 5, yMin: -1 },
    },
    hints: [
      {
        conceptId: null,
        content: [{ id: "hint", text: "Inspect the scene.", type: "text" }],
        geometryActions: [
          { objectIds: ["M"], type: "show" },
          { objectIds: ["A"], type: "hide" },
          { objectIds: ["M"], type: "highlight" },
          { objectIds: ["A", "B"], type: "focus" },
          { type: "clear_highlight" },
          { animationId: "move-M", objectId: "M", type: "animate" },
          {
            allowedObjectIds: ["A", "B"],
            correctObjectIds: null,
            prompt: [{ id: "prompt", text: "Select an endpoint.", type: "text" }],
            type: "ask_select",
          },
        ],
        hintLevel: 1,
        id: "hint-1",
        revealsCompleteSolution: false,
      },
    ],
    maximumScore: "4.00",
    problemId: "problem-1",
    problemVersionId: "problem-version-1",
    provenance,
    referenceSolutions: [
      {
        content: [{ id: "solution", latex: "CM^2=17", type: "display_math" }],
        expertVerified: true,
        id: "solution-1",
        methodLabel: "Coordinate method",
        nonExhaustive: true,
        solutionCode: "coordinate",
      },
    ],
    rubric: [
      {
        description: [{ id: "rubric", text: "Find the midpoint.", type: "text" }],
        id: "rubric-1",
        maximumScore: "2.00",
        orderIndex: 1,
        rubricCode: "midpoint",
        skillId: "skill-1",
      },
    ],
    skills: [
      {
        importance: "1.00000",
        role: "primary",
        skillCode: "SYN-MIDPOINT",
        skillId: "skill-1",
        skillName: "Midpoint reasoning",
      },
    ],
    statement: [
      { id: "text", text: "Synthetic statement.", type: "text" },
      { id: "inline", latex: "AB", type: "inline_math" },
      { id: "display", latex: "AB=6", type: "display_math" },
      {
        id: "rich",
        spans: [
          { text: "Let ", type: "text" },
          { latex: "M", type: "math" },
        ],
        type: "rich_line",
      },
      { id: "geometry", sceneVersionId: "scene-version-1", type: "geometry" },
      { alt: "Synthetic fallback", assetId: "asset-1", id: "image", type: "image" },
      {
        content: [{ id: "nested", text: "Synthetic note.", type: "text" }],
        id: "callout",
        kind: "note",
        type: "callout",
      },
    ],
    supportedExams: [
      {
        cycleCode: "SYN-AURORA-2027",
        examCode: "SYN-AURORA",
        examCycleId: "cycle-1",
        examDate: "2027-06-01",
        examId: "exam-1",
        examName: "Synthetic Aurora Examination",
        relevanceLevel: "high",
        relevanceNote: "Synthetic shared practice.",
      },
    ],
    version: 1,
  };
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("API boundary", () => {
  it("validates a current-user response", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ displayName: "Internal learner", id: "user-1" })),
    );

    await expect(getCurrentUser()).resolves.toEqual({
      displayName: "Internal learner",
      id: "user-1",
    });
  });

  it("rejects a malformed success response", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ displayName: "Missing identifier" })),
    );

    await expect(getCurrentUser()).rejects.toMatchObject({
      code: "invalid_response",
      status: 502,
    });
  });

  it("preserves a stable API error", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({ error: { code: "invalid_invite", message: "That invite is not valid." } }),
        { status: 401 },
      ),
    );

    await expect(login("wrong-code")).rejects.toEqual(
      new ApiError("invalid_invite", "That invite is not valid.", 401),
    );
  });

  it("uses a safe fallback for a non-JSON upstream error", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response("not-json", { status: 502 }));

    await expect(getCurrentUser()).rejects.toMatchObject({
      code: "request_failed",
      message: "Something went wrong. Try again.",
      status: 502,
    });
  });

  it("accepts an empty successful logout response", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(new Response(null, { status: 204 }));

    await expect(logout()).resolves.toBeUndefined();
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/auth/logout",
      expect.objectContaining({ credentials: "same-origin", method: "POST" }),
    );
  });

  it("validates the internal content-preview collection", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          items: [
            {
              externalCode: "SYN-M2-GEO-001",
              problemId: "problem-1",
              problemVersionId: "problem-version-1",
              supportedExamCount: 2,
              version: 1,
            },
          ],
        }),
      ),
    );

    await expect(getContentPreviews()).resolves.toMatchObject({
      items: [{ externalCode: "SYN-M2-GEO-001", supportedExamCount: 2 }],
    });
  });

  it("validates every typed preview block and curated geometry action", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify(validPreviewPayload())),
    );

    const result = await getContentPreview("problem-1");

    expect(result).toMatchObject({
      externalCode: "SYN-M2-GEO-001",
      geometryScene: { version: 1 },
    });
    expect(result.statement).toEqual(
      expect.arrayContaining([expect.objectContaining({ id: "geometry", type: "geometry" })]),
    );
  });

  it("rejects malformed typed blocks in a content preview", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          ...validPreviewPayload(),
          geometryScene: null,
          statement: [{ id: "bad", text: 42, type: "text" }],
        }),
      ),
    );

    await expect(getContentPreview("problem-1")).rejects.toMatchObject({
      code: "invalid_response",
      status: 502,
    });
  });
});
