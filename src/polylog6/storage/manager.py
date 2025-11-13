"""Runtime storage manager integrating encoder/decoder with workspace context."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, List, Optional, Protocol, Tuple, Union

from .encoder import EncodedPolygon, PolyformDecoder, PolyformEncoder


class EncodedPolygonProducer(Protocol):
    """Provides an iterator over encoded polygon entries."""

    def iter_encoded_polygons(self) -> Iterable[EncodedPolygon]:
        """Yield encoded polygons in workspace order."""


class EncodedPolygonConsumer(Protocol):
    """Consumes decoded storage chunks."""

    def ingest_tokens(self, chunk_index: int, tokens: List[Tuple[str, Union[int, EncodedPolygon]]]) -> None:
        """Apply decoded tokens (polygons/modules) for the given chunk."""


@dataclass(slots=True)
class StorageChunk:
    """Metadata and payload for a single storage chunk."""

    index: int
    payload: str
    count: int
    registry_state: Optional[dict] = None


def _chunk_iterable(iterable: Iterable[EncodedPolygon], size: int) -> Iterator[List[EncodedPolygon]]:
    batch: List[EncodedPolygon] = []
    for item in iterable:
        batch.append(item)
        if len(batch) >= size:
            yield batch
            batch = []
    if batch:
        yield batch


class PolyformStorageManager:
    """Coordinates chunked save/load operations for the polyform workspace."""

    def __init__(
        self,
        base_path: Union[str, Path],
        *,
        chunk_size: int = 10_000,
        snapshot_interval: int = 1,
        encoder: Optional[PolyformEncoder] = None,
        decoder: Optional[PolyformDecoder] = None,
    ) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if snapshot_interval <= 0:
            raise ValueError("snapshot_interval must be positive")
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.chunk_size = chunk_size
        self.snapshot_interval = snapshot_interval
        self.encoder = encoder or PolyformEncoder()
        self.decoder = decoder or PolyformDecoder(registry=self.encoder.registry)

    # ------------------------------------------------------------------
    # Save API
    # ------------------------------------------------------------------
    def save_workspace(self, name: str, producer: EncodedPolygonProducer) -> Path:
        """Stream encoded polygons to disk in chunked JSON lines format."""
        target = self.base_path / f"{name}.jsonl"
        total_polygons = 0
        with target.open("w", encoding="utf-8") as handle:
            metadata = {
                "type": "meta",
                "chunk_size": self.chunk_size,
                "snapshot_interval": self.snapshot_interval,
            }
            handle.write(json.dumps(metadata) + "\n")

            for index, batch in enumerate(_chunk_iterable(producer.iter_encoded_polygons(), self.chunk_size)):
                payload = self.encoder.encode_polygons(batch)
                total_polygons += len(batch)
                record: dict = {
                    "type": "chunk",
                    "index": index,
                    "count": len(batch),
                    "payload": payload,
                }
                if index % self.snapshot_interval == 0:
                    record["registry_state"] = self.encoder.registry.export_state()
                handle.write(json.dumps(record) + "\n")

            summary = {
                "type": "summary",
                "total_polygons": total_polygons,
                "chunks": max(0, total_polygons + self.chunk_size - 1) // self.chunk_size,
            }
            handle.write(json.dumps(summary) + "\n")
        return target

    # ------------------------------------------------------------------
    # Load API
    # ------------------------------------------------------------------
    def load_stream(self, path: Union[str, Path]) -> Iterator[Tuple[int, List[Tuple[str, Union[int, EncodedPolygon]]]]]:
        """Yield decoded chunk payloads from storage."""
        source = Path(path)
        registry_loaded = False
        with source.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                record = json.loads(line)
                record_type = record.get("type")
                if record_type == "meta" or record_type == "summary":
                    continue
                if record_type != "chunk":
                    raise ValueError(f"Unknown record type: {record_type}")
                registry_state = record.get("registry_state")
                if registry_state is not None or not registry_loaded:
                    self.encoder.registry.load_state(registry_state or {})
                    registry_loaded = True
                payload = record["payload"]
                tokens = self.decoder.decode(payload)
                yield record["index"], tokens

    def restore_to_workspace(self, path: Union[str, Path], consumer: EncodedPolygonConsumer) -> None:
        """Stream decoded chunks directly into a workspace consumer."""
        for chunk_index, tokens in self.load_stream(path):
            consumer.ingest_tokens(chunk_index, tokens)
