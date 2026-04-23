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
    python evaluate.py --provider local  # Run an offline local benchmark
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

from config import build_prompt, retrieve_context, TEMPERATURE, MAX_TOKENS

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
KNOWLEDGE_FILE = os.path.join(DATA_DIR, "knowledge.json")
TEST_FILE = os.path.join(DATA_DIR, "test_qa.json")
BEST_FILE = os.path.join(DATA_DIR, "best.json")
LOG_FILE = os.path.join(DATA_DIR, "experiments.log")
REPO_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PROVIDER = "gemini"

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


LOCAL_STOP_WORDS = {
    "the", "and", "for", "with", "from", "that", "this", "into", "about",
    "your", "their", "there", "what", "when", "where", "which", "who",
    "will", "would", "could", "should", "have", "has", "had", "does",
    "doesn", "just", "than", "then", "them", "they", "these", "those",
    "while", "also", "because", "using", "used", "into", "onto", "across",
    "under", "over", "between", "after", "before", "through", "about",
    "need", "want", "like", "my", "our", "you", "can", "how", "why",
    "is", "are", "was", "were", "be", "to", "of", "in", "on", "at",
    "or", "if", "it", "its", "a", "an", "do", "i",
}


def _normalize_tokens(text: str) -> List[str]:
    return [
        token
        for token in re.findall(r"[A-Za-z0-9][A-Za-z0-9+:/_-]*", text.lower())
        if len(token) > 2 and token not in LOCAL_STOP_WORDS
    ]


def _question_phrases(question: str) -> set[str]:
    tokens = _normalize_tokens(question)
    return {
        " ".join(tokens[index:index + 2])
        for index in range(len(tokens) - 1)
        if len(tokens[index:index + 2]) == 2
    }


QUESTION_BOOSTS = (
    (("realtime", "real-time", "chat", "collaborative"), ("realtime", "broadcast", "multiplayer", "sync")),
    (("firebase", "migrate", "migration"), ("firebase", "migrate", "migration", "storage", "auth")),
    (("vector", "embedding", "search", "machine", "learning"), ("vector", "embedding", "openai", "hugging", "search")),
    (("edge", "functions", "latency"), ("edge", "function", "latency", "serverless", "distributed")),
    (("hipaa", "compliance", "ephi", "health"), ("hipaa", "compliance", "ephi", "soc", "security")),
    (("storage", "files", "images", "videos"), ("storage", "bucket", "file", "image", "video", "rls")),
    (("portable", "lock-in", "postgres", "database"), ("postgres", "portable", "lock", "database")),
)


def _candidate_passages(question: str, knowledge_base: List[Dict[str, Any]]) -> List[str]:
    question_tokens = set(_normalize_tokens(question))
    question_phrases = _question_phrases(question)
    ranked: List[tuple[float, str]] = []
    question_lower = question.lower()

    for entry in knowledge_base:
        topic = str(entry.get("topic", ""))
        body = str(entry.get("content", ""))
        topic_tokens = set(_normalize_tokens(topic))
        pieces = re.split(r"(?<=[.!?])\s+|\n+|\s*[•;]\s+", body)

        for piece in pieces:
            normalized_piece = " ".join(piece.strip().split())
            if len(normalized_piece.split()) < 5:
                continue

            piece_tokens = set(_normalize_tokens(normalized_piece))
            if not piece_tokens:
                continue

            lowered_piece = normalized_piece.lower()
            overlap = len(question_tokens & piece_tokens)
            score = (overlap / max(1, len(question_tokens))) * 6
            score += len(question_tokens & topic_tokens) * 2.2
            score += sum(1 for phrase in question_phrases if phrase in lowered_piece) * 1.4

            if any(char.isdigit() for char in question) and any(char.isdigit() for char in normalized_piece):
                score += 0.5

            for required_terms, boosted_terms in QUESTION_BOOSTS:
                if any(term in question_lower for term in required_terms) and any(
                    term in lowered_piece or term in topic.lower()
                    for term in boosted_terms
                ):
                    score += 3.5

            if len(normalized_piece.split()) > 35:
                score -= 0.8

            if score > 0:
                ranked.append((score, normalized_piece))

    ranked.sort(key=lambda item: (-item[0], item[1]))
    unique_passages: List[str] = []
    seen = set()

    for _, passage in ranked:
        lowered = passage.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        unique_passages.append(passage)
        if len(unique_passages) == 4:
            break

    return unique_passages


