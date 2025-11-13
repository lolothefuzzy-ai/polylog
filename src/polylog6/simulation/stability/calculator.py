"""Stability calculator used by Tier 3 ingestion and promotion pipelines."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from statistics import fmean, pvariance
from typing import Sequence

from polylog6.storage.encoder import EncodedPolygon


def _clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


@dataclass(slots=True)
class StabilityObservation:
    """Breakdown of the intermediate stability components."""

    symmetry: float
    fold_penalty: float
    edge_balance: float

    @property
    def score(self) -> float:
        """Return the final stability score derived from the components."""

        base = self.symmetry * (1.0 - self.fold_penalty) * self.edge_balance
        return _clamp(base)

    def as_dict(self) -> dict[str, float]:
        """Expose a serialisable representation used by raw metrics."""

        return {
            "stability_symmetry": self.symmetry,
            "stability_fold_penalty": self.fold_penalty,
            "stability_edge_balance": self.edge_balance,
            "stability_score": self.score,
        }


class StabilityCalculator:
    """Estimate stability from encoded polygons using heuristic measures."""

    def compute(
        self,
        polygons: Sequence[EncodedPolygon],
        *,
        require_two_axes: bool = False,
    ) -> StabilityObservation:
        """Compute a stability observation for the provided polygons.

        Parameters
        ----------
        polygons:
            Iterable of :class:`EncodedPolygon` instances for the assembly.
        require_two_axes:
            When ``True`` the symmetry score is softened for planar assemblies to
            avoid overconfidence on degenerate shapes.
        """

        polygons = list(polygons)
        if not polygons:
            return StabilityObservation(symmetry=0.0, fold_penalty=1.0, edge_balance=0.0)

        symmetry = self._symmetry_score(polygons, require_two_axes=require_two_axes)
        fold_penalty = self._fold_penalty(polygons)
        edge_balance = self._edge_balance(polygons)

        return StabilityObservation(
            symmetry=_clamp(symmetry),
            fold_penalty=_clamp(fold_penalty),
            edge_balance=_clamp(edge_balance),
        )

    def _symmetry_score(
        self,
        polygons: Sequence[EncodedPolygon],
        *,
        require_two_axes: bool,
    ) -> float:
        if len(polygons) == 1:
            return 1.0

        deltas = [polygon.delta for polygon in polygons]
        xs = [delta[0] for delta in deltas]
        ys = [delta[1] for delta in deltas]
        zs = [delta[2] for delta in deltas]

        centroid = (fmean(xs), fmean(ys), fmean(zs))
        distances = [
            ((delta[0] - centroid[0]) ** 2 + (delta[1] - centroid[1]) ** 2 + (delta[2] - centroid[2]) ** 2) ** 0.5
            for delta in deltas
        ]

        if not distances:
            return 1.0

        dispersion = pvariance(distances) if len(distances) > 1 else 0.0
        if require_two_axes and all(delta[2] == deltas[0][2] for delta in deltas):
            dispersion *= 1.25
        return 1.0 / (1.0 + dispersion)

    def _fold_penalty(self, polygons: Sequence[EncodedPolygon]) -> float:
        rotations = [abs(polygon.rotation_count) for polygon in polygons]
        max_rotation = max(rotations) if rotations else 0
        if max_rotation == 0:
            rotation_penalty = 0.0
        else:
            rotation_penalty = _clamp(fmean(rotations) / max(max_rotation, 1), 0.0, 1.0)

        orientation_counts = Counter(polygon.orientation_index for polygon in polygons)
        dominant_orientation = orientation_counts.most_common(1)[0][1]
        orientation_penalty = 1.0 - (dominant_orientation / len(polygons))

        return _clamp((rotation_penalty + orientation_penalty) / 2.0, 0.0, 1.0)

    def _edge_balance(self, polygons: Sequence[EncodedPolygon]) -> float:
        counts = Counter(polygon.sides for polygon in polygons)
        if not counts:
            return 0.0
        min_count = min(counts.values())
        max_count = max(counts.values())
        if max_count == 0:
            return 0.0
        return min_count / max_count


__all__ = ["StabilityCalculator", "StabilityObservation"]
