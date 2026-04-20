import { repoLinks } from "../lib/site";

const linkGroups = [
  {
    title: "Workflow",
    links: [
      { label: "Hero", href: "#top" },
      { label: "Process", href: "#workflow" },
      { label: "Engine", href: "#engine" },
      { label: "Scoring", href: "#scoring" },
    ],
  },
  {
    title: "Repository",
    links: [
      { label: "README", href: repoLinks.readme },
      { label: "program.md", href: repoLinks.program },
      { label: "config.py", href: repoLinks.config },
      { label: "evaluate.py", href: repoLinks.evaluate },
    ],
  },
  {
    title: "Data",
    links: [
      { label: "prepare.py", href: repoLinks.prepare },
      { label: ".env.example", href: repoLinks.env },
      { label: "knowledge.json", href: repoLinks.knowledge },
      { label: "test_qa.json", href: repoLinks.tests },
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
            A visible workflow for turning business knowledge into a measured,
            domain-specific assistant.
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
        <span>Built around prepare.py, config.py, and evaluate.py</span>
      </div>
    </footer>
  );
}
