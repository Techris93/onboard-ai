"""
Research runtime for OnboardAI evaluation loops.

This module persists repeatable evaluation runs so the web/API layer can track
research-backed config tuning instead of treating evaluation as a one-off CLI
command.
"""

from __future__ import annotations

import asyncio
import contextlib
import io
import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

REPO_DIR = Path(__file__).resolve().parent
DATA_DIR = REPO_DIR / "data"
KNOWLEDGE_FILE = DATA_DIR / "knowledge.json"
TEST_FILE = DATA_DIR / "test_qa.json"
BEST_FILE = DATA_DIR / "best.json"
LOG_FILE = DATA_DIR / "experiments.log"
STATE_DIR = REPO_DIR / "state" / "research_api"


@dataclass
class ArtifactRecord:
    label: str
    kind: str
    path: str
    preview: str


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _now() -> str:
    return datetime.now().astimezone().isoformat()


def _slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return cleaned or "research-run"


def _trim(text: str, limit: int = 1000) -> str:
    cleaned = str(text or "").strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[:limit].rstrip() + "..."


def _artifact_from_file(label: str, kind: str, path: Path) -> ArtifactRecord:
    preview = ""
    if path.exists():
        try:
            preview = _trim(path.read_text(encoding="utf-8", errors="replace"), 900)
        except Exception:
            preview = ""
    return ArtifactRecord(label=label, kind=kind, path=str(path), preview=preview)


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


async def _run_evaluation_async(**kwargs: Any) -> Dict[str, Any]:
    from evaluate import run_evaluation

    return await run_evaluation(**kwargs)


def _knowledge_stats() -> Dict[str, Any]:
    knowledge = _load_json(Path(KNOWLEDGE_FILE))
    tests = _load_json(Path(TEST_FILE))
    knowledge_rows = knowledge.get("knowledge_base")
    test_rows = tests.get("test_pairs")
    return {
        "business_name": knowledge.get("business_name"),
        "knowledge_topics": len(knowledge_rows) if isinstance(knowledge_rows, list) else 0,
        "test_questions": len(test_rows) if isinstance(test_rows, list) else 0,
    }


def _baseline_payload() -> Dict[str, Any]:
    return _load_json(Path(BEST_FILE))


def _weakest_categories(score: Dict[str, Any], limit: int = 5) -> List[Dict[str, Any]]:
    by_category = score.get("by_category") or {}
    if not isinstance(by_category, dict):
        return []
    ordered = sorted(
        ((str(name), float(value)) for name, value in by_category.items()),
        key=lambda item: item[1],
    )
    return [{"category": name, "accuracy": round(value, 4)} for name, value in ordered[:limit]]


def _failed_examples(score: Dict[str, Any], limit: int = 5) -> List[Dict[str, Any]]:
    results = score.get("results") or []
    if not isinstance(results, list):
        return []
    failed = [row for row in results if isinstance(row, dict) and not row.get("pass")]
    return [
        {
            "question": str(row.get("question") or ""),
            "category": str(row.get("category") or ""),
            "accuracy": row.get("accuracy"),
            "expected": _trim(str(row.get("expected") or ""), 220),
            "actual": _trim(str(row.get("actual") or ""), 220),
        }
        for row in failed[:limit]
    ]


def _recommendations(score: Dict[str, Any]) -> List[str]:
    recommendations: List[str] = []
    weakest = _weakest_categories(score, limit=3)
    if weakest:
        recommendations.append(
            "Target the weakest categories first: "
            + ", ".join(item["category"] for item in weakest)
            + "."
        )
    failed = _failed_examples(score, limit=3)
    if failed:
        recommendations.append(
            "Add or refine few-shot examples for the failed questions before broad prompt changes."
        )
    if float(score.get("pass_rate") or 0) < 0.75:
        recommendations.append(
            "Improve retrieval coverage or response rules before changing temperature or token limits."
        )
    if not recommendations:
        recommendations.append("The evaluation is stable; focus on incremental config tuning and stronger edge-case examples.")
    return recommendations


