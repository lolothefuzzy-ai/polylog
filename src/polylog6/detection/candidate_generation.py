"""Candidate generation scaffolding for INT-014."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, Iterable, List, Optional

from .models import Candidate
from .topology import HullSummary


class CandidateGenerator:
    """Produce placeholder candidates based on descriptors."""

    def __init__(self, polyform_library: Iterable[str] | None = None) -> None:
        self.polyform_library = list(polyform_library or ["square", "hexagon", "triangle"])

    def generate(
        self,
        regions: List[Dict[str, Any]],
        descriptors: Dict[int, Dict[str, Any]],
        hulls: Optional[Dict[int, HullSummary]] = None,
    ) -> List[Candidate]:
        candidates: List[Candidate] = []
        for region in regions:
            label = int(region.get("label", -1))
            if label < 0:
                continue
            descriptor = descriptors.get(label, {})
            hull_summary = (hulls or {}).get(label)
            hull_metrics = self._compute_hull_metrics(hull_summary)
            score = self._score_candidate(descriptor, hull_metrics)
            for polyform in self.polyform_library:
                candidates.append(
                    Candidate(
                        region_label=label,
                        polyform_type=polyform,
                        score=score,
                        metadata={
                            "descriptor": descriptor,
                            "hull": asdict(hull_summary) if hull_summary else None,
                            "hull_metrics": hull_metrics,
                        },
                    )
                )
        return candidates

    def _score_candidate(self, descriptor: Dict[str, Any], hull_metrics: Dict[str, float]) -> float:
        descriptor_score = self._descriptor_score(descriptor)

        compactness_bonus = min(1.0, hull_metrics.get("compactness", 0.0)) * 0.3
        density_bonus = min(1.0, hull_metrics.get("density", 0.0)) * 0.2
        thickness_bonus = 0.0
        thickness = hull_metrics.get("thickness", 0.0)
        if thickness > 0.0:
            thickness_bonus = min(1.0, thickness / max(hull_metrics.get("planar_area", 1.0) ** 0.5, 1.0)) * 0.1

        return float(descriptor_score + compactness_bonus + density_bonus + thickness_bonus)

    def _descriptor_score(self, descriptor: Dict[str, Any]) -> float:
        periods = descriptor.get("periods", [])
        symmetries = descriptor.get("symmetries", {})
        edge_complexity = descriptor.get("edge_complexity", 0)

        top_periods = sum(p[2] for p in periods[:3]) if periods else 0.0
        symmetry_bonus = sum(symmetries.values())
        complexity_penalty = max(0.0, 1.0 - min(edge_complexity / 500.0, 1.0))

        return float(top_periods + symmetry_bonus + complexity_penalty)

    def _compute_hull_metrics(self, hull: Optional[HullSummary]) -> Dict[str, float]:
        metrics: Dict[str, float] = {
            "volume": 0.0,
            "planar_area": 0.0,
            "thickness": 0.0,
            "compactness": 0.0,
            "density": 0.0,
        }

        if hull is None:
            return metrics

        volume = float(hull.volume or 0.0)
        metrics["volume"] = volume

        bbox = hull.bounding_box
        if bbox is not None:
            min_corner, max_corner = bbox
            spans = tuple(max(max_val - min_val, 0.0) for min_val, max_val in zip(min_corner, max_corner))
            if len(spans) == 3:
                span_x, span_y, span_z = spans
            else:  # pragma: no cover - defensive fallback
                span_x = span_y = span_z = 0.0

            planar_area = max(span_x, 0.0) * max(span_y, 0.0)
            thickness = max(span_z, 0.0)

            metrics["planar_area"] = planar_area
            metrics["thickness"] = thickness

            non_zero_spans = [span for span in spans if span > 0.0]
            if non_zero_spans:
                shortest = min(non_zero_spans)
                longest = max(non_zero_spans)
                if longest > 0.0:
                    metrics["compactness"] = min(1.0, shortest / longest)

            if planar_area > 0.0:
                metrics["density"] = min(1.0, volume / planar_area)

        return metrics


__all__ = ["CandidateGenerator"]
