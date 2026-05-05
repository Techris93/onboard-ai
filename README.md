<p align="center">
  <h1 align="center">🧠 OnboardAI</h1>
  <p align="center"><strong>AI-Powered Business Onboarding</strong></p>
  <p align="center">Drop in your business data → AI agent optimizes the config → you get a custom AI assistant.</p>
</p>

---

## What It Does

OnboardAI uses the [autoresearch](https://github.com/karpathy/autoresearch) pattern to automatically optimize an AI assistant for your specific business. An AI agent iterates on system prompts, few-shot examples, and retrieval settings until the AI accurately answers your customers' questions.

## Quick Start

```bash
# 1. Install
pip install -r requirements.txt

# 2. Set your Gemini API key
cp .env.example .env
# Edit .env → add GEMINI_API_KEY

# 3. Generate sample data (or import your own)
python prepare.py

# 4. Run baseline evaluation
python evaluate.py --verbose

# or run fully offline without Gemini
python evaluate.py --provider local --verbose

# 5. Point your AI agent at program.md to start optimizing
```

`evaluate.py` now retries transient Gemini `429` and `503` failures with
backoff, so benchmark runs are less likely to fail on short-lived API issues.
It also supports `--provider local` for a model-free offline benchmark path.

## Private Public-Data Validation

Use the private validation runner when you want to onboard a public company for
testing without writing that demo data into the repo's tracked `data/` files or
the website.

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

The repo now includes a real onboarding API:

```bash
python backend_api.py --host 127.0.0.1 --port 8787
```

Available routes:
- `GET /api/health`
- `GET /api/runs/<run_id>`
- `POST /api/onboarding`

What the worker does:
- stores each onboarding run locally under `state/onboarding_api/`
- creates a writable llm-kb workspace under `state/llm_kb_workspace/` unless `LLM_KB_ROOT` is set
- writes a normalized intake packet and onboarding brief
- runs `llm-kb` sync, compile, agent recommendation, activation brief creation, filing, and publish-safe artifact generation when `llm-kb` is installed locally
- returns the stored run, command summaries, warnings, and artifact previews to the website

## Adaptive Onboarding Paths

OnboardAI no longer treats onboarding as a static checklist. Each completed or
stalled path updates local outcome memory so the next user can be routed with
better timing, confidence, and context.

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

The onboarding form in `app/` can now POST directly to the backend worker.

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

The checked-in `render.yaml` and `scripts/render_build.sh` install this repo's declared Python and frontend dependencies, then build the Vite app. The `llm-knowledge-base` repository is now public, so Render no longer needs GitHub credentials to clone it. The backend still treats the `llm-kb` binary as optional via `LLM_KB_BIN`, which keeps deploys healthy even when `llm-kb` is not installed in the image.

Recommended Render setup:
- Use the checked-in `render.yaml` Blueprint.
- Set `VITE_API_BASE_URL` on the static site to the backend service URL when the services are split.
- Set `INSTALL_LLM_KB=true` if you want Render to install the public `Techris93/llm-knowledge-base` repo during the build.
- Set `LLM_KB_BIN` only if you provide a custom `llm-kb` executable path in the runtime image.
- Keep `LLM_KB_ROOT=/opt/render/project/src/state/llm_kb_workspace` for a writable knowledge workspace.

## Frontend

A lightweight React/Vite landing page now lives in `app/`. It mirrors the
actual repository workflow instead of inventing product features, so you can
use it as a project homepage, demo shell, or launch pad for future UI work.

```bash
cd app
npm install
npm run dev
```

The frontend is intentionally separate from the Python harness:
- Root Python files still drive data prep, config tuning, and evaluation.
- `app/` is a presentational frontend for explaining and showcasing that loop.

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
prepare.py   — Load/generate business data (DO NOT MODIFY)
config.py    — AI configuration (AGENT MODIFIES THIS)
evaluate.py  — Scoring engine with retry-aware Gemini evaluation
backend_runtime.py  — Run storage, llm-kb orchestration, and artifact packaging
backend_api.py  — HTTP API for live onboarding intake execution
validate_public_company.py  — Private temp-workspace public-data validation
program.md   — Agent instructions
app/         — React/Vite frontend for the project homepage
```

## License

MIT
