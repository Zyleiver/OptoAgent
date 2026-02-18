"""
Continuous scheduler for OptoAgent.

Periodically runs monitor_sources and/or run_cycle via subprocess.
"""

import argparse
import subprocess
import sys
import time

import schedule

from optoagent.config import DEFAULT_QUERY, SCHEDULER_INTERVAL, SCHEDULER_UNIT
from optoagent.logger import get_logger

logger = get_logger(__name__)


def _job(query: str) -> None:
    """Execute one scheduled cycle."""
    logger.info("--- Running Scheduled Cycle at %s ---", time.ctime())

    # 1. Monitor tracked sources
    logger.info("[Scheduler] Running monitor_sources...")
    subprocess.run([sys.executable, "-m", "optoagent.cli", "monitor_sources"])

    # 2. Active Search + Idea Generation
    if query:
        logger.info("[Scheduler] Running run_cycle for '%s'...", query)
        subprocess.run(
            [sys.executable, "-m", "optoagent.cli", "run_cycle", "--query", query, "--limit", "3"]
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="OptoAgent Continuous Scheduler")
    parser.add_argument(
        "--interval", type=int, default=SCHEDULER_INTERVAL, help="Interval between checks"
    )
    parser.add_argument(
        "--unit",
        choices=["minutes", "hours"],
        default=SCHEDULER_UNIT,
        help="Time unit for interval",
    )
    parser.add_argument("--query", default=DEFAULT_QUERY, help="Search query for run_cycle")
    parser.add_argument("--dry-run", action="store_true", help="Run immediately once and exit")
    parser.add_argument(
        "--max-runs", type=int, default=0, help="Stop after N runs (0 = infinite)"
    )

    args = parser.parse_args()

    if args.dry_run:
        logger.info("Dry Run: Executing job immediately...")
        _job(args.query)
        return

    logger.info(
        "Scheduler started. Running every %d %s. Query: '%s'",
        args.interval,
        args.unit,
        args.query,
    )

    # Counter for --max-runs support
    counter = [0]

    def _wrapped_job() -> None:
        _job(args.query)
        if args.max_runs > 0:
            counter[0] += 1
            logger.info("Run %d/%d completed.", counter[0], args.max_runs)
            if counter[0] >= args.max_runs:
                logger.info("Max runs reached. Exiting.")
                sys.exit(0)

    if args.unit == "minutes":
        schedule.every(args.interval).minutes.do(_wrapped_job)
    else:
        schedule.every(args.interval).hours.do(_wrapped_job)

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    main()
