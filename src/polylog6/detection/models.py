"""Data models used across the INT-014 detection pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple


@dataclass(slots=True)
class RegionMetadata:
    """Lightweight representation of a segmented region."""

    label: int
    bbox: Tuple[int, int, int, int]
    area: int
    center: Tuple[float, float]
    color_mean: Tuple[float, float, float]
    mask: Any


@dataclass(slots=True)
class Candidate:
    """Represents a single polyform candidate for a region."""

    region_label: int
    polyform_type: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class DecompositionPlan:
    """Summarises the chosen candidates and aggregate stats."""

    candidates: List[Candidate]
    coverage_percent: float
    stats: Dict[str, Any] = field(default_factory=dict)


__all__ = ["RegionMetadata", "Candidate", "DecompositionPlan"]
