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

export type TrailOutcome = "success" | "stuck";

export type TrailMemory = {
  successes: Record<string, number>;
  stuck: Record<string, number>;
  updatedAt?: string;
};

export type LivingPathSignal = {
  model: string;
  label: string;
  action: string;
  priority: "watch" | "guide" | "route" | "adapt";
};

export type LivingOnboardingPath = {
  pathKey: string;
  trailStrength: number;
  confusionRisk: number;
  recommendedRole: string;
  receptiveWindow: string;
  adaptiveTone: string;
  progressiveAccess: string[];
  routeNow: string[];
  microQuestions: string[];
  cohortSignals: string[];
  simulation: string;
  signals: LivingPathSignal[];
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

export const defaultTrailMemory: TrailMemory = {
  successes: {},
  stuck: {},
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
  livingPath: LivingOnboardingPath;
};

function unique<T>(values: T[]) {
  return [...new Set(values)];
}

function clamp(value: number, min = 0, max = 100) {
  return Math.max(min, Math.min(max, Math.round(value)));
}

export function profileTrailKey(profile: OnboardingProfile) {
  return [
    profile.useCase,
    profile.companySize,
    profile.stage,
    profile.integrationMode,
  ].join(":");
}

export function evolveTrailMemory(
  memory: TrailMemory,
  profile: OnboardingProfile,
  outcome: TrailOutcome,
): TrailMemory {
  const pathKey = profileTrailKey(profile);
  const successes = { ...memory.successes };
  const stuck = { ...memory.stuck };

  if (outcome === "success") {
    successes[pathKey] = (successes[pathKey] ?? 0) + 1;
  } else {
    stuck[pathKey] = (stuck[pathKey] ?? 0) + 1;
  }

  return {
    successes,
    stuck,
    updatedAt: new Date().toISOString(),
  };
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
  const agents = ["Technical Writer"];

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

  if (
    profile.sources.includes("resources-api-reference") ||
    profile.integrationMode !== "advisory"
  ) {
    agents.push("Backend Architect");
  }

  if (
    profile.compliance.length > 0 ||
    profile.stage === "production" ||
    profile.sources.includes("product-security") ||
    profile.sources.includes("company-legal")
  ) {
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
    "The website posts onboarding answers to /api/onboarding and stores the project scope.",
    "A worker runs llm-kb knowledge compilation, agent recommendation, synthesis, and packaging against the approved sources.",
    "The platform stores the resulting brief, review outputs, and release-ready artifacts for launch and support teams.",
  ];
}

function priorityRoleFor(profile: OnboardingProfile) {
  if (profile.useCase === "product-api-assistant") {
    return "Developer success";
  }
  if (profile.useCase === "customer-support") {
    return "Support lead";
  }
  if (profile.useCase === "sales-enablement") {
    return "Revenue enablement";
  }
  if (profile.useCase === "operations-assistant") {
    return "Operations owner";
  }
  return "Internal champion";
}

function receptiveWindowFor(profile: OnboardingProfile) {
  if (profile.useCase === "customer-support") {
    return "Before support handoff or queue review";
  }
  if (profile.useCase === "product-api-assistant") {
    return "Morning developer planning block";
  }
  if (profile.useCase === "sales-enablement") {
    return "After account review and before follow-up drafting";
  }
  if (profile.useCase === "operations-assistant") {
    return "During compliance or runbook review";
  }
  return "At the start of a focused work block";
}

function adaptiveToneFor(profile: OnboardingProfile) {
  if (profile.stage === "production" || profile.compliance.length >= 2) {
    return "Precise, governance-aware, and escalation-first";
  }
  if (profile.companySize === "smb") {
    return "Direct, lightweight, and momentum-focused";
  }
  if (profile.useCase === "product-api-assistant") {
    return "Technical, example-led, and source-cited";
  }
  return "Calm, practical, and role-specific";
}

function buildLivingPath(
  profile: OnboardingProfile,
  selectedSources: CatalogItem[],
  metrics: ScoreBreakdown,
  trailMemory: TrailMemory,
): LivingOnboardingPath {
  const pathKey = profileTrailKey(profile);
  const successes = trailMemory.successes[pathKey] ?? 0;
  const stuck = trailMemory.stuck[pathKey] ?? 0;
  const score =
    metrics.knowledge + metrics.governance + metrics.operations + metrics.activation;
  const missingDocs =
    !profile.sources.includes("resources-documentation") &&
    !profile.sources.includes("resources-api-reference");
  const missingEscalation = !profile.sources.includes("company-contact");
  const governanceLoad = profile.compliance.length >= 2 ? 8 : 0;
  const productionLoad = profile.stage === "production" ? 10 : profile.stage === "pilot" ? 5 : 0;
  const confusionRisk = clamp(
    96 - score + stuck * 9 + (missingDocs ? 14 : 0) + (missingEscalation ? 8 : 0) + governanceLoad + productionLoad,
  );
  const trailStrength = clamp(
    22 + successes * 14 + selectedSources.length * 4 + profile.systems.length * 3 - stuck * 7,
  );
  const recommendedRole = priorityRoleFor(profile);
  const receptiveWindow = receptiveWindowFor(profile);
  const adaptiveTone = adaptiveToneFor(profile);
  const sourceLabels = selectedSources.slice(0, 3).map((item) => item.label);
  const sourceRoute =
    sourceLabels.length > 0
      ? sourceLabels.join(", ")
      : "Platform, Documentation, and Contact";
  const readinessState =
    confusionRisk >= 58 ? "intervene now" : confusionRisk >= 36 ? "guide closely" : "continue path";

  return {
    pathKey,
    trailStrength,
    confusionRisk,
    recommendedRole,
    receptiveWindow,
    adaptiveTone,
    progressiveAccess: [
      "Intake brief",
      "Source QA packet",
      profile.stage === "production" ? "Governed launch workspace" : "Pilot workspace",
      "Publishing and support handoff",
    ],
    routeNow: [
      `Route ${recommendedRole.toLowerCase()} through ${sourceRoute}.`,
      `Use ${profile.systems.slice(0, 2).join(" and ") || "website"} as the first delivery surface.`,
      `Hold governance review around ${profile.compliance.join(", ") || "baseline controls"}.`,
    ],
    microQuestions: [
      "Which role must reach value first?",
      "Which source should override every other answer?",
      "What signal should trigger a human handoff?",
    ],
    cohortSignals: [
      `Sync ${recommendedRole.toLowerCase()}, implementation, and review owners around the same packet.`,
      `Keep a shared checkpoint when ${profile.companyName} moves from ${profile.stage} to the next stage.`,
    ],
    simulation:
      confusionRisk >= 58
        ? "Run a stuck-user simulation before launch and remove the first blocked step."
        : "Simulate one confused user path each cycle so the next cohort gets a clearer trail.",
    signals: [
      {
        model: "Immune system",
        label: "Confusion sensor",
        priority: confusionRisk >= 58 ? "guide" : "watch",
        action: `${readinessState}: watch repeated revisits, low-confidence answers, and missing-source gaps.`,
      },
      {
        model: "Ant colonies",
        label: "Pheromone trail",
        priority: "route",
        action: `This path has ${trailStrength}% trail strength from selected sources and local success memory.`,
      },
      {
        model: "Mycelium networks",
        label: "Knowledge routing",
        priority: "route",
        action: `Route the right context to ${recommendedRole.toLowerCase()} before widening access.`,
      },
      {
        model: "Flocking birds",
        label: "Team sync",
        priority: "guide",
        action: "Keep each role moving by the same checkpoint instead of separate static checklists.",
      },
      {
        model: "Predator-prey cycles",
        label: "Stuck simulation",
        priority: confusionRisk >= 42 ? "adapt" : "watch",
        action: "Stress-test where users misread setup, trust, permissions, or source authority.",
      },
      {
        model: "Skin",
        label: "Progressive access",
        priority: "guide",
        action: "Unlock deeper tools only after the brief, source QA, and governance packet are ready.",
      },
      {
        model: "Circadian rhythm",
        label: "Timing",
        priority: "adapt",
        action: `Send the next nudge ${receptiveWindow.toLowerCase()}.`,
      },
      {
        model: "Tree roots",
        label: "Priority root",
        priority: "route",
        action: `Feed the weakest root first: ${metrics.knowledge <= metrics.governance ? "source coverage" : "governance clarity"}.`,
      },
      {
        model: "Echolocation",
        label: "Micro-checks",
        priority: "guide",
        action: "Ask short readiness questions to locate confusion before a person drops out.",
      },
      {
        model: "Octopus camouflage",
        label: "Adaptive tone",
        priority: "adapt",
        action: `Use a ${adaptiveTone.toLowerCase()} coaching style for this profile.`,
      },
    ],
  };
}

export function buildOnboardingResult(
  profile: OnboardingProfile,
  trailMemory: TrailMemory = defaultTrailMemory,
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
  const livingPath = buildLivingPath(profile, selectedSources, metrics, trailMemory);

  return {
    score,
    label,
    selectedSources,
    metrics,
    agents,
    deliverables,
    integrationSteps,
    livingPath,
    summary: `${profile.companyName} can start with a ${label.toLowerCase()} built around ${selectedSources.length} selected source surfaces, ${agents.length} recommended llm-kb-aligned roles, and a ${profile.integrationMode.replaceAll("-", " ")} activation path.`,
  };
}
