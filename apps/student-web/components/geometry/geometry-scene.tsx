"use client";

import Image from "next/image";
import { useCallback, useMemo, useState } from "react";

import {
  type ValidatedGeometryScene,
  validateAndOrderGeometryScene,
} from "../../features/geometry/geometry-scene";
import {
  applyGeometryAction,
  createGeometryInteractionState,
  selectGeometryObject,
  type GeometryInteractionState,
  type SelectionSource,
  validateGeometryAction,
} from "../../features/geometry/interaction-state";
import type { GeometryAction } from "../../lib/api";
import { TypedContentBlocks } from "../math/content-blocks";
import { GeometryBoard, type GeometryConstraintSnapshot } from "./geometry-board";

const IDENTIFIER = /^[A-Za-z][A-Za-z0-9_-]*$/;

interface GeometrySceneProps {
  readonly scene: unknown;
  readonly actions?: readonly unknown[];
  readonly showConstraintSnapshot?: boolean;
}

interface SafeFallbackData {
  readonly assetId: string;
  readonly description: string;
}

function safeFallbackData(scene: unknown): SafeFallbackData | null {
  if (typeof scene !== "object" || scene === null || Array.isArray(scene)) {
    return null;
  }
  const record = scene as Record<string, unknown>;
  return typeof record.fallbackImageAssetId === "string" &&
    IDENTIFIER.test(record.fallbackImageAssetId) &&
    typeof record.accessibilityDescription === "string" &&
    record.accessibilityDescription.trim().length > 0
    ? {
        assetId: record.fallbackImageAssetId,
        description: record.accessibilityDescription,
      }
    : null;
}

function StaticFallback({ data }: { readonly data: SafeFallbackData }) {
  return (
    <figure className="geometry-static-fallback">
      <Image
        alt={`${data.description} Static fallback.`}
        height={800}
        src={`/fixtures/${data.assetId}.svg`}
        unoptimized
        width={1200}
      />
      <figcaption>Static fallback for this curated scene.</figcaption>
    </figure>
  );
}

function actionLabel(action: GeometryAction): string {
  switch (action.type) {
    case "show":
      return `Show ${action.objectIds.join(", ")}`;
    case "hide":
      return `Hide ${action.objectIds.join(", ")}`;
    case "highlight":
      return `Highlight ${action.objectIds.join(", ")}`;
    case "clear_highlight":
      return "Clear highlight";
    case "focus":
      return `Focus ${action.objectIds.join(", ")}`;
    case "animate":
      return `Animate ${action.objectId}`;
    case "ask_select":
      return "Ask selection question";
  }
}

function actionResult(action: GeometryAction): string {
  switch (action.type) {
    case "show":
      return "Show applied.";
    case "hide":
      return "Hide applied.";
    case "highlight":
      return "Highlight applied.";
    case "clear_highlight":
      return "Highlight cleared.";
    case "focus":
      return "Focus applied.";
    case "animate":
      return "Animation applied.";
    case "ask_select":
      return "Selection question ready.";
  }
}

function selectionMessage(state: GeometryInteractionState): string | null {
  if (!state.selectedObjectId) {
    return null;
  }
  switch (state.selection?.result) {
    case "correct":
      return `${state.selectedObjectId} is the expected selection.`;
    case "incorrect":
      return `${state.selectedObjectId} is not the expected selection.`;
    case "ungraded":
      return `Selected ${state.selectedObjectId}. This question is not graded.`;
    default:
      return `Selected ${state.selectedObjectId}.`;
  }
}

function useValidatedScene(scene: unknown): ValidatedGeometryScene | null {
  return useMemo(() => {
    try {
      return validateAndOrderGeometryScene(scene);
    } catch {
      return null;
    }
  }, [scene]);
}

