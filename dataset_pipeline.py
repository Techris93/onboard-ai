"""
Fine-tuning dataset pipeline planning for OnboardAI.

The runtime is deterministic by default so the backend can produce useful
artifacts even when no paid generator provider is configured.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

REPO_DIR = Path(__file__).resolve().parent
STATE_DIR = REPO_DIR / "state" / "dataset_pipeline_api"


QUALITY_GATES = [
    "Schema validity",
    "Role correctness",
    "Final user turn quality",
    "Allowed labels",
    "Canonical order",
    "Duplicate prompt detection",
    "Placeholder and meta-text removal",
    "Target-scope signal",
    "Helper-scope policy",
    "Unsupported-primary policy",
    "Split intent",
    "Leakage risk",
    "Low-quality or synthetic pattern detection",
    "Gold reason quality",
    "Train/test leakage",
    "Company-data privacy",
    "Evaluation coverage",
]


@dataclass
class DatasetPipelineSpec:
    company_name: str
    target_model_family: str
    orchestrator: str
    generator_model: str
    objective: str
    batch_plan: List[str]
    generator_contract: List[str]
    quality_gates: List[str]
    archive_policy: List[str]
    improvement_loop: List[str]
    recommended_agents: List[str]


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return cleaned or "dataset-pipeline"


def build_dataset_pipeline(profile: Dict[str, Any]) -> DatasetPipelineSpec:
    company_name = str(profile.get("companyName") or "Company").strip() or "Company"
    use_case = str(profile.get("useCase") or "customer-support").replace("-", " ")
    industry = str(profile.get("industry") or "Software / SaaS").strip()
    compliance = profile.get("compliance") if isinstance(profile.get("compliance"), list) else []
    sources = profile.get("sources") if isinstance(profile.get("sources"), list) else []

    governance_note = (
        f"Respect {', '.join(str(item) for item in compliance)} controls."
        if compliance
        else "Use baseline privacy, security, and source-authority controls."
    )
    source_note = (
        f"Prioritize {len(sources)} selected source surfaces before generating rows."
        if sources
        else "Collect source authority before generation starts."
    )

    return DatasetPipelineSpec(
        company_name=company_name,
        target_model_family="5B to 15B expert language model or domain assistant",
        orchestrator="Codex Orchestrator",
        generator_model="Provider-neutral generator model, with DeepSeek v4 Pro as a low-cost example",
        objective=(
            f"Prepare high-quality fine-tuning data for {company_name}'s {use_case} workflow "
            f"in the {industry} context."
        ),
        batch_plan=[
            "Define target scope, case families, allowed labels, and exclusion boundaries.",
            "Reserve train, validation, and hard-evaluation splits before rows are generated.",
            "Set batch quotas by scenario, label, difficulty, and risk level.",
            source_note,
        ],
        generator_contract=[
            "Follow the Codex-authored row spec exactly and do not invent policy beyond the spec.",
            "Write natural, company-relevant turns with clear intent and no placeholder language.",
            "Include gold reasoning, quality notes, label rationale, and traceability metadata.",
            "Return rows in the approved schema so quality gates can reject weak rows automatically.",
        ],
        quality_gates=QUALITY_GATES,
        archive_policy=[
            "Keep accepted rows, rejected rows, rejection reasons, and batch reports together.",
            "Preserve batch prompts, generator specs, evaluation notes, and quality-gate versions.",
            "Never publish private source content, secrets, or customer-identifying data to the public site.",
            governance_note,
        ],
        improvement_loop=[
            "Summarize rejected patterns after each batch.",
            "Promote strong accepted rows into reference examples for the next generator spec.",
            "Tighten gates when weak rows pass, and relax only when a gate blocks valid target behavior.",
            "Produce a next-batch plan with lower cost, stronger coverage, and clearer eval targets.",
        ],
        recommended_agents=[
            "AI Engineer",
            "Backend Architect",
            "Security Engineer",
            "Code Reviewer",
            "Technical Writer",
        ],
    )


def render_dataset_pipeline_markdown(profile: Dict[str, Any]) -> str:
    spec = build_dataset_pipeline(profile)
    created_at = datetime.now().astimezone().isoformat()

    def bullet_block(items: List[str]) -> List[str]:
        return [f"- {item}" for item in items]

    lines = [
        f"# {spec.company_name} Fine-Tuning Dataset Pipeline",
        "",
        "## Executive Summary",
        "",
        spec.objective,
        "",
        f"- Target model family: {spec.target_model_family}",
        f"- Orchestrator: {spec.orchestrator}",
        f"- Generator model: {spec.generator_model}",
        f"- Created at: {created_at}",
        "",
        "## Batch Plan",
        "",
        *bullet_block(spec.batch_plan),
        "",
        "## Generator Contract",
        "",
        *bullet_block(spec.generator_contract),
        "",
        "## Quality Gates",
        "",
        *bullet_block(spec.quality_gates),
        "",
        "## Raw Batch Archive Policy",
        "",
        *bullet_block(spec.archive_policy),
        "",
        "## Iterative Improvement Loop",
        "",
        *bullet_block(spec.improvement_loop),
        "",
        "## Recommended Specialist Roles",
        "",
        *bullet_block(spec.recommended_agents),
        "",
    ]
    return "\n".join(lines)


def write_dataset_pipeline_artifacts(profile: Dict[str, Any], run_dir: Path) -> Dict[str, str]:
    spec = build_dataset_pipeline(profile)
    slug = slugify(str(profile.get("companyName") or "company"))
    markdown_path = run_dir / f"{slug}-dataset-pipeline.md"
    json_path = run_dir / f"{slug}-dataset-pipeline.json"

    markdown_path.write_text(render_dataset_pipeline_markdown(profile), encoding="utf-8")
    json_path.write_text(json.dumps(asdict(spec), indent=2), encoding="utf-8")

    return {
        "markdown": str(markdown_path),
        "json": str(json_path),
    }


def _public_artifact_path(path: str) -> str:
    return f"artifact://{Path(path).name}"


def run_dataset_pipeline_plan(payload: Dict[str, Any]) -> Dict[str, Any]:
    profile = payload.get("profile") if isinstance(payload.get("profile"), dict) else payload
    company_name = str(profile.get("companyName") or "Company").strip() or "Company"
    run_id = f"{datetime.now().strftime('%Y%m%d%H%M%S')}-{slugify(company_name)}"
    run_dir = STATE_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    paths = write_dataset_pipeline_artifacts(profile, run_dir)
    spec = build_dataset_pipeline(profile)
    response = {
        "runId": run_id,
        "status": "completed",
        "createdAt": datetime.now().astimezone().isoformat(),
        "companyName": company_name,
        "targetModelFamily": spec.target_model_family,
        "orchestrator": spec.orchestrator,
        "generatorModel": spec.generator_model,
        "qualityGateCount": len(spec.quality_gates),
        "recommendedAgents": spec.recommended_agents,
        "artifacts": [
            {
                "label": "Dataset pipeline plan",
                "kind": "markdown",
                "path": _public_artifact_path(paths["markdown"]),
            },
            {
                "label": "Dataset pipeline spec",
                "kind": "json",
                "path": _public_artifact_path(paths["json"]),
            },
        ],
        "runDirectory": f"run://{run_id}",
    }
    (run_dir / "response.json").write_text(json.dumps(response, indent=2), encoding="utf-8")
    return response


def load_dataset_pipeline_run(run_id: str) -> Dict[str, Any] | None:
    path = STATE_DIR / run_id / "response.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