def research_health() -> Dict[str, Any]:
    baseline = _baseline_payload()
    experiments_log = Path(LOG_FILE)
    latest_log = ""
    if experiments_log.exists():
        try:
            latest_log = experiments_log.read_text(encoding="utf-8").splitlines()[-1]
        except Exception:
            latest_log = ""
    run_dirs = sorted(
        [path for path in STATE_DIR.glob("*") if path.is_dir()],
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )
    latest_run = run_dirs[0].name if run_dirs else None
    return {
        "status": "ok",
        "generatedAt": _now(),
        "baseline": baseline or None,
        "latestExperimentLog": latest_log or None,
        "latestRunId": latest_run,
        "dataStats": _knowledge_stats(),
    }


def run_research_evaluation(payload: Dict[str, Any]) -> Dict[str, Any]:
    provider = str(payload.get("provider") or "local").strip() or "local"
    note = str(payload.get("note") or "").strip()
    max_retries = int(payload.get("maxRetries") or 4)
    retry_base_delay = float(payload.get("retryBaseDelay") or 2.0)
    created_at = _now()
    run_id = f"{datetime.now().strftime('%Y%m%d%H%M%S')}-{_slugify(provider)}"
    run_dir = ensure_dir(STATE_DIR / run_id)

    stdout_buffer = io.StringIO()
    with contextlib.redirect_stdout(stdout_buffer):
        score = asyncio.run(
            _run_evaluation_async(
                verbose=False,
                provider=provider,
                max_retries=max_retries,
                retry_base_delay=retry_base_delay,
            )
        )

    baseline = _baseline_payload()
    previous_best = (
        float(baseline.get("combined_score") or 0)
        if str(baseline.get("provider") or provider) == provider
        else 0.0
    )
    improved = float(score.get("combined_score") or 0) > previous_best
    weakest_categories = _weakest_categories(score)
    failed_examples = _failed_examples(score)
    recommendations = _recommendations(score)

    score_path = run_dir / "evaluation.json"
    brief_path = run_dir / "research-brief.md"
    response_path = run_dir / "response.json"
    transcript_path = run_dir / "stdout.txt"

    score_path.write_text(json.dumps(score, indent=2), encoding="utf-8")
    transcript_path.write_text(stdout_buffer.getvalue(), encoding="utf-8")
    brief_path.write_text(
        "\n".join(
            [
                "# OnboardAI Research Brief",
                "",
                f"- Generated at: {created_at}",
                f"- Provider: {provider}",
                f"- Combined score: {score['combined_score']}",
                f"- Previous best: {previous_best}",
                f"- Improved: {'yes' if improved else 'no'}",
                f"- Note: {note or 'none'}",
                "",
                "## Weakest Categories",
                "",
                *[
                    f"- {item['category']}: accuracy={item['accuracy']}"
                    for item in weakest_categories
                ],
                "",
                "## Recommendations",
                "",
                *[f"- {item}" for item in recommendations],
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    response = {
        "runId": run_id,
        "status": "completed",
        "createdAt": created_at,
        "provider": provider,
        "note": note,
        "combinedScore": score["combined_score"],
        "previousBest": previous_best,
        "improved": improved,
        "weakestCategories": weakest_categories,
        "failedExamples": failed_examples,
        "recommendations": recommendations,
        "dataStats": _knowledge_stats(),
        "artifacts": [
            asdict(_artifact_from_file("Evaluation JSON", "json", score_path)),
            asdict(_artifact_from_file("Research brief", "markdown", brief_path)),
            asdict(_artifact_from_file("Evaluation stdout", "text", transcript_path)),
        ],
        "runDirectory": str(run_dir),
        "resultUrl": f"/api/research/runs/{run_id}",
    }
    response_path.write_text(json.dumps(response, indent=2), encoding="utf-8")
    return response


def load_research_run(run_id: str) -> Dict[str, Any] | None:
    path = STATE_DIR / run_id / "response.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
