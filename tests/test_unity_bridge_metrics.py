"""Tests for UnityBridge metrics hooks."""
from __future__ import annotations

from src.common.unity_bridge import UnityBridge


class DummyMetrics:
    def __init__(self) -> None:
        self.connection_opened = 0
        self.connection_closed = 0
        self.msg_outbound = 0
        self.msg_inbound = 0

    def unity_connection_opened(self) -> None:  # pragma: no cover - simple counter
        self.connection_opened += 1

    def unity_connection_closed(self) -> None:  # pragma: no cover - simple counter
        self.connection_closed += 1

    def unity_message_outbound(self, count: int = 1) -> None:  # pragma: no cover
        self.msg_outbound += count

    def unity_message_inbound(self, count: int = 1) -> None:  # pragma: no cover
        self.msg_inbound += count


def test_unity_bridge_metrics_helpers_increment_counts() -> None:
    metrics = DummyMetrics()
    bridge = UnityBridge(metrics=metrics)

    bridge._record_connection_opened()  # type: ignore[attr-defined]
    bridge._record_connection_closed()  # type: ignore[attr-defined]
    bridge._record_message_outbound()  # type: ignore[attr-defined]
    bridge._record_message_inbound()  # type: ignore[attr-defined]

    assert metrics.connection_opened == 1
    assert metrics.connection_closed == 1
    assert metrics.msg_outbound == 1
    assert metrics.msg_inbound == 1
