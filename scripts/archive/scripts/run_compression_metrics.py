"""Run storage regression suite and emit compression telemetry artifacts (INT-005).

This helper wraps the pytest JSON reporting flow so CI jobs (or local dry runs)
can produce a normalised `compression_metrics.json` file for the telemetry
pipeline without manual command orchestration.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List, Sequence

from parse_metrics import generate_summary

_DEFAULT_TEST_TARGET = "src/polylog6/storage/tests/test_storage_pipeline.py"


class CommandError(RuntimeError):
    """Raised when the underlying pytest invocation fails."""


def _build_pytest_command(report_file: Path, pytest_args: Sequence[str]) -> List[str]:
    command = [sys.executable, "-m", "pytest", "--json-report", f"--json-report-file={report_file}"]
    command.extend(pytest_args)
    return command


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--label",
        default="ci-run",
        help="Label associated with the generated metrics snapshot.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("compression_metrics.json"),
        help="Destination file for aggregated metrics (JSON).",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("tmp_storage_report.json"),
        help="Intermediate pytest JSON report path.",
    )
    parser.add_argument(
        "--keep-report",
        action="store_true",
        help="Do not delete the JSON report after summarising (defaults to delete on success).",
    )
    parser.add_argument(
        "pytest_args",
        nargs=argparse.REMAINDER,
        help=(
            "Additional arguments forwarded to pytest. Use '--' before options to "
            "avoid argparse conflicts. Defaults to the storage pipeline regression suite."
        ),
    )
    return parser.parse_args()


def _resolve_pytest_args(extra_args: Sequence[str] | None) -> List[str]:
    if not extra_args:
        return [_DEFAULT_TEST_TARGET]

    # argparse.REMAINDER preserves the leading '--' delimiter; strip it if present.
    if extra_args and extra_args[0] == "--":
        return list(extra_args[1:]) or [_DEFAULT_TEST_TARGET]

    return list(extra_args)


def run(pytest_args: Sequence[str], report_file: Path) -> None:
    command = _build_pytest_command(report_file, pytest_args)
    result = subprocess.run(command, check=False)
    if result.returncode != 0:
        raise CommandError(
            "pytest run failed with exit code " f"{result.returncode}. Command: {' '.join(command)}"
        )


def main() -> None:
    args = _parse_args()
    pytest_args = _resolve_pytest_args(args.pytest_args)

    try:
        run(pytest_args, args.report)
        summary = generate_summary(args.report, args.output, args.label)
    finally:
        if not args.keep_report and args.report.exists():
            try:
                args.report.unlink()
            except OSError:
                pass

    print(f"Saved compression metrics summary to {args.output.resolve()}")
    print(summary := summary)  # noqa: F841 - provide summary in stdout for CI logs


if __name__ == "__main__":
    main()
