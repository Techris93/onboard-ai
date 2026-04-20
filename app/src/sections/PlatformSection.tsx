import { useRef } from "react";
import { useRevealOnScroll } from "../hooks/useRevealOnScroll";

const features = [
  {
    title: "A visible agent surface",
    description: "program.md tells the optimizer what it may change and config.py keeps every prompt and retrieval tweak in plain sight.",
  },
  {
    title: "Document-first ingestion",
    description: "prepare.py can bootstrap a sample business or turn text and markdown files into a knowledge base you can inspect and version.",
  },
  {
    title: "Retrieval you can tune",
    description: "MAX_CONTEXT_TOPICS, RELEVANCE_THRESHOLD, USE_FULL_KNOWLEDGE, and retrieve_context() give you explicit control over what the model sees.",
  },
  {
    title: "A score instead of a vibe",
    description: "evaluate.py measures accuracy, quality, and coverage so changes compete on evidence instead of intuition.",
  },
];

const repoArtifacts = [
  { label: "Agent instructions", file: "program.md" },
  { label: "Optimization surface", file: "config.py" },
  { label: "Business knowledge", file: "data/knowledge.json" },
  { label: "Test questions", file: "data/test_qa.json" },
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
          { cx: 200, cy: 56, label: "PREPARE" },
          { cx: 324, cy: 272, label: "CONFIG" },
          { cx: 76, cy: 272, label: "EVALUATE" },
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
            Everything important stays visible and diffable.
          </h2>
          <p className="section-copy reveal">
            This is not a black-box assistant builder. The repo makes it easy to
            inspect what data went in, what the agent changed, and why an
            iteration scored better than the last one.
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
            {repoArtifacts.map((artifact) => (
              <div key={artifact.file} className="artifact-card">
                <span>{artifact.label}</span>
                <code>{artifact.file}</code>
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
