# How To Use OnboardAI

This guide is for the owner or operator running OnboardAI. It explains what is usable today, what runs in local/offline mode, what is provider-ready but needs credentials, and what still needs production infrastructure before real customer use.

## 1. What OnboardAI Is

OnboardAI helps small and mid-sized companies turn company knowledge into governed AI onboarding plans, delivery artifacts, fine-tuning dataset batches, and expert model readiness signals.

The product is built around one practical principle: prepare, validate, and prove company data before fine-tuning or production deployment. That matters because smaller expert language models in the 5B to 15B range need high-quality, narrow, well-labeled data. Low-quality rows create low-quality model behavior.

OnboardAI currently supports:

- Public product education and onboarding intake.
- Authenticated SaaS dashboard under `/app`.
- Organizations, users, projects, jobs, artifacts, dataset batches, quality gate results, usage events, API keys, and provider settings.
- Local/offline dataset generation for safe validation without paid model calls.
- Provider-ready architecture for DeepSeek, Gemini, OpenAI, Anthropic, and local/offline generation.
- Fine-tuning readiness through dataset export, quality reporting, and model-card-oriented artifacts.

## 2. What Is Functional, Mocked, Or Provider-Ready

Functional now:

- Sign up, log in, log out locally from the SaaS dashboard.
- Create a workspace organization during sign up.
- Create projects.
- Queue onboarding jobs.
- Queue dataset batch jobs.
- Run one worker job from the dashboard.
- Run the worker from the command line.
- Store data in SQLite.
- Store and preview artifacts.
- Export accepted dataset rows as JSONL.
- Run local/offline dataset generation.
- Run quality gates and save per-row results.
- Track basic usage and audit events.
- Store provider key hashes and masked provider key labels server-side.
- Generate one-time API keys.

Local/offline or mock today:

- Billing plan display and usage tracking are active, but Stripe checkout and portal routes are not live.
- Local/offline dataset generation is active and deterministic.
- Password reset creates a server token, but email delivery is not wired.
- Team membership is displayed, but invitation email and acceptance flows are not complete.
- Error tracking shows whether `SENTRY_DSN` is configured, but no external adapter is active.

Provider-ready but not live yet:

- DeepSeek, Gemini, OpenAI, and Anthropic provider names and credential storage exist.
- External generation currently falls back to the safe local provider unless live provider execution is implemented.
- Fine-tuning job tracking is modeled as a readiness path, but real provider fine-tuning calls are not active.
- Stripe configuration is detected, but billing actions still need real Stripe routes.

Production infrastructure still required:

- Strong production secrets.
- Locked CORS origin.
- Persistent storage on Render or a Postgres migration.
- Dedicated background worker service for long-running production jobs.
- Real email delivery for password reset and team invitations.
- Live provider adapters after security review.

## 3. Public Website

The public website is the buyer-facing product surface at `https://techris93.github.io/onboard-ai/`.

Use it to:

- Explain what OnboardAI does.
- Navigate Product, Pricing, Security, Documentation, API, Blog, Changelog, About, Careers, Contact, Legal, Privacy, Terms, DPA, and Subprocessors pages.
- Start an onboarding intake.
- Show the value of AI onboarding, dataset preparation, quality gates, and fine-tuning readiness.
- Link operators into the SaaS dashboard under `/app`.

The public website does not expose:

- Provider secrets.
- Local operator paths.
- Raw internal command traces.
- Private customer documents.
- Database contents.
- Worker-only controls unless a user is authenticated in `/app`.

When using the Start Onboarding flow, enter:

- Company or platform name.
- Industry and company size.
- Main AI use case.
- Readiness stage.
- Integration mode.
- Source categories that should guide the rollout.
- Compliance needs.
- Systems where the AI experience will connect.

The public onboarding flow is useful for scoping and readiness. The authenticated dashboard is where durable jobs, artifacts, dataset batches, and exports live.

## 4. SaaS Dashboard Under `/app`

Open the dashboard at:

```text
https://techris93.github.io/onboard-ai/app
```

If GitHub Pages redirects the route, the fallback sends the page to the hash route automatically.

Sign up:

1. Open `/app`.
2. Choose `Sign up`.
3. Enter your name, email, password, and workspace name.
4. Submit the form.
5. OnboardAI creates your user, session, organization, owner membership, billing record, and default project.

