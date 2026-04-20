import { useRef } from "react";
import { useRevealOnScroll } from "../hooks/useRevealOnScroll";

const agentRows = [
  {
    phase: "Scope and orchestration",
    agents: ["Agents Orchestrator", "Project Shepherd"],
    outcome:
      "Coordinates the workstream, aligns stakeholders, and turns requests into an execution path with quality gates.",
  },
  {
    phase: "Solution architecture",
    agents: ["AI Engineer", "Backend Architect"],
    outcome:
      "Designs the retrieval, model, data, and integration layers behind each customer-specific assistant.",
  },
  {
    phase: "Security and governance",
    agents: ["Security Engineer", "Legal Compliance Checker"],
    outcome:
      "Adds threat modeling, access controls, policy awareness, and compliance posture to the delivery model.",
  },
  {
    phase: "Build, harden, and deploy",
    agents: ["Frontend Developer", "DevOps Automator", "Evidence Collector"],
    outcome:
      "Delivers a production-ready interface, deployment pipeline, and evidence-based validation loop.",
  },
  {
    phase: "Adoption and support",
    agents: ["Support Responder", "Technical Writer"],
    outcome:
      "Improves onboarding, internal enablement, support readiness, and documentation quality after launch.",
  },
];

export default function AgentSystemSection() {
  const sectionRef = useRef<HTMLElement | null>(null);

  useRevealOnScroll(sectionRef);

  return (
    <section id="agents" ref={sectionRef} className="section section-surface">
      <div className="section-inner">
        <div className="section-label reveal">Agent system</div>
        <h2 className="section-heading reveal">
          llm-kb can route the work to the right specialist agents.
        </h2>
        <p className="section-copy reveal">
          Instead of treating agent support as a vague future idea, the site now
          frames a concrete delivery stack based on the relevant llm-kb
          recommendation flow and specialist roles already available in the
          imported agent library.
        </p>

        <div className="agent-table reveal">
          <div className="agent-table-head">
            <span>Phase</span>
            <span>Relevant agents</span>
            <span>Business outcome</span>
          </div>

          {agentRows.map((row) => (
            <article key={row.phase} className="agent-row">
              <div className="agent-phase">
                <h3>{row.phase}</h3>
              </div>
              <div className="agent-pill-group">
                {row.agents.map((agent) => (
                  <span key={agent} className="agent-pill">
                    {agent}
                  </span>
                ))}
              </div>
              <p className="agent-outcome">{row.outcome}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
