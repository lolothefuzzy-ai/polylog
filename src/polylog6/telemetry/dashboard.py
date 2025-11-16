"""Telemetry dashboard scaffolding for compression metrics (INT-005).

Provides a light-weight ingestion and summarisation layer so CI artifacts can be
converted into actionable alerts without requiring a full UI stack yet.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional

_DEFAULT_THRESHOLDS: Dict[str, float] = {
    "compression_ratio_tier1_pct": 85.0,
    "compression_ratio_tier2_pct": 70.0,
}


@dataclass(slots=True)
class CompressionSnapshot:
    """Represents a single compression metrics ingestion."""

    label: str
    polygon_count: int
    chunk_count: int
    avg_chunk_fill: float
    compression_ratio_tier1_pct: float
    compression_ratio_tier2_pct: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    alerts: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialise the snapshot for logging or JSON storage."""

        return {
            "label": self.label,
            "polygon_count": self.polygon_count,
            "chunk_count": self.chunk_count,
            "avg_chunk_fill": self.avg_chunk_fill,
            "compression_ratio_tier1_pct": self.compression_ratio_tier1_pct,
            "compression_ratio_tier2_pct": self.compression_ratio_tier2_pct,
            "metadata": self.metadata,
            "alerts": list(self.alerts),
        }


class CompressionTelemetryDashboard:
    """Ingests compression metrics and produces high-level summaries."""

    def __init__(self, *, thresholds: Optional[Mapping[str, float]] = None) -> None:
        self._thresholds: Dict[str, float] = dict(_DEFAULT_THRESHOLDS)
        if thresholds:
            self._thresholds.update(thresholds)
        self._snapshots: List[CompressionSnapshot] = []

    # ------------------------------------------------------------------
    # Ingestion helpers
    # ------------------------------------------------------------------
    def ingest_metrics(self, label: str, metrics: Mapping[str, Any]) -> CompressionSnapshot:
        """Parse a metrics payload produced by the storage regression harness."""

        size_metrics: MutableMapping[str, Any] = {
            **metrics.get("size_metrics", {}),
        }
        snapshot = CompressionSnapshot(
            label=label,
            polygon_count=int(metrics.get("total_polygons", 0)),
            chunk_count=int(metrics.get("chunk_count", 0)),
            avg_chunk_fill=float(metrics.get("avg_chunk_fill", 0.0)),
            compression_ratio_tier1_pct=float(size_metrics.get("compression_ratio_tier1_pct", 0.0)),
            compression_ratio_tier2_pct=float(size_metrics.get("compression_ratio_tier2_pct", 0.0)),
            metadata={
                "chunk_size": metrics.get("chunk_size"),
                "module_refs": metrics.get("module_refs"),
                "min_chunk_fill": metrics.get("min_chunk_fill"),
                "max_chunk_fill": metrics.get("max_chunk_fill"),
            },
        )
        snapshot.alerts = self._evaluate_thresholds(snapshot)
        self._snapshots.append(snapshot)
        return snapshot

    def ingest_metrics_file(self, path: Path) -> List[CompressionSnapshot]:
        """Load one or more records from a JSON file and ingest them.

        The JSON structure can be one of:

        * ``{"label": "ci-run", "metrics": {...}}``
        * ``[{"label": "runA", "metrics": {...}}, {...}]``
        * ``{"runs": [{"label": "runA", "metrics": {...}}]}``
        """

        data = json.loads(path.read_text(encoding="utf-8"))
        records: Iterable[Mapping[str, Any]]

        if isinstance(data, Mapping) and "metrics" in data:
            records = [data]  # type: ignore[list-item] - safe by construction
        elif isinstance(data, Mapping) and "runs" in data:
            runs = data.get("runs", [])
            if not isinstance(runs, list):
                raise ValueError("Expected 'runs' to be a list")
            records = [record for record in runs if isinstance(record, Mapping)]
        elif isinstance(data, list):
            records = [record for record in data if isinstance(record, Mapping)]
        else:
            raise ValueError("Unsupported metrics JSON structure")

        ingested: List[CompressionSnapshot] = []
        for record in records:
            label = str(record.get("label", "run"))
            metrics = record.get("metrics")
            if not isinstance(metrics, Mapping):
                raise ValueError("Each record must contain a 'metrics' mapping")
            ingested.append(self.ingest_metrics(label, metrics))
        return ingested

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------
    def snapshots(self) -> List[CompressionSnapshot]:
        return list(self._snapshots)

    def summary(self) -> Dict[str, Any]:
        if not self._snapshots:
            return {"runs": 0, "breaches": 0, "averages": {}, "worst_case": {}}

        runs = len(self._snapshots)
        breaches = sum(1 for snapshot in self._snapshots if snapshot.alerts)

        tier1_values = [snapshot.compression_ratio_tier1_pct for snapshot in self._snapshots]
        tier2_values = [snapshot.compression_ratio_tier2_pct for snapshot in self._snapshots]

        worst_snapshot = min(self._snapshots, key=lambda snap: snap.compression_ratio_tier2_pct)

        return {
            "runs": runs,
            "breaches": breaches,
            "averages": {
                "compression_ratio_tier1_pct": sum(tier1_values) / runs,
                "compression_ratio_tier2_pct": sum(tier2_values) / runs,
            },
            "worst_case": worst_snapshot.to_dict(),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _evaluate_thresholds(self, snapshot: CompressionSnapshot) -> List[str]:
        alerts: List[str] = []
        tier1_threshold = self._thresholds.get("compression_ratio_tier1_pct")
        tier2_threshold = self._thresholds.get("compression_ratio_tier2_pct")

        if tier1_threshold is not None and snapshot.compression_ratio_tier1_pct < tier1_threshold:
            alerts.append(
                f"tier1 compression {snapshot.compression_ratio_tier1_pct:.2f}% < {tier1_threshold:.2f}%"
            )
        if tier2_threshold is not None and snapshot.compression_ratio_tier2_pct < tier2_threshold:
            alerts.append(
                f"tier2 compression {snapshot.compression_ratio_tier2_pct:.2f}% < {tier2_threshold:.2f}%"
            )

        return alerts


__all__ = ["CompressionTelemetryDashboard", "CompressionSnapshot"]
