"""Geometry runtime loop that drives the SimulationEngine checkpoints."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence

from .engines import CheckpointSummary, SimulationEngine
from .engines.checkpointing.workspace import PolyformWorkspace
from ..storage.encoder import EncodedPolygon
from polylog6.folding.engine import FoldingEngine
from polylog6.storage.polyform_storage import PolyformStorage
# UnicodeStorage - use PolyformStorage or SymbolRegistry instead
# from polylog6.storage.unicode_storage import UnicodeStorage
try:
    from polylog6.storage.polyform_storage import PolyformStorage as UnicodeStorage
except ImportError:
    # Fallback: create minimal stub
    class UnicodeStorage:
        """Minimal stub for UnicodeStorage"""
        def __init__(self, *args, **kwargs):
            pass
from polylog6.telemetry.simulation_telemetry_bridge import SimulationTelemetryBridge
from .tier3_ingestion import Tier3CandidateIngestionPipeline


@dataclass(slots=True)
class GeometryEvent:
    """Represents a batch of polygons emitted by the geometry generator."""

    polygons: Sequence[EncodedPolygon]
    force_checkpoint: bool = False
    label_override: Optional[str] = None
    metadata: Optional[Dict[str, object]] = None


@dataclass
class GeometryRuntime:
    """High-level orchestrator pairing geometry generation with checkpoints."""

    engine: SimulationEngine = field(default_factory=SimulationEngine)
    events_until_checkpoint: int = 1
    folding_engine: FoldingEngine = field(default_factory=FoldingEngine)
    pending_folding_events: List = field(default_factory=list)
    telemetry_bridge: SimulationTelemetryBridge = field(default_factory=SimulationTelemetryBridge)
    tier3_pipeline: Tier3CandidateIngestionPipeline | None = None

    def __post_init__(self) -> None:
        if self.events_until_checkpoint <= 0:
            raise ValueError("events_until_checkpoint must be positive")
        self._event_counter = 0
        self.step_count = 0

    @property
    def workspace(self) -> PolyformWorkspace:
        return self.engine.workspace

    def process_event(self, event: GeometryEvent) -> Optional[CheckpointSummary]:
        """Apply a geometry event and trigger checkpoints as needed."""

        self._ingest_polygons(event.polygons)
        self._event_counter += 1
        force = event.force_checkpoint or self._event_counter >= self.events_until_checkpoint
        if force:
            summary = self.engine.tick(force=True, label=event.label_override)
            self._event_counter = 0
            if summary is not None and self.tier3_pipeline is not None:
                self.tier3_pipeline.ingest_checkpoint(summary, self.workspace)
            return summary
        return None

    def _ingest_polygons(self, polygons: Sequence[EncodedPolygon]) -> None:
        for polygon in polygons:
            self.engine.add_encoded(polygon)

    def step(self):
        """Advance simulation by one step."""
        # Process folding events
        for event in self.pending_folding_events:
            self.folding_engine.process(event)
        self.pending_folding_events = []
        self.step_count += 1
        # Emit telemetry
        self.telemetry_bridge.emit("step_completed", {"step_count": self.step_count})

    # Convenience helpers -------------------------------------------------
    def process_stream(self, stream: Iterable[GeometryEvent]) -> List[CheckpointSummary]:
        """Process a stream of geometry events until exhaustion."""

        summaries: List[CheckpointSummary] = []
        for event in stream:
            summary = self.process_event(event)
            if summary is not None:
                summaries.append(summary)
        return summaries

    def restore(self, checkpoint_path: Path) -> None:
        self.engine.restore(checkpoint_path)

    def clear(self) -> None:
        self.engine.clear()


class SimulationRuntime:
    """Core simulation runtime."""
    
    def __init__(self, *, tier3_pipeline: Tier3CandidateIngestionPipeline | None = None):
        self.folding_engine = FoldingEngine()  # Add folding engine
        self.geometry_runtime = GeometryRuntime(tier3_pipeline=tier3_pipeline)
        self.telemetry_bridge = SimulationTelemetryBridge()
        self.storage = PolyformStorage()
        self.unicode_storage = UnicodeStorage()
    
    def step(self):
        """Advance simulation by one step."""
        # Process folding events
        for event in self.geometry_runtime.pending_folding_events:
            self.folding_engine.process(event)
        self.geometry_runtime.pending_folding_events = []
        self.geometry_runtime.step_count += 1
        # Emit telemetry
        self.telemetry_bridge.emit("step_completed", {"step_count": self.geometry_runtime.step_count})

    def create_polyform(self, polyform_id: str, data: dict):
        """Create a new polyform instance."""
        # Add to storage and get symbol
        symbol = self.storage.add(polyform_id, data, frequency=1)
        # Add to unicode storage
        self.unicode_storage.add(symbol, data)
        # Create simulation entity with symbol
        entity = self._create_entity(symbol, data)
        return entity


__all__ = ["GeometryRuntime", "GeometryEvent", "SimulationRuntime"]
