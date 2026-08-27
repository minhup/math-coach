import type { ContentBlock } from "../../lib/api";
import { MathRenderer } from "./math-renderer";

function TypedContentBlock({ block }: { block: ContentBlock }) {
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
      return (
        <p className="preview-geometry-reference">
          Curated geometry scene version: <code>{block.sceneVersionId}</code>
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
          <TypedContentBlocks blocks={block.content} />
        </aside>
      );
  }
}

export function TypedContentBlocks({ blocks }: { blocks: ContentBlock[] }) {
  return (
    <div className="preview-blocks">
      {blocks.map((block) => (
        <TypedContentBlock block={block} key={block.id} />
      ))}
    </div>
  );
}
