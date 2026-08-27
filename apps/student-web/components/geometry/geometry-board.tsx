"use client";

import { useEffect, useId, useRef } from "react";

import type { ValidatedGeometryScene } from "../../features/geometry/geometry-scene";
import type {
  GeometryInteractionState,
  SelectionSource,
} from "../../features/geometry/interaction-state";

export const GEOMETRY_RENDERER_FAILED_MESSAGE = "Geometry renderer failed.";

export interface GeometryConstraintSnapshot {
  readonly pointCoordinates: Readonly<Record<string, readonly [number, number]>>;
  readonly constraintErrors: Readonly<Record<string, number>>;
}

interface GeometryBoardProps {
  readonly scene: ValidatedGeometryScene;
  readonly interaction: GeometryInteractionState;
  readonly onSelect: (objectId: string, source: SelectionSource) => void;
  readonly onReady: () => void;
  readonly onFailure: (message: typeof GEOMETRY_RENDERER_FAILED_MESSAGE) => void;
  readonly onSnapshot?: (snapshot: GeometryConstraintSnapshot) => void;
}

type RenderedElement = JXG.GeometryElement;

interface CoordinateElement {
  X(): number;
  Y(): number;
}

interface LineElement {
  point1: unknown;
  point2: unknown;
  stdform: unknown;
}

interface CircleElement {
  center: unknown;
  Radius(): number;
}

function isCoordinatePair(
  value: readonly [number, number] | null,
): value is readonly [number, number] {
  return value !== null;
}

function coordinates(element: unknown): readonly [number, number] | null {
  if (typeof element !== "object" || element === null) {
    return null;
  }
  const candidate = element as Partial<CoordinateElement>;
  if (typeof candidate.X !== "function" || typeof candidate.Y !== "function") {
    return null;
  }
  const x = candidate.X.call(element);
  const y = candidate.Y.call(element);
  return Number.isFinite(x) && Number.isFinite(y) ? [x, y] : null;
}

function lineEndpoints(
  element: unknown,
): readonly [readonly [number, number], readonly [number, number]] | null {
  if (typeof element !== "object" || element === null) {
    return null;
  }
  const line = element as Partial<LineElement>;
  const first = coordinates(line.point1);
  const second = coordinates(line.point2);
  return first && second ? [first, second] : null;
}

function circleData(
  element: unknown,
): { center: readonly [number, number]; radius: number } | null {
  if (typeof element !== "object" || element === null) {
    return null;
  }
  const circle = element as Partial<CircleElement>;
  const center = coordinates(circle.center);
  if (!center || typeof circle.Radius !== "function") {
    return null;
  }
  const radius = circle.Radius.call(element);
  return Number.isFinite(radius) ? { center, radius } : null;
}

function distance(first: readonly [number, number], second: readonly [number, number]): number {
  return Math.hypot(first[0] - second[0], first[1] - second[1]);
}

function lineCoefficients(element: unknown): readonly [number, number, number] | null {
  if (typeof element !== "object" || element === null) {
    return null;
  }
  const stdform = (element as Partial<LineElement>).stdform;
  if (
    !Array.isArray(stdform) ||
    stdform.length < 3 ||
    !stdform.slice(0, 3).every((value) => typeof value === "number" && Number.isFinite(value))
  ) {
    return null;
  }
  return [stdform[0] as number, stdform[1] as number, stdform[2] as number];
}

function lineDirection(element: unknown): readonly [number, number] | null {
  const coefficients = lineCoefficients(element);
  if (coefficients) {
    return [coefficients[2], -coefficients[1]];
  }
  const endpoints = lineEndpoints(element);
  return endpoints ? [endpoints[1][0] - endpoints[0][0], endpoints[1][1] - endpoints[0][1]] : null;
}

