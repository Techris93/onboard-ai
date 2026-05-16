import Footer from "../sections/Footer";
import Navigation from "../components/Navigation";

export const publicPages = {
  product: {
    title: "Product",
    eyebrow: "Platform",
    body:
      "OnboardAI gives teams a governed path from company knowledge to AI onboarding, dataset readiness, quality gates, and operator-reviewed artifacts.",
    points: [
      "Public intake and private workspace separation.",
      "Persistent projects, jobs, artifacts, dataset batches, and quality results.",
      "Provider-ready adapters with local/offline execution available for safe validation.",
    ],
  },
  pricing: {
    title: "Pricing",
    eyebrow: "Plans",
    body:
      "Pricing is structured around how deeply a company needs to operationalize AI onboarding and dataset preparation.",
    points: [
      "Starter: onboarding runs, planning, and artifact exports.",
      "Growth: dataset generation, quality gates, and evaluation loops.",
      "Enterprise: private deployment, custom providers, compliance, human review, and fine-tuning readiness.",
    ],
  },
  security: {
    title: "Security",
    eyebrow: "Trust",
    body:
      "OnboardAI is designed around tenant isolation, role-based access, audit logs, server-side provider secrets, and publish-safe artifacts.",
    points: [
      "Provider keys are never placed in frontend code.",
      "Authenticated SaaS routes enforce membership and role checks.",
      "Audit events track sensitive actions such as job creation, provider-key updates, and reviews.",
    ],
  },
  docs: {
    title: "Documentation",
    eyebrow: "Resources",
    body:
      "Documentation covers local development, production deployment, worker operation, provider configuration, billing setup, and security controls.",
    points: [
      "Run the backend API and worker locally for development.",
      "Use Render for the API and GitHub Pages for the frontend.",
      "Use local/offline providers before enabling paid model providers.",
    ],
  },
  api: {
    title: "API Reference",
    eyebrow: "Developers",
    body:
      "The API supports auth, workspace dashboards, project creation, job queues, artifact retrieval, dataset exports, provider settings, and health checks.",
    points: [
      "Use bearer tokens for SaaS routes.",
      "Use job endpoints for long-running onboarding and dataset generation.",
      "Use artifact and export endpoints to move approved outputs into downstream systems.",
    ],
  },
  blog: {
    title: "Blog",
    eyebrow: "Thinking",
    body:
      "Editorial content should explain why high-quality company data, source authority, and quality gates matter before fine-tuning.",
    points: [
      "How small expert models change company AI strategy.",
      "Why rejected rows are as important as accepted rows.",
      "How to evaluate AI onboarding before importing private customer data.",
    ],
  },
  changelog: {
    title: "Changelog",
    eyebrow: "Release Notes",
    body:
      "The current release adds the production SaaS foundation: auth, tenancy, SQLite persistence, jobs, dashboard, dataset generation, quality gates, and mock billing/provider hooks.",
    points: [
      "Public site remains available on GitHub Pages.",
      "Backend worker supports durable job execution.",
      "Dashboard lives under /app with a GitHub Pages fallback route.",
    ],
  },
  about: {
    title: "About",
    eyebrow: "Company",
    body:
      "OnboardAI is built for companies that want personalized AI systems grounded in real company knowledge, not generic chatbot behavior.",
    points: [
      "AI onboarding for small and mid-sized companies.",
      "Dataset preparation for expert language models.",
      "Production readiness for teams that need governance and evidence.",
    ],
  },
  careers: {
    title: "Careers",
    eyebrow: "Team",
    body:
      "OnboardAI needs people who care about product quality, data quality, security, AI evaluation, and practical customer delivery.",
    points: [
      "AI engineering and evaluation.",
      "Security-conscious product engineering.",
      "Technical writing and customer enablement.",
    ],
  },
  contact: {
    title: "Contact",
    eyebrow: "Support",
    body:
      "Use the onboarding flow to scope a company rollout, or prepare a private validation run before sharing sensitive client data.",
    points: [
      "Start with public-source validation.",
      "Define target use cases and source authority.",
      "Move to private documents only after the workflow is proven.",
    ],
  },
  legal: {
    title: "Legal",
    eyebrow: "Policies",
    body:
      "Legal coverage for OnboardAI should include terms, privacy, data processing, subprocessors, retention, and customer deletion workflows.",
    points: [
      "Customer data should remain tenant-scoped.",
      "Provider use should be disclosed before live model execution.",
      "Exports should only include customer-approved materials.",
    ],
  },
  privacy: {
    title: "Privacy",
    eyebrow: "Policy",
    body:
      "OnboardAI is structured so provider secrets stay server-side and public validation data remains separate from private customer workspaces.",
    points: [
      "Use local/offline mode for dry runs.",
      "Use audit logs for sensitive operations.",
      "Use deletion and retention workflows for customer-controlled data.",
    ],
  },
  terms: {
    title: "Terms",
    eyebrow: "Agreement",
    body:
      "Production terms should define acceptable use, provider responsibilities, customer data ownership, service limits, and human review requirements.",
    points: [
      "Fine-tuning should require explicit customer approval.",
      "Generated datasets should be reviewed before provider upload.",
      "Operators should verify outputs before production use.",
    ],
  },
  dpa: {
    title: "DPA",
    eyebrow: "Data Processing",
    body:
      "The DPA should describe roles, subprocessors, retention, deletion, security controls, breach notification, and transfer mechanisms.",
    points: [
      "Keep provider keys encrypted or hashed server-side.",
      "Maintain audit history for sensitive data operations.",
      "Document subprocessors before enterprise rollout.",
    ],
  },
  subprocessors: {
    title: "Subprocessors",
    eyebrow: "Compliance",
    body:
      "Subprocessor disclosures should identify hosting, model providers, billing, monitoring, and storage vendors used by each deployment.",
    points: [
      "Render can host the backend.",
      "GitHub Pages can host the public frontend.",
      "Model providers are optional and should be enabled per workspace.",
    ],
  },
};

export type PublicPageKey = keyof typeof publicPages;

export default function PublicInfoPage({ pageKey }: { pageKey: PublicPageKey }) {
  const page = publicPages[pageKey];

  return (
    <>
      <Navigation />
      <main className="page-shell">
        <section className="section hero-section public-info-hero">
          <div className="section-inner">
            <div className="section-label">{page.eyebrow}</div>
            <h1 className="hero-heading">
              <span>{page.title}</span>
            </h1>
            <p className="hero-copy">{page.body}</p>
            <div className="public-info-grid">
              {page.points.map((point) => (
                <article key={point} className="glass-card">
                  <p className="card-copy">{point}</p>
                </article>
              ))}
            </div>
            <div className="button-row">
              <a className="button button-primary" href="./app">
                Open Dashboard
              </a>
              <a className="button button-secondary" href="./">
                Back Home
              </a>
            </div>
          </div>
        </section>
        <Footer />
      </main>
    </>
  );
}
