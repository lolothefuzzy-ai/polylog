"""Stability analysis utilities for polyform assemblies."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Optional

import numpy as np

_logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class StabilityMetrics:
    """Container for intermediate stability values."""

    base: float
    connectivity: float
    symmetry: float

    def combined(self) -> float:
        """Return the clamped geometric mean of the components."""

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
        """Compute a normalized stability score for ``assembly``."""

        _logger.debug("Calculating stability for assembly %s", getattr(assembly, "id", "<unknown>"))

        direct_metric = getattr(assembly, "calculate_stability", None)
        if callable(direct_metric) and direct_metric is not self.calculate_stability:
            result = _try_float(direct_metric)
            if result is None:
                result = _try_float(direct_metric, assembly)
            if result is not None:
                _logger.debug("Using assembly-provided stability metric: %s", result)
                return result

        if callable(self._custom_metric):
            result = _try_float(self._custom_metric, assembly)
            if result is not None:
                _logger.debug("Using custom stability metric override: %s", result)
                return result

        try:
            polyforms = _safe_iterable(assembly, "get_all_polyforms")
            bonds = _safe_iterable(assembly, "get_bonds")
        except AttributeError:
            _logger.warning("Assembly missing geometry APIs; returning default score %s", self._default_score)
            return self._default_score

        if polyforms is None:
            _logger.warning("Assembly returned no polyforms; using default score %s", self._default_score)
            return self._default_score

        metrics = self._compute_metrics(polyforms, bonds)
        combined = metrics.combined()
        _logger.debug(
            "Stability metrics computed: base=%s connectivity=%s symmetry=%s combined=%s",
            metrics.base,
            metrics.connectivity,
            metrics.symmetry,
            combined,
        )
        return combined

    def _compute_metrics(
        self,
        polyforms: Iterable[Dict[str, Any]],
        bonds: Optional[Iterable[Dict[str, Any]]],
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


def _safe_iterable(obj: Any, method: str) -> Optional[Iterable]:
    """Return iterable from ``obj.method`` when available, otherwise ``None``."""

    func = getattr(obj, method, None)
    if not callable(func):
        return None
    try:
        value = func()
    except TypeError:
        value = func(obj)
    except Exception:  # pragma: no cover - defensive guard
        return None
    if value is None:
        return None
    try:
        iter(value)
    except TypeError:
        return None
    return value


def _try_float(func: Callable[..., Any], *args: Any) -> Optional[float]:
    """Call ``func`` with ``args`` and coerce the result to a clipped float."""

    try:
        value = func(*args)
    except Exception:  # pragma: no cover - defensive guard
        return None

    try:
        scalar = float(value)
    except (TypeError, ValueError):
        return None

    return float(np.clip(scalar, 0.0, 1.0))


__all__ = ["StabilityAnalyzer", "StabilityMetrics"]
