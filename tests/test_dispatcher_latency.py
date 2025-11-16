"""Performance guardrail tests for dispatcher latency."""

from __future__ import annotations

import time

from pathlib import Path

from polylog6.monitoring.context_brief_tailer import ContextBriefEntry
from polylog6.monitoring.dispatcher import dispatch_entries
from polylog6.monitoring.library_refresh import LibraryRefreshWorker
from polylog6.monitoring.telemetry_bridge import DetectionTelemetryBridge
from polylog6.monitoring.library_refresh import compute_registry_digest


def _checkpoint_payload(base_path: Path, label: str) -> dict[str, object]:
    return {
        "label": label,
        "path": str(base_path / f"{label}.jsonl"),
        "polygons": 128,
        "chunk_count": 4,
        "module_refs": 0,
        "registry_digest": compute_registry_digest({"registry": {}}),
        "timestamp": 1_700_000_000.0,
    }


def _telemetry_payload(idx: int) -> dict[str, object]:
    return {
        "request_id": f"req-{idx}",
        "region_count": 3,
        "candidate_count": 5,
        "coverage_percent": 92.5,
        "schema_version": "0.1",
        "hull_region_count": 2,
        "hull_volume_total": 12.0,
        "avg_candidate_score": 2.8,
        "duration_ms": 65.0 + idx,
    }


def test_dispatch_entries_latency_under_100ms(tmp_path):
    context_path = tmp_path / "context-brief.jsonl"
    worker = LibraryRefreshWorker(
        context_path,
        registry_state_provider=lambda: {"registry": {}},
    )

    entries = []
    for idx in range(10):
        entries.append(
            ContextBriefEntry(
                payload={
                    "checkpoint_record": _checkpoint_payload(tmp_path, f"checkpoint-{idx}"),
                    "detection_telemetry": _telemetry_payload(idx),
                }
            )
        )

    bridge = DetectionTelemetryBridge()

    started = time.perf_counter()
    result = dispatch_entries(entries, worker, telemetry_bridge=bridge)
    elapsed_ms = (time.perf_counter() - started) * 1000.0

    assert result.processed == len(entries)
    assert elapsed_ms < 100.0, f"Dispatcher latency {elapsed_ms:.3f} ms exceeded 100 ms budget"
