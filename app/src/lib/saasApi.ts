import { defaultOnboardingProfile, type OnboardingProfile } from "./onboarding";
import { getConfiguredApiBaseUrl } from "./api";

export type AppJob = {
  id: string;
  type: string;
  status: string;
  attempts: number;
  maxAttempts: number;
  error?: string | null;
  createdAt: string;
  updatedAt: string;
  result?: Record<string, unknown> | null;
};

export type AppArtifact = {
  id: string;
  label: string;
  kind: string;
  preview: string;
  storageUri: string;
  createdAt: string;
  jobId?: string | null;
};

export type AppDashboard = {
  environment: string;
  user: { id: string; email: string; name: string };
  organizations: Array<{
    id: string;
    name: string;
    slug: string;
    plan: string;
    role: string;
    environment: string;
  }>;
  activeOrganizationId: string;
  projects: Array<{
    id: string;
    organization_id: string;
    name: string;
    slug: string;
    description?: string;
  }>;
  activeProjectId?: string;
  members: Array<{ id: string; email: string; name: string; role: string; status: string }>;
  jobs: AppJob[];
  artifacts: AppArtifact[];
  datasetPipelines: Array<{ id: string; name: string; status: string; spec?: Record<string, unknown> }>;
  datasetBatches: Array<{
    id: string;
    status: string;
    provider: string;
    requested_rows: number;
    accepted_rows: number;
    rejected_rows: number;
    pass_rate: number;
    report?: Record<string, unknown>;
  }>;
  reviewQueueCount: number;
  billing: {
    provider: string;
    status: string;
    plan: string;
    planDefinition: {
      name: string;
      price: string;
      limits: Record<string, number>;
      features: string[];
    };
    usage: Record<string, number>;
    stripeConfigured: boolean;
  };
  providers: Array<{
    provider: string;
    configured: boolean;
    mode: string;
    maskedValue?: string | null;
  }>;
  monitoring: {
    failedJobs: number;
    queuedJobs: number;
    health: string;
    errorTrackingConfigured: boolean;
    latestAuditEvents: Array<Record<string, string>>;
  };
  security: {
    tenantIsolation: string;
    secretPolicy: string;
    corsOrigin: string;
    rateLimitMode: string;
  };
};

export type AuthResponse = {
  token: string;
  expiresAt: string;
  user: AppDashboard["user"];
  dashboard: AppDashboard;
};

function apiUrl(path: string) {
  const base = getConfiguredApiBaseUrl();
  return base ? `${base}${path}` : path;
}

async function request<T>(
  path: string,
  options: RequestInit & { token?: string } = {},
): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  if (options.token) {
    headers.set("Authorization", `Bearer ${options.token}`);
  }

  const response = await fetch(apiUrl(path), {
    ...options,
    headers,
  });
  const payload = (await response.json().catch(() => null)) as
    | T
    | { error?: string }
    | null;

  if (!response.ok) {
    throw new Error(
      payload &&
        typeof payload === "object" &&
        "error" in payload &&
        payload.error
        ? payload.error
        : "The OnboardAI API request failed.",
    );
  }

  return payload as T;
}

export function signup(input: {
  email: string;
  password: string;
  name: string;
  organizationName: string;
}) {
  return request<AuthResponse>("/api/auth/signup", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function login(input: { email: string; password: string }) {
  return request<AuthResponse>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function loadDashboard(token: string) {
  return request<AppDashboard>("/api/app/dashboard", { token });
}

export function createProject(
  token: string,
  input: { organizationId: string; name: string; description: string },
) {
  return request<{ project: AppDashboard["projects"][number] }>("/api/app/projects", {
    method: "POST",
    token,
    body: JSON.stringify(input),
  });
}

export function createOnboardingJob(
  token: string,
  input: {
    organizationId: string;
    projectId?: string;
    profile?: OnboardingProfile;
  },
) {
  return request<{ job: AppJob }>("/api/app/onboarding-jobs", {
    method: "POST",
    token,
    body: JSON.stringify({
      ...input,
      profile: input.profile ?? defaultOnboardingProfile,
    }),
  });
}

export function createDatasetBatchJob(
  token: string,
  input: {
    organizationId: string;
    projectId?: string;
    provider: string;
    requestedRows: number;
    profile?: Partial<OnboardingProfile>;
  },
) {
  return request<{ job: AppJob }>("/api/app/dataset-batches", {
    method: "POST",
    token,
    body: JSON.stringify(input),
  });
}

export function runNextJob(token: string) {
  return request<{ processed: Array<Record<string, unknown>>; count: number }>(
    "/api/app/jobs/run-next",
    {
      method: "POST",
      token,
      body: JSON.stringify({ limit: 1 }),
    },
  );
}

export function saveProviderKey(
  token: string,
  input: { organizationId: string; provider: string; secret: string },
) {
  return request<{ provider: string; configured: boolean; maskedValue: string }>(
    "/api/app/provider-keys",
    {
      method: "POST",
      token,
      body: JSON.stringify(input),
    },
  );
}

export function createApiKey(
  token: string,
  input: { organizationId: string; name: string; role: string },
) {
  return request<{ id: string; name: string; prefix: string; role: string; secret: string }>(
    "/api/app/api-keys",
    {
      method: "POST",
      token,
      body: JSON.stringify(input),
    },
  );
}

export function getArtifact(token: string, artifactId: string) {
  return request<AppArtifact & { content: string }>(`/api/app/artifacts/${artifactId}`, {
    token,
  });
}

export function exportDatasetBatch(token: string, batchId: string) {
  return request<{ batchId: string; format: string; rowCount: number; content: string }>(
    `/api/app/dataset-batches/${batchId}/export`,
    { token },
  );
}
