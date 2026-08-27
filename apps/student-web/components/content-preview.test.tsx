import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { ContentPreview as ContentPreviewData } from "../lib/api";
import { ContentPreview } from "./content-preview";

const graph = vi.hoisted(() => {
  const create = vi.fn((type: string, parents: unknown[]) => {
    const coordinates = type === "point" ? (parents as number[]) : [0, 0];
    const element = {
      on: vi.fn(() => element),
      setAttribute: vi.fn(() => element),
      X: () => coordinates[0] ?? 0,
      Y: () => coordinates[1] ?? 0,
    };
    return element;
  });
  return {
    create,
    freeBoard: vi.fn(),
    initBoard: vi.fn(() => ({ create, update: vi.fn() })),
  };
});

vi.mock("jsxgraph", () => ({
  default: { JSXGraph: { initBoard: graph.initBoard, freeBoard: graph.freeBoard } },
}));

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
  publicationStatus: "synthetic_only" as const,
  restrictions: ["not_real_exam_content"],
  rightsBasis: "original_fixture" as const,
  rightsEvidence: "Created for testing.",
  rightsReviewedAt: "2026-08-26",
  rightsReviewer: "Synthetic fixture reviewer",
  sourceKind: "original_synthetic" as const,
  sourceReference: "repo://synthetic",
  title: "Synthetic problem",
  translationDescription: null,
};

const preview: ContentPreviewData = {
  difficultyBand: "core",
  estimatedMinutes: 12,
  externalCode: "SYN-M2-GEO-001",
  geometryScene: {
    accessibilityDescription: "A coordinate triangle with midpoint M.",
    animationIds: [],
    fallbackImageAssetId: "synthetic-fallback",
    id: "10000000-0000-4000-8000-000000000501",
    initialVisibleObjectIds: ["A", "B", "M"],
    objects: [
      { id: "A", label: "A", parents: [], type: "point", x: 0, y: 0 },
      { id: "B", label: "B", parents: [], type: "point", x: 6, y: 0 },
      { id: "M", label: "M", parents: ["A", "B"], type: "midpoint" },
    ],
    provenance,
    version: 1,
    viewport: { xMax: 7, xMin: -1, yMax: 5, yMin: -1 },
  },
  hints: [
    {
      conceptId: null,
      content: [{ id: "hint-1", text: "Start with the midpoint.", type: "text" }],
      geometryActions: [{ objectIds: ["M"], type: "highlight" }],
      hintLevel: 1,
      id: "hint-id-1",
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
      description: [{ id: "rubric", text: "Find M.", type: "text" }],
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
    { id: "text", text: "This fixture is synthetic.", type: "text" },
    { id: "inline", latex: "AB", type: "inline_math" },
    {
      id: "statement",
      spans: [
        { text: "Let ", type: "text" },
        { latex: "M", type: "math" },
        { text: " be the midpoint.", type: "text" },
      ],
      type: "rich_line",
    },
    {
      id: "scene",
      sceneVersionId: "10000000-0000-4000-8000-000000000501",
      type: "geometry",
    },
    { alt: "Synthetic diagram fallback", assetId: "asset-1", id: "image", type: "image" },
    {
      content: [{ id: "callout-math", latex: "AM=MB", type: "inline_math" }],
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
    {
      cycleCode: "SYN-HARBOR-2027",
      examCode: "SYN-HARBOR",
      examCycleId: "cycle-2",
      examDate: "2027-06-15",
      examId: "exam-2",
      examName: "Synthetic Harbor Examination",
      relevanceLevel: "high",
      relevanceNote: "Synthetic shared practice.",
    },
  ],
  version: 1,
};

describe("ContentPreview", () => {
  it("renders typed content, live geometry, multi-exam relevance, provenance, and non-exhaustive references", async () => {
    render(<ContentPreview preview={preview} />);

    expect(screen.getByRole("heading", { name: "SYN-M2-GEO-001" })).toBeInTheDocument();
    expect(screen.getByText("SYN-AURORA-2027")).toBeInTheDocument();
    expect(screen.getByText("SYN-HARBOR-2027")).toBeInTheDocument();
    expect(screen.getByText("Reference solutions are non-exhaustive.")).toBeInTheDocument();
    expect(screen.getAllByText("A coordinate triangle with midpoint M.")).toHaveLength(2);
    expect(screen.getByText("Original synthetic Math Coach fixture.")).toBeInTheDocument();
    expect(await screen.findByLabelText("Interactive geometry")).toBeInTheDocument();
    expect(screen.queryByText(/Curated geometry scene version:/)).not.toBeInTheDocument();
    expect(document.querySelector("script")).toBeNull();
  });

  it("renders a version without optional geometry and without hint actions", () => {
    render(
      <ContentPreview
        preview={{
          ...preview,
          geometryScene: null,
          hints: [{ ...preview.hints[0], geometryActions: [] }],
        }}
      />,
    );

    expect(screen.queryByRole("heading", { name: "Curated geometry scene" })).toBeNull();
    expect(screen.queryByText(/validated geometry action/)).toBeNull();
    expect(screen.getByText("Synthetic diagram fallback")).toBeInTheDocument();
  });

  it("keeps invalid typed mathematics source-free and correctable", async () => {
    const untrustedSource = String.raw`\frac{PRIVATE_PREVIEW_SOURCE}{`;
    const { container } = render(
      <ContentPreview
        preview={{
          ...preview,
          statement: [{ id: "invalid-math", latex: untrustedSource, type: "display_math" }],
        }}
      />,
    );

    expect(await screen.findByRole("img", { name: "Math needs correction" })).toBeInTheDocument();
    expect(container.innerHTML).not.toContain("PRIVATE_PREVIEW_SOURCE");
    expect(container.innerHTML).not.toContain("\\frac");
  });

  it("renders a Vietnamese mixed text and mathematics line as typed spans", async () => {
    render(
      <ContentPreview
        preview={{
          ...preview,
          statement: [
            {
              id: "mixed-vietnamese",
              spans: [
                { text: "Với ", type: "text" },
                { latex: "x^2=4", type: "math" },
                { text: ", ta có hai nghiệm.", type: "text" },
              ],
              type: "rich_line",
            },
          ],
        }}
      />,
    );

    expect(screen.getByText(/Với/)).toBeInTheDocument();
    expect(screen.getByText(/ta có hai nghiệm/)).toBeInTheDocument();
    expect(await screen.findByLabelText("Inline mathematics")).toHaveAttribute(
      "data-math-render-state",
      "rendered",
    );
  });
});
