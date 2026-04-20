import { useRef } from "react";
import { useRevealOnScroll } from "../hooks/useRevealOnScroll";

const heroProof = [
  "Customized AI integration for small to mid-sized companies.",
  "Relevant llm-kb agents for delivery, hardening, and support.",
  "Enterprise-grade posture for security, deployment, and governance.",
];

export default function HeroSection() {
  const sectionRef = useRef<HTMLElement | null>(null);

  useRevealOnScroll(sectionRef, ".reveal", 0.1, "top 95%", 24);

  return (
    <section id="top" ref={sectionRef} className="section hero-section">
      <div className="section-inner hero-stack">
        <div className="section-label reveal">
          Customized AI integration for small to mid-sized companies
        </div>

        <h1 className="hero-heading reveal">
          Build a
          {" "}
          <span>professional AI delivery system.</span>
        </h1>

        <p className="hero-copy reveal">
          OnboardAI now presents a stronger, service-ready offering: use
          company knowledge, llm-kb knowledge operations, and relevant
          specialist agents to design, secure, deploy, and support AI systems
          that feel credible for real businesses and professional buyers.
        </p>

        <div className="button-row reveal">
          <a className="button button-primary" href="#capabilities">
            See Capabilities
          </a>
          <a className="button button-secondary" href="#agents">
            View Agent System
          </a>
        </div>

        <div className="hero-proof-grid reveal" aria-label="Core positioning">
          {heroProof.map((item) => (
            <div key={item} className="proof-pill">
              {item}
            </div>
          ))}
        </div>

        <div className="scroll-indicator" aria-hidden="true" />
      </div>
    </section>
  );
}
