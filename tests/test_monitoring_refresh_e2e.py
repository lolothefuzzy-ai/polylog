"""End-to-end coverage for monitoring registry drift fan-out (INT-004)."""
from __future__ import annotations

from pathlib import Path
from typing import Dict

import pytest

from polylog6.monitoring.alerts import fanout_alert_callbacks
from polylog6.monitoring.library_refresh import (
    CheckpointRecord,
    LibraryRefreshWorker,
    compute_registry_digest,
)


@pytest.fixture()
def mock_alert_endpoints() -> Dict[str, list[str]]:
    return {"webhook": [], "email": [], "dashboard": []}


@pytest.fixture()
def record(tmp_path: Path) -> CheckpointRecord:
    baseline_state = {"registry": {"uuid-1": {"O": 1}, "uuid-2": {"O": 2}}}
    digest = compute_registry_digest(baseline_state)
    return CheckpointRecord(
        label="checkpoint-001",
        path=tmp_path / "checkpoint.jsonl",
        polygons=128,
        chunk_count=8,
        module_refs=0,
        registry_digest=digest,
        timestamp=1_700_000_000.0,
    )


def test_registry_drift_detection_e2e(mock_alert_endpoints: Dict[str, list[str]], record: CheckpointRecord, tmp_path: Path) -> None:
    modified_state = {"registry": {"uuid-1": {"O": 1}}}

    def registry_provider() -> Dict[str, object]:
        return modified_state

    def make_alert_sink(channel: str):
        return lambda code, checkpoint: mock_alert_endpoints[channel].append(code)

    alert_sink = fanout_alert_callbacks(
        [
            make_alert_sink("webhook"),
            make_alert_sink("email"),
            make_alert_sink("dashboard"),
        ]
    )

    refresh_calls: list[str] = []

    worker = LibraryRefreshWorker(
        tmp_path / "context.jsonl",
        registry_state_provider=registry_provider,
        on_refresh=lambda checkpoint: refresh_calls.append(checkpoint.label),
        on_alert=alert_sink,
    )

    result = worker.process_record(record)
    assert result is not None
    assert result.registry_match is False
    assert result.refreshed is True

    for channel, calls in mock_alert_endpoints.items():
        assert calls == ["registry_mismatch"], f"Alert not emitted on {channel}"
    assert refresh_calls == [record.label]


def test_registry_parity_check_stability(record: CheckpointRecord) -> None:
    state = {"registry": {"a": 1, "b": 2}}
    matching_digest = compute_registry_digest(state)
    parity_record = CheckpointRecord(
        label=record.label,
        path=record.path,
        polygons=record.polygons,
        chunk_count=record.chunk_count,
        module_refs=record.module_refs,
        registry_digest=matching_digest,
        timestamp=record.timestamp,
    )

    worker = LibraryRefreshWorker(
        Path("memory/coordination/context-brief.jsonl"),
        registry_state_provider=lambda: state,
    )
    result = worker.process_record(parity_record)
    assert result is not None
    assert result.registry_match is True
    assert result.refreshed is False
