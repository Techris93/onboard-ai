# Render Production Environment Guide

This guide explains how to configure the OnboardAI Render backend for production. It covers required environment variables, strong secret generation, CORS, worker protection, SQLite persistent disk setup, and the Postgres migration path.

Current deployment:

- Backend service: `https://onboard-ai-backend-u5af.onrender.com`
- Frontend origin: `https://techris93.github.io`
- GitHub Pages frontend: `https://techris93.github.io/onboard-ai/`
- Backend start command: `python backend_api.py --host 0.0.0.0 --port $PORT`

Official Render references:

- Environment variables: `https://render.com/docs/configure-environment-variables`
- Persistent disks: `https://render.com/docs/disks`
- Render Postgres: `https://render.com/docs/postgresql-creating-connecting`

## 1. Why These Settings Matter

`ONBOARDAI_ENV=production` tells the backend to use production behavior. It disables the development seed route and makes the default CORS fallback use the GitHub Pages origin instead of allowing every origin.

`ONBOARDAI_SECRET_KEY` is used by the backend to hash and sign sensitive auth-related values, including password and session material. The local fallback value is only for development and must not be used for production.

`ONBOARDAI_ALLOWED_ORIGIN=https://techris93.github.io` locks browser access to the GitHub Pages frontend origin. This prevents other browser origins from calling the backend through normal CORS-enabled frontend requests.

`ONBOARDAI_WORKER_TOKEN` protects the worker-only endpoint `/api/worker/run-once` when it is set. A private worker process should send it through the `X-Worker-Token` header.

Persistent storage or Postgres prevents data loss between deploys and restarts. Without persistent storage, SQLite data written inside the application filesystem can disappear when Render rebuilds or replaces the service instance.

## 2. Generate Strong Secrets

Generate two different secrets locally. One secret is for `ONBOARDAI_SECRET_KEY`; the other is for `ONBOARDAI_WORKER_TOKEN`.

Option A:

```bash
openssl rand -hex 32
```

Option B:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

Rules:

- Use a different value for `ONBOARDAI_SECRET_KEY` and `ONBOARDAI_WORKER_TOKEN`.
- Never commit either value.
- Never paste either value into frontend code.
- Never expose either value in GitHub Pages.
- Store them only in Render environment variables and a secure password manager.
- Rotate the value if it is accidentally shared.

## 3. Set Environment Variables In Render Dashboard

1. Open `https://dashboard.render.com`.
2. Select the OnboardAI backend service.
3. Open the `Environment` tab.
4. Add or update each variable below.
5. Save changes.
6. Trigger a manual redeploy if Render does not redeploy automatically.

Required variables:

| Key | Value |
| --- | --- |
| `ONBOARDAI_ENV` | `production` |
| `ONBOARDAI_ALLOWED_ORIGIN` | `https://techris93.github.io` |
| `ONBOARDAI_SECRET_KEY` | A generated secret from Section 2 |

Recommended worker variable:

| Key | Value |
| --- | --- |
| `ONBOARDAI_WORKER_TOKEN` | A different generated secret from Section 2 |

Recommended optional variables:

| Key | When to set it |
| --- | --- |
| `ONBOARDAI_DB_PATH` | Set when using SQLite on a Render persistent disk |
| `STRIPE_SECRET_KEY` | Set only when real Stripe billing routes are implemented |
| `SENTRY_DSN` | Set only when external error tracking is enabled |
| `GEMINI_API_KEY` | Set only when Gemini-backed evaluation or provider work is enabled |
| `LLM_KB_ROOT` | Set when you need a writable llm-kb workspace |
| `LLM_KB_BIN` | Set only if a custom `llm-kb` executable exists in the runtime image |
| `INSTALL_LLM_KB` | Set to `true` only if Render should install the public llm-kb package during build |

## 4. Persistent Storage Option For SQLite

SQLite is the immediate supported database path in the current code. For an early pilot, use a Render persistent disk and point SQLite at that disk.

Render dashboard steps:

1. Open the OnboardAI backend service in Render.
2. Open service settings.
3. Add a persistent disk if the selected service plan supports disks.
4. Choose a mount path such as `/var/data`.
5. Save the disk configuration.
6. Open the `Environment` tab.
7. Set `ONBOARDAI_DB_PATH=/var/data/onboardai.sqlite3`.
8. Redeploy the backend service.
9. Open `/api/deployment/health` and confirm `databasePath` reports `configured`.

Important SQLite notes:

- SQLite plus persistent disk is acceptable for an early pilot.
- It is not ideal for high-concurrency SaaS.
- If `ONBOARDAI_DB_PATH` points to the application filesystem instead of the disk mount, data may be lost on redeploy.
- Persistent disk availability depends on the Render service type and plan.
- Backups remain your responsibility unless you add a managed backup workflow.
- Scaling a service with a local disk requires extra care because one mounted disk is not the same as a shared multi-instance database.

## 5. Postgres Option

Postgres is the recommended long-term production database. The current OnboardAI code uses SQLite directly through `saas_runtime.py`; it does not currently read `DATABASE_URL` or run Postgres migrations. Do not set `DATABASE_URL` and assume the app is using Postgres until the data layer is implemented and tested.

Render Postgres setup path:

1. Open Render Dashboard.
2. Create a new Render Postgres database.
3. Put it in the same region as the backend service.
4. Copy the internal database URL.
5. Add `DATABASE_URL` to the backend service only after the OnboardAI backend supports it.
6. Redeploy the backend.
7. Run migration tests before using it for customers.

Recommended migration plan:

