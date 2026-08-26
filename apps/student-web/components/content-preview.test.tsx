import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { ContentPreview as ContentPreviewData } from "../lib/api";
import { ContentPreview } from "./content-preview";

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
    id: "scene-version-1",
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
    { id: "scene", sceneVersionId: "scene-version-1", type: "geometry" },
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
  it("renders typed content, multi-exam relevance, provenance, and non-exhaustive references", () => {
    render(<ContentPreview preview={preview} />);

    expect(screen.getByRole("heading", { name: "SYN-M2-GEO-001" })).toBeInTheDocument();
    expect(screen.getByText("SYN-AURORA-2027")).toBeInTheDocument();
    expect(screen.getByText("SYN-HARBOR-2027")).toBeInTheDocument();
    expect(screen.getByText("Reference solutions are non-exhaustive.")).toBeInTheDocument();
    expect(screen.getByText("A coordinate triangle with midpoint M.")).toBeInTheDocument();
    expect(screen.getByText("Original synthetic Math Coach fixture.")).toBeInTheDocument();
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
});
