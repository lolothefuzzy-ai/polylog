"""Coverage for monitoring service bootstrap and watcher wiring."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import pytest

from polylog6.monitoring.service import (
    MonitoringLoop,
    MonitoringRuntimeConfig,
    create_monitoring_loop,
)


@pytest.fixture()
def stub_context_path(monkeypatch, tmp_path: Path) -> Path:
    path = tmp_path / "context-brief.jsonl"
    monkeypatch.setattr(
        "polylog6.monitoring.service.resolve_context_brief_path",
        lambda *, ensure_exists: path,
    )
    monkeypatch.setattr("polylog6.monitoring.service.monitoring_poll_interval", lambda: 0.0)
    return path


def test_create_monitoring_loop_disabled(monkeypatch, stub_context_path: Path) -> None:
    monkeypatch.setattr("polylog6.monitoring.service.monitoring_enabled", lambda: False)

    loop, bridge, watcher = create_monitoring_loop(
        MonitoringRuntimeConfig(registry_state_provider=lambda: {})
    )

    assert loop is None
    assert bridge is None
    assert watcher is None


def test_create_monitoring_loop_auto_start_watcher(monkeypatch, stub_context_path: Path) -> None:
    monkeypatch.setattr("polylog6.monitoring.service.monitoring_enabled", lambda: True)

    captured: Dict[str, Any] = {}

    def fake_watch_context(tailer, refresh_worker, **kwargs):
        captured["tailer"] = tailer
        captured["worker"] = refresh_worker
        captured["kwargs"] = kwargs
        return "watcher-token"

    monkeypatch.setattr(
        "polylog6.monitoring.service.watch_context_brief",
        fake_watch_context,
    )

    config = MonitoringRuntimeConfig(
        registry_state_provider=lambda: {},
        enable_watcher=True,
        auto_start_watcher=True,
        dispatcher_error_handler=lambda entry, exc: None,
        max_entries=5,
    )

    loop, bridge, watcher = create_monitoring_loop(config)

    assert isinstance(loop, MonitoringLoop)
    assert bridge is not None
    assert watcher == "watcher-token"
    assert captured["kwargs"]["max_entries"] == 5


def test_create_monitoring_loop_returns_manual_watcher(monkeypatch, stub_context_path: Path) -> None:
    monkeypatch.setattr("polylog6.monitoring.service.monitoring_enabled", lambda: True)

    stub_instances = []

    class StubWatcher:
        def __init__(self, tailer) -> None:
            self.tailer = tailer
            self.started = False
            stub_instances.append(self)

    monkeypatch.setattr("polylog6.monitoring.service.ContextBriefWatcher", StubWatcher)

    config = MonitoringRuntimeConfig(
        registry_state_provider=lambda: {},
        enable_watcher=True,
        auto_start_watcher=False,
    )

    loop, bridge, watcher = create_monitoring_loop(config)

    assert isinstance(loop, MonitoringLoop)
    assert bridge is not None
    assert watcher is not None
    assert watcher is stub_instances[0]
    assert watcher.tailer.log_path == stub_context_path
    assert watcher.started is False
