import type { TranscriptState } from "./transcript-state";

export const SYNTHETIC_CORRECTION_TRANSCRIPT: TranscriptState = {
  attemptId: "synthetic-attempt-m3-001",
  blocks: [
    {
      id: "synthetic-text-1",
      text: "Factor the quadratic expression: ",
      type: "text",
    },
    {
      id: "synthetic-math-1",
      latex: "x^2-5x+6=(x-2)(x-3)",
      type: "math",
    },
    {
      id: "synthetic-text-2",
      text: ".\nSet each factor equal to zero: ",
      type: "text",
    },
    {
      id: "synthetic-math-invalid",
      latex: String.raw`\frac{PRIVATE_FIXTURE_SOURCE}{`,
      type: "math",
    },
    {
      id: "synthetic-text-3",
      text: ".\nThe two solutions are ",
      type: "text",
    },
    {
      id: "synthetic-math-3",
      latex: String.raw`x\in\{2,3\}`,
      type: "math",
    },
    {
      id: "synthetic-text-4",
      text: ".",
      type: "text",
    },
  ],
  schemaVersion: "2.0.0",
};
