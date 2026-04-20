import { useRef } from "react";
import { useRevealOnScroll } from "../hooks/useRevealOnScroll";

const useCases = [
  {
    industry: "Customer support modernization",
    knowledge: "Help-center docs, refund policies, onboarding material, escalation rules",
    questions: "What can the assistant answer, when should it escalate, and how should it sound?",
    outcome: "A practical fit for small and mid-sized companies replacing fragmented support content with a governed AI layer.",
  },
  {
    industry: "Internal knowledge copilots",
    knowledge: "SOPs, playbooks, compliance notes, delivery checklists, team conventions",
    questions: "How do we do this, what policy applies here, and what should happen next?",
    outcome: "Useful when growing teams need faster onboarding and more consistent decisions without losing control.",
  },
  {
    industry: "Domain-specific AI integration",
    knowledge: "Product specs, architecture notes, pricing logic, integration guidance, implementation constraints",
    questions: "Can the assistant support sales, delivery, ops, and customer-facing use cases with the right boundaries?",
    outcome: "Strong for organizations that need custom AI behavior tied to how the business actually runs.",
  },
  {
    industry: "Enterprise-ready rollout paths",
    knowledge: "Security requirements, deployment standards, review criteria, support processes",
    questions: "What does it take to move from prototype to a governed, supportable production system?",
    outcome: "Gives companies a story that can satisfy both operators and more demanding enterprise buyers.",
  },
];

export default function UseCasesSection() {
  const sectionRef = useRef<HTMLElement | null>(null);

  useRevealOnScroll(sectionRef);

  return (
    <section id="use-cases" ref={sectionRef} className="section">
      <div className="section-inner">
        <div className="section-label reveal">Use cases</div>
        <h2 className="section-heading reveal">
          Built for AI integrations that need to survive real operations.
        </h2>
        <p className="section-copy reveal">
          The website now speaks to service buyers and delivery teams alike:
          customer support, internal copilots, domain-specific assistants, and
          professional rollout programs.
        </p>

        <div className="usecase-grid">
          {useCases.map((useCase) => (
            <article key={useCase.industry} className="glass-card reveal">
              <p className="usecase-tag">{useCase.industry}</p>
              <div className="usecase-stack">
                <div>
                  <h3 className="usecase-label">Knowledge</h3>
                  <p className="card-copy">{useCase.knowledge}</p>
                </div>
                <div>
                  <h3 className="usecase-label">Questions</h3>
                  <p className="card-copy">{useCase.questions}</p>
                </div>
                <div>
                  <h3 className="usecase-label">Why it fits</h3>
                  <p className="card-copy">{useCase.outcome}</p>
                </div>
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
