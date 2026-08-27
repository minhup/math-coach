import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import type {
  ConfirmedTranscriptSnapshot,
  TranscriptState,
} from "../../features/transcription/transcript-state";
import { TranscriptEditor } from "./transcript-editor";

vi.mock("mathlive", () => ({}));

const invalidSource = String.raw`\frac{PRIVATE_INVALID_SOURCE}{`;

const initialState: TranscriptState = {
  attemptId: "synthetic-attempt-correction",
  blocks: [
    { id: "text-a", text: "Start with the equation. ", type: "text" },
    { id: "math-a", latex: invalidSource, type: "math" },
    { id: "text-b", text: " Therefore the positive root is ", type: "text" },
    { id: "math-b", latex: "x=2", type: "math" },
    { id: "text-c", text: ".", type: "text" },
  ],
  schemaVersion: "2.0.0",
};

function textNodeContaining(root: HTMLElement, text: string) {
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  let node = walker.nextNode();
  while (node !== null && !node.textContent?.includes(text)) {
    node = walker.nextNode();
  }
  if (node === null) {
    throw new Error(`Text node not found: ${text}`);
  }
  return node;
}

function placeCaret(root: HTMLElement, text: string, offset: number) {
  root.focus();
  const node = textNodeContaining(root, text);
  const range = document.createRange();
  range.setStart(node, offset);
  range.collapse(true);
  const selection = window.getSelection();
  selection?.removeAllRanges();
  selection?.addRange(range);
  fireEvent.pointerUp(root);
}