function ValidatedGeometrySceneExperience({
  validatedScene,
  actions = [],
  showConstraintSnapshot = false,
}: Omit<GeometrySceneProps, "scene"> & {
  readonly validatedScene: ValidatedGeometryScene;
}) {
  const [interaction, setInteraction] = useState<GeometryInteractionState>(() =>
    createGeometryInteractionState(validatedScene),
  );
  const [rendererStatus, setRendererStatus] = useState<"loading" | "ready" | "failed">("loading");
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [snapshot, setSnapshot] = useState<GeometryConstraintSnapshot | null>(null);

  const actionValidation = useMemo(() => {
    const valid: GeometryAction[] = [];
    let rejected = false;
    for (const value of actions) {
      const action = validateGeometryAction(validatedScene, value);
      if (action) {
        valid.push(action);
      } else {
        rejected = true;
      }
    }
    return { actions: valid, rejected };
  }, [actions, validatedScene]);

  const handleSelect = useCallback(
    (objectId: string, source: SelectionSource) => {
      setInteraction(
        (current) => selectGeometryObject(validatedScene, current, objectId, source).state,
      );
    },
    [validatedScene],
  );

  const handleAction = useCallback(
    (action: GeometryAction) => {
      setInteraction((current) => {
        const transition = applyGeometryAction(validatedScene, current, action);
        if (transition.accepted) {
          setActionMessage(actionResult(action));
        }
        return transition.state;
      });
    },
    [validatedScene],
  );

  const handleReady = useCallback(() => setRendererStatus("ready"), []);
  const handleFailure = useCallback(() => setRendererStatus("failed"), []);
  const handleSnapshot = useCallback(
    (nextSnapshot: GeometryConstraintSnapshot) => setSnapshot(nextSnapshot),
    [],
  );

  if (rendererStatus === "failed") {
    return (
      <section className="geometry-experience geometry-fallback" aria-label="Geometry unavailable">
        <p role="alert">Geometry unavailable.</p>
        <p>{validatedScene.scene.accessibilityDescription}</p>
        <StaticFallback
          data={{
            assetId: validatedScene.scene.fallbackImageAssetId,
            description: validatedScene.scene.accessibilityDescription,
          }}
        />
      </section>
    );
  }

  const allowedSelection = interaction.selection
    ? new Set(interaction.selection.allowedObjectIds)
    : null;
  const selectableObjects = validatedScene.scene.objects.filter((item) => item.selectable === true);
  const selectedMessage = selectionMessage(interaction);

  return (
    <section className="geometry-experience" aria-label="Interactive geometry">
      <p className="geometry-description">{validatedScene.scene.accessibilityDescription}</p>
      {rendererStatus === "loading" ? <p role="status">Loading geometry…</p> : null}
      {rendererStatus === "ready" ? <p className="sr-only">Interactive geometry ready.</p> : null}

      <div className="geometry-layout">
        <GeometryBoard
          interaction={interaction}
          onFailure={handleFailure}
          onReady={handleReady}
          onSelect={handleSelect}
          onSnapshot={handleSnapshot}
          scene={validatedScene}
        />

        <aside className="geometry-controls" aria-label="Geometry controls">
          {actionValidation.rejected ? (
            <p className="error-text" role="alert">
              A geometry action was rejected.
            </p>
          ) : null}
          {actionValidation.actions.length > 0 ? (
            <div className="geometry-action-list">
              {actionValidation.actions.map((action, index) => (
                <button
                  key={`${action.type}-${index}`}
                  onClick={() => handleAction(action)}
                  type="button"
                >
                  {actionLabel(action)}
                </button>
              ))}
            </div>
          ) : null}
          {actionMessage ? (
            <p aria-label="Geometry action result" role="status">
              {actionMessage}
            </p>
          ) : null}

          {interaction.selection ? (
            <div className="geometry-selection-question">
              <TypedContentBlocks blocks={[...interaction.selection.prompt]} />
            </div>
          ) : null}
          <div className="geometry-selection-list" aria-label="Selectable geometry objects">
            {selectableObjects.map((item) => (
              <button
                disabled={allowedSelection !== null && !allowedSelection.has(item.id)}
                key={item.id}
                onClick={() => handleSelect(item.id, "keyboard")}
                type="button"
              >
                Select {item.label ?? item.id}
              </button>
            ))}
          </div>
          {selectedMessage ? (
            <p aria-label="Selection result" role="status">
              {selectedMessage}
            </p>
          ) : null}
        </aside>
      </div>

      {showConstraintSnapshot && snapshot ? (
        <output className="geometry-constraint-snapshot" data-testid="geometry-constraint-snapshot">
          {JSON.stringify(snapshot)}
        </output>
      ) : null}

      <details className="geometry-fallback-details">
        <summary>Static fallback</summary>
        <StaticFallback
          data={{
            assetId: validatedScene.scene.fallbackImageAssetId,
            description: validatedScene.scene.accessibilityDescription,
          }}
        />
      </details>
    </section>
  );
}

export function GeometryScene({
  scene,
  actions = [],
  showConstraintSnapshot = false,
}: GeometrySceneProps) {
  const validatedScene = useValidatedScene(scene);
  const fallback = useMemo(() => safeFallbackData(scene), [scene]);

  if (!validatedScene) {
    return (
      <section className="geometry-experience geometry-fallback" aria-label="Geometry unavailable">
        <p role="status">Geometry unavailable.</p>
        {fallback ? <StaticFallback data={fallback} /> : null}
      </section>
    );
  }

  return (
    <ValidatedGeometrySceneExperience
      actions={actions}
      key={`${validatedScene.scene.id}-${validatedScene.scene.version}`}
      showConstraintSnapshot={showConstraintSnapshot}
      validatedScene={validatedScene}
    />
  );
}
