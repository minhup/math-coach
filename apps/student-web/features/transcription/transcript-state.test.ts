import { describe, expect, it } from "vitest";

import {
  addBlock,
  confirmTranscript,
  deleteBlock,
  mergeStepWithPrevious,
  moveBlock,
  moveStep,
  splitStep,
  type TranscriptState,
  updateBlockValue,
  validateTranscriptState,
} from "./transcript-state";

const initialState: TranscriptState = {
  attemptId: "synthetic-attempt-001",
  blocks: [
    { id: "block-text-1", stepId: "step-1", text: "Let x be positive.", type: "text" },
    { id: "block-math-1", latex: "x^2=4", stepId: "step-1", type: "math" },
    { id: "block-text-2", stepId: "step-2", text: "Therefore", type: "text" },
    { id: "block-math-2", latex: "x=2", stepId: "step-2", type: "math" },
    { id: "block-text-3", stepId: "step-3", text: "Check the result.", type: "text" },
  ],
  schemaVersion: "1.0.0",
  steps: [
    { blockIds: ["block-text-1", "block-math-1"], id: "step-1" },
    { blockIds: ["block-text-2", "block-math-2"], id: "step-2" },
    { blockIds: ["block-text-3"], id: "step-3" },
  ],
};

function expectInvalid(state: TranscriptState, message: RegExp) {
  expect(() => validateTranscriptState(state)).toThrow(message);
}

describe("validateTranscriptState", () => {
  it("accepts a valid typed, ordered transcript", () => {
    expect(validateTranscriptState(initialState)).toBe(initialState);
  });

  it("rejects duplicate, empty, unknown, repeated, orphaned, and mismatched identities", () => {
    expectInvalid(
      { ...initialState, blocks: [...initialState.blocks, initialState.blocks[0]] },
      /duplicate block ID/i,
    );
    expectInvalid(
      { ...initialState, steps: [...initialState.steps, initialState.steps[0]] },
      /duplicate step ID/i,
    );
    expectInvalid(
      { ...initialState, steps: [{ blockIds: [], id: "empty-step" }, ...initialState.steps] },
      /at least one block/i,
    );
    expectInvalid(
      {
        ...initialState,
        steps: [{ blockIds: ["unknown-block"], id: "step-unknown" }, ...initialState.steps],
      },
      /unknown block/i,
    );
    expectInvalid(
      {
        ...initialState,
        steps: initialState.steps.map((step) =>
          step.id === "step-2" ? { ...step, blockIds: [...step.blockIds, "block-math-1"] } : step,
        ),
      },
      /more than once/i,
    );
    expectInvalid(
      {
        ...initialState,
        blocks: [
          ...initialState.blocks,
          { id: "orphan", stepId: "step-1", text: "Lost", type: "text" },
        ],
      },
      /orphaned block/i,
    );
    expectInvalid(
      {
        ...initialState,
        blocks: initialState.blocks.map((block) =>
          block.id === "block-math-1" ? { ...block, stepId: "step-2" } : block,
        ),
      },
      /ownership/i,
    );
    expectInvalid(
      { ...initialState, blocks: [{ ...initialState.blocks[0], id: " " }] },
      /non-empty block ID/i,
    );
    expectInvalid({ ...initialState, steps: [] }, /at least one step/i);
  });
});

describe("block operations", () => {
  it("adds text and math at explicit positions without mutating input", () => {
    const withText = addBlock(initialState, {
      block: { id: "block-text-new", stepId: "step-1", text: "Suppose", type: "text" },
      index: 0,
      stepId: "step-1",
    });
    const withMath = addBlock(withText, {
      block: { id: "block-math-new", latex: "x>0", stepId: "step-1", type: "math" },
      index: 2,
      stepId: "step-1",
    });

    expect(initialState.steps[0].blockIds).toEqual(["block-text-1", "block-math-1"]);
    expect(withMath.steps[0].blockIds).toEqual([
      "block-text-new",
      "block-text-1",
      "block-math-new",
      "block-math-1",
    ]);
    expect(withMath.blocks.at(-1)).toEqual({
      id: "block-math-new",
      latex: "x>0",
      stepId: "step-1",
      type: "math",
    });
    expect(validateTranscriptState(withMath)).toBe(withMath);
  });

  it("rejects duplicate IDs, unknown steps, mismatched ownership, and invalid positions", () => {
    expect(() =>
      addBlock(initialState, {
        block: { id: "block-text-1", stepId: "step-1", text: "Duplicate", type: "text" },
        index: 0,
        stepId: "step-1",
      }),
    ).toThrow(/duplicate block ID/i);
    expect(() =>
      addBlock(initialState, {
        block: { id: "new", stepId: "unknown", text: "Unknown", type: "text" },
        index: 0,
        stepId: "unknown",
      }),
    ).toThrow(/unknown step/i);
    expect(() =>
      addBlock(initialState, {
        block: { id: "new", stepId: "step-2", text: "Mismatch", type: "text" },
        index: 0,
        stepId: "step-1",
      }),
    ).toThrow(/ownership/i);
    expect(() =>
      addBlock(initialState, {
        block: { id: "new", stepId: "step-1", text: "Too far", type: "text" },
        index: 3,
        stepId: "step-1",
      }),
    ).toThrow(/position/i);
  });

  it("deletes one block and rejects deletion of a step's only block", () => {
    const next = deleteBlock(initialState, "block-text-2");

    expect(next.blocks.map(({ id }) => id)).not.toContain("block-text-2");
    expect(next.steps[1].blockIds).toEqual(["block-math-2"]);
    expect(initialState.steps[1].blockIds).toEqual(["block-text-2", "block-math-2"]);
    expect(() => deleteBlock(initialState, "block-text-3")).toThrow(/only block/i);
    expect(() => deleteBlock(initialState, "unknown")).toThrow(/unknown block/i);
  });

  it("moves blocks only within their owning step and rejects boundaries", () => {
    const down = moveBlock(initialState, "block-text-1", "down");
    expect(down.steps[0].blockIds).toEqual(["block-math-1", "block-text-1"]);
    expect(moveBlock(down, "block-text-1", "up").steps[0].blockIds).toEqual(
      initialState.steps[0].blockIds,
    );
    expect(() => moveBlock(initialState, "block-text-1", "up")).toThrow(/already first/i);
    expect(() => moveBlock(initialState, "block-math-1", "down")).toThrow(/already last/i);
  });

  it("updates only the matching typed value and preserves the block variant", () => {
    const text = updateBlockValue(initialState, "block-text-1", "Assume x is positive.");
    const math = updateBlockValue(text, "block-math-1", String.raw`\sqrt{x}=2`);

    expect(text.blocks[0]).toEqual({
      id: "block-text-1",
      stepId: "step-1",
      text: "Assume x is positive.",
      type: "text",
    });
    expect(math.blocks[1]).toEqual({
      id: "block-math-1",
      latex: String.raw`\sqrt{x}=2`,
      stepId: "step-1",
      type: "math",
    });
    expect(initialState.blocks[0]).not.toBe(text.blocks[0]);
  });
});

