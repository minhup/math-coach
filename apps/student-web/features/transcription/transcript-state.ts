export const TRANSCRIPT_SCHEMA_VERSION = "1.0.0" as const;

export type TranscriptBlock =
  | { id: string; stepId: string; text: string; type: "text" }
  | { id: string; latex: string; stepId: string; type: "math" };

export type TranscriptStep = {
  blockIds: string[];
  id: string;
};

export type TranscriptState = {
  attemptId: string;
  blocks: TranscriptBlock[];
  schemaVersion: typeof TRANSCRIPT_SCHEMA_VERSION;
  steps: TranscriptStep[];
};

export type ConfirmedTranscriptSnapshot = TranscriptState;

type Direction = "down" | "up";

export class TranscriptStateError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "TranscriptStateError";
  }
}

function requireNonEmptyId(id: string, kind: "attempt" | "block" | "step") {
  if (id.trim().length === 0) {
    throw new TranscriptStateError(`Transcript must have a non-empty ${kind} ID.`);
  }
}

function cloneBlock(block: TranscriptBlock): TranscriptBlock {
  return block.type === "text" ? { ...block } : { ...block };
}

function findBlock(state: TranscriptState, blockId: string) {
  const block = state.blocks.find(({ id }) => id === blockId);
  if (block === undefined) {
    throw new TranscriptStateError(`Unknown block ID: ${blockId}`);
  }
  return block;
}

function findStepIndex(state: TranscriptState, stepId: string) {
  const index = state.steps.findIndex(({ id }) => id === stepId);
  if (index === -1) {
    throw new TranscriptStateError(`Unknown step ID: ${stepId}`);
  }
  return index;
}

export function validateTranscriptState(state: TranscriptState): TranscriptState {
  requireNonEmptyId(state.attemptId, "attempt");
  if (state.schemaVersion !== TRANSCRIPT_SCHEMA_VERSION) {
    throw new TranscriptStateError("Unsupported transcript schema version.");
  }
  if (state.steps.length === 0) {
    throw new TranscriptStateError("A transcript must contain at least one step.");
  }

  const blocksById = new Map<string, TranscriptBlock>();
  for (const block of state.blocks) {
    requireNonEmptyId(block.id, "block");
    if (blocksById.has(block.id)) {
      throw new TranscriptStateError(`Duplicate block ID: ${block.id}`);
    }
    blocksById.set(block.id, block);
  }

  const stepIds = new Set<string>();
  const referenceCounts = new Map<string, number>();
  for (const step of state.steps) {
    requireNonEmptyId(step.id, "step");
    if (stepIds.has(step.id)) {
      throw new TranscriptStateError(`Duplicate step ID: ${step.id}`);
    }
    stepIds.add(step.id);
    if (step.blockIds.length === 0) {
      throw new TranscriptStateError(`Step ${step.id} must contain at least one block.`);
    }

    for (const blockId of step.blockIds) {
      const block = blocksById.get(blockId);
      if (block === undefined) {
        throw new TranscriptStateError(`Step ${step.id} references unknown block: ${blockId}`);
      }
      const count = (referenceCounts.get(blockId) ?? 0) + 1;
      if (count > 1) {
        throw new TranscriptStateError(`Block ${blockId} is referenced more than once.`);
      }
      referenceCounts.set(blockId, count);
      if (block.stepId !== step.id) {
        throw new TranscriptStateError(`Block ${blockId} has mismatched step ownership.`);
      }
    }
  }

  for (const block of state.blocks) {
    if (!referenceCounts.has(block.id)) {
      throw new TranscriptStateError(`Transcript contains orphaned block: ${block.id}`);
    }
  }

  return state;
}

export function addBlock(
  state: TranscriptState,
  input: { block: TranscriptBlock; index: number; stepId: string },
): TranscriptState {
  validateTranscriptState(state);
  if (state.blocks.some(({ id }) => id === input.block.id)) {
    throw new TranscriptStateError(`Duplicate block ID: ${input.block.id}`);
  }
  requireNonEmptyId(input.block.id, "block");
  const stepIndex = findStepIndex(state, input.stepId);
  if (input.block.stepId !== input.stepId) {
    throw new TranscriptStateError(`Block ${input.block.id} has mismatched step ownership.`);
  }
  const step = state.steps[stepIndex];
  if (!Number.isInteger(input.index) || input.index < 0 || input.index > step.blockIds.length) {
    throw new TranscriptStateError("Block insertion position is outside the target step.");
  }

  const blockIds = [...step.blockIds];
  blockIds.splice(input.index, 0, input.block.id);
  const next: TranscriptState = {
    ...state,
    blocks: [...state.blocks, cloneBlock(input.block)],
    steps: state.steps.map((candidate, index) =>
      index === stepIndex ? { ...candidate, blockIds } : candidate,
    ),
  };
  return validateTranscriptState(next);
}

export function deleteBlock(state: TranscriptState, blockId: string): TranscriptState {
  validateTranscriptState(state);
  const block = findBlock(state, blockId);
  const stepIndex = findStepIndex(state, block.stepId);
  const step = state.steps[stepIndex];
  if (step.blockIds.length === 1) {
    throw new TranscriptStateError(`Cannot delete the only block in step ${step.id}.`);
  }

  const next: TranscriptState = {
    ...state,
    blocks: state.blocks.filter(({ id }) => id !== blockId),
    steps: state.steps.map((candidate, index) =>
      index === stepIndex
        ? { ...candidate, blockIds: candidate.blockIds.filter((id) => id !== blockId) }
        : candidate,
    ),
  };
  return validateTranscriptState(next);
}

