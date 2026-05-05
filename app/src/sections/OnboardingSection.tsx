import { type FormEvent, useEffect, useRef, useState } from "react";
import { useRevealOnScroll } from "../hooks/useRevealOnScroll";
import {
  getConfiguredApiBaseUrl,
  submitOnboarding,
  type BackendOnboardingResponse,
} from "../lib/api";
import {
  allCatalogItems,
  buildOnboardingResult,
  catalogGroups,
  companySizes,
  complianceOptions,
  defaultOnboardingProfile,
  defaultPathMemory,
  deliverySystems,
  evolvePathMemory,
  industries,
  integrationModes,
  type DeliverySystem,
  type OnboardingProfile,
  type RolloutStage,
  type PathMemory,
  type PathOutcome,
  type IntegrationMode,
  type UseCase,
  type CompanySize,
  rolloutStages,
  useCaseOptions,
} from "../lib/onboarding";

const PATH_MEMORY_KEY = "onboard-ai:adaptive-path-memory";

function toggleValue(values: string[], value: string) {
  return values.includes(value)
    ? values.filter((item) => item !== value)
    : [...values, value];
}

function backendStatusText(
  state: "idle" | "submitting" | "success" | "error",
  result: BackendOnboardingResponse | null,
  apiBaseUrl: string,
) {
  if (state === "submitting") {
    return "Live onboarding worker is running this intake now.";
  }

  if (state === "success" && result) {
    return `Stored run ${result.runId} completed in ${result.status} mode.`;
  }

  if (state === "error") {
    return "The live worker did not complete this request, so the page stayed on the planning preview.";
  }

  if (apiBaseUrl) {
    return "This build is configured for live backend onboarding.";
  }

  return "This deployment keeps live backend execution optional until a worker is attached.";
}

function isRecord(value: unknown): value is Record<string, number> {
  return (
    typeof value === "object" &&
    value !== null &&
    Object.values(value).every((item) => typeof item === "number")
  );
}

function loadPathMemory(): PathMemory {
  if (typeof window === "undefined") {
    return defaultPathMemory;
  }

  try {
    const raw = window.localStorage.getItem(PATH_MEMORY_KEY);
    if (!raw) {
      return defaultPathMemory;
    }
    const parsed = JSON.parse(raw) as Partial<PathMemory>;
    if (!isRecord(parsed.successes) || !isRecord(parsed.stuck)) {
      return defaultPathMemory;
    }
    return {
      successes: parsed.successes,
      stuck: parsed.stuck,
      updatedAt: parsed.updatedAt,
    };
  } catch {
    return defaultPathMemory;
  }
}

