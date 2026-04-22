import { useRef, useState } from "react";
import { useRevealOnScroll } from "../hooks/useRevealOnScroll";
import {
  allCatalogItems,
  buildOnboardingResult,
  catalogGroups,
  companySizes,
  complianceOptions,
  defaultOnboardingProfile,
  deliverySystems,
  industries,
  integrationModes,
  rolloutStages,
  type DeliverySystem,
  type OnboardingProfile,
  type RolloutStage,
  type IntegrationMode,
  type UseCase,
  type CompanySize,
  useCaseOptions,
} from "../lib/onboarding";

function toggleValue(values: string[], value: string) {
  return values.includes(value)
    ? values.filter((item) => item !== value)
    : [...values, value];
}

export default function OnboardingSection() {
  const sectionRef = useRef<HTMLElement | null>(null);
  const [profile, setProfile] = useState(defaultOnboardingProfile);

  useRevealOnScroll(sectionRef);

  const result = buildOnboardingResult(profile);

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
          This intake turns company context, source selection, delivery scope,
          and governance needs into a launch-ready onboarding packet. The
          website can do the intake today, and the same packet can drive a live
          llm-kb workflow through a backend worker or local bridge.
        </p>

        <div className="onboarding-layout">
          <form
            className="glass-card onboarding-panel reveal"
            onSubmit={(event) => event.preventDefault()}
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
          </form>

          <aside className="glass-card onboarding-summary reveal">
            <div className="summary-score-row">
              <div>
                <div className="summary-kicker">Readiness score</div>
                <div className="summary-score">{result.score}</div>
              </div>
              <div className="summary-label">{result.label}</div>
            </div>

            <p className="card-copy onboarding-summary-copy">{result.summary}</p>

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
                {result.agents.map((agent) => (
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
