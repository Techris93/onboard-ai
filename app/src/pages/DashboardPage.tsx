import { type FormEvent, useEffect, useState } from "react";
import {
  createApiKey,
  createDatasetBatchJob,
  createOnboardingJob,
  createProject,
  exportDatasetBatch,
  getArtifact,
  loadDashboard,
  login,
  runNextJob,
  saveProviderKey,
  signup,
  type AppArtifact,
  type AppDashboard,
} from "../lib/saasApi";
import { defaultOnboardingProfile, type OnboardingProfile } from "../lib/onboarding";

const TOKEN_KEY = "onboard-ai:saas-token";

function downloadText(filename: string, content: string) {
  const url = URL.createObjectURL(new Blob([content], { type: "text/plain" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function AuthPanel({
  onAuthed,
}: {
  onAuthed: (token: string, dashboard: AppDashboard) => void;
}) {
  const [mode, setMode] = useState<"login" | "signup">("signup");
  const [email, setEmail] = useState("owner@onboardai.local");
  const [password, setPassword] = useState("onboardai-local");
  const [name, setName] = useState("OnboardAI Owner");
  const [organizationName, setOrganizationName] = useState("OnboardAI Workspace");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      const response =
        mode === "signup"
          ? await signup({ email, password, name, organizationName })
          : await login({ email, password });
      window.localStorage.setItem(TOKEN_KEY, response.token);
      onAuthed(response.token, response.dashboard);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="app-shell auth-shell">
      <section className="auth-hero">
        <a className="brand-mark" href="./">
          OnboardAI
        </a>
        <p className="section-label">SaaS workspace</p>
        <h1>Operate AI onboarding like a production system.</h1>
        <p>
          Create a workspace, save projects, enqueue onboarding jobs, generate
          dataset batches, review quality gates, and keep artifacts in a durable
          product dashboard.
        </p>
      </section>

      <form className="glass-card auth-card" onSubmit={submit}>
        <div className="auth-mode-row">
          <button
            type="button"
            className={`auth-mode${mode === "signup" ? " is-active" : ""}`}
            onClick={() => setMode("signup")}
          >
            Sign up
          </button>
          <button
            type="button"
            className={`auth-mode${mode === "login" ? " is-active" : ""}`}
            onClick={() => setMode("login")}
          >
            Log in
          </button>
        </div>

        {mode === "signup" ? (
          <>
            <label className="field">
              <span className="field-label">Name</span>
              <input className="field-input" value={name} onChange={(event) => setName(event.target.value)} />
            </label>
            <label className="field">
              <span className="field-label">Workspace</span>
              <input
                className="field-input"
                value={organizationName}
                onChange={(event) => setOrganizationName(event.target.value)}
              />
            </label>
          </>
        ) : null}

        <label className="field">
          <span className="field-label">Email</span>
          <input className="field-input" value={email} onChange={(event) => setEmail(event.target.value)} />
        </label>
        <label className="field">
          <span className="field-label">Password</span>
          <input
            className="field-input"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </label>

        {error ? <p className="app-error">{error}</p> : null}
        <button className="button button-primary app-wide-button" type="submit" disabled={submitting}>
          {submitting ? "Working..." : mode === "signup" ? "Create workspace" : "Log in"}
        </button>
        <p className="field-copy">
          Local/dev credentials are safe to replace. Provider and billing
          secrets are never stored in the frontend.
        </p>
      </form>
    </main>
  );
}

function MetricCard({ label, value }: { label: string; value: string | number }) {
  return (
    <article className="metric-card app-metric-card">
      <div className="metric-value">{value}</div>
      <h3 className="card-heading">{label}</h3>
    </article>
  );
}

export default function DashboardPage() {
  const [token, setToken] = useState(() => window.localStorage.getItem(TOKEN_KEY) ?? "");
  const [dashboard, setDashboard] = useState<AppDashboard | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [projectName, setProjectName] = useState("Customer AI Rollout");
  const [companyName, setCompanyName] = useState("Customer Company");
  const [requestedRows, setRequestedRows] = useState(8);
  const [provider, setProvider] = useState("local");
  const [providerSecret, setProviderSecret] = useState("");
  const [selectedArtifact, setSelectedArtifact] = useState<(AppArtifact & { content: string }) | null>(null);
  const [lastApiKey, setLastApiKey] = useState("");

  const refresh = async (nextToken = token) => {
    if (!nextToken) {
      return;
    }
    const response = await loadDashboard(nextToken);
    setDashboard(response);
  };

  useEffect(() => {
    if (!token) {
      return;
    }
    refresh().catch((err) => {
      setError(err instanceof Error ? err.message : "Could not load dashboard.");
      window.localStorage.removeItem(TOKEN_KEY);
      setToken("");
    });
  }, [token]);

  const runAction = async (action: () => Promise<unknown>, success: string) => {
    setError("");
    setNotice("");
    try {
      await action();
      setNotice(success);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Action failed.");
    }
  };

  if (!token || !dashboard) {
    return (
      <AuthPanel
        onAuthed={(nextToken, nextDashboard) => {
          setToken(nextToken);
          setDashboard(nextDashboard);
        }}
      />
    );
  }

  const activeOrg = dashboard.organizations.find(
    (item) => item.id === dashboard.activeOrganizationId,
  );
  const activeProject = dashboard.projects.find(
    (item) => item.id === dashboard.activeProjectId,
  );
  const latestBatch = dashboard.datasetBatches[0];

  const profile: OnboardingProfile = {
    ...defaultOnboardingProfile,
    companyName,
    useCase: "fine-tuning-dataset" as const,
    sources: [
      "product-platform",
      "product-dataset-pipeline",
      "product-elm-readiness",
      "product-security",
      "resources-documentation",
      "resources-api-reference",
    ],
    compliance: ["SOC 2"],
    systems: ["website", "developer-portal", "support-desk"],
  };

  return (
    <main className="app-shell dashboard-shell">
      <header className="app-topbar">
        <a className="brand-mark" href="./">
          OnboardAI
        </a>
        <div>
          <span>{dashboard.user.email}</span>
          <button
            className="button button-secondary app-compact-button"
            type="button"
            onClick={() => {
              window.localStorage.removeItem(TOKEN_KEY);
              setToken("");
              setDashboard(null);
            }}
          >
            Log out
          </button>
        </div>
      </header>

      <section className="app-hero-panel">
        <div>
          <p className="section-label">Production dashboard</p>
          <h1>{activeOrg?.name ?? "Workspace"}</h1>
          <p>
            Manage projects, durable jobs, artifacts, dataset batches, provider
            settings, billing readiness, audit signals, and security posture.
          </p>
        </div>
        <div className="app-status-card">
          <span>Environment</span>
          <strong>{dashboard.environment}</strong>
          <small>Plan: {dashboard.billing.planDefinition.name}</small>
        </div>
      </section>

      {error ? <div className="app-error">{error}</div> : null}
      {notice ? <div className="app-notice">{notice}</div> : null}

      <section className="app-grid app-metrics">
        <MetricCard label="Projects" value={dashboard.projects.length} />
        <MetricCard label="Queued jobs" value={dashboard.monitoring.queuedJobs} />
        <MetricCard label="Artifacts" value={dashboard.artifacts.length} />
        <MetricCard label="Review queue" value={dashboard.reviewQueueCount} />
      </section>

      <section className="app-grid app-two-column">
        <article className="glass-card app-panel">
          <h2>Start Work</h2>
          <p className="card-copy">
            Jobs are durable. Create them first, then run the worker so long AI
            workflows do not depend on one request staying open.
          </p>
          <label className="field">
            <span className="field-label">Company for this run</span>
            <input className="field-input" value={companyName} onChange={(event) => setCompanyName(event.target.value)} />
          </label>
          <div className="button-row">
            <button
              className="button button-primary"
              type="button"
              onClick={() =>
                runAction(
                  () =>
                    createOnboardingJob(token, {
                      organizationId: dashboard.activeOrganizationId,
                      projectId: dashboard.activeProjectId,
                      profile,
                    }),
                  "Onboarding job queued.",
                )
              }
            >
              Queue onboarding
            </button>
            <button
              className="button button-secondary"
              type="button"
              onClick={() => runAction(() => runNextJob(token), "Worker processed the next job.")}
            >
              Run worker once
            </button>
          </div>
        </article>

        <article className="glass-card app-panel">
          <h2>Dataset Generation</h2>
          <p className="card-copy">
            Local/offline generation is functional today. External providers use
            the same adapter contract once credentials and live execution are enabled.
          </p>
          <div className="form-grid">
            <label className="field">
              <span className="field-label">Provider</span>
              <select className="field-input" value={provider} onChange={(event) => setProvider(event.target.value)}>
                {dashboard.providers.map((item) => (
                  <option key={item.provider} value={item.provider}>
                    {item.provider}
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              <span className="field-label">Rows</span>
              <input
                className="field-input"
                type="number"
                min={1}
                max={100}
                value={requestedRows}
                onChange={(event) => setRequestedRows(Number(event.target.value))}
              />
            </label>
          </div>
          <button
            className="button button-primary app-wide-button"
            type="button"
            onClick={() =>
              runAction(
                () =>
                  createDatasetBatchJob(token, {
                    organizationId: dashboard.activeOrganizationId,
                    projectId: dashboard.activeProjectId,
                    provider,
                    requestedRows,
                    profile,
                  }),
                "Dataset batch job queued.",
              )
            }
          >
            Queue dataset batch
          </button>
        </article>
      </section>

      <section className="app-grid app-two-column">
        <article className="glass-card app-panel">
          <h2>Projects</h2>
          <p className="card-copy">
            Active project: {activeProject?.name ?? "No project selected"}
          </p>
          <label className="field">
            <span className="field-label">New project</span>
            <input className="field-input" value={projectName} onChange={(event) => setProjectName(event.target.value)} />
          </label>
          <button
            className="button button-secondary app-wide-button"
            type="button"
            onClick={() =>
              runAction(
                () =>
                  createProject(token, {
                    organizationId: dashboard.activeOrganizationId,
                    name: projectName,
                    description: "Production SaaS workspace project.",
                  }),
                "Project created.",
              )
            }
          >
            Create project
          </button>
          <div className="app-list">
            {dashboard.projects.map((project) => (
              <div key={project.id} className="app-list-item">
                <strong>{project.name}</strong>
                <span>{project.slug}</span>
              </div>
            ))}
          </div>
        </article>

        <article className="glass-card app-panel">
          <h2>Jobs</h2>
          <div className="app-list">
            {dashboard.jobs.map((job) => (
              <div key={job.id} className="app-list-item">
                <strong>{job.type}</strong>
                <span>{job.status}</span>
                {job.result ? <small>{JSON.stringify(job.result).slice(0, 180)}</small> : null}
              </div>
            ))}
            {dashboard.jobs.length === 0 ? <p className="card-copy">No jobs yet.</p> : null}
          </div>
        </article>
      </section>

      <section className="app-grid app-two-column">
        <article className="glass-card app-panel">
          <h2>Artifacts</h2>
          <div className="app-list">
            {dashboard.artifacts.map((artifact) => (
              <button
                key={artifact.id}
                className="app-list-item app-list-button"
                type="button"
                onClick={() =>
                  runAction(async () => {
                    const result = await getArtifact(token, artifact.id);
                    setSelectedArtifact(result);
                  }, "Artifact opened.")
                }
              >
                <strong>{artifact.label}</strong>
                <span>{artifact.kind}</span>
                <small>{artifact.preview}</small>
              </button>
            ))}
            {dashboard.artifacts.length === 0 ? <p className="card-copy">Artifacts appear after jobs complete.</p> : null}
          </div>
        </article>

        <article className="glass-card app-panel">
          <h2>Artifact Preview</h2>
          {selectedArtifact ? (
            <>
              <div className="artifact-header">
                <strong>{selectedArtifact.label}</strong>
                <span className="artifact-kind">{selectedArtifact.kind}</span>
              </div>
              <pre className="app-code-block">{selectedArtifact.content}</pre>
              <button
                className="button button-secondary app-wide-button"
                type="button"
                onClick={() => downloadText(`${selectedArtifact.label}.${selectedArtifact.kind}`, selectedArtifact.content)}
              >
                Download artifact
              </button>
            </>
          ) : (
            <p className="card-copy">Open an artifact to inspect and export it.</p>
          )}
        </article>
      </section>

      <section className="app-grid app-two-column">
        <article className="glass-card app-panel">
          <h2>Dataset Batches</h2>
          <div className="app-list">
            {dashboard.datasetBatches.map((batch) => (
              <div key={batch.id} className="app-list-item">
                <strong>{batch.provider} batch</strong>
                <span>{batch.status}</span>
                <small>
                  {batch.accepted_rows} accepted, {batch.rejected_rows} rejected,
                  pass rate {Math.round(batch.pass_rate * 100)}%
                </small>
              </div>
            ))}
          </div>
          {latestBatch ? (
            <button
              className="button button-secondary app-wide-button"
              type="button"
              onClick={() =>
                runAction(async () => {
                  const result = await exportDatasetBatch(token, latestBatch.id);
                  downloadText(`${latestBatch.id}.jsonl`, result.content);
                }, "Dataset export prepared.")
              }
            >
              Export latest accepted rows
            </button>
          ) : null}
        </article>

        <article className="glass-card app-panel">
          <h2>Quality Gates</h2>
          {latestBatch?.report ? (
            <div className="app-list">
              <div className="app-list-item">
                <strong>Pass rate</strong>
                <span>{Math.round(Number(latestBatch.pass_rate) * 100)}%</span>
              </div>
              <div className="app-list-item">
                <strong>Weak labels</strong>
                <span>{JSON.stringify(latestBatch.report.weakLabels ?? [])}</span>
              </div>
              <div className="app-list-item">
                <strong>Coverage gaps</strong>
                <span>{JSON.stringify(latestBatch.report.coverageGaps ?? [])}</span>
              </div>
            </div>
          ) : (
            <p className="card-copy">Run a dataset batch to see gate results.</p>
          )}
        </article>
      </section>

      <section className="app-grid app-three-column">
        <article className="glass-card app-panel">
          <h2>Providers</h2>
          <div className="app-list">
            {dashboard.providers.map((item) => (
              <div key={item.provider} className="app-list-item">
                <strong>{item.provider}</strong>
                <span>{item.configured ? "Configured" : "Needs key"}</span>
                <small>{item.mode}</small>
              </div>
            ))}
          </div>
          <label className="field">
            <span className="field-label">External provider secret</span>
            <input
              className="field-input"
              value={providerSecret}
              onChange={(event) => setProviderSecret(event.target.value)}
              placeholder="Stored server-side only"
            />
          </label>
          <button
            className="button button-secondary app-wide-button"
            type="button"
            onClick={() =>
              runAction(
                () =>
                  saveProviderKey(token, {
                    organizationId: dashboard.activeOrganizationId,
                    provider: provider === "local" ? "gemini" : provider,
                    secret: providerSecret,
                  }),
                "Provider key saved server-side.",
              )
            }
          >
            Save provider key
          </button>
        </article>

        <article className="glass-card app-panel">
          <h2>Billing</h2>
          <p className="card-copy">
            {dashboard.billing.planDefinition.name} plan, {dashboard.billing.status}
          </p>
          <div className="app-list">
            {Object.entries(dashboard.billing.usage).map(([key, value]) => (
              <div key={key} className="app-list-item">
                <strong>{key}</strong>
                <span>{value}</span>
              </div>
            ))}
          </div>
          <small>
            Stripe configured: {dashboard.billing.stripeConfigured ? "yes" : "mock mode"}
          </small>
        </article>

        <article className="glass-card app-panel">
          <h2>Security</h2>
          <div className="app-list">
            <div className="app-list-item">
              <strong>Tenant isolation</strong>
              <span>{dashboard.security.tenantIsolation}</span>
            </div>
            <div className="app-list-item">
              <strong>Secrets</strong>
              <span>{dashboard.security.secretPolicy}</span>
            </div>
            <div className="app-list-item">
              <strong>Rate limit</strong>
              <span>{dashboard.security.rateLimitMode}</span>
            </div>
          </div>
          <button
            className="button button-secondary app-wide-button"
            type="button"
            onClick={() =>
              runAction(async () => {
                const result = await createApiKey(token, {
                  organizationId: dashboard.activeOrganizationId,
                  name: "Dashboard API key",
                  role: "operator",
                });
                setLastApiKey(result.secret);
              }, "API key created. Copy it now; it will not be shown again.")
            }
          >
            Create API key
          </button>
          {lastApiKey ? <pre className="app-code-block">{lastApiKey}</pre> : null}
        </article>
      </section>

      <section className="app-grid app-two-column">
        <article className="glass-card app-panel">
          <h2>Team</h2>
          <div className="app-list">
            {dashboard.members.map((member) => (
              <div key={member.id} className="app-list-item">
                <strong>{member.name}</strong>
                <span>{member.role}</span>
                <small>{member.email}</small>
              </div>
            ))}
          </div>
        </article>
        <article className="glass-card app-panel">
          <h2>Monitoring</h2>
          <p className="card-copy">
            Health is {dashboard.monitoring.health}; failed jobs: {dashboard.monitoring.failedJobs}.
          </p>
          <div className="app-list">
            {dashboard.monitoring.latestAuditEvents.map((event, index) => (
              <div key={`${event.action}-${index}`} className="app-list-item">
                <strong>{event.action}</strong>
                <span>{event.target_type}</span>
                <small>{event.created_at}</small>
              </div>
            ))}
          </div>
        </article>
      </section>
    </main>
  );
}
