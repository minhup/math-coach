"use client";

import { useRef, useState } from "react";

import {
  addBlock,
  confirmTranscript,
  deleteBlock,
  mergeStepWithPrevious,
  moveBlock,
  moveStep,
  splitStep,
  type ConfirmedTranscriptSnapshot,
  type TranscriptBlock,
  type TranscriptState,
  updateBlockValue,
  validateTranscriptState,
} from "../../features/transcription/transcript-state";
import { MathLiveEditor } from "../math/mathlive-editor";
import { MathRenderer } from "../math/math-renderer";

type TranscriptEditorProps = {
  initialState: TranscriptState;
  onConfirm?: (snapshot: ConfirmedTranscriptSnapshot) => void;
};

function blockById(state: TranscriptState, blockId: string): TranscriptBlock {
  const block = state.blocks.find(({ id }) => id === blockId);
  if (block === undefined) {
    throw new Error(`Validated transcript is missing block ${blockId}.`);
  }
  return block;
}

export function TranscriptEditor({ initialState, onConfirm }: TranscriptEditorProps) {
  const [transcript, setTranscript] = useState(() => validateTranscriptState(initialState));
  const [confirmed, setConfirmed] = useState<ConfirmedTranscriptSnapshot | null>(null);
  const idCounters = useRef({ math: 0, step: 0, text: 0 });

  function replaceTranscript(operation: (current: TranscriptState) => TranscriptState) {
    setTranscript((current) => operation(current));
    setConfirmed(null);
  }

  function nextUniqueId(kind: "math" | "step" | "text") {
    const existing = new Set([
      ...transcript.blocks.map(({ id }) => id),
      ...transcript.steps.map(({ id }) => id),
    ]);
    let candidate: string;
    do {
      idCounters.current[kind] += 1;
      candidate = `m3-${kind}-${idCounters.current[kind]}`;
    } while (existing.has(candidate));
    return candidate;
  }

  function confirmVisibleTranscript() {
    const snapshot = confirmTranscript(transcript);
    setConfirmed(snapshot);
    onConfirm?.(snapshot);
  }

  return (
    <section className="transcript-editor" aria-labelledby="transcript-editor-title">
      <div className="transcript-editor-heading">
        <div>
          <p className="eyebrow">Typed correction</p>
          <h2 id="transcript-editor-title">Review the transcript</h2>
        </div>
        <p>Use the visual fields and labelled controls. Drag-and-drop is not required.</p>
      </div>

      <div className="transcript-steps">
        {transcript.steps.map((step, stepIndex) => (
          <section
            aria-labelledby={`transcript-step-${step.id}`}
            className="transcript-step"
            key={step.id}
            role="region"
          >
            <div className="transcript-step-heading">
              <h3 id={`transcript-step-${step.id}`}>Step {stepIndex + 1}</h3>
              <div className="transcript-control-row">
                <button
                  aria-label={`Move step ${stepIndex + 1} up`}
                  className="transcript-control"
                  disabled={stepIndex === 0}
                  onClick={() => replaceTranscript((state) => moveStep(state, step.id, "up"))}
                  type="button"
                >
                  Move up
                </button>
                <button
                  aria-label={`Move step ${stepIndex + 1} down`}
                  className="transcript-control"
                  disabled={stepIndex === transcript.steps.length - 1}
                  onClick={() => replaceTranscript((state) => moveStep(state, step.id, "down"))}
                  type="button"
                >
                  Move down
                </button>
                <button
                  aria-label={`Merge step ${stepIndex + 1} with previous`}
                  className="transcript-control"
                  disabled={stepIndex === 0}
                  onClick={() =>
                    replaceTranscript((state) => mergeStepWithPrevious(state, step.id))
                  }
                  type="button"
                >
                  Merge previous
                </button>
              </div>
            </div>

            <div className="transcript-blocks">
              {step.blockIds.map((blockId, blockIndex) => {
                const block = blockById(transcript, blockId);
                const blockNumber = blockIndex + 1;
                const stepNumber = stepIndex + 1;
                return (
                  <div
                    aria-label={`${block.type === "text" ? "Text" : "Mathematics"} block ${blockNumber}`}
                    className={`transcript-block transcript-block-${block.type}`}
                    key={block.id}
                    role="group"
                  >
                    <div className="transcript-block-main">
                      {block.type === "text" ? (
                        <label className="transcript-field-label">
                          <span>Text block</span>
                          <textarea
                            aria-label={`Edit text in step ${stepNumber}, block ${blockNumber}`}
                            onChange={(event) =>
                              replaceTranscript((state) =>
                                updateBlockValue(state, block.id, event.target.value),
                              )
                            }
                            rows={2}
                            value={block.text}
                          />
                        </label>
                      ) : (
                        <div className="transcript-math-field">
                          <span className="transcript-field-label">Mathematics block</span>
                          <MathRenderer
                            label={`Mathematics preview for step ${stepNumber}, block ${blockNumber}`}
                            latex={block.latex}
                            mode="display"
                          />
                          <MathLiveEditor
                            label={`Edit mathematics in step ${stepNumber}, block ${blockNumber}`}
                            onInput={(value) =>
                              replaceTranscript((state) => updateBlockValue(state, block.id, value))
                            }
                            value={block.latex}
                          />
                        </div>
                      )}
                    </div>

                    <div className="transcript-control-row transcript-block-controls">
                      <button
                        aria-label={`Move block ${blockNumber} up`}
                        className="transcript-control"
                        disabled={blockIndex === 0}
                        onClick={() =>
                          replaceTranscript((state) => moveBlock(state, block.id, "up"))
                        }
                        type="button"
                      >
                        Move up
                      </button>
                      <button
                        aria-label={`Move block ${blockNumber} down`}
                        className="transcript-control"
                        disabled={blockIndex === step.blockIds.length - 1}
                        onClick={() =>
                          replaceTranscript((state) => moveBlock(state, block.id, "down"))
                        }
                        type="button"
                      >
                        Move down
                      </button>
                      <button
                        aria-label={`Delete block ${blockNumber}`}
                        className="transcript-control transcript-control-danger"
                        disabled={step.blockIds.length === 1}
                        onClick={() => replaceTranscript((state) => deleteBlock(state, block.id))}
                        type="button"
                      >
                        Delete
                      </button>
                      {blockIndex > 0 ? (
                        <button
                          aria-label={`Split before block ${blockNumber}`}
                          className="transcript-control"
                          onClick={() => {
                            const newStepId = nextUniqueId("step");
                            replaceTranscript((state) =>
                              splitStep(state, {
                                beforeBlockId: block.id,
                                newStepId,
                                stepId: step.id,
                              }),
                            );
                          }}
                          type="button"
                        >
                          Split step here
                        </button>
                      ) : null}
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="transcript-add-row">
              <button
                aria-label="Add text block"
                className="secondary-button"
                onClick={() => {
                  const blockId = nextUniqueId("text");
                  replaceTranscript((state) =>
                    addBlock(state, {
                      block: { id: blockId, stepId: step.id, text: "", type: "text" },
                      index: step.blockIds.length,
                      stepId: step.id,
                    }),
                  );
                }}
                type="button"
              >
                + Text
              </button>
              <button
                aria-label="Add math block"
                className="secondary-button"
                onClick={() => {
                  const blockId = nextUniqueId("math");
                  replaceTranscript((state) =>
                    addBlock(state, {
                      block: { id: blockId, latex: "", stepId: step.id, type: "math" },
                      index: step.blockIds.length,
                      stepId: step.id,
                    }),
                  );
                }}
                type="button"
              >
                + Math
              </button>
            </div>
          </section>
        ))}
      </div>

      <div className="transcript-confirmation">
        <button
          className="primary-button"
          onClick={confirmVisibleTranscript}
          type="button"
          aria-label="Confirm transcript for future grading"
        >
          Confirm transcript
        </button>
        <p>
          The confirmed snapshot will be the future authoritative grading input. No grading runs
          here.
        </p>
      </div>

      {confirmed !== null ? (
        <section
          aria-label="Confirmed transcript snapshot"
          className="transcript-snapshot"
          role="status"
        >
          <p className="eyebrow">Confirmed snapshot</p>
          <h3>Future authoritative grading input</h3>
          <ol>
            {confirmed.steps.map((step) => (
              <li key={step.id}>
                {step.id}: {step.blockIds.map((id) => blockById(confirmed, id).type).join(" → ")}
              </li>
            ))}
          </ol>
        </section>
      ) : null}
    </section>
  );
}
