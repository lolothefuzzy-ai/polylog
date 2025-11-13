"""Monitoring service bootstrap for Track B integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable, Optional

from .config import monitoring_enabled, monitoring_poll_interval, resolve_context_brief_path
from .context_brief_tailer import ContextBriefTailer, ContextBriefWatcher
from .dispatcher import DispatcherErrorHandler, watch_context_brief
from .library_refresh import LibraryRefreshWorker
from .loop import MonitoringLoop, MonitoringLoopConfig
from .telemetry_bridge import DetectionTelemetryBridge
from .alerts import AlertRecord, ListAlertSink, fanout_alert_callbacks, fanout_refresh_callbacks


@dataclass(slots=True)
class MonitoringRuntimeConfig:
    """Runtime dependency bundle for monitoring loop wiring."""

    registry_state_provider: callable
    refresh_callbacks: Iterable[callable] | None = None
    alert_callbacks: Iterable[callable] | None = None
    enable_watcher: bool = False
    auto_start_watcher: bool = False
    dispatcher_error_handler: Optional[DispatcherErrorHandler] = None
    max_entries: Optional[int] = None


def create_monitoring_loop(
    config: MonitoringRuntimeConfig,
) -> tuple[
    MonitoringLoop | None,
    DetectionTelemetryBridge | None,
    ContextBriefWatcher | None,
]:
    """Instantiate monitoring loop with configured tailer/refresh worker.

    Returns ``(None, None, None)`` when the monitoring feature flag is disabled.
    """

    if not monitoring_enabled():
        return None, None, None

    context_path = resolve_context_brief_path(ensure_exists=True)
    tailer = ContextBriefTailer(context_path, poll_interval=monitoring_poll_interval())

    refresh_worker = LibraryRefreshWorker(
        context_path,
        registry_state_provider=config.registry_state_provider,
        on_refresh=fanout_refresh_callbacks(tuple(config.refresh_callbacks or [])),
        on_alert=fanout_alert_callbacks(tuple(config.alert_callbacks or [])),
    )

    telemetry_bridge = DetectionTelemetryBridge()

    loop = MonitoringLoop(
        tailer,
        refresh_worker,
        telemetry_bridge=telemetry_bridge,
        enabled=monitoring_enabled,
        config=MonitoringLoopConfig(poll_interval=monitoring_poll_interval()),
    )

    watcher: ContextBriefWatcher | None = None
    if config.enable_watcher:
        if config.auto_start_watcher:
            watcher = watch_context_brief(
                tailer,
                refresh_worker,
                telemetry_bridge=telemetry_bridge,
                error_handler=config.dispatcher_error_handler,
                max_entries=config.max_entries,
            )
        else:
            watcher = ContextBriefWatcher(tailer)

    return loop, telemetry_bridge, watcher


class MonitoringService:
    """Lightweight façade for routing detection telemetry into monitoring."""

    LATENCY_ALERT_THRESHOLD_MS = 30_000.0
    MONITORING_LATENCY_THRESHOLD_MS = 100.0
    ZERO_REGION_THRESHOLD = 0

    def __init__(
        self,
        *,
        bridge: DetectionTelemetryBridge | None = None,
        alert_sink: ListAlertSink | None = None,
        telemetry_consumer: Optional[Callable[[dict[str, Any]], None]] = None,
    ) -> None:
        self._bridge = bridge or DetectionTelemetryBridge()
        self._alert_sink = alert_sink or ListAlertSink()
        self._telemetry_consumer = telemetry_consumer

    @property
    def alert_sink(self) -> ListAlertSink:
        return self._alert_sink

    def ingest_telemetry(self, payload: dict[str, Any]) -> None:
        snapshot = self._bridge.emit(payload)
        duration_ms = float(
            payload.get("duration_ms")
            or payload.get("detection_duration_ms")
            or 0.0
        )
        region_count = int(payload.get("region_count", 0))

        if duration_ms > self.LATENCY_ALERT_THRESHOLD_MS:
            self._emit_alert(
                code="slow_detection",
                severity="ERROR",
                message=(
                    f"Detection latency {duration_ms:.1f} ms exceeds "
                    f"{self.LATENCY_ALERT_THRESHOLD_MS:.1f} ms threshold"
                ),
                metadata={"duration_ms": duration_ms, "request_id": snapshot.request_id},
            )

        if region_count <= self.ZERO_REGION_THRESHOLD:
            self._emit_alert(
                code="zero_regions",
                severity="ERROR",
                message="Detection produced zero regions",
                metadata={"request_id": snapshot.request_id},
            )

        if self._telemetry_consumer is not None:
            self._telemetry_consumer(dict(payload))

    async def ingest_telemetry_async(self, payload: dict[str, Any]) -> None:
        self.ingest_telemetry(payload)

    def _emit_alert(
        self,
        *,
        code: str,
        severity: str,
        message: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        record = AlertRecord(
            severity=severity,
            message=message,
            metadata={"code": code, **(metadata or {})},
        )
        self._alert_sink.emit(record)


class _NullMonitoringService:
    def ingest_telemetry(self, payload: dict[str, Any]) -> None:  # pragma: no cover - no-op
        return

    async def ingest_telemetry_async(self, payload: dict[str, Any]) -> None:  # pragma: no cover - no-op
        return


_MONITORING_SERVICE: MonitoringService | _NullMonitoringService | None = None


def monitoring_active() -> bool:
    return monitoring_enabled()


def get_monitoring_service() -> MonitoringService | _NullMonitoringService:
    global _MONITORING_SERVICE
    if _MONITORING_SERVICE is None:
        if monitoring_active():
            _MONITORING_SERVICE = MonitoringService()
        else:
            _MONITORING_SERVICE = _NullMonitoringService()
    return _MONITORING_SERVICE


def set_monitoring_service_for_testing(service: MonitoringService | _NullMonitoringService) -> None:
    global _MONITORING_SERVICE
    _MONITORING_SERVICE = service


def reset_monitoring_service() -> None:
    global _MONITORING_SERVICE
    _MONITORING_SERVICE = None


__all__ = [
    "MonitoringRuntimeConfig",
    "MonitoringLoop",
    "MonitoringLoopConfig",
    "MonitoringService",
    "monitoring_active",
    "get_monitoring_service",
    "set_monitoring_service_for_testing",
    "reset_monitoring_service",
]
