"""Unity data bridge for Polylog6.

Provides a lightweight WebSocket server that streams simulation updates to a
Unity client.  The server is optional – it starts only when explicitly enabled
and degrades gracefully when dependencies are missing.
"""
from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import threading
from dataclasses import asdict, dataclass
from typing import Any, Callable, Dict, Optional
from uuid import uuid4

from jsonschema import ValidationError, validate

from polylog6.metrics.service import MetricsService

try:  # Structured logging optional
    import structlog
except Exception:  # pragma: no cover
    structlog = None

try:  # Optional dependency for WebSocket support.
    import websockets  # type: ignore
except Exception:  # pragma: no cover - dependency is optional
    websockets = None


@dataclass
class FrameUpdate:
    """Payload describing a single frame of simulation data."""

    frame: int
    fps: float
    stability_score: float
    kpi_snapshot: Dict[str, Any]

    def to_payload(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["type"] = "frame_update"
        return payload


@dataclass
class InteractionEvent:
    """Payload describing a user interaction within the UI."""

    event: str
    timestamp: float
    context: Dict[str, Any]

    def to_payload(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["type"] = "interaction_event"
        return payload


MESSAGE_SCHEMA = {
    "type": "object",
    "properties": {
        "type": {"type": "string"},
        "payload": {"type": "object"},
        "timestamp": {"type": "number"},
    },
    "required": ["type", "payload"],
}


class UnityBridge:
    """Manage a WebSocket feed for Unity visualisation clients."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8765,
        metrics_service: Optional[MetricsService] = None,
    ) -> None:
        if metrics_service is None:
            raise ValueError("metrics_service is required")

        self._host = host
        self._port = port
        self._logger = structlog.get_logger(__name__) if structlog else logging.getLogger(__name__)
        self._clients: set[websockets.WebSocketServerProtocol] = set()
        self._client_ids: Dict[websockets.WebSocketServerProtocol, str] = {}
        self._queue: Optional[asyncio.Queue[Dict[str, Any]]] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._server: Optional[websockets.server.Serve] = None  # type: ignore[attr-defined]
        self._thread: Optional[threading.Thread] = None
        self._command_handler: Optional[Callable[[Dict[str, Any]], None]] = None
        self._metrics = metrics_service
        self._metrics.start()

    # ------------------------------------------------------------------
    # Lifecycle management
    # ------------------------------------------------------------------
    def start(self) -> bool:
        if websockets is None:
            self._logger.warning("Unity bridge unavailable: websockets package not installed")
            return False
        if self._thread and self._thread.is_alive():
            return True

        self._queue = asyncio.Queue()
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        self._log("unity_bridge_start", host=self._host, port=self._port)
        return True

    def stop(self) -> None:
        if self._loop is None:
            return

        async def _shutdown() -> None:
            if self._server is not None:
                self._server.close()
                await self._server.wait_closed()
                self._server = None
            for client in set(self._clients):
                await client.close()
            self._clients.clear()

        asyncio.run_coroutine_threadsafe(_shutdown(), self._loop).result()
        self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread is not None:
            self._thread.join(timeout=2)
        self._loop = None
        self._queue = None
        self._thread = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def queue_update(self, update: FrameUpdate) -> None:
        if not self._loop or not self._queue:
            return
        try:
            payload = update.to_payload()
            asyncio.run_coroutine_threadsafe(self._queue.put(payload), self._loop)
        except RuntimeError:
            self._logger.debug("Unity bridge queue unavailable; dropping frame %s", update.frame)

    def queue_interaction_event(self, event: InteractionEvent) -> None:
        if not self._loop or not self._queue:
            return
        try:
            payload = event.to_payload()
            asyncio.run_coroutine_threadsafe(self._queue.put(payload), self._loop)
        except RuntimeError:
            self._logger.debug("Unity bridge queue unavailable; dropping event %s", event.event)

    def set_command_handler(self, handler: Callable[[Dict[str, Any]], None]) -> None:
        """Register callback for inbound commands from Unity clients."""

        self._command_handler = handler

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _run_loop(self) -> None:
        assert self._loop is not None
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._async_main())
        except Exception as exc:  # pragma: no cover - defensive
            self._logger.error("Unity bridge loop exited with error: %s", exc)
        finally:
            self._loop.close()

    async def _async_main(self) -> None:
        assert self._queue is not None
        self._server = await websockets.serve(self._handler, self._host, self._port)
        self._log("unity_bridge_listening", host=self._host, port=self._port)
        broadcaster = asyncio.create_task(self._broadcast_loop())
        try:
            await self._server.wait_closed()
        finally:
            broadcaster.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await broadcaster

    async def _broadcast_loop(self) -> None:
        assert self._queue is not None
        while True:
            payload_dict = await self._queue.get()
            payload = json.dumps(payload_dict)
            for client in list(self._clients):
                try:
                    await client.send(payload)
                    self._record_message_outbound()
                except Exception as exc:
                    self._log("unity_client_send_failed", error=str(exc), client=str(client.remote_address))
                    await client.close()
                    self._clients.discard(client)
                    self._record_connection_closed()

    async def _handler(self, websocket: websockets.WebSocketServerProtocol) -> None:
        self._clients.add(websocket)
        correlation_id = uuid4().hex
        self._client_ids[websocket] = correlation_id
        self._log(
            "unity_client_connected",
            client=str(websocket.remote_address),
            correlation_id=correlation_id,
        )
        self._record_connection_opened()
        try:
            async for message in websocket:
                self._record_message_inbound()
                self._log(
                    "unity_message_received",
                    message=message[:256],
                    correlation_id=correlation_id,
                )
                if self._command_handler is None:
                    continue
                try:
                    parsed = json.loads(message)
                    if not self._validate_message(parsed):
                        continue
                    if isinstance(parsed, dict):
                        self._command_handler(parsed)
                except json.JSONDecodeError:
                    self._log(
                        "unity_message_invalid_json",
                        message=message[:256],
                        correlation_id=correlation_id,
                    )
        finally:
            self._clients.discard(websocket)
            self._client_ids.pop(websocket, None)
            self._log(
                "unity_client_disconnected",
                client=str(websocket.remote_address),
                correlation_id=correlation_id,
            )
            self._record_connection_closed()

    # ------------------------------------------------------------------
    # Metrics helpers
    # ------------------------------------------------------------------
    def _record_connection_opened(self) -> None:
        if self._metrics is None:
            return
        try:
            self._metrics.unity_connection_opened()
        except Exception:  # pragma: no cover - metrics failures should not crash bridge
            self._log("unity_metrics_error", event="connection_opened", error="increment_failed")

    def _record_connection_closed(self) -> None:
        if self._metrics is None:
            return
        try:
            self._metrics.unity_connection_closed()
        except Exception:  # pragma: no cover
            self._log("unity_metrics_error", event="connection_closed", error="decrement_failed")

    def _record_message_outbound(self) -> None:
        if self._metrics is None:
            return
        try:
            self._metrics.unity_message_outbound()
        except Exception:  # pragma: no cover
            self._log("unity_metrics_error", event="message_outbound", error="increment_failed")

    def _record_message_inbound(self) -> None:
        if self._metrics is None:
            return
        try:
            self._metrics.unity_message_inbound()
        except Exception:  # pragma: no cover
            self._log("unity_metrics_error", event="message_inbound", error="increment_failed")

    def _validate_message(self, message: Dict[str, Any]) -> bool:
        try:
            validate(instance=message, schema=MESSAGE_SCHEMA)
            return True
        except ValidationError as exc:
            if self._metrics is not None:
                self._metrics.unity_message_invalid()
            self._log(
                "unity_message_schema_error",
                error=str(exc),
                message=str(message)[:256],
            )
            return False

    def _log(self, event: str, **context: Any) -> None:
        if structlog:
            self._logger.info(event, **context)
        else:
            self._logger.info("%s | %s", event, context)


__all__ = ["UnityBridge", "FrameUpdate", "InteractionEvent"]
