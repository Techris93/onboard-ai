import { useRef } from "react";
import { useRevealOnScroll } from "../hooks/useRevealOnScroll";

const useCases = [
  {
    industry: "Coffee shops and retail",
    knowledge: "Menus, hours, loyalty perks, refunds, seasonal items",
    questions: "Pricing, store hours, complaints, delivery, gift cards",
    outcome: "Great for the sample dataset and for fast feedback loops on customer support answers.",
  },
  {
    industry: "SaaS documentation",
    knowledge: "Feature docs, pricing, exports, plan limits, integration notes",
    questions: "Plan fit, onboarding blockers, CSV export, API access",
    outcome: "Lets teams benchmark whether product answers are grounded in the latest docs.",
  },
  {
    industry: "Internal operations",
    knowledge: "SOPs, onboarding guides, HR policies, escalation paths",
    questions: "Benefits, laptop requests, approval chains, incident steps",
    outcome: "Useful when you want to test an internal assistant before exposing it to staff.",
  },
  {
    industry: "Professional services",
    knowledge: "Fees, intake rules, timelines, deliverables, client policies",
    questions: "What documents are needed, how long a process takes, what happens next",
    outcome: "Helps domain experts tune careful, bounded answers instead of generic chatbot copy.",
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
          Built for domain-specific question answering.
        </h2>
        <p className="section-copy reveal">
          OnboardAI works best when you have a bounded knowledge base and a set
          of questions that matter enough to test before shipping.
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