function distanceToLine(point: readonly [number, number], element: unknown): number | null {
  const coefficients = lineCoefficients(element);
  if (coefficients) {
    const [constant, xCoefficient, yCoefficient] = coefficients;
    const denominator = Math.hypot(xCoefficient, yCoefficient);
    return denominator === 0
      ? Number.POSITIVE_INFINITY
      : Math.abs(constant + xCoefficient * point[0] + yCoefficient * point[1]) / denominator;
  }
  const endpoints = lineEndpoints(element);
  if (!endpoints) {
    return null;
  }
  const [[x1, y1], [x2, y2]] = endpoints;
  const denominator = Math.hypot(x2 - x1, y2 - y1);
  return denominator === 0
    ? Number.POSITIVE_INFINITY
    : Math.abs((y2 - y1) * point[0] - (x2 - x1) * point[1] + x2 * y1 - y2 * x1) / denominator;
}

function metric(value: number): number {
  return Number(value.toPrecision(12));
}

export function createGeometryConstraintSnapshot(
  scene: ValidatedGeometryScene,
  elements: ReadonlyMap<string, unknown>,
): GeometryConstraintSnapshot {
  const pointCoordinates: Record<string, readonly [number, number]> = {};
  const constraintErrors: Record<string, number> = {};
  const definitions = new Map(scene.scene.objects.map((item) => [item.id, item] as const));

  for (const item of scene.scene.objects) {
    const point = coordinates(elements.get(item.id));
    if (point && ["point", "midpoint", "intersection"].includes(item.type)) {
      pointCoordinates[item.id] = [metric(point[0]), metric(point[1])];
    }
    if (item.type === "midpoint" && point) {
      const first = coordinates(elements.get(item.parents?.[0] ?? ""));
      const second = coordinates(elements.get(item.parents?.[1] ?? ""));
      if (first && second) {
        constraintErrors[`midpoint:${item.id}`] = metric(
          distance(point, [(first[0] + second[0]) / 2, (first[1] + second[1]) / 2]),
        );
      }
    }
    if (item.type === "intersection" && point) {
      for (const parentId of item.parents ?? []) {
        const parentDefinition = definitions.get(parentId);
        const parentElement = elements.get(parentId);
        if (parentDefinition && ["circle", "circumcircle"].includes(parentDefinition.type)) {
          const circle = circleData(parentElement);
          if (circle) {
            constraintErrors[`intersection:${item.id}:${parentId}`] = metric(
              Math.abs(distance(point, circle.center) - circle.radius),
            );
          }
        } else {
          const error = distanceToLine(point, parentElement);
          if (error !== null) {
            constraintErrors[`intersection:${item.id}:${parentId}`] = metric(error);
          }
        }
      }
    }
    if (item.type === "perpendicular" || item.type === "parallel") {
      const parentVector = lineDirection(elements.get(item.parents?.[0] ?? ""));
      const constructedVector = lineDirection(elements.get(item.id));
      if (parentVector && constructedVector) {
        const scale = Math.hypot(...parentVector) * Math.hypot(...constructedVector);
        const raw =
          item.type === "perpendicular"
            ? Math.abs(
                parentVector[0] * constructedVector[0] + parentVector[1] * constructedVector[1],
              )
            : Math.abs(
                parentVector[0] * constructedVector[1] - parentVector[1] * constructedVector[0],
              );
        constraintErrors[`${item.type}:${item.id}`] = metric(
          scale === 0 ? Number.POSITIVE_INFINITY : raw / scale,
        );
      }
    }
    if (item.type === "circumcircle") {
      const circle = circleData(elements.get(item.id));
      const vertices = (item.parents ?? []).map((id) => coordinates(elements.get(id)));
      if (circle && vertices.every(isCoordinatePair)) {
        const radii = vertices.map((vertex) => distance(circle.center, vertex));
        constraintErrors[`circumcircle:${item.id}`] = metric(
          Math.max(...radii) - Math.min(...radii),
        );
      }
    }
  }

  return { pointCoordinates, constraintErrors };
}

function parentElements(
  objectId: string,
  parentIds: readonly string[],
  elements: ReadonlyMap<string, RenderedElement>,
): RenderedElement[] {
  return parentIds.map((parentId) => {
    const parent = elements.get(parentId);
    if (!parent) {
      throw new Error(`Validated parent missing for ${objectId}`);
    }
    return parent;
  });
}

