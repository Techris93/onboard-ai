import { useRef } from "react";
import { useRevealOnScroll } from "../hooks/useRevealOnScroll";

const capabilities = [
  {
    title: "Customized AI integration for small to mid-sized companies",
    body: "OnboardAI is a tailored delivery model for companies that need AI to fit their operating reality, not the other way around.",
    points: [
      "Domain-specific assistants built from internal documents, product knowledge, and operating procedures",
      "Implementation scope shaped around each company’s workflows, team maturity, and escalation model",
      "Delivery paths that start lean for SMB teams and scale toward enterprise governance and automation",
    ],
  },
  {
    title: "Local-first knowledge operations with llm-kb",
    body: "llm-kb serves as a core capability, turning project memory, reusable outputs, and agent selection into a practical delivery layer.",
    points: [
      "Sync, compile, search, ask, synthesize, curate, and publish knowledge artifacts locally",
      "Reusable markdown outputs for briefs, executive notes, reports, and decision support",
      "Project memory that supports onboarding, architecture work, incidents, and continuous improvement",
    ],
  },
  {
    title: "Living onboarding paths from biological systems",
    body: "OnboardAI copies nature's adaptive operating systems so each onboarding journey senses confusion, remembers what worked, and routes the next person better.",
    points: [
      "Immune-style confusion detection, early intervention, and progressive access barriers",
      "Ant-trail confidence memory that strengthens successful paths and decays stale ones",
      "Echolocation micro-questions and adaptive coaching tone for role, confidence, and motivation",
    ],
  },
  {
    title: "Professional delivery with specialist agents",
    body: "Relevant llm-kb agent workflows can recommend and activate specialist roles for frontend polish, AI engineering, backend architecture, security hardening, DevOps automation, QA, compliance, and support.",
    points: [
      "Agent recommendation and activation for the right skill at the right stage",
      "Evidence-based QA and hardening before anything is called production-ready",
      "Stronger handoffs from design and integration through launch and support continuity",
    ],
  },
];

export default function CapabilitiesSection() {
  const sectionRef = useRef<HTMLElement | null>(null);

  useRevealOnScroll(sectionRef);

  return (
    <section id="capabilities" ref={sectionRef} className="section section-dark">
      <div className="section-inner">
        <div className="section-label reveal">Capabilities</div>
        <h2 className="section-heading reveal">
          A service-ready AI platform, not just a prompt experiment.
        </h2>
        <p className="section-copy reveal">
          Structured knowledge operations, specialist-agent delivery, and a
          path from SMB deployment to enterprise-grade governance define the
          platform.
        </p>

        <div className="capability-grid">
          {capabilities.map((capability) => (
            <article key={capability.title} className="glass-card reveal">
              <h3 className="card-heading capability-heading">
                {capability.title}
              </h3>
              <p className="card-copy">{capability.body}</p>
              <ul className="capability-points">
                {capability.points.map((point) => (
                  <li key={point}>{point}</li>
                ))}
              </ul>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