export default function OnboardingSection() {
  const sectionRef = useRef<HTMLElement | null>(null);
  const [profile, setProfile] = useState(defaultOnboardingProfile);
  const [submissionState, setSubmissionState] = useState<
    "idle" | "submitting" | "success" | "error"
  >("idle");
  const [backendResult, setBackendResult] =
    useState<BackendOnboardingResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [pathMemory, setPathMemory] = useState<PathMemory>(() =>
    loadPathMemory(),
  );

  useRevealOnScroll(sectionRef);

  useEffect(() => {
    window.localStorage.setItem(PATH_MEMORY_KEY, JSON.stringify(pathMemory));
  }, [pathMemory]);

  const result = buildOnboardingResult(profile, pathMemory);
  const adaptivePath = result.adaptivePath;
  const apiBaseUrl = getConfiguredApiBaseUrl();
  const agentList =
    backendResult?.recommendedAgents.length &&
    backendResult.recommendedAgents.length > 0
      ? backendResult.recommendedAgents
      : result.agents;

  const setField = <K extends keyof OnboardingProfile>(
    key: K,
    value: OnboardingProfile[K],
  ) => {
    setProfile((current) => ({
      ...current,
      [key]: value,
    }));
  };

  const toggleSources = (value: string) => {
    setField("sources", toggleValue(profile.sources, value));
  };

  const toggleCompliance = (value: string) => {
    setField("compliance", toggleValue(profile.compliance, value));
  };

  const toggleSystems = (value: DeliverySystem) => {
    setField("systems", toggleValue(profile.systems, value) as DeliverySystem[]);
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmissionState("submitting");
    setErrorMessage("");

    try {
      const response = await submitOnboarding(profile);
      setBackendResult(response);
      setSubmissionState("success");
    } catch (error) {
      setSubmissionState("error");
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "The backend onboarding worker could not complete this request.",
      );
    }
  };

  const recordPathOutcome = (outcome: PathOutcome) => {
    setPathMemory((current) => evolvePathMemory(current, profile, outcome));
  };

  return (
    <section
      id="onboarding"
      ref={sectionRef}
      className="section section-surface"
    >
      <div className="section-inner">
        <div className="section-label reveal">Start onboarding</div>
        <h2 className="section-heading reveal">
          Collect the real inputs before you promise a real AI rollout.
        </h2>
        <p className="section-copy reveal">
          This intake still gives you a live readiness preview on the page, but
          it can now also send the packet into a backend worker that stores the
          run, routes through llm-kb, and returns publish-safe artifacts.
        </p>

        <div className="onboarding-layout">
          <form
            className="glass-card onboarding-panel reveal"
            onSubmit={handleSubmit}
          >
            <div className="form-grid">
              <label className="field">
                <span className="field-label">Company</span>
                <input
                  className="field-input"
                  value={profile.companyName}
                  onChange={(event) => setField("companyName", event.target.value)}
                  placeholder="Company or platform name"
                />
              </label>

              <label className="field">
                <span className="field-label">Industry</span>
                <select
                  className="field-input"
                  value={profile.industry}
                  onChange={(event) => setField("industry", event.target.value)}
                >
                  {industries.map((industry) => (
                    <option key={industry} value={industry}>
                      {industry}
                    </option>
                  ))}
                </select>
              </label>

              <label className="field">
                <span className="field-label">Company size</span>
                <select
                  className="field-input"
                  value={profile.companySize}
                  onChange={(event) =>
                    setField("companySize", event.target.value as CompanySize)
                  }
                >
                  {companySizes.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>

              <label className="field">
                <span className="field-label">Primary use case</span>
                <select
                  className="field-input"
                  value={profile.useCase}
                  onChange={(event) =>
                    setField("useCase", event.target.value as UseCase)
                  }
                >
                  {useCaseOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>

              <label className="field">
                <span className="field-label">Rollout stage</span>
                <select
                  className="field-input"
                  value={profile.stage}
                  onChange={(event) =>
                    setField("stage", event.target.value as RolloutStage)
                  }
                >
                  {rolloutStages.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>

              <label className="field">
                <span className="field-label">Integration mode</span>
                <select
                  className="field-input"
                  value={profile.integrationMode}
                  onChange={(event) =>
                    setField(
                      "integrationMode",
                      event.target.value as IntegrationMode,
                    )
                  }
                >
                  {integrationModes.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <div className="field-block">
              <div className="field-label">Source surfaces</div>
              <p className="field-copy">
                Choose the public and company-facing surfaces that should shape
                the onboarding packet.
              </p>
              <div className="toggle-grid">
                {catalogGroups.map((group) => (
                  <div key={group.id} className="toggle-group">
                    <div className="toggle-group-title">{group.title}</div>
                    <div className="toggle-chip-wrap">
                      {group.items.map((item) => {
                        const active = profile.sources.includes(item.id);
                        return (
                          <button
                            key={item.id}
                            type="button"
                            className={`toggle-chip${active ? " is-active" : ""}`}
                            onClick={() => toggleSources(item.id)}
                          >
                            {item.label}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="field-block">
              <div className="field-label">Security and governance</div>
              <p className="field-copy">
                Pick the controls that change review scope, escalation paths, or
                rollout trust requirements.
              </p>
              <div className="toggle-chip-wrap">
                {complianceOptions.map((option) => {
                  const active = profile.compliance.includes(option);
                  return (
                    <button
                      key={option}
                      type="button"
                      className={`toggle-chip${active ? " is-active" : ""}`}
                      onClick={() => toggleCompliance(option)}
                    >
                      {option}
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="field-block">
              <div className="field-label">Delivery systems</div>
              <p className="field-copy">
                These help determine whether the first rollout is web-first,
                docs-first, support-first, or API-first.
              </p>
              <div className="toggle-chip-wrap">
                {deliverySystems.map((system) => {
                  const active = profile.systems.includes(system.value);
                  return (
                    <button
                      key={system.value}
                      type="button"
                      className={`toggle-chip${active ? " is-active" : ""}`}
                      onClick={() => toggleSystems(system.value)}
                    >
                      {system.label}
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="field-block onboarding-submit-block">
              <div className="field-label">Activation</div>
              <p className="field-copy">
                The page keeps the static pilot preview, and this button can
                also push the intake into a live worker when a backend is
                attached for the deployment.
              </p>
              <div className="button-row onboarding-actions">
                <button
                  className="button button-primary"
                  type="submit"
                  disabled={submissionState === "submitting"}
                >
                  {submissionState === "submitting"
                    ? "Running backend workflow..."
                    : "Run backend onboarding"}
                </button>
              </div>
              <p className="submission-note">
                {backendStatusText(submissionState, backendResult, apiBaseUrl)}
              </p>
            </div>
          </form>

          <aside className="glass-card onboarding-summary reveal">
            <div className="summary-score-row">
              <div>
                <div className="summary-kicker">Readiness score</div>
                <div className="summary-score">{result.score}</div>
              </div>
              <div className="summary-label">{result.label}</div>
            </div>

            <p className="card-copy onboarding-summary-copy">
              {backendResult?.summary ?? result.summary}
            </p>

            <div className="summary-metric-grid">
              <div className="summary-metric-card">
                <span>Knowledge</span>
                <strong>{result.metrics.knowledge}</strong>
              </div>
              <div className="summary-metric-card">
                <span>Governance</span>
                <strong>{result.metrics.governance}</strong>
              </div>
              <div className="summary-metric-card">
                <span>Operations</span>
                <strong>{result.metrics.operations}</strong>
              </div>
              <div className="summary-metric-card">
                <span>Activation</span>
                <strong>{result.metrics.activation}</strong>
              </div>
            </div>

            <div className="summary-block">
              <p className="footer-title">Path outcome memory</p>
              <div className="summary-metric-grid adaptive-path-metrics">
                <div className="summary-metric-card">
                  <span>Confidence</span>
                  <strong>{adaptivePath.pathConfidence}%</strong>
                </div>
                <div className="summary-metric-card">
                  <span>Stuck risk</span>
                  <strong>{adaptivePath.confusionRisk}%</strong>
                </div>
              </div>
              <div className="path-action-row">
                <button
                  type="button"
                  className="button button-secondary path-action-button"
                  onClick={() => recordPathOutcome("success")}
                >
                  Mark successful
                </button>
                <button
                  type="button"
                  className="button button-secondary path-action-button"
                  onClick={() => recordPathOutcome("stuck")}
                >
                  Mark stuck
                </button>
              </div>
            </div>

            <div className="summary-block">
              <p className="footer-title">Adaptive path signals</p>
              <div className="adaptive-signal-list">
                {adaptivePath.signals.map((signal) => (
                  <div key={signal.model} className="adaptive-signal-item">
                    <div className="adaptive-signal-head">
                      <span>{signal.model}</span>
                      <strong>{signal.label}</strong>
                    </div>
                    <p>{signal.action}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="summary-block">
              <p className="footer-title">Route next</p>
              <div className="summary-list">
                {adaptivePath.routeNow.map((step) => (
                  <div key={step} className="summary-list-item">
                    {step}
                  </div>
                ))}
              </div>
            </div>

            <div className="summary-block">
              <p className="footer-title">Micro-checks</p>
              <div className="summary-list">
                {adaptivePath.microQuestions.map((question) => (
                  <div key={question} className="summary-list-item">
                    {question}
                  </div>
                ))}
              </div>
            </div>

            <div className="summary-block">
              <p className="footer-title">First packet includes</p>
              <div className="summary-list">
                {result.deliverables.map((item) => (
                  <div key={item} className="summary-list-item">
                    {item}
                  </div>
                ))}
              </div>
            </div>

            <div className="summary-block">
              <p className="footer-title">Recommended llm-kb agent roles</p>
              <div className="agent-pill-group">
                {agentList.map((agent) => (
                  <span key={agent} className="agent-pill">
                    {agent}
                  </span>
                ))}
              </div>
            </div>

            <div className="summary-block">
              <p className="footer-title">Working integration path</p>
              <div className="summary-list">
                {result.integrationSteps.map((step) => (
                  <div key={step} className="summary-list-item">
                    {step}
                  </div>
                ))}
              </div>
            </div>

            <div className="summary-block">
              <p className="footer-title">Backend execution</p>
              <div className={`execution-banner is-${submissionState}`}>
                {backendStatusText(submissionState, backendResult, apiBaseUrl)}
              </div>

              {errorMessage ? (
                <div className="summary-list">
                  <div className="summary-list-item">{errorMessage}</div>
                </div>
              ) : null}

              {backendResult?.warnings.length ? (
                <div className="summary-list">
                  {backendResult.warnings.map((warning) => (
                    <div key={warning} className="summary-list-item">
                      {warning}
                    </div>
                  ))}
                </div>
              ) : null}

              {backendResult?.commandResults.length ? (
                <div className="summary-list">
                  {backendResult.commandResults.map((item) => (
                    <div key={item.step} className="summary-list-item command-item">
                      <div className="command-summary-row">
                        <strong>{item.step}</strong>
                        <span
                          className={`status-pill${
                            item.ok ? " is-success" : " is-error"
                          }`}
                        >
                          {item.ok ? "Completed" : "Needs attention"}
                        </span>
                      </div>
                      <div className="command-summary-copy">{item.summary}</div>
                    </div>
                  ))}
                </div>
              ) : null}
            </div>

            {backendResult?.artifacts.length ? (
              <div className="summary-block">
                <p className="footer-title">Returned artifacts</p>
                <div className="summary-list">
                  {backendResult.artifacts.slice(0, 4).map((artifact) => (
                    <div
                      key={`${artifact.kind}-${artifact.label}`}
                      className="summary-list-item artifact-item"
                    >
                      <div className="artifact-header">
                        <strong>{artifact.label}</strong>
                        <span className="artifact-kind">{artifact.kind}</span>
                      </div>
                      {artifact.preview ? (
                        <p className="artifact-preview">{artifact.preview}</p>
                      ) : null}
                    </div>
                  ))}
                </div>
              </div>
            ) : null}

            <div className="summary-block">
              <p className="footer-title">Selected surfaces</p>
              <div className="summary-chip-strip">
                {(result.selectedSources.length > 0
                  ? result.selectedSources
                  : allCatalogItems.slice(0, 4)
                ).map((item) => (
                  <span key={item.id} className="proof-pill summary-source-pill">
                    {item.label}
                  </span>
                ))}
              </div>
            </div>
          </aside>
        </div>
      </div>
    </section>
  );
}
