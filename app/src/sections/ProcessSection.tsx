import { useRef } from "react";
import { useRevealOnScroll } from "../hooks/useRevealOnScroll";

const steps = [
  {
    number: "01",
    title: "Ingest and structure the company context",
    body: "Use llm-kb and the project data flow to sync source material, compile reusable knowledge, and keep onboarding artifacts visible and searchable.",
  },
  {
    number: "02",
    title: "Select the right specialist agents",
    body: "Route the work through llm-kb’s agent recommendation layer so frontend, AI, backend, security, DevOps, QA, and support roles appear where they add real value.",
  },
  {
    number: "03",
    title: "Validate, harden, and deploy professionally",
    body: "Use the evaluation harness, evidence-based QA, and deployment automation to move from proof of concept toward enterprise-ready delivery.",
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
          A delivery workflow that can grow past demo status.
        </h2>
        <p className="section-copy reveal">
          OnboardAI works as a complete execution model: local knowledge
          operations, relevant llm-kb agent selection, configurable AI
          behavior, and measurable quality before deployment.
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
