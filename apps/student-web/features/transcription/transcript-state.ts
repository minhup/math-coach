export const TRANSCRIPT_SCHEMA_VERSION = "2.0.0" as const;

export type TranscriptBlock =
  { id: string; text: string; type: "text" } | { id: string; latex: string; type: "math" };

export type TranscriptState = {
  attemptId: string;
  blocks: TranscriptBlock[];
  schemaVersion: typeof TRANSCRIPT_SCHEMA_VERSION;
};

export type ConfirmedTranscriptSnapshot = TranscriptState;

type Direction = "down" | "up";

export class TranscriptStateError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "TranscriptStateError";
  }
}

function cloneBlock(block: TranscriptBlock): TranscriptBlock {
  return { ...block };
}

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

export function confirmTranscript(state: TranscriptState): ConfirmedTranscriptSnapshot {
  validateTranscriptState(state);
  return {
    attemptId: state.attemptId,
    blocks: state.blocks.map(cloneBlock),
    schemaVersion: state.schemaVersion,
  };
}
