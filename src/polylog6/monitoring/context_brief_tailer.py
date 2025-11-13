"""Utilities for tailing context-brief JSONL logs (INT-003).

The context brief is a newline-delimited JSON feed emitted by the async inbox.
Each record may include a ``registry_digest`` field used to trigger library
refreshes. The :class:`ContextBriefTailer` provides a lightweight abstraction
that keeps track of file offsets, tolerates partial writes, and exposes helper
methods for iterative consumption.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Iterator, List, Optional, Union

FileSystemEventHandler = None  # type: ignore
Observer = None  # type: ignore

try:  # pragma: no cover - optional dependency
    from watchdog.events import FileSystemEventHandler as _WatchdogEvents  # type: ignore
    from watchdog.observers import Observer as _WatchdogObserver  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    _WatchdogEvents = None  # type: ignore
    _WatchdogObserver = None  # type: ignore

if _WatchdogObserver is not None and _WatchdogEvents is not None:
    Observer = _WatchdogObserver  # type: ignore[assignment]
    FileSystemEventHandler = _WatchdogEvents  # type: ignore[assignment]

__all__ = [
    "ContextBriefEntry",
    "ContextBriefTailer",
    "ContextBriefWatcher",
]


@dataclass(slots=True)
class ContextBriefEntry:
    """Represents a single decoded context brief line."""

    payload: Dict[str, object]
    registry_digest: Optional[str] = None


class ContextBriefTailer:
    """Incrementally tail ``context-brief.jsonl`` for registry digests."""

    def __init__(
        self,
        log_path: Union[str, Path],
        *,
        poll_interval: float = 0.5,
        encoding: str = "utf-8",
    ) -> None:
        self.log_path = Path(log_path)
        self._poll_interval = poll_interval
        self._encoding = encoding
        self._offset = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def read_new_entries(self) -> List[ContextBriefEntry]:
        """Return entries appended since the previous read.

        The tailer maintains an internal byte offset so callers can invoke this
        method in a polling loop without re-reading historical data. If the
        underlying file is truncated (e.g., log rotation), the offset is reset
        automatically.
        """

        if not self.log_path.exists():
            self._offset = 0
            return []

        entries: List[ContextBriefEntry] = []
        current_size = self.log_path.stat().st_size
        if current_size < self._offset:
            # File truncated or rotated – restart from beginning
            self._offset = 0

        with self.log_path.open("r", encoding=self._encoding) as handle:
            handle.seek(self._offset)
            for raw_line in handle:
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    payload: Dict[str, object] = json.loads(line)
                except json.JSONDecodeError:
                    # Skip malformed/partial lines; caller can retry on next poll
                    continue
                entries.append(
                    ContextBriefEntry(
                        payload=payload,
                        registry_digest=str(payload.get("registry_digest"))
                        if payload.get("registry_digest") is not None
                        else None,
                    )
                )
            self._offset = handle.tell()
        return entries

    def follow(self) -> Iterator[ContextBriefEntry]:
        """Continuously yield new entries using ``poll_interval`` delays."""

        while True:
            for entry in self.read_new_entries():
                yield entry
            time.sleep(self._poll_interval)

    def reset(self) -> None:
        """Reset the internal file offset. Useful for test harnesses."""

        self._offset = 0


if FileSystemEventHandler is not None:

    class _WatchdogHandler(FileSystemEventHandler):  # type: ignore[misc]
        """Internal watchdog event handler that delegates to the tailer."""

        def __init__(self, tailer: ContextBriefTailer, callback: Callable[[ContextBriefEntry], None]) -> None:
            self._tailer = tailer
            self._callback = callback
            self._target = tailer.log_path.resolve()

        def on_modified(self, event) -> None:  # pragma: no cover - file system integration
            if Path(event.src_path).resolve() == self._target:
                for entry in self._tailer.read_new_entries():
                    self._callback(entry)

        def on_created(self, event) -> None:  # pragma: no cover - file system integration
            if Path(event.src_path).resolve() == self._target:
                self._tailer.reset()
                for entry in self._tailer.read_new_entries():
                    self._callback(entry)

        def on_moved(self, event) -> None:  # pragma: no cover - file system integration
            # When logs rotate, the destination becomes the new file we watch.
            if Path(event.dest_path).resolve() == self._target:
                self._tailer.reset()

else:  # pragma: no cover - defensive fallback when watchdog missing

    class _WatchdogHandler:  # type: ignore[too-many-ancestors]
        def __init__(self, *args, **kwargs) -> None:
            raise RuntimeError(
                "watchdog is not installed. Install it via `pip install watchdog` to use ContextBriefWatcher."
            )


class ContextBriefWatcher:
    """Watchdog-backed watcher that triggers callbacks on new context brief entries."""

    def __init__(self, tailer: ContextBriefTailer) -> None:
        if Observer is None or FileSystemEventHandler is None:  # pragma: no cover - defensive
            raise RuntimeError(
                "watchdog is not installed. Install it via `pip install watchdog` to use ContextBriefWatcher."
            )
        self._tailer = tailer
        self._observer: Observer = Observer()  # type: ignore[assignment]
        self._handler: Optional[_WatchdogHandler] = None

    def start(self, callback: Callable[[ContextBriefEntry], None]) -> None:
        """Begin watching for log updates and invoke *callback* with new entries."""

        if self._handler is not None:
            raise RuntimeError("ContextBriefWatcher already started")

        handler = _WatchdogHandler(self._tailer, callback)
        self._handler = handler
        watch_dir = self._tailer.log_path.parent
        watch_dir.mkdir(parents=True, exist_ok=True)
        self._observer.schedule(handler, str(watch_dir), recursive=False)
        self._observer.start()

        # Emit any entries that already exist beyond the current pointer.
        for entry in self._tailer.read_new_entries():
            callback(entry)

    def stop(self) -> None:
        """Stop watching the log file."""

        if self._handler is None:
            return
        self._observer.stop()
        self._observer.join()
        self._handler = None
