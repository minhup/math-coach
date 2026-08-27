import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  syntheticGeometryActions,
  syntheticGeometryScene,
} from "../../features/geometry/synthetic-fixtures";
import { GeometryScene } from "./geometry-scene";

const graph = vi.hoisted(() => {
  let shouldFail = false;
  const elements = new Map<
    string,
    {
      handlers: Map<string, (event: Event) => void>;
      on: ReturnType<typeof vi.fn>;
      setAttribute: ReturnType<typeof vi.fn>;
      X: () => number;
      Y: () => number;
    }
  >();
  const create = vi.fn((type: string, parents: unknown[], attributes: Record<string, unknown>) => {
    if (shouldFail) {
      throw new Error("synthetic failure");
    }
    const handlers = new Map<string, (event: Event) => void>();
    const coordinates = type === "point" ? (parents as number[]) : [0, 0];
    const element = {
      handlers,
      on: vi.fn((event: string, handler: (event: Event) => void) => {
        handlers.set(event, handler);
        return element;
      }),
      setAttribute: vi.fn(() => element),
      X: () => coordinates[0] ?? 0,
      Y: () => coordinates[1] ?? 0,
    };
    elements.set(String(attributes.id), element);
    return element;
  });
  const board = { create, update: vi.fn() };
  return {
    board,
    create,
    elements,
    freeBoard: vi.fn(),
    initBoard: vi.fn(() => board),
    fail(value: boolean) {
      shouldFail = value;
    },
    reset() {
      shouldFail = false;
      create.mockClear();
      board.update.mockClear();
      elements.clear();
      this.freeBoard.mockClear();
      this.initBoard.mockClear();
    },
  };
});

vi.mock("jsxgraph", () => ({
  default: { JSXGraph: { initBoard: graph.initBoard, freeBoard: graph.freeBoard } },
}));

afterEach(() => {
  graph.reset();
});

describe("GeometryScene", () => {
  it("renders loading, accessible ready content, and the curated static fallback", async () => {
    render(<GeometryScene actions={syntheticGeometryActions} scene={syntheticGeometryScene} />);

    expect(screen.getByRole("status")).toHaveTextContent("Loading geometry");
    await waitFor(() =>
      expect(screen.getByText("Interactive geometry ready.")).toBeInTheDocument(),
    );
    expect(screen.getByText(syntheticGeometryScene.accessibilityDescription)).toBeInTheDocument();
    expect(
      screen.getByRole("img", { name: syntheticGeometryScene.accessibilityDescription }),
    ).toBeInTheDocument();
    await userEvent.click(screen.getByText("Static fallback"));
    expect(
      screen.getByRole("img", {
        name: `${syntheticGeometryScene.accessibilityDescription} Static fallback.`,
      }),
    ).toHaveAttribute("src", "/fixtures/synthetic-m4-geometry-fallback.svg");
  });

  it("applies every typed action and supports keyboard ask-select", async () => {
    render(<GeometryScene actions={syntheticGeometryActions} scene={syntheticGeometryScene} />);
    await waitFor(() =>
      expect(screen.getByText("Interactive geometry ready.")).toBeInTheDocument(),
    );

    await userEvent.click(screen.getByRole("button", { name: "Highlight A, B" }));
    expect(screen.getByRole("status", { name: "Geometry action result" })).toHaveTextContent(
      "Highlight applied.",
    );
    await userEvent.click(screen.getByRole("button", { name: "Clear highlight" }));
    await userEvent.click(screen.getByRole("button", { name: "Focus triangle" }));
    await userEvent.click(screen.getByRole("button", { name: "Animate A" }));
    await userEvent.click(screen.getByRole("button", { name: "Ask selection question" }));

    expect(screen.getByText("Select point A.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Select C" })).toBeDisabled();
    await userEvent.click(screen.getByRole("button", { name: "Select B" }));
    expect(screen.getByRole("status", { name: "Selection result" })).toHaveTextContent(
      "B is not the expected selection.",
    );
    await userEvent.click(screen.getByRole("button", { name: "Select A" }));
    expect(screen.getByRole("status", { name: "Selection result" })).toHaveTextContent(
      "A is the expected selection.",
    );
  });

  it("accepts configured touch selection from the board", async () => {
    render(<GeometryScene actions={[]} scene={syntheticGeometryScene} />);
    await waitFor(() => expect(graph.elements.get("A")).toBeDefined());

    act(() =>
      graph.elements.get("A")?.handlers.get("down")?.({ pointerType: "touch" } as PointerEvent),
    );

    await waitFor(() =>
      expect(screen.getByRole("status", { name: "Selection result" })).toHaveTextContent(
        "Selected A.",
      ),
    );
  });

  it("rejects invalid actions without exposing a control", async () => {
    render(
      <GeometryScene
        actions={[{ type: "show", objectIds: ["UNKNOWN"], javascript: "unsafe()" }]}
        scene={syntheticGeometryScene}
      />,
    );
    await waitFor(() =>
      expect(screen.getByText("Interactive geometry ready.")).toBeInTheDocument(),
    );

    expect(screen.getByRole("alert")).toHaveTextContent("A geometry action was rejected.");
    expect(screen.queryByText("unsafe()")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /UNKNOWN/ })).not.toBeInTheDocument();
  });

  it("uses a concise fallback for invalid scenes without rendering arbitrary markup", () => {
    const invalidScene = structuredClone(syntheticGeometryScene) as Record<string, unknown>;
    invalidScene.html = "<script>unsafe()</script>";
    render(<GeometryScene actions={[]} scene={invalidScene} />);

    expect(screen.getByRole("status")).toHaveTextContent("Geometry unavailable.");
    expect(screen.queryByTestId("geometry-board")).not.toBeInTheDocument();
    expect(screen.queryByText("unsafe()")).not.toBeInTheDocument();
    expect(document.querySelector("script")).toBeNull();
  });

  it("frees partial output and shows the static fallback after renderer failure", async () => {
    graph.fail(true);
    render(<GeometryScene actions={[]} scene={syntheticGeometryScene} />);

    await waitFor(() =>
      expect(screen.getByRole("alert")).toHaveTextContent("Geometry unavailable."),
    );
    expect(
      screen.getByRole("img", {
        name: `${syntheticGeometryScene.accessibilityDescription} Static fallback.`,
      }),
    ).toHaveAttribute("src", "/fixtures/synthetic-m4-geometry-fallback.svg");
    expect(graph.freeBoard).toHaveBeenCalled();
  });
});
