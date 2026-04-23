import { useRef } from "react";
import { useRevealOnScroll } from "../hooks/useRevealOnScroll";

const integrationCards = [
  {
    title: "1. Intake on the website",
    body:
      "The frontend collects company context, desired source surfaces, rollout stage, governance needs, and target delivery systems.",
  },
  {
    title: "2. /api/onboarding receives the packet",
    body:
      "When a backend worker is attached, the site posts the intake to /api/onboarding, where llm-kb can run, artifacts are stored, and a run record is returned to the UI.",
  },
  {
    title: "3. Results return to the operator view",
    body:
      "The site can display stored onboarding packets, artifact previews, launch notes, and agent recommendations without exposing raw CLI details to buyers.",
  },
];

const operatingModes = [
  {
    title: "Static pilot mode",
    body:
      "Useful on GitHub Pages today: capture the intake, keep the readiness preview, and validate the workflow even before a live worker is attached.",
  },
  {
    title: "Backend worker mode",
    body:
      "Best for production: the website posts the intake to a live API, a worker runs llm-kb and the evaluation stack, and the stored results come back into the interface.",
  },
  {
    title: "Local bridge mode",
    body:
      "Useful for private or local-first delivery: the same API contract points at a local worker, which lets an operator run llm-kb nearby and still feed the site real artifacts.",
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
