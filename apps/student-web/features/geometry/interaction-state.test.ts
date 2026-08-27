import { describe, expect, it } from "vitest";

import { validateAndOrderGeometryScene } from "./geometry-scene";
import {
  applyGeometryAction,
  createGeometryInteractionState,
  selectGeometryObject,
} from "./interaction-state";
import { syntheticGeometryScene } from "./synthetic-fixtures";

const validatedScene = validateAndOrderGeometryScene(syntheticGeometryScene);

describe("geometry interaction state", () => {
  it("creates deterministic initial visibility in construction order", () => {
    const state = createGeometryInteractionState(validatedScene);

    expect(state.visibleObjectIds).toEqual(validatedScene.constructionOrder);
    expect(state.highlightedObjectIds).toEqual([]);
    expect(state.focusedObjectIds).toEqual([]);
    expect(state.animation).toBeNull();
    expect(state.selectedObjectId).toBeNull();
    expect(state.selection).toBeNull();
    expect(createGeometryInteractionState(validatedScene)).toEqual(state);
  });

  it("applies show and hide without mutating the previous state", () => {
    const initial = createGeometryInteractionState(validatedScene);
    const hidden = applyGeometryAction(validatedScene, initial, {
      type: "hide",
      objectIds: ["circleA", "A"],
    });
    const shown = applyGeometryAction(validatedScene, hidden.state, {
      type: "show",
      objectIds: ["A"],
    });

    expect(hidden.accepted).toBe(true);
    expect(hidden.state.visibleObjectIds).not.toContain("A");
    expect(hidden.state.visibleObjectIds).not.toContain("circleA");
    expect(initial.visibleObjectIds).toContain("A");
    expect(shown.state.visibleObjectIds).toContain("A");
    expect(shown.state.visibleObjectIds).not.toContain("circleA");
  });

  it("applies highlight, targeted and global clear, and focus", () => {
    const initial = createGeometryInteractionState(validatedScene);
    const highlighted = applyGeometryAction(validatedScene, initial, {
      type: "highlight",
      objectIds: ["B", "A"],
    });
    const partiallyCleared = applyGeometryAction(validatedScene, highlighted.state, {
      type: "clear_highlight",
      objectIds: ["B"],
    });
    const focused = applyGeometryAction(validatedScene, partiallyCleared.state, {
      type: "focus",
      objectIds: ["triangle", "A"],
    });
    const cleared = applyGeometryAction(validatedScene, focused.state, {
      type: "clear_highlight",
      objectIds: null,
    });

    expect(highlighted.state.highlightedObjectIds).toEqual(["A", "B"]);
    expect(partiallyCleared.state.highlightedObjectIds).toEqual(["A"]);
    expect(focused.state.focusedObjectIds).toEqual(["A", "triangle"]);
    expect(cleared.state.highlightedObjectIds).toEqual([]);
  });

  it("records only an allowlisted point pulse with a deterministic sequence", () => {
    const initial = createGeometryInteractionState(validatedScene);
    const first = applyGeometryAction(validatedScene, initial, {
      type: "animate",
      objectId: "A",
      animationId: "pulse-A",
    });
    const second = applyGeometryAction(validatedScene, first.state, {
      type: "animate",
      objectId: "A",
      animationId: "pulse-A",
    });

    expect(first.state.animation).toEqual({
      objectId: "A",
      animationId: "pulse-A",
      sequence: 1,
    });
    expect(second.state.animation?.sequence).toBe(2);
  });

  it.each([
    { type: "show", objectIds: ["UNKNOWN"] },
    { type: "animate", objectId: "base", animationId: "pulse-A" },
    { type: "animate", objectId: "A", animationId: "unknown" },
    { type: "show", objectIds: ["A", "A"] },
    { type: "show", objectIds: ["A"], javascript: "unsafe()" },
  ])("rejects an invalid action without changing state", (action) => {
    const initial = createGeometryInteractionState(validatedScene);
    const transition = applyGeometryAction(validatedScene, initial, action);

    expect(transition).toEqual({
      accepted: false,
      state: initial,
      error: "Geometry action is invalid.",
    });
    expect(transition.state).toBe(initial);
  });

  it("enforces ask-select capabilities and returns correct and incorrect states", () => {
    const initial = createGeometryInteractionState(validatedScene);
    const asked = applyGeometryAction(validatedScene, initial, {
      type: "ask_select",
      prompt: [{ id: "select-a", type: "text", text: "Select point A." }],
      allowedObjectIds: ["A", "B"],
      correctObjectIds: ["A"],
    });
    const disallowed = selectGeometryObject(validatedScene, asked.state, "C", "pointer");
    const incorrect = selectGeometryObject(validatedScene, asked.state, "B", "touch");
    const correct = selectGeometryObject(validatedScene, asked.state, "A", "keyboard");

    expect(asked.accepted).toBe(true);
    expect(asked.state.selection).toMatchObject({
      allowedObjectIds: ["A", "B"],
      result: "pending",
      selectedObjectId: null,
    });
    expect(disallowed.accepted).toBe(false);
    expect(disallowed.state).toBe(asked.state);
    expect(incorrect.state.selection).toMatchObject({
      selectedObjectId: "B",
      result: "incorrect",
    });
    expect(correct.state.selection).toMatchObject({
      selectedObjectId: "A",
      result: "correct",
    });
  });

  it("selects configured objects outside a question and rejects locked objects", () => {
    const initial = createGeometryInteractionState(validatedScene);
    const selected = selectGeometryObject(validatedScene, initial, "A", "pointer");
    const locked = selectGeometryObject(validatedScene, initial, "M", "keyboard");

    expect(selected.accepted).toBe(true);
    expect(selected.state.selectedObjectId).toBe("A");
    expect(selected.state.selection).toBeNull();
    expect(locked.accepted).toBe(false);
    expect(locked.state).toBe(initial);
  });

  it("returns the same ungraded response for pointer, touch, and keyboard selection", () => {
    const asked = applyGeometryAction(
      validatedScene,
      createGeometryInteractionState(validatedScene),
      {
        type: "ask_select",
        prompt: [{ id: "select-any", type: "text", text: "Select a point." }],
        allowedObjectIds: ["A"],
        correctObjectIds: null,
      },
    );

    const results = (["pointer", "touch", "keyboard"] as const).map(
      (source) => selectGeometryObject(validatedScene, asked.state, "A", source).state.selection,
    );

    expect(results[0]).toMatchObject({ selectedObjectId: "A", result: "ungraded" });
    expect(results[1]).toEqual(results[0]);
    expect(results[2]).toEqual(results[0]);
    expect(JSON.stringify(results[0])).toBe(JSON.stringify(results[1]));
  });

  it("rejects ask-select IDs that are unknown, duplicated, locked, or outside the allowlist", () => {
    const initial = createGeometryInteractionState(validatedScene);
    const invalidActions = [
      {
        type: "ask_select",
        prompt: [{ id: "p1", type: "text", text: "Select." }],
        allowedObjectIds: ["UNKNOWN"],
      },
      {
        type: "ask_select",
        prompt: [{ id: "p2", type: "text", text: "Select." }],
        allowedObjectIds: ["A", "A"],
      },
      {
        type: "ask_select",
        prompt: [{ id: "p3", type: "text", text: "Select." }],
        allowedObjectIds: ["M"],
      },
      {
        type: "ask_select",
        prompt: [{ id: "p4", type: "text", text: "Select." }],
        allowedObjectIds: ["A"],
        correctObjectIds: ["B"],
      },
    ];

    expect(
      invalidActions.every(
        (action) => !applyGeometryAction(validatedScene, initial, action).accepted,
      ),
    ).toBe(true);
  });
});
