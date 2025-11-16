"""Smoke tests for the geometry runtime checkpoint loop (INT-001)."""
from __future__ import annotations

from pathlib import Path

import json
import pytest

from polylog6.simulation.runtime import GeometryEvent, GeometryRuntime
from polylog6.simulation.engines import SimulationEngine
from polylog6.simulation.engine import run_geometry_session
from polylog6.storage.encoder import EncodedPolygon
from polylog6.storage.manager import PolyformStorageManager


@pytest.fixture()
def sample_polygons() -> list[EncodedPolygon]:
    return [
        EncodedPolygon(3, 0, 0, (0, 0, 0)),
        EncodedPolygon(4, 1, 2, (1, 0, -1)),
        EncodedPolygon(5, 2, 3, (2, -1, 2)),
    ]


def _build_engine(base_dir: Path, *, inbox_path: Path | None = None) -> SimulationEngine:
    storage_dir = base_dir / "chunks"
    storage_manager = PolyformStorageManager(storage_dir, chunk_size=2, snapshot_interval=1)
    return SimulationEngine(storage_manager=storage_manager, inbox_path=inbox_path, checkpoint_interval=1)


def test_geometry_runtime_checkpoint_and_restore(tmp_path: Path, sample_polygons: list[EncodedPolygon]) -> None:
    inbox_path = tmp_path / "inbox.jsonl"
    runtime = GeometryRuntime(engine=_build_engine(tmp_path, inbox_path=inbox_path), events_until_checkpoint=1)

    summary = runtime.process_event(GeometryEvent(polygons=sample_polygons, force_checkpoint=True, label_override="evt-000"))
    assert summary is not None
    assert summary.polygons == len(sample_polygons)
    assert summary.chunk_count == 2  # ceil(3 / chunk_size=2)
    assert summary.path.exists()
    assert runtime.workspace.polygon_count() == len(sample_polygons)

    inbox_content = inbox_path.read_text(encoding="utf-8").strip().splitlines()
    assert inbox_content, "Expected async inbox to receive an entry"
    payload = json.loads(inbox_content[-1])
    assert payload["label"] == "evt-000"
    assert payload["polygons"] == len(sample_polygons)

    restored_runtime = GeometryRuntime(engine=_build_engine(tmp_path), events_until_checkpoint=1)
    restored_runtime.restore(summary.path)
    assert restored_runtime.workspace.polygon_count() == len(sample_polygons)

    # Ensure subsequent event schedules a new checkpoint based on cadence.
    second_summary = runtime.process_event(GeometryEvent(polygons=sample_polygons, force_checkpoint=False))
    assert second_summary is not None
    assert second_summary.label.startswith("checkpoint-")


def test_run_geometry_session_integration(sample_polygons: list[EncodedPolygon]) -> None:
    events = [GeometryEvent(polygons=sample_polygons)]
    summaries = run_geometry_session(events, events_until_checkpoint=1)
    assert len(summaries) == 1
    assert summaries[0].polygons == len(sample_polygons)
