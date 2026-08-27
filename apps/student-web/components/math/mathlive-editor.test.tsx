import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { MathLiveEditor } from "./mathlive-editor";

vi.mock("mathlive", () => ({}));

describe("MathLiveEditor", () => {
  it("loads a visual field through its value property without source text or form controls", async () => {
    const source = String.raw`\frac{PRIVATE_EDITOR_SOURCE}{`;
    const { container } = render(
      <MathLiveEditor label="Correct mathematics" onInput={() => undefined} value={source} />,
    );

    expect(screen.getByText("Loading visual math editor…")).toBeInTheDocument();
    const field = await screen.findByLabelText("Correct mathematics");
    await waitFor(() => expect(Reflect.get(field, "value")).toBe(source));

    expect(field.tagName).toBe("MATH-FIELD");
    expect(field).toHaveTextContent("");
    expect(container.querySelector("input, textarea")).toBeNull();
    expect(container.innerHTML).not.toContain("PRIVATE_EDITOR_SOURCE");
  });

  it("propagates the public input value and follows external corrections", async () => {
    const onInput = vi.fn();
    const { rerender } = render(
      <MathLiveEditor label="Visual expression" onInput={onInput} value="x^2" />,
    );
    const field = await screen.findByLabelText("Visual expression");
    await waitFor(() => expect(Reflect.get(field, "value")).toBe("x^2"));

    Reflect.set(field, "value", "x=2");
    field.dispatchEvent(new Event("input", { bubbles: true }));
    expect(onInput).toHaveBeenCalledWith("x=2");

    rerender(<MathLiveEditor label="Visual expression" onInput={onInput} value="x=3" />);
    await waitFor(() => expect(Reflect.get(field, "value")).toBe("x=3"));
  });
});
