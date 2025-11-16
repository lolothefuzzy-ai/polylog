"""Coordination loop runner for monitoring dispatcher (INT-003/INT-004)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional
import time

from .context_brief_tailer import ContextBriefTailer
from .dispatcher import dispatch_once, run_dispatch_loop
from .library_refresh import LibraryRefreshWorker
from .telemetry_bridge import DetectionTelemetryBridge
from .telemetry import MonitoringTelemetry


@dataclass(slots=True)
class MonitoringLoopConfig:
    """Configuration for the monitoring dispatcher loop."""

    poll_interval: Optional[float] = None
    max_entries: Optional[int] = None


class MonitoringLoop:
    """Feature-flag-aware wrapper driving the dispatcher loop."""

    def __init__(
        self,
        tailer: ContextBriefTailer,
        refresh_worker: LibraryRefreshWorker,
        *,
        telemetry_bridge: DetectionTelemetryBridge | None = None,
        enabled: Callable[[], bool] | None = None,
        config: MonitoringLoopConfig | None = None,
    ) -> None:
        self._tailer = tailer
        self._refresh_worker = refresh_worker
        self._telemetry_bridge = telemetry_bridge
        self._enabled = enabled or (lambda: True)
        self._config = config or MonitoringLoopConfig()
        self._telemetry = MonitoringTelemetry()  

    def run_once(self) -> None:
        """Execute a single dispatcher iteration regardless of feature flag."""
        start_time = time.perf_counter()
        
        dispatch_once(
            self._tailer,
            self._refresh_worker,
            telemetry_bridge=self._telemetry_bridge,
            max_entries=self._config.max_entries,
        )
        
        duration = time.perf_counter() - start_time
        self._telemetry.record_dispatch(duration)
        self._telemetry.record_iteration()

    def run(self, *, max_iterations: Optional[int] = None) -> None:
        """Run the dispatcher loop until the flag disables it or limit reached."""
        iteration = 0
        self._telemetry.record_loop_start()
        while self._enabled() and (max_iterations is None or iteration < max_iterations):
            self.run_once()
            iteration += 1
            
            # Sleep between iterations
            if self._config.poll_interval:
                time.sleep(self._config.poll_interval)
        
        self._telemetry.record_loop_completion(iteration)


__all__ = ["MonitoringLoop", "MonitoringLoopConfig"]
