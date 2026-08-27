import { act, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { validateAndOrderGeometryScene } from "../../features/geometry/geometry-scene";
import { createGeometryInteractionState } from "../../features/geometry/interaction-state";
import { syntheticGeometryScene } from "../../features/geometry/synthetic-fixtures";
import { createGeometryConstraintSnapshot, GeometryBoard } from "./geometry-board";

interface FakeElement {
  id: string;
  handlers: Map<string, (event: Event) => void>;
  on: ReturnType<typeof vi.fn>;
  setAttribute: ReturnType<typeof vi.fn>;
  X: () => number;
  Y: () => number;
}

const graph = vi.hoisted(() => {
  const elements = new Map<string, FakeElement>();
  let createFailureAt: number | null = null;
  const create = vi.fn((type: string, parents: unknown[], attributes: Record<string, unknown>) => {
    if (createFailureAt !== null && create.mock.calls.length === createFailureAt) {
      throw new Error("synthetic renderer failure");
    }
    const handlers = new Map<string, (event: Event) => void>();
    const coordinates = type === "point" ? (parents as number[]) : [0, 0];
    const element: FakeElement = {
      id: String(attributes.id),
      handlers,
      on: vi.fn((event: string, handler: (event: Event) => void) => {
        handlers.set(event, handler);
        return element;
      }),
      setAttribute: vi.fn(() => element),
      X: () => coordinates[0] ?? 0,
      Y: () => coordinates[1] ?? 0,
    };
    elements.set(element.id, element);
    return element;
  });
  const board = { create, update: vi.fn() };
  const initBoard = vi.fn(() => board);
  const freeBoard = vi.fn(function (this: unknown) {
    if (this !== jsxGraph) {
      throw new TypeError("freeBoard requires its JSXGraph receiver");
    }
  });
  const jsxGraph = { initBoard, freeBoard };
  return {
    board,
    create,
    elements,
    freeBoard,
    initBoard,
    failCreateAt(index: number | null) {
      createFailureAt = index;
    },
    jsxGraph,
    reset() {
      create.mockClear();
      board.update.mockClear();
      initBoard.mockClear();
      freeBoard.mockClear();
      elements.clear();
      createFailureAt = null;
    },
  };
});

vi.mock("jsxgraph", () => ({
  default: { JSXGraph: graph.jsxGraph },
}));

const scene = validateAndOrderGeometryScene(syntheticGeometryScene);

afterEach(() => {
  graph.reset();
});

describe("GeometryBoard", () => {
  it("constructs every approved primitive in deterministic order with curated parents", async () => {
    const onReady = vi.fn();
    const { unmount } = render(
      <GeometryBoard
        interaction={createGeometryInteractionState(scene)}
        onFailure={vi.fn()}
        onReady={onReady}
        onSelect={vi.fn()}
        scene={scene}
      />,
    );

    expect(
      screen.getByRole("img", { name: syntheticGeometryScene.accessibilityDescription }),
    ).toBeInTheDocument();
    await waitFor(() => expect(onReady).toHaveBeenCalledOnce());
    expect(graph.create.mock.calls.map(([type]) => type)).toEqual([
      "point",
      "point",
      "point",
      "midpoint",
      "angle",
      "arc",
      "line",
      "circle",
      "intersection",
      "circumcircle",
      "text",
      "parallel",
      "perpendicular",
      "line",
      "segment",
      "polygon",
    ]);
    expect(graph.initBoard).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({ title: syntheticGeometryScene.accessibilityDescription }),
    );
    const baseCall = graph.create.mock.calls.find(([, , attributes]) => attributes.id === "base");
    expect(baseCall?.[1]).toEqual([graph.elements.get("A"), graph.elements.get("B")]);
    expect(
      graph.create.mock.calls.find(([, , attributes]) => attributes.id === "A")?.[2],
    ).toMatchObject({
      fixed: false,
    });
    expect(
      graph.create.mock.calls.find(([, , attributes]) => attributes.id === "B")?.[2],
    ).toMatchObject({
      fixed: true,
    });
    expect(
      graph.create.mock.calls.find(([, , attributes]) => attributes.id === "M")?.[2],
    ).toMatchObject({
      fixed: true,
    });
    expect([...(graph.elements.get("A")?.handlers.keys() ?? [])]).toEqual(["down", "drag", "up"]);
    expect(graph.elements.get("B")?.handlers.has("drag")).toBe(false);

    unmount();
    expect(graph.freeBoard).toHaveBeenCalledWith(graph.board);
  });

  it("measures derived midpoint, intersection, line, and circumcircle constraints", () => {
    const point = (x: number, y: number) => ({ X: () => x, Y: () => y });
    const line = (constant: number, x: number, y: number) => ({
      stdform: [constant, x, y],
    });
    const center = point(3, 2);
    const elements = new Map<string, unknown>([
      ["A", point(1, 1)],
      ["B", point(5, 1)],
      ["C", point(2, 4)],
      ["M", point(3, 1)],
      ["I", point(1 + Math.sqrt(10), 1)],
      ["base", line(-1, 0, 1)],
      ["circleA", { center: point(1, 1), Radius: () => Math.sqrt(10) }],
      ["parallelC", line(-4, 0, 1)],
      ["perpendicularC", line(-2, 1, 0)],
      ["circumABC", { center, Radius: () => Math.sqrt(5) }],
    ]);

    const result = createGeometryConstraintSnapshot(scene, elements);

    expect(result.pointCoordinates).toMatchObject({ A: [1, 1], B: [5, 1], M: [3, 1] });
    expect(result.pointCoordinates.I?.[0]).toBeCloseTo(1 + Math.sqrt(10));
    expect(Object.values(result.constraintErrors)).not.toHaveLength(0);
    for (const error of Object.values(result.constraintErrors)) {
      expect(error).toBeLessThan(1e-10);
    }
  });

  it("reports configured pointer and touch selection only", async () => {
    const onSelect = vi.fn();
    render(
      <GeometryBoard
        interaction={createGeometryInteractionState(scene)}
        onFailure={vi.fn()}
        onReady={vi.fn()}
        onSelect={onSelect}
        scene={scene}
      />,
    );
    await waitFor(() => expect(graph.elements.get("A")).toBeDefined());

    act(() =>
      graph.elements.get("A")?.handlers.get("down")?.({ pointerType: "touch" } as PointerEvent),
    );
    act(() =>
      graph.elements.get("B")?.handlers.get("down")?.({ pointerType: "mouse" } as PointerEvent),
    );

    expect(onSelect).toHaveBeenNthCalledWith(1, "A", "touch");
    expect(onSelect).toHaveBeenNthCalledWith(2, "B", "pointer");
    expect(graph.elements.get("M")?.handlers.has("down")).toBe(false);
  });

  it("applies visibility, highlight, focus, selection, and pulse state", async () => {
    const initial = createGeometryInteractionState(scene);
    const { rerender } = render(
      <GeometryBoard
        interaction={initial}
        onFailure={vi.fn()}
        onReady={vi.fn()}
        onSelect={vi.fn()}
        scene={scene}
      />,
    );
    await waitFor(() => expect(graph.elements.get("A")).toBeDefined());

    rerender(
      <GeometryBoard
        interaction={{
          ...initial,
          animation: { objectId: "A", animationId: "pulse-A", sequence: 1 },
          focusedObjectIds: ["triangle"],
          highlightedObjectIds: ["B"],
          selectedObjectId: "A",
          visibleObjectIds: initial.visibleObjectIds.filter((id) => id !== "circleA"),
        }}
        onFailure={vi.fn()}
        onReady={vi.fn()}
        onSelect={vi.fn()}
        scene={scene}
      />,
    );

    await waitFor(() =>
      expect(graph.elements.get("circleA")?.setAttribute).toHaveBeenCalledWith(
        expect.objectContaining({ visible: false }),
      ),
    );
    expect(graph.elements.get("B")?.setAttribute).toHaveBeenCalledWith(
      expect.objectContaining({ strokeColor: "#b54708" }),
    );
    expect(graph.elements.get("triangle")?.setAttribute).toHaveBeenCalledWith(
      expect.objectContaining({ strokeWidth: 4 }),
    );
    expect(graph.elements.get("A")?.setAttribute).toHaveBeenCalledWith(
      expect.objectContaining({ size: 7 }),
    );
  });

  it("frees a partially created board and reports one safe failure", async () => {
    graph.failCreateAt(4);
    const onFailure = vi.fn();
    render(
      <GeometryBoard
        interaction={createGeometryInteractionState(scene)}
        onFailure={onFailure}
        onReady={vi.fn()}
        onSelect={vi.fn()}
        scene={scene}
      />,
    );

    await waitFor(() => expect(onFailure).toHaveBeenCalledOnce());
    expect(graph.freeBoard).toHaveBeenCalledWith(graph.board);
    expect(onFailure).toHaveBeenCalledWith("Geometry renderer failed.");
  });
});
