"""Context brief dispatcher utilities (INT-003/INT-004).

The dispatcher ties :class:`ContextBriefTailer` output to
:class:`LibraryRefreshWorker` parity checks and optionally feeds detection
telemetry into the monitoring bridge.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, List, Sequence

from .context_brief_tailer import ContextBriefEntry, ContextBriefTailer, ContextBriefWatcher
from .library_refresh import LibraryRefreshWorker, record_from_payload
from .telemetry_bridge import DetectionTelemetryBridge

DispatcherErrorHandler = Callable[[ContextBriefEntry, Exception], None]


@dataclass(slots=True)
class DispatchResult:
    """Aggregator for a single dispatcher pass."""

    processed: int
    refresh_results: list
    telemetry_snapshots: list


def dispatch_entries(
    entries: Sequence[ContextBriefEntry],
    refresh_worker: LibraryRefreshWorker,
    *,
    telemetry_bridge: DetectionTelemetryBridge | None = None,
    error_handler: DispatcherErrorHandler | None = None,
    max_entries: int | None = None,
) -> DispatchResult:
    """Process a pre-supplied batch of context-brief entries.

    Useful for watcher-driven integrations where the filesystem handler already
    collected the new entries and we want to reuse dispatcher logic.
    """

    if max_entries is not None:
        entries = entries[:max_entries]

    refresh_results = []
    telemetry_snapshots = []

    for entry in entries:
        # Feed detection telemetry (if present) into monitoring bridge.
        if telemetry_bridge is not None:
            telemetry_payload = entry.payload.get("detection_telemetry")
            if isinstance(telemetry_payload, dict):
                telemetry_snapshots.append(telemetry_bridge.emit(telemetry_payload))

        payload = entry.payload.get("checkpoint_record")
        if payload is None:
            payload = entry.payload

        try:
            record = record_from_payload(payload)
        except Exception as exc:  # pragma: no cover - defensive guard
            if error_handler is not None:
                error_handler(entry, exc)
            continue

        result = refresh_worker.process_record(record)
        if result is not None:
            refresh_results.append(result)

    return DispatchResult(
        processed=len(entries),
        refresh_results=refresh_results,
        telemetry_snapshots=telemetry_snapshots,
    )


def dispatch_once(
    tailer: ContextBriefTailer,
    refresh_worker: LibraryRefreshWorker,
    *,
    telemetry_bridge: DetectionTelemetryBridge | None = None,
    error_handler: DispatcherErrorHandler | None = None,
    max_entries: int | None = None,
) -> DispatchResult:
    """Process newly appended context-brief entries once."""

    entries = tailer.read_new_entries()
    return dispatch_entries(
        entries,
        refresh_worker,
        telemetry_bridge=telemetry_bridge,
        error_handler=error_handler,
        max_entries=max_entries,
    )


def run_dispatch_loop(
    tailer: ContextBriefTailer,
    refresh_worker: LibraryRefreshWorker,
    *,
    telemetry_bridge: DetectionTelemetryBridge | None = None,
    error_handler: DispatcherErrorHandler | None = None,
    enabled: Callable[[], bool] | None = None,
    poll_interval: float | None = None,
    max_entries: int | None = None,
    max_iterations: int | None = None,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> List[DispatchResult]:
    """Continuously dispatch context-brief entries while the feature flag allows.

    Args:
        enabled: Callable returning ``True`` to continue looping. Defaults to
            always-on when omitted. Useful for feature-flag-based gating.
        poll_interval: Delay between iterations; falls back to the tailer's
            configured poll interval when omitted.
        max_iterations: Optional cap to facilitate deterministic testing.
        sleep_fn: Dependency-injected sleep function (e.g., ``lambda _: None`` for
            unit tests).
    """

    if enabled is None:
        enabled = lambda: True  # noqa: E731 - simple default lambda

    results: List[DispatchResult] = []
    iterations = 0

    while enabled():
        results.append(
            dispatch_once(
                tailer,
                refresh_worker,
                telemetry_bridge=telemetry_bridge,
                error_handler=error_handler,
                max_entries=max_entries,
            )
        )

        iterations += 1
        if max_iterations is not None and iterations >= max_iterations:
            break

        sleep_duration = (
            poll_interval
            if poll_interval is not None
            else getattr(tailer, "_poll_interval", 0.5)
        )
        if sleep_duration > 0:
            sleep_fn(sleep_duration)

    return results


def watch_context_brief(
    tailer: ContextBriefTailer,
    refresh_worker: LibraryRefreshWorker,
    *,
    telemetry_bridge: DetectionTelemetryBridge | None = None,
    error_handler: DispatcherErrorHandler | None = None,
    max_entries: int | None = None,
) -> ContextBriefWatcher:
    """Convenience helper that wires :class:`ContextBriefWatcher` to the dispatcher."""

    watcher = ContextBriefWatcher(tailer)

    def _callback(entry: ContextBriefEntry) -> None:
        dispatch_entries(
            [entry],
            refresh_worker,
            telemetry_bridge=telemetry_bridge,
            error_handler=error_handler,
            max_entries=max_entries,
        )

    watcher.start(_callback)
    return watcher


__all__ = ["DispatchResult", "dispatch_once", "run_dispatch_loop", "watch_context_brief"]
