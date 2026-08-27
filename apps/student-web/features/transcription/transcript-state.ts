import type { components } from "@math-coach/api-client";

export const TRANSCRIPT_SCHEMA_VERSION = "3.0.0" as const;

export type TranscriptState = components["schemas"]["TranscriptDocument"];
export type TranscriptBlock = TranscriptState["blocks"][number];

export type ConfirmedTranscriptSnapshot = TranscriptState;

type Direction = "down" | "up";

export class TranscriptStateError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "TranscriptStateError";
  }
}

function cloneBlock(block: TranscriptBlock): TranscriptBlock {
  return {
    ...block,
    ...(block.sourceRegion === undefined || block.sourceRegion === null
      ? {}
      : { sourceRegion: { ...block.sourceRegion } }),
  };
}

const warningMessages = {
  ambiguous_cross_out: "A crossed-out part may need review.",
  ambiguous_insertion: "An inserted part may need review.",
  low_confidence_math: "A formula may need review.",
  low_confidence_text: "Some text may need review.",
  ordering_uncertain: "The reading order may need review.",
  source_region_unavailable: "A source location is unavailable.",
} as const;

function findBlockIndex(state: TranscriptState, blockId: string) {
  const index = state.blocks.findIndex(({ id }) => id === blockId);
  if (index === -1) {
    throw new TranscriptStateError(`Unknown block ID: ${blockId}`);
  }
  return index;
}

export function validateTranscriptState(state: TranscriptState): TranscriptState {
  if (state.attemptId.trim().length === 0) {
    throw new TranscriptStateError("Transcript must have a non-empty attempt ID.");
  }
  if (state.schemaVersion !== TRANSCRIPT_SCHEMA_VERSION) {
    throw new TranscriptStateError("Unsupported transcript schema version.");
  }
  if (state.blocks.length === 0) {
    throw new TranscriptStateError("A transcript must contain at least one block.");
  }

  const blockIds = new Set<string>();
  for (const block of state.blocks) {
    if (block.id.trim().length === 0) {
      throw new TranscriptStateError("Transcript must have a non-empty block ID.");
    }
    if (blockIds.has(block.id)) {
      throw new TranscriptStateError(`Duplicate block ID: ${block.id}`);
    }
    blockIds.add(block.id);
    const region = block.sourceRegion;
    if (
      region !== undefined &&
      region !== null &&
      (region.attemptAssetId.trim().length === 0 ||
        region.units !== "normalized" ||
        ![region.x, region.y, region.width, region.height].every(Number.isFinite) ||
        region.x < 0 ||
        region.y < 0 ||
        region.width <= 0 ||
        region.height <= 0 ||
        region.x + region.width > 1 ||
        region.y + region.height > 1)
    ) {
      throw new TranscriptStateError(`Invalid source region for block: ${block.id}`);
    }
  }
  for (const warning of state.warnings) {
    if (warning.message !== warningMessages[warning.code]) {
      throw new TranscriptStateError("Transcript warning message is invalid.");
    }
    if (
      warning.blockId !== undefined &&
      warning.blockId !== null &&
      !blockIds.has(warning.blockId)
    ) {
      throw new TranscriptStateError(`Warning references an unknown block ID: ${warning.blockId}`);
    }
  }
  return state;
}

export function addBlock(
  state: TranscriptState,
  input: { block: TranscriptBlock; index: number },
): TranscriptState {
  validateTranscriptState(state);
  if (state.blocks.some(({ id }) => id === input.block.id)) {
    throw new TranscriptStateError(`Duplicate block ID: ${input.block.id}`);
  }
  if (!Number.isInteger(input.index) || input.index < 0 || input.index > state.blocks.length) {
    throw new TranscriptStateError("Block insertion position is outside the transcript.");
  }

  const blocks = state.blocks.map(cloneBlock);
  blocks.splice(input.index, 0, cloneBlock(input.block));
  return validateTranscriptState({ ...state, blocks });
}

export function deleteBlock(state: TranscriptState, blockId: string): TranscriptState {
  validateTranscriptState(state);
  const blockIndex = findBlockIndex(state, blockId);
  if (state.blocks.length === 1) {
    throw new TranscriptStateError("Cannot delete the transcript's only block.");
  }
  return validateTranscriptState({
    ...state,
    blocks: state.blocks.filter((_, index) => index !== blockIndex).map(cloneBlock),
    warnings: state.warnings.filter(({ blockId: warningBlockId }) => warningBlockId !== blockId),
  });
}

