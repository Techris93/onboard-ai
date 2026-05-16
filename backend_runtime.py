"""
Backend runtime for OnboardAI onboarding intake execution.

This module validates intake payloads, stores normalized runs locally, and
bridges the intake to the specialist workspace so the website can return real
artifacts instead of only a static planning preview.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from dataset_pipeline import write_dataset_pipeline_artifacts


REPO_DIR = Path(__file__).resolve().parent
STATE_DIR = REPO_DIR / "state" / "onboarding_api"
LLM_KB_WORKSPACE = Path(
    os.environ.get("LLM_KB_ROOT", str(REPO_DIR / "state" / "llm_kb_workspace"))
).expanduser()
DEFAULT_LLM_KB_BIN = Path(
    os.environ.get("LLM_KB_BIN", "/Users/chrixchange/llm-knowledge-base/llm-kb")
).expanduser()

SOURCE_LABELS = {
    "product-platform": "Platform",
    "product-ai-onboarding": "AI Onboarding",
    "product-dataset-pipeline": "Fine-Tuning Dataset Pipeline",
    "product-elm-readiness": "ELM Readiness",
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
    "fine-tuning-dataset": "Fine-tuning dataset pipeline",
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
    label: str
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


def ensure_llm_kb_workspace() -> Path:
    workspace = ensure_dir(LLM_KB_WORKSPACE)
    for rel in [
        "config",
        "raw",
        "wiki/projects",
        "wiki/sources",
        "wiki/concepts",
        "wiki/indexes",
        "wiki/agents",
        "outputs/onboardai",
        "state",
    ]:
        ensure_dir(workspace / rel)

    sources_config = workspace / "config" / "sources.toml"
    if not sources_config.exists():
        sources_config.write_text("[projects]\n", encoding="utf-8")

    return workspace


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
    if profile["useCase"] == "fine-tuning-dataset" or "product-dataset-pipeline" in profile["sources"]:
        return (
            f"Design a fine-tuning dataset generation workflow for {profile['companyName']} "
            f"focused on {_use_case_label(profile).lower()} with {source_summary}. "
            "Include Codex orchestration, generator model instructions, quality gates, "
            "rejected-row handling, and 5B to 15B expert model readiness."
        )
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
            "This intake is ready for specialist-agent selection, artifact packaging, and publish-safe storage.",
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
        "## Recommended Specialist Roles",
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


def public_llm_kb_status() -> Dict[str, Any]:
    status = llm_kb_status()
    return {
        "available": status["available"],
        "binary": "configured" if status["available"] else "unavailable",
        "root": "private delivery workspace",
    }


def _sanitize_public_text(value: str) -> str:
    sanitized = value.replace(str(REPO_DIR), "<workspace>")
    sanitized = sanitized.replace(str(LLM_KB_WORKSPACE), "<delivery-workspace>")
    sanitized = re.sub(r"/Users/[^\s\"']+", "<local-path>", sanitized)
    return sanitized


def _public_artifact_record(record: ArtifactRecord) -> Dict[str, Any]:
    payload = asdict(record)
    payload["path"] = f"artifact://{Path(record.path).name}"
    payload["preview"] = _sanitize_public_text(record.preview)
    return payload


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
                f"Source preparation completed with {parsed.get('copied', '?')} updated files, "
                f"{parsed.get('skipped', '?')} unchanged files, and {parsed.get('missing', '?')} missing source patterns."
            )
        if step == "compile":
            return (
                f"Knowledge compilation completed and wrote {parsed.get('sources_written', '?')} "
                f"source pages and {parsed.get('project_pages_written', '?')} project pages."
            )
        if step == "agents":
            recommended = len(parse_agent_names(stdout))
            return f"Specialist routing recommended {recommended} delivery roles for this onboarding task."
        if step == "agent-start":
            selected = parsed.get("selected", "No agent selected")
            return f"An activation brief was created for {selected}."
        if step.startswith("publish"):
            return "A publish-safe artifact was prepared for controlled sharing."
        if step == "file-output":
            return "The onboarding brief was filed into the delivery workspace."

    stderr_preview = _trim(stderr or stdout or "Unknown command failure.", 260)
    return f"{_artifact_label_for_step(step)} needs attention. {stderr_preview}"


def _artifact_label_for_step(step: str) -> str:
    labels = {
        "sync": "Source preparation",
        "compile": "Knowledge compilation",
        "agents": "Specialist routing",
        "agent-start": "Activation brief",
        "file-output": "Workspace filing",
        "publish-brief": "Published onboarding brief",
        "publish-dataset-pipeline": "Published dataset pipeline",
        "publish-intake": "Published intake packet",
    }
    return labels.get(step, step.replace("-", " ").title())


def _public_command_record(record: CommandRecord) -> Dict[str, Any]:
    payload = asdict(record)
    payload["step"] = slugify(record.label)
    payload["stdout_preview"] = _sanitize_public_text(record.stdout_preview)
    payload["stderr_preview"] = _sanitize_public_text(record.stderr_preview)
    payload["parsed"] = {
        key: _sanitize_public_text(value) for key, value in record.parsed.items()
    }
    return payload


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
    env = os.environ.copy()
    env["LLM_KB_ROOT"] = str(cwd)
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=env,
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
        label=_artifact_label_for_step(step),
        command=f"{_artifact_label_for_step(step)} operator action",
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
    workspace = ensure_llm_kb_workspace()
    return {
        "available": DEFAULT_LLM_KB_BIN.exists(),
        "binary": str(DEFAULT_LLM_KB_BIN),
        "root": str(workspace),
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
    dataset_pipeline_paths = write_dataset_pipeline_artifacts(profile, run_dir)
    response_path = run_dir / "response.json"

    _write_json(intake_json_path, profile)
    intake_markdown_path.write_text(build_intake_markdown(profile), encoding="utf-8")

    llm_kb = llm_kb_status()
    command_results: List[CommandRecord] = []
    artifacts = [
        _artifact_from_file("Normalized intake", "json", intake_json_path),
        _artifact_from_file("Intake packet", "markdown", intake_markdown_path),
        _artifact_from_file("Fine-tuning dataset pipeline", "markdown", Path(dataset_pipeline_paths["markdown"])),
        _artifact_from_file("Dataset pipeline spec", "json", Path(dataset_pipeline_paths["json"])),
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
                "publish-dataset-pipeline",
                [
                    "publish",
                    str(dataset_pipeline_paths["markdown"]),
                    "--target",
                    "outputs",
                    "--into",
                    "onboardai",
                    "--title",
                    f"{slugify(profile['companyName'])}-dataset-pipeline",
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

        for record in [item for item in command_results if item.step.startswith("publish")]:
            published_to = record.parsed.get("published_to")
            output_path = record.stdout_preview.splitlines()[0].strip() if record.stdout_preview else ""
            if output_path and Path(output_path).exists():
                artifacts.append(
                    _artifact_from_file(
                        f"{_artifact_label_for_step(record.step)} source",
                        "markdown",
                        Path(output_path),
                    )
                )
            if published_to and Path(published_to).exists():
                artifacts.append(
                    _artifact_from_file(
                        _artifact_label_for_step(record.step),
                        "markdown",
                        Path(published_to),
                    )
                )
    else:
        warnings.append(
            "The specialist workspace is not available in this environment, so the run returned packet artifacts only."
        )
        brief_markdown_path.write_text(
            build_brief_markdown(profile, recommended_agents),
            encoding="utf-8",
        )
        artifacts.append(_artifact_from_file("Onboarding brief", "markdown", brief_markdown_path))

    critical_steps = {"agents", "agent-start", "publish-brief", "publish-dataset-pipeline", "publish-intake"}
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
            f"{profile['companyName']} has a delivery-ready onboarding package with "
            f"{len(recommended_agents)} recommended specialist roles and {len(artifacts)} tracked artifacts."
        ),
        "recommendedAgents": recommended_agents,
        "artifacts": [_public_artifact_record(item) for item in artifacts],
        "commandResults": [_public_command_record(item) for item in command_results],
        "warnings": warnings,
        "llmKb": public_llm_kb_status(),
        "runDirectory": f"run://{run_id}",
        "resultUrl": f"/api/runs/{run_id}",
    }
    _write_json(response_path, response)
    return response


def load_run(run_id: str) -> Dict[str, Any] | None:
    path = STATE_DIR / run_id / "response.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
