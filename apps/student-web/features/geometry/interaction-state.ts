import type { ContentBlock, GeometryAction } from "../../lib/api";
import type { ValidatedGeometryScene } from "./geometry-scene";

export const GEOMETRY_ACTION_INVALID_MESSAGE = "Geometry action is invalid.";

export type SelectionResult = "pending" | "correct" | "incorrect" | "ungraded";
export type SelectionSource = "pointer" | "touch" | "keyboard";

export interface GeometrySelectionState {
  readonly prompt: readonly ContentBlock[];
  readonly allowedObjectIds: readonly string[];
  readonly correctObjectIds: readonly string[] | null;
  readonly selectedObjectId: string | null;
  readonly result: SelectionResult;
}

export interface GeometryAnimationState {
  readonly objectId: string;
  readonly animationId: string;
  readonly sequence: number;
}

export interface GeometryInteractionState {
  readonly visibleObjectIds: readonly string[];
  readonly highlightedObjectIds: readonly string[];
  readonly focusedObjectIds: readonly string[];
  readonly animation: GeometryAnimationState | null;
  readonly selection: GeometrySelectionState | null;
}

export type GeometryInteractionTransition =
  | { readonly accepted: true; readonly state: GeometryInteractionState }
  | {
      readonly accepted: false;
      readonly state: GeometryInteractionState;
      readonly error: typeof GEOMETRY_ACTION_INVALID_MESSAGE;
    };

const IDENTIFIER = /^[A-Za-z][A-Za-z0-9_-]*$/;
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const POINT_TYPES = new Set(["point", "midpoint", "intersection"]);

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function hasOnlyKeys(value: Record<string, unknown>, keys: readonly string[]): boolean {
  const allowed = new Set(keys);
  return Object.keys(value).every((key) => allowed.has(key));
}

function isIdentifier(value: unknown): value is string {
  return typeof value === "string" && IDENTIFIER.test(value);
}

function isNonBlankString(value: unknown): value is string {
  return typeof value === "string" && value.trim().length > 0;
}

function isIdentifierList(value: unknown, allowEmpty = false): value is string[] {
  return (
    Array.isArray(value) &&
    (allowEmpty || value.length > 0) &&
    value.every(isIdentifier) &&
    value.length === new Set(value).size
  );
}

function isContentBlock(value: unknown): value is ContentBlock {
  if (!isRecord(value) || !isIdentifier(value.id) || typeof value.type !== "string") {
    return false;
  }
  switch (value.type) {
    case "text":
      return hasOnlyKeys(value, ["id", "type", "text"]) && isNonBlankString(value.text);
    case "inline_math":
    case "display_math":
      return hasOnlyKeys(value, ["id", "type", "latex"]) && isNonBlankString(value.latex);
    case "rich_line":
      return (
        hasOnlyKeys(value, ["id", "type", "spans"]) &&
        Array.isArray(value.spans) &&
        value.spans.length > 0 &&
        value.spans.every(
          (span) =>
            isRecord(span) &&
            ((span.type === "text" &&
              hasOnlyKeys(span, ["type", "text"]) &&
              isNonBlankString(span.text)) ||
              (span.type === "math" &&
                hasOnlyKeys(span, ["type", "latex"]) &&
                isNonBlankString(span.latex))),
        )
      );
    case "geometry":
      return (
        hasOnlyKeys(value, ["id", "type", "sceneVersionId"]) &&
        typeof value.sceneVersionId === "string" &&
        UUID.test(value.sceneVersionId)
      );
    case "image":
      return (
        hasOnlyKeys(value, ["id", "type", "assetId", "alt"]) &&
        isIdentifier(value.assetId) &&
        isNonBlankString(value.alt)
      );
    case "callout":
      return (
        hasOnlyKeys(value, ["id", "type", "kind", "content"]) &&
        ["note", "warning", "hint", "success"].includes(String(value.kind)) &&
        Array.isArray(value.content) &&
        value.content.length > 0 &&
        value.content.every(isContentBlock)
      );
    default:
      return false;
  }
}

function objectIdsAreKnown(scene: ValidatedGeometryScene, objectIds: readonly string[]): boolean {
  const known = new Set(scene.scene.objects.map((item) => item.id));
  return objectIds.every((id) => known.has(id));
}

