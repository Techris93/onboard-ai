const linkGroups = [
  {
    title: "Platform",
    links: [
      { label: "Capabilities", href: "#capabilities" },
      { label: "Workflow", href: "#workflow" },
      { label: "Engine", href: "#engine" },
      { label: "Agent System", href: "#agents" },
      { label: "Readiness", href: "#scoring" },
    ],
  },
  {
    title: "Solutions",
    links: [
      { label: "Customer Support AI", href: "#use-cases" },
      { label: "Internal Knowledge AI", href: "#use-cases" },
      { label: "Domain-Specific Assistants", href: "#use-cases" },
      { label: "Enterprise Rollout Paths", href: "#use-cases" },
    ],
  },
  {
    title: "Approach",
    links: [
      { label: "Customized Integration", href: "#top" },
      { label: "Specialist Agents", href: "#agents" },
      { label: "Knowledge Operations", href: "#engine" },
      { label: "Operational Readiness", href: "#scoring" },
    ],
  },
];

export default function Footer() {
  return (
    <footer className="site-footer">
      <div className="section-inner footer-grid">
        <div className="footer-brand">
          <div className="brand-mark">OnboardAI</div>
          <p className="footer-copy">
            Customized AI integration for small to mid-sized companies, with a
            stronger path toward enterprise-grade delivery, governance, and
            operational support.
          </p>
        </div>

        {linkGroups.map((group) => (
          <div key={group.title}>
            <p className="footer-title">{group.title}</p>
            <div className="footer-link-list">
              {group.links.map((link) => (
                <a
                  key={link.label}
                  className="footer-link"
                  href={link.href}
                  target={link.href.startsWith("http") ? "_blank" : undefined}
                  rel={link.href.startsWith("http") ? "noreferrer" : undefined}
                >
                  {link.label}
                </a>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div className="footer-bar">
        <span>{new Date().getFullYear()} OnboardAI</span>
        <span>Built around llm-kb, agent orchestration, and measurable AI delivery</span>
      </div>
    </footer>
  );
}
