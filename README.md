<p align="center">
  <h1 align="center">🧠 OnboardAI</h1>
  <p align="center"><strong>AI Onboarding, Dataset Preparation, and Expert Model Readiness</strong></p>
  <p align="center">Turn company knowledge into governed AI rollout plans, fine-tuning dataset pipelines, and delivery-ready artifacts.</p>
</p>

---

## What It Does

OnboardAI helps small and mid-sized companies prepare customized AI systems with structured onboarding, knowledge operations, specialist-agent routing, evaluation loops, and fine-tuning dataset planning for smaller expert language models.

The product focuses on three connected workflows:
- Company AI onboarding for support, internal copilots, product/API assistants, sales enablement, and operations.
- Fine-tuning dataset generation with Codex-authored specs, provider-neutral generator execution, quality gates, rejected-row tracking, and batch improvement reports.
- Operational readiness for security, governance, deployment, support, and public-source validation before private client data is imported.

## SaaS Foundation

OnboardAI now includes a production SaaS foundation in addition to the public
marketing site:

- `/app` authenticated dashboard
- SQLite-backed users, sessions, organizations, memberships, projects, jobs, artifacts, dataset pipelines, dataset batches, dataset rows, quality gates, usage events, billing customers, provider keys, API keys, and audit logs
- durable job queue with a worker command
- local/offline dataset row generation
- quality gate execution and accepted-row JSONL export
- mock billing and provider adapter interfaces ready for Stripe and external model providers
- public pages for product, pricing, security, docs, API, blog, changelog, legal, privacy, terms, DPA, and subprocessors

See [`PRODUCTION_SAAS.md`](PRODUCTION_SAAS.md) for setup, environment, worker,
security, and production migration details.

Operator guides:
- [`USER_GUIDE.md`](USER_GUIDE.md) explains how to use every current public site, dashboard, worker, dataset, quality gate, artifact, provider, billing, API, and deployment feature.
- [`RENDER_ENV_GUIDE.md`](RENDER_ENV_GUIDE.md) explains how to configure Render production environment variables, strong secrets, CORS, worker protection, persistent SQLite storage, and the Postgres migration path.

## Quick Start

```bash
# 1. Install
pip install -r requirements.txt

# 2. Set your Gemini API key
cp .env.example .env
# Edit .env → add GEMINI_API_KEY

# 3. Prepare local evaluation data or import company documents
python prepare.py

# 4. Run baseline evaluation
python evaluate.py --verbose

# or run fully offline without Gemini
python evaluate.py --provider local --verbose

# 5. Point your AI agent at program.md to start optimizing
```

`evaluate.py` retries transient Gemini `429` and `503` failures with
backoff, so benchmark runs are less likely to fail on short-lived API issues.
It also supports `--provider local` for a model-free offline benchmark path.

## Fine-Tuning Dataset Pipeline

OnboardAI includes a deterministic dataset pipeline planner that can run without provider keys. It produces a company-specific plan covering:
- Codex orchestration for goals, use-case specs, schemas, labels, prompts, quality gates, rejects, reports, and worklog.
- Generator contracts for low-cost providers such as DeepSeek v4 Pro or any compatible model execution layer.
- Raw batch archive policy for accepted rows, rejected rows, quality notes, gold reasoning, and traceability metadata.
- Quality gates for schema validity, role correctness, allowed labels, canonical order, duplicate prompts, placeholder text, target-scope signal, helper-scope policy, unsupported-primary policy, split intent, leakage risk, synthetic pattern detection, gold reason quality, train/test leakage, company-data privacy, and evaluation coverage.
- Iterative improvement after every batch so the next generator spec and gate set become stronger.

The backend writes dataset pipeline markdown and JSON artifacts during onboarding runs.

## Private Public-Data Validation

Use the private validation runner when you want to onboard a public company for
testing without writing that external validation data into the repo's tracked
`data/` files or the website.

```bash
python validate_public_company.py \
  --business-name "Acme Cloud" \
  --url https://acme.com \
  --url https://acme.com/docs \
  --url https://acme.com/pricing \
  --provider local \
  --num-qa 12 \
  --verbose-eval
```

Notes:
- The runner copies the Python harness into an isolated temp workspace.
- `--provider local` is the default, so you can run a full benchmark without Gemini.
- Use `--depth` and `--max-pages` only when you want the scraper to crawl beyond the exact URLs you listed.
- Use `--cleanup` if you want the temp workspace deleted after a successful run.

## Backend Worker

The repo includes a real onboarding API:

```bash
python backend_api.py --host 127.0.0.1 --port 8787
```

Available routes:
- `GET /api/health`
- `GET /api/deployment/health`
- `GET /api/app/dashboard`
- `GET /api/runs/<run_id>`
- `GET /api/dataset-pipeline/runs/<run_id>`
- `GET /api/app/jobs/<job_id>`
- `GET /api/app/artifacts/<artifact_id>`
- `POST /api/onboarding`
- `POST /api/dataset-pipeline/plan`
- `POST /api/auth/signup`
- `POST /api/auth/login`
- `POST /api/app/onboarding-jobs`
- `POST /api/app/dataset-batches`
- `POST /api/app/jobs/run-next`

What the worker does:
- stores each onboarding run locally under `state/onboarding_api/`
- stores SaaS state in SQLite at `state/onboardai.sqlite3` unless `ONBOARDAI_DB_PATH` is set
- creates a writable llm-kb workspace under `state/llm_kb_workspace/` unless `LLM_KB_ROOT` is set
- writes a normalized intake packet, onboarding brief, and fine-tuning dataset pipeline plan
- uses `llm-kb` for source preparation, knowledge compilation, agent recommendation, activation brief creation, filing, and publish-safe artifact generation when it is installed locally
- returns the stored run, command summaries, warnings, and artifact previews to the website

