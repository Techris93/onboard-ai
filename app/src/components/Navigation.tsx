import { useEffect, useState } from "react";

const navItems = [
  { label: "Start Onboarding", href: "#onboarding" },
  { label: "Product", href: "#product" },
  { label: "Resources", href: "#resources" },
  { label: "Company", href: "#company" },
  { label: "Pilot", href: "#pilot" },
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
            href="#integration"
          >
            Integration Model
          </a>
          <a
            className="button button-primary nav-primary"
            href="#onboarding"
          >
            Start Onboarding
          </a>
        </div>
      </div>
    </header>
  );
}