describe("TranscriptEditor", () => {
  it("presents one inline plaintext editor with a native caret and no text-block controls", async () => {
    const { container } = render(<TranscriptEditor initialState={initialState} />);

    const editor = screen.getByRole("textbox", { name: "Editable transcript document" });
    expect(editor).toHaveAttribute("contenteditable", "plaintext-only");
    expect(editor).toHaveAttribute("aria-multiline", "true");
    expect(editor).toHaveTextContent("Start with the equation.");
    expect(
      container.querySelector("textarea, .transcript-block, .transcript-block-menu"),
    ).toBeNull();
    expect(screen.queryByRole("button", { name: "Add text block" })).toBeNull();
    expect(screen.getByRole("button", { name: "Insert formula at caret" })).toBeInTheDocument();
    expect(container.innerHTML).not.toMatch(/stepId|PRIVATE_INVALID_SOURCE/);
  });

  it("types directly at the browser caret and confirms the visible text", async () => {
    const onConfirm = vi.fn<(snapshot: ConfirmedTranscriptSnapshot) => void>();
    const user = userEvent.setup();
    render(<TranscriptEditor initialState={initialState} onConfirm={onConfirm} />);
    const editor = screen.getByRole("textbox", { name: "Editable transcript document" });

    placeCaret(editor, "Start with the equation.", 5);
    const textNode = textNodeContaining(editor, "Start with the equation.") as Text;
    textNode.insertData(5, " directly");
    fireEvent.input(editor, { data: " directly", inputType: "insertText" });
    await user.click(screen.getByRole("button", { name: "Confirm transcript" }));

    expect(onConfirm.mock.calls[0]?.[0].blocks[0]).toEqual({
      id: "text-a",
      text: "Start directly with the equation. ",
      type: "text",
    });
  });

  it("accepts only plain text from paste into canonical transcript state", async () => {
    const onConfirm = vi.fn<(snapshot: ConfirmedTranscriptSnapshot) => void>();
    const user = userEvent.setup();
    const { container } = render(
      <TranscriptEditor initialState={initialState} onConfirm={onConfirm} />,
    );
    const editor = screen.getByRole("textbox", { name: "Editable transcript document" });

    placeCaret(editor, "Start with the equation.", 5);
    fireEvent.paste(editor, {
      clipboardData: {
        getData: (type: string) =>
          type === "text/plain" ? " pasted" : '<img src="https://example.invalid/tracker">',
      },
    });
    await user.click(screen.getByRole("button", { name: "Confirm transcript" }));

    expect(onConfirm.mock.calls[0]?.[0].blocks[0]).toMatchObject({
      text: "Start pasted with the equation. ",
    });
    expect(container.querySelector("img, script, iframe")).toBeNull();
  });

  it("inserts and focuses visual mathematics at the saved caret", async () => {
    const onConfirm = vi.fn<(snapshot: ConfirmedTranscriptSnapshot) => void>();
    const user = userEvent.setup();
    render(<TranscriptEditor initialState={initialState} onConfirm={onConfirm} />);
    const editor = screen.getByRole("textbox", { name: "Editable transcript document" });

    placeCaret(editor, "Start with the equation.", 5);
    await user.click(screen.getByRole("button", { name: "Insert formula at caret" }));
    const field = await screen.findByLabelText("Edit formula 1");
    await waitFor(() => expect(field).toHaveFocus());
    Reflect.set(field, "value", "y=1");
    field.dispatchEvent(new Event("input", { bubbles: true }));
    await user.click(screen.getByRole("button", { name: "Done editing formula 1" }));
    await user.click(screen.getByRole("button", { name: "Confirm transcript" }));

    expect(onConfirm.mock.calls[0]?.[0].blocks.slice(0, 3)).toEqual([
      { id: "text-a", text: "Start", type: "text" },
      { id: "m3-math-1", latex: "y=1", type: "math" },
      { id: "m3-text-1", text: " with the equation. ", type: "text" },
    ]);
  });

  it("edits valid and invalid inline formulas without exposing source or a simultaneous preview", async () => {
    const user = userEvent.setup();
    const { container } = render(<TranscriptEditor initialState={initialState} />);

    expect(await screen.findByRole("img", { name: "Math needs correction" })).toBeInTheDocument();
    expect(container.innerHTML).not.toContain("PRIVATE_INVALID_SOURCE");
    const validToken = screen.getByRole("button", { name: "Edit formula 2" }).parentElement;
    expect(validToken?.querySelector(".katex")).not.toBeNull();

    await user.click(screen.getByRole("button", { name: "Edit formula 1" }));
    const field = await screen.findByLabelText("Edit formula 1");
    await waitFor(() => expect(Reflect.get(field, "value")).toBe(invalidSource));
    expect(screen.queryByRole("img", { name: "Math needs correction" })).toBeNull();
    expect(container.innerHTML).not.toContain("PRIVATE_INVALID_SOURCE");

    Reflect.set(field, "value", "x^2=4");
    field.dispatchEvent(new Event("input", { bubbles: true }));
    await user.click(screen.getByRole("button", { name: "Done editing formula 1" }));
    await waitFor(() => expect(container.querySelectorAll(".katex")).toHaveLength(2));
  });

  it("keeps a formula until explicit deletion confirmation and joins surrounding text", async () => {
    const user = userEvent.setup();
    const { container } = render(<TranscriptEditor initialState={initialState} />);

    await user.click(screen.getByRole("button", { name: "Edit formula 1" }));
    await user.click(screen.getByRole("button", { name: "Delete formula 1" }));
    let dialog = screen.getByRole("alertdialog", { name: "Delete this formula?" });
    expect(container.querySelectorAll("[data-transcript-math-id]")).toHaveLength(2);
    expect(within(dialog).getByRole("button", { name: "Keep formula" })).toHaveFocus();
    await user.keyboard("{Escape}");
    expect(screen.queryByRole("alertdialog")).toBeNull();
    expect(container.querySelectorAll("[data-transcript-math-id]")).toHaveLength(2);

    await user.click(screen.getByRole("button", { name: "Delete formula 1" }));
    dialog = screen.getByRole("alertdialog", { name: "Delete this formula?" });
    await user.click(within(dialog).getByRole("button", { name: "Delete formula" }));
    expect(container.querySelectorAll("[data-transcript-math-id]")).toHaveLength(1);
    expect(container.querySelector("[data-transcript-text-id='text-a']")?.textContent).toBe(
      "Start with the equation.  Therefore the positive root is ",
    );
  });

  it("intercepts selected, adjacent, and empty-formula deletion before removing a token", async () => {
    const user = userEvent.setup();
    const { container } = render(<TranscriptEditor initialState={initialState} />);
    const editor = screen.getByRole("textbox", { name: "Editable transcript document" });

    editor.focus();
    const selection = window.getSelection();
    const range = document.createRange();
    range.setStart(textNodeContaining(editor, "Start with the equation."), 5);
    range.setEnd(textNodeContaining(editor, " Therefore the positive root is "), 1);
    selection?.removeAllRanges();
    selection?.addRange(range);
    fireEvent.keyDown(editor, { key: "Delete" });
    selection?.removeAllRanges();
    const selectedDialog = container.querySelector<HTMLElement>("[role='alertdialog']");
    expect(selectedDialog).not.toBeNull();
    expect(container.querySelectorAll("[data-transcript-math-id]")).toHaveLength(2);
    const keepFormula = Array.from(selectedDialog?.querySelectorAll("button") ?? []).find(
      ({ textContent }) => textContent === "Keep formula",
    );
    if (keepFormula === undefined) {
      throw new Error("Keep formula action not found in confirmation dialog.");
    }
    await user.click(keepFormula);

    placeCaret(editor, " Therefore the positive root is ", 0);
    fireEvent.keyDown(editor, { key: "Backspace" });
    let dialog = screen.getByRole("alertdialog", { name: "Delete this formula?" });
    expect(container.querySelectorAll("[data-transcript-math-id]")).toHaveLength(2);
    await user.click(within(dialog).getByRole("button", { name: "Keep formula" }));

    placeCaret(editor, "Start with the equation.", 5);
    await user.click(screen.getByRole("button", { name: "Insert formula at caret" }));
    const emptyField = await screen.findByLabelText("Edit formula 1");
    fireEvent.keyDown(emptyField, { key: "Backspace" });
    dialog = screen.getByRole("alertdialog", { name: "Delete this formula?" });
    expect(dialog).toBeInTheDocument();
  });

  it("reorders an active formula contextually and confirms content without technical structure", async () => {
    const onConfirm = vi.fn<(snapshot: ConfirmedTranscriptSnapshot) => void>();
    const user = userEvent.setup();
    render(<TranscriptEditor initialState={initialState} onConfirm={onConfirm} />);

    await user.click(screen.getByRole("button", { name: "Edit formula 2" }));
    await user.click(screen.getByRole("button", { name: "Move formula 2 earlier" }));
    await user.click(screen.getByRole("button", { name: "Done editing formula 2" }));
    await user.click(screen.getByRole("button", { name: "Confirm transcript" }));

    expect(onConfirm.mock.calls[0]?.[0].blocks.map(({ id }) => id)).toEqual([
      "text-a",
      "math-a",
      "math-b",
      "text-b",
      "text-c",
    ]);
    const confirmation = screen.getByRole("status", { name: "Confirmed transcript" });
    expect(confirmation).toHaveTextContent("Future authoritative grading input");
    expect(confirmation.textContent).not.toMatch(/text-a|math-a|step-|schemaVersion|2\.0\.0|→/);
  });
});
