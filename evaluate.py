"""
OnboardAI — Evaluation Harness
Scores the AI config from config.py against test Q&A pairs.

Most day-to-day optimization work should happen in config.py, but the
evaluation harness can still be improved for reliability and tooling.

Scoring (0-100):
  - Accuracy (50 pts)  — Does the answer contain the key facts?
  - Quality  (30 pts)  — Is the answer well-structured and appropriate length?
  - Coverage (20 pts)  — What % of test questions got a passing score?

Usage:
    python evaluate.py              # Run evaluation
    python evaluate.py --verbose    # Show per-question details
    python evaluate.py --commit     # Auto-commit if score improved
    python evaluate.py --baseline   # Show best score so far
"""

import json
import os
import sys
import re
import asyncio
import argparse
import random
import subprocess
from datetime import datetime
from typing import Dict, List, Any, Optional
from difflib import SequenceMatcher

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import build_prompt, TEMPERATURE, MAX_TOKENS

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
KNOWLEDGE_FILE = os.path.join(DATA_DIR, "knowledge.json")
TEST_FILE = os.path.join(DATA_DIR, "test_qa.json")
BEST_FILE = os.path.join(DATA_DIR, "best.json")
LOG_FILE = os.path.join(DATA_DIR, "experiments.log")
REPO_DIR = os.path.dirname(os.path.abspath(__file__))

# ═══ Gemini Client ═══════════════════════════════════════════════════════════

GEMINI_AVAILABLE = False
_CLIENT = None
_USE_LEGACY = False

try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    try:
        import google.generativeai as genai_legacy
        GEMINI_AVAILABLE = True
    except ImportError:
        pass

from dotenv import load_dotenv
load_dotenv()


def _get_client():
    global _CLIENT, _USE_LEGACY
    if _CLIENT is not None:
        return _CLIENT

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key.startswith("your_"):
        return None

    try:
        from google import genai
        _CLIENT = genai.Client(api_key=api_key)
        _USE_LEGACY = False
    except ImportError:
        import google.generativeai as generativeai
        generativeai.configure(api_key=api_key)
        _CLIENT = generativeai.GenerativeModel("gemini-2.5-flash")
        _USE_LEGACY = True

    return _CLIENT


async def ask_model(prompt: str) -> str:
    """Send prompt to Gemini and return response."""
    client = _get_client()
    if client is None:
        return "[AI unavailable: set GEMINI_API_KEY in .env]"

    loop = asyncio.get_event_loop()
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            if _USE_LEGACY:
                response = await loop.run_in_executor(
                    None, lambda: client.generate_content(prompt)
                )
            else:
                response = await loop.run_in_executor(
                    None, lambda: client.models.generate_content(
                        model="gemini-2.5-flash", contents=prompt
                    )
                )

            text = getattr(response, "text", "") or ""
            return text.strip() if text.strip() else "[AI error: empty response]"
        except Exception as e:
            last_error = e
            if attempt >= MAX_RETRIES or not _is_retryable_error(e):
                break

            delay = _compute_retry_delay(e, attempt)
            print(
                f"  ↻ Gemini transient error "
                f"(attempt {attempt}/{MAX_RETRIES}): "
                f"retrying in {delay:.1f}s"
            )
            await asyncio.sleep(delay)

    return f"[AI error: {last_error}]"


MAX_RETRIES = 4
RETRY_BASE_DELAY = 2.0
RETRYABLE_ERROR_MARKERS = (
    "429",
    "503",
    "RESOURCE_EXHAUSTED",
    "UNAVAILABLE",
    "rate limit",
    "quota",
    "temporarily unavailable",
    "service unavailable",
)


def _is_retryable_error(error: Exception) -> bool:
    text = str(error).lower()
    return any(marker.lower() in text for marker in RETRYABLE_ERROR_MARKERS)


def _extract_retry_delay_seconds(message: str) -> Optional[float]:
    patterns = (
        r"retry_delay\s*\{\s*seconds:\s*(\d+)",
        r"retry in\s*(\d+(?:\.\d+)?)s",
        r"retry in\s*(\d+(?:\.\d+)?)\s*seconds?",
        r'"retryDelay"\s*:\s*"(\d+(?:\.\d+)?)s"',
    )

    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE | re.DOTALL)
        if match:
            return float(match.group(1))

    return None


def _compute_retry_delay(error: Exception, attempt: int) -> float:
    explicit_delay = _extract_retry_delay_seconds(str(error))
    if explicit_delay is not None:
        return explicit_delay

    backoff = RETRY_BASE_DELAY * (2 ** (attempt - 1))
    jitter = random.uniform(0, min(1.0, backoff * 0.15))
    return backoff + jitter


# ═══ Scoring ═════════════════════════════════════════════════════════════════

