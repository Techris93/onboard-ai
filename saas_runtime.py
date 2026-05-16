"""
Production SaaS foundation for OnboardAI.

This module keeps the current stdlib backend deployable while adding the
durable pieces a real SaaS needs: auth, tenancy, jobs, artifacts, dataset
generation, quality gates, provider settings, usage tracking, and billing
foundations. SQLite is the local production path; the schema is intentionally
plain SQL so it can migrate to Postgres later.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from backend_runtime import run_onboarding
from dataset_pipeline import build_dataset_pipeline


REPO_DIR = Path(__file__).resolve().parent
STATE_DIR = REPO_DIR / "state"
DB_PATH = Path(os.environ.get("ONBOARDAI_DB_PATH", STATE_DIR / "onboardai.sqlite3"))
APP_ENV = os.environ.get("ONBOARDAI_ENV", "local")
SESSION_TTL_DAYS = int(os.environ.get("ONBOARDAI_SESSION_TTL_DAYS", "14"))
SECRET_KEY = os.environ.get("ONBOARDAI_SECRET_KEY", "local-dev-secret-change-me")

ROLES = {"owner", "admin", "operator", "viewer"}
JOB_STATUSES = {"queued", "running", "completed", "failed", "needs_review"}
PROVIDER_NAMES = ["local", "deepseek", "gemini", "openai", "anthropic"]
ALLOWED_LABELS = [
    "answerable",
    "handoff_required",
    "policy_boundary",
    "integration_guidance",
    "dataset_quality",
    "security_review",
]

PLAN_DEFINITIONS = {
    "starter": {
        "name": "Starter",
        "price": "$299/mo",
        "limits": {"onboarding_runs": 25, "generated_rows": 500, "evaluations": 25},
        "features": ["Onboarding runs", "Dataset planning", "Artifact exports"],
    },
    "growth": {
        "name": "Growth",
        "price": "$1,200/mo",
        "limits": {"onboarding_runs": 250, "generated_rows": 10000, "evaluations": 250},
        "features": ["Dataset generation", "Quality gates", "Evaluation loops"],
    },
    "enterprise": {
        "name": "Enterprise",
        "price": "Custom",
        "limits": {"onboarding_runs": -1, "generated_rows": -1, "evaluations": -1},
        "features": ["Private deployment", "Custom providers", "Human review"],
    },
}


def configured_cors_origin() -> str:
    configured = os.environ.get("ONBOARDAI_ALLOWED_ORIGIN")
    if configured:
        return configured
    if APP_ENV == "production":
        return "https://techris93.github.io"
    return "*"


class SaasError(Exception):
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


@dataclass
class Actor:
    user_id: str
    email: str
    name: str


@dataclass
class ProviderRow:
    messages: List[Dict[str, str]]
    label: str
    expected_behavior: str
    gold_reasoning: str
    source_trace: str
    quality_notes: str
    split: str
    token_estimate: int
    cost_estimate: float


class ClosingConnection(sqlite3.Connection):
    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> bool:
        result = super().__exit__(exc_type, exc_value, traceback)
        self.close()
        return result


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def slugify(value: str) -> str:
    cleaned = "".join(char.lower() if char.isalnum() else "-" for char in value)
    return "-".join(part for part in cleaned.split("-") if part) or "item"


def new_id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_urlsafe(12).replace('-', '').replace('_', '')[:16]}"


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, factory=ClosingConnection)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _json(value: Any) -> str:
    return json.dumps(value, separators=(",", ":"), sort_keys=True)


def _load_json(value: str | None, default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return {key: row[key] for key in row.keys()}


def _fetch_one(conn: sqlite3.Connection, query: str, args: Iterable[Any] = ()) -> Optional[sqlite3.Row]:
    return conn.execute(query, tuple(args)).fetchone()


def _fetch_all(conn: sqlite3.Connection, query: str, args: Iterable[Any] = ()) -> List[sqlite3.Row]:
    return list(conn.execute(query, tuple(args)).fetchall())


def _hash_token(token: str) -> str:
    return hmac.new(SECRET_KEY.encode("utf-8"), token.encode("utf-8"), hashlib.sha256).hexdigest()


def _hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        210_000,
    )
    return f"pbkdf2_sha256${salt}${base64.b64encode(digest).decode('ascii')}"


def _verify_password(password: str, stored: str) -> bool:
    try:
        scheme, salt, digest = stored.split("$", 2)
    except ValueError:
        return False
    if scheme != "pbkdf2_sha256":
        return False
    return hmac.compare_digest(_hash_password(password, salt), stored)


def init_db() -> None:
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                reset_token_hash TEXT,
                reset_expires_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS sessions (
                token_hash TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                revoked_at TEXT
            );

            CREATE TABLE IF NOT EXISTS organizations (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                slug TEXT NOT NULL UNIQUE,
                plan TEXT NOT NULL DEFAULT 'starter',
                environment TEXT NOT NULL DEFAULT 'local',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS memberships (
                id TEXT PRIMARY KEY,
                organization_id TEXT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                role TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL,
                UNIQUE(organization_id, user_id)
            );

            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                organization_id TEXT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                slug TEXT NOT NULL,
                description TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(organization_id, slug)
            );

            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                organization_id TEXT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                project_id TEXT REFERENCES projects(id) ON DELETE SET NULL,
                type TEXT NOT NULL,
                status TEXT NOT NULL,
                attempts INTEGER NOT NULL DEFAULT 0,
                max_attempts INTEGER NOT NULL DEFAULT 3,
                payload_json TEXT NOT NULL,
                result_json TEXT,
                error TEXT,
                created_by TEXT REFERENCES users(id) ON DELETE SET NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                started_at TEXT,
                completed_at TEXT
            );

            CREATE TABLE IF NOT EXISTS onboarding_runs (
                id TEXT PRIMARY KEY,
                organization_id TEXT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                project_id TEXT REFERENCES projects(id) ON DELETE SET NULL,
                job_id TEXT REFERENCES jobs(id) ON DELETE SET NULL,
                status TEXT NOT NULL,
                summary TEXT,
                payload_json TEXT NOT NULL,
                result_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS dataset_pipelines (
                id TEXT PRIMARY KEY,
                organization_id TEXT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                project_id TEXT REFERENCES projects(id) ON DELETE SET NULL,
                name TEXT NOT NULL,
                status TEXT NOT NULL,
                spec_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS dataset_batches (
                id TEXT PRIMARY KEY,
                pipeline_id TEXT NOT NULL REFERENCES dataset_pipelines(id) ON DELETE CASCADE,
                organization_id TEXT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                project_id TEXT REFERENCES projects(id) ON DELETE SET NULL,
                status TEXT NOT NULL,
                provider TEXT NOT NULL,
                requested_rows INTEGER NOT NULL,
                accepted_rows INTEGER NOT NULL DEFAULT 0,
                rejected_rows INTEGER NOT NULL DEFAULT 0,
                pass_rate REAL NOT NULL DEFAULT 0,
                report_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS dataset_rows (
                id TEXT PRIMARY KEY,
                batch_id TEXT NOT NULL REFERENCES dataset_batches(id) ON DELETE CASCADE,
                organization_id TEXT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                project_id TEXT REFERENCES projects(id) ON DELETE SET NULL,
                split TEXT NOT NULL,
                label TEXT NOT NULL,
                prompt_json TEXT NOT NULL,
                expected_behavior TEXT NOT NULL,
                gold_reasoning TEXT NOT NULL,
                source_trace TEXT NOT NULL,
                quality_notes TEXT NOT NULL,
                gate_results_json TEXT NOT NULL,
                status TEXT NOT NULL,
                rejection_reason TEXT,
                provider TEXT NOT NULL,
                token_estimate INTEGER NOT NULL DEFAULT 0,
                cost_estimate REAL NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS quality_gate_results (
                id TEXT PRIMARY KEY,
                row_id TEXT NOT NULL REFERENCES dataset_rows(id) ON DELETE CASCADE,
                gate TEXT NOT NULL,
                passed INTEGER NOT NULL,
                reason TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS artifacts (
                id TEXT PRIMARY KEY,
                organization_id TEXT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                project_id TEXT REFERENCES projects(id) ON DELETE SET NULL,
                job_id TEXT REFERENCES jobs(id) ON DELETE SET NULL,
                label TEXT NOT NULL,
                kind TEXT NOT NULL,
                content TEXT NOT NULL,
                preview TEXT NOT NULL,
                storage_uri TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS agent_runs (
                id TEXT PRIMARY KEY,
                organization_id TEXT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                project_id TEXT REFERENCES projects(id) ON DELETE SET NULL,
                job_id TEXT REFERENCES jobs(id) ON DELETE SET NULL,
                agent_name TEXT NOT NULL,
                status TEXT NOT NULL,
                summary TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS evaluations (
                id TEXT PRIMARY KEY,
                organization_id TEXT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                project_id TEXT REFERENCES projects(id) ON DELETE SET NULL,
                job_id TEXT REFERENCES jobs(id) ON DELETE SET NULL,
                provider TEXT NOT NULL,
                score REAL NOT NULL DEFAULT 0,
                result_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS provider_keys (
                id TEXT PRIMARY KEY,
                organization_id TEXT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                provider TEXT NOT NULL,
                secret_hash TEXT NOT NULL,
                masked_value TEXT NOT NULL,
                configured_by TEXT REFERENCES users(id) ON DELETE SET NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(organization_id, provider)
            );

            CREATE TABLE IF NOT EXISTS api_keys (
                id TEXT PRIMARY KEY,
                organization_id TEXT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                key_hash TEXT NOT NULL UNIQUE,
                prefix TEXT NOT NULL,
                role TEXT NOT NULL,
                created_by TEXT REFERENCES users(id) ON DELETE SET NULL,
                created_at TEXT NOT NULL,
                revoked_at TEXT
            );

            CREATE TABLE IF NOT EXISTS audit_logs (
                id TEXT PRIMARY KEY,
                organization_id TEXT REFERENCES organizations(id) ON DELETE SET NULL,
                user_id TEXT REFERENCES users(id) ON DELETE SET NULL,
                action TEXT NOT NULL,
                target_type TEXT NOT NULL,
                target_id TEXT,
                metadata_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS usage_events (
                id TEXT PRIMARY KEY,
                organization_id TEXT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                project_id TEXT REFERENCES projects(id) ON DELETE SET NULL,
                event_type TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                metadata_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS billing_customers (
                id TEXT PRIMARY KEY,
                organization_id TEXT NOT NULL UNIQUE REFERENCES organizations(id) ON DELETE CASCADE,
                provider TEXT NOT NULL,
                external_customer_id TEXT,
                plan TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS invitations (
                id TEXT PRIMARY KEY,
                organization_id TEXT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                email TEXT NOT NULL,
                role TEXT NOT NULL,
                token_hash TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS notifications (
                id TEXT PRIMARY KEY,
                organization_id TEXT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status, created_at);
            CREATE INDEX IF NOT EXISTS idx_artifacts_org ON artifacts(organization_id, created_at);
            CREATE INDEX IF NOT EXISTS idx_dataset_rows_batch ON dataset_rows(batch_id, status);
            CREATE INDEX IF NOT EXISTS idx_audit_org ON audit_logs(organization_id, created_at);
            """
        )


