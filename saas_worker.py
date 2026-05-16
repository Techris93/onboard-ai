"""Background worker for durable OnboardAI SaaS jobs."""

from __future__ import annotations

import argparse
import json
import time

from saas_runtime import init_db, run_next_job


def main() -> int:
    parser = argparse.ArgumentParser(description="Run OnboardAI queued SaaS jobs.")
    parser.add_argument("--once", action="store_true", help="Process one batch of jobs and exit.")
    parser.add_argument("--limit", type=int, default=1, help="Jobs to process per tick.")
    parser.add_argument("--interval", type=float, default=5.0, help="Polling interval in seconds.")
    args = parser.parse_args()

    init_db()
    while True:
        result = run_next_job(limit=args.limit)
        print(json.dumps(result), flush=True)
        if args.once:
            return 0
        time.sleep(args.interval)


if __name__ == "__main__":
    raise SystemExit(main())