function adjacentIndex(currentIndex: number, length: number, direction: Direction, kind: string) {
  const targetIndex = direction === "up" ? currentIndex - 1 : currentIndex + 1;
  if (targetIndex < 0) {
    throw new TranscriptStateError(`${kind} is already first.`);
  }
  if (targetIndex >= length) {
    throw new TranscriptStateError(`${kind} is already last.`);
  }
  return targetIndex;
}

export function moveBlock(
  state: TranscriptState,
  blockId: string,
  direction: Direction,
): TranscriptState {
  validateTranscriptState(state);
  const block = findBlock(state, blockId);
  const stepIndex = findStepIndex(state, block.stepId);
  const step = state.steps[stepIndex];
  const blockIndex = step.blockIds.indexOf(blockId);
  const targetIndex = adjacentIndex(blockIndex, step.blockIds.length, direction, "Block");
  const blockIds = [...step.blockIds];
  [blockIds[blockIndex], blockIds[targetIndex]] = [blockIds[targetIndex], blockIds[blockIndex]];

  const next: TranscriptState = {
    ...state,
    steps: state.steps.map((candidate, index) =>
      index === stepIndex ? { ...candidate, blockIds } : candidate,
    ),
  };
  return validateTranscriptState(next);
}

export function updateBlockValue(
  state: TranscriptState,
  blockId: string,
  value: string,
): TranscriptState {
  validateTranscriptState(state);
  findBlock(state, blockId);
  const next: TranscriptState = {
    ...state,
    blocks: state.blocks.map((block) => {
      if (block.id !== blockId) {
        return block;
      }
      return block.type === "text" ? { ...block, text: value } : { ...block, latex: value };
    }),
  };
  return validateTranscriptState(next);
}

export function splitStep(
  state: TranscriptState,
  input: { beforeBlockId: string; newStepId: string; stepId: string },
): TranscriptState {
  validateTranscriptState(state);
  requireNonEmptyId(input.newStepId, "step");
  if (state.steps.some(({ id }) => id === input.newStepId)) {
    throw new TranscriptStateError(`Duplicate step ID: ${input.newStepId}`);
  }
  const stepIndex = findStepIndex(state, input.stepId);
  const step = state.steps[stepIndex];
  const splitIndex = step.blockIds.indexOf(input.beforeBlockId);
  if (splitIndex === -1) {
    throw new TranscriptStateError(
      `Block ${input.beforeBlockId} does not belong to step ${step.id}.`,
    );
  }
  if (splitIndex === 0) {
    throw new TranscriptStateError("Cannot split before the first block of a step.");
  }

  const leadingIds = step.blockIds.slice(0, splitIndex);
  const trailingIds = step.blockIds.slice(splitIndex);
  const nextSteps = [...state.steps];
  nextSteps.splice(
    stepIndex,
    1,
    { ...step, blockIds: leadingIds },
    { blockIds: trailingIds, id: input.newStepId },
  );
  const movedIds = new Set(trailingIds);
  const next: TranscriptState = {
    ...state,
    blocks: state.blocks.map((block) =>
      movedIds.has(block.id) ? { ...block, stepId: input.newStepId } : block,
    ),
    steps: nextSteps,
  };
  return validateTranscriptState(next);
}

export function mergeStepWithPrevious(state: TranscriptState, stepId: string): TranscriptState {
  validateTranscriptState(state);
  const stepIndex = findStepIndex(state, stepId);
  if (stepIndex === 0) {
    throw new TranscriptStateError("Cannot merge the first step with a previous step.");
  }
  const previous = state.steps[stepIndex - 1];
  const current = state.steps[stepIndex];
  const movedIds = new Set(current.blockIds);
  const nextSteps = [...state.steps];
  nextSteps.splice(stepIndex - 1, 2, {
    ...previous,
    blockIds: [...previous.blockIds, ...current.blockIds],
  });
  const next: TranscriptState = {
    ...state,
    blocks: state.blocks.map((block) =>
      movedIds.has(block.id) ? { ...block, stepId: previous.id } : block,
    ),
    steps: nextSteps,
  };
  return validateTranscriptState(next);
}

export function moveStep(
  state: TranscriptState,
  stepId: string,
  direction: Direction,
): TranscriptState {
  validateTranscriptState(state);
  const stepIndex = findStepIndex(state, stepId);
  const targetIndex = adjacentIndex(stepIndex, state.steps.length, direction, "Step");
  const steps = [...state.steps];
  [steps[stepIndex], steps[targetIndex]] = [steps[targetIndex], steps[stepIndex]];
  return validateTranscriptState({ ...state, steps });
}

export function confirmTranscript(state: TranscriptState): ConfirmedTranscriptSnapshot {
  validateTranscriptState(state);
  const blocksById = new Map(state.blocks.map((block) => [block.id, block]));
  const orderedBlocks: TranscriptBlock[] = [];
  const steps = state.steps.map((step) => {
    const blockIds = [...step.blockIds];
    for (const blockId of blockIds) {
      const block = blocksById.get(blockId);
      if (block === undefined) {
        throw new TranscriptStateError(`Unknown block ID: ${blockId}`);
      }
      orderedBlocks.push(cloneBlock(block));
    }
    return { blockIds, id: step.id };
  });

  return {
    attemptId: state.attemptId,
    blocks: orderedBlocks,
    schemaVersion: state.schemaVersion,
    steps,
  };
}
