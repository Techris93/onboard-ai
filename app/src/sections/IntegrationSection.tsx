import { useRef } from "react";
import { useRevealOnScroll } from "../hooks/useRevealOnScroll";

const integrationCards = [
  {
    title: "1. Intake on the website",
    body:
      "The frontend collects company context, desired source surfaces, rollout stage, governance needs, and target delivery systems.",
  },
  {
    title: "2. Delivery worker receives the packet",
    body:
      "When a backend worker is attached, the intake is sent to the delivery API so specialist routing, artifact packaging, and dataset planning can run securely.",
  },
  {
    title: "3. Results return to the operator view",
    body:
      "The interface can display stored onboarding packets, artifact previews, launch notes, and agent recommendations without exposing operator-only implementation detail to buyers.",
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
      "Best for production: the website posts the intake to a live API, a worker runs knowledge operations and evaluation tasks, and the stored results come back into the interface.",
  },
  {
    title: "Local bridge mode",
    body:
      "Useful for private or local-first delivery: the same API contract points at a local worker, which lets an operator run the private delivery workspace nearby and still feed the site real artifacts.",
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
          How the onboarding flow runs in production.
        </h2>
        <p className="section-copy reveal">
          The public site presents the intake and returned artifacts, while
          live knowledge operations, dataset planning, and evaluation work run
          behind an API worker or a private local bridge.
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
