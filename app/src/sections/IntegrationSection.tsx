import { useRef } from "react";
import { useRevealOnScroll } from "../hooks/useRevealOnScroll";

const integrationCards = [
  {
    title: "1. Intake on the website",
    body:
      "The frontend collects company context, desired source surfaces, rollout stage, governance needs, and target delivery systems.",
  },
  {
    title: "2. llm-kb runs behind the scenes",
    body:
      "A backend worker or local bridge turns that intake into project memory, source compilation, agent recommendations, briefs, and publish-safe outputs.",
  },
  {
    title: "3. Results return to the operator view",
    body:
      "The site can display the onboarding packet, launch checklist, review notes, and support guidance without exposing raw CLI details to buyers.",
  },
];

const operatingModes = [
  {
    title: "Static pilot mode",
    body:
      "Useful on GitHub Pages today: capture the onboarding intake, generate the brief, and validate the workflow before adding live execution.",
  },
  {
    title: "Backend worker mode",
    body:
      "Best for production: the website posts the intake to an API, a worker runs llm-kb and the evaluation stack, and results are stored for the team.",
  },
  {
    title: "Local bridge mode",
    body:
      "Useful for private or local-first delivery: an operator or desktop helper runs llm-kb locally, then publishes the resulting artifacts back to the website.",
  },
];

export default function IntegrationSection() {
  const sectionRef = useRef<HTMLElement | null>(null);

  useRevealOnScroll(sectionRef);

  return (
    <section
      id="integration"
      ref={sectionRef}
      className="section section-surface"
    >
      <div className="section-inner">
        <div className="section-label reveal">Integration model</div>
        <h2 className="section-heading reveal">
          How to make the onboarding flow actually work.
        </h2>
        <p className="section-copy reveal">
          GitHub Pages can present the intake and outputs, but live llm-kb
          execution belongs behind an API worker or a local bridge. That keeps
          the website professional while still letting the underlying agent and
          knowledge workflows do real work.
        </p>

        <div className="integration-grid">
          {integrationCards.map((card) => (
            <article key={card.title} className="glass-card reveal">
              <h3 className="card-heading">{card.title}</h3>
              <p className="card-copy">{card.body}</p>
            </article>
          ))}
        </div>

        <div className="integration-mode-panel reveal">
          <div className="readiness-panel-header">
            <span>Recommended operating modes</span>
          </div>
          <div className="readiness-list">
            {operatingModes.map((mode) => (
              <article key={mode.title} className="readiness-item">
                <h3 className="readiness-title">{mode.title}</h3>
                <p className="card-copy">{mode.body}</p>
              </article>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