function createElement(
  board: JXG.Board,
  item: ValidatedGeometryScene["scene"]["objects"][number],
  elements: ReadonlyMap<string, RenderedElement>,
  visible: boolean,
): RenderedElement {
  const parents = parentElements(item.id, item.parents ?? [], elements);
  const attributes: Record<string, unknown> = {
    fixed: true,
    highlight: false,
    id: item.id,
    name: item.label ?? "",
    visible,
    withLabel: Boolean(item.label),
  };
  switch (item.type) {
    case "point":
      if (typeof item.x !== "number" || typeof item.y !== "number") {
        throw new Error("Validated free point coordinates are missing");
      }
      return board.create<RenderedElement>("point", [item.x, item.y], {
        ...attributes,
        fixed: item.draggable !== true,
        size: 4,
      });
    case "segment":
      return board.create<RenderedElement>("segment", parents, attributes);
    case "line":
      return board.create<RenderedElement>("line", parents, {
        ...attributes,
        straightFirst: true,
        straightLast: true,
      });
    case "ray":
      return board.create<RenderedElement>("line", parents, {
        ...attributes,
        straightFirst: false,
        straightLast: true,
      });
    case "circle":
      return board.create<RenderedElement>("circle", parents, attributes);
    case "arc":
      return board.create<RenderedElement>("arc", parents, attributes);
    case "polygon":
      return board.create<RenderedElement>("polygon", parents, {
        ...attributes,
        borders: { fixed: true, highlight: false },
        fillColor: "#dbeafe",
        fillOpacity: 0.22,
      });
    case "angle":
      return board.create<RenderedElement>("angle", parents, {
        ...attributes,
        fillColor: "#dbeafe",
        radius: 0.75,
      });
    case "midpoint":
      return board.create<RenderedElement>("midpoint", parents, { ...attributes, size: 4 });
    case "intersection":
      return board.create<RenderedElement>("intersection", [...parents, item.intersectionIndex], {
        ...attributes,
        size: 4,
      });
    case "perpendicular":
      return board.create<RenderedElement>("perpendicular", parents, attributes);
    case "parallel":
      return board.create<RenderedElement>("parallel", parents, attributes);
    case "circumcircle":
      return board.create<RenderedElement>("circumcircle", parents, attributes);
    case "label": {
      const anchor = parents[0];
      return board.create<RenderedElement>(
        "text",
        [
          () => (coordinates(anchor)?.[0] ?? 0) + 0.35,
          () => (coordinates(anchor)?.[1] ?? 0) + 0.55,
          item.label ?? "",
        ],
        {
          ...attributes,
          display: "internal",
          parse: false,
          useMathJax: false,
          withLabel: false,
        },
      );
    }
  }
}

function selectionSource(event: Event): SelectionSource {
  if (("pointerType" in event && event.pointerType === "touch") || "touches" in event) {
    return "touch";
  }
  return "pointer";
}

function applyInteraction(
  scene: ValidatedGeometryScene,
  interaction: GeometryInteractionState,
  elements: ReadonlyMap<string, RenderedElement>,
): void {
  const visible = new Set(interaction.visibleObjectIds);
  const highlighted = new Set(interaction.highlightedObjectIds);
  const focused = new Set(interaction.focusedObjectIds);
  for (const item of scene.scene.objects) {
    const element = elements.get(item.id);
    if (!element) {
      throw new Error("Validated geometry element is missing");
    }
    const isSelected = interaction.selectedObjectId === item.id;
    const isHighlighted = highlighted.has(item.id);
    const isFocused = focused.has(item.id);
    element.setAttribute({
      fillColor: isSelected ? "#7c3aed" : isHighlighted ? "#fef0c7" : "#dbeafe",
      strokeColor: isSelected
        ? "#7c3aed"
        : isHighlighted
          ? "#b54708"
          : isFocused
            ? "#087f5b"
            : "#164e63",
      strokeWidth: isFocused ? 4 : isHighlighted || isSelected ? 3 : 2,
      visible: visible.has(item.id),
    });
    if (["point", "midpoint", "intersection"].includes(item.type)) {
      (element as JXG.Point).setAttribute({ size: isSelected ? 7 : isHighlighted ? 6 : 4 });
    }
  }
}

