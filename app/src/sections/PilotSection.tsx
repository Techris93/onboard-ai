import { useRef } from "react";
import { useRevealOnScroll } from "../hooks/useRevealOnScroll";

const validationMetrics = [
  { label: "Test workspace", value: "Private" },
  { label: "Source policy", value: "Official-only" },
  { label: "Before client data", value: "Required" },
  { label: "Website exposure", value: "None" },
];

const validationChecklist = [
  "Choose one public company or platform and collect only official public sources in a temporary workspace.",
  "Generate a Q&A set and run the evaluation harness before touching private customer documentation.",
  "Tune prompts and retrieval privately, then carry only the lessons and generic product improvements back into the website.",
];

const validationOutputs = [
  "A private benchmark for source coverage, retrieval behavior, and model accuracy.",
  "A safe rehearsal for llm-kb agent selection, synthesis, and onboarding operations.",
  "A cleaner launch path because the public test stays off the customer-facing dashboard.",
];

export default function PilotSection() {
  const sectionRef = useRef<HTMLElement | null>(null);

  useRevealOnScroll(sectionRef);

  return (
    <section id="pilot" ref={sectionRef} className="section section-dark">
      <div className="section-inner pilot-layout">
        <div className="pilot-copy">
          <div className="section-label reveal">Validation</div>
          <h2 className="section-heading reveal">
            Run public-source validation before importing real client data.
          </h2>
          <p className="section-copy reveal">
            Public-company tests are useful for proving the onboarding workflow,
            but they belong in a temporary workspace, not on the public
            dashboard. Use one external platform to validate source selection,
            Q&amp;A generation, evaluation, and prompt tuning, then keep the
            live site generic and client-ready.
          </p>

          <div className="pilot-metric-grid">
            {validationMetrics.map((metric) => (
              <article key={metric.label} className="metric-card reveal">
                <div className="metric-value">{metric.value}</div>
                <h3 className="card-heading">{metric.label}</h3>
              </article>
            ))}
          </div>

          <div className="pilot-note-list reveal">
            {validationChecklist.map((note) => (
              <div key={note} className="summary-list-item">
                {note}
              </div>
            ))}
          </div>
        </div>

        <div className="glass-card pilot-panel reveal">
          <div className="summary-kicker">Validation protocol</div>
          <div className="pilot-verdict-row">
            <div className="summary-score">01</div>
            <div>
              <div className="summary-label">Keep the benchmark private</div>
              <p className="card-copy pilot-date">
                Use public-company tests to validate the onboarding system, not
                to populate the production dashboard.
              </p>
            </div>
          </div>

          <div className="summary-block">
            <p className="footer-title">Private validation checklist</p>
            <div className="summary-list">
              {validationChecklist.map((item) => (
                <div key={item} className="summary-list-item">
                  {item}
                </div>
              ))}
            </div>
          </div>

          <div className="summary-block">
            <p className="footer-title">Why this matters</p>
            <div className="summary-list">
              {validationOutputs.map((item) => (
                <div key={item} className="summary-list-item">
                  {item}
                </div>
              ))}
            </div>
          </div>

          <div className="summary-block">
            <p className="footer-title">Production rule</p>
            <div className="summary-list">
              <div className="summary-list-item">
                Only generic onboarding capabilities, delivery guidance, and
                customer-approved materials should appear on the live website.
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
