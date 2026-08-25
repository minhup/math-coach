const steps = [
  { label: "Add your paper solution", note: "Select and verify a photo", state: "Active" },
  {
    label: "Confirm the transcript",
    note: "Visual correction arrives in Milestone 3",
    state: "Next",
  },
  { label: "Review the reasoning", note: "Step feedback arrives in Milestone 5", state: "Later" },
  { label: "Hint or retry", note: "Choose the next useful action", state: "Later" },
];

export function WorkflowPanel() {
  return (
    <aside className="workflow-panel" aria-labelledby="workflow-title">
      <p className="eyebrow">Practice workflow</p>
      <h1 id="workflow-title">From paper to useful feedback.</h1>
      <p className="workflow-intro">
        The coach keeps each transition explicit, so you stay in control of what gets evaluated.
      </p>
      <ol className="workflow-list">
        {steps.map((step, index) => (
          <li className={`workflow-step ${index === 0 ? "active" : ""}`} key={step.label}>
            <span className="step-number">{index + 1}</span>
            <span className="step-copy">
              <strong>{step.label}</strong>
              <span>{step.note}</span>
            </span>
            <span className="step-state">{step.state}</span>
          </li>
        ))}
      </ol>
      <div className="multi-target-note">
        <strong>One learning path, multiple goals</strong>
        Future combined plans will balance shared skills and target-specific practice without making
        one examination implicitly primary.
      </div>
    </aside>
  );
}
