import { useRef } from "react";
import { useRevealOnScroll } from "../hooks/useRevealOnScroll";

const steps = [
  {
    number: "01",
    title: "Prepare the knowledge base",
    body: "Import .txt or .md files with prepare.py, or edit data/knowledge.json and data/test_qa.json directly when you want tight control over the domain.",
    command: "python prepare.py --import-docs ./docs",
  },
  {
    number: "02",
    title: "Tune the assistant config",
    body: "Let the agent refine the system prompt, few-shot examples, response rules, model settings, and retrieval thresholds inside one diffable file: config.py.",
    command: "config.py",
  },
  {
    number: "03",
    title: "Evaluate and keep winners",
    body: "Run the scoring harness, inspect weak categories, and keep improvements that raise answer accuracy, response quality, and question coverage.",
    command: "python evaluate.py --commit",
  },
];

export default function ProcessSection() {
  const sectionRef = useRef<HTMLElement | null>(null);

  useRevealOnScroll(sectionRef);

  return (
    <section id="workflow" ref={sectionRef} className="section section-dark">
      <div className="section-inner">
        <div className="section-label reveal">Workflow</div>
        <h2 className="section-heading reveal">
          Three files, one loop, no hidden magic.
        </h2>
        <p className="section-copy reveal">
          The repository keeps the optimization surface visible: data lives in
          JSON, agent instructions live in
          {" "}
          <code>program.md</code>
          , and the actual prompt-and-retrieval controls live in
          {" "}
          <code>config.py</code>
          .
        </p>

        <div className="process-grid">
          {steps.map((step) => (
            <article key={step.number} className="glass-card reveal">
              <div className="process-number">{step.number}</div>
              <h3 className="card-heading">{step.title}</h3>
              <p className="card-copy">{step.body}</p>
              <div className="command-chip">
                <span className="command-chip-label">Focus</span>
                <code>{step.command}</code>
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
