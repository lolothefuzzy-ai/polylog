"""IPC bridge notes for Track B coordination."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(slots=True)
class IPCConfig:
    """Configuration for Tauri ↔ FastAPI communication."""

    base_url: str = "http://127.0.0.1:8000"
    timeout_seconds: float = 30.0
    enable_batching: bool = False


class DetectionIPCClient(Protocol):
    """Protocol for outbound IPC calls from Tauri or other frontends."""

    def invoke(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:  # pragma: no cover - stub
        ...


def build_default_ipc_config() -> IPCConfig:
    """Return default IPC configuration.

    TODO(INT-014): Revisit once the FastAPI route structure is finalized and we
    benchmark startup timing for the embedded Python runtime vs. external server.
    """

    return IPCConfig()


def describe_ipc_contract() -> dict[str, Any]:
    """Human-readable description of expected endpoints.

    This helper will feed documentation for Track B when wiring the UI. Adjust
    as FastAPI routes are implemented.
    """

    return {
        "analyze_sync": {
            "method": "POST",
            "path": "/detection/analyze",
            "payload": {"image_path": "str", "request_id": "Optional[str]"},
            "response": "Detection plan payload (JSON)",
        },
        "analyze_async": {
            "method": "POST",
            "path": "/detection/analyze_async",
            "payload": {"image_path": "str", "callback": "url"},
            "response": "Accepted / 202",
        },
        "telemetry_emit": {
            "method": "POST",
            "path": "/detection/telemetry",
            "payload": {
                "request_id": "Optional[str]",
                "region_count": "int",
                "candidate_count": "int",
                "coverage_percent": "float",
                "schema_version": "str (current: 0.1)",
            },
            "response": "Accepted / 202",
        },
    }
