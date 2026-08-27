import { describe, expect, it } from "vitest";

import {
  addBlock,
  confirmTranscript,
  deleteBlock,
  deleteMathBlock,
  insertMathAtTextOffset,
  moveBlock,
  type TranscriptState,
  updateBlockValue,
  validateTranscriptState,
} from "./transcript-state";

const initialState: TranscriptState = {
  attemptId: "synthetic-attempt-001",
  blocks: [
    { id: "block-text-1", text: "Let x be positive.", type: "text" },
    { id: "block-math-1", latex: "x^2=4", type: "math" },
    { id: "block-text-2", text: "Therefore", type: "text" },
    { id: "block-math-2", latex: "x=2", type: "math" },
  ],
  schemaVersion: "3.0.0",
  warnings: [],
};

describe("flat transcript state", () => {
  it("confirms the exact visible mixed-block order without reasoning steps", () => {
    expect(validateTranscriptState(initialState)).toBe(initialState);

    const snapshot = confirmTranscript(initialState);
    expect(snapshot).toEqual({
      attemptId: "synthetic-attempt-001",
      blocks: [
        { id: "block-text-1", text: "Let x be positive.", type: "text" },
        { id: "block-math-1", latex: "x^2=4", type: "math" },
        { id: "block-text-2", text: "Therefore", type: "text" },
        { id: "block-math-2", latex: "x=2", type: "math" },
      ],
      schemaVersion: "3.0.0",
      warnings: [],
    });
    expect(snapshot).not.toHaveProperty("steps");
    expect(snapshot.blocks.every((block) => !("stepId" in block))).toBe(true);

    snapshot.blocks[0] = { id: "changed", text: "Changed after confirmation", type: "text" };
    expect(initialState.blocks[0]).toEqual({
      id: "block-text-1",
      text: "Let x be positive.",
      type: "text",
    });
  });

  it("rejects invalid document and block identities", () => {
    expect(() => validateTranscriptState({ ...initialState, attemptId: " " })).toThrow(
      /non-empty attempt ID/i,
    );
    expect(() => validateTranscriptState({ ...initialState, blocks: [] })).toThrow(
      /at least one block/i,
    );
    expect(() =>
      validateTranscriptState({
        ...initialState,
        blocks: [{ id: " ", text: "Missing identity", type: "text" }],
      }),
    ).toThrow(/non-empty block ID/i);
    expect(() =>
      validateTranscriptState({
        ...initialState,
        blocks: [...initialState.blocks, { ...initialState.blocks[0] }],
      }),
    ).toThrow(/duplicate block ID/i);
    const unsupportedVersion = { ...initialState, schemaVersion: "1.0.0" };
    expect(() => {
      // @ts-expect-error This deliberately malformed boundary value must be rejected at runtime.
      validateTranscriptState(unsupportedVersion);
    }).toThrow(/unsupported transcript schema version/i);
  });

  it("adds typed blocks at explicit document positions without mutating input", () => {
    const withText = addBlock(initialState, {
      block: { id: "block-text-new", text: "Suppose", type: "text" },
      index: 0,
    });
    const withMath = addBlock(withText, {
      block: { id: "block-math-new", latex: "x>0", type: "math" },
      index: 2,
    });

    expect(initialState.blocks.map(({ id }) => id)).toEqual([
      "block-text-1",
      "block-math-1",
      "block-text-2",
      "block-math-2",
    ]);
    expect(withMath.blocks.map(({ id }) => id)).toEqual([
      "block-text-new",
      "block-text-1",
      "block-math-new",
      "block-math-1",
      "block-text-2",
      "block-math-2",
    ]);
    expect(() =>
      addBlock(initialState, {
        block: { id: "block-text-1", text: "Duplicate", type: "text" },
        index: 0,
      }),
    ).toThrow(/duplicate block ID/i);
    expect(() =>
      addBlock(initialState, {
        block: { id: "block-too-far", text: "Too far", type: "text" },
        index: initialState.blocks.length + 1,
      }),
    ).toThrow(/position/i);
  });

  it("deletes a block without references and keeps one correctable block", () => {
    const next = deleteBlock(initialState, "block-text-2");

    expect(next.blocks.map(({ id }) => id)).toEqual([
      "block-text-1",
      "block-math-1",
      "block-math-2",
    ]);
    expect(initialState.blocks.map(({ id }) => id)).toContain("block-text-2");
    expect(() => deleteBlock(initialState, "unknown")).toThrow(/unknown block/i);
    expect(() =>
      deleteBlock(
        {
          attemptId: "one-block",
          blocks: [{ id: "only-block", text: "Keep me", type: "text" }],
          schemaVersion: "3.0.0",
          warnings: [],
        },
        "only-block",
      ),
    ).toThrow(/only block/i);
  });

  it("reorders adjacent blocks across the continuous document", () => {
    const moved = moveBlock(initialState, "block-text-2", "up");

    expect(moved.blocks.map(({ id }) => id)).toEqual([
      "block-text-1",
      "block-text-2",
      "block-math-1",
      "block-math-2",
    ]);
    expect(moveBlock(moved, "block-text-2", "down").blocks).toEqual(initialState.blocks);
    expect(() => moveBlock(initialState, "block-text-1", "up")).toThrow(/already first/i);
    expect(() => moveBlock(initialState, "block-math-2", "down")).toThrow(/already last/i);
  });

  it("updates one typed value without changing its block variant", () => {
    const text = updateBlockValue(initialState, "block-text-1", "Assume x is positive.");
    const math = updateBlockValue(text, "block-math-1", String.raw`\sqrt{x}=2`);

    expect(text.blocks[0]).toEqual({
      id: "block-text-1",
      text: "Assume x is positive.",
      type: "text",
    });
    expect(math.blocks[1]).toEqual({
      id: "block-math-1",
      latex: String.raw`\sqrt{x}=2`,
      type: "math",
    });
    expect(initialState.blocks[0]).not.toBe(text.blocks[0]);
    expect(() => updateBlockValue(initialState, "unknown", "value")).toThrow(/unknown block/i);
  });

  it("inserts mathematics at an exact text caret without losing surrounding text", () => {
    const next = insertMathAtTextOffset(initialState, {
      mathBlockId: "inserted-math",
      offset: 6,
      textBlockId: "block-text-1",
      trailingTextBlockId: "inserted-text",
    });

    expect(next.blocks).toEqual([
      { id: "block-text-1", text: "Let x ", type: "text" },
      { id: "inserted-math", latex: "", type: "math" },
      { id: "inserted-text", text: "be positive.", type: "text" },
      { id: "block-math-1", latex: "x^2=4", type: "math" },
      { id: "block-text-2", text: "Therefore", type: "text" },
      { id: "block-math-2", latex: "x=2", type: "math" },
    ]);
    expect(initialState.blocks[0]).toEqual({
      id: "block-text-1",
      text: "Let x be positive.",
      type: "text",
    });
  });

  it("keeps an editable text position after start and end formula insertion", () => {
    const atStart = insertMathAtTextOffset(initialState, {
      mathBlockId: "math-at-start",
      offset: 0,
      textBlockId: "block-text-1",
      trailingTextBlockId: "unused-start-text",
    });
    const atEnd = insertMathAtTextOffset(initialState, {
      mathBlockId: "math-at-end",
      offset: "Let x be positive.".length,
      textBlockId: "block-text-1",
      trailingTextBlockId: "text-after-end",
    });

    expect(atStart.blocks.slice(0, 2)).toEqual([
      { id: "math-at-start", latex: "", type: "math" },
      { id: "block-text-1", text: "Let x be positive.", type: "text" },
    ]);
    expect(atEnd.blocks.slice(0, 3)).toEqual([
      { id: "block-text-1", text: "Let x be positive.", type: "text" },
      { id: "math-at-end", latex: "", type: "math" },
      { id: "text-after-end", text: "", type: "text" },
    ]);
    expect(() =>
      insertMathAtTextOffset(initialState, {
        mathBlockId: "bad-offset",
        offset: 99,
        textBlockId: "block-text-1",
        trailingTextBlockId: "bad-offset-text",
      }),
    ).toThrow(/caret position/i);
  });

  it("deletes a confirmed formula and joins surrounding text in reading order", () => {
    const next = deleteMathBlock(initialState, {
      mathBlockId: "block-math-1",
      replacementTextBlockId: "unused-replacement",
    });

    expect(next.blocks).toEqual([
      { id: "block-text-1", text: "Let x be positive.Therefore", type: "text" },
      { id: "block-math-2", latex: "x=2", type: "math" },
    ]);
    expect(initialState.blocks).toHaveLength(4);

    expect(
      deleteMathBlock(
        {
          attemptId: "formula-only",
          blocks: [{ id: "only-formula", latex: "x=1", type: "math" }],
          schemaVersion: "3.0.0",
          warnings: [],
        },
        { mathBlockId: "only-formula", replacementTextBlockId: "empty-document-text" },
      ).blocks,
    ).toEqual([{ id: "empty-document-text", text: "", type: "text" }]);

    expect(() =>
      deleteMathBlock(initialState, {
        mathBlockId: "block-text-1",
        replacementTextBlockId: "replacement",
      }),
    ).toThrow(/math block/i);
  });
});