def audit_log(
    conn: sqlite3.Connection,
    organization_id: str | None,
    user_id: str | None,
    action: str,
    target_type: str,
    target_id: str | None = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    conn.execute(
        """
        INSERT INTO audit_logs (
            id, organization_id, user_id, action, target_type, target_id,
            metadata_json, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            new_id("audit"),
            organization_id,
            user_id,
            action,
            target_type,
            target_id,
            _json(metadata or {}),
            utc_now(),
        ),
    )


def usage_event(
    conn: sqlite3.Connection,
    organization_id: str,
    project_id: str | None,
    event_type: str,
    quantity: int = 1,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    conn.execute(
        """
        INSERT INTO usage_events (
            id, organization_id, project_id, event_type, quantity,
            metadata_json, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            new_id("usage"),
            organization_id,
            project_id,
            event_type,
            quantity,
            _json(metadata or {}),
            utc_now(),
        ),
    )


def _public_user(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "email": row["email"],
        "name": row["name"],
        "createdAt": row["created_at"],
    }


def signup(payload: Dict[str, Any]) -> Dict[str, Any]:
    init_db()
    email = str(payload.get("email") or "").strip().lower()
    password = str(payload.get("password") or "")
    name = str(payload.get("name") or email.split("@")[0] or "OnboardAI User").strip()
    org_name = str(payload.get("organizationName") or f"{name}'s Workspace").strip()
    if "@" not in email:
        raise SaasError(400, "A valid email is required.")
    if len(password) < 8:
        raise SaasError(400, "Password must be at least 8 characters.")
    if not org_name:
        raise SaasError(400, "Organization name is required.")

    now = utc_now()
    user_id = new_id("usr")
    org_id = new_id("org")
    project_id = new_id("prj")
    membership_id = new_id("mem")
    billing_id = new_id("bill")
    org_slug = slugify(org_name)
    with connect() as conn:
        if _fetch_one(conn, "SELECT id FROM users WHERE email = ?", (email,)):
            raise SaasError(409, "An account already exists for this email.")
        suffix = 1
        base_slug = org_slug
        while _fetch_one(conn, "SELECT id FROM organizations WHERE slug = ?", (org_slug,)):
            suffix += 1
            org_slug = f"{base_slug}-{suffix}"
        conn.execute(
            "INSERT INTO users (id, email, name, password_hash, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, email, name, _hash_password(password), now, now),
        )
        conn.execute(
            "INSERT INTO organizations (id, name, slug, plan, environment, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (org_id, org_name, org_slug, "starter", APP_ENV, now, now),
        )
        conn.execute(
            "INSERT INTO memberships (id, organization_id, user_id, role, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (membership_id, org_id, user_id, "owner", "active", now),
        )
        conn.execute(
            "INSERT INTO projects (id, organization_id, name, slug, description, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                project_id,
                org_id,
                "Default AI Onboarding",
                "default-ai-onboarding",
                "Initial workspace for onboarding, dataset readiness, and artifact review.",
                now,
                now,
            ),
        )
        conn.execute(
            "INSERT INTO billing_customers (id, organization_id, provider, plan, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (billing_id, org_id, "mock", "starter", "trial", now, now),
        )
        audit_log(conn, org_id, user_id, "auth.signup", "user", user_id, {"environment": APP_ENV})
    return login({"email": email, "password": password})


