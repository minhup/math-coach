import { render, screen, waitFor, within } from "@testing-library/react";
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
    { id: "text-a", text: "Start with the equation.", type: "text" },
    { id: "math-a", latex: invalidSource, type: "math" },
    { id: "text-b", text: "Therefore the positive root is", type: "text" },
    { id: "math-b", latex: "x=2", type: "math" },
  ],
  schemaVersion: "2.0.0",
};

describe("TranscriptEditor", () => {
  it("presents one continuous editable document without reasoning-step UI", async () => {
    const { container } = render(<TranscriptEditor initialState={initialState} />);

    const document = screen.getByRole("document", { name: "Editable transcript document" });
    expect(document).toBeInTheDocument();
    expect(screen.getByLabelText("Edit text block 1")).toHaveValue("Start with the equation.");
    expect(screen.getAllByRole("group", { name: /Transcript block \d/ })).toHaveLength(4);
    expect(screen.queryByRole("heading", { name: /Step \d/i })).toBeNull();
    expect(screen.queryByRole("button", { name: /split|merge|move step/i })).toBeNull();
    expect(container.innerHTML).not.toContain("stepId");
    expect(container.innerHTML).not.toContain("PRIVATE_INVALID_SOURCE");
  });

  it("shows one rendered formula until the learner activates visual editing", async () => {
    const user = userEvent.setup();
    render(<TranscriptEditor initialState={initialState} />);
    const validMathBlock = screen.getByRole("group", { name: "Transcript block 4" });

    await waitFor(() => expect(within(validMathBlock).getByLabelText("Mathematics block 4")));
    expect(validMathBlock.querySelector(".katex")).not.toBeNull();
    expect(within(validMathBlock).queryByLabelText("Edit mathematics block 4")).toBeNull();

    await user.click(within(validMathBlock).getByLabelText("Edit formula 4"));
    const field = await within(validMathBlock).findByLabelText("Edit mathematics block 4");
    expect(field.tagName).toBe("MATH-FIELD");
    expect(validMathBlock.querySelector(".katex")).toBeNull();

    await user.click(within(validMathBlock).getByLabelText("Done editing formula 4"));
    await waitFor(() => expect(validMathBlock.querySelector(".katex")).not.toBeNull());
    expect(within(validMathBlock).queryByLabelText("Edit mathematics block 4")).toBeNull();
  });

  it("corrects an invalid formula through MathLive without exposing its source", async () => {
    const user = userEvent.setup();
    const { container } = render(<TranscriptEditor initialState={initialState} />);
    const invalidMathBlock = screen.getByRole("group", { name: "Transcript block 2" });

    expect(
      await within(invalidMathBlock).findByRole("img", { name: "Math needs correction" }),
    ).toBeInTheDocument();
    expect(container.innerHTML).not.toContain("PRIVATE_INVALID_SOURCE");
    await user.click(within(invalidMathBlock).getByLabelText("Edit formula 2"));

    const field = await within(invalidMathBlock).findByLabelText("Edit mathematics block 2");
    await waitFor(() => expect(Reflect.get(field, "value")).toBe(invalidSource));
    expect(
      within(invalidMathBlock).queryByRole("img", { name: "Math needs correction" }),
    ).toBeNull();
    expect(container.innerHTML).not.toContain("PRIVATE_INVALID_SOURCE");

    Reflect.set(field, "value", "x^2=4");
    field.dispatchEvent(new Event("input", { bubbles: true }));
    await user.click(within(invalidMathBlock).getByLabelText("Done editing formula 2"));

    await waitFor(() => expect(invalidMathBlock.querySelector(".katex")).not.toBeNull());
    expect(screen.queryByRole("img", { name: "Math needs correction" })).toBeNull();
  });

  it("adds, deletes, and reorders flat blocks through contextual controls", async () => {
    const user = userEvent.setup();
    render(<TranscriptEditor initialState={initialState} />);

    const firstMenu = screen.getByLabelText("Block 1 options").closest("details");
    expect(firstMenu).not.toHaveAttribute("open");
    await user.click(screen.getByLabelText("Block 1 options"));
    expect(firstMenu).toHaveAttribute("open");
    expect(screen.getByRole("button", { name: "Move block 1 up" })).toBeDisabled();
    await user.click(screen.getByRole("button", { name: "Move block 1 down" }));
    const reordered = screen.getAllByRole("group", { name: /Transcript block \d/ });
    expect(within(reordered[1]).getByLabelText("Edit text block 2")).toHaveValue(
      "Start with the equation.",
    );

    await user.click(screen.getByRole("button", { name: "Add text block" }));
    await user.type(screen.getByLabelText("Edit text block 5"), "New conclusion.");
    await user.click(screen.getByLabelText("Block 5 options"));
    await user.click(screen.getByRole("button", { name: "Delete block 5" }));
    expect(screen.queryByDisplayValue("New conclusion.")).toBeNull();

    await user.click(screen.getByRole("button", { name: "Add math block" }));
    expect(screen.getByLabelText("Edit formula 5")).toBeInTheDocument();
  });

  it("confirms the exact flat snapshot while showing only reviewed content", async () => {
    const onConfirm = vi.fn<(snapshot: ConfirmedTranscriptSnapshot) => void>();
    const user = userEvent.setup();
    render(<TranscriptEditor initialState={initialState} onConfirm={onConfirm} />);

    const firstText = screen.getByLabelText("Edit text block 1");
    await user.clear(firstText);
    await user.type(firstText, "Begin with the equation.");
    await user.click(screen.getByLabelText("Block 1 options"));
    await user.click(screen.getByRole("button", { name: "Move block 1 down" }));
    await user.click(screen.getByLabelText("Confirm transcript"));

    expect(onConfirm).toHaveBeenCalledWith({
      attemptId: "synthetic-attempt-correction",
      blocks: [
        { id: "math-a", latex: invalidSource, type: "math" },
        { id: "text-a", text: "Begin with the equation.", type: "text" },
        { id: "text-b", text: "Therefore the positive root is", type: "text" },
        { id: "math-b", latex: "x=2", type: "math" },
      ],
      schemaVersion: "2.0.0",
    });

    const confirmation = screen.getByRole("status", { name: "Confirmed transcript" });
    expect(confirmation).toHaveTextContent("Future authoritative grading input");
    expect(confirmation).toHaveTextContent("Begin with the equation.");
    expect(confirmation).toHaveTextContent("Therefore the positive root is");
    expect(confirmation.textContent).not.toMatch(/text-a|math-a|step-|schemaVersion|2\.0\.0|→/);
  });
});
