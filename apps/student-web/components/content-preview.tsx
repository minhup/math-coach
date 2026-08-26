import type { ContentBlock, ContentPreview as ContentPreviewData } from "../lib/api";

function TypedBlock({ block }: { block: ContentBlock }) {
  switch (block.type) {
    case "text":
      return <p>{block.text}</p>;
    case "inline_math":
      return (
        <span className="preview-inline-math" aria-label="Inline mathematics">
          {block.latex}
        </span>
      );
    case "display_math":
      return (
        <div className="preview-display-math" aria-label="Displayed mathematics">
          {block.latex}
        </div>
      );
    case "rich_line":
      return (
        <p>
          {block.spans.map((span, index) =>
            span.type === "text" ? (
              <span key={`${block.id}-${index}`}>{span.text}</span>
            ) : (
              <span
                aria-label="Inline mathematics"
                className="preview-inline-math"
                key={`${block.id}-${index}`}
              >
                {span.latex}
              </span>
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
          <TypedBlocks blocks={block.content} />
        </aside>
      );
  }
}

function TypedBlocks({ blocks }: { blocks: ContentBlock[] }) {
  return (
    <div className="preview-blocks">
      {blocks.map((block) => (
        <TypedBlock block={block} key={block.id} />
      ))}
    </div>
  );
}

export function ContentPreview({ preview }: { preview: ContentPreviewData }) {
  return (
    <article className="content-preview">
      <header className="preview-title">
        <div>
          <p className="eyebrow">Immutable problem version {preview.version}</p>
          <h1>{preview.externalCode}</h1>
        </div>
        <dl className="preview-facts">
          <div>
            <dt>Difficulty</dt>
            <dd>{preview.difficultyBand}</dd>
          </div>
          <div>
            <dt>Time</dt>
            <dd>{preview.estimatedMinutes} min</dd>
          </div>
          <div>
            <dt>Score</dt>
            <dd>{preview.maximumScore}</dd>
          </div>
        </dl>
      </header>

      <section className="preview-section" aria-labelledby="supported-exams-heading">
        <h2 id="supported-exams-heading">Supported examinations</h2>
        <ul className="preview-card-list">
          {preview.supportedExams.map((exam) => (
            <li key={exam.examCycleId}>
              <strong>{exam.cycleCode}</strong>
              <span>{exam.examName}</span>
              <small>
                {exam.relevanceLevel} relevance · {exam.relevanceNote}
              </small>
            </li>
          ))}
        </ul>
      </section>

      <section className="preview-section" aria-labelledby="statement-heading">
        <h2 id="statement-heading">Statement</h2>
        <TypedBlocks blocks={preview.statement} />
      </section>

      <section className="preview-section" aria-labelledby="skills-heading">
        <h2 id="skills-heading">Skill coverage</h2>
        <ul className="preview-compact-list">
          {preview.skills.map((skill) => (
            <li key={skill.skillId}>
              <strong>{skill.skillCode}</strong> — {skill.skillName} ({skill.role},{" "}
              {skill.importance})
            </li>
          ))}
        </ul>
      </section>

      {preview.geometryScene ? (
        <section className="preview-section preview-scene" aria-labelledby="geometry-heading">
          <h2 id="geometry-heading">Curated geometry scene</h2>
          <p>{preview.geometryScene.accessibilityDescription}</p>
          <dl className="preview-facts">
            <div>
              <dt>Version</dt>
              <dd>{preview.geometryScene.version}</dd>
            </div>
            <div>
              <dt>Objects</dt>
              <dd>{preview.geometryScene.objects.length}</dd>
            </div>
            <div>
              <dt>Fallback asset</dt>
              <dd>{preview.geometryScene.fallbackImageAssetId}</dd>
            </div>
          </dl>
        </section>
      ) : null}

      <section className="preview-section" aria-labelledby="solutions-heading">
        <h2 id="solutions-heading">Reference solutions</h2>
        <p className="preview-policy-note">Reference solutions are non-exhaustive.</p>
        {preview.referenceSolutions.map((solution) => (
          <div className="preview-subsection" key={solution.id}>
            <h3>{solution.methodLabel}</h3>
            <TypedBlocks blocks={solution.content} />
          </div>
        ))}
      </section>

      <section className="preview-section" aria-labelledby="rubric-heading">
        <h2 id="rubric-heading">Rubric</h2>
        <ol className="preview-numbered-list">
          {preview.rubric.map((item) => (
            <li key={item.id}>
              <div>
                <TypedBlocks blocks={item.description} />
              </div>
              <strong>{item.maximumScore} points</strong>
            </li>
          ))}
        </ol>
      </section>

      <section className="preview-section" aria-labelledby="hints-heading">
        <h2 id="hints-heading">Progressive hints</h2>
        {preview.hints.map((hint) => (
          <details className="preview-hint" key={hint.id}>
            <summary>
              Level {hint.hintLevel}
              {hint.revealsCompleteSolution ? " · complete solution reveal" : ""}
            </summary>
            <TypedBlocks blocks={hint.content} />
            {hint.geometryActions.length > 0 ? (
              <p className="muted">{hint.geometryActions.length} validated geometry action(s)</p>
            ) : null}
          </details>
        ))}
      </section>

      <footer className="preview-provenance">
        <h2>Source and provenance</h2>
        <p>{preview.provenance.attributionText}</p>
        <p className="muted">
          {preview.provenance.sourceKind} · {preview.provenance.rightsBasis} ·{" "}
          {preview.provenance.publicationStatus}
        </p>
      </footer>
    </article>
  );
}
