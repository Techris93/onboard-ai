export type CompanySize = "smb" | "mid-market" | "enterprise";
export type UseCase =
  | "customer-support"
  | "internal-copilot"
  | "product-api-assistant"
  | "sales-enablement"
  | "operations-assistant";
export type RolloutStage = "discovery" | "pilot" | "production";
export type IntegrationMode = "advisory" | "backend-worker" | "local-bridge";
export type DeliverySystem =
  | "website"
  | "help-center"
  | "developer-portal"
  | "api-gateway"
  | "crm"
  | "internal-wiki"
  | "support-desk"
  | "status-feed";

export type CatalogItem = {
  id: string;
  label: string;
  summary: string;
  output: string;
};

export type CatalogGroup = {
  id: "product" | "resources" | "company";
  title: string;
  intro: string;
  items: CatalogItem[];
};

export type OnboardingProfile = {
  companyName: string;
  industry: string;
  companySize: CompanySize;
  useCase: UseCase;
  stage: RolloutStage;
  integrationMode: IntegrationMode;
  sources: string[];
  compliance: string[];
  systems: DeliverySystem[];
};

export const catalogGroups: CatalogGroup[] = [
  {
    id: "product",
    title: "Product",
    intro:
      "These surfaces define what the platform does, how buyers understand value, and which operational risks show up during onboarding.",
    items: [
      {
        id: "product-platform",
        label: "Platform",
        summary:
          "Capture the core product architecture, product modules, service boundaries, and who the platform is built for.",
        output:
          "Platform narrative, feature map, and use-case framing for the onboarding brief.",
      },
      {
        id: "product-pricing",
        label: "Pricing",
        summary:
          "Collect plan structure, usage limits, enterprise gating, and any expansion paths that affect rollout design.",
        output:
          "Commercial summary for pilot scope, buyer expectations, and expansion assumptions.",
      },
      {
        id: "product-security",
        label: "Security",
        summary:
          "Pull public controls, compliance posture, access model, and hardening guidance into the delivery plan.",
        output:
          "Security and governance checklist mapped to the onboarding program.",
      },
      {
        id: "product-changelog",
        label: "Changelog",
        summary:
          "Track release velocity, deprecations, and product updates that can change prompts, integrations, or support guidance.",
        output:
          "Change-monitoring brief for launch, maintenance, and support operations.",
      },
    ],
  },
  {
    id: "resources",
    title: "Resources",
    intro:
      "These sources shape answer quality, implementation reliability, and the confidence level of a production rollout.",
    items: [
      {
        id: "resources-documentation",
        label: "Documentation",
        summary:
          "Use onboarding guides, setup flows, troubleshooting material, and product docs as the primary operating context.",
        output:
          "Structured knowledge pack for onboarding, implementation, and customer guidance.",
      },
      {
        id: "resources-api-reference",
        label: "API Reference",
        summary:
          "Collect endpoint coverage, auth model, object semantics, and constraints that affect assistant accuracy.",
        output:
          "API-aware implementation notes and retrieval-safe reference coverage.",
      },
      {
        id: "resources-community",
        label: "Community",
        summary:
          "Use community channels, open-source signals, and public examples to understand real operator behavior and edge cases.",
        output:
          "Edge-case and ecosystem notes for support, onboarding, and continuous improvement.",
      },
      {
        id: "resources-blog",
        label: "Blog",
        summary:
          "Capture product announcements, migration notes, case studies, and editorial context around how the platform evolves.",
        output:
          "Narrative support for rollout messaging, migration warnings, and customer education.",
      },
    ],
  },
  {
    id: "company",
    title: "Company",
    intro:
      "These pages add trust, buyer context, escalation routes, and legal guardrails that a serious onboarding flow should not ignore.",
    items: [
      {
        id: "company-about",
        label: "About",
        summary:
          "Understand the company's positioning, story, mission, and target audience so the assistant sounds aligned.",
        output:
          "Brand and positioning context for system prompts, handoff notes, and buyer-facing copy.",
      },
      {
        id: "company-careers",
        label: "Careers",
        summary:
          "Hiring pages reveal organizational maturity, operating focus, support motion, and what the company is scaling.",
        output:
          "Organization maturity notes for rollout complexity and support expectations.",
      },
      {
        id: "company-contact",
        label: "Contact",
        summary:
          "Capture support, sales, and escalation paths so the system knows when to route rather than hallucinate.",
        output:
          "Escalation map for support, sales, onboarding, and exception handling.",
      },
      {
        id: "company-legal",
        label: "Legal",
        summary:
          "Bring terms, privacy, support policy, and SLA material into the onboarding process when trust and governance matter.",
        output:
          "Legal and policy coverage for compliant answers and enterprise readiness.",
      },
    ],
  },
];

