import { describe, expect, it } from "vitest";

import { GEOMETRY_SCENE_INVALID_MESSAGE, validateAndOrderGeometryScene } from "./geometry-scene";
import { cloneSyntheticGeometryScene, syntheticGeometryScene } from "./synthetic-fixtures";

type MutableRecord = Record<string, unknown>;

function sceneRecord(): MutableRecord {
  return cloneSyntheticGeometryScene() as MutableRecord;
}

function objects(scene: MutableRecord): MutableRecord[] {
  return scene.objects as MutableRecord[];
}

function object(scene: MutableRecord, id: string): MutableRecord {
  const match = objects(scene).find((item) => item.id === id);
  if (!match) {
    throw new Error(`Missing fixture object ${id}`);
  }
  return match;
}

function expectInvalid(scene: unknown): void {
  expect(() => validateAndOrderGeometryScene(scene)).toThrow(GEOMETRY_SCENE_INVALID_MESSAGE);
}

describe("validateAndOrderGeometryScene", () => {
  it("returns the same canonical scene with a stable parent-first order", () => {
    const result = validateAndOrderGeometryScene(syntheticGeometryScene);

    expect(result.scene).toBe(syntheticGeometryScene);
    expect(result.constructionOrder).toEqual([
      "A",
      "B",
      "C",
      "M",
      "angleBAC",
      "arcABC",
      "base",
      "circleA",
      "I",
      "circumABC",
      "labelM",
      "parallelC",
      "perpendicularC",
      "rayAC",
      "segmentAB",
      "triangle",
    ]);
    expect(validateAndOrderGeometryScene(syntheticGeometryScene)).toEqual(result);
  });

  it("produces the same order when declarations are permuted", () => {
    const scene = sceneRecord();
    scene.objects = objects(scene).toReversed();

    expect(validateAndOrderGeometryScene(scene).constructionOrder).toEqual(
      validateAndOrderGeometryScene(syntheticGeometryScene).constructionOrder,
    );
  });

  it.each([
    ["duplicate IDs", (scene: MutableRecord) => objects(scene).push({ ...objects(scene)[0] })],
    [
      "unknown parents",
      (scene: MutableRecord) => (object(scene, "segmentAB").parents = ["A", "X"]),
    ],
    ["direct cycles", (scene: MutableRecord) => (object(scene, "base").parents = ["base", "B"])],
    [
      "indirect cycles",
      (scene: MutableRecord) => (object(scene, "base").parents = ["parallelC", "B"]),
    ],
    ["unsupported types", (scene: MutableRecord) => (object(scene, "base").type = "bezier")],
    [
      "non-finite viewport",
      (scene: MutableRecord) => ((scene.viewport as MutableRecord).xMin = NaN),
    ],
    ["reversed viewport", (scene: MutableRecord) => ((scene.viewport as MutableRecord).xMin = 8)],
    ["non-finite coordinates", (scene: MutableRecord) => (object(scene, "A").x = Infinity)],
    ["missing point coordinates", (scene: MutableRecord) => delete object(scene, "A").x],
    ["unknown visible IDs", (scene: MutableRecord) => (scene.initialVisibleObjectIds = ["X"])],
    [
      "duplicate visible IDs",
      (scene: MutableRecord) => (scene.initialVisibleObjectIds = ["A", "A"]),
    ],
    ["blank descriptions", (scene: MutableRecord) => (scene.accessibilityDescription = "  ")],
    ["missing fallback", (scene: MutableRecord) => delete scene.fallbackImageAssetId],
    [
      "wrong parent types",
      (scene: MutableRecord) => (object(scene, "segmentAB").parents = ["base", "B"]),
    ],
    ["constructed dragging", (scene: MutableRecord) => (object(scene, "M").draggable = true)],
    ["label selection", (scene: MutableRecord) => (object(scene, "labelM").selectable = true)],
    [
      "missing intersection branch",
      (scene: MutableRecord) => delete object(scene, "I").intersectionIndex,
    ],
    [
      "duplicate animation IDs",
      (scene: MutableRecord) => (scene.animationIds = ["pulse-A", "pulse-A"]),
    ],
    ["scene scripts", (scene: MutableRecord) => (scene.script = "unsafe()")],
    ["object markup", (scene: MutableRecord) => (object(scene, "A").html = "<b>A</b>")],
  ])("rejects %s atomically", (_label, mutate) => {
    const scene = sceneRecord();
    mutate(scene);

    expectInvalid(scene);
  });
});