def login(payload: Dict[str, Any]) -> Dict[str, Any]:
    init_db()
    email = str(payload.get("email") or "").strip().lower()
    password = str(payload.get("password") or "")
    with connect() as conn:
        user = _fetch_one(conn, "SELECT * FROM users WHERE email = ?", (email,))
        if not user or not _verify_password(password, user["password_hash"]):
            raise SaasError(401, "Invalid email or password.")
        token = secrets.token_urlsafe(32)
        now = utc_now()
        expires_at = (datetime.now(timezone.utc) + timedelta(days=SESSION_TTL_DAYS)).isoformat()
        conn.execute(
            "INSERT INTO sessions (token_hash, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
            (_hash_token(token), user["id"], now, expires_at),
        )
        audit_log(conn, None, user["id"], "auth.login", "session", None, {})
    return {
        "token": token,
        "expiresAt": expires_at,
        "user": _public_user(user),
        "dashboard": get_dashboard(token),
    }


def logout(token: str) -> Dict[str, Any]:
    init_db()
    with connect() as conn:
        conn.execute(
            "UPDATE sessions SET revoked_at = ? WHERE token_hash = ?",
            (utc_now(), _hash_token(token)),
        )
    return {"status": "ok"}


def request_password_reset(payload: Dict[str, Any]) -> Dict[str, Any]:
    init_db()
    email = str(payload.get("email") or "").strip().lower()
    token = secrets.token_urlsafe(28)
    expires = (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat()
    with connect() as conn:
        user = _fetch_one(conn, "SELECT * FROM users WHERE email = ?", (email,))
        if user:
            conn.execute(
                "UPDATE users SET reset_token_hash = ?, reset_expires_at = ?, updated_at = ? WHERE id = ?",
                (_hash_token(token), expires, utc_now(), user["id"]),
            )
            audit_log(conn, None, user["id"], "auth.password_reset_requested", "user", user["id"], {})
    return {
        "status": "ok",
        "message": "If the account exists, a reset token has been created.",
        "localResetToken": token if APP_ENV == "local" else None,
        "expiresAt": expires if APP_ENV == "local" else None,
    }


def require_actor(token: str) -> Actor:
    init_db()
    if not token:
        raise SaasError(401, "Authentication is required.")
    with connect() as conn:
        session = _fetch_one(
            conn,
            """
            SELECT sessions.*, users.email, users.name
            FROM sessions
            JOIN users ON users.id = sessions.user_id
            WHERE sessions.token_hash = ?
              AND sessions.revoked_at IS NULL
              AND sessions.expires_at > ?
            """,
            (_hash_token(token), utc_now()),
        )
        if not session:
            raise SaasError(401, "Session is invalid or expired.")
        return Actor(user_id=session["user_id"], email=session["email"], name=session["name"])


def _membership(conn: sqlite3.Connection, actor: Actor, organization_id: str) -> sqlite3.Row:
    membership = _fetch_one(
        conn,
        """
        SELECT * FROM memberships
        WHERE user_id = ? AND organization_id = ? AND status = 'active'
        """,
        (actor.user_id, organization_id),
    )
    if not membership:
        raise SaasError(403, "You do not have access to this organization.")
    return membership


def require_role(
    conn: sqlite3.Connection,
    actor: Actor,
    organization_id: str,
    allowed: Iterable[str],
) -> sqlite3.Row:
    membership = _membership(conn, actor, organization_id)
    if membership["role"] not in set(allowed):
        raise SaasError(403, "Your role does not allow this action.")
    return membership


def _default_org_project(conn: sqlite3.Connection, actor: Actor) -> Tuple[str, str]:
    row = _fetch_one(
        conn,
        """
        SELECT organizations.id AS organization_id, projects.id AS project_id
        FROM memberships
        JOIN organizations ON organizations.id = memberships.organization_id
        LEFT JOIN projects ON projects.organization_id = organizations.id
        WHERE memberships.user_id = ? AND memberships.status = 'active'
        ORDER BY organizations.created_at ASC, projects.created_at ASC
        LIMIT 1
        """,
        (actor.user_id,),
    )
    if not row:
        raise SaasError(404, "No workspace exists for this user.")
    return row["organization_id"], row["project_id"]


def _organization(conn: sqlite3.Connection, organization_id: str) -> sqlite3.Row:
    org = _fetch_one(conn, "SELECT * FROM organizations WHERE id = ?", (organization_id,))
    if not org:
        raise SaasError(404, "Organization was not found.")
    return org


def _project(conn: sqlite3.Connection, organization_id: str, project_id: str) -> sqlite3.Row:
    project = _fetch_one(
        conn,
        "SELECT * FROM projects WHERE id = ? AND organization_id = ?",
        (project_id, organization_id),
    )
    if not project:
        raise SaasError(404, "Project was not found.")
    return project


def _artifact_public(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "label": row["label"],
        "kind": row["kind"],
        "preview": row["preview"],
        "storageUri": row["storage_uri"],
        "createdAt": row["created_at"],
        "jobId": row["job_id"],
        "projectId": row["project_id"],
    }


def _job_public(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "type": row["type"],
        "status": row["status"],
        "attempts": row["attempts"],
        "maxAttempts": row["max_attempts"],
        "error": row["error"],
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
        "startedAt": row["started_at"],
        "completedAt": row["completed_at"],
        "result": _load_json(row["result_json"], None),
        "projectId": row["project_id"],
    }


def _billing_summary(conn: sqlite3.Connection, organization_id: str) -> Dict[str, Any]:
    billing = _fetch_one(
        conn,
        "SELECT * FROM billing_customers WHERE organization_id = ?",
        (organization_id,),
    )
    usage_rows = _fetch_all(
        conn,
        """
        SELECT event_type, SUM(quantity) AS quantity
        FROM usage_events
        WHERE organization_id = ?
        GROUP BY event_type
        """,
        (organization_id,),
    )
    usage = {row["event_type"]: row["quantity"] for row in usage_rows}
    plan_key = billing["plan"] if billing else "starter"
    return {
        "provider": billing["provider"] if billing else "mock",
        "status": billing["status"] if billing else "trial",
        "plan": plan_key,
        "planDefinition": PLAN_DEFINITIONS.get(plan_key, PLAN_DEFINITIONS["starter"]),
        "usage": usage,
        "stripeConfigured": bool(os.environ.get("STRIPE_SECRET_KEY")),
    }


def _provider_status(conn: sqlite3.Connection, organization_id: str) -> List[Dict[str, Any]]:
    configured = {
        row["provider"]: row
        for row in _fetch_all(
            conn,
            "SELECT provider, masked_value, updated_at FROM provider_keys WHERE organization_id = ?",
            (organization_id,),
        )
    }
    return [
        {
            "provider": provider,
            "configured": provider == "local" or provider in configured,
            "mode": "local/offline" if provider == "local" else "external adapter",
            "maskedValue": configured[provider]["masked_value"] if provider in configured else None,
            "updatedAt": configured[provider]["updated_at"] if provider in configured else None,
        }
        for provider in PROVIDER_NAMES
    ]


def _monitoring_summary(conn: sqlite3.Connection, organization_id: str) -> Dict[str, Any]:
    failed = _fetch_one(
        conn,
        "SELECT COUNT(*) AS count FROM jobs WHERE organization_id = ? AND status = 'failed'",
        (organization_id,),
    )
    queued = _fetch_one(
        conn,
        "SELECT COUNT(*) AS count FROM jobs WHERE organization_id = ? AND status = 'queued'",
        (organization_id,),
    )
    latest_audit = _fetch_all(
        conn,
        "SELECT action, target_type, target_id, created_at FROM audit_logs WHERE organization_id = ? ORDER BY created_at DESC LIMIT 8",
        (organization_id,),
    )
    return {
        "failedJobs": failed["count"] if failed else 0,
        "queuedJobs": queued["count"] if queued else 0,
        "health": "operational",
        "errorTrackingConfigured": bool(os.environ.get("SENTRY_DSN")),
        "latestAuditEvents": [_row_to_dict(row) for row in latest_audit],
    }


def get_dashboard(token: str) -> Dict[str, Any]:
    actor = require_actor(token)
    with connect() as conn:
        organizations = _fetch_all(
            conn,
            """
            SELECT organizations.*, memberships.role
            FROM memberships
            JOIN organizations ON organizations.id = memberships.organization_id
            WHERE memberships.user_id = ? AND memberships.status = 'active'
            ORDER BY organizations.created_at ASC
            """,
            (actor.user_id,),
        )
        if not organizations:
            raise SaasError(404, "No organizations were found.")
        organization_id = organizations[0]["id"]
        projects = _fetch_all(
            conn,
            "SELECT * FROM projects WHERE organization_id = ? ORDER BY created_at ASC",
            (organization_id,),
        )
        project_id = projects[0]["id"] if projects else None
        members = _fetch_all(
            conn,
            """
            SELECT users.id, users.email, users.name, memberships.role, memberships.status
            FROM memberships
            JOIN users ON users.id = memberships.user_id
            WHERE memberships.organization_id = ?
            ORDER BY memberships.created_at ASC
            """,
            (organization_id,),
        )
        jobs = _fetch_all(
            conn,
            "SELECT * FROM jobs WHERE organization_id = ? ORDER BY created_at DESC LIMIT 12",
            (organization_id,),
        )
        artifacts = _fetch_all(
            conn,
            "SELECT * FROM artifacts WHERE organization_id = ? ORDER BY created_at DESC LIMIT 12",
            (organization_id,),
        )
        pipelines = _fetch_all(
            conn,
            "SELECT * FROM dataset_pipelines WHERE organization_id = ? ORDER BY created_at DESC LIMIT 8",
            (organization_id,),
        )
        batches = _fetch_all(
            conn,
            "SELECT * FROM dataset_batches WHERE organization_id = ? ORDER BY created_at DESC LIMIT 8",
            (organization_id,),
        )
        reviews = _fetch_one(
            conn,
            "SELECT COUNT(*) AS count FROM dataset_rows WHERE organization_id = ? AND status = 'needs_review'",
            (organization_id,),
        )
        return {
            "environment": APP_ENV,
            "user": {"id": actor.user_id, "email": actor.email, "name": actor.name},
            "organizations": [
                {
                    "id": row["id"],
                    "name": row["name"],
                    "slug": row["slug"],
                    "plan": row["plan"],
                    "role": row["role"],
                    "environment": row["environment"],
                }
                for row in organizations
            ],
            "activeOrganizationId": organization_id,
            "projects": [_row_to_dict(row) for row in projects],
            "activeProjectId": project_id,
            "members": [_row_to_dict(row) for row in members],
            "jobs": [_job_public(row) for row in jobs],
            "artifacts": [_artifact_public(row) for row in artifacts],
            "datasetPipelines": [
                {
                    **_row_to_dict(row),
                    "spec": _load_json(row["spec_json"], {}),
                    "spec_json": None,
                }
                for row in pipelines
            ],
            "datasetBatches": [
                {
                    **_row_to_dict(row),
                    "report": _load_json(row["report_json"], {}),
                    "report_json": None,
                }
                for row in batches
            ],
            "reviewQueueCount": reviews["count"] if reviews else 0,
            "billing": _billing_summary(conn, organization_id),
            "providers": _provider_status(conn, organization_id),
            "monitoring": _monitoring_summary(conn, organization_id),
            "security": {
                "tenantIsolation": "enforced by membership checks",
                "secretPolicy": "provider secrets are hashed/masked and never returned",
                "corsOrigin": configured_cors_origin(),
                "rateLimitMode": "model-ready; gateway enforcement recommended for production",
            },
        }


def create_project(token: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    actor = require_actor(token)
    organization_id = str(payload.get("organizationId") or "")
    name = str(payload.get("name") or "").strip()
    description = str(payload.get("description") or "").strip()
    if not name:
        raise SaasError(400, "Project name is required.")
    with connect() as conn:
        if not organization_id:
            organization_id, _ = _default_org_project(conn, actor)
        require_role(conn, actor, organization_id, {"owner", "admin", "operator"})
        project_id = new_id("prj")
        slug = slugify(name)
        suffix = 1
        base_slug = slug
        while _fetch_one(
            conn,
            "SELECT id FROM projects WHERE organization_id = ? AND slug = ?",
            (organization_id, slug),
        ):
            suffix += 1
            slug = f"{base_slug}-{suffix}"
        now = utc_now()
        conn.execute(
            "INSERT INTO projects (id, organization_id, name, slug, description, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (project_id, organization_id, name, slug, description, now, now),
        )
        audit_log(conn, organization_id, actor.user_id, "project.create", "project", project_id, {"name": name})
        return {"project": _row_to_dict(_project(conn, organization_id, project_id))}


def _create_job(
    conn: sqlite3.Connection,
    actor: Actor,
    organization_id: str,
    project_id: str | None,
    job_type: str,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    job_id = new_id("job")
    now = utc_now()
    conn.execute(
        """
        INSERT INTO jobs (
            id, organization_id, project_id, type, status, payload_json,
            created_by, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            job_id,
            organization_id,
            project_id,
            job_type,
            "queued",
            _json(payload),
            actor.user_id,
            now,
            now,
        ),
    )
    audit_log(conn, organization_id, actor.user_id, "job.create", "job", job_id, {"type": job_type})
    usage_event(conn, organization_id, project_id, f"{job_type}_jobs", 1)
    return _job_public(_fetch_one(conn, "SELECT * FROM jobs WHERE id = ?", (job_id,)))


def create_onboarding_job(token: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    actor = require_actor(token)
    with connect() as conn:
        organization_id = str(payload.get("organizationId") or "")
        project_id = str(payload.get("projectId") or "")
        if not organization_id:
            organization_id, default_project_id = _default_org_project(conn, actor)
            project_id = project_id or default_project_id
        require_role(conn, actor, organization_id, {"owner", "admin", "operator"})
        if project_id:
            _project(conn, organization_id, project_id)
        job = _create_job(
            conn,
            actor,
            organization_id,
            project_id or None,
            "onboarding",
            {"profile": payload.get("profile") or payload},
        )
        return {"job": job}


def create_dataset_batch_job(token: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    actor = require_actor(token)
    with connect() as conn:
        organization_id = str(payload.get("organizationId") or "")
        project_id = str(payload.get("projectId") or "")
        if not organization_id:
            organization_id, default_project_id = _default_org_project(conn, actor)
            project_id = project_id or default_project_id
        require_role(conn, actor, organization_id, {"owner", "admin", "operator"})
        if project_id:
            _project(conn, organization_id, project_id)
        provider = str(payload.get("provider") or "local").strip().lower()
        if provider not in PROVIDER_NAMES:
            raise SaasError(400, "Unsupported provider.")
        requested_rows = int(payload.get("requestedRows") or 8)
        requested_rows = max(1, min(requested_rows, 100))
        job = _create_job(
            conn,
            actor,
            organization_id,
            project_id or None,
            "dataset_batch",
            {
                "provider": provider,
                "requestedRows": requested_rows,
                "profile": payload.get("profile") or {},
            },
        )
        return {"job": job}


class ProviderAdapter:
    provider = "base"

    def generate_rows(self, profile: Dict[str, Any], requested_rows: int) -> List[ProviderRow]:
        raise NotImplementedError


class LocalProviderAdapter(ProviderAdapter):
    provider = "local"

    def generate_rows(self, profile: Dict[str, Any], requested_rows: int) -> List[ProviderRow]:
        company = str(profile.get("companyName") or "Customer Company")
        use_case = str(profile.get("useCase") or "fine-tuning-dataset").replace("-", " ")
        sources = profile.get("sources") if isinstance(profile.get("sources"), list) else []
        source_trace = ", ".join(str(item) for item in sources[:4]) or "approved company sources"
        labels = ALLOWED_LABELS
        splits = ["train", "train", "validation", "test"]
        rows: List[ProviderRow] = []
        for index in range(requested_rows):
            label = labels[index % len(labels)]
            split = splits[index % len(splits)]
            user_turn = (
                f"For {company}, what should the assistant do when a {use_case} request "
                f"needs {label.replace('_', ' ')} using {source_trace}?"
            )
            rows.append(
                ProviderRow(
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are an OnboardAI domain assistant that follows approved "
                                "company sources and escalates when source authority is missing."
                            ),
                        },
                        {"role": "user", "content": user_turn},
                    ],
                    label=label,
                    expected_behavior=(
                        "The assistant should answer only from approved source context, identify "
                        "the relevant boundary, and route to a human owner when confidence or "
                        "authority is insufficient."
                    ),
                    gold_reasoning=(
                        f"The row targets {label} behavior for {company}, keeps the final user "
                        "turn specific, and avoids training the model to invent unsupported policy."
                    ),
                    source_trace=source_trace,
                    quality_notes=(
                        "Local deterministic generation for workflow validation; replace with "
                        "external provider generation when production keys are configured."
                    ),
                    split=split,
                    token_estimate=165 + index * 3,
                    cost_estimate=0.0,
                )
            )
        return rows


class ExternalProviderPlaceholder(LocalProviderAdapter):
    def __init__(self, provider: str):
        self.provider = provider

    def generate_rows(self, profile: Dict[str, Any], requested_rows: int) -> List[ProviderRow]:
        rows = super().generate_rows(profile, requested_rows)
        for row in rows:
            row.quality_notes = (
                f"{self.provider} adapter contract is configured, but this run used the "
                "safe local generator because live provider execution requires credentials "
                "and explicit enablement."
            )
            row.cost_estimate = 0.0
        return rows


def provider_adapter(provider: str) -> ProviderAdapter:
    if provider == "local":
        return LocalProviderAdapter()
    return ExternalProviderPlaceholder(provider)


def run_quality_gates(row: ProviderRow, seen_prompts: set[str]) -> List[Dict[str, Any]]:
    final_user = next((msg["content"] for msg in reversed(row.messages) if msg.get("role") == "user"), "")
    prompt_key = final_user.lower().strip()
    gate_results = [
        ("Schema validity", bool(row.messages and row.label and row.expected_behavior), "Required row fields are present."),
        ("Role correctness", all(msg.get("role") in {"system", "user", "assistant"} for msg in row.messages), "Message roles are allowed."),
        ("Final user turn quality", len(final_user.split()) >= 10 and "?" in final_user, "Final user turn is specific and question-shaped."),
        ("Allowed labels", row.label in ALLOWED_LABELS, "Label is in the approved label set."),
        ("Canonical order", row.messages[0].get("role") == "system" and row.messages[-1].get("role") == "user", "Messages follow system-to-user order."),
        ("Duplicate prompt detection", prompt_key not in seen_prompts, "Prompt has not appeared in this batch."),
        ("Placeholder and meta-text removal", not any(token in final_user.lower() for token in ["placeholder", "lorem", "todo", "insert"]), "No placeholder text detected."),
        ("Target-scope signal", "assistant" in row.expected_behavior.lower() or "onboardai" in row.quality_notes.lower(), "Row targets assistant behavior."),
        ("Helper-scope policy", "human" in row.expected_behavior.lower() or "route" in row.expected_behavior.lower(), "Row preserves human handoff boundaries."),
        ("Unsupported-primary policy", "invent" not in row.expected_behavior.lower(), "Row does not reward unsupported invention."),
        ("Split intent", row.split in {"train", "validation", "test"}, "Split is allowed."),
        ("Leakage risk", not any(token in (final_user + row.expected_behavior).lower() for token in ["api_key", "secret", "password", "ssn"]), "No obvious secret or PII leakage."),
        ("Low-quality or synthetic pattern detection", len(set(final_user.lower().split())) >= 8, "Text has enough lexical variety."),
        ("Gold reason quality", len(row.gold_reasoning.split()) >= 14, "Gold reasoning is meaningful."),
        ("Train/test leakage", not (row.split == "test" and "train" in final_user.lower()), "No obvious split leakage."),
        ("Company-data privacy", "<" not in row.source_trace and "private customer" not in row.source_trace.lower(), "Source trace avoids private customer data."),
        ("Evaluation coverage", row.label in ALLOWED_LABELS, "Label contributes to coverage accounting."),
    ]
    seen_prompts.add(prompt_key)
    return [
        {"gate": gate, "passed": bool(passed), "reason": reason if passed else f"Failed: {reason}"}
        for gate, passed, reason in gate_results
    ]


def _create_artifact(
    conn: sqlite3.Connection,
    organization_id: str,
    project_id: str | None,
    job_id: str | None,
    label: str,
    kind: str,
    content: str,
) -> str:
    artifact_id = new_id("art")
    preview = content[:900].strip()
    storage_uri = f"artifact://{artifact_id}"
    conn.execute(
        """
        INSERT INTO artifacts (
            id, organization_id, project_id, job_id, label, kind, content,
            preview, storage_uri, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            artifact_id,
            organization_id,
            project_id,
            job_id,
            label,
            kind,
            content,
            preview,
            storage_uri,
            utc_now(),
        ),
    )
    return artifact_id


def _ensure_pipeline(
    conn: sqlite3.Connection,
    organization_id: str,
    project_id: str | None,
    profile: Dict[str, Any],
) -> str:
    existing = _fetch_one(
        conn,
        "SELECT id FROM dataset_pipelines WHERE organization_id = ? AND project_id IS ? ORDER BY created_at DESC LIMIT 1",
        (organization_id, project_id),
    )
    if existing:
        return existing["id"]
    spec = build_dataset_pipeline(profile)
    pipeline_id = new_id("pipe")
    now = utc_now()
    conn.execute(
        """
        INSERT INTO dataset_pipelines (
            id, organization_id, project_id, name, status, spec_json, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            pipeline_id,
            organization_id,
            project_id,
            f"{spec.company_name} dataset pipeline",
            "active",
            _json(asdict(spec)),
            now,
            now,
        ),
    )
    return pipeline_id


def _complete_onboarding_job(conn: sqlite3.Connection, job: sqlite3.Row) -> Dict[str, Any]:
    payload = _load_json(job["payload_json"], {})
    profile = payload.get("profile") if isinstance(payload.get("profile"), dict) else payload
    result = run_onboarding(profile)
    run_id = new_id("run")
    conn.execute(
        """
        INSERT INTO onboarding_runs (
            id, organization_id, project_id, job_id, status, summary,
            payload_json, result_json, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            job["organization_id"],
            job["project_id"],
            job["id"],
            result.get("status", "completed"),
            result.get("summary", ""),
            _json(profile),
            _json(result),
            utc_now(),
        ),
    )
    for artifact in result.get("artifacts", []):
        label = str(artifact.get("label") or "Artifact")
        kind = str(artifact.get("kind") or "text")
        preview = str(artifact.get("preview") or "")
        if preview:
            _create_artifact(conn, job["organization_id"], job["project_id"], job["id"], label, kind, preview)
    _ensure_pipeline(conn, job["organization_id"], job["project_id"], profile)
    usage_event(conn, job["organization_id"], job["project_id"], "onboarding_runs", 1)
    return {
        "onboardingRunId": run_id,
        "summary": result.get("summary"),
        "status": result.get("status"),
        "artifactCount": len(result.get("artifacts", [])),
    }


def _complete_dataset_batch_job(conn: sqlite3.Connection, job: sqlite3.Row) -> Dict[str, Any]:
    payload = _load_json(job["payload_json"], {})
    profile = payload.get("profile") if isinstance(payload.get("profile"), dict) else {}
    provider = str(payload.get("provider") or "local").lower()
    requested_rows = int(payload.get("requestedRows") or 8)
    pipeline_id = _ensure_pipeline(conn, job["organization_id"], job["project_id"], profile)
    adapter = provider_adapter(provider)
    generated_rows = adapter.generate_rows(profile, requested_rows)
    batch_id = new_id("batch")
    now = utc_now()
    conn.execute(
        """
        INSERT INTO dataset_batches (
            id, pipeline_id, organization_id, project_id, status, provider,
            requested_rows, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            batch_id,
            pipeline_id,
            job["organization_id"],
            job["project_id"],
            "running",
            provider,
            requested_rows,
            now,
            now,
        ),
    )

    accepted = 0
    rejected = 0
    rejection_reasons: Dict[str, int] = {}
    label_counts: Dict[str, int] = {}
    seen_prompts: set[str] = set()
    export_rows: List[Dict[str, Any]] = []

    for generated in generated_rows:
        gate_results = run_quality_gates(generated, seen_prompts)
        failed = [item for item in gate_results if not item["passed"]]
        status = "accepted" if not failed else "rejected"
        rejection_reason = "; ".join(item["gate"] for item in failed) if failed else None
        if status == "accepted":
            accepted += 1
        else:
            rejected += 1
            rejection_reasons[rejection_reason or "quality gates"] = rejection_reasons.get(rejection_reason or "quality gates", 0) + 1
        label_counts[generated.label] = label_counts.get(generated.label, 0) + 1
        row_id = new_id("row")
        conn.execute(
            """
            INSERT INTO dataset_rows (
                id, batch_id, organization_id, project_id, split, label,
                prompt_json, expected_behavior, gold_reasoning, source_trace,
                quality_notes, gate_results_json, status, rejection_reason,
                provider, token_estimate, cost_estimate, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row_id,
                batch_id,
                job["organization_id"],
                job["project_id"],
                generated.split,
                generated.label,
                _json(generated.messages),
                generated.expected_behavior,
                generated.gold_reasoning,
                generated.source_trace,
                generated.quality_notes,
                _json(gate_results),
                status,
                rejection_reason,
                provider,
                generated.token_estimate,
                generated.cost_estimate,
                utc_now(),
            ),
        )
        for gate in gate_results:
            conn.execute(
                """
                INSERT INTO quality_gate_results (
                    id, row_id, gate, passed, reason, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (new_id("gate"), row_id, gate["gate"], 1 if gate["passed"] else 0, gate["reason"], utc_now()),
            )
        if status == "accepted":
            export_rows.append(
                {
                    "messages": generated.messages,
                    "label": generated.label,
                    "expected_behavior": generated.expected_behavior,
                    "gold_reasoning": generated.gold_reasoning,
                    "split": generated.split,
                    "source_trace": generated.source_trace,
                }
            )

    pass_rate = accepted / max(1, len(generated_rows))
    weak_labels = [label for label, count in label_counts.items() if count < 2]
    report = {
        "acceptedRows": accepted,
        "rejectedRows": rejected,
        "passRate": round(pass_rate, 4),
        "rejectionReasons": rejection_reasons,
        "weakLabels": weak_labels,
        "coverageGaps": [label for label in ALLOWED_LABELS if label not in label_counts],
        "costPerAcceptedRow": 0 if accepted else None,
        "nextBatchPlan": [
            "Increase coverage for weak labels.",
            "Review rejected rows before changing generator specs.",
            "Keep local/offline generation for dry runs and switch providers only after keys are configured.",
        ],
    }
    status = "completed" if rejected == 0 else "needs_review"
    conn.execute(
        """
        UPDATE dataset_batches
        SET status = ?, accepted_rows = ?, rejected_rows = ?, pass_rate = ?,
            report_json = ?, updated_at = ?
        WHERE id = ?
        """,
        (status, accepted, rejected, pass_rate, _json(report), utc_now(), batch_id),
    )
    jsonl = "\n".join(json.dumps(row, sort_keys=True) for row in export_rows)
    _create_artifact(conn, job["organization_id"], job["project_id"], job["id"], "Accepted dataset export", "jsonl", jsonl)
    _create_artifact(conn, job["organization_id"], job["project_id"], job["id"], "Dataset batch report", "json", json.dumps(report, indent=2))
    usage_event(conn, job["organization_id"], job["project_id"], "generated_rows", len(generated_rows), {"provider": provider})
    usage_event(conn, job["organization_id"], job["project_id"], "accepted_rows", accepted, {"provider": provider})
    return {
        "batchId": batch_id,
        "pipelineId": pipeline_id,
        "status": status,
        "acceptedRows": accepted,
        "rejectedRows": rejected,
        "passRate": round(pass_rate, 4),
        "report": report,
    }


def run_next_job(limit: int = 1, organization_id: str | None = None) -> Dict[str, Any]:
    init_db()
    processed: List[Dict[str, Any]] = []
    with connect() as conn:
        for _ in range(max(1, limit)):
            if organization_id:
                job = _fetch_one(
                    conn,
                    """
                    SELECT * FROM jobs
                    WHERE status = 'queued' AND organization_id = ?
                    ORDER BY created_at ASC
                    LIMIT 1
                    """,
                    (organization_id,),
                )
            else:
                job = _fetch_one(
                    conn,
                    "SELECT * FROM jobs WHERE status = 'queued' ORDER BY created_at ASC LIMIT 1",
                )
            if not job:
                break
            now = utc_now()
            conn.execute(
                "UPDATE jobs SET status = 'running', attempts = attempts + 1, started_at = ?, updated_at = ? WHERE id = ?",
                (now, now, job["id"]),
            )
            try:
                if job["type"] == "onboarding":
                    result = _complete_onboarding_job(conn, job)
                elif job["type"] == "dataset_batch":
                    result = _complete_dataset_batch_job(conn, job)
                else:
                    raise SaasError(400, f"Unsupported job type: {job['type']}")
                status = "completed" if result.get("status") != "needs_review" else "needs_review"
                conn.execute(
                    "UPDATE jobs SET status = ?, result_json = ?, completed_at = ?, updated_at = ? WHERE id = ?",
                    (status, _json(result), utc_now(), utc_now(), job["id"]),
                )
                audit_log(conn, job["organization_id"], job["created_by"], "job.completed", "job", job["id"], {"status": status})
                processed.append({"id": job["id"], "status": status, "result": result})
            except Exception as exc:  # noqa: BLE001
                attempts = int(job["attempts"] or 0) + 1
                next_status = "failed" if attempts >= int(job["max_attempts"] or 3) else "queued"
                conn.execute(
                    "UPDATE jobs SET status = ?, error = ?, updated_at = ? WHERE id = ?",
                    (next_status, str(exc), utc_now(), job["id"]),
                )
                audit_log(conn, job["organization_id"], job["created_by"], "job.failed", "job", job["id"], {"error": str(exc)})
                processed.append({"id": job["id"], "status": next_status, "error": str(exc)})
    return {"processed": processed, "count": len(processed)}


def get_job(token: str, job_id: str) -> Dict[str, Any]:
    actor = require_actor(token)
    with connect() as conn:
        job = _fetch_one(conn, "SELECT * FROM jobs WHERE id = ?", (job_id,))
        if not job:
            raise SaasError(404, "Job was not found.")
        _membership(conn, actor, job["organization_id"])
        artifacts = _fetch_all(conn, "SELECT * FROM artifacts WHERE job_id = ? ORDER BY created_at ASC", (job_id,))
        return {"job": _job_public(job), "artifacts": [_artifact_public(row) for row in artifacts]}


def get_artifact(token: str, artifact_id: str) -> Dict[str, Any]:
    actor = require_actor(token)
    with connect() as conn:
        artifact = _fetch_one(conn, "SELECT * FROM artifacts WHERE id = ?", (artifact_id,))
        if not artifact:
            raise SaasError(404, "Artifact was not found.")
        _membership(conn, actor, artifact["organization_id"])
        return {
            **_artifact_public(artifact),
            "content": artifact["content"],
        }


def export_dataset_batch(token: str, batch_id: str) -> Dict[str, Any]:
    actor = require_actor(token)
    with connect() as conn:
        batch = _fetch_one(conn, "SELECT * FROM dataset_batches WHERE id = ?", (batch_id,))
        if not batch:
            raise SaasError(404, "Dataset batch was not found.")
        _membership(conn, actor, batch["organization_id"])
        rows = _fetch_all(
            conn,
            "SELECT * FROM dataset_rows WHERE batch_id = ? AND status = 'accepted' ORDER BY created_at ASC",
            (batch_id,),
        )
        export_rows = [
            {
                "messages": _load_json(row["prompt_json"], []),
                "label": row["label"],
                "expected_behavior": row["expected_behavior"],
                "gold_reasoning": row["gold_reasoning"],
                "split": row["split"],
                "source_trace": row["source_trace"],
            }
            for row in rows
        ]
        return {
            "batchId": batch_id,
            "format": "jsonl",
            "rowCount": len(export_rows),
            "content": "\n".join(json.dumps(row, sort_keys=True) for row in export_rows),
        }


def review_dataset_row(token: str, row_id: str, decision: str) -> Dict[str, Any]:
    actor = require_actor(token)
    if decision not in {"accepted", "rejected"}:
        raise SaasError(400, "Decision must be accepted or rejected.")
    with connect() as conn:
        row = _fetch_one(conn, "SELECT * FROM dataset_rows WHERE id = ?", (row_id,))
        if not row:
            raise SaasError(404, "Dataset row was not found.")
        require_role(conn, actor, row["organization_id"], {"owner", "admin", "operator"})
        conn.execute(
            "UPDATE dataset_rows SET status = ?, rejection_reason = ? WHERE id = ?",
            (decision, None if decision == "accepted" else "Human reviewer rejected the row.", row_id),
        )
        audit_log(conn, row["organization_id"], actor.user_id, "dataset_row.review", "dataset_row", row_id, {"decision": decision})
        return {"id": row_id, "status": decision}


def save_provider_key(token: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    actor = require_actor(token)
    provider = str(payload.get("provider") or "").strip().lower()
    secret = str(payload.get("secret") or "").strip()
    organization_id = str(payload.get("organizationId") or "")
    if provider not in PROVIDER_NAMES or provider == "local":
        raise SaasError(400, "Choose an external provider.")
    if len(secret) < 8:
        raise SaasError(400, "Provider secret is too short.")
    with connect() as conn:
        if not organization_id:
            organization_id, _ = _default_org_project(conn, actor)
        require_role(conn, actor, organization_id, {"owner", "admin"})
        now = utc_now()
        masked = secret[:4] + "..." + secret[-4:]
        conn.execute(
            """
            INSERT INTO provider_keys (
                id, organization_id, provider, secret_hash, masked_value,
                configured_by, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(organization_id, provider)
            DO UPDATE SET secret_hash = excluded.secret_hash,
                          masked_value = excluded.masked_value,
                          configured_by = excluded.configured_by,
                          updated_at = excluded.updated_at
            """,
            (
                new_id("prov"),
                organization_id,
                provider,
                _hash_token(secret),
                masked,
                actor.user_id,
                now,
                now,
            ),
        )
        audit_log(conn, organization_id, actor.user_id, "provider_key.upsert", "provider", provider, {"provider": provider})
        return {"provider": provider, "configured": True, "maskedValue": masked}


def create_api_key(token: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    actor = require_actor(token)
    organization_id = str(payload.get("organizationId") or "")
    name = str(payload.get("name") or "Default API key").strip()
    role = str(payload.get("role") or "operator").strip()
    if role not in ROLES:
        raise SaasError(400, "Invalid API key role.")
    raw_key = "oa_" + secrets.token_urlsafe(32)
    prefix = raw_key[:10]
    with connect() as conn:
        if not organization_id:
            organization_id, _ = _default_org_project(conn, actor)
        require_role(conn, actor, organization_id, {"owner", "admin"})
        key_id = new_id("key")
        conn.execute(
            """
            INSERT INTO api_keys (
                id, organization_id, name, key_hash, prefix, role,
                created_by, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (key_id, organization_id, name, _hash_token(raw_key), prefix, role, actor.user_id, utc_now()),
        )
        audit_log(conn, organization_id, actor.user_id, "api_key.create", "api_key", key_id, {"role": role})
        return {"id": key_id, "name": name, "prefix": prefix, "role": role, "secret": raw_key}


def deployment_health() -> Dict[str, Any]:
    init_db()
    with connect() as conn:
        job_counts = {
            row["status"]: row["count"]
            for row in _fetch_all(conn, "SELECT status, COUNT(*) AS count FROM jobs GROUP BY status")
        }
        return {
            "status": "ok",
            "environment": APP_ENV,
            "database": "sqlite",
            "databasePath": "configured",
            "jobCounts": job_counts,
            "providers": PROVIDER_NAMES,
            "billingAdapter": "mock" if not os.environ.get("STRIPE_SECRET_KEY") else "stripe-ready",
            "generatedAt": utc_now(),
        }


def seed_demo() -> Dict[str, Any]:
    """Create a local dev account only when no users exist."""
    init_db()
    with connect() as conn:
        existing = _fetch_one(conn, "SELECT COUNT(*) AS count FROM users")
        if existing and int(existing["count"]) > 0:
            return {"created": False, "message": "Seed skipped because users already exist."}
    return signup(
        {
            "email": "owner@onboardai.local",
            "password": "onboardai-local",
            "name": "OnboardAI Owner",
            "organizationName": "OnboardAI Demo Workspace",
        }
    )
