import { useRef } from "react";
import { useRevealOnScroll } from "../hooks/useRevealOnScroll";

const scores = [
  {
    value: "KB",
    label: "Knowledge ops",
    body: "llm-kb supports sync, compile, search, ask, synthesize, curate, publish, and status workflows for reusable project memory.",
  },
  {
    value: "AG",
    label: "Agent routing",
    body: "llm-kb can recommend relevant agents and generate task-ready activation prompts for role-specific execution.",
  },
  {
    value: "OP",
    label: "Operationalization",
    body: "Mistake tracking, publish-safe outputs, weekly briefs, and deployment automation support a more professional operating model.",
  },
];

const readinessPillars = [
  {
    title: "Security-conscious delivery",
    body: "Security review, access control thinking, and governance language are part of the product story from the start.",
  },
  {
    title: "Evidence-based quality",
    body: "The platform emphasizes measurable evaluation, visible validation, and disciplined hardening before launch.",
  },
  {
    title: "Deployment and support continuity",
    body: "Operational automation, documentation, and support readiness help the rollout survive beyond the initial build.",
  },
];

export default function ScoreSection() {
  const sectionRef = useRef<HTMLElement | null>(null);

  useRevealOnScroll(sectionRef);

  return (
    <section id="scoring" ref={sectionRef} className="section section-dark">
      <div className="section-inner">
        <div className="section-label reveal">Scoring</div>
        <h2 className="section-heading reveal">
          Operational readiness, not just model tuning.
        </h2>
        <p className="section-copy reveal">
          The page now presents llm-kb as part of the platform capability set:
          knowledge operations, agent routing, publish-safe outputs, and the
          existing evaluation harness for evidence-based improvement.
        </p>

        <div className="score-layout">
          <div className="score-grid">
            {scores.map((score) => (
              <article key={score.label} className="metric-card reveal">
                <div className="metric-value">{score.value}</div>
                <h3 className="card-heading">{score.label}</h3>
                <p className="card-copy">{score.body}</p>
              </article>
            ))}
          </div>

          <div className="readiness-panel reveal">
            <div className="readiness-panel-header">
              <span>Readiness pillars</span>
            </div>

            <div className="readiness-list">
              {readinessPillars.map((pillar) => (
                <article key={pillar.title} className="readiness-item">
                  <h3 className="readiness-title">{pillar.title}</h3>
                  <p className="card-copy">{pillar.body}</p>
                </article>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
