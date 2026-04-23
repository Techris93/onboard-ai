"""
Minimal HTTP API for live onboarding intake execution.

Endpoints:
  GET  /api/health
  GET  /api/runs/<run_id>
  POST /api/onboarding
"""

from __future__ import annotations

import argparse
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from backend_runtime import llm_kb_status, load_run, run_onboarding
from research_runtime import load_research_run, research_health, run_research_evaluation


def _allowed_origins() -> str:
    return os.environ.get("ONBOARDAI_ALLOWED_ORIGIN", "*")


class OnboardingApiHandler(BaseHTTPRequestHandler):
    server_version = "OnboardAIBackend/0.1"

    def _send_json(self, status_code: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", _allowed_origins())
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", _allowed_origins())
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self._send_json(
                200,
                {
                    "status": "ok",
                    "service": "onboard-ai-backend",
                    "llmKb": llm_kb_status(),
                },
            )
            return

        if parsed.path.startswith("/api/runs/"):
            run_id = parsed.path.rsplit("/", 1)[-1]
            payload = load_run(run_id)
            if payload is None:
                self._send_json(404, {"error": f"Run '{run_id}' was not found."})
                return
            self._send_json(200, payload)
            return

        if parsed.path == "/api/research/health":
            self._send_json(200, research_health())
            return

        if parsed.path.startswith("/api/research/runs/"):
            run_id = parsed.path.rsplit("/", 1)[-1]
            payload = load_research_run(run_id)
            if payload is None:
                self._send_json(404, {"error": f"Research run '{run_id}' was not found."})
                return
            self._send_json(200, payload)
            return

        self._send_json(404, {"error": "Route not found."})

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path not in {"/api/onboarding", "/api/research/evaluate"}:
            self._send_json(404, {"error": "Route not found."})
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            content_length = 0

        try:
            raw_body = self.rfile.read(content_length or 0).decode("utf-8")
            payload = json.loads(raw_body or "{}")
        except json.JSONDecodeError:
            self._send_json(400, {"error": "Request body must be valid JSON."})
            return

        try:
            if parsed.path == "/api/onboarding":
                result = run_onboarding(payload)
            else:
                result = run_research_evaluation(payload)
        except Exception as exc:  # noqa: BLE001
            self._send_json(500, {"error": str(exc)})
            return

        self._send_json(200, result)

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return


def main() -> int:
    parser = argparse.ArgumentParser(description="OnboardAI backend worker API")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), OnboardingApiHandler)
    print(f"OnboardAI backend listening on http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
