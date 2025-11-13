"""Lightweight alert primitives for monitoring utilities (INT-006).

Provides in-memory collectors and logging sinks so reconciliation workflows can
surface actionable alerts without pulling in a full notification stack.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Protocol, Sequence, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - import for typing only
    from .registry_reconciliation import RegistryDiff
    from .library_refresh import CheckpointRecord


@dataclass(slots=True)
class AlertRecord:
    """Represents a single alert emitted by a monitoring harness."""

    severity: str
    message: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class AlertSink(Protocol):
    """Interface implemented by alert collectors."""

    def emit(self, alert: AlertRecord) -> None:
        ...


class ListAlertSink:
    """Collect alerts in-memory for later inspection or testing."""

    def __init__(self) -> None:
        self._alerts: List[AlertRecord] = []

    def emit(self, alert: AlertRecord) -> None:  # pragma: no cover - trivial
        self._alerts.append(alert)

    def alerts(self) -> List[AlertRecord]:
        return list(self._alerts)


class LoggingAlertSink:
    """Forward alerts to the standard library logger."""

    def __init__(self, logger) -> None:  # type: ignore[no-untyped-def]
        self._logger = logger

    def emit(self, alert: AlertRecord) -> None:  # pragma: no cover - thin wrapper
        log_fn = getattr(self._logger, alert.severity.lower(), self._logger.warning)
        log_fn("%s | metadata=%s", alert.message, alert.metadata)


def render_registry_diff_alerts(diff: "RegistryDiff") -> Iterable[AlertRecord]:
    """Generate alert records summarising registry diffs."""

    if diff.missing_symbols:
        missing_details = ", ".join(sorted(diff.missing_symbols))
        yield AlertRecord(
            severity="ERROR",
            message=(
                "Registry parity check failed: baseline symbols missing in "
                f"candidate '{diff.candidate_label}'."
            ),
            metadata={"missing_symbols": missing_details},
        )

    if diff.unexpected_symbols:
        unexpected_details = ", ".join(sorted(diff.unexpected_symbols))
        yield AlertRecord(
            severity="ERROR",
            message=(
                "Registry parity check failed: unexpected symbols present in "
                f"candidate '{diff.candidate_label}'."
            ),
            metadata={"unexpected_symbols": unexpected_details},
        )

    if diff.mismatched_symbols:
        mismatch_details = ", ".join(sorted(diff.mismatched_symbols))
        yield AlertRecord(
            severity="WARNING",
            message=(
                "Registry parity check found mismatched symbol assignments in "
                f"candidate '{diff.candidate_label}'."
            ),
            metadata={"mismatched_symbols": mismatch_details},
        )


__all__ = [
    "AlertRecord",
    "AlertSink",
    "ListAlertSink",
    "LoggingAlertSink",
    "render_registry_diff_alerts",
    "fanout_alert_callbacks",
    "fanout_refresh_callbacks",
]


def fanout_alert_callbacks(
    callbacks: Sequence[Callable[[str, "CheckpointRecord"], None]] | None,
) -> Callable[[str, "CheckpointRecord"], None] | None:
    """Return a fan-out handler for alert callbacks.

    ``LibraryRefreshWorker`` expects ``on_alert`` callbacks that accept the alert
    code and the checkpoint record. This helper allows us to supply a sequence of
    callbacks while keeping the worker API unchanged.
    """

    if not callbacks:
        return None

    callbacks = tuple(callbacks)

    def _dispatch(code: str, record: "CheckpointRecord") -> None:
        for callback in callbacks:
            callback(code, record)

    return _dispatch


def fanout_refresh_callbacks(
    callbacks: Sequence[Callable[["CheckpointRecord"], None]] | None,
) -> Callable[["CheckpointRecord"], None] | None:
    """Return a fan-out handler for refresh callbacks."""

    if not callbacks:
        return None

    callbacks = tuple(callbacks)

    def _dispatch(record: "CheckpointRecord") -> None:
        for callback in callbacks:
            callback(record)

    return _dispatch
