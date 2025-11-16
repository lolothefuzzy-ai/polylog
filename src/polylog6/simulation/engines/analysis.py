"""Analysis utilities: stability scoring and fold optimization."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence

import numpy as np


# ---------------------------------------------------------------------------
# Stability analysis
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class StabilityMetrics:
    """Container for intermediate stability components."""

    base: float
    connectivity: float
    symmetry: float

    def combined(self) -> float:
        product = max(self.base * self.connectivity * self.symmetry, 1e-9)
        return float(np.clip(product ** (1.0 / 3.0), 0.0, 1.0))


class StabilityAnalyzer:
    """Estimate assembly stability using lightweight geometric heuristics."""

    def __init__(self, *, config: Optional[Dict[str, Any]] = None) -> None:
        self._config = config or {}
        self._default_score: float = float(self._config.get("default_score", 0.9))
        self._symmetry_weight: float = float(self._config.get("symmetry_weight", 1.0))
        self._connectivity_bias: float = float(self._config.get("connectivity_bias", 0.0))
        self._custom_metric: Optional[Callable[..., float]] = self._config.get("custom_metric")

    def calculate_stability(self, assembly: Any) -> float:
        direct_metric = getattr(assembly, "calculate_stability", None)
        if callable(direct_metric) and direct_metric is not self.calculate_stability:
            result = _try_float(direct_metric)
            if result is None:
                result = _try_float(direct_metric, assembly)
            if result is not None:
                return result

        if callable(self._custom_metric):
            result = _try_float(self._custom_metric, assembly)
            if result is not None:
                return result

        try:
            polyforms = _safe_iterable(assembly, "get_all_polyforms")
            bonds = _safe_iterable(assembly, "get_bonds")
        except AttributeError:
            return self._default_score

        if polyforms is None:
            return self._default_score

        metrics = self._compute_metrics(polyforms, bonds)
        return metrics.combined()

    def _compute_metrics(
        self, polyforms: Iterable[Dict[str, Any]], bonds: Optional[Iterable[Dict[str, Any]]]
    ) -> StabilityMetrics:
        count = 0
        centroids: List[np.ndarray] = []
        side_counts: List[int] = []
        for polyform in polyforms:
            count += 1
            vertices = np.asarray(polyform.get("vertices", ()), dtype=float)
            if vertices.size:
                centroids.append(vertices.mean(axis=0))
            sides = int(polyform.get("sides", max(len(vertices), 1)))
            side_counts.append(max(sides, 3))

        if count == 0:
            return StabilityMetrics(self._default_score, self._default_score, self._default_score)

        base_score = np.clip(0.6 + 0.04 * np.mean(side_counts), 0.0, 1.0)

        bond_count = len(list(bonds)) if bonds is not None else 0
        max_possible_bonds = max(count * (count - 1) / 2.0, 1.0)
        connectivity_score = np.clip(bond_count / max_possible_bonds + self._connectivity_bias, 0.0, 1.0)

        symmetry_score = 1.0
        if len(centroids) >= 2:
            centroids_array = np.asarray(centroids)
            center = centroids_array.mean(axis=0)
            deviances = np.linalg.norm(centroids_array - center, axis=1)
            if deviances.size:
                normalized_var = np.var(deviances) / (np.mean(deviances) + 1e-6)
                symmetry_score = np.clip(1.0 / (1.0 + normalized_var), 0.2, 1.0)
        symmetry_score = np.clip(symmetry_score * self._symmetry_weight, 0.0, 1.0)

        return StabilityMetrics(
            base=float(base_score),
            connectivity=float(connectivity_score),
            symmetry=float(symmetry_score),
        )


def _safe_iterable(obj: Any, method: str) -> Optional[Iterable[Any]]:
    func = getattr(obj, method, None)
    if not callable(func):
        return None
    try:
        value = func()
    except TypeError:
        value = func(obj)
    except Exception:
        return None
    if value is None:
        return None
    try:
        iter(value)
    except TypeError:
        return None
    return value


def _try_float(func: Callable[..., Any], *args: Any) -> Optional[float]:
    try:
        value = func(*args)
    except Exception:
        return None
    try:
        scalar = float(value)
    except (TypeError, ValueError):
        return None
    return float(np.clip(scalar, 0.0, 1.0))


# ---------------------------------------------------------------------------
# Fold optimization
# ---------------------------------------------------------------------------
class OptimizationEngine:
    """Heuristic fold optimizer that nudges assemblies toward stability."""

    def __init__(self, *, config: Optional[Dict[str, Any]] = None) -> None:
        self._config = config or {}
        self._stability_target: float = float(self._config.get("target_stability", 0.85))
        self._max_step: float = float(self._config.get("max_step", 15.0))
        self._analyzer = self._config.get("stability_analyzer") or StabilityAnalyzer()

    def optimize_fold(self, assembly: Any) -> Any:
        current_angles = _coerce_sequence(getattr(assembly, "get_fold_angles", None))
        if current_angles:
            optimized = self._nudge_angles(current_angles, assembly)
            setter = getattr(assembly, "set_fold_angles", None)
            if callable(setter):
                setter(optimized)
        # Allow assemblies without these APIs to pass through untouched
        return assembly

    def _nudge_angles(self, angles: Sequence[float], assembly: Any) -> List[float]:
        if not angles:
            return []
        current_score = _try_float(self._analyzer.calculate_stability, assembly) or 0.0
        delta = self._stability_target - current_score
        step = np.clip(delta * 10.0, -self._max_step, self._max_step)
        # Move angles toward 90° with bounded step
        target = np.deg2rad(90.0)
        adjusted: List[float] = []
        for angle in angles:
            rad = np.deg2rad(angle)
            nudged = rad + np.deg2rad(step) * np.sign(target - rad)
            adjusted.append(np.rad2deg(nudged))
        return adjusted


def _coerce_sequence(candidate: Optional[Callable[[], Sequence[float]]]) -> List[float]:
    if not callable(candidate):
        return []
    try:
        values = candidate()
    except Exception:
        return []
    if values is None:
        return []
    return list(values)


__all__ = ["OptimizationEngine", "StabilityAnalyzer", "StabilityMetrics"]
