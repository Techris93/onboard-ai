import { useRef } from "react";
import { useRevealOnScroll } from "../hooks/useRevealOnScroll";

const features = [
  {
    title: "llm-kb agent recommendation and activation",
    description: "Use llm-kb agents, agent-show, agent-use, and agent-start to move from a request to a role-specific execution path quickly and consistently.",
  },
  {
    title: "Local-first knowledge compilation",
    description: "Sync, compile, search, ask, and synthesize project memory into reusable markdown outputs instead of losing context across chats and repos.",
  },
  {
    title: "Operational memory and mistake guardrails",
    description: "llm-kb can track recurring mistakes, surface guardrails, and keep the team from relearning the same expensive lessons on each rollout.",
  },
  {
    title: "Publish-safe outputs and executive artifacts",
    description: "Generate briefs, reports, and sanitized outputs that are useful for internal delivery, stakeholder updates, and controlled sharing.",
  },
];

const deliveryPillars = [
  {
    label: "Knowledge memory",
    detail: "Structured project memory that can support onboarding, implementation, and ongoing operations.",
  },
  {
    label: "Agent orchestration",
    detail: "Relevant specialist roles can be surfaced at the right time instead of overloading one generic assistant.",
  },
  {
    label: "Executive outputs",
    detail: "Briefs, reports, and reusable summaries help stakeholders stay aligned without reading raw implementation detail.",
  },
  {
    label: "Operational guardrails",
    detail: "Mistake tracking and workflow discipline reduce regression risk as the system evolves.",
  },
];

function OrbitVisualization() {
  return (
    <div className="orbit-shell" aria-hidden="true">
      <svg viewBox="0 0 400 400">
        <circle
          cx="200"
          cy="200"
          r="144"
          fill="none"
          stroke="rgba(216, 163, 109, 0.14)"
          strokeWidth="1"
        />

        <g className="orbit-rotate">
          <circle
            cx="200"
            cy="200"
            r="144"
            fill="none"
            stroke="rgba(216, 163, 109, 0.32)"
            strokeWidth="1"
            strokeDasharray="10 6"
            className="dash-shift"
          />
        </g>

        {[
          { cx: 200, cy: 56, label: "SYNC" },
          { cx: 324, cy: 272, label: "ROUTE" },
          { cx: 76, cy: 272, label: "DEPLOY" },
        ].map((node) => (
          <g key={node.label}>
            <circle
              cx={node.cx}
              cy={node.cy}
              r="28"
              fill="rgba(216, 163, 109, 0.12)"
              stroke="rgba(216, 163, 109, 0.4)"
              strokeWidth="1"
            />
            <text
              x={node.cx}
              y={node.cy + 4}
              textAnchor="middle"
              className="orbit-label"
            >
              {node.label}
            </text>
          </g>
        ))}

        <g>
          <circle
            cx="200"
            cy="200"
            r="48"
            fill="none"
            stroke="rgba(111, 198, 255, 0.16)"
            strokeWidth="1"
          />
          <circle
            cx="200"
            cy="200"
            r="40"
            fill="rgba(111, 198, 255, 0.08)"
            className="node-pulse"
          />
          <text x="200" y="204" textAnchor="middle" className="orbit-center">
            ONBOARD
          </text>
        </g>
      </svg>
    </div>
  );
}

export default function PlatformSection() {
  const sectionRef = useRef<HTMLElement | null>(null);

  useRevealOnScroll(sectionRef, ".reveal", 0.1, "top 78%");

  return (
    <section id="engine" ref={sectionRef} className="section section-surface">
      <div className="section-inner platform-layout">
        <div className="platform-copy">
          <div className="section-label reveal">Engine</div>
          <h2 className="section-heading reveal">
            llm-kb turns scattered work into a usable delivery engine.
          </h2>
          <p className="section-copy reveal">
            This is no longer framed as a black-box assistant builder. The
            website now shows how OnboardAI can combine knowledge compilation,
            specialist-agent routing, output synthesis, and publish-safe
            operational workflows in one platform narrative.
          </p>

          <div className="feature-list">
            {features.map((feature) => (
              <article key={feature.title} className="feature-item reveal">
                <div className="feature-icon" aria-hidden="true">
                  <span />
                </div>
                <div>
                  <h3 className="feature-title">{feature.title}</h3>
                  <p className="feature-copy">{feature.description}</p>
                </div>
              </article>
            ))}
          </div>

          <div className="artifact-grid reveal">
            {deliveryPillars.map((artifact) => (
              <div key={artifact.label} className="artifact-card">
                <span>{artifact.label}</span>
                <p className="artifact-detail">{artifact.detail}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="platform-visual reveal">
          <div className="platform-visual-sticky">
            <OrbitVisualization />
          </div>
        </div>
      </div>
    </section>
  );
}
