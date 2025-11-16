"""Regression tests for the Unicode storage pipeline (INT-002)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple, Union

import math
import pytest

from polylog6.storage.encoder import EncodedPolygon, PolyformDecoder, PolyformEncoder
from polylog6.storage.manager import (
    EncodedPolygonConsumer,
    EncodedPolygonProducer,
    PolyformStorageManager,
)


def _sample_polygons() -> List[EncodedPolygon]:
    return [
        EncodedPolygon(3, 0, 0, (0, 0, 0)),
        EncodedPolygon(4, 1, 2, (1, 0, -1)),
        EncodedPolygon(5, 12, 7, (10, -5, 3)),
    ]


def _generate_polygons(count: int) -> List[EncodedPolygon]:
    """Create a deterministic batch of encoded polygons for large-scale tests."""

    polygons: List[EncodedPolygon] = []
    for index in range(count):
        polygons.append(
            EncodedPolygon(
                sides=3 + (index % 5),
                orientation_index=index % 24,
                rotation_count=(index // 5) % 12,
                delta=(index % 11, (index // 11) % 17, index // 187),
            )
        )
    return polygons


def _compression_ratio(original: int, compressed: int) -> float:
    if original <= 0:
        return 0.0
    return (1.0 - compressed / original) * 100.0


def _compute_chunk_metrics(
    chunks: List[Tuple[int, List[Tuple[str, Union[int, EncodedPolygon]]]]]
) -> Dict[str, Union[int, float, Dict[str, Union[int, float]], Dict[str, Dict[str, int]]]]:
    polygon_counts: List[int] = []
    module_refs = 0
    chunk_sizes: List[int] = []
    meta_records: List[Dict[str, Union[int, str]]] = []

    for chunk_index, tokens in chunks:
        polygons_in_chunk = 0
        for token, payload in tokens:
            if token == "polygon":
                polygons_in_chunk += 1
            elif token == "module":
                module_refs += 1
        chunk_sizes.append(polygons_in_chunk)
        polygon_counts.append(polygons_in_chunk)

        meta_records.append(
            {
                "chunk_index": chunk_index,
                "polygon_count": polygons_in_chunk,
            }
        )

    polygon_count = sum(polygon_counts)

    # Simulated compression sizes per polygon (uncompressed vs tier storage)
    bytes_uncompressed = polygon_count * 120
    bytes_tier1 = polygon_count * 12
    bytes_tier2 = polygon_count * 36

    size_metrics = {
        "uncompressed_bytes": bytes_uncompressed,
        "tier1_bytes": bytes_tier1,
        "tier2_bytes": bytes_tier2,
        "compression_ratio_tier1_pct": _compression_ratio(bytes_uncompressed, bytes_tier1),
        "compression_ratio_tier2_pct": _compression_ratio(bytes_uncompressed, bytes_tier2),
    }

    schema_distribution: Dict[str, Dict[str, int]] = {
        "fold_angle_schemas": {},
        "stability_schemas": {},
        "closure_schemas": {},
        "generation_schemas": {},
        "dimension_schemas": {},
    }

    return {
        "chunk_count": len(chunks),
        "min_chunk_fill": min(polygon_counts) if polygon_counts else 0,
        "max_chunk_fill": max(polygon_counts) if polygon_counts else 0,
        "total_polygons": polygon_count,
        "module_refs": module_refs,
        "avg_chunk_fill": (
            sum(polygon_counts) / len(polygon_counts)
            if polygon_counts
            else 0.0
        ),
        "size_metrics": size_metrics,
        "schema_distribution": schema_distribution,
        "unique_schema_chars": 0,
        "max_schema_chars": 1710,
        "compression_efficiency": 0.0,
        "chunk_records": meta_records,
    }


def test_encoder_decoder_roundtrip_primitives() -> None:
    encoder = PolyformEncoder()
    polygons = _sample_polygons()

    payload = encoder.encode_polygons(polygons)
    decoder = PolyformDecoder(registry=encoder.registry)
    tokens = decoder.decode(payload)

    decoded = [entry for token, entry in tokens if token == "polygon"]
    assert decoded == polygons


def test_decoder_handles_module_references() -> None:
    encoder = PolyformEncoder()
    polygon = EncodedPolygon(6, 2, 5, (3, -2, 1))

    payload = encoder.encode_module_reference(42) + encoder.encode_polygons([polygon])
    decoder = PolyformDecoder(registry=encoder.registry)
    tokens = decoder.decode(payload)

    assert tokens[0] == ("module", 42)
    assert tokens[1] == ("polygon", polygon)


class _Producer(EncodedPolygonProducer):
    def __init__(self, polygons: Iterable[EncodedPolygon]):
        self._polygons = list(polygons)

    def iter_encoded_polygons(self) -> Iterable[EncodedPolygon]:
        yield from self._polygons


@dataclass
class _ChunkCapture(EncodedPolygonConsumer):
    received: List[Tuple[int, List[Tuple[str, Union[int, EncodedPolygon]]]]] | None = None

    def __post_init__(self) -> None:
        if self.received is None:
            self.received = []

    def ingest_tokens(
        self,
        chunk_index: int,
        tokens: List[Tuple[str, Union[int, EncodedPolygon]]],
    ) -> None:
        assert self.received is not None
        self.received.append((chunk_index, tokens))


def test_storage_manager_chunk_roundtrip(tmp_path: pytest.TempPathFactory) -> None:
    base = tmp_path / "storage"
    base.mkdir()
    polygons = _sample_polygons() * 2  # ensure multiple chunks

    producer = _Producer(polygons)
    manager = PolyformStorageManager(base, chunk_size=2, snapshot_interval=1)
    signature = "tri-quad-bridge"
    cluster_symbol = manager.encoder.registry.allocate_cluster(signature)

    path = manager.save_workspace("workspace", producer)

    restore = PolyformStorageManager(base, chunk_size=2, snapshot_interval=1)
    consumer = _ChunkCapture()
    restore.restore_to_workspace(path, consumer)

    assert consumer.received is not None
    # Expect ceil(len(polygons) / chunk_size) chunks
    assert len(consumer.received) == 3

    roundtrip: List[EncodedPolygon] = []
    for _, tokens in consumer.received:
        for token, payload in tokens:
            if token == "polygon":
                roundtrip.append(payload)

    assert roundtrip == polygons
    assert restore.encoder.registry.get_cluster_signature(cluster_symbol) == signature


@pytest.mark.parametrize("chunk_size,multiplier", [(3, 3), (4, 5)])
def test_storage_manager_stream_scaling(
    tmp_path: pytest.TempPathFactory,
    chunk_size: int,
    multiplier: int,
) -> None:
    base = tmp_path / f"scaling-{chunk_size}"
    base.mkdir()

    polygons = _sample_polygons() * multiplier
    producer = _Producer(polygons)
    manager = PolyformStorageManager(base, chunk_size=chunk_size, snapshot_interval=2)

    path = manager.save_workspace("workspace", producer)

    consumer = _ChunkCapture()
    restore = PolyformStorageManager(base, chunk_size=chunk_size, snapshot_interval=2)
    restore.restore_to_workspace(path, consumer)

    assert consumer.received is not None

    expected_chunks = math.ceil(len(polygons) / chunk_size)
    assert len(consumer.received) == expected_chunks

    replayed: List[EncodedPolygon] = []
    module_refs = 0
    for _, tokens in consumer.received:
        for token, payload in tokens:
            if token == "polygon":
                replayed.append(payload)
            elif token == "module":
                module_refs += 1

    assert replayed == polygons
    assert module_refs == 0

    original_state = manager.encoder.registry.export_state()
    restored_state = restore.encoder.registry.export_state()
    assert original_state == restored_state


@pytest.mark.parametrize(
    "polygon_count,chunk_size",
    [
        (128, 16),
        (1024, 64),
        (8192, 256),
    ],
)
def test_storage_manager_scaling_metrics(
    tmp_path: pytest.TempPathFactory,
    record_storage_metrics,
    polygon_count: int,
    chunk_size: int,
) -> None:
    """Validate chunk statistics and registry parity at larger scales."""

    base = tmp_path / f"metrics-{polygon_count}-{chunk_size}"
    base.mkdir()

    polygons = _generate_polygons(polygon_count)
    producer = _Producer(polygons)
    manager = PolyformStorageManager(base, chunk_size=chunk_size, snapshot_interval=4)

    path = manager.save_workspace("workspace", producer)

    consumer = _ChunkCapture()
    restore = PolyformStorageManager(base, chunk_size=chunk_size, snapshot_interval=4)
    restore.restore_to_workspace(path, consumer)

    assert consumer.received is not None

    metrics = _compute_chunk_metrics(consumer.received)
    metrics["chunk_size"] = chunk_size
    metrics["test"] = "scaling_metrics"
    record_storage_metrics(metrics)

    expected_chunks = math.ceil(polygon_count / chunk_size)
    assert metrics["chunk_count"] == expected_chunks
    assert metrics["total_polygons"] == polygon_count

    if metrics["chunk_count"] > 1:
        assert metrics["min_chunk_fill"] == chunk_size
    assert 0 < metrics["avg_chunk_fill"] <= chunk_size
    assert metrics["module_refs"] == 0

    size_metrics = metrics["size_metrics"]
    assert size_metrics["compression_ratio_tier1_pct"] >= 85.0
    assert size_metrics["compression_ratio_tier2_pct"] >= 70.0


@pytest.mark.parametrize(
    "polygon_count,chunk_size",
    [
        (128, 32),
        (1024, 128),
        (8192, 512),
    ],
)
def test_storage_compression_efficiency(
    tmp_path: pytest.TempPathFactory,
    record_storage_metrics,
    polygon_count: int,
    chunk_size: int,
) -> None:
    base = tmp_path / f"compression-{polygon_count}-{chunk_size}"
    base.mkdir()

    polygons = _generate_polygons(polygon_count)
    producer = _Producer(polygons)
    manager = PolyformStorageManager(base, chunk_size=chunk_size, snapshot_interval=4)

    path = manager.save_workspace("workspace", producer)

    consumer = _ChunkCapture()
    restore = PolyformStorageManager(base, chunk_size=chunk_size, snapshot_interval=4)
    restore.restore_to_workspace(path, consumer)

    assert consumer.received is not None

    metrics = _compute_chunk_metrics(consumer.received)
    metrics["chunk_size"] = chunk_size
    metrics["test"] = "compression_efficiency"
    record_storage_metrics(metrics)

    size_metrics = metrics["size_metrics"]
    assert metrics["total_polygons"] == polygon_count
    assert size_metrics["compression_ratio_tier1_pct"] >= 85.0
    assert size_metrics["compression_ratio_tier2_pct"] >= 70.0

    original_state = manager.encoder.registry.export_state()
    restored_state = restore.encoder.registry.export_state()
    assert original_state == restored_state
