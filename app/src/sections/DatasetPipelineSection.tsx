import { useRef } from "react";
import { useRevealOnScroll } from "../hooks/useRevealOnScroll";

const pipelineStages = [
  {
    title: "Codex Orchestrator",
    body:
      "Owns the goal, use-case spec, schema, label boundaries, hard evaluation patterns, quality gates, rejects, reports, and worklog.",
  },
  {
    title: "Generator Model",
    body:
      "Uses a provider-neutral generator layer. DeepSeek v4 Pro can be one low-cost option, but the generator follows OnboardAI specs instead of inventing policy.",
  },
  {
    title: "Batch Archive",
    body:
      "Preserves accepted rows, rejected rows, quality notes, gold reasoning, generator specs, and batch reports without exposing private company data.",
  },
  {
    title: "Quality Gates",
    body:
      "Filters weak rows through schema, label, leakage, duplicate, placeholder, scope, split, privacy, and gold-reason checks before training data is trusted.",
  },
  {
    title: "Improvement Loop",
    body:
      "Uses every rejected pattern and accepted exemplar to improve the next generator spec, tighten gates, and lower the cost of future batches.",
  },
];

const qualityGates = [
  "Schema validity",
  "Role correctness",
  "Allowed labels",
  "Canonical order",
  "Duplicate prompt detection",
  "Placeholder and meta-text removal",
  "Target-scope signal",
  "Helper-scope policy",
  "Unsupported-primary policy",
  "Split intent",
  "Leakage risk",
  "Synthetic pattern detection",
  "Gold reason quality",
  "Train/test leakage",
  "Company-data privacy",
  "Evaluation coverage",
];

const outcomes = [
  {
    label: "Expert model readiness",
    value: "5B-15B",
    body:
      "Prepare smaller expert language models around a company domain instead of relying on one oversized general model.",
  },
  {
    label: "Dataset quality loop",
    value: "Gated",
    body:
      "Each batch earns its way into the dataset through measurable checks, rejected-row reports, and spec refinement.",
  },
  {
    label: "Commercial use case",
    value: "$50k+",
    body:
      "Position fine-tuning and data preparation as a serious company service with privacy, evaluation, and delivery discipline.",
  },
];

export default function DatasetPipelineSection() {
  const sectionRef = useRef<HTMLElement | null>(null);

  useRevealOnScroll(sectionRef);

  return (
    <section
      id="dataset-pipeline"
      ref={sectionRef}
      className="section section-surface"
    >
      <div className="section-inner">
        <div className="section-label reveal">Fine-tuning pipeline</div>
        <h2 className="section-heading reveal">
          Build high-quality datasets for company-specific expert models.
        </h2>
        <p className="section-copy reveal">
          OnboardAI turns fine-tuning into an operating system: Codex designs
          the workflow, a generator model produces rows from strict specs, and
          quality gates reject weak data before it can damage model behavior.
        </p>

        <div className="dataset-pipeline-layout">
          <div className="dataset-stage-list">
            {pipelineStages.map((stage, index) => (
              <article key={stage.title} className="dataset-stage reveal">
                <div className="dataset-stage-index">
                  {String(index + 1).padStart(2, "0")}
                </div>
                <div>
                  <h3 className="card-heading">{stage.title}</h3>
                  <p className="card-copy">{stage.body}</p>
                </div>
              </article>
            ))}
          </div>

          <aside className="glass-card dataset-gates-panel reveal">
            <div className="summary-kicker">Quality gate set</div>
            <div className="quality-gate-grid">
              {qualityGates.map((gate) => (
                <span key={gate} className="quality-gate-pill">
                  {gate}
                </span>
              ))}
            </div>
          </aside>
        </div>

        <div className="dataset-outcome-grid">
          {outcomes.map((outcome) => (
            <article key={outcome.label} className="metric-card reveal">
              <div className="metric-value">{outcome.value}</div>
              <h3 className="card-heading">{outcome.label}</h3>
              <p className="card-copy">{outcome.body}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
