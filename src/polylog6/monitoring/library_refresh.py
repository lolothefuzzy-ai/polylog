"""Monitoring loop utilities for INT-003/004."""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Iterator, List, Mapping, Optional, Union

from polylog6.storage.manager import PolyformStorageManager

RegistryStateProvider = Callable[[], Dict[str, object]]
RefreshCallback = Callable[["CheckpointRecord"], None]
AlertCallback = Callable[[str, "CheckpointRecord"], None]


@dataclass(slots=True)
class CheckpointRecord:
    """Snapshot metadata emitted by :class:`PolyformEngine`."""

    label: str
    path: Path
    polygons: int
    chunk_count: int
    module_refs: int
    registry_digest: str
    timestamp: float


@dataclass(slots=True)
class MonitoringResult:
    """Outcome of processing a single checkpoint record."""

    record: CheckpointRecord
    registry_match: bool
    refreshed: bool


def compute_registry_digest(state: Dict[str, object]) -> str:
    """Compute a registry digest compatible with :class:`PolyformEngine`."""

    serialized = json.dumps(state, sort_keys=True).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


class LibraryRefreshWorker:
    """Tail the async inbox and coordinate library refreshes."""

    def __init__(
        self,
        context_log_path: Union[str, Path],
        *,
        storage_manager: Optional[PolyformStorageManager] = None,
        registry_state_provider: Optional[RegistryStateProvider] = None,
        on_refresh: Optional[RefreshCallback] = None,
        on_alert: Optional[AlertCallback] = None,
    ) -> None:
        self.context_log_path = Path(context_log_path)
        self._offset = 0
        self._on_refresh = on_refresh
        self._on_alert = on_alert

        if registry_state_provider is not None:
            self._registry_state_provider = registry_state_provider
        elif storage_manager is not None:
            self._registry_state_provider = (
                lambda: storage_manager.encoder.registry.export_state()
            )
        else:
            raise ValueError(
                "registry_state_provider or storage_manager must be provided"
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def process_new_records(self) -> List[MonitoringResult]:
        """Parse newly appended checkpoint summaries and check registry parity."""

        results: List[MonitoringResult] = []

        for record in self._load_new_records():
            result = self.process_record(record)
            if result is not None:
                results.append(result)

        return results

    def process_record(self, record: CheckpointRecord) -> Optional[MonitoringResult]:
        """Evaluate a single checkpoint record."""

        try:
            registry_state = self._registry_state_provider()
            current_digest = compute_registry_digest(registry_state)
        except Exception as exc:  # pragma: no cover - defensive guard
            if self._on_alert is not None:
                self._on_alert(f"registry_provider_error:{exc}", record)
            return None

        registry_match = current_digest == record.registry_digest
        refreshed = False

        if not registry_match and self._on_refresh is not None:
            self._on_refresh(record)
            refreshed = True

        if not registry_match and self._on_alert is not None:
            self._on_alert("registry_mismatch", record)

        return MonitoringResult(
            record=record,
            registry_match=registry_match,
            refreshed=refreshed,
        )

    def watch(self, interval_seconds: float = 1.0) -> Iterator[MonitoringResult]:
        """Continuously poll the context log and yield monitoring results."""

        while True:
            results = self.process_new_records()
            for result in results:
                yield result
            time.sleep(interval_seconds)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _load_new_records(self) -> List[CheckpointRecord]:
        if not self.context_log_path.exists():
            return []

        records: List[CheckpointRecord] = []
        with self.context_log_path.open("r", encoding="utf-8") as handle:
            handle.seek(self._offset)
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                records.append(_record_from_dict(data))
            self._offset = handle.tell()
        return records


def _record_from_dict(payload: Dict[str, object]) -> CheckpointRecord:
    return CheckpointRecord(
        label=str(payload["label"]),
        path=Path(str(payload["path"])),
        polygons=int(payload["polygons"]),
        chunk_count=int(payload["chunk_count"]),
        module_refs=int(payload["module_refs"]),
        registry_digest=str(payload["registry_digest"]),
        timestamp=float(payload["timestamp"]),
    )


def record_from_payload(payload: Mapping[str, object]) -> CheckpointRecord:
    """Convert a mapping payload into a :class:`CheckpointRecord`."""

    return _record_from_dict(dict(payload))


__all__ = [
    "CheckpointRecord",
    "LibraryRefreshWorker",
    "MonitoringResult",
    "compute_registry_digest",
    "record_from_payload",
]
