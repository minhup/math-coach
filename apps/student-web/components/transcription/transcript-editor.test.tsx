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
    { id: "text-a", stepId: "step-a", text: "Start with the equation.", type: "text" },
    { id: "math-a", latex: invalidSource, stepId: "step-a", type: "math" },
    { id: "text-b", stepId: "step-b", text: "Therefore the positive root is", type: "text" },
    { id: "math-b", latex: "x=2", stepId: "step-b", type: "math" },
  ],
  schemaVersion: "1.0.0",
  steps: [
    { blockIds: ["text-a", "math-a"], id: "step-a" },
    { blockIds: ["text-b", "math-b"], id: "step-b" },
  ],
};

describe("TranscriptEditor", () => {
  it("corrects invalid mathematics visually and confirms the exact typed ordered state", async () => {
    const onConfirm = vi.fn<(snapshot: ConfirmedTranscriptSnapshot) => void>();
    const { container } = render(
      <TranscriptEditor initialState={initialState} onConfirm={onConfirm} />,
    );

    expect(await screen.findByRole("img", { name: "Math needs correction" })).toBeInTheDocument();
    expect(container.innerHTML).not.toContain("PRIVATE_INVALID_SOURCE");
    const field = await screen.findByLabelText("Edit mathematics in step 1, block 2");
    await waitFor(() => expect(Reflect.get(field, "value")).toBe(invalidSource));

    Reflect.set(field, "value", "x^2=4");
    field.dispatchEvent(new Event("input", { bubbles: true }));

    await waitFor(() =>
      expect(screen.queryByRole("img", { name: "Math needs correction" })).toBeNull(),
    );
    await userEvent
      .setup()
      .click(screen.getByRole("button", { name: "Confirm transcript for future grading" }));

    expect(onConfirm).toHaveBeenCalledWith({
      ...initialState,
      blocks: [
        initialState.blocks[0],
        { id: "math-a", latex: "x^2=4", stepId: "step-a", type: "math" },
        initialState.blocks[2],
        initialState.blocks[3],
      ],
    });
    expect(screen.getByRole("status", { name: "Confirmed transcript snapshot" })).toHaveTextContent(
      "step-a: text → math",
    );
    expect(screen.getByText("Future authoritative grading input")).toBeInTheDocument();
    expect(screen.queryByText(/grade|score|correct answer/i)).toBeNull();
  });

  it("adds, deletes, and reorders typed blocks with labelled boundary controls", async () => {
    const user = userEvent.setup();
    render(<TranscriptEditor initialState={initialState} />);
    const firstStep = screen.getByRole("region", { name: "Step 1" });

    expect(within(firstStep).getByRole("button", { name: "Move block 1 up" })).toBeDisabled();
    expect(within(firstStep).getByRole("button", { name: "Move block 2 down" })).toBeDisabled();
    await user.click(within(firstStep).getByRole("button", { name: "Move block 1 down" }));
    const blocks = within(firstStep).getAllByRole("group", { name: /block \d/i });
    expect(blocks[1]).toHaveTextContent("Start with the equation.");

    await user.click(within(firstStep).getByRole("button", { name: "Add text block" }));
    expect(within(firstStep).getAllByRole("group", { name: /block \d/i })).toHaveLength(3);
    await user.type(
      within(firstStep).getByLabelText("Edit text in step 1, block 3"),
      "New reason.",
    );
    await user.click(within(firstStep).getByRole("button", { name: "Delete block 3" }));
    expect(within(firstStep).queryByDisplayValue("New reason.")).toBeNull();

    await user.click(within(firstStep).getByRole("button", { name: "Add math block" }));
    const addedField = await within(firstStep).findByLabelText(
      "Edit mathematics in step 1, block 3",
    );
    expect(addedField.tagName).toBe("MATH-FIELD");
  });

  it("splits, merges, and reorders steps without changing block order", async () => {
    const onConfirm = vi.fn<(snapshot: ConfirmedTranscriptSnapshot) => void>();
    const user = userEvent.setup();
    render(<TranscriptEditor initialState={initialState} onConfirm={onConfirm} />);

    const firstStep = screen.getByRole("region", { name: "Step 1" });
    await user.click(within(firstStep).getByRole("button", { name: "Split before block 2" }));
    expect(screen.getAllByRole("region", { name: /Step \d/ })).toHaveLength(3);
    expect(screen.getByRole("button", { name: "Move step 1 up" })).toBeDisabled();

    await user.click(screen.getByRole("button", { name: "Merge step 2 with previous" }));
    expect(screen.getAllByRole("region", { name: /Step \d/ })).toHaveLength(2);
    await user.click(screen.getByRole("button", { name: "Move step 2 up" }));

    const orderedSteps = screen.getAllByRole("region", { name: /Step \d/ });
    expect(
      within(orderedSteps[0]).getByDisplayValue("Therefore the positive root is"),
    ).toBeInTheDocument();
    expect(
      within(orderedSteps[1]).getByDisplayValue("Start with the equation."),
    ).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Confirm transcript for future grading" }));
    expect(onConfirm.mock.calls[0][0].steps.map(({ id }) => id)).toEqual(["step-b", "step-a"]);
    expect(onConfirm.mock.calls[0][0].blocks.map(({ id }) => id)).toEqual([
      "text-b",
      "math-b",
      "text-a",
      "math-a",
    ]);
    expect(screen.getByRole("status", { name: "Confirmed transcript snapshot" })).toHaveTextContent(
      "step-b: text → mathstep-a: text → math",
    );
  });
});
