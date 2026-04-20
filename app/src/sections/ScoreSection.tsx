import { useRef } from "react";
import { useRevealOnScroll } from "../hooks/useRevealOnScroll";
import { repoLinks } from "../lib/site";

const scores = [
  {
    value: "50",
    label: "Accuracy",
    body: "Checks whether key facts from the expected answer actually appear in the model output.",
  },
  {
    value: "30",
    label: "Quality",
    body: "Rewards answers that are structured, appropriately sized, and not obviously broken.",
  },
  {
    value: "20",
    label: "Coverage",
    body: "Measures how often the assistant clears the pass threshold across the full question set.",
  },
];

const knobs = [
  "SYSTEM_PROMPT and business-specific tone",
  "FEW_SHOT_EXAMPLES for weak categories",
  "RESPONSE_RULES for edge-case behavior",
  "retrieve_context() and relevance thresholds",
  "TEMPERATURE and MAX_TOKENS for output control",
];

const runbook = [
  "cp .env.example .env",
  "Add GEMINI_API_KEY",
  "python prepare.py",
  "python evaluate.py --verbose",
  "python evaluate.py --commit",
];

export default function ScoreSection() {
  const sectionRef = useRef<HTMLElement | null>(null);

  useRevealOnScroll(sectionRef);

  return (
    <section id="scoring" ref={sectionRef} className="section section-dark">
      <div className="section-inner">
        <div className="section-label reveal">Scoring</div>
        <h2 className="section-heading reveal">
          Optimize with evidence, not vibes.
        </h2>
        <p className="section-copy reveal">
          The evaluation harness already separates accuracy, quality, and
          coverage, so the agent has a concrete target instead of a hand-wavy
          prompt brief.
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
              <span>Runbook</span>
              <code>evaluate.py</code>
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
                href={repoLinks.program}
                target="_blank"
                rel="noreferrer"
              >
                Read program.md
              </a>
              <a
                className="button button-secondary"
                href={repoLinks.config}
                target="_blank"
                rel="noreferrer"
              >
                Inspect config.py
              </a>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
