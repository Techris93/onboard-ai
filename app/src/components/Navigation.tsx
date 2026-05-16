import { useEffect, useState } from "react";
import { catalogGroups } from "../lib/onboarding";

const workflowLinks = [
  { label: "Start Onboarding", href: "#onboarding", note: "Intake and readiness" },
  { label: "Dataset Pipeline", href: "#dataset-pipeline", note: "Fine-tuning data generation" },
  { label: "Platform Engine", href: "#engine", note: "Prompt, retrieval, evaluation" },
  { label: "Capabilities", href: "#capabilities", note: "What the platform delivers" },
  { label: "Workflow", href: "#workflow", note: "How rollout happens" },
  { label: "Integration Model", href: "#integration", note: "Static, backend, local bridge" },
  { label: "Agent System", href: "#agents", note: "Specialist role routing" },
  { label: "Validation", href: "#pilot", note: "Private benchmark path" },
];

const navGroups = [
  {
    label: "Workflow",
    href: "#onboarding",
    links: workflowLinks,
  },
  ...catalogGroups.map((group) => ({
    label: group.title,
    href: `#${group.id}`,
    links: group.items.map((item) => ({
      label: item.label,
      href: `#${item.id}`,
      note: item.summary,
    })),
  })),
];

export default function Navigation() {
  const [scrolled, setScrolled] = useState(false);
  const [activeMenu, setActiveMenu] = useState<string | null>(null);
  const [mobileOpen, setMobileOpen] = useState(false);

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

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setActiveMenu(null);
        setMobileOpen(false);
      }
    };

    window.addEventListener("keydown", onKeyDown);
    return () => {
      window.removeEventListener("keydown", onKeyDown);
    };
  }, []);

  const closeMenus = () => {
    setActiveMenu(null);
    setMobileOpen(false);
  };

  return (
    <header
      className={`site-nav${scrolled ? " is-scrolled" : ""}${mobileOpen ? " has-open-menu" : ""}`}
    >
      <div className="nav-inner">
        <a className="brand-mark" href="#top" onClick={closeMenus}>
          OnboardAI
        </a>

        <nav className="nav-menu" aria-label="Primary">
          {navGroups.map((group) => (
            <div
              key={group.label}
              className="nav-group"
              onMouseEnter={() => setActiveMenu(group.label)}
              onMouseLeave={() => setActiveMenu(null)}
            >
              <button
                type="button"
                className="nav-group-trigger"
                aria-haspopup="true"
                aria-expanded={activeMenu === group.label}
                onClick={() =>
                  setActiveMenu((current) =>
                    current === group.label ? null : group.label,
                  )
                }
                onFocus={() => setActiveMenu(group.label)}
              >
                <span>{group.label}</span>
                <span className="nav-trigger-mark" aria-hidden="true" />
              </button>

              <div
                className={`nav-dropdown${activeMenu === group.label ? " is-open" : ""}`}
              >
                <a
                  className="nav-dropdown-heading"
                  href={group.href}
                  onClick={closeMenus}
                >
                  {group.label}
                </a>
                <div className="nav-dropdown-list">
                  {group.links.map((item) => (
                    <a
                      key={item.href}
                      className="nav-dropdown-link"
                      href={item.href}
                      onClick={closeMenus}
                    >
                      <span>{item.label}</span>
                      <small>{item.note}</small>
                    </a>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </nav>

        <div className="nav-actions">
          <a
            className="button button-secondary nav-secondary"
            href="#integration"
          >
            Integration Model
          </a>
          <a
            className="button button-primary nav-primary"
            href="#onboarding"
            onClick={closeMenus}
          >
            Start Onboarding
          </a>
          <button
            type="button"
            className={`menu-toggle${mobileOpen ? " is-open" : ""}`}
            aria-label={mobileOpen ? "Close navigation menu" : "Open navigation menu"}
            aria-expanded={mobileOpen}
            aria-controls="mobile-navigation"
            onClick={() => setMobileOpen((current) => !current)}
          >
            <span />
            <span />
            <span />
          </button>
        </div>
      </div>

      <nav
        id="mobile-navigation"
        className={`mobile-nav-panel${mobileOpen ? " is-open" : ""}`}
        aria-label="Mobile navigation"
        aria-hidden={!mobileOpen}
      >
        <div className="mobile-nav-inner">
          {navGroups.map((group) => (
            <section key={group.label} className="mobile-nav-group">
              <a
                className="mobile-nav-heading"
                href={group.href}
                onClick={closeMenus}
              >
                {group.label}
              </a>
              <div className="mobile-nav-link-list">
                {group.links.map((item) => (
                  <a
                    key={item.href}
                    className="mobile-nav-link"
                    href={item.href}
                    onClick={closeMenus}
                  >
                    <span>{item.label}</span>
                    <small>{item.note}</small>
                  </a>
                ))}
              </div>
            </section>
          ))}
        </div>
      </nav>
    </header>
  );
}