Log in:

1. Open `/app`.
2. Choose `Log in`.
3. Enter the same email and password.
4. Submit the form.

Sessions:

- The frontend stores the session token in browser local storage.
- SaaS API calls send the token as a bearer token.
- Logging out removes the token from local storage.
- Sessions expire server-side based on the configured session lifetime.

Workspace and project meaning:

- A workspace is an organization or customer account.
- A project is a scoped AI rollout inside a workspace.
- Jobs, artifacts, dataset batches, provider keys, usage events, and audit records belong to an organization.

Dashboard panels:

- Metrics show project count, queued jobs, artifact count, and review queue count.
- Start Work queues onboarding jobs and runs one worker job.
- Dataset Generation queues dataset batch jobs.
- Projects creates and lists projects.
- Jobs shows job type, status, and recent result summary.
- Artifacts lists generated outputs.
- Artifact Preview opens and downloads artifact content.
- Dataset Batches shows provider, status, accepted rows, rejected rows, and pass rate.
- Quality Gates shows pass rate, weak labels, and coverage gaps for the latest batch.
- Providers shows local/offline and external provider configuration status.
- Billing shows the active plan, billing adapter status, and usage counters.
- Security shows tenant isolation, secret policy, and rate-limit posture.
- Team shows organization members and roles.
- Monitoring shows health, failed job count, and recent audit events.

## 5. Onboarding Runs

An onboarding run packages company context into a durable delivery artifact set.

Queue an onboarding job:

1. Open `/app`.
2. Sign up or log in.
3. Confirm the active workspace and project.
4. In `Start Work`, enter the company name for the run.
5. Click `Queue onboarding`.
6. The dashboard creates a durable job with status `queued`.

Process the job:

1. Click `Run worker once` from the dashboard, or run the worker command locally.
2. The worker picks the next queued job.
3. The worker runs onboarding logic, readiness packaging, and artifact creation.
4. The job moves to `completed` or `failed`.
5. The dashboard refreshes to show artifacts and job result.

Artifacts can include:

- Normalized intake information.
- Onboarding brief.
- Delivery plan.
- Dataset pipeline plan.
- Readiness summary.
- Publish-safe artifact previews.

Preview and download artifacts:

1. Open the `Artifacts` panel.
2. Select an artifact.
3. Review the content in `Artifact Preview`.
4. Click `Download artifact` if you need a local copy.

Readiness information tells you whether the company is ready for a pilot, what source gaps remain, which specialist roles should be involved, and what should be validated before production.

## 6. Dataset Generation Pipeline

Dataset generation is how OnboardAI turns a scoped company use case into training-ready examples for future expert model work.

Queue a dataset batch:

1. Open `/app`.
2. Go to `Dataset Generation`.
3. Choose a provider.
4. Use `local` for safe offline generation.
5. Enter the number of rows.
6. Click `Queue dataset batch`.
7. Click `Run worker once` or process the job with the worker.

Local/offline generation:

- Works without provider keys.
- Produces deterministic rows for validation and UI workflows.
- Is safe for testing the product loop.
- Is labeled honestly as local/offline generation.

Provider-ready generation:

- DeepSeek, Gemini, OpenAI, and Anthropic appear as external adapter options.
- Provider keys can be stored server-side.
- Live external generation still needs provider-specific execution code before it should be considered active.

Each generated row stores:

- Messages.
- Label.
- Expected behavior.
- Gold reasoning.
- Source trace.
- Quality notes.
- Gate results.
- Accepted or rejected status.
- Rejection reason when applicable.
- Train, validation, or test split.
- Provider.
- Token and cost estimates when available.
- Batch, project, and organization IDs.

Accepted rows are rows that pass all gates. Rejected rows are rows that fail at least one gate and should not be trusted for training until reviewed or regenerated.

Export accepted rows:

1. Complete a dataset batch.
2. Open `Dataset Batches`.
3. Click `Export latest accepted rows`.
4. The browser downloads a JSONL file.

JSONL export is the bridge into future fine-tuning. Each line is a structured training example. Operators should review exports before uploading them to any fine-tuning provider.

## 7. Quality Gates

