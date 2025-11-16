from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import pytest

from polylog6.monitoring.library_refresh import (
    CheckpointRecord,
    LibraryRefreshWorker,
    MonitoringResult,
    compute_registry_digest,
)


def _write_record(path: Path, payload: Dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")


def _sample_payload(**overrides: object) -> Dict[str, object]:
    payload: Dict[str, object] = {
        "label": "checkpoint-0001",
        "path": "storage/chunks/workspace.jsonl",
        "polygons": 12,
        "chunk_count": 3,
        "module_refs": 0,
        "registry_digest": "",
        "timestamp": 42.0,
    }
    payload.update(overrides)
    return payload


def test_library_refresh_requires_provider(tmp_path: Path) -> None:
    log_path = tmp_path / "context-brief.jsonl"

    with pytest.raises(ValueError):
        LibraryRefreshWorker(log_path)


def test_library_refresh_detects_matching_registry(tmp_path: Path) -> None:
    log_path = tmp_path / "context-brief.jsonl"
    state = {"symbols": {"triangle": "A"}}
    digest = compute_registry_digest(state)

    _write_record(log_path, _sample_payload(registry_digest=digest))

    worker = LibraryRefreshWorker(
        log_path,
        registry_state_provider=lambda: state,
    )

    results = worker.process_new_records()

    assert len(results) == 1
    result = results[0]
    assert result.registry_match is True
    assert result.refreshed is False
    assert result.record.registry_digest == digest

    # Replaying without new records should yield no work.
    assert worker.process_new_records() == []


def test_library_refresh_triggers_callbacks(tmp_path: Path) -> None:
    log_path = tmp_path / "context-brief.jsonl"
    mismatch_state = {"symbols": {"square": "B"}}
    matching_state = {"symbols": {"triangle": "A"}}
    matching_digest = compute_registry_digest(matching_state)

    _write_record(log_path, _sample_payload(registry_digest=matching_digest))

    refresh_calls: List[CheckpointRecord] = []
    alerts: List[tuple[str, CheckpointRecord]] = []

    worker = LibraryRefreshWorker(
        log_path,
        registry_state_provider=lambda: mismatch_state,
        on_refresh=lambda record: refresh_calls.append(record),
        on_alert=lambda level, record: alerts.append((level, record)),
    )

    results = worker.process_new_records()

    assert len(results) == 1
    result: MonitoringResult = results[0]
    assert result.registry_match is False
    assert result.refreshed is True

    assert refresh_calls == [result.record]
    assert alerts == [("registry_mismatch", result.record)]

    # No additional callbacks when log is unchanged.
    assert worker.process_new_records() == []
