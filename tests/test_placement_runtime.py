from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

import pytest

from polylog6.simulation.placement.attachment_resolver import AttachmentOption
from polylog6.simulation.placement.fold_sequencer import FoldSequence, FoldStep
from polylog6.simulation.placement.runtime import PlacementRuntime, PlacementSpec, PolyformHydrator
from polylog6.simulation.runtime import GeometryEvent
from polylog6.storage.encoder import EncodedPolygon
from polylog6.storage.manager import PolyformStorageManager


@dataclass
class StubHydrator(PolyformHydrator):
    polygons: List[EncodedPolygon]

    def instantiate(
        self,
        *,
        polyform_id: str,
        scaler: float,
        folds: Iterable[float] | None,
    ) -> List[EncodedPolygon]:
        return self.polygons


@dataclass
class StubFoldSequencer:
    sequence: FoldSequence

    def generate_sequence(self, polyform_id: str, *, scaler: float = 1.0) -> FoldSequence:  # pragma: no cover - simple stub
        return self.sequence


@pytest.fixture
def runtime_with_resolver() -> PlacementRuntime:
    polygons = [
        EncodedPolygon(3, 0, 0, (0, 0, 0)),
        EncodedPolygon(4, 1, 0, (1, 0, 0)),
    ]
    hydrator = StubHydrator(polygons)
    storage_manager = PolyformStorageManager("tmp")
    fold_sequence = FoldSequence(
        polyform_id="test",
        steps=[
            FoldStep(index=0, polygon_symbol="A", angle_degrees=90.0, axis=(1.0, 0.0, 0.0), duration_ms=10.0)
        ],
        collisions_detected=False,
        warnings=[],
        lod_levels_used=[1, 2],
    )
    return PlacementRuntime(
        storage_manager=storage_manager,
        hydrator=hydrator,
        fold_sequencer=StubFoldSequencer(fold_sequence),
    )


def test_runtime_auto_attachment_schema(runtime_with_resolver: PlacementRuntime) -> None:
    spec = PlacementSpec(polyform_id="test", attachment_schema="auto")

    events = list(runtime_with_resolver.emit_events([spec]))
    assert len(events) == 1
    event = events[0]
    assert isinstance(event, GeometryEvent)
    assert event.label_override != "auto"
    assert event.metadata is not None
    assert "fold_sequence" in event.metadata
    sequence = event.metadata["fold_sequence"]
    assert sequence["collisions"] is False
    assert sequence["steps"][0]["symbol"] == "A"


def test_resolve_attachment_schema_explicit(runtime_with_resolver: PlacementRuntime) -> None:
    option = runtime_with_resolver.resolve_attachment_schema(3, 4, dimension="2d")
    assert option is not None
    assert isinstance(option, AttachmentOption)
    assert option.char