export function GeometryBoard({
  scene,
  interaction,
  onSelect,
  onReady,
  onFailure,
  onSnapshot,
}: GeometryBoardProps) {
  const reactId = useId();
  const boardId = `geometry-board-${reactId.replaceAll(":", "")}`;
  const boardRef = useRef<JXG.Board | null>(null);
  const elementsRef = useRef<Map<string, RenderedElement>>(new Map());
  const freeBoardRef = useRef<((board: JXG.Board) => void) | null>(null);
  const pulseTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const interactionRef = useRef(interaction);

  useEffect(() => {
    interactionRef.current = interaction;
  }, [interaction]);

  useEffect(() => {
    let disposed = false;
    const elements = new Map<string, RenderedElement>();
    elementsRef.current = elements;
    const setup = async () => {
      let board: JXG.Board | null = null;
      try {
        const JXGModule = await import("jsxgraph");
        if (disposed) {
          return;
        }
        board = JXGModule.default.JSXGraph.initBoard(boardId, {
          axis: true,
          boundingbox: [
            scene.scene.viewport.xMin,
            scene.scene.viewport.yMax,
            scene.scene.viewport.xMax,
            scene.scene.viewport.yMin,
          ],
          keepaspectratio: true,
          pan: { enabled: false },
          showCopyright: false,
          showNavigation: false,
          title: scene.scene.accessibilityDescription,
          zoom: { wheel: false },
        });
        boardRef.current = board;
        freeBoardRef.current = JXGModule.default.JSXGraph.freeBoard;
        const visible = new Set(interactionRef.current.visibleObjectIds);
        for (const objectId of scene.constructionOrder) {
          const item = scene.scene.objects.find((candidate) => candidate.id === objectId);
          if (!item) {
            throw new Error("Validated geometry definition is missing");
          }
          const element = createElement(board, item, elements, visible.has(item.id));
          elements.set(item.id, element);
          if (item.selectable === true) {
            element.on("down", (event) => onSelect(item.id, selectionSource(event)));
          }
          if (item.type === "point" && item.draggable === true) {
            const reportConstraintSnapshot = () => {
              onSnapshot?.(createGeometryConstraintSnapshot(scene, elements));
            };
            element.on("drag", reportConstraintSnapshot);
            element.on("up", reportConstraintSnapshot);
          }
        }
        applyInteraction(scene, interactionRef.current, elements);
        board.update();
        onSnapshot?.(createGeometryConstraintSnapshot(scene, elements));
        onReady();
      } catch {
        if (board) {
          freeBoardRef.current?.(board);
        }
        boardRef.current = null;
        elements.clear();
        onFailure(GEOMETRY_RENDERER_FAILED_MESSAGE);
      }
    };
    void setup();
    return () => {
      disposed = true;
      if (pulseTimerRef.current) {
        clearTimeout(pulseTimerRef.current);
      }
      if (boardRef.current) {
        freeBoardRef.current?.(boardRef.current);
      }
      boardRef.current = null;
      elements.clear();
    };
  }, [boardId, onFailure, onReady, onSelect, onSnapshot, scene]);

  useEffect(() => {
    const board = boardRef.current;
    if (!board) {
      return;
    }
    try {
      applyInteraction(scene, interaction, elementsRef.current);
      if (interaction.animation) {
        const element = elementsRef.current.get(interaction.animation.objectId);
        element?.setAttribute({ strokeColor: "#b54708" });
        (element as JXG.Point | undefined)?.setAttribute({ size: 8 });
        if (!globalThis.matchMedia?.("(prefers-reduced-motion: reduce)").matches) {
          if (pulseTimerRef.current) {
            clearTimeout(pulseTimerRef.current);
          }
          pulseTimerRef.current = setTimeout(() => {
            applyInteraction(scene, interactionRef.current, elementsRef.current);
            boardRef.current?.update();
          }, 500);
        }
      }
      board.update();
    } catch {
      onFailure(GEOMETRY_RENDERER_FAILED_MESSAGE);
    }
  }, [interaction, onFailure, scene]);

  return (
    <div
      aria-label={scene.scene.accessibilityDescription}
      className="geometry-board jxgbox"
      data-testid="geometry-board"
      id={boardId}
      role="img"
      tabIndex={-1}
    />
  );
}
