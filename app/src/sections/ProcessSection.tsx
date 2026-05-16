import { useRef } from "react";
import { useRevealOnScroll } from "../hooks/useRevealOnScroll";

const steps = [
  {
    number: "01",
    title: "Ingest and structure the company context",
    body: "Use a private knowledge workspace to prepare source material, structure reusable knowledge, and keep onboarding artifacts visible and searchable.",
  },
  {
    number: "02",
    title: "Select the right specialist agents",
    body: "Route the work through specialist-agent recommendations so frontend, AI, backend, security, DevOps, QA, and support roles appear where they add real value.",
  },
  {
    number: "03",
    title: "Generate and gate fine-tuning data",
    body: "Let Codex own dataset specs and quality gates while generator models produce batches that must pass privacy, label, leakage, and gold-reason checks.",
  },
  {
    number: "04",
    title: "Validate, harden, and deploy professionally",
    body: "Use evaluation, evidence-based QA, and deployment automation to move from prototype to enterprise-ready delivery.",
  },
  {
    number: "05",
    title: "Let each onboarding path improve the next one",
    body: "Use path outcome memory to mark successful routes, detect stuck users, age out stale signals, and recommend the next best step by role and confidence.",
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
          A delivery workflow built for public-facing AI services.
        </h2>
        <p className="section-copy reveal">
          OnboardAI works as a complete execution model: local knowledge
          operations, relevant specialist selection, fine-tuning dataset
          preparation, configurable AI behavior, path outcome memory, and
          measurable quality before deployment.
        </p>

        <div className="process-grid">
          {steps.map((step) => (
            <article key={step.number} className="glass-card reveal">
              <div className="process-number">{step.number}</div>
              <h3 className="card-heading">{step.title}</h3>
              <p className="card-copy">{step.body}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