export function validateGeometryAction(
  scene: ValidatedGeometryScene,
  value: unknown,
): GeometryAction | null {
  if (!isRecord(value) || typeof value.type !== "string") {
    return null;
  }
  switch (value.type) {
    case "show":
    case "hide":
    case "highlight":
    case "focus":
      if (
        !hasOnlyKeys(value, ["type", "objectIds"]) ||
        !isIdentifierList(value.objectIds) ||
        !objectIdsAreKnown(scene, value.objectIds)
      ) {
        return null;
      }
      return value as GeometryAction;
    case "clear_highlight": {
      if (!hasOnlyKeys(value, ["type", "objectIds"])) {
        return null;
      }
      const ids = value.objectIds;
      if (
        ids !== undefined &&
        ids !== null &&
        (!isIdentifierList(ids, true) || !objectIdsAreKnown(scene, ids))
      ) {
        return null;
      }
      return value as GeometryAction;
    }
    case "animate": {
      if (
        !hasOnlyKeys(value, ["type", "objectId", "animationId"]) ||
        !isIdentifier(value.objectId) ||
        !isIdentifier(value.animationId) ||
        !scene.scene.animationIds.includes(value.animationId)
      ) {
        return null;
      }
      const object = scene.scene.objects.find((item) => item.id === value.objectId);
      if (!object || !POINT_TYPES.has(object.type)) {
        return null;
      }
      return value as GeometryAction;
    }
    case "ask_select": {
      if (
        !hasOnlyKeys(value, ["type", "prompt", "allowedObjectIds", "correctObjectIds"]) ||
        !Array.isArray(value.prompt) ||
        value.prompt.length === 0 ||
        !value.prompt.every(isContentBlock) ||
        !isIdentifierList(value.allowedObjectIds) ||
        !objectIdsAreKnown(scene, value.allowedObjectIds)
      ) {
        return null;
      }
      const allowed = value.allowedObjectIds;
      const selectable = new Set(
        scene.scene.objects.filter((item) => item.selectable === true).map((item) => item.id),
      );
      if (!allowed.every((id) => selectable.has(id))) {
        return null;
      }
      const correct = value.correctObjectIds;
      if (
        correct !== undefined &&
        correct !== null &&
        (!isIdentifierList(correct, true) || !correct.every((id) => allowed.includes(id)))
      ) {
        return null;
      }
      return value as GeometryAction;
    }
    default:
      return null;
  }
}

function orderIds(scene: ValidatedGeometryScene, ids: ReadonlySet<string>): readonly string[] {
  return scene.constructionOrder.filter((id) => ids.has(id));
}

function accepted(state: GeometryInteractionState): GeometryInteractionTransition {
  return { accepted: true, state };
}

function rejected(state: GeometryInteractionState): GeometryInteractionTransition {
  return { accepted: false, state, error: GEOMETRY_ACTION_INVALID_MESSAGE };
}

export function createGeometryInteractionState(
  scene: ValidatedGeometryScene,
): GeometryInteractionState {
  return {
    visibleObjectIds: orderIds(scene, new Set(scene.scene.initialVisibleObjectIds)),
    highlightedObjectIds: [],
    focusedObjectIds: [],
    animation: null,
    selection: null,
  };
}

export function applyGeometryAction(
  scene: ValidatedGeometryScene,
  state: GeometryInteractionState,
  value: unknown,
): GeometryInteractionTransition {
  const action = validateGeometryAction(scene, value);
  if (!action) {
    return rejected(state);
  }
  switch (action.type) {
    case "show":
      return accepted({
        ...state,
        visibleObjectIds: orderIds(
          scene,
          new Set([...state.visibleObjectIds, ...action.objectIds]),
        ),
      });
    case "hide": {
      const hidden = new Set(action.objectIds);
      return accepted({
        ...state,
        visibleObjectIds: state.visibleObjectIds.filter((id) => !hidden.has(id)),
      });
    }
    case "highlight":
      return accepted({
        ...state,
        highlightedObjectIds: orderIds(
          scene,
          new Set([...state.highlightedObjectIds, ...action.objectIds]),
        ),
      });
    case "clear_highlight": {
      const cleared = new Set(action.objectIds ?? state.highlightedObjectIds);
      return accepted({
        ...state,
        highlightedObjectIds: state.highlightedObjectIds.filter((id) => !cleared.has(id)),
      });
    }
    case "focus":
      return accepted({ ...state, focusedObjectIds: orderIds(scene, new Set(action.objectIds)) });
    case "animate":
      return accepted({
        ...state,
        animation: {
          objectId: action.objectId,
          animationId: action.animationId,
          sequence: (state.animation?.sequence ?? 0) + 1,
        },
      });
    case "ask_select":
      return accepted({
        ...state,
        selection: {
          prompt: action.prompt,
          allowedObjectIds: orderIds(scene, new Set(action.allowedObjectIds)),
          correctObjectIds:
            action.correctObjectIds == null
              ? null
              : orderIds(scene, new Set(action.correctObjectIds)),
          selectedObjectId: null,
          result: "pending",
        },
      });
  }
}

export function selectGeometryObject(
  scene: ValidatedGeometryScene,
  state: GeometryInteractionState,
  objectId: unknown,
  source: unknown,
): GeometryInteractionTransition {
  if (
    !isIdentifier(objectId) ||
    (source !== "pointer" && source !== "touch" && source !== "keyboard") ||
    !state.selection ||
    !state.selection.allowedObjectIds.includes(objectId)
  ) {
    return rejected(state);
  }
  const object = scene.scene.objects.find((item) => item.id === objectId);
  if (!object || object.selectable !== true) {
    return rejected(state);
  }
  const result = state.selection.correctObjectIds
    ? state.selection.correctObjectIds.includes(objectId)
      ? "correct"
      : "incorrect"
    : "ungraded";
  return accepted({
    ...state,
    selection: { ...state.selection, selectedObjectId: objectId, result },
  });
}
