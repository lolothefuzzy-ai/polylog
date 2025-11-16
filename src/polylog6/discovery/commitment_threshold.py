"""Visualization commitment threshold logic for closure discovery."""
from __future__ import annotations

import logging
from enum import Enum
from typing import List, Optional, Tuple

LOGGER = logging.getLogger(__name__)


class CommitmentDecision(Enum):
    """Reasons explaining why a closure was accepted or rejected."""

    HIGH_TIER_HIGH_CLOSURE = "tier >= 5 and closure >= 0.88"
    EXCEPTIONAL_SYMMETRY = "symmetry in {T,O,I} and priority >= 12.0"
    VERY_HIGH_PRIORITY = "priority >= 18.0"
    REJECTED = "did not meet any threshold"


class VisualizationCommitmentThreshold:
    """Centralised rules for deciding visualization commitments."""

    HIGH_TIER = 5
    HIGH_CLOSURE_RATIO = 0.88
    SYMMETRY_WHITELIST = {"T", "O", "I"}
    SYMMETRY_PRIORITY = 12.0
    PRIORITY_HARD_MIN = 18.0

    @staticmethod
    def should_commit(
        *,
        tier: int,
        closure_ratio: float,
        symmetry_group: str,
        priority_score: float,
        worker_id: Optional[str] = None,
    ) -> Tuple[bool, CommitmentDecision]:
        """Return whether visualization should be committed and why."""

        prefix = f"[{worker_id or 'discovery'}]"

        if tier >= VisualizationCommitmentThreshold.HIGH_TIER and closure_ratio >= VisualizationCommitmentThreshold.HIGH_CLOSURE_RATIO:
            LOGGER.info(
                "%s COMMIT: tier=%s closure=%.2f -> %s",
                prefix,
                tier,
                closure_ratio,
                CommitmentDecision.HIGH_TIER_HIGH_CLOSURE.value,
            )
            return True, CommitmentDecision.HIGH_TIER_HIGH_CLOSURE

        if (
            symmetry_group in VisualizationCommitmentThreshold.SYMMETRY_WHITELIST
            and priority_score >= VisualizationCommitmentThreshold.SYMMETRY_PRIORITY
        ):
            LOGGER.info(
                "%s COMMIT: symmetry=%s priority=%.2f -> %s",
                prefix,
                symmetry_group,
                priority_score,
                CommitmentDecision.EXCEPTIONAL_SYMMETRY.value,
            )
            return True, CommitmentDecision.EXCEPTIONAL_SYMMETRY

        if priority_score >= VisualizationCommitmentThreshold.PRIORITY_HARD_MIN:
            LOGGER.info(
                "%s COMMIT: priority=%.2f -> %s",
                prefix,
                priority_score,
                CommitmentDecision.VERY_HIGH_PRIORITY.value,
            )
            return True, CommitmentDecision.VERY_HIGH_PRIORITY

        LOGGER.debug(
            "%s REJECT: tier=%s closure=%.2f symmetry=%s priority=%.2f",
            prefix,
            tier,
            closure_ratio,
            symmetry_group,
            priority_score,
        )
        return False, CommitmentDecision.REJECTED

    @staticmethod
    def extract_menu_contexts(
        *,
        tier: int,
        closure_ratio: float,
        symmetry_group: str,
    ) -> List[str]:
        """Produce UI menu contexts for committed assets."""

        contexts: List[str] = []

        if symmetry_group in VisualizationCommitmentThreshold.SYMMETRY_WHITELIST:
            contexts.append(f"workspace_symmetry_{symmetry_group.lower()}")

        if closure_ratio >= 0.90:
            contexts.append("closure_ratio_very_high")
        elif closure_ratio >= 0.80:
            contexts.append("closure_ratio_high")

        if tier >= VisualizationCommitmentThreshold.HIGH_TIER:
            contexts.append(f"tier_{tier}")

        return contexts
