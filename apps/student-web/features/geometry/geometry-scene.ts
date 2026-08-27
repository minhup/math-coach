import type { components } from "@math-coach/api-client";

export type GeometryScene = components["schemas"]["GeometrySceneVersion"];
export type GeometryObject = components["schemas"]["GeometryObject"];

export const GEOMETRY_SCENE_INVALID_MESSAGE = "Geometry scene data is invalid.";

const IDENTIFIER = /^[A-Za-z][A-Za-z0-9_-]*$/;
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const OBJECT_TYPES = new Set<GeometryObject["type"]>([
  "point",
  "segment",
  "line",
  "ray",
  "circle",
  "arc",
  "polygon",
  "angle",
  "midpoint",
  "intersection",
  "perpendicular",
  "parallel",
  "circumcircle",
  "label",
]);
const POINT_TYPES = new Set<GeometryObject["type"]>(["point", "midpoint", "intersection"]);
const LINE_TYPES = new Set<GeometryObject["type"]>([
  "segment",
  "line",
  "ray",
  "perpendicular",
  "parallel",
]);
const CURVE_TYPES = new Set<GeometryObject["type"]>([...LINE_TYPES, "circle", "circumcircle"]);
const POINT_PARENT_TYPES = new Set<GeometryObject["type"]>([
  "segment",
  "line",
  "ray",
  "circle",
  "arc",
  "polygon",
  "angle",
  "midpoint",
  "circumcircle",
  "label",
]);
const PARENT_COUNTS: Record<GeometryObject["type"], readonly [number, number]> = {
  point: [0, 0],
  segment: [2, 2],
  line: [2, 2],
  ray: [2, 2],
  circle: [2, 2],
  arc: [3, 3],
  polygon: [3, 32],
  angle: [3, 3],
  midpoint: [2, 2],
  intersection: [2, 2],
  perpendicular: [2, 2],
  parallel: [2, 2],
  circumcircle: [3, 3],
  label: [1, 1],
};

const SCENE_KEYS = new Set([
  "id",
  "version",
  "viewport",
  "objects",
  "initialVisibleObjectIds",
  "animationIds",
  "fallbackImageAssetId",
  "accessibilityDescription",
  "provenance",
]);
const OBJECT_KEYS = new Set([
  "id",
  "type",
  "parents",
  "x",
  "y",
  "label",
  "draggable",
  "selectable",
  "intersectionIndex",
]);
const PROVENANCE_KEYS = new Set([
  "sourceKind",
  "title",
  "creator",
  "sourceReference",
  "acquisitionDate",
  "acquiredBy",
  "rightsBasis",
  "rightsEvidence",
  "permittedUses",
  "restrictions",
  "attributionText",
  "adaptationDescription",
  "translationDescription",
  "derivativeOf",
  "mathematicsReviewer",
  "mathematicsReviewedAt",
  "rightsReviewer",
  "rightsReviewedAt",
  "publicationStatus",
  "publicationDate",
]);

export class GeometrySceneValidationError extends Error {
  constructor() {
    super(GEOMETRY_SCENE_INVALID_MESSAGE);
    this.name = "GeometrySceneValidationError";
  }
}

export interface ValidatedGeometryScene {
  readonly scene: GeometryScene;
  readonly constructionOrder: readonly string[];
}

