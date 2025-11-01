"""Prometheus metrics service and KPI registry for Polylog6."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

try:  # Optional dependency for Prometheus metrics export
    from prometheus_client import (  # type: ignore
        Counter,
        Gauge,
        Summary,
        start_http_server,
    )
except Exception:  # pragma: no cover - Prometheus support is optional
    Counter = Gauge = Summary = None
    start_http_server = None


# Default schema path (project_root/Properties/ALLDOCS/metrics/kpi_schema.json)
_SCHEMA_DEFAULT = (
    Path(__file__).resolve().parents[3]
    / "Properties"
    / "ALLDOCS"
    / "metrics"
    / "kpi_schema.json"
)


@dataclass(frozen=True)
class KPI:
    """Describes a single KPI entry loaded from the schema."""

    key: str
    name: str
    unit: str
    threshold: float
    slo: str
    collection: str
    calculation: str
    alert_level: str
    definition: str
    links: List[str]
    owner: str


class KPIRegistry:
    """Runtime registry for KPI definitions and auxiliary metadata."""

    def __init__(self, schema_path: Optional[Path] = None) -> None:
        self.schema_path: Path = schema_path or _SCHEMA_DEFAULT
        self.version: Optional[str] = None
        self.schema_date: Optional[str] = None
        self.description: Optional[str] = None
        self.platforms: List[str] = []
        self.reporting_cadence: Dict[str, List[str]] = {}
        self.alert_escalation: Dict[str, Dict[str, Any]] = {}
        self._kpis: Dict[str, KPI] = {}
        self.refresh()

    def refresh(self) -> None:
        """Reload the KPI schema from disk."""

        if not self.schema_path.exists():
            raise FileNotFoundError(f"KPI schema not found: {self.schema_path}")

        with self.schema_path.open("r", encoding="utf-8") as fp:
            raw = json.load(fp)

        self.version = raw.get("version")
        self.schema_date = raw.get("schema_date")
        self.description = raw.get("description")
        self.platforms = list(raw.get("platforms", []))
        self.reporting_cadence = raw.get("reporting_cadence", {})
        self.alert_escalation = raw.get("alert_escalation", {})

        self._kpis = {}
        for key, entry in raw.get("kpis", {}).items():
            try:
                kpi = KPI(
                    key=key,
                    name=entry["name"],
                    unit=entry["unit"],
                    threshold=float(entry["threshold"]),
                    slo=entry["slo"],
                    collection=entry["collection"],
                    calculation=entry["calculation"],
                    alert_level=entry["alert_level"],
                    definition=entry["definition"],
                    links=list(entry.get("links", [])),
                    owner=entry.get("owner", ""),
                )
            except KeyError as exc:  # pragma: no cover - schema-level validation
                raise ValueError(f"Missing KPI field for '{key}': {exc}") from exc
            self._kpis[key] = kpi

    @property
    def keys(self) -> Iterable[str]:
        return self._kpis.keys()

    def get(self, key: str) -> KPI:
        return self._kpis[key]

    def to_dict(self) -> Dict[str, Any]:
        """Return a serialisable view of the registry."""

        return {
            "version": self.version,
            "schema_date": self.schema_date,
            "description": self.description,
            "platforms": self.platforms,
            "reporting_cadence": self.reporting_cadence,
            "alert_escalation": self.alert_escalation,
            "kpis": {key: kpi.__dict__ for key, kpi in self._kpis.items()},
        }

    def build_payload(self, samples: Dict[str, float]) -> Dict[str, Any]:
        """Build a telemetry payload that pairs KPI metadata with sample values."""

        payload = {"version": self.version, "schema_date": self.schema_date, "samples": []}

        for key, value in samples.items():
            if key not in self._kpis:
                continue
            kpi = self._kpis[key]
            payload["samples"].append(
                {
                    "key": key,
                    "value": value,
                    "unit": kpi.unit,
                    "threshold": kpi.threshold,
                    "alert_level": kpi.alert_level,
                }
            )

        return payload


class MetricsService:
    """Expose Prometheus metrics and KPI utilities."""

    def __init__(self) -> None:
        self._prometheus_available = Counter is not None
        if self._prometheus_available:
            self._celery_task_duration = Summary(
                "polylog_celery_task_duration_seconds", "Celery task duration"
            )
            self._celery_worker_gauge = Gauge(
                "polylog_celery_workers", "Number of active Celery workers"
            )
            self._cache_hits = Counter(
                "polylog_stability_cache_hits_total", "Stability cache hit count"
            )
            self._cache_misses = Counter(
                "polylog_stability_cache_misses_total", "Stability cache miss count"
            )
            self._unity_connections_active = Gauge(
                "polylog_unity_connections_active", "Active Unity bridge connections"
            )
            self._unity_connections_total = Counter(
                "polylog_unity_connections_total", "Unity bridge connections established"
            )
            self._unity_messages_out_total = Counter(
                "polylog_unity_messages_out_total", "Unity bridge outbound messages"
            )
            self._unity_messages_in_total = Counter(
                "polylog_unity_messages_in_total", "Unity bridge inbound messages"
            )
            self._unity_reconnect_attempts_total = Counter(
                "polylog_unity_reconnect_attempts_total", "Unity bridge reconnect attempts"
            )
            self._unity_messages_invalid_total = Counter(
                "polylog_unity_messages_invalid_total", "Invalid Unity messages detected"
            )
        self._registry = KPIRegistry()
        self._exporter_started = False

    def start(self, port: int = 8000) -> None:
        if not self._prometheus_available or start_http_server is None or self._exporter_started:
            return
        start_http_server(port)
        self._exporter_started = True

    # ------------------------------------------------------------------
    # KPI utilities
    # ------------------------------------------------------------------
    def get_registry(self) -> KPIRegistry:
        return self._registry

    # ------------------------------------------------------------------
    # Celery metrics
    # ------------------------------------------------------------------
    def observe_celery_task(self, duration_seconds: float) -> None:
        if not self._prometheus_available:
            return
        self._celery_task_duration.observe(duration_seconds)

    def set_celery_worker_count(self, workers: float) -> None:
        if not self._prometheus_available:
            return
        self._celery_worker_gauge.set(workers)

    # Cache metrics
    def record_cache_hit(self) -> None:
        if not self._prometheus_available:
            return
        self._cache_hits.inc()

    def record_cache_miss(self) -> None:
        if not self._prometheus_available:
            return
        self._cache_misses.inc()

    # Unity metrics helpers
    def unity_connection_opened(self) -> None:
        if not self._prometheus_available:
            return
        self._unity_connections_total.inc()
        self._unity_connections_active.inc()

    def unity_connection_closed(self) -> None:
        if not self._prometheus_available:
            return
        try:
            self._unity_connections_active.dec()
        except ValueError:
            self._unity_connections_active.set(0)

    def unity_message_outbound(self, count: int = 1) -> None:
        if not self._prometheus_available or count <= 0:
            return
        self._unity_messages_out_total.inc(count)

    def unity_message_inbound(self, count: int = 1) -> None:
        if not self._prometheus_available or count <= 0:
            return
        self._unity_messages_in_total.inc(count)

    def unity_reconnect_attempt(self) -> None:
        if not self._prometheus_available:
            return
        self._unity_reconnect_attempts_total.inc()

    def unity_message_invalid(self) -> None:
        if not self._prometheus_available:
            return
        self._unity_messages_invalid_total.inc()


metrics_service = MetricsService()


def get_registry(reload: bool = False) -> KPIRegistry:
    """Return shared KPI registry instance."""

    if reload:
        metrics_service.get_registry().refresh()
    return metrics_service.get_registry()


__all__ = [
    "KPI",
    "KPIRegistry",
    "MetricsService",
    "metrics_service",
    "get_registry",
]
