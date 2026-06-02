"""Command line entry point for contract validation."""

from __future__ import annotations

import argparse
from pathlib import Path

from video_factory_contracts.validation import validate_repo


def main(argv: list[str] | None = None) -> int:
    """Run contract validation and return a process exit code."""
    parser = argparse.ArgumentParser(description="Validate repository contracts.")
    parser.add_argument("--repo", default=".", help="Repository root to validate.")
    parser.add_argument(
        "--skip-harness",
        action="store_true",
        help="Skip the local RepoFrame harness check. Useful outside Codex machines.",
    )
    args = parser.parse_args(argv)

    report = validate_repo(Path(args.repo), skip_harness=args.skip_harness)
    print(report.render())
    return 1 if report.errors else 0

