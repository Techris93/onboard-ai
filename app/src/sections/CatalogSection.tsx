import { useRef } from "react";
import { useRevealOnScroll } from "../hooks/useRevealOnScroll";
import { catalogGroups } from "../lib/onboarding";

export default function CatalogSection() {
  const sectionRef = useRef<HTMLElement | null>(null);

  useRevealOnScroll(sectionRef);

  return (
    <section id="library" ref={sectionRef} className="section section-dark">
      <div className="section-inner">
        <div className="section-label reveal">Product and trust surfaces</div>
        <h2 className="section-heading reveal">
          Product, resources, and company pages become onboarding inputs.
        </h2>
        <p className="section-copy reveal">
          These are not filler nav links. They are the source surfaces that turn
          a generic assistant idea into a structured onboarding program with
          stronger retrieval, better escalation behavior, and more credible
          rollout decisions.
        </p>

        <div className="directory-stack">
          {catalogGroups.map((group) => (
            <div
              key={group.id}
              id={group.id}
              className="directory-group glass-card reveal"
            >
              <div className="directory-header">
                <div className="section-label">{group.title}</div>
                <p className="card-copy">{group.intro}</p>
              </div>

              <div className="directory-grid">
                {group.items.map((item) => (
                  <article
                    key={item.id}
                    id={item.id}
                    className="directory-card"
                  >
                    <h3 className="card-heading">{item.label}</h3>
                    <p className="card-copy">{item.summary}</p>
                    <div className="directory-output">{item.output}</div>
                  </article>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