def answer_locally(question: str, knowledge_base: List[Dict[str, Any]], business_name: str) -> str:
    candidates = _candidate_passages(question, knowledge_base)
    if not candidates:
        fallback_context = retrieve_context(question, knowledge_base)
        fallback = re.sub(r"\s+", " ", fallback_context.replace("**", "")).strip()
        if not fallback:
            return f"I couldn't find enough grounded information in the {business_name} knowledge base to answer that cleanly."
        fallback_words = fallback.split()
        if len(fallback_words) > 60:
            fallback = " ".join(fallback_words[:60]).rstrip(",;:") + "."
        elif not fallback.endswith((".", "!", "?")):
            fallback += "."
        return fallback

    answer = " ".join(candidates[:3]).strip()

    if re.match(r"(?i)^(can|does|do|is|are|has|have|will|would|should)\b", question):
        lowered_answer = f" {answer.lower()} "
        if not lowered_answer.strip().startswith(("yes", "no", "absolutely")):
            negative_markers = (" not ", "n't", " no ", " without ")
            prefix = "No." if any(marker in lowered_answer for marker in negative_markers) else "Yes."
            answer = f"{prefix} {answer}"

    answer = re.sub(r"\s+", " ", answer).strip()
    sentences = re.split(r"(?<=[.!?])\s+", answer)
    answer = " ".join(sentence for sentence in sentences if sentence).strip()
    if len(answer.split()) > 80:
        answer = " ".join(answer.split()[:80]).rstrip(",;:") + "."
    if not answer.endswith((".", "!", "?")):
        answer += "."
    return answer


async def answer_question(
    question: str,
    knowledge_base: List[Dict[str, Any]],
    business_name: str,
    provider: str = DEFAULT_PROVIDER,
) -> str:
    if provider == "local":
        return answer_locally(question, knowledge_base, business_name)

    prompt = build_prompt(question, knowledge_base, business_name)
    return await ask_model(prompt)


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
    provider: str = DEFAULT_PROVIDER,
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
    print(f"  Provider: {provider}")

    results = []
    for i, qa in enumerate(test_pairs):
        actual_answer = await answer_question(
            qa["question"],
            kb,
            business_name,
            provider=provider,
        )
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
        "provider": provider,
    }


def print_results(score: Dict, verbose: bool = False):
    """Print score results."""
    print(f"\n{'═' * 60}")
    print(f"  OnboardAI — Evaluation Results")
    print(f"  {score['timestamp']}")
    print(f"{'═' * 60}")
    print(f"\n  📊 Combined Score:   {score['combined_score']:.1f} / 100")
    print(f"     Provider:         {score.get('provider', DEFAULT_PROVIDER)}")
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
    parser.add_argument("--provider", choices=["gemini", "local"],
                        default=DEFAULT_PROVIDER,
                        help="Answer provider for evaluation (default: gemini)")
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
            best_provider = best.get("provider", DEFAULT_PROVIDER)
            if best_provider == args.provider:
                print(f"Best score ({args.provider}): {best.get('combined_score', 0):.2f}")
            else:
                print(f"No baseline yet for provider '{args.provider}'. Latest saved baseline is for '{best_provider}'.")
        else:
            print(f"No baseline yet for provider '{args.provider}'. Run `python evaluate.py --provider {args.provider}` first.")
        return

    score = await run_evaluation(
        verbose=args.verbose,
        provider=args.provider,
        max_retries=args.max_retries,
        retry_base_delay=args.retry_base_delay,
    )
    print_results(score, verbose=args.verbose)

    # Track best
    previous_best = 0
    if os.path.exists(BEST_FILE):
        with open(BEST_FILE) as f:
            best_payload = json.load(f)
        if best_payload.get("provider", DEFAULT_PROVIDER) == args.provider:
            previous_best = best_payload.get("combined_score", 0)

    if score["combined_score"] > previous_best:
        with open(BEST_FILE, "w") as f:
            json.dump({"combined_score": score["combined_score"],
                       "provider": args.provider,
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
            "provider": args.provider,
            "score": score["combined_score"],
            "accuracy": score["avg_accuracy"],
            "pass_rate": score["pass_rate"],
            "ts": score["timestamp"],
        }) + "\n")


if __name__ == "__main__":
    asyncio.run(main())
