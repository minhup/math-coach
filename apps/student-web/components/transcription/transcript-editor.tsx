"use client";

import {
  type ClipboardEvent as ReactClipboardEvent,
  type FormEvent,
  type KeyboardEvent,
  type PointerEvent,
  useLayoutEffect,
  useRef,
  useState,
} from "react";

import {
  confirmTranscript,
  type ConfirmedTranscriptSnapshot,
  deleteMathBlock,
  insertMathAtTextOffset,
  moveBlock,
  type TranscriptBlock,
  type TranscriptState,
  updateBlockValue,
  validateTranscriptState,
} from "../../features/transcription/transcript-state";
import { MathLiveEditor } from "../math/mathlive-editor";
import { MathRenderer } from "../math/math-renderer";

type TranscriptEditorProps = {
  initialState: TranscriptState;
  onConfirm?: (snapshot: ConfirmedTranscriptSnapshot) => Promise<void> | void;
  onSourceRegionChange?: (region: NonNullable<TranscriptBlock["sourceRegion"]>) => void;
  sourceLabel?: string;
};

type CaretPosition = {
  blockId: string;
  offset: number;
};

function textRunForNode(root: HTMLElement, node: Node): HTMLElement | null {
  const element = node.nodeType === Node.ELEMENT_NODE ? (node as Element) : node.parentElement;
  const run = element?.closest<HTMLElement>("[data-transcript-text-id]") ?? null;
  return run !== null && root.contains(run) ? run : null;
}

function readCaretPosition(root: HTMLElement): CaretPosition | null {
  const selection = window.getSelection();
  if (selection === null || selection.rangeCount === 0) {
    return null;
  }
  const range = selection.getRangeAt(0);
  const run = textRunForNode(root, range.startContainer);
  const blockId = run?.dataset.transcriptTextId;
  if (run === null || blockId === undefined) {
    return null;
  }

  const prefix = range.cloneRange();
  prefix.selectNodeContents(run);
  prefix.setEnd(range.startContainer, range.startOffset);
  return { blockId, offset: prefix.toString().length };
}

function restoreCaret(root: HTMLElement, position: CaretPosition) {
  const run = Array.from(root.querySelectorAll<HTMLElement>("[data-transcript-text-id]")).find(
    ({ dataset }) => dataset.transcriptTextId === position.blockId,
  );
  if (run === undefined) {
    return;
  }
  const textNode = run.firstChild ?? run.appendChild(document.createTextNode(""));
  const offset = Math.min(position.offset, textNode.textContent?.length ?? 0);
  const range = document.createRange();
  range.setStart(textNode, offset);
  range.collapse(true);
  const selection = window.getSelection();
  selection?.removeAllRanges();
  selection?.addRange(range);
  root.focus();
}

function syncTextRuns(root: HTMLElement, state: TranscriptState): TranscriptState {
  const visibleText = new Map(
    Array.from(root.querySelectorAll<HTMLElement>("[data-transcript-text-id]")).flatMap((run) => {
      const id = run.dataset.transcriptTextId;
      return id === undefined ? [] : [[id, run.textContent ?? ""] as const];
    }),
  );
  return state.blocks.reduce(
    (current, block) =>
      block.type === "text" && visibleText.get(block.id) !== block.text
        ? updateBlockValue(current, block.id, visibleText.get(block.id) ?? block.text)
        : current,
    state,
  );
}

function formulaDeletionCaret(state: TranscriptState, mathBlockId: string, replacementId: string) {
  const index = state.blocks.findIndex(({ id }) => id === mathBlockId);
  const previous = state.blocks[index - 1];
  const next = state.blocks[index + 1];
  if (previous?.type === "text") {
    return { blockId: previous.id, offset: previous.text.length };
  }
  if (next?.type === "text") {
    return { blockId: next.id, offset: 0 };
  }
  return { blockId: replacementId, offset: 0 };
}

