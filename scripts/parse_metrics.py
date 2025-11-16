"""Parse pytest JSON reports into compression metrics artifacts (INT-002).

This script consumes the ``--json-report`` output from pytest runs of
``test_storage_pipeline.py`` and consolidates compression metrics captured by the
telemetry dashboard scaffold.
"""

from __future__ import annotations

import json
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Any, Dict, List, Sequence

from polylog6.telemetry import CompressionTelemetryDashboard


def _parse_args() -> Namespace:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path, help="Path to pytest JSON report")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("compression_metrics.json"),
        help="Destination path for summarised metrics",
    )
    parser.add_argument(
        "--label",
        type=str,
        default="ci-run",
        help="Label to associate with this metrics snapshot",
    )
    return parser.parse_args()


def _coerce_metrics_entry(entry: Any, metrics_blocks: List[Dict[str, Any]], seen: set[str]) -> None:
    """Normalise plugin-specific payload structures into raw metric dicts."""

    payload: Any

    if isinstance(entry, dict):
        if "name" in entry and entry.get("name") == "storage_metrics":
            payload = entry.get("data")
        elif "storage_metrics" in entry:
            payload = entry.get("storage_metrics")
        else:
            return
    elif isinstance(entry, Sequence) and len(entry) == 2:
        key, payload = entry  # type: ignore[assignment]
        if key != "storage_metrics":
            return
    else:
        return

    if isinstance(payload, dict):
        fingerprint = json.dumps(payload, sort_keys=True)
        if fingerprint not in seen:
            seen.add(fingerprint)
            metrics_blocks.append(payload)


def _extract_metrics(report: Dict[str, Any]) -> List[Dict[str, Any]]:
    metrics_blocks: List[Dict[str, Any]] = []
    seen: set[str] = set()

    for test in report.get("tests", []):
        for container in (
            test.get("user_properties"),
            test.get("call", {}).get("user_properties"),
            test.get("call", {}).get("extradata"),
        ):
            if not isinstance(container, list):
                continue
            for entry in container:
                _coerce_metrics_entry(entry, metrics_blocks, seen)

    return metrics_blocks


def generate_summary(report_path: Path, output_path: Path, label: str) -> Dict[str, Any]:
    """Read a pytest JSON report, ingest metrics, and persist the summary."""

    report_data = json.loads(report_path.read_text(encoding="utf-8"))

    metrics_blocks = _extract_metrics(report_data)
    dashboard = CompressionTelemetryDashboard()

    for index, metrics in enumerate(metrics_blocks):
        effective_label = f"{label}-{index}" if len(metrics_blocks) > 1 else label
        dashboard.ingest_metrics(effective_label, metrics)

    summary = {
        "label": label,
        "runs": [snapshot.to_dict() for snapshot in dashboard.snapshots()],
        "summary": dashboard.summary(),
    }

    output_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return summary


def main() -> None:
    args = _parse_args()
    generate_summary(args.report, args.output, args.label)


if __name__ == "__main__":
    main()
