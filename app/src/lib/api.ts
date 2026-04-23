import type { OnboardingProfile } from "./onboarding";

declare global {
  interface Window {
    __ONBOARDAI_API_BASE_URL__?: string;
  }
}

export type BackendArtifact = {
  label: string;
  kind: string;
  path: string;
  preview: string;
};

export type BackendCommandResult = {
  step: string;
  command: string;
  ok: boolean;
  exit_code: number;
  summary: string;
  stdout_preview: string;
  stderr_preview: string;
  parsed: Record<string, string>;
};

export type BackendOnboardingResponse = {
  runId: string;
  status: string;
  createdAt: string;
  companyName: string;
  integrationMode: string;
  summary: string;
  recommendedAgents: string[];
  artifacts: BackendArtifact[];
  commandResults: BackendCommandResult[];
  warnings: string[];
  llmKb: {
    available: boolean;
    binary: string;
    root: string;
  };
  runDirectory: string;
  resultUrl: string;
};

function cleanBaseUrl(value: string | undefined) {
  const trimmed = value?.trim();
  if (!trimmed) {
    return "";
  }
  return trimmed.endsWith("/") ? trimmed.slice(0, -1) : trimmed;
}

export function getConfiguredApiBaseUrl() {
  if (typeof window === "undefined") {
    return "";
  }

  const runtimeBase = cleanBaseUrl(window.__ONBOARDAI_API_BASE_URL__);
  if (runtimeBase) {
    return runtimeBase;
  }

  const envBase = cleanBaseUrl(import.meta.env.VITE_API_BASE_URL);
  if (envBase) {
    return envBase;
  }

  if (
    window.location.hostname === "localhost" ||
    window.location.hostname === "127.0.0.1"
  ) {
    return "http://127.0.0.1:8787";
  }

  return "";
}

function buildApiUrl(path: string) {
  const base = getConfiguredApiBaseUrl();
  return base ? `${base}${path}` : path;
}

export async function submitOnboarding(
  profile: OnboardingProfile,
): Promise<BackendOnboardingResponse> {
  const response = await fetch(buildApiUrl("/api/onboarding"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(profile),
  });

  let payload: BackendOnboardingResponse | { error?: string } | null = null;
  try {
    payload = (await response.json()) as BackendOnboardingResponse | {
      error?: string;
    };
  } catch {
    payload = null;
  }

  if (!response.ok) {
    const errorMessage =
      payload && "error" in payload && payload.error
        ? payload.error
        : response.status === 404
          ? "This deployment does not have a live onboarding worker attached yet."
          : "The onboarding worker could not complete this request.";
    throw new Error(errorMessage);
  }

  return payload as BackendOnboardingResponse;
}
