from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import research_runtime


class ResearchRuntimeTests(unittest.TestCase):
    def test_run_research_evaluation_persists_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            best_file = temp_path / "best.json"
            best_file.write_text(json.dumps({"combined_score": 52.0, "provider": "local"}), encoding="utf-8")

            async def fake_run_evaluation(**_: object) -> dict:
                return {
                    "combined_score": 61.5,
                    "pass_rate": 0.8,
                    "by_category": {"pricing": 0.44, "security": 0.91},
                    "results": [
                        {
                            "question": "What does pricing look like?",
                            "category": "pricing",
                            "accuracy": 0.32,
                            "expected": "Pricing is flexible.",
                            "actual": "I am not sure.",
                            "pass": False,
                        }
                    ],
                }

            with mock.patch.object(research_runtime, "STATE_DIR", temp_path / "state"), mock.patch.object(
                research_runtime, "BEST_FILE", str(best_file)
            ), mock.patch.object(research_runtime, "_run_evaluation_async", fake_run_evaluation), mock.patch.object(
                research_runtime, "_knowledge_stats", return_value={"business_name": "Acme", "knowledge_topics": 8, "test_questions": 12}
            ):
                payload = research_runtime.run_research_evaluation({"provider": "local", "note": "smoke"})

            self.assertEqual(payload["status"], "completed")
            self.assertTrue(payload["improved"])
            self.assertTrue(Path(payload["runDirectory"]).exists())
            self.assertEqual(len(payload["artifacts"]), 3)
            self.assertEqual(payload["weakestCategories"][0]["category"], "pricing")

    def test_research_health_reports_latest_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            state_dir = temp_path / "state"
            latest = state_dir / "20260423010101-local"
            latest.mkdir(parents=True, exist_ok=True)
            response_path = latest / "response.json"
            response_path.write_text(json.dumps({"runId": latest.name}), encoding="utf-8")
            best_file = temp_path / "best.json"
            best_file.write_text(json.dumps({"combined_score": 77.3, "provider": "local"}), encoding="utf-8")
            experiments = temp_path / "experiments.log"
            experiments.write_text('{"score": 77.3}\n', encoding="utf-8")

            with mock.patch.object(research_runtime, "STATE_DIR", state_dir), mock.patch.object(
                research_runtime, "BEST_FILE", str(best_file)
            ), mock.patch.object(research_runtime, "LOG_FILE", str(experiments)), mock.patch.object(
                research_runtime, "_knowledge_stats", return_value={"business_name": "Acme", "knowledge_topics": 8, "test_questions": 12}
            ):
                payload = research_runtime.research_health()

            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["latestRunId"], latest.name)
            self.assertEqual(payload["baseline"]["combined_score"], 77.3)


if __name__ == "__main__":
    unittest.main()
