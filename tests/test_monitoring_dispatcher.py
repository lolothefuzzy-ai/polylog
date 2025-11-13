"""Tests for dispatcher utilities with ContextBriefWatcher integration."""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import List

import pytest

from polylog6.monitoring.context_brief_tailer import ContextBriefTailer
from polylog6.monitoring.dispatcher import dispatch_entries, watch_context_brief
from polylog6.monitoring.library_refresh import CheckpointRecord, LibraryRefreshWorker
from polylog6.monitoring.telemetry_bridge import DetectionTelemetryBridge


class DummyRefreshWorker(LibraryRefreshWorker):
    def __init__(self, context_log_path: Path) -> None:
        super().__init__(
            context_log_path=context_log_path,
            registry_state_provider=lambda: {"registry": {}},
        )
        self.processed: List[CheckpointRecord] = []

    def process_record(self, record: CheckpointRecord):  # type: ignore[override]
        self.processed.append(record)
        return record


@pytest.mark.skipif(sys.platform.startswith("win"), reason="watchdog tests flaky on Windows CI")
def test_watch_context_brief(monkeypatch, tmp_path):
    pytest.importorskip("watchdog.observers")

    log_path = tmp_path / "context-brief.jsonl"
    log_path.write_text("", encoding="utf-8")

    tailer = ContextBriefTailer(log_path, poll_interval=0.0)
    worker = DummyRefreshWorker(log_path)
    telemetry = DetectionTelemetryBridge()

    seen = {"entries": 0, "snapshots": 0}

    def fake_dispatch(entries, refresh_worker, **kwargs):
        result = dispatch_entries(entries, refresh_worker, **kwargs)
        seen["entries"] += result.processed
        seen["snapshots"] += len(result.telemetry_snapshots)
        return result

    monkeypatch.setattr("polylog6.monitoring.dispatcher.dispatch_entries", fake_dispatch)

    watcher = watch_context_brief(
        tailer,
        worker,
        telemetry_bridge=telemetry,
    )

    try:
        log_path.write_text('{"registry_digest": "abc123"}\n', encoding="utf-8")
        time.sleep(0.2)
    finally:
        watcher.stop()

    assert seen["entries"] >= 1
