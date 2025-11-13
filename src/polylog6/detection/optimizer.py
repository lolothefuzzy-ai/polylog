"""Optimizer stubs for selecting candidates and computing coverage."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

from .models import Candidate, DecompositionPlan
from .topology import HullSummary


@dataclass(slots=True)
class OptimizationOptions:
    """Placeholder optimization parameters."""

    max_candidates_per_region: int = 1


class CandidateOptimizer:
    """Pick top candidates per region and compute aggregate stats."""

    def __init__(self, *, options: OptimizationOptions | None = None) -> None:
        self.options = options or OptimizationOptions()

    def optimize(
        self,
        candidates: Iterable[Candidate],
        *,
        expected_region_count: Optional[int] = None,
        hulls: Optional[Dict[int, HullSummary]] = None,
    ) -> DecompositionPlan:
        best_by_region: Dict[int, List[Candidate]] = {}
        for cand in candidates:
            best_by_region.setdefault(cand.region_label, []).append(cand)

        chosen: List[Candidate] = []
        for region_label, region_candidates in best_by_region.items():
            sorted_candidates = sorted(region_candidates, key=lambda c: c.score, reverse=True)
            chosen.extend(sorted_candidates[: self.options.max_candidates_per_region])

        region_count = expected_region_count or len(best_by_region) or 1
        coverage_percent = float(len(best_by_region) / region_count * 100.0)
        avg_score = float(sum(c.score for c in chosen) / len(chosen)) if chosen else 0.0
        hull_stats = {}
        if hulls:
            hull_stats = {
                "hull_count": len(hulls),
                "total_volume": float(sum((summary.volume or 0.0) for summary in hulls.values())),
            }

        stats = {
            "regions_covered": len(best_by_region),
            "avg_score": avg_score,
        }
        if hull_stats:
            stats["hull"] = hull_stats
        return DecompositionPlan(candidates=chosen, coverage_percent=coverage_percent, stats=stats)


__all__ = ["CandidateOptimizer", "OptimizationOptions"]
