import { useEffect, useState } from "react";
import { repoLinks } from "../lib/site";

const navItems = [
  { label: "Capabilities", href: "#capabilities" },
  { label: "Workflow", href: "#workflow" },
  { label: "Agents", href: "#agents" },
  { label: "Use Cases", href: "#use-cases" },
  { label: "Readiness", href: "#scoring" },
];

export default function Navigation() {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => {
      setScrolled(window.scrollY > 32);
    };

    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });

    return () => {
      window.removeEventListener("scroll", onScroll);
    };
  }, []);

  return (
    <header className={`site-nav${scrolled ? " is-scrolled" : ""}`}>
      <div className="nav-inner">
        <a className="brand-mark" href="#top">
          OnboardAI
        </a>

        <nav className="nav-links" aria-label="Primary">
          {navItems.map((item) => (
            <a key={item.href} className="nav-link" href={item.href}>
              {item.label}
            </a>
          ))}
        </nav>

        <div className="nav-actions">
          <a
            className="button button-secondary nav-secondary"
            href={repoLinks.readme}
            target="_blank"
            rel="noreferrer"
          >
            README
          </a>
          <a
            className="button button-primary nav-primary"
            href="#capabilities"
          >
            Explore Platform
          </a>
        </div>
      </div>
    </header>
  );
}
