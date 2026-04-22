"""
Run a private public-data onboarding validation in an isolated temp workspace.

This keeps third-party test data out of the repo's tracked data files and out
of the website bundle while still exercising the real harvest/evaluate loop.

Example:
    python validate_public_company.py \
        --business-name "Acme Cloud" \
        --url https://acme.com \
        --url https://acme.com/docs \
        --url https://acme.com/pricing \
        --num-qa 12 \
        --verbose-eval
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import List


REPO_DIR = Path(__file__).resolve().parent
TEMPLATE_FILES = (
    "config.py",
    "evaluate.py",
    "harvest.py",
    "prepare.py",
    "requirements.txt",
    ".env",
    ".env.example",
    ".gitignore",
)


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "company"


def ensure_empty_workspace(workspace: Path) -> None:
    if workspace.exists():
        existing = list(workspace.iterdir())
        if existing:
            raise FileExistsError(
                f"Workspace already exists and is not empty: {workspace}"
            )
    else:
        workspace.mkdir(parents=True, exist_ok=True)


def scaffold_workspace(workspace: Path) -> None:
    ensure_empty_workspace(workspace)

    for name in TEMPLATE_FILES:
        source = REPO_DIR / name
        if source.exists():
            shutil.copy2(source, workspace / name)

    (workspace / "data").mkdir(exist_ok=True)


def write_manifest(workspace: Path, args: argparse.Namespace) -> None:
    manifest = {
        "business_name": args.business_name,
        "urls": args.url,
        "docs": args.docs,
        "depth": args.depth,
        "max_pages": args.max_pages,
        "num_qa": args.num_qa,
        "max_retries": args.max_retries,
        "retry_base_delay": args.retry_base_delay,
        "created_at": datetime.now().isoformat(),
        "source_repo": str(REPO_DIR),
        "python": sys.executable,
    }

    with open(workspace / "validation_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)


def run_step(command: List[str], cwd: Path, env: dict, dry_run: bool = False) -> None:
    print(f"\n  $ {' '.join(shlex.quote(part) for part in command)}")
    if dry_run:
        return

    subprocess.run(command, cwd=cwd, env=env, check=True)


def build_commands(args: argparse.Namespace) -> List[List[str]]:
    commands: List[List[str]] = []

    for url in args.url:
        commands.append([
            sys.executable,
            "harvest.py",
            "--url",
            url,
            "--depth",
            str(args.depth),
            "--max-pages",
            str(args.max_pages),
            "--business-name",
            args.business_name,
        ])

    for docs_path in args.docs:
        commands.append([
            sys.executable,
            "harvest.py",
            "--docs",
            docs_path,
            "--business-name",
            args.business_name,
        ])

    commands.append([
        sys.executable,
        "harvest.py",
        "--generate-qa",
        "--num-qa",
        str(args.num_qa),
    ])

    evaluate_command = [
        sys.executable,
        "evaluate.py",
        "--max-retries",
        str(args.max_retries),
        "--retry-base-delay",
        str(args.retry_base_delay),
    ]
    if args.verbose_eval:
        evaluate_command.append("--verbose")
    commands.append(evaluate_command)

    return commands


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a private public-company validation in a temp workspace."
    )
    parser.add_argument("--business-name", required=True,
                        help="Business name for the validation run")
    parser.add_argument("--url", action="append", default=[],
                        help="Public URL to ingest. Repeat for multiple pages.")
    parser.add_argument("--docs", action="append", default=[],
                        help="Optional local docs path to ingest. Repeat as needed.")
    parser.add_argument("--depth", type=int, default=0,
                        help="Harvest crawl depth per URL (default: 0)")
    parser.add_argument("--max-pages", type=int, default=1,
                        help="Harvest page cap per URL (default: 1)")
    parser.add_argument("--num-qa", type=int, default=12,
                        help="Number of generated Q&A pairs (default: 12)")
    parser.add_argument("--max-retries", type=int, default=4,
                        help="Total Gemini attempts per evaluation question")
    parser.add_argument("--retry-base-delay", type=float, default=2.0,
                        help="Initial evaluation backoff delay in seconds")
    parser.add_argument("--verbose-eval", action="store_true",
                        help="Pass --verbose through to evaluate.py")
    parser.add_argument("--workspace", type=str,
                        help="Optional empty workspace directory to use")
    parser.add_argument("--cleanup", action="store_true",
                        help="Delete the temp workspace after a successful run")
    parser.add_argument("--dry-run", action="store_true",
                        help="Scaffold the workspace and print commands without executing")

    args = parser.parse_args()

    if not args.url and not args.docs:
        parser.error("Provide at least one --url or --docs input.")

    return args


def main() -> int:
    args = parse_args()
    workspace = (
        Path(args.workspace).expanduser().resolve()
        if args.workspace
        else Path(
            tempfile.mkdtemp(prefix=f"onboardai-validation-{slugify(args.business_name)}-")
        )
    )

    try:
        scaffold_workspace(workspace)
        write_manifest(workspace, args)

        print(f"\n  Validation workspace: {workspace}")
        print("  This run is isolated from the repo's tracked data files and website assets.")

        env = os.environ.copy()
        commands = build_commands(args)

        for command in commands:
            run_step(command, cwd=workspace, env=env, dry_run=args.dry_run)

        print("\n  Dry run complete." if args.dry_run else "\n  Validation run complete.")

        if args.cleanup:
            shutil.rmtree(workspace)
            print("  Workspace cleaned up.")
        else:
            print(f"  Workspace retained at: {workspace}")

        return 0
    except subprocess.CalledProcessError as exc:
        print(f"\n  ❌ Validation step failed with exit code {exc.returncode}")
        print(f"  Inspect the isolated workspace here: {workspace}")
        return exc.returncode
    except FileExistsError as exc:
        print(f"\n  ❌ {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
