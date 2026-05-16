import { catalogGroups } from "../lib/onboarding";

const pageLinks = [
  { label: "Dashboard", href: "./app" },
  { label: "Pricing", href: "./pricing" },
  { label: "Security", href: "./security" },
  { label: "Docs", href: "./docs" },
  { label: "API", href: "./api" },
  { label: "Changelog", href: "./changelog" },
  { label: "Privacy", href: "./privacy" },
  { label: "Terms", href: "./terms" },
  { label: "DPA", href: "./dpa" },
  { label: "Subprocessors", href: "./subprocessors" },
];

export default function Footer() {
  return (
    <footer className="site-footer">
      <div className="section-inner footer-grid">
        <div className="footer-brand">
          <div className="brand-mark">OnboardAI</div>
          <p className="footer-copy">
            OnboardAI turns intake answers, public and private source material,
            fine-tuning dataset requirements, and specialist delivery roles
            into a professional onboarding packet for real AI rollouts.
          </p>
        </div>

        {catalogGroups.map((group) => (
          <div key={group.title}>
            <p className="footer-title">{group.title}</p>
            <div className="footer-link-list">
              {group.items.map((item) => (
                <a
                  key={item.id}
                  className="footer-link"
                  href={`#${item.id}`}
                >
                  {item.label}
                </a>
              ))}
            </div>
          </div>
        ))}
        <div>
          <p className="footer-title">SaaS</p>
          <div className="footer-link-list">
            {pageLinks.map((item) => (
              <a key={item.href} className="footer-link" href={item.href}>
                {item.label}
              </a>
            ))}
          </div>
        </div>
      </div>

      <div className="footer-bar">
        <span>{new Date().getFullYear()} OnboardAI</span>
        <span>AI onboarding, expert-model dataset preparation, and production readiness</span>
      </div>
    </footer>
  );
}
