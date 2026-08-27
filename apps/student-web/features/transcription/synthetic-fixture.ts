import type { TranscriptState } from "./transcript-state";

export const SYNTHETIC_CORRECTION_TRANSCRIPT: TranscriptState = {
  attemptId: "synthetic-attempt-m3-001",
  blocks: [
    {
      id: "synthetic-text-1",
      stepId: "synthetic-step-1",
      text: "Factor the quadratic expression.",
      type: "text",
    },
    {
      id: "synthetic-math-1",
      latex: "x^2-5x+6=(x-2)(x-3)",
      stepId: "synthetic-step-1",
      type: "math",
    },
    {
      id: "synthetic-text-2",
      stepId: "synthetic-step-2",
      text: "Set each factor equal to zero.",
      type: "text",
    },
    {
      id: "synthetic-math-invalid",
      latex: String.raw`\frac{PRIVATE_FIXTURE_SOURCE}{`,
      stepId: "synthetic-step-2",
      type: "math",
    },
    {
      id: "synthetic-text-3",
      stepId: "synthetic-step-3",
      text: "The two solutions are shown below.",
      type: "text",
    },
    {
      id: "synthetic-math-3",
      latex: String.raw`x\in\{2,3\}`,
      stepId: "synthetic-step-3",
      type: "math",
    },
  ],
  schemaVersion: "1.0.0",
  steps: [
    { blockIds: ["synthetic-text-1", "synthetic-math-1"], id: "synthetic-step-1" },
    {
      blockIds: ["synthetic-text-2", "synthetic-math-invalid"],
      id: "synthetic-step-2",
    },
    { blockIds: ["synthetic-text-3", "synthetic-math-3"], id: "synthetic-step-3" },
  ],
};