1. Keep SQLite on a persistent disk for the pilot.
2. Add a Postgres-compatible data layer, such as SQLAlchemy or a small repository abstraction.
3. Move schema creation out of direct SQLite calls and into migrations.
4. Create migrations for users, organizations, memberships, projects, jobs, onboarding runs, dataset pipelines, dataset batches, dataset rows, quality gate results, artifacts, provider keys, API keys, audit logs, usage events, billing customers, invitations, and notifications.
5. Test signup, login, dashboard loading, project creation, onboarding jobs, dataset jobs, worker processing, artifact retrieval, dataset export, provider keys, API keys, billing usage, and audit logs.
6. Run a temporary import from SQLite to Postgres if pilot data must be preserved.
7. Switch production to Postgres only after tests pass.

Current accuracy statement:

- SQLite is supported today.
- SQLite on a Render persistent disk is the immediate durable Render option.
- Postgres is documented as the recommended migration path, not as an active runtime in the current code.

## 6. Worker Protection

There are two worker paths:

- `/api/app/jobs/run-next` is an authenticated dashboard endpoint that processes one job for the signed-in operator's organization.
- `/api/worker/run-once` is a worker-only operational endpoint that can process queued jobs globally.

When `ONBOARDAI_WORKER_TOKEN` is set, `/api/worker/run-once` requires:

```text
X-Worker-Token: your_worker_token
```

Do not expose the worker token to GitHub Pages. It belongs only in Render environment variables, private worker service configuration, or secure operator automation.

Production recommendation:

- Keep the web API as one Render service.
- Add a separate worker service that runs `python saas_worker.py --limit 1 --interval 5`.
- Give the worker service the same database configuration as the API service.
- Use the dashboard `Run worker once` button for operator convenience, not final production scaling.
- Use the worker-only endpoint only from private automation when token protection is enabled.

## 7. Redeploy And Verify

After saving env vars, redeploy the backend.

Backend health check:

1. Open `https://onboard-ai-backend-u5af.onrender.com/api/deployment/health`.
2. Confirm `status` is `ok`.
3. Confirm `environment` is `production`.
4. Confirm `databasePath` reports `configured`.
5. Confirm providers include `local`, `deepseek`, `gemini`, `openai`, and `anthropic`.
6. Confirm billing adapter reports `mock` unless Stripe is intentionally enabled.

Frontend check:

1. Open `https://techris93.github.io/onboard-ai/`.
2. Open `https://techris93.github.io/onboard-ai/app`.
3. Sign up or log in.
4. Queue a small local/offline dataset batch.
5. Run a worker job from the dashboard or confirm the production worker service processes it.
6. Confirm the job completes.
7. Export accepted rows.
8. Confirm no secrets are returned in dashboard or API responses.

If the health endpoint still reports `local`, Render has not received or applied `ONBOARDAI_ENV=production`.

## 8. Troubleshooting

Backend still says environment is local:

- Confirm `ONBOARDAI_ENV` is set on the backend service, not the static frontend.
- Confirm the value is exactly `production`.
- Redeploy the backend after saving.

CORS error from GitHub Pages:

- Confirm `ONBOARDAI_ALLOWED_ORIGIN=https://techris93.github.io`.
- Confirm the browser is using `https://techris93.github.io/onboard-ai/`.
- Confirm the frontend bundle points to `https://onboard-ai-backend-u5af.onrender.com`.
- Redeploy the backend.

Dashboard cannot reach backend:

- Confirm the backend service is live.
- Confirm the frontend was built with `VITE_API_BASE_URL` pointing to the Render backend.
- Confirm the backend health endpoint returns JSON.

Data disappears after redeploy:

- Confirm `ONBOARDAI_DB_PATH` points to a persistent disk mount.
- Confirm the disk is attached to the backend service.
- Confirm the backend was redeployed after the disk and env var were added.

Worker endpoint returns unauthorized:

- Confirm `ONBOARDAI_WORKER_TOKEN` is set.
- Confirm private automation sends `X-Worker-Token`.
- Confirm no extra spaces were copied into the token value.

Secret was accidentally exposed:

- Rotate the exposed secret immediately.
- Update it in Render.
- Redeploy.
- Log out old sessions if session integrity may be affected.

Postgres database URL added but app still uses SQLite:

- That is expected with the current code.
- The backend does not currently read `DATABASE_URL`.
- Implement the Postgres data layer and migrations before relying on Postgres.

Render did not redeploy after env changes:

- Trigger a manual deploy from the service page.
- Check deploy logs for build or startup failures.
- Reopen `/api/deployment/health` after the deploy is live.

## 9. Recommended Production Configuration

Use this checklist before customer use:

- `ONBOARDAI_ENV=production`
- `ONBOARDAI_ALLOWED_ORIGIN=https://techris93.github.io`
- Strong `ONBOARDAI_SECRET_KEY`
- Strong `ONBOARDAI_WORKER_TOKEN`
- `ONBOARDAI_DB_PATH=/var/data/onboardai.sqlite3` with a Render persistent disk
- Provider keys stored only on the backend
- Stripe key set only when real billing is enabled
- Sentry DSN set only when error tracking is enabled
- Regular backups enabled
- Dedicated worker service configured
- Production privacy, terms, DPA, retention, deletion, and subprocessor policies reviewed

## 10. Current Postgres Status

Postgres is not active in the current backend. The current runtime creates and uses SQLite tables directly. Treat Postgres as the next production migration, not a setting that can be turned on by adding `DATABASE_URL`.

The safe path is:

1. Use SQLite with a persistent Render disk for the pilot.
2. Build the Postgres adapter and migrations.
3. Test all SaaS flows against Postgres.
4. Migrate data if needed.
5. Switch production after verification.