export function TranscriptEditor({
  initialState,
  onConfirm,
  onSourceRegionChange,
  sourceLabel = "Simulated OCR transcript",
}: TranscriptEditorProps) {
  const [transcript, setTranscript] = useState(() => validateTranscriptState(initialState));
  const transcriptRef = useRef(transcript);
  const [activeMathBlockId, setActiveMathBlockId] = useState<string | null>(null);
  const [pendingDeleteMathId, setPendingDeleteMathId] = useState<string | null>(null);
  const [confirmed, setConfirmed] = useState<ConfirmedTranscriptSnapshot | null>(null);
  const [confirmationError, setConfirmationError] = useState<string | null>(null);
  const [isConfirming, setIsConfirming] = useState(false);
  const editorRef = useRef<HTMLDivElement>(null);
  const lastCaretRef = useRef<CaretPosition | null>(null);
  const pendingCaretRestoreRef = useRef<CaretPosition | null>(null);
  const idCounters = useRef({ math: 0, text: 0 });

  function replaceTranscript(operation: (current: TranscriptState) => TranscriptState) {
    const next = operation(transcriptRef.current);
    transcriptRef.current = next;
    setTranscript(next);
    setConfirmed(null);
    setConfirmationError(null);
  }

  function nextUniqueId(kind: "math" | "text") {
    const existing = new Set(transcriptRef.current.blocks.map(({ id }) => id));
    let candidate: string;
    do {
      idCounters.current[kind] += 1;
      candidate = `m3-${kind}-${idCounters.current[kind]}`;
    } while (existing.has(candidate));
    return candidate;
  }

  function rememberCaret() {
    const root = editorRef.current;
    if (root !== null) {
      lastCaretRef.current = readCaretPosition(root) ?? lastCaretRef.current;
    }
  }

  useLayoutEffect(() => {
    const root = editorRef.current;
    const position = pendingCaretRestoreRef.current;
    if (root !== null && position !== null) {
      pendingCaretRestoreRef.current = null;
      lastCaretRef.current = position;
      restoreCaret(root, position);
    }
  }, [transcript]);

  function syncVisibleText() {
    const root = editorRef.current;
    if (root === null) {
      return transcriptRef.current;
    }
    const next = syncTextRuns(root, transcriptRef.current);
    transcriptRef.current = next;
    setTranscript(next);
    setConfirmed(null);
    setConfirmationError(null);
    return next;
  }

  function insertFormulaAtCaret() {
    const visible = syncVisibleText();
    const fallback = [...visible.blocks].reverse().find((block) => block.type === "text");
    const saved = lastCaretRef.current;
    const position =
      saved !== null &&
      visible.blocks.some(({ id, type }) => type === "text" && id === saved.blockId)
        ? saved
        : fallback?.type === "text"
          ? { blockId: fallback.id, offset: fallback.text.length }
          : null;
    if (position === null) {
      return;
    }

    const mathBlockId = nextUniqueId("math");
    const trailingTextBlockId = nextUniqueId("text");
    replaceTranscript((current) =>
      insertMathAtTextOffset(current, {
        mathBlockId,
        offset: position.offset,
        textBlockId: position.blockId,
        trailingTextBlockId,
      }),
    );
    setActiveMathBlockId(mathBlockId);
  }

  function requestFormulaDeletion(mathBlockId: string) {
    syncVisibleText();
    setPendingDeleteMathId(mathBlockId);
  }

  function cancelFormulaDeletion() {
    setPendingDeleteMathId(null);
  }

  function deletionTarget(direction: "backward" | "forward") {
    const root = editorRef.current;
    if (root === null) {
      return null;
    }
    const selection = window.getSelection();
    if (selection === null || selection.rangeCount === 0) {
      return null;
    }
    const range = selection.getRangeAt(0);
    if (!range.collapsed) {
      return (
        Array.from(root.querySelectorAll<HTMLElement>("[data-transcript-math-id]")).find((token) =>
          range.intersectsNode(token),
        )?.dataset.transcriptMathId ?? null
      );
    }

    const caret = readCaretPosition(root);
    if (caret === null) {
      return null;
    }
    const current = transcriptRef.current;
    const textIndex = current.blocks.findIndex(({ id }) => id === caret.blockId);
    const textBlock = current.blocks[textIndex];
    if (textBlock?.type !== "text") {
      return null;
    }
    const adjacent =
      direction === "backward" && caret.offset === 0
        ? current.blocks[textIndex - 1]
        : direction === "forward" && caret.offset === textBlock.text.length
          ? current.blocks[textIndex + 1]
          : undefined;
    return adjacent?.type === "math" ? adjacent.id : null;
  }

  function interceptFormulaDeletion(direction: "backward" | "forward", preventDefault: () => void) {
    const target = deletionTarget(direction);
    if (target !== null) {
      preventDefault();
      requestFormulaDeletion(target);
      return true;
    }
    return false;
  }

  function handleEditorKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key === "Backspace") {
      interceptFormulaDeletion("backward", () => event.preventDefault());
    } else if (event.key === "Delete") {
      interceptFormulaDeletion("forward", () => event.preventDefault());
    }
  }

  function handleBeforeInput(event: FormEvent<HTMLDivElement>) {
    const inputType = (event.nativeEvent as InputEvent).inputType;
    if (inputType === "deleteContentBackward") {
      interceptFormulaDeletion("backward", () => event.preventDefault());
    } else if (inputType === "deleteContentForward") {
      interceptFormulaDeletion("forward", () => event.preventDefault());
    }
  }

  function handlePaste(event: ReactClipboardEvent<HTMLDivElement>) {
    event.preventDefault();
    const root = editorRef.current;
    const selection = window.getSelection();
    if (root === null || selection === null || selection.rangeCount === 0) {
      return;
    }
    const selectedFormula = deletionTarget("forward");
    if (selectedFormula !== null && !selection.getRangeAt(0).collapsed) {
      requestFormulaDeletion(selectedFormula);
      return;
    }

    const range = selection.getRangeAt(0);
    const startRun = textRunForNode(root, range.startContainer);
    const endRun = textRunForNode(root, range.endContainer);
    if (startRun === null || startRun !== endRun) {
      return;
    }
    range.deleteContents();
    const pasted = document.createTextNode(event.clipboardData.getData("text/plain"));
    range.insertNode(pasted);
    range.setStartAfter(pasted);
    range.collapse(true);
    selection.removeAllRanges();
    selection.addRange(range);
    rememberCaret();
    syncVisibleText();
  }

  function confirmFormulaDeletion() {
    const mathBlockId = pendingDeleteMathId;
    if (mathBlockId === null) {
      return;
    }
    const replacementTextBlockId = nextUniqueId("text");
    pendingCaretRestoreRef.current = formulaDeletionCaret(
      transcriptRef.current,
      mathBlockId,
      replacementTextBlockId,
    );
    replaceTranscript((current) =>
      deleteMathBlock(current, { mathBlockId, replacementTextBlockId }),
    );
    setActiveMathBlockId(null);
    setPendingDeleteMathId(null);
  }

  async function confirmVisibleTranscript() {
    const root = editorRef.current;
    const visible =
      root === null ? transcriptRef.current : syncTextRuns(root, transcriptRef.current);
    transcriptRef.current = visible;
    setTranscript(visible);
    const snapshot = confirmTranscript(visible);
    setConfirmationError(null);
    setIsConfirming(true);
    try {
      await onConfirm?.(snapshot);
      setConfirmed(snapshot);
    } catch {
      setConfirmationError("The exact transcript version could not be confirmed. Try again.");
    } finally {
      setIsConfirming(false);
    }
  }

  return (
    <section className="transcript-editor" aria-labelledby="transcript-editor-title">
      <div className="transcript-editor-heading">
        <div>
          <p className="eyebrow">{sourceLabel}</p>
          <h2 id="transcript-editor-title">Review the transcript</h2>
        </div>
        <p>Place the caret, type naturally, or insert and correct a formula before confirming.</p>
      </div>

      {transcript.warnings.length > 0 ? (
        <section aria-label="Transcription warnings" className="transcription-warnings">
          <strong>Review these uncertain parts</strong>
          <ul>
            {transcript.warnings.map((warning) => (
              <li key={`${warning.code}-${warning.blockId ?? "document"}`}>{warning.message}</li>
            ))}
          </ul>
        </section>
      ) : null}

      {onSourceRegionChange === undefined ||
      transcript.blocks.every(({ sourceRegion }) => sourceRegion == null) ? null : (
        <section aria-label="Transcript source regions" className="transcript-source-regions">
          <strong>Compare with the image</strong>
          <div>
            {transcript.blocks.map((block, index) => {
              const region = block.sourceRegion;
              return region == null ? null : (
                <button
                  aria-label={`Show source region for block ${index + 1}`}
                  className="transcript-source-region-button"
                  key={block.id}
                  onClick={() => onSourceRegionChange(region)}
                  type="button"
                >
                  Block {index + 1} · {block.type === "math" ? "formula" : "text"}
                </button>
              );
            })}
          </div>
        </section>
      )}

      <div className="transcript-toolbar" aria-label="Transcript tools" role="toolbar">
        <button
          aria-label="Insert formula at caret"
          className="transcript-insert-math"
          onClick={insertFormulaAtCaret}
          onPointerDown={(event: PointerEvent<HTMLButtonElement>) => event.preventDefault()}
          type="button"
        >
          + Formula
        </button>
      </div>

      <div
        aria-label="Editable transcript document"
        aria-multiline="true"
        className="transcript-document"
        contentEditable="plaintext-only"
        onBeforeInput={handleBeforeInput}
        onFocus={rememberCaret}
        onInput={() => {
          rememberCaret();
          const root = editorRef.current;
          if (root !== null) {
            transcriptRef.current = syncTextRuns(root, transcriptRef.current);
          }
          if (confirmed !== null) {
            pendingCaretRestoreRef.current = lastCaretRef.current;
            setTranscript(transcriptRef.current);
            setConfirmed(null);
          }
        }}
        onKeyDown={handleEditorKeyDown}
        onKeyUp={rememberCaret}
        onPaste={handlePaste}
        onPointerUp={rememberCaret}
        ref={editorRef}
        role="textbox"
        spellCheck
        suppressContentEditableWarning
      >
        {transcript.blocks.map((block, blockIndex) => {
          if (block.type === "text") {
            return (
              <span
                className="transcript-text-run"
                data-transcript-text-id={block.id}
                key={block.id}
              >
                {block.text}
              </span>
            );
          }

          const formulaNumber = transcript.blocks
            .slice(0, blockIndex + 1)
            .filter(({ type }) => type === "math").length;
          const active = activeMathBlockId === block.id;
          return (
            <span
              className={`transcript-math-token${active ? " transcript-math-token-active" : ""}`}
              contentEditable={false}
              data-transcript-math-id={block.id}
              key={block.id}
            >
              {active ? (
                <span
                  className="transcript-math-editor"
                  onKeyDown={(event) => {
                    if (
                      block.latex.length === 0 &&
                      (event.key === "Backspace" || event.key === "Delete")
                    ) {
                      event.preventDefault();
                      event.stopPropagation();
                      requestFormulaDeletion(block.id);
                    }
                  }}
                >
                  <MathLiveEditor
                    focusOnReady
                    label={`Edit formula ${formulaNumber}`}
                    onInput={(value) =>
                      replaceTranscript((current) => updateBlockValue(current, block.id, value))
                    }
                    value={block.latex}
                  />
                  <span className="transcript-formula-actions">
                    <button
                      aria-label={`Done editing formula ${formulaNumber}`}
                      className="transcript-done-button"
                      onClick={() => setActiveMathBlockId(null)}
                      type="button"
                    >
                      Done
                    </button>
                    <button
                      aria-label={`Move formula ${formulaNumber} earlier`}
                      className="transcript-control"
                      disabled={blockIndex === 0}
                      onClick={() => replaceTranscript((state) => moveBlock(state, block.id, "up"))}
                      type="button"
                    >
                      Move earlier
                    </button>
                    <button
                      aria-label={`Move formula ${formulaNumber} later`}
                      className="transcript-control"
                      disabled={blockIndex === transcript.blocks.length - 1}
                      onClick={() =>
                        replaceTranscript((state) => moveBlock(state, block.id, "down"))
                      }
                      type="button"
                    >
                      Move later
                    </button>
                    <button
                      aria-label={`Delete formula ${formulaNumber}`}
                      className="transcript-control transcript-control-danger"
                      onClick={() => requestFormulaDeletion(block.id)}
                      type="button"
                    >
                      Delete formula
                    </button>
                  </span>
                </span>
              ) : (
                <button
                  aria-label={`Edit formula ${formulaNumber}`}
                  className="transcript-math-activation"
                  onClick={() => setActiveMathBlockId(block.id)}
                  onKeyDown={(event) => {
                    if (event.key === "Backspace" || event.key === "Delete") {
                      event.preventDefault();
                      event.stopPropagation();
                      requestFormulaDeletion(block.id);
                    }
                  }}
                  type="button"
                >
                  <MathRenderer
                    label={`Formula ${formulaNumber}`}
                    latex={block.latex}
                    mode="inline"
                  />
                </button>
              )}
            </span>
          );
        })}
      </div>

      <div className="transcript-confirmation">
        <button
          aria-label="Confirm exact transcript"
          className="primary-button"
          disabled={isConfirming}
          onClick={() => void confirmVisibleTranscript()}
          type="button"
        >
          {isConfirming ? "Saving exact version…" : "Confirm exact transcript"}
        </button>
        <p>
          This confirmed version is the authoritative downstream input. The next evaluation remains
          a clearly labeled deterministic mock; production grading does not run here.
        </p>
        {confirmationError === null ? null : <p role="alert">{confirmationError}</p>}
      </div>

      {confirmed !== null ? (
        <section aria-label="Confirmed transcript" className="transcript-snapshot" role="status">
          <p className="eyebrow">Confirmed transcript</p>
          <h3>Future authoritative grading input</h3>
          <div className="transcript-confirmed-document">
            {confirmed.blocks.map((block, blockIndex) =>
              block.type === "text" ? (
                <span key={block.id}>{block.text}</span>
              ) : (
                <MathRenderer
                  key={block.id}
                  label={`Confirmed formula ${blockIndex + 1}`}
                  latex={block.latex}
                  mode="inline"
                />
              ),
            )}
          </div>
        </section>
      ) : null}

      {pendingDeleteMathId !== null ? (
        <div className="transcript-dialog-backdrop">
          <section
            aria-describedby="delete-formula-description"
            aria-labelledby="delete-formula-title"
            aria-modal="true"
            className="transcript-delete-dialog"
            onKeyDown={(event) => {
              if (event.key === "Escape") {
                event.preventDefault();
                event.stopPropagation();
                cancelFormulaDeletion();
              }
            }}
            role="alertdialog"
          >
            <h3 id="delete-formula-title">Delete this formula?</h3>
            <p id="delete-formula-description">
              The surrounding text will be joined. The formula is kept until you confirm.
            </p>
            <div className="transcript-dialog-actions">
              <button
                autoFocus
                className="secondary-button"
                onClick={cancelFormulaDeletion}
                type="button"
              >
                Keep formula
              </button>
              <button className="danger-button" onClick={confirmFormulaDeletion} type="button">
                Delete formula
              </button>
            </div>
          </section>
        </div>
      ) : null}
    </section>
  );
}
