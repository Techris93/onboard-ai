"""
Backend runtime for OnboardAI onboarding intake execution.

This module validates intake payloads, stores normalized runs locally, and
bridges the intake to llm-kb so the website can return real artifacts instead
of only a static planning preview.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


REPO_DIR = Path(__file__).resolve().parent
STATE_DIR = REPO_DIR / "state" / "onboarding_api"
DEFAULT_LLM_KB_BIN = Path(
    os.environ.get("LLM_KB_BIN", "/Users/chrixchange/llm-knowledge-base/llm-kb")
).expanduser()

SOURCE_LABELS = {
    "product-platform": "Platform",
    "product-pricing": "Pricing",
    "product-security": "Security",
    "product-changelog": "Changelog",
    "resources-documentation": "Documentation",
    "resources-api-reference": "API Reference",
    "resources-community": "Community",
    "resources-blog": "Blog",
    "company-about": "About",
    "company-careers": "Careers",
    "company-contact": "Contact",
    "company-legal": "Legal",
}

USE_CASE_LABELS = {
    "customer-support": "Customer support assistant",
    "internal-copilot": "Internal knowledge copilot",
    "product-api-assistant": "Product and API assistant",
    "sales-enablement": "Sales enablement assistant",
    "operations-assistant": "Operations and compliance assistant",
}

INTEGRATION_LABELS = {
    "advisory": "Static pilot mode",
    "backend-worker": "Backend worker mode",
    "local-bridge": "Local bridge mode",
}

DELIVERY_SYSTEM_LABELS = {
    "website": "Website",
    "help-center": "Help center",
    "developer-portal": "Developer portal",
    "api-gateway": "API gateway",
    "crm": "CRM / sales ops",
    "internal-wiki": "Internal wiki",
    "support-desk": "Support desk",
    "status-feed": "Status / changelog feed",
}


@dataclass
class ArtifactRecord:
    label: str
    kind: str
    path: str
    preview: str


@dataclass
class CommandRecord:
    step: str
    command: str
    ok: bool
    exit_code: int
    summary: str
    stdout_preview: str
    stderr_preview: str
    parsed: Dict[str, str]


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return cleaned or "run"


def _now() -> str:
    return datetime.now().astimezone().isoformat()


def _trim(text: str, limit: int = 1000) -> str:
    cleaned = text.strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[:limit].rstrip() + "..."


def _coerce_list(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _label_values(values: List[str], lookup: Dict[str, str]) -> List[str]:
    return [lookup.get(value, value) for value in values]


def normalize_profile(payload: Dict[str, Any]) -> Dict[str, Any]:
    company_name = str(
        payload.get("companyName")
        or payload.get("company_name")
        or "Unnamed company"
    ).strip()

    return {
        "companyName": company_name or "Unnamed company",
        "industry": str(payload.get("industry") or "Software / SaaS").strip(),
        "companySize": str(payload.get("companySize") or "mid-market").strip(),
        "useCase": str(payload.get("useCase") or "customer-support").strip(),
        "stage": str(payload.get("stage") or "discovery").strip(),
        "integrationMode": str(
            payload.get("integrationMode") or "backend-worker"
        ).strip(),
        "sources": _coerce_list(payload.get("sources")),
        "compliance": _coerce_list(payload.get("compliance")),
        "systems": _coerce_list(payload.get("systems")),
    }


def _source_labels(profile: Dict[str, Any]) -> List[str]:
    return _label_values(profile["sources"], SOURCE_LABELS)


def _system_labels(profile: Dict[str, Any]) -> List[str]:
    return _label_values(profile["systems"], DELIVERY_SYSTEM_LABELS)


def _use_case_label(profile: Dict[str, Any]) -> str:
    return USE_CASE_LABELS.get(profile["useCase"], profile["useCase"])


def _integration_label(profile: Dict[str, Any]) -> str:
    return INTEGRATION_LABELS.get(
        profile["integrationMode"], profile["integrationMode"]
    )


def build_agent_task(profile: Dict[str, Any]) -> str:
    source_summary = ", ".join(_source_labels(profile)[:6]) or "core company sources"
    return (
        f"Design a {profile['industry']} onboarding workflow for {profile['companyName']} "
        f"focused on {_use_case_label(profile).lower()} with {source_summary} in "
        f"{_integration_label(profile).lower()}."
    )


def build_intake_markdown(profile: Dict[str, Any]) -> str:
    source_labels = _source_labels(profile)
    system_labels = _system_labels(profile)
    compliance = profile["compliance"] or ["Baseline controls"]

    lines = [
        f"# {profile['companyName']} Intake Packet",
        "",
        "## Program Snapshot",
        "",
        f"- Industry: {profile['industry']}",
        f"- Company size: {profile['companySize']}",
        f"- Use case: {_use_case_label(profile)}",
        f"- Rollout stage: {profile['stage']}",
        f"- Integration mode: {_integration_label(profile)}",
        "",
        "## Selected Source Surfaces",
        "",
    ]

    for item in source_labels or ["No source surfaces selected yet."]:
        lines.append(f"- {item}")

    lines.extend(["", "## Governance", ""])
    for item in compliance:
        lines.append(f"- {item}")

    lines.extend(["", "## Delivery Systems", ""])
    for item in system_labels or ["No delivery systems selected yet."]:
        lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "## Backend Intent",
            "",
            "This intake is ready for llm-kb-backed agent selection, artifact packaging, and publish-safe storage.",
            "",
        ]
    )
    return "\n".join(lines)


def build_brief_markdown(profile: Dict[str, Any], agents: List[str]) -> str:
    source_labels = _source_labels(profile)
    systems = _system_labels(profile)
    governance = profile["compliance"] or ["Baseline controls"]

    lines = [
        f"# {profile['companyName']} Onboarding Brief",
        "",
        "## Executive Summary",
        "",
        (
            f"{profile['companyName']} is being prepared for a {_integration_label(profile).lower()} "
            f"centered on {_use_case_label(profile).lower()} in the {profile['industry'].lower()} motion."
        ),
        "",
        "## Scope Priorities",
        "",
        f"- Source coverage: {', '.join(source_labels) if source_labels else 'Expand source coverage during discovery.'}",
        f"- Delivery systems: {', '.join(systems) if systems else 'Clarify launch surfaces before activation.'}",
        f"- Governance: {', '.join(governance)}",
        "",
        "## Recommended llm-kb Roles",
        "",
    ]

    for agent in agents or ["Technical Writer"]:
        lines.append(f"- {agent}")

    lines.extend(
        [
            "",
            "## Execution Notes",
            "",
            "- Keep the intake packet, agent activation brief, and published outputs aligned.",
            "- Use publish-safe artifacts for stakeholder sharing and operator dashboards.",
            "- Expand source coverage before production if pricing, legal, or support escalation paths remain incomplete.",
            "",
        ]
    )
    return "\n".join(lines)


def _artifact_from_file(label: str, kind: str, path: Path) -> ArtifactRecord:
    preview = ""
    if path.exists():
        try:
            preview = _trim(path.read_text(encoding="utf-8", errors="replace"), 900)
        except Exception:
            preview = ""
    return ArtifactRecord(label=label, kind=kind, path=str(path), preview=preview)


def _summarize_command(
    step: str,
    command: List[str],
    exit_code: int,
    stdout: str,
    stderr: str,
    parsed: Dict[str, str],
) -> str:
    if exit_code == 0:
        if step == "sync":
            return (
                f"llm-kb sync completed with {parsed.get('copied', '?')} copied files, "
                f"{parsed.get('skipped', '?')} skipped files, and {parsed.get('missing', '?')} missing patterns."
            )
        if step == "compile":
            return (
                f"llm-kb compile completed and wrote {parsed.get('sources_written', '?')} "
                f"source pages and {parsed.get('project_pages_written', '?')} project pages."
            )
        if step == "agents":
            recommended = len(parse_agent_names(stdout))
            return f"llm-kb recommended {recommended} specialist roles for this onboarding task."
        if step == "agent-start":
            selected = parsed.get("selected", "No agent selected")
            return f"llm-kb created an activation brief for {selected}."
        if step.startswith("publish"):
            return f"llm-kb published a sanitized artifact to {parsed.get('published_to', 'its publish target')}."
        if step == "file-output":
            return "llm-kb filed the onboarding brief back into its local knowledge store."

    stderr_preview = _trim(stderr or stdout or "Unknown command failure.", 260)
    return f"{step} failed with exit code {exit_code}. {stderr_preview}"


TOP_LEVEL_OUTPUT_KEYS = {
    "copied",
    "skipped",
    "missing",
    "manifest",
    "sources_written",
    "project_pages_written",
    "concept_pages_written",
    "decision_pages_written",
    "timeline_pages_written",
    "executive_pages_written",
    "index",
    "source",
    "selected",
    "key",
    "output",
    "project_root",
    "cd_command",
    "published_to",
    "redactions",
    "mode",
    "provider",
    "fallback_used",
    "note",
    "written",
    "iterations",
    "last_copied",
}


def run_llm_kb_command(step: str, args: List[str], cwd: Path) -> CommandRecord:
    command = [str(DEFAULT_LLM_KB_BIN), *args]
    completed = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
    )

    parsed: Dict[str, str] = {}
    for line in completed.stdout.splitlines():
        if line.startswith(" "):
            continue

        compact_pairs = re.findall(r"([a-z_]+)=([^\s]+)", line.strip())
        if len(compact_pairs) > 1:
            for key, value in compact_pairs:
                if key in TOP_LEVEL_OUTPUT_KEYS:
                    parsed[key] = value
            continue

        match = re.match(r"^([a-z_]+)=(.+)$", line.strip())
        if match:
            key, value = match.groups()
            if key in TOP_LEVEL_OUTPUT_KEYS:
                parsed[key] = value.strip()

    summary = _summarize_command(
        step,
        command,
        completed.returncode,
        completed.stdout,
        completed.stderr,
        parsed,
    )

    return CommandRecord(
        step=step,
        command=shlex.join(command),
        ok=completed.returncode == 0,
        exit_code=completed.returncode,
        summary=summary,
        stdout_preview=_trim(completed.stdout, 800),
        stderr_preview=_trim(completed.stderr, 500),
        parsed=parsed,
    )


def parse_agent_names(stdout: str) -> List[str]:
    agents: List[str] = []
    for line in stdout.splitlines():
        match = re.match(r"^\s*\d+\s+\|\s+([^|]+?)\s+\|", line)
        if match:
            agents.append(match.group(1).strip())
    return agents


def llm_kb_status() -> Dict[str, Any]:
    return {
        "available": DEFAULT_LLM_KB_BIN.exists(),
        "binary": str(DEFAULT_LLM_KB_BIN),
        "root": str(DEFAULT_LLM_KB_BIN.resolve().parent) if DEFAULT_LLM_KB_BIN.exists() else "",
    }


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def run_onboarding(payload: Dict[str, Any]) -> Dict[str, Any]:
    profile = normalize_profile(payload)
    created_at = _now()
    run_id = f"{datetime.now().strftime('%Y%m%d%H%M%S')}-{slugify(profile['companyName'])}"
    run_dir = ensure_dir(STATE_DIR / run_id)

    intake_json_path = run_dir / "intake.json"
    intake_markdown_path = run_dir / "intake-packet.md"
    brief_markdown_path = run_dir / "onboarding-brief.md"
    activation_path = run_dir / "agent-activation.md"
    response_path = run_dir / "response.json"

    _write_json(intake_json_path, profile)
    intake_markdown_path.write_text(build_intake_markdown(profile), encoding="utf-8")

    llm_kb = llm_kb_status()
    command_results: List[CommandRecord] = []
    artifacts = [
        _artifact_from_file("Normalized intake", "json", intake_json_path),
        _artifact_from_file("Intake packet", "markdown", intake_markdown_path),
    ]
    recommended_agents: List[str] = []
    warnings: List[str] = []

    if llm_kb["available"]:
        llm_kb_root = Path(llm_kb["root"])
        task = build_agent_task(profile)

        for step, args in [
            ("sync", ["sync"]),
            ("compile", ["compile"]),
            ("agents", ["agents", task, "--limit", "5"]),
            ("agent-start", ["agent-start", task, "--output", str(activation_path)]),
        ]:
            command_results.append(run_llm_kb_command(step, args, cwd=llm_kb_root))

        if command_results:
            recommended_agents = parse_agent_names(command_results[2].stdout_preview)
        if not recommended_agents:
            selected = command_results[-1].parsed.get("selected")
            if selected:
                recommended_agents = [selected]

        brief_markdown_path.write_text(
            build_brief_markdown(profile, recommended_agents),
            encoding="utf-8",
        )
        artifacts.append(_artifact_from_file("Onboarding brief", "markdown", brief_markdown_path))

        if activation_path.exists():
            artifacts.append(_artifact_from_file("Agent activation brief", "markdown", activation_path))

        for step, args in [
            (
                "file-output",
                [
                    "file-output",
                    str(brief_markdown_path),
                    "--into",
                    "notes",
                    "--title",
                    f"{slugify(profile['companyName'])}-onboarding-brief",
                ],
            ),
            (
                "publish-brief",
                [
                    "publish",
                    str(brief_markdown_path),
                    "--target",
                    "outputs",
                    "--into",
                    "onboardai",
                    "--title",
                    f"{slugify(profile['companyName'])}-onboarding-brief",
                ],
            ),
            (
                "publish-intake",
                [
                    "publish",
                    str(intake_markdown_path),
                    "--target",
                    "outputs",
                    "--into",
                    "onboardai",
                    "--title",
                    f"{slugify(profile['companyName'])}-intake-packet",
                ],
            ),
        ]:
            command_results.append(run_llm_kb_command(step, args, cwd=llm_kb_root))

        for record in command_results[-2:]:
            published_to = record.parsed.get("published_to")
            output_path = record.stdout_preview.splitlines()[0].strip() if record.stdout_preview else ""
            if output_path and Path(output_path).exists():
                artifacts.append(
                    _artifact_from_file(
                        f"{record.step} output",
                        "markdown",
                        Path(output_path),
                    )
                )
            if published_to and Path(published_to).exists():
                artifacts.append(
                    _artifact_from_file(
                        f"{record.step} publish target",
                        "markdown",
                        Path(published_to),
                    )
                )
    else:
        warnings.append(
            "llm-kb was not found on this machine, so the run stayed in packet-only mode."
        )
        brief_markdown_path.write_text(
            build_brief_markdown(profile, recommended_agents),
            encoding="utf-8",
        )
        artifacts.append(_artifact_from_file("Onboarding brief", "markdown", brief_markdown_path))

    critical_steps = {"agents", "agent-start", "publish-brief", "publish-intake"}
    critical_results = [item for item in command_results if item.step in critical_steps]
    status = "completed" if critical_results and all(item.ok for item in critical_results) else (
        "partial" if command_results else "packet-only"
    )

    response = {
        "runId": run_id,
        "status": status,
        "createdAt": created_at,
        "companyName": profile["companyName"],
        "integrationMode": profile["integrationMode"],
        "summary": (
            f"{profile['companyName']} now has a stored onboarding run with "
            f"{len(recommended_agents)} llm-kb-recommended roles and {len(artifacts)} tracked artifacts."
        ),
        "recommendedAgents": recommended_agents,
        "artifacts": [asdict(item) for item in artifacts],
        "commandResults": [asdict(item) for item in command_results],
        "warnings": warnings,
        "llmKb": llm_kb,
        "runDirectory": str(run_dir),
        "resultUrl": f"/api/runs/{run_id}",
    }
    _write_json(response_path, response)
    return response


def load_run(run_id: str) -> Dict[str, Any] | None:
    path = STATE_DIR / run_id / "response.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