Run the SaaS worker locally:

```bash
python saas_worker.py --once --limit 1
```

## Adaptive Onboarding Paths

OnboardAI treats onboarding as an adaptive workflow. Each completed or stalled
path updates local outcome memory so the next user can be routed with better
timing, confidence, and context.

Implemented capabilities:
- **Confusion detection** identifies risk early and recommends intervention.
- **Path confidence memory** strengthens successful routes and ages out stale ones.
- **Knowledge routing** sends the right docs, tasks, and agent roles to the person who needs them.
- **Team alignment** keeps onboarding owners synced through lightweight signals.
- **Friction simulation** identifies where a user is likely to get stuck before the real handoff.
- **Progressive access** unlocks tools and features in safer layers.
- **Timing optimization** recommends guidance moments based on receptivity.
- **Priority routing** emphasizes the onboarding steps that matter most for the role.
- **Micro-checks** ask short questions to locate confusion quickly.
- **Tone adaptation** adjusts training style to role, confidence, and motivation.

How to use it:
1. Open the frontend and start an onboarding run.
2. Complete the company profile, source selection, integration mode, and role context.
3. Review the **Adaptive Path Signals** panel for path confidence, confusion risk, and the next best action.
4. Click **Mark successful** when a path worked or **Mark stuck** when the user stalled. Those signals update the local path memory for future recommendations.

## Frontend To Backend Wiring

The onboarding form in `app/` can POST directly to the backend worker.

Local development:

```bash
python backend_api.py --host 127.0.0.1 --port 8787
cd app
VITE_API_BASE_URL=http://127.0.0.1:8787 npm run dev
```

Deployment options:
- Same-origin deployment: serve the frontend and backend behind one domain and let the app use `/api/onboarding`.
- Configured API deployment: build the frontend with `VITE_API_BASE_URL=https://your-api.example.com`.
- Runtime injection: set `window.__ONBOARDAI_API_BASE_URL__` before the app boots if you need to swap API targets without rebuilding.

### Render

The checked-in `render.yaml` and `scripts/render_build.sh` install this repo's declared Python and frontend dependencies, then build the Vite app. The public `llm-knowledge-base` repository can be installed during Render builds without GitHub credentials. The backend treats the `llm-kb` binary as optional via `LLM_KB_BIN`, which keeps deploys healthy even when `llm-kb` is not installed in the image.

Recommended Render setup:
- Use the checked-in `render.yaml` Blueprint.
- Set `VITE_API_BASE_URL` on the static site to the backend service URL when the services are split.
- Set `INSTALL_LLM_KB=true` if you want Render to install the public `Techris93/llm-knowledge-base` repo during the build.
- Set `LLM_KB_BIN` only if you provide a custom `llm-kb` executable path in the runtime image.
- Keep `LLM_KB_ROOT=/opt/render/project/src/state/llm_kb_workspace` for a writable knowledge workspace.

## Frontend

The React/Vite public site lives in `app/`. It presents OnboardAI as a product
surface for AI onboarding, fine-tuning dataset readiness, grouped navigation,
and backend-powered artifact generation.

```bash
cd app
npm install
npm run dev
```

The frontend is intentionally separate from the Python backend:
- Root Python files drive data prep, config tuning, dataset planning, and evaluation.
- `app/` presents the public product experience and submits approved intakes to the backend worker.
- `app/` also contains the authenticated SaaS dashboard under `/app`.

## How It Works

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  prepare.py  │────▶│  config.py   │────▶│ evaluate.py  │
│  Load data   │     │  AI config   │     │  Score it    │
│  (your biz)  │     │  (agent      │     │  (0-100)     │
│              │     │   edits)     │     │              │
└──────────────┘     └──────┬───────┘     └──────┬───────┘
                            │                     │
                            ◀─────────────────────┘
                            improved? commit : try again
```

## For Your Business

### Option A: Import documents
```bash
# Drop .txt or .md files into a folder and import
python prepare.py --import-docs path/to/your/docs/
```

### Option B: Edit directly
Edit `data/knowledge.json` with your business info and `data/test_qa.json` with real customer questions.

## Scoring

| Component | Max | Measures |
|-----------|-----|----------|
| Accuracy | 50 | Key facts in answers |
| Quality | 30 | Structure & length |
| Coverage | 20 | % of questions passed |

## Use Cases

| Business | Knowledge | Test Questions |
|----------|-----------|---------------|
| Coffee shop | Menu, hours, policies | "How much is a latte?" |
| Law firm | Case procedures, fees | "How long does filing take?" |
| SaaS company | Features, pricing, docs | "Can I export to CSV?" |
| Hospital | Services, insurance, hours | "Do you accept Medicare?" |
| Real estate | Listings, processes, fees | "What's the commission?" |

## Project Structure

```
prepare.py            — Import or generate local business knowledge
config.py             — Assistant configuration and retrieval behavior
evaluate.py           — Scoring engine with retry-aware Gemini and local evaluation
dataset_pipeline.py   — Fine-tuning dataset pipeline planning and artifacts
backend_runtime.py    — Run storage, llm-kb orchestration, and artifact packaging
backend_api.py        — HTTP API for live onboarding and research execution
saas_runtime.py       — Auth, tenancy, jobs, dataset rows, quality gates, billing/provider foundations
saas_worker.py        — Background worker for queued SaaS jobs
validate_public_company.py — Private temp-workspace public-data validation
program.md            — Agent instructions
app/                  — React/Vite public product site
```

## License

MIT
