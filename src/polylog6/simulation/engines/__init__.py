"""Simulation engine bundle providing geometry + storage coordination."""
from __future__ import annotations

from .analysis import OptimizationEngine, StabilityAnalyzer, StabilityMetrics
from .config import DEFAULT_SCORE, SMOOTHING_WINDOWS
from .core import SimulationEngine
from .checkpointing.polyform_engine import CheckpointSummary, PolyformEngine
from .checkpointing.workspace import PolyformWorkspace, WorkspacePolygon

__all__ = [
    "CheckpointSummary",
    "DEFAULT_SCORE",
    "OptimizationEngine",
    "PolyformEngine",
    "PolyformWorkspace",
    "SimulationEngine",
    "SMOOTHING_WINDOWS",
    "StabilityAnalyzer",
    "StabilityMetrics",
    "WorkspacePolygon",
]