export const allCatalogItems = catalogGroups.flatMap((group) => group.items);

export const companySizes = [
  { value: "smb", label: "Small company" },
  { value: "mid-market", label: "Mid-sized company" },
  { value: "enterprise", label: "Enterprise program" },
] as const;

export const industries = [
  "Software / SaaS",
  "Developer platform",
  "Fintech",
  "Healthcare",
  "Ecommerce",
  "Professional services",
  "Education",
] as const;

export const useCaseOptions = [
  { value: "customer-support", label: "Customer support assistant" },
  { value: "internal-copilot", label: "Internal knowledge copilot" },
  { value: "product-api-assistant", label: "Product and API assistant" },
  { value: "sales-enablement", label: "Sales enablement assistant" },
  { value: "operations-assistant", label: "Operations and compliance assistant" },
] as const;

export const rolloutStages = [
  { value: "discovery", label: "Discovery" },
  { value: "pilot", label: "Pilot" },
  { value: "production", label: "Production" },
] as const;

export const integrationModes = [
  {
    value: "advisory",
    label: "Advisory planning",
    detail:
      "Use the site to scope sources, agents, and deliverables before live execution exists.",
  },
  {
    value: "backend-worker",
    label: "Backend worker",
    detail:
      "A web API hands the intake to a worker that runs llm-kb, compiles knowledge, and publishes outputs.",
  },
  {
    value: "local-bridge",
    label: "Local bridge",
    detail:
      "An operator or desktop helper runs llm-kb locally and returns results to the web surface.",
  },
] as const;

export const complianceOptions = [
  "SOC 2",
  "HIPAA",
  "GDPR",
  "SSO / identity controls",
] as const;

export const deliverySystems = [
  { value: "website", label: "Website" },
  { value: "help-center", label: "Help center" },
  { value: "developer-portal", label: "Developer portal" },
  { value: "api-gateway", label: "API gateway" },
  { value: "crm", label: "CRM / sales ops" },
  { value: "internal-wiki", label: "Internal wiki" },
  { value: "support-desk", label: "Support desk" },
  { value: "status-feed", label: "Status / changelog feed" },
] as const;

export const defaultOnboardingProfile: OnboardingProfile = {
  companyName: "Northwind Support",
  industry: "Software / SaaS",
  companySize: "mid-market",
  useCase: "customer-support",
  stage: "discovery",
  integrationMode: "backend-worker",
  sources: [
    "product-platform",
    "product-security",
    "resources-documentation",
    "resources-api-reference",
    "company-contact",
  ],
  compliance: [],
  systems: ["website", "help-center", "support-desk"],
};

type ScoreBreakdown = {
  knowledge: number;
  governance: number;
  operations: number;
  activation: number;
};

export type OnboardingResult = {
  score: number;
  label: string;
  summary: string;
  selectedSources: CatalogItem[];
  metrics: ScoreBreakdown;
  deliverables: string[];
  agents: string[];
  integrationSteps: string[];
};

function unique<T>(values: T[]) {
  return [...new Set(values)];
}

function scoreProfile(profile: OnboardingProfile): ScoreBreakdown {
  const sourceCoverage = Math.min(
    28,
    Math.round((profile.sources.length / allCatalogItems.length) * 28),
  );

  const governance =
    Math.min(14, profile.compliance.length * 4) +
    (profile.sources.includes("product-security") ? 4 : 0) +
    (profile.sources.includes("company-legal") ? 3 : 0) +
    (profile.sources.includes("company-contact") ? 2 : 0);

  const operations =
    (profile.stage === "discovery" ? 10 : profile.stage === "pilot" ? 15 : 20) +
    Math.min(6, profile.systems.length * 1.5);

  const activation =
    (profile.integrationMode === "advisory"
      ? 11
      : profile.integrationMode === "backend-worker"
        ? 19
        : 16) +
    (profile.sources.includes("resources-api-reference") ? 3 : 0) +
    (profile.sources.includes("product-changelog") ? 2 : 0) +
    (profile.sources.includes("resources-documentation") ? 1 : 0);

  return {
    knowledge: sourceCoverage,
    governance: Math.min(25, governance),
    operations: Math.min(25, operations),
    activation: Math.min(25, activation),
  };
}

