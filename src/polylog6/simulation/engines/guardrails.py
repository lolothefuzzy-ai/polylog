"""Guardrail evaluation utilities for simulation checkpoints."""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from statistics import fmean, pvariance
from typing import Callable, List, Optional

from .checkpointing.workspace import PolyformWorkspace

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class GuardrailConfig:
    """Configuration for pre-checkpoint guardrail evaluation."""

    stability_threshold: float = 0.85
    closure_threshold: float = 0.30
    raise_on_breach: bool = False


@dataclass(slots=True)
class GuardrailStatus:
    """Results of guardrail evaluation."""

    stability_score: float = 1.0
    closure_ratio: float = 0.0
    breaches: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    dimension: str = "2d"

    @property
    def passed(self) -> bool:
        return not self.breaches


class GuardrailBreachError(RuntimeError):
    """Raised when guardrails are configured to hard fail on breach."""


def evaluate_guardrails(
    workspace: PolyformWorkspace,
    config: Optional[GuardrailConfig],
    *,
    on_alert: Optional[Callable[[GuardrailStatus], None]] = None,
) -> GuardrailStatus:
    """Evaluate workspace guardrails and optionally emit alerts."""

    status = GuardrailStatus()

    encoded_polygons = list(workspace.iter_encoded_polygons())
    module_refs = workspace.module_references()
    status.dimension = "3d" if module_refs else "2d"
    status.stability_score = _estimate_stability(encoded_polygons)
    status.closure_ratio = _estimate_closure_ratio(len(module_refs), len(encoded_polygons))

    if config:
        if module_refs:
            if status.stability_score < config.stability_threshold:
                status.breaches.append(
                    f"stability {status.stability_score:.3f} < {config.stability_threshold:.2f}"
                )
            if status.closure_ratio < config.closure_threshold:
                status.breaches.append(
                    f"closure {status.closure_ratio:.3f} < {config.closure_threshold:.2f}"
                )
        else:
            status.warnings.append(
                "no module references recorded; treating guardrails as 2D-exempt"
            )
            if status.stability_score < config.stability_threshold:
                status.warnings.append(
                    (
                        f"stability score {status.stability_score:.3f} below 2D advisory"
                        f" ({config.stability_threshold:.2f})"
                    )
                )

    if status.breaches:
        message = (
            "Guardrail breach detected: " + ", ".join(status.breaches)
        )
        logger.warning(message)
        if on_alert:
            on_alert(status)
        if config and config.raise_on_breach:
            raise GuardrailBreachError(message)
    else:
        if status.warnings:
            logger.info(
                "Guardrail warnings: %s",
                "; ".join(status.warnings),
            )
        if on_alert:
            on_alert(status)

    return status


def _estimate_stability(encoded_polygons) -> float:
    """Heuristic stability estimate based on polygon dispersion."""

    if not encoded_polygons:
        return 1.0

    positions = [polygon.delta for polygon in encoded_polygons]
    xs = [pos[0] for pos in positions]
    ys = [pos[1] for pos in positions]
    zs = [pos[2] for pos in positions]

    centroid = (fmean(xs), fmean(ys), fmean(zs))
    distances = [
        math.sqrt((pos[0] - centroid[0]) ** 2 + (pos[1] - centroid[1]) ** 2 + (pos[2] - centroid[2]) ** 2)
        for pos in positions
    ]

    variation = pvariance(distances) if len(distances) > 1 else 0.0
    stability = 1.0 / (1.0 + variation)
    return max(0.0, min(1.0, stability))


def _estimate_closure_ratio(module_ref_count: int, polygon_count: int) -> float:
    """Estimate closure ratio using module references vs. polygons."""

    if polygon_count == 0:
        return 1.0
    if module_ref_count == 0:
        return 0.0
    ratio = module_ref_count / float(polygon_count)
    return max(0.0, min(1.0, ratio))