def extract_key_facts(expected: str) -> List[str]:
    """Extract key facts from expected answer for matching."""
    # Split into sentences/phrases
    facts = []

    # Extract prices
    prices = re.findall(r'\$[\d.]+', expected)
    facts.extend(prices)

    # Extract times/hours
    times = re.findall(r'\d+(?:am|pm|:\d+)', expected, re.IGNORECASE)
    facts.extend(times)

    # Extract percentages
    pcts = re.findall(r'\d+%', expected)
    facts.extend(pcts)

    # Extract numbers with context
    numbers = re.findall(r'\d+(?:\.\d+)?(?:\s*(?:points?|days?|hours?|lbs?|miles?|locations?))', expected, re.IGNORECASE)
    facts.extend(numbers)

    # Extract email/phone
    contacts = re.findall(r'[\w.+-]+@[\w.-]+|(?:\(\d+\)\s*)?[\d-]{7,}', expected)
    facts.extend(contacts)

    # Extract key noun phrases (simplified)
    key_words = set()
    for word in expected.split():
        clean = word.strip(".,!?;:\"'()").lower()
        if len(clean) > 4 and clean not in {
            "about", "their", "there", "these", "those", "would", "could",
            "should", "which", "where", "after", "before", "through",
        }:
            key_words.add(clean)

    return facts + list(key_words)


def score_answer(actual: str, expected: str) -> Dict[str, Any]:
    """Score a single answer against expected."""
    actual_lower = actual.lower()
    expected_lower = expected.lower()

    # Fact coverage: what % of key facts appear in the actual answer
    facts = extract_key_facts(expected)
    if facts:
        found = sum(1 for f in facts if f.lower() in actual_lower)
        fact_score = found / len(facts)
    else:
        fact_score = SequenceMatcher(None, actual_lower, expected_lower).ratio()

    # Semantic similarity (simple)
    similarity = SequenceMatcher(None, actual_lower, expected_lower).ratio()

    # Length penalty: too short or too long
    expected_len = len(expected.split())
    actual_len = len(actual.split())
    if actual_len < expected_len * 0.3:
        length_penalty = 0.5  # way too short
    elif actual_len > expected_len * 3:
        length_penalty = 0.8  # too verbose
    else:
        length_penalty = 1.0

    # Error detection
    is_error = actual.startswith("[AI") or "unavailable" in actual_lower
    if is_error:
        return {"accuracy": 0, "quality": 0, "pass": False, "error": True}

    # Combined accuracy (0-1): weighted fact coverage + similarity
    accuracy = (fact_score * 0.7 + similarity * 0.3) * length_penalty

    # Quality (0-1): response structure
    quality = 1.0
    if actual_len < 5:
        quality *= 0.3
    if "i don't know" in actual_lower and "don't know" not in expected_lower:
        quality *= 0.5
    if not actual.rstrip().endswith((".", "!", "?")):
        quality *= 0.9

    return {
        "accuracy": round(accuracy, 4),
        "quality": round(quality, 4),
        "fact_coverage": round(fact_score, 4),
        "similarity": round(similarity, 4),
        "pass": accuracy >= 0.4,
        "error": False,
    }


# ═══ Evaluation ══════════════════════════════════════════════════════════════

async def run_evaluation(
    verbose: bool = False,
    max_retries: int = MAX_RETRIES,
    retry_base_delay: float = RETRY_BASE_DELAY,
) -> Dict:
    """Run the full evaluation."""
    global MAX_RETRIES, RETRY_BASE_DELAY
    MAX_RETRIES = max(1, max_retries)
    RETRY_BASE_DELAY = max(0.1, retry_base_delay)

    # Load data
    if not os.path.exists(KNOWLEDGE_FILE) or not os.path.exists(TEST_FILE):
        print("❌ Run `python prepare.py` first.")
        sys.exit(1)

    with open(KNOWLEDGE_FILE) as f:
        knowledge = json.load(f)
    with open(TEST_FILE) as f:
        test_data = json.load(f)

    kb = knowledge["knowledge_base"]
    business_name = knowledge.get("business_name", "Business")
    test_pairs = test_data["test_pairs"]

    print(f"  Running evaluation against {len(test_pairs)} questions...")

    results = []
    for i, qa in enumerate(test_pairs):
        prompt = build_prompt(qa["question"], kb, business_name)
        actual_answer = await ask_model(prompt)
        scores = score_answer(actual_answer, qa["expected_answer"])

        result = {
            "question": qa["question"],
            "expected": qa["expected_answer"],
            "actual": actual_answer,
            "category": qa.get("category", "?"),
            "difficulty": qa.get("difficulty", "?"),
            **scores,
        }
        results.append(result)

        # Progress dot
        status = "✅" if scores["pass"] else "❌"
        if verbose:
            print(f"\n  Q{i+1}: {qa['question']}")
            print(f"       Expected: {qa['expected_answer'][:100]}...")
            print(f"       Got:      {actual_answer[:100]}...")
            print(f"       {status} accuracy={scores['accuracy']:.2f}  "
                  f"facts={scores.get('fact_coverage', 0):.2f}  "
                  f"quality={scores['quality']:.2f}")
        else:
            print(f"  {status}", end="", flush=True)

    if not verbose:
        print()

    # Aggregate scores
    n = len(results)
    errors = sum(1 for r in results if r["error"])

    avg_accuracy = sum(r["accuracy"] for r in results) / n if n else 0
    avg_quality = sum(r["quality"] for r in results) / n if n else 0
    pass_rate = sum(1 for r in results if r["pass"]) / n if n else 0

    # Final score (0-100)
    accuracy_score = avg_accuracy * 50
    quality_score = avg_quality * 30
    coverage_score = pass_rate * 20
    combined = round(accuracy_score + quality_score + coverage_score, 2)

    # Per-category breakdown
    by_category = {}
    for r in results:
        cat = r["category"]
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(r)

    return {
        "combined_score": combined,
        "accuracy_score": round(accuracy_score, 2),
        "quality_score": round(quality_score, 2),
        "coverage_score": round(coverage_score, 2),
        "avg_accuracy": round(avg_accuracy, 4),
        "avg_quality": round(avg_quality, 4),
        "pass_rate": round(pass_rate, 4),
        "total_questions": n,
        "passed": sum(1 for r in results if r["pass"]),
        "failed": sum(1 for r in results if not r["pass"]),
        "errors": errors,
        "by_category": {
            cat: round(sum(r["accuracy"] for r in rs) / len(rs), 4)
            for cat, rs in by_category.items()
        },
        "results": results,
        "timestamp": datetime.now().isoformat(),
    }


