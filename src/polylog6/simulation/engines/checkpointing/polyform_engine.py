"""Streaming-aware engine that coordinates geometry checkpoints."""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from polylog6.storage.manager import PolyformStorageManager

from .workspace import PolyformWorkspace


@dataclass(slots=True)
class CheckpointSummary:
    """Metadata describing a saved workspace snapshot."""

    label: str
    path: Path
    polygons: int
    chunk_count: int
    module_refs: int
    registry_digest: str
    timestamp: float


class PolyformEngine:
    """Central coordinator between geometry workspace and storage manager."""

    def __init__(
        self,
        *,
        workspace: Optional[PolyformWorkspace] = None,
        storage_manager: Optional[PolyformStorageManager] = None,
        chunk_dir: Optional[Path] = None,
        chunk_size: int = 10_000,
        snapshot_interval: int = 3,
        inbox_path: Optional[Path] = None,
    ) -> None:
        self.workspace = workspace or PolyformWorkspace()
        base_path = Path(chunk_dir) if chunk_dir is not None else Path("storage/chunks")
        self.storage_manager = storage_manager or PolyformStorageManager(
            base_path,
            chunk_size=chunk_size,
            snapshot_interval=snapshot_interval,
        )
        self._inbox_path = Path(inbox_path) if inbox_path is not None else None

    # ------------------------------------------------------------------
    # Checkpoint lifecycle
    # ------------------------------------------------------------------
    def checkpoint(self, label: str, *, inbox_path: Optional[Path] = None) -> CheckpointSummary:
        """Persist the current workspace and emit coordination metadata."""

        resolved_inbox = Path(inbox_path) if inbox_path is not None else self._inbox_path

        checkpoint_path = self.storage_manager.save_workspace(label, self.workspace)
        summary = CheckpointSummary(
            label=label,
            path=checkpoint_path,
            polygons=self.workspace.polygon_count(),
            chunk_count=self._chunk_count(),
            module_refs=len(self.workspace.module_references()),
            registry_digest=self._registry_digest(),
            timestamp=time.time(),
        )
        if resolved_inbox is not None:
            self._append_async_log(resolved_inbox, summary)
        return summary

    def restore_from(self, checkpoint_path: Path) -> None:
        """Replay a checkpoint into the managed workspace."""

        self.workspace.clear()
        for chunk_index, tokens in self.storage_manager.load_stream(checkpoint_path):
            self.workspace.ingest_tokens(chunk_index, tokens)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _append_async_log(self, inbox_path: Path, summary: CheckpointSummary) -> None:
        inbox_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "label": summary.label,
            "path": str(summary.path),
            "polygons": summary.polygons,
            "chunk_count": summary.chunk_count,
            "module_refs": summary.module_refs,
            "registry_digest": summary.registry_digest,
            "timestamp": summary.timestamp,
        }
        with inbox_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload) + "\n")

    def _registry_digest(self) -> str:
        state = self.storage_manager.encoder.registry.export_state()
        serialized = json.dumps(state, sort_keys=True).encode("utf-8")
        return hashlib.sha256(serialized).hexdigest()

    def _chunk_count(self) -> int:
        polygons = self.workspace.polygon_count()
        size = self.storage_manager.chunk_size
        if polygons == 0:
            return 0
        return (polygons + size - 1) // size


__all__ = ["CheckpointSummary", "PolyformEngine"]
