import { useRef } from "react";
import { useRevealOnScroll } from "../hooks/useRevealOnScroll";
import { repoLinks } from "../lib/site";

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

const knobs = [
  "llm-kb agents for best-fit specialist selection",
  "llm-kb agent-start for activation-ready execution prompts",
  "llm-kb mistake-check and mistake-autolearn for guardrails",
  "llm-kb synthesize and publish for reusable outputs",
  "config.py and evaluate.py for answer quality and retrieval tuning",
];

const runbook = [
  "llm-kb sync",
  "llm-kb compile",
  "llm-kb agents \"customized AI integration build\"",
  "llm-kb agent-start \"enterprise delivery hardening\" --copy",
  "python evaluate.py --verbose",
  "llm-kb publish outputs/brief.md --target outputs --into publish",
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

          <div className="command-panel reveal">
            <div className="command-panel-header">
              <span>Operational runbook</span>
              <code>llm-kb + evaluate.py</code>
            </div>

            <div className="command-list">
              {runbook.map((step, index) => (
                <div key={step} className="command-line">
                  <span>{String(index + 1).padStart(2, "0")}</span>
                  <code>{step}</code>
                </div>
              ))}
            </div>

            <div className="knob-list">
              <h3 className="knob-heading">Agent-editable knobs</h3>
              <ul>
                {knobs.map((knob) => (
                  <li key={knob}>{knob}</li>
                ))}
              </ul>
            </div>

            <div className="button-row button-row-left">
              <a
                className="button button-primary"
                href={repoLinks.readme}
                target="_blank"
                rel="noreferrer"
              >
                Read implementation docs
              </a>
              <a
                className="button button-secondary"
                href={repoLinks.config}
                target="_blank"
                rel="noreferrer"
              >
                Inspect tuning surface
              </a>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
