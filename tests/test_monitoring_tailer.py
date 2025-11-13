"""Tests for monitoring tailer and library refresh scaffolding."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterator

import pytest

from polylog6.monitoring.context_brief_tailer import ContextBriefEntry, ContextBriefTailer
from polylog6.monitoring.dispatcher import DispatchResult, dispatch_once, run_dispatch_loop
from polylog6.monitoring.library_refresh import (
    LibraryRefreshWorker,
    compute_registry_digest,
)
from polylog6.monitoring.loop import MonitoringLoop, MonitoringLoopConfig
from polylog6.monitoring.telemetry_bridge import DetectionTelemetryBridge


def test_context_brief_tailer_tracks_new_entries(tmp_path: Path) -> None:
    log_path = tmp_path / "context-brief.jsonl"
    tailer = ContextBriefTailer(log_path)

    # No file yet → no entries.
    assert tailer.read_new_entries() == []

    # First entry appears.
    log_path.write_text(json.dumps({"registry_digest": "abc123"}) + "\n", encoding="utf-8")
    entries = tailer.read_new_entries()
    assert [entry.registry_digest for entry in entries] == ["abc123"]

    # No additional entries since file unchanged.
    assert tailer.read_new_entries() == []

    # Simulate truncation/rotation then append a fresh entry.
    log_path.write_text("", encoding="utf-8")
    assert tailer.read_new_entries() == []  # offset reset

    log_path.write_text(json.dumps({"registry_digest": "xyz789"}) + "\n", encoding="utf-8")
    entries = tailer.read_new_entries()
    assert [entry.registry_digest for entry in entries] == ["xyz789"]


def test_library_refresh_worker_triggers_on_mismatch(tmp_path: Path) -> None:
    log_path = tmp_path / "context-brief.jsonl"

    matching_state: Dict[str, Dict[str, str]] = {
        "clusters": {},
        "assemblies": {},
        "megas": {},
    }
    mismatched_state: Dict[str, Dict[str, str]] = {
        "clusters": {"signature:1": "Ω₁"},
        "assemblies": {},
        "megas": {},
    }
    matching_digest = compute_registry_digest(matching_state)

    records = [
        {
            "label": "checkpoint-001",
            "path": str(tmp_path / "checkpoint-001.jsonl"),
            "polygons": 128,
            "chunk_count": 8,
            "module_refs": 0,
            "registry_digest": matching_digest,
            "timestamp": 1_699_999_999.0,
        },
        {
            "label": "checkpoint-002",
            "path": str(tmp_path / "checkpoint-002.jsonl"),
            "polygons": 256,
            "chunk_count": 16,
            "module_refs": 0,
            "registry_digest": matching_digest,
            "timestamp": 1_700_000_000.0,
        },
    ]
    log_path.write_text("".join(json.dumps(record) + "\n" for record in records), encoding="utf-8")

    states: Iterator[Dict[str, Dict[str, str]]] = iter([matching_state, mismatched_state])

    def registry_state_provider() -> Dict[str, Dict[str, str]]:
        try:
            return next(states)
        except StopIteration:
            return mismatched_state

    refresh_events: list[str] = []
    alert_events: list[tuple[str, str]] = []

    worker = LibraryRefreshWorker(
        log_path,
        registry_state_provider=registry_state_provider,
        on_refresh=lambda record: refresh_events.append(record.label),
        on_alert=lambda code, record: alert_events.append((code, record.label)),
    )

    results = worker.process_new_records()
    assert len(results) == 2

    first, second = results
    assert first.record.label == "checkpoint-001"
    assert first.registry_match is True
    assert first.refreshed is False

    assert second.record.label == "checkpoint-002"
    assert second.registry_match is False
    assert second.refreshed is True

    assert refresh_events == ["checkpoint-002"]
    assert alert_events == [("registry_mismatch", "checkpoint-002")]


def test_dispatch_once_routes_refresh_and_telemetry(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    tailer = ContextBriefTailer(tmp_path / "context-brief.jsonl")

    baseline_state: Dict[str, Dict[str, str]] = {"clusters": {}, "assemblies": {}}
    current_state: Dict[str, Dict[str, str]] = {"clusters": {"sig:1": "Ω1"}, "assemblies": {}}
    baseline_digest = compute_registry_digest(baseline_state)

    entry = ContextBriefEntry(
        payload={
            "checkpoint_record": {
                "label": "checkpoint-123",
                "path": str(tmp_path / "checkpoint-123.jsonl"),
                "polygons": 64,
                "chunk_count": 4,
                "module_refs": 0,
                "registry_digest": baseline_digest,
                "timestamp": 1_700_000_500.0,
            },
            "detection_telemetry": {
                "request_id": "req-telemetry",
                "region_count": 3,
                "coverage_percent": 35.0,
                "hull_region_count": 0,
                "hull_volume_total": 0.0,
                "topology_backend": "trimesh",
                "avg_candidate_score": 1.0,
            },
        }
    )

    monkeypatch.setattr(tailer, "read_new_entries", lambda: [entry])

    refresh_events: list[str] = []
    alert_events: list[str] = []

    worker = LibraryRefreshWorker(
        tmp_path / "context-brief.jsonl",
        registry_state_provider=lambda: current_state,
        on_refresh=lambda record: refresh_events.append(record.label),
        on_alert=lambda code, record: alert_events.append(f"{code}:{record.label}"),
    )
    bridge = DetectionTelemetryBridge()

    result: DispatchResult = dispatch_once(tailer, worker, telemetry_bridge=bridge)

    assert result.processed == 1
    assert refresh_events == ["checkpoint-123"]
    assert alert_events == ["registry_mismatch:checkpoint-123"]

    assert len(result.refresh_results) == 1
    refresh_result = result.refresh_results[0]
    assert refresh_result.registry_match is False
    assert refresh_result.refreshed is True

    snapshots = result.telemetry_snapshots
    assert len(snapshots) == 1
    snapshot = snapshots[0]
    assert snapshot.request_id == "req-telemetry"
    assert snapshot.alerts  # coverage threshold breached → alert emitted


def test_run_dispatch_loop_honors_feature_flag(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    tailer = ContextBriefTailer(tmp_path / "context-brief.jsonl")
    entry = ContextBriefEntry(payload={"registry_digest": "noop"})
    monkeypatch.setattr(tailer, "read_new_entries", lambda: [entry])

    worker = LibraryRefreshWorker(
        tmp_path / "context-brief.jsonl",
        registry_state_provider=lambda: {"clusters": {}, "assemblies": {}},
    )

    bridge = DetectionTelemetryBridge()
    enabled_calls: list[bool] = [True, False]

    def fake_enabled() -> bool:
        return enabled_calls.pop(0) if enabled_calls else False

    results = run_dispatch_loop(
        tailer,
        worker,
        telemetry_bridge=bridge,
        enabled=fake_enabled,
        poll_interval=0,
        max_entries=1,
        sleep_fn=lambda _: None,
    )

    assert len(results) == 1
    assert results[0].processed == 1


def test_run_dispatch_loop_max_iterations(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    tailer = ContextBriefTailer(tmp_path / "context-brief.jsonl")
    monkeypatch.setattr(tailer, "read_new_entries", lambda: [])

    worker = LibraryRefreshWorker(
        tmp_path / "context-brief.jsonl",
        registry_state_provider=lambda: {"clusters": {}, "assemblies": {}},
    )

    results = run_dispatch_loop(
        tailer,
        worker,
        poll_interval=0,
        max_iterations=3,
        sleep_fn=lambda _: None,
    )

    assert len(results) == 3
    assert all(result.processed == 0 for result in results)


def test_monitoring_loop_runs_with_feature_flag(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    tailer = ContextBriefTailer(tmp_path / "context-brief.jsonl")

    entry = ContextBriefEntry(
        payload={
            "checkpoint_record": {
                "label": "checkpoint-loop",
                "path": str(tmp_path / "checkpoint-loop.jsonl"),
                "polygons": 10,
                "chunk_count": 1,
                "module_refs": 0,
                "registry_digest": "digest-loop",
                "timestamp": 1_700_000_900.0,
            }
        }
    )

    entries = [entry, entry]

    def fake_read() -> list[ContextBriefEntry]:
        return [entries.pop(0)] if entries else []

    monkeypatch.setattr(tailer, "read_new_entries", fake_read)

    refresh_events: list[str] = []

    worker = LibraryRefreshWorker(
        tmp_path / "context-brief.jsonl",
        registry_state_provider=lambda: {"clusters": {}, "assemblies": {}},
        on_refresh=lambda record: refresh_events.append(record.label),
    )

    enabled_calls: list[bool] = [True, True, False]

    def enabled() -> bool:
        return enabled_calls.pop(0)

    loop = MonitoringLoop(
        tailer,
        worker,
        telemetry_bridge=None,
        enabled=enabled,
        config=MonitoringLoopConfig(poll_interval=0, max_entries=1),
    )

    loop.run()

    assert refresh_events == ["checkpoint-loop", "checkpoint-loop"]
