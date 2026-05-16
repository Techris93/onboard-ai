# OnboardAI Production SaaS Foundation

OnboardAI now has a production SaaS foundation layered on top of the existing
public site and backend planner. The foundation is intentionally dependency-light
so it can keep deploying on Render while still adding the durable primitives a
real SaaS needs.

## What Is Functional

- User sign up, login, logout-ready session storage, and password-reset token creation.
- Organizations, memberships, roles, and projects.
- SQLite persistence for local and Render deployments.
- Durable jobs with `queued`, `running`, `completed`, `failed`, and `needs_review` statuses.
- Worker execution through `saas_worker.py` or `/api/worker/run-once`.
- Dashboard route under `/app`.
- Onboarding jobs that store runs and artifacts.
- Dataset batch jobs with local/offline row generation.
- Quality gates saved per row.
- Accepted/rejected dataset row storage.
- JSONL export for accepted rows.
- Artifact preview and download from the dashboard.
- Provider adapter contract with local/offline execution and external-provider placeholders.
- Provider key storage that hashes and masks secrets server-side.
- Billing foundations with Starter, Growth, and Enterprise plans.
- Usage tracking for jobs, generated rows, accepted rows, and onboarding runs.
- Audit logs for sensitive actions.
- API key generation with one-time secret display.
- Public pages for Product, Pricing, Security, Docs, API, Blog, Changelog, About, Careers, Contact, Legal, Privacy, Terms, DPA, and Subprocessors.

## What Is Local Or Mocked

- Billing uses a mock adapter until `STRIPE_SECRET_KEY` and Stripe routes are enabled.
- DeepSeek, Gemini, OpenAI, and Anthropic dataset generation use the provider adapter contract but fall back to safe local generation unless live execution is explicitly implemented.
- Password reset creates a token; email delivery is not wired yet.
- Team invitation storage exists, but email sending and invite acceptance UI are not complete.
- Fine-tuning integration is modeled for readiness and export; real fine-tuning API calls are not enabled yet.

## Environment Variables

```bash
ONBOARDAI_ENV=local
ONBOARDAI_SECRET_KEY=replace_with_a_long_random_secret
ONBOARDAI_DB_PATH=state/onboardai.sqlite3
ONBOARDAI_ALLOWED_ORIGIN=http://127.0.0.1:3000
ONBOARDAI_WORKER_TOKEN=replace_with_worker_token
STRIPE_SECRET_KEY=
SENTRY_DSN=
GEMINI_API_KEY=
LLM_KB_ROOT=state/llm_kb_workspace
LLM_KB_BIN=/path/to/llm-kb
```

Production should set:

- `ONBOARDAI_ENV=production`
- a strong `ONBOARDAI_SECRET_KEY`
- a locked `ONBOARDAI_ALLOWED_ORIGIN`
- a private `ONBOARDAI_WORKER_TOKEN`
- a persistent database/storage strategy

## Local Development

Start the backend:

```bash
python backend_api.py --host 127.0.0.1 --port 8787
```

Start the frontend:

```bash
cd app
VITE_API_BASE_URL=http://127.0.0.1:8787 npm run dev
```

Open:

```text
http://127.0.0.1:3000/app
```

Run the worker once:

```bash
python saas_worker.py --once --limit 1
```

Or from the dashboard, click `Run worker once`.

## Core API Routes

Auth:

- `POST /api/auth/signup`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `POST /api/auth/password-reset`

Dashboard:

- `GET /api/app/dashboard`
- `POST /api/app/projects`
- `POST /api/app/onboarding-jobs`
- `POST /api/app/dataset-batches`
- `POST /api/app/jobs/run-next`
- `GET /api/app/jobs/<job_id>`
- `GET /api/app/artifacts/<artifact_id>`
- `GET /api/app/dataset-batches/<batch_id>/export`
- `POST /api/app/provider-keys`
- `POST /api/app/api-keys`
- `POST /api/app/reviews/rows/<row_id>`

Operations:

- `GET /api/deployment/health`
- `POST /api/worker/run-once`

Compatibility routes remain available:

- `POST /api/onboarding`
- `POST /api/dataset-pipeline/plan`
- `POST /api/research/evaluate`

## Database Model

SQLite tables include:

- `users`
- `sessions`
- `organizations`
- `memberships`
- `projects`
- `jobs`
- `onboarding_runs`
- `dataset_pipelines`
- `dataset_batches`
- `dataset_rows`
- `quality_gate_results`
- `artifacts`
- `agent_runs`
- `evaluations`
- `provider_keys`
- `api_keys`
- `audit_logs`
- `usage_events`
- `billing_customers`
- `invitations`
- `notifications`

The schema uses plain SQL in `saas_runtime.py`, which keeps the migration path
to Postgres straightforward. For Postgres, replace the connection layer, move
schema migrations into a dedicated migration tool, and keep the table boundaries.

## Render Notes

The existing web service can keep running `backend_api.py`. For production-grade
job execution, add a second Render worker service using:

```bash
python saas_worker.py --limit 1 --interval 5
```

If you do not add a worker service yet, jobs can still be processed manually
from the dashboard through `Run worker once`.

## Security Notes

- SaaS routes require bearer-token authentication.
- Organization access is checked through memberships.
- Role checks protect project creation, provider keys, API keys, jobs, and row review.
- Provider secrets are hashed and masked; raw secrets are never returned.
- API keys are shown once at creation.
- Audit logs capture sensitive operations.
- CORS should be locked in production with `ONBOARDAI_ALLOWED_ORIGIN`.

## Next Production Steps

1. Move SQLite to managed Postgres for durable multi-instance deployments.
2. Add a dedicated Render worker service.
3. Add real Stripe checkout and customer portal routes.
4. Implement live provider adapters for DeepSeek, Gemini, OpenAI, and Anthropic.
5. Add email delivery for password reset and team invitations.
6. Add real fine-tuning job submission only after generated datasets pass review.
