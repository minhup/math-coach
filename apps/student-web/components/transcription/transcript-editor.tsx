"use client";

import { useRef, useState } from "react";

import {
  addBlock,
  confirmTranscript,
  type ConfirmedTranscriptSnapshot,
  deleteBlock,
  moveBlock,
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

export function TranscriptEditor({ initialState, onConfirm }: TranscriptEditorProps) {
  const [transcript, setTranscript] = useState(() => validateTranscriptState(initialState));
  const [activeMathBlockId, setActiveMathBlockId] = useState<string | null>(null);
  const [confirmed, setConfirmed] = useState<ConfirmedTranscriptSnapshot | null>(null);
  const idCounters = useRef({ math: 0, text: 0 });

  function replaceTranscript(operation: (current: TranscriptState) => TranscriptState) {
    setTranscript((current) => operation(current));
    setConfirmed(null);
  }

  function nextUniqueId(kind: "math" | "text") {
    const existing = new Set(transcript.blocks.map(({ id }) => id));
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
          <p className="eyebrow">Simulated OCR transcript</p>
          <h2 id="transcript-editor-title">Review the transcript</h2>
        </div>
        <p>Edit the document so it matches the uploaded solution, then confirm it.</p>
      </div>

      <div
        aria-label="Editable transcript document"
        className="transcript-document"
        role="document"
      >
        {transcript.blocks.map((block, blockIndex) => {
          const blockNumber = blockIndex + 1;
          return (
            <div
              aria-label={`Transcript block ${blockNumber}`}
              className={`transcript-block transcript-block-${block.type}`}
              key={block.id}
              role="group"
            >
              {block.type === "text" ? (
                <textarea
                  aria-label={`Edit text block ${blockNumber}`}
                  className="transcript-text-field"
                  onChange={(event) =>
                    replaceTranscript((current) =>
                      updateBlockValue(current, block.id, event.target.value),
                    )
                  }
                  rows={1}
                  value={block.text}
                />
              ) : activeMathBlockId === block.id ? (
                <div className="transcript-math-editor">
                  <MathLiveEditor
                    label={`Edit mathematics block ${blockNumber}`}
                    onInput={(value) =>
                      replaceTranscript((current) => updateBlockValue(current, block.id, value))
                    }
                    value={block.latex}
                  />
                  <button
                    aria-label={`Done editing formula ${blockNumber}`}
                    className="transcript-done-button"
                    onClick={() => setActiveMathBlockId(null)}
                    type="button"
                  >
                    Done
                  </button>
                </div>
              ) : (
                <button
                  aria-label={`Edit formula ${blockNumber}`}
                  className="transcript-math-activation"
                  onClick={() => setActiveMathBlockId(block.id)}
                  type="button"
                >
                  <MathRenderer
                    label={`Mathematics block ${blockNumber}`}
                    latex={block.latex}
                    mode="display"
                  />
                </button>
              )}

              <details className="transcript-block-menu">
                <summary aria-label={`Block ${blockNumber} options`}>
                  <span aria-hidden="true">•••</span>
                </summary>
                <div className="transcript-control-row">
                  <button
                    aria-label={`Move block ${blockNumber} up`}
                    className="transcript-control"
                    disabled={blockIndex === 0}
                    onClick={() => replaceTranscript((state) => moveBlock(state, block.id, "up"))}
                    type="button"
                  >
                    Move up
                  </button>
                  <button
                    aria-label={`Move block ${blockNumber} down`}
                    className="transcript-control"
                    disabled={blockIndex === transcript.blocks.length - 1}
                    onClick={() => replaceTranscript((state) => moveBlock(state, block.id, "down"))}
                    type="button"
                  >
                    Move down
                  </button>
                  <button
                    aria-label={`Delete block ${blockNumber}`}
                    className="transcript-control transcript-control-danger"
                    disabled={transcript.blocks.length === 1}
                    onClick={() => {
                      if (activeMathBlockId === block.id) {
                        setActiveMathBlockId(null);
                      }
                      replaceTranscript((state) => deleteBlock(state, block.id));
                    }}
                    type="button"
                  >
                    Delete
                  </button>
                </div>
              </details>
            </div>
          );
        })}

        <div className="transcript-add-row">
          <span>Add to document</span>
          <button
            aria-label="Add text block"
            className="transcript-add-button"
            onClick={() => {
              const blockId = nextUniqueId("text");
              replaceTranscript((state) =>
                addBlock(state, {
                  block: { id: blockId, text: "", type: "text" },
                  index: state.blocks.length,
                }),
              );
            }}
            type="button"
          >
            + Text
          </button>
          <button
            aria-label="Add math block"
            className="transcript-add-button"
            onClick={() => {
              const blockId = nextUniqueId("math");
              replaceTranscript((state) =>
                addBlock(state, {
                  block: { id: blockId, latex: "", type: "math" },
                  index: state.blocks.length,
                }),
              );
            }}
            type="button"
          >
            + Math
          </button>
        </div>
      </div>

      <div className="transcript-confirmation">
        <button
          aria-label="Confirm transcript"
          className="primary-button"
          onClick={confirmVisibleTranscript}
          type="button"
        >
          Confirm transcript
        </button>
        <p>
          This confirmed document will be the future authoritative grading input. Reasoning analysis
          happens later and does not run here.
        </p>
      </div>

      {confirmed !== null ? (
        <section aria-label="Confirmed transcript" className="transcript-snapshot" role="status">
          <p className="eyebrow">Confirmed transcript</p>
          <h3>Future authoritative grading input</h3>
          <div className="transcript-confirmed-document">
            {confirmed.blocks.map((block, blockIndex) =>
              block.type === "text" ? (
                <p key={block.id}>{block.text}</p>
              ) : (
                <MathRenderer
                  key={block.id}
                  label={`Confirmed formula ${blockIndex + 1}`}
                  latex={block.latex}
                  mode="display"
                />
              ),
            )}
          </div>
        </section>
      ) : null}
    </section>
  );
}