def print_results(score: Dict, verbose: bool = False):
    """Print score results."""
    print(f"\n{'═' * 60}")
    print(f"  OnboardAI — Evaluation Results")
    print(f"  {score['timestamp']}")
    print(f"{'═' * 60}")
    print(f"\n  📊 Combined Score:   {score['combined_score']:.1f} / 100")
    print(f"     Accuracy:         {score['accuracy_score']:.1f} / 50")
    print(f"     Quality:          {score['quality_score']:.1f} / 30")
    print(f"     Coverage:         {score['coverage_score']:.1f} / 20")
    print(f"\n  ✅ Passed: {score['passed']}/{score['total_questions']}  "
          f"({score['pass_rate']*100:.0f}%)")
    if score['errors']:
        print(f"  ⚠️  AI errors: {score['errors']}")

    # Per-category
    print(f"\n  {'─' * 56}")
    print(f"  Per-Category Accuracy:")
    for cat, acc in sorted(score["by_category"].items(), key=lambda x: -x[1]):
        bar = "█" * int(acc * 20) + "░" * (20 - int(acc * 20))
        print(f"    {cat:15s}  {bar}  {acc:.0%}")

    print(f"\n{'═' * 60}")
    print(f"\n>>> SCORE={score['combined_score']:.2f} <<<\n")


# ═══ Git Integration ═════════════════════════════════════════════════════════

def git_commit(score: float):
    """Commit config.py if score improved."""
    subprocess.run(
        ["git", "add", "config.py"],
        cwd=REPO_DIR, capture_output=True
    )
    subprocess.run(
        ["git", "commit", "-m",
         f"feat(config): score={score:.2f}"],
        cwd=REPO_DIR, capture_output=True
    )


# ═══ Main ════════════════════════════════════════════════════════════════════

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--commit", action="store_true")
    parser.add_argument("--baseline", action="store_true")
    parser.add_argument("--max-retries", type=int, default=MAX_RETRIES,
                        help="Total Gemini attempts per question (default: 4)")
    parser.add_argument("--retry-base-delay", type=float,
                        default=RETRY_BASE_DELAY,
                        help="Initial backoff delay in seconds (default: 2.0)")
    args = parser.parse_args()

    os.makedirs(DATA_DIR, exist_ok=True)

    if args.baseline:
        if os.path.exists(BEST_FILE):
            with open(BEST_FILE) as f:
                best = json.load(f)
            print(f"Best score: {best.get('combined_score', 0):.2f}")
        else:
            print("No baseline yet. Run `python evaluate.py` first.")
        return

    score = await run_evaluation(
        verbose=args.verbose,
        max_retries=args.max_retries,
        retry_base_delay=args.retry_base_delay,
    )
    print_results(score, verbose=args.verbose)

    # Track best
    previous_best = 0
    if os.path.exists(BEST_FILE):
        with open(BEST_FILE) as f:
            previous_best = json.load(f).get("combined_score", 0)

    if score["combined_score"] > previous_best:
        with open(BEST_FILE, "w") as f:
            json.dump({"combined_score": score["combined_score"],
                       "timestamp": score["timestamp"]}, f, indent=2)
        if previous_best > 0:
            print(f"  📈 New best! {previous_best:.1f} → {score['combined_score']:.1f}")
        else:
            print(f"  📊 Baseline: {score['combined_score']:.1f}")

        if args.commit:
            git_commit(score["combined_score"])
            print(f"  ✅ Committed config.py")
    else:
        print(f"  📉 No improvement. Current: {score['combined_score']:.1f}, "
              f"Best: {previous_best:.1f}")

    # Log
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps({
            "score": score["combined_score"],
            "accuracy": score["avg_accuracy"],
            "pass_rate": score["pass_rate"],
            "ts": score["timestamp"],
        }) + "\n")


if __name__ == "__main__":
    asyncio.run(main())
