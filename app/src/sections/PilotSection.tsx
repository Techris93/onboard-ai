import { useRef } from "react";
import { useRevealOnScroll } from "../hooks/useRevealOnScroll";
import {
  buildOnboardingResult,
  publicPilot,
  supabasePilotProfile,
} from "../lib/onboarding";

export default function PilotSection() {
  const sectionRef = useRef<HTMLElement | null>(null);
  const pilotResult = buildOnboardingResult(supabasePilotProfile);

  useRevealOnScroll(sectionRef);

  return (
    <section id="pilot" ref={sectionRef} className="section section-dark">
      <div className="section-inner pilot-layout">
        <div className="pilot-copy">
          <div className="section-label reveal">Public-data pilot</div>
          <h2 className="section-heading reveal">
            Supabase is the best first public onboarding target.
          </h2>
          <p className="section-copy reveal">{publicPilot.summary}</p>

          <div className="pilot-metric-grid">
            {publicPilot.metrics.map((metric) => (
              <article key={metric.label} className="metric-card reveal">
                <div className="metric-value">{metric.value}</div>
                <h3 className="card-heading">{metric.label}</h3>
              </article>
            ))}
          </div>

          <div className="pilot-note-list reveal">
            {publicPilot.notes.map((note) => (
              <div key={note} className="summary-list-item">
                {note}
              </div>
            ))}
          </div>
        </div>

        <div className="glass-card pilot-panel reveal">
          <div className="summary-kicker">Pilot verdict</div>
          <div className="pilot-verdict-row">
            <div className="summary-score">{pilotResult.score}</div>
            <div>
              <div className="summary-label">{publicPilot.verdict}</div>
              <p className="card-copy pilot-date">
                First staging run completed on {publicPilot.dateLabel}.
              </p>
            </div>
          </div>

          <div className="summary-block">
            <p className="footer-title">Agent fit for the pilot</p>
            <div className="agent-pill-group">
              {pilotResult.agents.map((agent) => (
                <span key={agent} className="agent-pill">
                  {agent}
                </span>
              ))}
            </div>
          </div>

          <div className="summary-block">
            <p className="footer-title">Official source set</p>
            <div className="pilot-link-list">
              {publicPilot.links.map((link) => (
                <a
                  key={link.label}
                  className="pilot-link"
                  href={link.href}
                  target="_blank"
                  rel="noreferrer"
                >
                  {link.label}
                </a>
              ))}
            </div>
          </div>

          <div className="summary-block">
            <p className="footer-title">What this pilot proves</p>
            <div className="summary-list">
              {pilotResult.deliverables.map((item) => (
                <div key={item} className="summary-list-item">
                  {item}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