function invalid(): never {
  throw new GeometrySceneValidationError();
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function hasOnlyKeys(value: Record<string, unknown>, keys: ReadonlySet<string>): boolean {
  return Object.keys(value).every((key) => keys.has(key));
}

function isNonBlankString(value: unknown): value is string {
  return typeof value === "string" && value.trim().length > 0;
}

function isIdentifier(value: unknown): value is string {
  return typeof value === "string" && IDENTIFIER.test(value);
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((item) => typeof item === "string");
}

function isUnique(values: readonly string[]): boolean {
  return values.length === new Set(values).size;
}

function isOptionalString(value: unknown): boolean {
  return value === undefined || value === null || isNonBlankString(value);
}

function isOptionalBoolean(value: unknown): boolean {
  return value === undefined || value === null || typeof value === "boolean";
}

function validateProvenance(value: unknown): void {
  if (!isRecord(value) || !hasOnlyKeys(value, PROVENANCE_KEYS)) {
    invalid();
  }
  const stringKeys = [
    "title",
    "creator",
    "sourceReference",
    "acquisitionDate",
    "acquiredBy",
    "rightsEvidence",
    "attributionText",
    "mathematicsReviewer",
    "mathematicsReviewedAt",
    "rightsReviewer",
    "rightsReviewedAt",
    "publicationDate",
  ];
  if (
    !stringKeys.every((key) => isNonBlankString(value[key])) ||
    value.sourceKind !== "original_synthetic" ||
    value.rightsBasis !== "original_fixture" ||
    value.publicationStatus !== "synthetic_only" ||
    !isStringArray(value.permittedUses) ||
    value.permittedUses.length === 0 ||
    !value.permittedUses.every(isNonBlankString) ||
    !isStringArray(value.restrictions) ||
    !value.restrictions.every(isNonBlankString) ||
    !isStringArray(value.derivativeOf) ||
    !value.derivativeOf.every((id) => UUID.test(id)) ||
    !isOptionalString(value.adaptationDescription) ||
    !isOptionalString(value.translationDescription)
  ) {
    invalid();
  }
}

function validateViewport(value: unknown): void {
  if (
    !isRecord(value) ||
    !hasOnlyKeys(value, new Set(["xMin", "xMax", "yMin", "yMax"])) ||
    ![value.xMin, value.xMax, value.yMin, value.yMax].every(
      (coordinate) => typeof coordinate === "number" && Number.isFinite(coordinate),
    ) ||
    (value.xMin as number) >= (value.xMax as number) ||
    (value.yMin as number) >= (value.yMax as number)
  ) {
    invalid();
  }
}

function validateObject(value: unknown): asserts value is GeometryObject {
  if (
    !isRecord(value) ||
    !hasOnlyKeys(value, OBJECT_KEYS) ||
    !isIdentifier(value.id) ||
    typeof value.type !== "string" ||
    !OBJECT_TYPES.has(value.type as GeometryObject["type"]) ||
    !isOptionalString(value.label) ||
    !isOptionalBoolean(value.draggable) ||
    !isOptionalBoolean(value.selectable)
  ) {
    invalid();
  }
  const type = value.type as GeometryObject["type"];
  const parents = value.parents === undefined ? [] : value.parents;
  if (!isStringArray(parents) || !parents.every(isIdentifier) || !isUnique(parents)) {
    invalid();
  }
  const [minimumParents, maximumParents] = PARENT_COUNTS[type];
  if (parents.length < minimumParents || parents.length > maximumParents) {
    invalid();
  }
  const xIsFinite = typeof value.x === "number" && Number.isFinite(value.x);
  const yIsFinite = typeof value.y === "number" && Number.isFinite(value.y);
  if (type === "point") {
    if (!xIsFinite || !yIsFinite) {
      invalid();
    }
  } else if (
    (value.x !== undefined && value.x !== null) ||
    (value.y !== undefined && value.y !== null)
  ) {
    invalid();
  }
  if (value.draggable === true && type !== "point") {
    invalid();
  }
  if (value.selectable === true && type === "label") {
    invalid();
  }
  if (type === "intersection") {
    if (value.intersectionIndex !== 0 && value.intersectionIndex !== 1) {
      invalid();
    }
  } else if (value.intersectionIndex !== undefined && value.intersectionIndex !== null) {
    invalid();
  }
  if (type === "label" && !isNonBlankString(value.label)) {
    invalid();
  }
}

function stableConstructionOrder(objects: readonly GeometryObject[]): readonly string[] {
  const parentsById = new Map(objects.map((item) => [item.id, item.parents ?? []] as const));
  const remaining = new Set(parentsById.keys());
  const constructed = new Set<string>();
  const order: string[] = [];
  while (remaining.size > 0) {
    const ready = [...remaining]
      .filter((id) => parentsById.get(id)?.every((parentId) => constructed.has(parentId)))
      .sort();
    if (ready.length === 0) {
      invalid();
    }
    const next = ready[0];
    remaining.delete(next);
    constructed.add(next);
    order.push(next);
  }
  return order;
}

function validateParentTypes(objects: readonly GeometryObject[]): void {
  const objectById = new Map(objects.map((item) => [item.id, item] as const));
  for (const item of objects) {
    const parents = (item.parents ?? []).map((id) => objectById.get(id));
    if (parents.some((parent) => parent === undefined)) {
      invalid();
    }
    const parentTypes = parents.map((parent) => parent?.type);
    if (POINT_PARENT_TYPES.has(item.type) && !parentTypes.every((type) => POINT_TYPES.has(type!))) {
      invalid();
    }
    if (item.type === "intersection" && !parentTypes.every((type) => CURVE_TYPES.has(type!))) {
      invalid();
    }
    if (
      (item.type === "perpendicular" || item.type === "parallel") &&
      (!LINE_TYPES.has(parentTypes[0]!) || !POINT_TYPES.has(parentTypes[1]!))
    ) {
      invalid();
    }
  }
}

export function validateAndOrderGeometryScene(value: unknown): ValidatedGeometryScene {
  if (
    !isRecord(value) ||
    !hasOnlyKeys(value, SCENE_KEYS) ||
    typeof value.id !== "string" ||
    !UUID.test(value.id) ||
    !Number.isInteger(value.version) ||
    (value.version as number) < 1 ||
    !Array.isArray(value.objects) ||
    value.objects.length === 0 ||
    !isStringArray(value.initialVisibleObjectIds) ||
    value.initialVisibleObjectIds.length === 0 ||
    !isStringArray(value.animationIds) ||
    !isIdentifier(value.fallbackImageAssetId) ||
    !isNonBlankString(value.accessibilityDescription)
  ) {
    invalid();
  }
  validateViewport(value.viewport);
  validateProvenance(value.provenance);
  value.objects.forEach(validateObject);

  const scene = value as unknown as GeometryScene;
  const objectIds = scene.objects.map((item) => item.id);
  if (
    !isUnique(objectIds) ||
    !isUnique(scene.initialVisibleObjectIds) ||
    !scene.initialVisibleObjectIds.every((id) => objectIds.includes(id)) ||
    !isUnique(scene.animationIds)
  ) {
    invalid();
  }
  for (const item of scene.objects) {
    if (!(item.parents ?? []).every((parentId) => objectIds.includes(parentId))) {
      invalid();
    }
  }
  const constructionOrder = stableConstructionOrder(scene.objects);
  validateParentTypes(scene.objects);
  return { scene, constructionOrder };
}