describe("step operations", () => {
  it("splits before a middle block while preserving order, IDs, and ownership", () => {
    const next = splitStep(initialState, {
      beforeBlockId: "block-math-1",
      newStepId: "step-1b",
      stepId: "step-1",
    });

    expect(next.steps.slice(0, 2)).toEqual([
      { blockIds: ["block-text-1"], id: "step-1" },
      { blockIds: ["block-math-1"], id: "step-1b" },
    ]);
    expect(next.blocks.find(({ id }) => id === "block-text-1")?.stepId).toBe("step-1");
    expect(next.blocks.find(({ id }) => id === "block-math-1")?.stepId).toBe("step-1b");
    expect(initialState.blocks[1].stepId).toBe("step-1");
  });

  it("rejects invalid split boundaries and duplicate new step IDs", () => {
    expect(() =>
      splitStep(initialState, {
        beforeBlockId: "block-text-1",
        newStepId: "step-new",
        stepId: "step-1",
      }),
    ).toThrow(/first block/i);
    expect(() =>
      splitStep(initialState, {
        beforeBlockId: "block-text-3",
        newStepId: "step-new",
        stepId: "step-1",
      }),
    ).toThrow(/does not belong/i);
    expect(() =>
      splitStep(initialState, {
        beforeBlockId: "block-math-1",
        newStepId: "step-2",
        stepId: "step-1",
      }),
    ).toThrow(/duplicate step ID/i);
  });

  it("merges with the previous step and preserves leading then trailing order", () => {
    const next = mergeStepWithPrevious(initialState, "step-2");

    expect(next.steps).toEqual([
      {
        blockIds: ["block-text-1", "block-math-1", "block-text-2", "block-math-2"],
        id: "step-1",
      },
      { blockIds: ["block-text-3"], id: "step-3" },
    ]);
    expect(next.blocks.find(({ id }) => id === "block-text-2")?.stepId).toBe("step-1");
    expect(next.blocks.find(({ id }) => id === "block-math-2")?.stepId).toBe("step-1");
    expect(() => mergeStepWithPrevious(initialState, "step-1")).toThrow(/first step/i);
  });

  it("moves adjacent steps without changing internal block order", () => {
    const up = moveStep(initialState, "step-2", "up");
    expect(up.steps.map(({ id }) => id)).toEqual(["step-2", "step-1", "step-3"]);
    expect(up.steps[0].blockIds).toEqual(["block-text-2", "block-math-2"]);
    expect(moveStep(up, "step-2", "down").steps).toEqual(initialState.steps);
    expect(() => moveStep(initialState, "step-1", "up")).toThrow(/already first/i);
    expect(() => moveStep(initialState, "step-3", "down")).toThrow(/already last/i);
  });
});

describe("confirmTranscript", () => {
  it("serializes exact visible order deterministically into an independent typed snapshot", () => {
    const reordered = moveBlock(moveStep(initialState, "step-2", "up"), "block-text-1", "down");
    const first = confirmTranscript(reordered);
    const second = confirmTranscript(reordered);

    expect(first).toEqual({
      attemptId: "synthetic-attempt-001",
      blocks: [
        { id: "block-text-2", stepId: "step-2", text: "Therefore", type: "text" },
        { id: "block-math-2", latex: "x=2", stepId: "step-2", type: "math" },
        { id: "block-math-1", latex: "x^2=4", stepId: "step-1", type: "math" },
        { id: "block-text-1", stepId: "step-1", text: "Let x be positive.", type: "text" },
        { id: "block-text-3", stepId: "step-3", text: "Check the result.", type: "text" },
      ],
      schemaVersion: "1.0.0",
      steps: [
        { blockIds: ["block-text-2", "block-math-2"], id: "step-2" },
        { blockIds: ["block-math-1", "block-text-1"], id: "step-1" },
        { blockIds: ["block-text-3"], id: "step-3" },
      ],
    });
    expect(JSON.stringify(first)).toBe(JSON.stringify(second));

    first.steps[0].blockIds[0] = "changed-after-confirmation";
    const firstText = first.blocks.find((block) => block.type === "text");
    if (firstText !== undefined) {
      firstText.text = "changed after confirmation";
    }
    expect(reordered.steps[0].blockIds[0]).toBe("block-text-2");
    expect(reordered.blocks.find(({ id }) => id === "block-text-2")).toMatchObject({
      text: "Therefore",
    });
  });
});