Quality gates protect the dataset from weak, unsafe, duplicated, or poorly scoped rows.

Current gates:

- Schema validity checks that required fields are present.
- Role correctness checks that message roles are allowed.
- Final user turn quality checks that the final user prompt is specific and question-shaped.
- Allowed labels checks that each row uses the approved label set.
- Canonical order checks that messages follow system-to-user order.
- Duplicate prompt detection checks that a prompt has not already appeared in the batch.
- Placeholder and meta-text detection checks for filler or unfinished row text.
- Target-scope signal checks that the row targets assistant or OnboardAI behavior.
- Helper-scope policy checks that human handoff boundaries are preserved.
- Unsupported-primary policy checks that rows do not reward invented answers.
- Split intent checks that train, validation, and test split values are valid.
- Leakage risk checks for obvious secret or sensitive-data tokens.
- Low-quality or synthetic pattern detection checks for enough lexical variety.
- Gold reason quality checks that gold reasoning is meaningful.
- Train/test leakage checks that evaluation data does not leak training intent.
- Company-data privacy checks that source traces avoid private customer data markers.
- Evaluation coverage checks that labels contribute to coverage accounting.

Pass rate:

- Pass rate is the accepted row count divided by total generated rows.
- A 100 percent pass rate means every row passed the current gate set.
- A lower pass rate is not automatically bad if the rejects reveal useful improvements.

Rejection reasons:

- Use rejection reasons to improve generator specs.
- Repeated rejection reasons show where the generator or source scope is weak.
- Rejected rows should be archived, not hidden, because they explain what the next batch must avoid.

Weak labels and coverage gaps:

- Weak labels show labels that have too little support in the current batch.
- Coverage gaps show labels missing from the current batch.
- Use both signals to plan the next batch.

## 8. Worker Mode

OnboardAI uses jobs so long-running AI work does not depend on one browser request staying open.

Job statuses:

- `queued` means the job is waiting for a worker.
- `running` means a worker is processing the job.
- `completed` means the job finished and stored results.
- `failed` means the job exhausted the current execution attempt and stored an error.
- `needs_review` is reserved for jobs that require human approval.

Run the worker locally:

```bash
python saas_worker.py --once --limit 1
```

Run the worker continuously for local operations:

```bash
python saas_worker.py --limit 1 --interval 5
```

Trigger one job from the dashboard:

1. Open `/app`.
2. Queue an onboarding or dataset batch job.
3. Click `Run worker once`.
4. Refresh or wait for the dashboard to reload.

Production worker recommendation:

- Run the API as one Render web service.
- Run `saas_worker.py` as a separate private worker service.
- Keep worker secrets out of the frontend.
- Use `/api/worker/run-once` only for private operational automation.
- Use dashboard `Run worker once` for admin/operator convenience, not as the final production scaling model.

## 9. Provider Settings

Provider settings live in the `/app` dashboard under `Providers`.

Provider key rules:

- Keys are submitted to the backend only.
- Keys are hashed and masked server-side.
- Raw secrets are never returned to the frontend.
- Local/offline mode does not need a provider key.
- Provider keys should never be committed to the repo.
- Provider keys should never be placed in GitHub Pages or frontend code.

Provider status:

- `local` is always configured and runs offline.
- `deepseek`, `gemini`, `openai`, and `anthropic` are external adapter options.
- Saving a key marks an external provider as configured.
- Live generation still requires provider-specific execution implementation.

Use external providers only after:

- Local/offline workflow is proven.
- Sources and labels are approved.
- Quality gates are passing.
- The organization has approved provider data handling.
- Provider costs and rate limits are understood.

## 10. Billing And Usage

Current billing foundation:

- Starter plan covers onboarding, planning, and artifact exports.
- Growth plan covers dataset generation, quality gates, and evaluation loops.
- Enterprise plan covers private deployment, custom providers, human review, and fine-tuning support.

Usage tracking currently records:

- Onboarding runs.
- Generated rows.
- Accepted rows.
- Provider-related batch usage.
- Job and artifact activity through audit events.

Mock/local billing today:

- The dashboard shows billing status and usage.
- Stripe detection is based on whether `STRIPE_SECRET_KEY` is configured.
- Real checkout, customer portal, invoices, and plan enforcement still need Stripe routes.

