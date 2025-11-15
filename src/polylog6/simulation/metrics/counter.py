"""Frequency counter persistence with rotation guarantees."""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)


class FrequencyCounterPersistence:
    """Manage an in-memory frequency map with periodic disk rotations."""

    ROTATION_INTERVAL_SEC: int = 300

    def __init__(self, checkpoint_path: str = "storage/cache_state.json") -> None:
        self.checkpoint_path = Path(checkpoint_path)
        self.checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        self.map: Dict[str, Dict[str, float | int]] = {}
        self.last_rotation = time.time()
        self.rotation_count = 0

    def load(self) -> None:
        """Load frequency counters from disk if present."""
        if not self.checkpoint_path.exists():
            self.map = {}
            return

        try:
            raw = self.checkpoint_path.read_text(encoding="utf-8")
            self.map = json.loads(raw)
            logger.info("Loaded %d frequency counters from %s", len(self.map), self.checkpoint_path)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Failed to load frequency counters: %s", exc)
            self.map = {}

    def increment(self, canonical_sig: str) -> None:
        """Increment the counter for ``canonical_sig`` and update timestamps."""
        now = time.time()
        record = self.map.setdefault(
            canonical_sig,
            {"count": 0, "first_seen": now, "last_seen": now},
        )

        record["count"] = int(record.get("count", 0)) + 1
        record["last_seen"] = now

    def maybe_rotate(self) -> bool:
        """Rotate to disk if the rotation interval has elapsed."""
        elapsed = time.time() - self.last_rotation
        if elapsed < self.ROTATION_INTERVAL_SEC:
            return False

        self.rotate()
        return True

    def rotate(self) -> None:
        """Persist the current map to disk using an atomic replace."""
        temp_path = self.checkpoint_path.with_suffix(".tmp")

        try:
            temp_path.write_text(json.dumps(self.map, indent=2), encoding="utf-8")
            temp_path.replace(self.checkpoint_path)
            self.last_rotation = time.time()
            self.rotation_count += 1
            logger.debug("Rotated frequency counters to %s", self.checkpoint_path)
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Failed to rotate frequency counters: %s", exc)
            if temp_path.exists():
                temp_path.unlink(missing_ok=True)
            raise