export function moveBlock(
  state: TranscriptState,
  blockId: string,
  direction: Direction,
): TranscriptState {
  validateTranscriptState(state);
  const blockIndex = findBlockIndex(state, blockId);
  const targetIndex = direction === "up" ? blockIndex - 1 : blockIndex + 1;
  if (targetIndex < 0) {
    throw new TranscriptStateError("Block is already first.");
  }
  if (targetIndex >= state.blocks.length) {
    throw new TranscriptStateError("Block is already last.");
  }

  const blocks = state.blocks.map(cloneBlock);
  [blocks[blockIndex], blocks[targetIndex]] = [blocks[targetIndex], blocks[blockIndex]];
  return validateTranscriptState({ ...state, blocks });
}

export function updateBlockValue(
  state: TranscriptState,
  blockId: string,
  value: string,
): TranscriptState {
  validateTranscriptState(state);
  const blockIndex = findBlockIndex(state, blockId);
  const blocks = state.blocks.map(cloneBlock);
  const block = blocks[blockIndex];
  blocks[blockIndex] =
    block.type === "text" ? { ...block, text: value } : { ...block, latex: value };
  return validateTranscriptState({ ...state, blocks });
}

export function insertMathAtTextOffset(
  state: TranscriptState,
  input: {
    mathBlockId: string;
    offset: number;
    textBlockId: string;
    trailingTextBlockId: string;
  },
): TranscriptState {
  validateTranscriptState(state);
  const textBlockIndex = findBlockIndex(state, input.textBlockId);
  const textBlock = state.blocks[textBlockIndex];
  if (textBlock.type !== "text") {
    throw new TranscriptStateError("Mathematics can only be inserted at a text caret.");
  }
  if (!Number.isInteger(input.offset) || input.offset < 0 || input.offset > textBlock.text.length) {
    throw new TranscriptStateError("Text caret position is outside the text block.");
  }

  for (const id of [input.mathBlockId, input.trailingTextBlockId]) {
    if (id.trim().length === 0) {
      throw new TranscriptStateError("Inserted blocks must have non-empty IDs.");
    }
    if (state.blocks.some((block) => block.id === id)) {
      throw new TranscriptStateError(`Duplicate block ID: ${id}`);
    }
  }
  if (input.mathBlockId === input.trailingTextBlockId) {
    throw new TranscriptStateError(`Duplicate block ID: ${input.mathBlockId}`);
  }

  const leadingText = textBlock.text.slice(0, input.offset);
  const trailingText = textBlock.text.slice(input.offset);
  const inserted: TranscriptBlock[] =
    input.offset === 0
      ? [{ id: input.mathBlockId, latex: "", type: "math" }, cloneBlock(textBlock)]
      : [
          { ...textBlock, text: leadingText },
          { id: input.mathBlockId, latex: "", type: "math" },
          { id: input.trailingTextBlockId, text: trailingText, type: "text" },
        ];
  const blocks = state.blocks.map(cloneBlock);
  blocks.splice(textBlockIndex, 1, ...inserted);
  return validateTranscriptState({ ...state, blocks });
}

export function deleteMathBlock(
  state: TranscriptState,
  input: { mathBlockId: string; replacementTextBlockId: string },
): TranscriptState {
  validateTranscriptState(state);
  const mathBlockIndex = findBlockIndex(state, input.mathBlockId);
  if (state.blocks[mathBlockIndex].type !== "math") {
    throw new TranscriptStateError("Only a math block can be deleted as a formula.");
  }

  const blocks = state.blocks.map(cloneBlock);
  const previous = blocks[mathBlockIndex - 1];
  const next = blocks[mathBlockIndex + 1];
  if (previous?.type === "text" && next?.type === "text") {
    blocks.splice(mathBlockIndex - 1, 3, {
      ...previous,
      text: previous.text + next.text,
    });
  } else {
    blocks.splice(mathBlockIndex, 1);
  }

  if (!blocks.some((block) => block.type === "text")) {
    if (input.replacementTextBlockId.trim().length === 0) {
      throw new TranscriptStateError("Replacement text block must have a non-empty ID.");
    }
    if (blocks.some((block) => block.id === input.replacementTextBlockId)) {
      throw new TranscriptStateError(`Duplicate block ID: ${input.replacementTextBlockId}`);
    }
    blocks.splice(Math.min(mathBlockIndex, blocks.length), 0, {
      id: input.replacementTextBlockId,
      text: "",
      type: "text",
    });
  }

  const remainingIds = new Set(blocks.map(({ id }) => id));
  return validateTranscriptState({
    ...state,
    blocks,
    warnings: state.warnings.filter(
      ({ blockId }) => blockId === undefined || blockId === null || remainingIds.has(blockId),
    ),
  });
}

export function confirmTranscript(state: TranscriptState): ConfirmedTranscriptSnapshot {
  validateTranscriptState(state);
  return {
    attemptId: state.attemptId,
    blocks: state.blocks.map(cloneBlock),
    schemaVersion: state.schemaVersion,
    warnings: state.warnings.map((warning) => ({ ...warning })),
  };
}
