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

# 5. Point your AI agent at program.md to start optimizing
```

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
evaluate.py  — Scoring engine (DO NOT MODIFY)
program.md   — Agent instructions
app/         — React/Vite frontend for the project homepage
```

## License

MIT