function labelForScore(score: number) {
  if (score >= 85) {
    return "Enterprise-ready trajectory";
  }
  if (score >= 70) {
    return "Launchable onboarding scope";
  }
  if (score >= 55) {
    return "Structured pilot scope";
  }
  return "Foundation intake";
}

function buildAgentList(profile: OnboardingProfile) {
  const agents = ["Software Architect", "Technical Writer"];

  if (
    profile.useCase === "customer-support" ||
    profile.useCase === "sales-enablement"
  ) {
    agents.push("Frontend Developer", "AI Engineer");
  }

  if (
    profile.useCase === "internal-copilot" ||
    profile.useCase === "product-api-assistant" ||
    profile.useCase === "operations-assistant"
  ) {
    agents.push("AI Engineer", "Backend Architect");
  }

  if (profile.compliance.length > 0 || profile.stage === "production") {
    agents.push("Security Engineer", "Code Reviewer");
  }

  if (
    profile.integrationMode !== "advisory" ||
    profile.systems.includes("api-gateway") ||
    profile.systems.includes("status-feed")
  ) {
    agents.push("DevOps Automator");
  }

  return unique(agents).slice(0, 6);
}

function buildDeliverables(
  profile: OnboardingProfile,
  selectedSources: CatalogItem[],
  agents: string[],
) {
  const visibleSources = selectedSources.slice(0, 4).map((item) => item.label);
  const sourceSummary =
    visibleSources.length > 0 ? visibleSources.join(", ") : "core public surfaces";

  return [
    `${profile.companyName} onboarding brief covering ${sourceSummary}.`,
    `${profile.useCase.replaceAll("-", " ")} assistant scope for the ${profile.industry.toLowerCase()} motion.`,
    `${profile.integrationMode.replaceAll("-", " ")} operating model with roles for ${agents
      .slice(0, 3)
      .join(", ")}.`,
    `Governance packet for ${profile.compliance.length > 0 ? profile.compliance.join(", ") : "baseline delivery controls"}.`,
  ];
}

function buildIntegrationSteps(profile: OnboardingProfile) {
  if (profile.integrationMode === "advisory") {
    return [
      "Capture onboarding answers in the web intake and generate a delivery brief.",
      "Review source priorities, agent roles, and rollout constraints with stakeholders.",
      "Hand the approved brief to an operator who runs llm-kb and publishes outputs back into the project.",
    ];
  }

  if (profile.integrationMode === "local-bridge") {
    return [
      "The website collects onboarding answers and prepares a normalized intake packet.",
      "A local bridge or desktop helper runs llm-kb knowledge compilation and agent selection against that packet.",
      "The generated briefs, QA notes, and publish-safe outputs return to the site or operator dashboard.",
    ];
  }

  return [
    "The website posts onboarding answers to an intake API and stores the project scope.",
    "A worker runs llm-kb knowledge compilation, agent recommendation, synthesis, and packaging against the approved sources.",
    "The platform stores the resulting brief, review outputs, and release-ready artifacts for launch and support teams.",
  ];
}

export function buildOnboardingResult(
  profile: OnboardingProfile,
): OnboardingResult {
  const selectedSources = allCatalogItems.filter((item) =>
    profile.sources.includes(item.id),
  );
  const metrics = scoreProfile(profile);
  const score =
    metrics.knowledge + metrics.governance + metrics.operations + metrics.activation;
  const label = labelForScore(score);
  const agents = buildAgentList(profile);
  const deliverables = buildDeliverables(profile, selectedSources, agents);
  const integrationSteps = buildIntegrationSteps(profile);

  return {
    score,
    label,
    selectedSources,
    metrics,
    agents,
    deliverables,
    integrationSteps,
    summary: `${profile.companyName} can start with a ${label.toLowerCase()} built around ${selectedSources.length} selected source surfaces, ${agents.length} recommended llm-kb-aligned roles, and a ${profile.integrationMode.replaceAll("-", " ")} activation path.`,
  };
}
