"""Append-only metrics emission with file locking guarantees."""
from __future__ import annotations

import gzip
import json
import logging
import time
from pathlib import Path
from typing import Dict, Iterable, List

from .schema import CandidateEvent

logger = logging.getLogger(__name__)


class MetricsEmitter:
    """Emit and manage candidate events in an append-only JSONL stream."""

    def __init__(self, output_path: str = "storage/caches/tier_candidates.jsonl") -> None:
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.lock_path = self.output_path.with_suffix(".lock")

    def emit(self, candidate: Dict) -> None:
        """Append ``candidate`` to the JSONL event stream atomically."""
        serialized = json.dumps(candidate)

        with open(self.lock_path, "w", encoding="utf-8") as lock_file:
            import fcntl

            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            try:
                with open(self.output_path, "a", encoding="utf-8") as stream:
                    stream.write(serialized + "\n")
                    stream.flush()
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

        logger.debug("Emitted candidate event %s", candidate.get("event_id"))

    def read_events_last_24h(self, now: float | None = None) -> List[Dict]:
        """Return events from the last 24 hours."""
        now = now or time.time()
        cutoff = now - 24 * 3600
        events: List[Dict] = []

        with open(self.lock_path, "w", encoding="utf-8") as lock_file:
            import fcntl

            fcntl.flock(lock_file.fileno(), fcntl.LOCK_SH)
            try:
                if not self.output_path.exists():
                    return []

                with open(self.output_path, "r", encoding="utf-8") as stream:
                    for line in stream:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            event = json.loads(line)
                        except json.JSONDecodeError:
                            logger.warning("Skipping malformed event line: %s", line[:64])
                            continue

                        if float(event.get("timestamp", 0.0)) >= cutoff:
                            events.append(event)
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

        return events

    def rotate(self, retention_days: int = 7) -> None:
        """Archive events older than ``retention_days`` into a gzip file."""
        cutoff = time.time() - retention_days * 24 * 3600

        with open(self.lock_path, "w", encoding="utf-8") as lock_file:
            import fcntl

            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            try:
                if not self.output_path.exists():
                    return

                active: List[str] = []
                archive: List[str] = []

                with open(self.output_path, "r", encoding="utf-8") as stream:
                    for line in stream:
                        stripped = line.strip()
                        if not stripped:
                            continue
                        try:
                            event = json.loads(stripped)
                        except json.JSONDecodeError:
                            logger.warning("Skipping malformed event line: %s", stripped[:64])
                            continue

                        if float(event.get("timestamp", 0.0)) < cutoff:
                            archive.append(stripped)
                        else:
                            active.append(stripped)

                with open(self.output_path, "w", encoding="utf-8") as stream:
                    for record in active:
                        stream.write(record + "\n")

                if archive:
                    archive_path = self.output_path.with_suffix(".archive.jsonl.gz")
                    with gzip.open(archive_path, "at", encoding="utf-8") as archive_stream:
                        for record in archive:
                            archive_stream.write(record + "\n")

                logger.info(
                    "Metrics rotation complete: %d active, %d archived", len(active), len(archive)
                )
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

    def read_all(self) -> Iterable[CandidateEvent]:
        """Yield every stored candidate event as :class:`CandidateEvent`."""
        if not self.output_path.exists():
            return []

        with open(self.output_path, "r", encoding="utf-8") as stream:
            for line in stream:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield CandidateEvent.from_json(line)
                except Exception as exc:  # pragma: no cover - defensive
                    logger.warning("Failed to parse event line: %s", exc)
