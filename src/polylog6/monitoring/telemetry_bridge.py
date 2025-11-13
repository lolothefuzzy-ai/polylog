"""Detection telemetry bridge utilities for monitoring convergence (INT-014 ↔ INT-004).

This module exposes a lightweight adapter that can ingest detection pipeline
telemetry payloads and convert them into snapshots suitable for monitoring or
alerting frameworks.  The bridge mirrors the structure of
:class:`CompressionTelemetryDashboard` so downstream dashboards can present
consistent summaries.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Mapping, MutableSequence, Optional

DEFAULT_THRESHOLDS: Dict[str, float] = {
    "coverage_percent_min": 40.0,
    "hull_region_min": 1.0,
    "avg_candidate_score_min": 1.5,
}


@dataclass(slots=True)
class DetectionTelemetrySnapshot:
    """Structured view of a single detection telemetry payload."""

    request_id: Optional[str]
    region_count: int
    coverage_percent: float
    hull_region_count: int
    hull_volume_total: float
    topology_backend: Optional[str]
    avg_candidate_score: float
    timestamp: float = field(default_factory=lambda: time.time())
    alerts: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "region_count": self.region_count,
            "coverage_percent": self.coverage_percent,
            "hull_region_count": self.hull_region_count,
            "hull_volume_total": self.hull_volume_total,
            "topology_backend": self.topology_backend,
            "avg_candidate_score": self.avg_candidate_score,
            "timestamp": self.timestamp,
            "alerts": list(self.alerts),
            "metadata": dict(self.metadata),
        }


class DetectionTelemetryBridge:
    """Aggregate detection telemetry snapshots for monitoring consumers."""

    def __init__(self, *, thresholds: Optional[Mapping[str, float]] = None) -> None:
        self._thresholds: Dict[str, float] = dict(DEFAULT_THRESHOLDS)
        if thresholds:
            self._thresholds.update(thresholds)
        self._snapshots: MutableSequence[DetectionTelemetrySnapshot] = []

    # ------------------------------------------------------------------
    # Ingestion helpers
    # ------------------------------------------------------------------
    def emit(self, payload: Mapping[str, Any]) -> DetectionTelemetrySnapshot:
        """Convert a detection telemetry payload into a snapshot."""

        snapshot = DetectionTelemetrySnapshot(
            request_id=_optional_str(payload.get("request_id")),
            region_count=int(payload.get("region_count", 0)),
            coverage_percent=float(payload.get("coverage_percent", 0.0)),
            hull_region_count=int(payload.get("hull_region_count", 0)),
            hull_volume_total=float(payload.get("hull_volume_total", 0.0)),
            topology_backend=_optional_str(payload.get("topology_backend")),
            avg_candidate_score=float(payload.get("avg_candidate_score", 0.0)),
            metadata={
                "candidate_count": payload.get("candidate_count"),
                "topology": payload.get("topology"),
            },
        )
        snapshot.alerts = self._evaluate_thresholds(snapshot)
        self._snapshots.append(snapshot)
        return snapshot

    def sink(self) -> Callable[[Mapping[str, Any]], None]:
        """Return a callable suitable for `ImageDetectionService.telemetry_emitter`."""

        def _sink(payload: Mapping[str, Any]) -> None:
            self.emit(payload)

        return _sink

    # ------------------------------------------------------------------
    # Reporting helpers
    # ------------------------------------------------------------------
    def snapshots(self) -> List[DetectionTelemetrySnapshot]:
        return list(self._snapshots)

    def summary(self) -> Dict[str, Any]:
        if not self._snapshots:
            return {"runs": 0, "breaches": 0, "averages": {}, "worst_case": {}}

        runs = len(self._snapshots)
        breaches = sum(1 for snap in self._snapshots if snap.alerts)
        coverage_values = [snap.coverage_percent for snap in self._snapshots]
        score_values = [snap.avg_candidate_score for snap in self._snapshots]
        hull_values = [snap.hull_region_count for snap in self._snapshots]

        worst_snapshot = min(self._snapshots, key=lambda snap: snap.coverage_percent)

        return {
            "runs": runs,
            "breaches": breaches,
            "averages": {
                "coverage_percent": sum(coverage_values) / runs,
                "avg_candidate_score": sum(score_values) / runs,
                "hull_region_count": sum(hull_values) / runs,
            },
            "worst_case": worst_snapshot.to_dict(),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _evaluate_thresholds(self, snapshot: DetectionTelemetrySnapshot) -> List[str]:
        alerts: List[str] = []

        coverage_min = self._thresholds.get("coverage_percent_min")
        if coverage_min is not None and snapshot.coverage_percent < coverage_min:
            alerts.append(
                f"coverage {snapshot.coverage_percent:.1f}% < {coverage_min:.1f}% threshold"
            )

        hull_min = self._thresholds.get("hull_region_min")
        if hull_min is not None and snapshot.hull_region_count < hull_min:
            alerts.append(
                f"hull regions {snapshot.hull_region_count} < {int(hull_min)} minimum"
            )

        score_min = self._thresholds.get("avg_candidate_score_min")
        if score_min is not None and snapshot.avg_candidate_score < score_min:
            alerts.append(
                f"avg candidate score {snapshot.avg_candidate_score:.2f} < {score_min:.2f}"
            )

        return alerts


def _optional_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    return str(value)


__all__ = ["DetectionTelemetryBridge", "DetectionTelemetrySnapshot"]
