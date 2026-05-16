"""
Minimal HTTP API for live onboarding intake execution.

Endpoints:
  GET  /api/health
  GET  /api/runs/<run_id>
  GET  /api/dataset-pipeline/runs/<run_id>
  POST /api/onboarding
  POST /api/dataset-pipeline/plan
"""

from __future__ import annotations

import argparse
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from backend_runtime import load_run, public_llm_kb_status, run_onboarding
from dataset_pipeline import load_dataset_pipeline_run, run_dataset_pipeline_plan
from research_runtime import load_research_run, research_health, run_research_evaluation
from saas_runtime import (
    SaasError,
    create_api_key,
    create_dataset_batch_job,
    create_onboarding_job,
    create_project,
    deployment_health,
    export_dataset_batch,
    get_artifact,
    get_dashboard,
    get_job,
    login,
    logout,
    request_password_reset,
    review_dataset_row,
    run_next_job,
    save_provider_key,
    seed_demo,
    signup,
)


def _allowed_origins() -> str:
    configured = os.environ.get("ONBOARDAI_ALLOWED_ORIGIN")
    if configured:
        return configured
    if os.environ.get("ONBOARDAI_ENV", "local") == "production":
        return "https://techris93.github.io"
    return "*"


class OnboardingApiHandler(BaseHTTPRequestHandler):
    server_version = "OnboardAIBackend/0.1"

    def _send_json(self, status_code: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", _allowed_origins())
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type, X-Worker-Token")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", _allowed_origins())
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type, X-Worker-Token")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def _bearer_token(self) -> str:
        value = self.headers.get("Authorization", "")
        if value.lower().startswith("bearer "):
            return value.split(" ", 1)[1].strip()
        return ""

    def _read_payload(self) -> dict | None:
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            content_length = 0

        try:
            raw_body = self.rfile.read(content_length or 0).decode("utf-8")
            payload = json.loads(raw_body or "{}")
        except json.JSONDecodeError:
            self._send_json(400, {"error": "Request body must be valid JSON."})
            return None
        return payload if isinstance(payload, dict) else {}

    def _send_error(self, exc: Exception) -> None:
        if isinstance(exc, SaasError):
            self._send_json(exc.status_code, {"error": exc.message})
            return
        self._send_json(500, {"error": str(exc)})

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self._send_json(
                200,
                {
                    "status": "ok",
                    "service": "onboard-ai-backend",
                    "llmKb": public_llm_kb_status(),
                },
            )
            return

        if parsed.path == "/api/deployment/health":
            try:
                self._send_json(200, deployment_health())
            except Exception as exc:  # noqa: BLE001
                self._send_error(exc)
            return

        if parsed.path == "/api/app/dashboard":
            try:
                self._send_json(200, get_dashboard(self._bearer_token()))
            except Exception as exc:  # noqa: BLE001
                self._send_error(exc)
            return

        if parsed.path.startswith("/api/app/jobs/"):
            job_id = parsed.path.rsplit("/", 1)[-1]
            try:
                self._send_json(200, get_job(self._bearer_token(), job_id))
            except Exception as exc:  # noqa: BLE001
                self._send_error(exc)
            return

        if parsed.path.startswith("/api/app/artifacts/"):
            artifact_id = parsed.path.rsplit("/", 1)[-1]
            try:
                self._send_json(200, get_artifact(self._bearer_token(), artifact_id))
            except Exception as exc:  # noqa: BLE001
                self._send_error(exc)
            return

        if parsed.path.startswith("/api/app/dataset-batches/") and parsed.path.endswith("/export"):
            batch_id = parsed.path.split("/")[-2]
            try:
                self._send_json(200, export_dataset_batch(self._bearer_token(), batch_id))
            except Exception as exc:  # noqa: BLE001
                self._send_error(exc)
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

        if parsed.path.startswith("/api/dataset-pipeline/runs/"):
            run_id = parsed.path.rsplit("/", 1)[-1]
            payload = load_dataset_pipeline_run(run_id)
            if payload is None:
                self._send_json(
                    404,
                    {"error": f"Dataset pipeline run '{run_id}' was not found."},
                )
                return
            self._send_json(200, payload)
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
        payload = self._read_payload()
        if payload is None:
            return

        try:
            if parsed.path == "/api/auth/signup":
                result = signup(payload)
            elif parsed.path == "/api/auth/login":
                result = login(payload)
            elif parsed.path == "/api/auth/logout":
                result = logout(self._bearer_token())
            elif parsed.path == "/api/auth/password-reset":
                result = request_password_reset(payload)
            elif parsed.path == "/api/app/projects":
                result = create_project(self._bearer_token(), payload)
            elif parsed.path == "/api/app/onboarding-jobs":
                result = create_onboarding_job(self._bearer_token(), payload)
            elif parsed.path == "/api/app/dataset-batches":
                result = create_dataset_batch_job(self._bearer_token(), payload)
            elif parsed.path == "/api/app/jobs/run-next":
                dashboard = get_dashboard(self._bearer_token())
                result = run_next_job(
                    limit=int(payload.get("limit") or 1),
                    organization_id=dashboard["activeOrganizationId"],
                )
            elif parsed.path == "/api/app/provider-keys":
                result = save_provider_key(self._bearer_token(), payload)
            elif parsed.path == "/api/app/api-keys":
                result = create_api_key(self._bearer_token(), payload)
            elif parsed.path.startswith("/api/app/reviews/rows/"):
                row_id = parsed.path.rsplit("/", 1)[-1]
                result = review_dataset_row(
                    self._bearer_token(),
                    row_id,
                    str(payload.get("decision") or ""),
                )
            elif parsed.path == "/api/worker/run-once":
                worker_token = os.environ.get("ONBOARDAI_WORKER_TOKEN")
                if worker_token and self.headers.get("X-Worker-Token") != worker_token:
                    raise SaasError(401, "Worker token is invalid.")
                result = run_next_job(limit=int(payload.get("limit") or 1))
            elif parsed.path == "/api/dev/seed":
                if os.environ.get("ONBOARDAI_ENV", "local") == "production":
                    raise SaasError(403, "Seed route is disabled in production.")
                result = seed_demo()
            elif parsed.path == "/api/onboarding":
                result = run_onboarding(payload)
            elif parsed.path == "/api/research/evaluate":
                result = run_research_evaluation(payload)
            elif parsed.path == "/api/dataset-pipeline/plan":
                result = run_dataset_pipeline_plan(payload)
            else:
                self._send_json(404, {"error": "Route not found."})
                return
        except Exception as exc:  # noqa: BLE001
            self._send_error(exc)
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