Production billing flow should include:

- Stripe customer creation.
- Checkout sessions.
- Customer portal.
- Plan limits.
- Usage metering.
- Invoice history.
- Billing audit events.

## 11. Security And Compliance

Tenant isolation:

- SaaS routes require bearer-token authentication.
- Organization access is checked through memberships.
- Role checks protect project creation, provider keys, API keys, jobs, and row review.

Roles:

- `owner` can manage the workspace and sensitive configuration.
- `admin` can manage most workspace operations.
- `operator` can run onboarding and dataset work.
- `viewer` is intended for read-oriented access.

Secrets:

- Provider keys are hashed and masked.
- API keys are displayed once at creation.
- Environment secrets belong in Render or local private environment files.
- `.env` is a local/private operator file and should not be committed.

CORS:

- `ONBOARDAI_ALLOWED_ORIGIN` controls which frontend origin can call the backend.
- Production should lock this to `https://techris93.github.io`.
- Local development can use local origins.

Before real customers use the product:

- Set strong production secrets.
- Move SQLite to persistent storage or migrate to Postgres.
- Add backups.
- Add real email delivery.
- Add dedicated worker service.
- Review provider data handling.
- Enable rate limiting at the gateway or service layer.
- Finalize privacy, terms, DPA, retention, deletion, and subprocessor policies.

## 12. Deployment

Current deployment model:

- GitHub Pages hosts the frontend.
- Render hosts the backend API.
- The frontend is built with `VITE_API_BASE_URL` pointing to the backend.
- The deployed backend is `https://onboard-ai-backend-u5af.onrender.com`.
- The deployed frontend is `https://techris93.github.io/onboard-ai/`.

Required production backend environment:

- `ONBOARDAI_ENV=production`
- `ONBOARDAI_SECRET_KEY` set to a strong random value.
- `ONBOARDAI_ALLOWED_ORIGIN=https://techris93.github.io`
- `ONBOARDAI_WORKER_TOKEN` set to a different strong random value if worker endpoint protection is used.
- Provider keys only when external providers are enabled.
- `STRIPE_SECRET_KEY` only when Stripe billing is enabled.
- `SENTRY_DSN` only when error tracking is enabled.
- `ONBOARDAI_DB_PATH` pointing to persistent disk if SQLite is used on Render.

Frontend deployment verification:

1. Open `https://techris93.github.io/onboard-ai/`.
2. Confirm the homepage loads.
3. Open `https://techris93.github.io/onboard-ai/app`.
4. Confirm the dashboard route loads.
5. Sign up or log in.

Backend deployment verification:

1. Open `https://onboard-ai-backend-u5af.onrender.com/api/deployment/health`.
2. Confirm `status` is `ok`.
3. Confirm `environment` is `production` after production env vars are set.
4. Confirm `databasePath` reports `configured`.
5. Confirm provider names are present.
6. Confirm billing adapter reports `mock` unless Stripe is configured.

## 13. API Usage

Use the API from trusted app code, internal tools, or operator scripts. Do not expose secrets in frontend code.

Auth:

- `POST /api/auth/signup` creates a user, workspace, owner membership, session, billing record, and default project.
- `POST /api/auth/login` creates a session for an existing user.
- `POST /api/auth/logout` ends the current session.
- `POST /api/auth/password-reset` creates a reset token, but email delivery is not active yet.

Dashboard:

- `GET /api/app/dashboard` returns the authenticated workspace summary.

Projects:

- `POST /api/app/projects` creates a project in the active organization.

Jobs:

- `POST /api/app/onboarding-jobs` queues an onboarding run.
- `POST /api/app/dataset-batches` queues a dataset batch.
- `POST /api/app/jobs/run-next` runs one organization-scoped job for the authenticated operator.
- `GET /api/app/jobs/<job_id>` returns one job.

Artifacts:

- `GET /api/app/artifacts/<artifact_id>` returns artifact metadata and content for the authorized organization.

Dataset batches:

- `GET /api/app/dataset-batches/<batch_id>/export` returns accepted rows as JSONL content.
- `POST /api/app/reviews/rows/<row_id>` accepts or rejects a row.

Provider keys:

- `POST /api/app/provider-keys` stores a hashed and masked external provider secret.

