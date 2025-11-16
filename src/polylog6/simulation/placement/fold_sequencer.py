"""Catalog-driven fold sequencer with lightweight collision guards."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import numpy as np


@dataclass(slots=True)
class FoldStep:
    """Single fold operation emitted by the sequencer."""

    index: int
    polygon_symbol: str
    angle_degrees: float
    axis: Tuple[float, float, float]
    duration_ms: float


@dataclass(slots=True)
class FoldSequence:
    """Fold sequence with metadata and guardrail information."""

    polyform_id: str
    steps: List[FoldStep]
    collisions_detected: bool
    warnings: List[str] = field(default_factory=list)
    lod_levels_used: Sequence[int] = field(default_factory=list)


@dataclass(slots=True)
class SequencerConfig:
    """Runtime configuration knobs for fold sequencing."""

    duration_scale: float = 1.0
    collision_guard: bool = True
    axis_epsilon: float = 1e-6
    min_duration_ms: float = 8.0
    base_angle_scale: float = 1.0


class FoldSequencer:
    """Generate fold sequences informed by geometry and scaler catalogs."""

    def __init__(
        self,
        *,
        geometry_catalog: Mapping[str, Any],
        scaler_catalog: Mapping[str, Any],
        lod_metadata: Optional[Mapping[str, Any]] = None,
        config: Optional[SequencerConfig] = None,
    ) -> None:
        self._geometry = geometry_catalog
        self._scaler = scaler_catalog
        self._lod = lod_metadata or {}
        self._config = config or SequencerConfig()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def generate_sequence(
        self,
        polyform_id: str,
        *,
        scaler: float = 1.0,
    ) -> FoldSequence:
        components = self._resolve_components(polyform_id)
        if not components:
            raise ValueError(f"Unknown polyform: {polyform_id}")

        lod_levels = self._lod_levels(polyform_id)
        steps: List[FoldStep] = []
        for index, component in enumerate(components):
            sides = int(component.get("sides", 0))
            if sides < 3:
                continue
            symbol = component.get("symbol") or self._symbol_for_component(component, sides)
            angle = self._derive_fold_angle(polyform_id, component, scaler)
            axis = self._derive_axis(component)
            duration = self._estimate_duration(angle, scaler, sides)
            steps.append(
                FoldStep(
                    index=index,
                    polygon_symbol=symbol,
                    angle_degrees=angle,
                    axis=axis,
                    duration_ms=duration,
                )
            )

        collisions_detected = False
        warnings: List[str] = []
        if self._config.collision_guard and steps:
            collisions_detected, warnings = self._collision_guard(components, scaler)

        return FoldSequence(
            polyform_id=polyform_id,
            steps=steps,
            collisions_detected=collisions_detected,
            warnings=warnings,
            lod_levels_used=lod_levels,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _resolve_components(self, polyform_id: str) -> List[Dict[str, Any]]:
        primitives = self._geometry.get("primitives", {}) if isinstance(self._geometry, Mapping) else {}
        if polyform_id in primitives:
            return [primitives[polyform_id]]

        # Allow lookup by primitive symbol (A–R)
        for entry in primitives.values():
            if entry.get("symbol") == polyform_id:
                return [entry]

        polyhedra = self._geometry.get("polyhedra", {}) if isinstance(self._geometry, Mapping) else {}
        if polyform_id in polyhedra:
            resolved: List[Dict[str, Any]] = []
            components = polyhedra[polyform_id].get("components", [])
            for component in components:
                if isinstance(component, str):
                    resolved.extend(self._resolve_components(component))
                elif isinstance(component, Mapping):
                    resolved.append(dict(component))
            return resolved

        return []

    def _symbol_for_component(self, component: Mapping[str, Any], sides: int) -> str:
        symbol = component.get("symbol")
        if isinstance(symbol, str):
            return symbol
        name_to_symbol = {
            "triangle": "A",
            "square": "B",
            "pentagon": "C",
            "hexagon": "D",
        }
        return name_to_symbol.get(component.get("name", ""), f"S{sides}")

    def _derive_fold_angle(self, polyform_id: str, component: Mapping[str, Any], scaler: float) -> float:
        sides = int(component.get("sides", 3))
        base_angle = 180.0 - (360.0 / max(sides, 3))
        scaler_entry = self._lookup_scaler_entry(polyform_id)
        bias = 1.0
        if scaler_entry:
            preferred_scale = scaler_entry.get("attachment_scaler_ranges", {})
            if preferred_scale and isinstance(preferred_scale, Mapping):
                first_range = next(iter(preferred_scale.values()))
                preferred = float(first_range.get("preferred_scale", 1.0))
                bias = preferred
        adjusted = base_angle * self._config.base_angle_scale * scaler * bias
        return float(max(0.0, min(adjusted, 180.0)))

    def _derive_axis(self, component: Mapping[str, Any]) -> Tuple[float, float, float]:
        bbox = component.get("bounding_box")
        if isinstance(bbox, Mapping):
            axis = np.asarray(bbox.get("max", (1.0, 0.0, 0.0))) - np.asarray(bbox.get("min", (0.0, 0.0, 0.0)))
        else:
            vertices = np.asarray(component.get("vertices", ((1.0, 0.0, 0.0),)), dtype=float)
            if vertices.size == 0:
                axis = np.asarray((1.0, 0.0, 0.0), dtype=float)
            else:
                axis = vertices.ptp(axis=0)
        norm = np.linalg.norm(axis)
        if norm <= self._config.axis_epsilon:
            return (1.0, 0.0, 0.0)
        normalized = axis / norm
        return (float(normalized[0]), float(normalized[1]), float(normalized[2]))

    def _estimate_duration(self, angle: float, scaler: float, sides: int) -> float:
        base = max(angle / max(sides, 1), self._config.min_duration_ms)
        duration = base * self._config.duration_scale * scaler
        return float(duration)

    def _collision_guard(self, components: Iterable[Mapping[str, Any]], scaler: float) -> Tuple[bool, List[str]]:
        boxes = []
        for component in components:
            bbox = self._component_bbox(component)
            if bbox is None:
                continue
            scaled = (
                tuple(float(value) * scaler for value in bbox[0]),
                tuple(float(value) * scaler for value in bbox[1]),
            )
            boxes.append(scaled)

        warnings: List[str] = []
        for i, first in enumerate(boxes):
            for j in range(i + 1, len(boxes)):
                second = boxes[j]
                if self._boxes_overlap(first, second):
                    warnings.append(f"bbox_overlap:{i}-{j}")
        return (len(warnings) > 0, warnings)

    def _component_bbox(self, component: Mapping[str, Any]) -> Optional[Tuple[Tuple[float, float, float], Tuple[float, float, float]]]:
        bbox = component.get("bounding_box")
        if isinstance(bbox, Mapping):
            minimum = bbox.get("min")
            maximum = bbox.get("max")
            if isinstance(minimum, Sequence) and isinstance(maximum, Sequence):
                return (tuple(float(value) for value in minimum), tuple(float(value) for value in maximum))
        vertices = component.get("vertices")
        if isinstance(vertices, Sequence) and vertices:
            array = np.asarray(vertices, dtype=float)
            minimum = tuple(float(value) for value in np.min(array, axis=0))
            maximum = tuple(float(value) for value in np.max(array, axis=0))
            return (minimum, maximum)
        return None

    def _lookup_scaler_entry(self, polyform_id: str) -> Optional[Mapping[str, Any]]:
        polyforms = self._scaler.get("polyforms", {}) if isinstance(self._scaler, Mapping) else {}
        if polyform_id in polyforms:
            return polyforms[polyform_id]
        for entry in polyforms.values():
            if entry.get("symbol") == polyform_id:
                return entry
        return None

    def _lod_levels(self, polyform_id: str) -> Sequence[int]:
        polyforms = self._lod.get("polyforms", {}) if isinstance(self._lod, Mapping) else {}
        entry = polyforms.get(polyform_id)
        if not isinstance(entry, Mapping):
            return []
        levels = entry.get("levels", [])
        return [int(level.get("level", 0)) for level in levels if isinstance(level, Mapping)]

    @staticmethod
    def _boxes_overlap(
        first: Tuple[Tuple[float, float, float], Tuple[float, float, float]],
        second: Tuple[Tuple[float, float, float], Tuple[float, float, float]],
    ) -> bool:
        for axis in range(3):
            if first[1][axis] < second[0][axis] or second[1][axis] < first[0][axis]:
                return False
        return True


__all__ = ["FoldSequencer", "FoldSequence", "FoldStep", "SequencerConfig"]
