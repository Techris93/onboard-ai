import { useRef } from "react";
import { useRevealOnScroll } from "../hooks/useRevealOnScroll";
import { repoLinks } from "../lib/site";

const heroCommands = [
  "python prepare.py --import-docs ./docs",
  "edit config.py",
  "python evaluate.py --verbose",
];

export default function HeroSection() {
  const sectionRef = useRef<HTMLElement | null>(null);

  useRevealOnScroll(sectionRef, ".reveal", 0.1, "top 95%", 24);

  return (
    <section id="top" ref={sectionRef} className="section hero-section">
      <div className="section-inner hero-stack">
        <div className="section-label reveal">Open-source prompt tuning workflow</div>

        <h1 className="hero-heading reveal">
          Turn business docs into a
          {" "}
          <span>measurable AI assistant.</span>
        </h1>

        <p className="hero-copy reveal">
          OnboardAI gives you a clean loop for ingesting company knowledge,
          tuning prompts and retrieval in
          {" "}
          <code>config.py</code>
          {" "}
          and scoring every iteration against real question-answer pairs
          before you trust the output.
        </p>

        <div className="button-row reveal">
          <a className="button button-primary" href="#workflow">
            See the Workflow
          </a>
          <a
            className="button button-secondary"
            href={repoLinks.repo}
            target="_blank"
            rel="noreferrer"
          >
            Open the Repo
          </a>
        </div>

        <div className="hero-command-grid reveal" aria-label="Core commands">
          {heroCommands.map((command) => (
            <div key={command} className="command-pill">
              <span className="command-pill-label">Run</span>
              <code>{command}</code>
            </div>
          ))}
        </div>

        <div className="scroll-indicator" aria-hidden="true" />
      </div>
    </section>
  );
}