API keys:

- `POST /api/app/api-keys` creates a one-time API key secret.

Health checks:

- `GET /api/health` checks the legacy API health.
- `GET /api/deployment/health` checks SaaS runtime health.

Worker-only operations:

- `POST /api/worker/run-once` runs queued work globally and should be protected with `X-Worker-Token` when `ONBOARDAI_WORKER_TOKEN` is set.

Compatibility routes:

- `POST /api/onboarding` runs the original synchronous onboarding endpoint.
- `POST /api/dataset-pipeline/plan` runs dataset pipeline planning.
- `POST /api/research/evaluate` runs research evaluation.

## 14. Troubleshooting

Cannot log in:

- Confirm the backend is reachable.
- Confirm the account exists.
- Try signing up with a new email if this is a fresh database.
- Confirm the browser has not stored an expired token; log out and sign in again.

Dashboard cannot reach backend:

- Confirm the frontend bundle was built with the correct `VITE_API_BASE_URL`.
- Confirm the backend URL is online.
- Confirm CORS allows the GitHub Pages origin.

GitHub Pages loads but `/app` fails:

- Confirm `app/public/404.html` exists in the build.
- Open `https://techris93.github.io/onboard-ai/#/app` as a fallback.
- Redeploy GitHub Pages if the latest build did not publish.

Render backend not updated:

- Check the latest Render deploy.
- Trigger a manual deploy from the Render dashboard.
- Confirm the GitHub repository pushed the latest commit.

Worker does not process jobs:

- Confirm jobs are queued.
- Click `Run worker once`.
- Run `python saas_worker.py --once --limit 1` locally against the intended database.
- In production, confirm the worker service uses the same persistent database as the API.

Provider key not working:

- Confirm the key was saved for an external provider, not `local`.
- Confirm the dashboard marks the provider as configured.
- Remember that live external provider generation still needs provider execution implementation.

Dataset export is empty:

- Confirm a dataset batch completed.
- Confirm accepted row count is greater than zero.
- Review quality gate failures if rows were rejected.

CORS error:

- Set `ONBOARDAI_ALLOWED_ORIGIN=https://techris93.github.io` in production.
- Redeploy the backend.
- Confirm browser requests are going to the Render backend.

Missing environment variables:

- Add them in Render under the backend service environment settings.
- Redeploy after saving.
- Check `/api/deployment/health`.

Rate-limited AI provider:

- Use local/offline generation for validation.
- Reduce batch size.
- Add retry/backoff in the provider adapter before live provider rollout.

## 15. Recommended Daily Workflow

1. Open `/app`.
2. Sign up or log in.
3. Confirm the workspace and project.
4. Create a project if the customer or rollout is new.
5. Enter the company name in `Start Work`.
6. Queue onboarding.
7. Run the worker once or let the production worker process the job.
8. Review generated artifacts.
9. Download the artifacts needed for the delivery team.
10. Queue a small local/offline dataset batch.
11. Run the worker again.
12. Review pass rate, weak labels, and coverage gaps.
13. Export accepted rows.
14. Improve the next batch based on rejection reasons and coverage gaps.
15. Configure external provider keys only after the local workflow is proven.
16. Move to provider generation and fine-tuning readiness only after data quality is reliable.

## 16. Limitations And Next Steps

Production-ready now:

- Public website.
- Authenticated dashboard.
- SQLite persistence.
- Local/offline dataset generation.
- Quality gates.
- Artifact preview and export.
- Job queue foundation.
- Provider-key masking.
- Usage and audit foundations.

Needs production setup:

- Strong Render secrets.
- Production CORS.
- Persistent disk or Postgres migration.
- Dedicated worker service.
- Backups.

Needs external credentials:

- Gemini, DeepSeek, OpenAI, Anthropic, or other provider keys for future live provider work.
- Stripe key for real billing.
- Sentry DSN for external error tracking.
- Email provider credentials for password reset and invitations.

Needs implementation before claiming full production coverage:

- Live provider generation adapters.
- Real fine-tuning job submission.
- Stripe checkout and customer portal.
- Password reset email delivery.
- Team invitation acceptance flow.
- Postgres adapter and migrations.
- Human review queue UI beyond the current row review endpoint foundation.

