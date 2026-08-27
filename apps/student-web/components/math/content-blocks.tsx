import type { ContentBlock } from "../../lib/api";
import { GeometryScene } from "../geometry/geometry-scene";
import { MathRenderer } from "./math-renderer";

export interface ResolvedGeometryContent {
  readonly scene: unknown;
  readonly actions: readonly unknown[];
}

export type GeometryContentResolver = (sceneVersionId: string) => ResolvedGeometryContent | null;

function TypedContentBlock({
  block,
  resolveGeometry,
}: {
  block: ContentBlock;
  resolveGeometry?: GeometryContentResolver;
}) {
  switch (block.type) {
    case "text":
      return <p>{block.text}</p>;
    case "inline_math":
      return <MathRenderer label="Inline mathematics" latex={block.latex} mode="inline" />;
    case "display_math":
      return <MathRenderer label="Displayed mathematics" latex={block.latex} mode="display" />;
    case "rich_line":
      return (
        <p>
          {block.spans.map((span, index) =>
            span.type === "text" ? (
              <span key={`${block.id}-${index}`}>{span.text}</span>
            ) : (
              <MathRenderer
                key={`${block.id}-${index}`}
                label="Inline mathematics"
                latex={span.latex}
                mode="inline"
              />
            ),
          )}
        </p>
      );
    case "geometry":
      const resolvedGeometry = resolveGeometry?.(block.sceneVersionId);
      if (resolvedGeometry) {
        return <GeometryScene actions={resolvedGeometry.actions} scene={resolvedGeometry.scene} />;
      }
      return (
        <p className="geometry-unresolved" role="status">
          Geometry unavailable.
        </p>
      );
    case "image":
      return (
        <figure className="preview-asset-reference">
          <div aria-hidden="true">Image asset</div>
          <figcaption>{block.alt}</figcaption>
        </figure>
      );
    case "callout":
      return (
        <aside className={`preview-callout preview-callout-${block.kind}`}>
          <TypedContentBlocks blocks={block.content} resolveGeometry={resolveGeometry} />
        </aside>
      );
  }
}

export function TypedContentBlocks({
  blocks,
  resolveGeometry,
}: {
  blocks: ContentBlock[];
  resolveGeometry?: GeometryContentResolver;
}) {
  return (
    <div className="preview-blocks">
      {blocks.map((block) => (
        <TypedContentBlock block={block} key={block.id} resolveGeometry={resolveGeometry} />
      ))}
    </div>
  );
}
