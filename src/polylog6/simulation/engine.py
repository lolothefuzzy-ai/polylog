"""Simulation engine entry point (legacy compatibility shim)."""

from __future__ import annotations

from typing import Iterable, Optional

from .engines import (
    CheckpointSummary,
    OptimizationEngine,
    SimulationEngine,
    StabilityAnalyzer,
)
from .runtime import GeometryEvent, GeometryRuntime
from .tier3_ingestion import Tier3CandidateIngestionPipeline


def run_geometry_session(
    events: Iterable[GeometryEvent],
    *,
    engine: Optional[SimulationEngine] = None,
    events_until_checkpoint: int = 1,
    tier3_pipeline: Tier3CandidateIngestionPipeline | None = None,
) -> list[CheckpointSummary]:
    """Process geometry events through the checkpointing runtime.

    Parameters
    ----------
    events:
        Iterable of :class:`GeometryEvent` instances produced by the geometry loop.
    engine:
        Optional preconfigured :class:`SimulationEngine`. When omitted a new engine
        is created with ``checkpoint_interval`` set to ``events_until_checkpoint``.
    events_until_checkpoint:
        Number of events to process before forcing a checkpoint when ``force`` is
        not supplied on the event. Defaults to ``1`` for immediate saves.
    """

    runtime = GeometryRuntime(
        engine=engine or SimulationEngine(checkpoint_interval=events_until_checkpoint),
        events_until_checkpoint=events_until_checkpoint,
        tier3_pipeline=tier3_pipeline,
    )
    return runtime.process_stream(events)


__all__ = [
    "CheckpointSummary",
    "GeometryEvent",
    "GeometryRuntime",
    "OptimizationEngine",
    "SimulationEngine",
    "StabilityAnalyzer",
    "run_geometry_session",
]

