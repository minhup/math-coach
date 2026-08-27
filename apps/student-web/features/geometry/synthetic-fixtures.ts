import type { components } from "@math-coach/api-client";

export type GeometryScene = components["schemas"]["GeometrySceneVersion"];
export type GeometryAction =
  components["schemas"]["ContentPreviewResponse"]["hints"][number]["geometryActions"][number];

const provenance: components["schemas"]["Provenance"] = {
  sourceKind: "original_synthetic",
  title: "Synthetic Milestone 4 geometry scene",
  creator: "Math Coach fixture author",
  sourceReference: "repo://content/synthetic-m4-geometry-v1",
  acquisitionDate: "2026-08-27",
  acquiredBy: "Math Coach development",
  rightsBasis: "original_fixture",
  rightsEvidence: "Created solely for Milestone 4 automated testing.",
  permittedUses: ["internal_development", "automated_testing"],
  restrictions: ["not_real_exam_content"],
  attributionText: "Original synthetic Math Coach fixture.",
  adaptationDescription: null,
  translationDescription: null,
  derivativeOf: [],
  mathematicsReviewer: "Synthetic fixture reviewer",
  mathematicsReviewedAt: "2026-08-27",
  rightsReviewer: "Synthetic fixture reviewer",
  rightsReviewedAt: "2026-08-27",
  publicationStatus: "synthetic_only",
  publicationDate: "2026-08-27",
};

export const syntheticGeometryScene: GeometryScene = {
  id: "40000000-0000-4000-8000-000000000501",
  version: 1,
  viewport: { xMin: -5, xMax: 8, yMin: -5, yMax: 7 },
  objects: [
    { id: "labelM", type: "label", parents: ["M"], label: "Midpoint M" },
    { id: "circumABC", type: "circumcircle", parents: ["A", "B", "C"] },
    { id: "parallelC", type: "parallel", parents: ["base", "C"] },
    { id: "perpendicularC", type: "perpendicular", parents: ["base", "C"] },
    {
      id: "I",
      type: "intersection",
      parents: ["base", "circleA"],
      intersectionIndex: 0,
      label: "I",
      selectable: true,
    },
    { id: "M", type: "midpoint", parents: ["A", "B"], label: "M" },
    { id: "angleBAC", type: "angle", parents: ["B", "A", "C"] },
    { id: "triangle", type: "polygon", parents: ["A", "B", "C"] },
    { id: "arcABC", type: "arc", parents: ["A", "B", "C"] },
    { id: "circleA", type: "circle", parents: ["A", "C"] },
    { id: "rayAC", type: "ray", parents: ["A", "C"] },
    { id: "base", type: "line", parents: ["A", "B"] },
    { id: "segmentAB", type: "segment", parents: ["A", "B"] },
    { id: "C", type: "point", x: 1, y: 3, label: "C", selectable: true },
    { id: "B", type: "point", x: 6, y: 0, label: "B", selectable: true },
    {
      id: "A",
      type: "point",
      x: 0,
      y: 0,
      label: "A",
      draggable: true,
      selectable: true,
    },
  ],
  initialVisibleObjectIds: [
    "A",
    "B",
    "C",
    "segmentAB",
    "base",
    "rayAC",
    "circleA",
    "arcABC",
    "triangle",
    "angleBAC",
    "M",
    "I",
    "perpendicularC",
    "parallelC",
    "circumABC",
    "labelM",
  ],
  animationIds: ["pulse-A"],
  fallbackImageAssetId: "synthetic-m4-geometry-fallback",
  accessibilityDescription:
    "A synthetic coordinate construction containing three free points and examples of every approved geometry primitive.",
  provenance,
};

export const syntheticGeometryActions: readonly GeometryAction[] = [
  { type: "show", objectIds: ["labelM"] },
  { type: "hide", objectIds: ["labelM"] },
  { type: "highlight", objectIds: ["A", "B"] },
  { type: "clear_highlight", objectIds: null },
  { type: "focus", objectIds: ["triangle"] },
  { type: "animate", objectId: "A", animationId: "pulse-A" },
  {
    type: "ask_select",
    prompt: [{ id: "select-a-prompt", type: "text", text: "Select point A." }],
    allowedObjectIds: ["A", "B"],
    correctObjectIds: ["A"],
  },
];

export function cloneSyntheticGeometryScene(): unknown {
  return structuredClone(syntheticGeometryScene);
}
