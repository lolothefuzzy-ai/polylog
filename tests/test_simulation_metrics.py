from __future__ import annotations

import gzip
import json
import sys
import time
from dataclasses import asdict

import pytest

from polylog6.simulation.metrics import (
    CandidateEvent,
    CanonicalSignatureFactory,
    FrequencyCounterPersistence,
    MetricsEmitter,
)


def _make_candidate_event(*, timestamp: float | None = None) -> CandidateEvent:
    timestamp = timestamp or time.time()
    composition = (3, 4, 4, 5)
    symmetry_group = "D4"
    scaler_stability = 0.82
    canonical = CanonicalSignatureFactory.compute(
        composition,
        symmetry_group,
        scaler_stability,
    )
    return CandidateEvent(
        event_id="evt-001",
        session_id="session-123",
        timestamp=timestamp,
        canonical_signature=canonical,
        composition=composition,
        symmetry_group=symmetry_group,
        symmetry_score=0.84,
        shared_edges=4,
        multi_edge_count=2,
        attachment_scalers=[0.91, 0.88],
        scaler_stability=scaler_stability,
        frequency_in_session=5,
        slider_params={"alpha": 0.42},
        candidate_hash=canonical,
        tier=0,
        compression_metadata={"ratio": 11.5},
    )


def test_canonical_signature_factory_is_deterministic() -> None:
    signature_a = CanonicalSignatureFactory.compute((3, 5, 4), "C3", 0.91)
    signature_b = CanonicalSignatureFactory.compute((5, 3, 4), "C3", 0.91)
    signature_c = CanonicalSignatureFactory.compute((3, 5, 4), "C4", 0.91)

    assert signature_a == signature_b
    assert signature_a != signature_c


def test_candidate_event_round_trip_serialization() -> None:
    event = _make_candidate_event()

    payload = event.to_json()
    restored = CandidateEvent.from_json(payload)

    assert asdict(event) == asdict(restored)


def test_candidate_event_validation_thresholds() -> None:
    valid_event = _make_candidate_event()
    assert valid_event.is_valid()

    below_threshold = CandidateEvent(
        event_id="evt-low",
        session_id="session-123",
        timestamp=time.time(),
        canonical_signature="deadbeefdeadbeef",
        composition=(3, 3, 3),
        symmetry_group="C1",
        symmetry_score=0.65,
        shared_edges=2,
        multi_edge_count=0,
        attachment_scalers=[],
        scaler_stability=0.6,
        frequency_in_session=1,
        slider_params={},
        candidate_hash="deadbeefdeadbeef",
    )

    assert not below_threshold.is_valid()


def test_metrics_emitter_emit_and_read_last_24h(tmp_path) -> None:
    pytest.importorskip("fcntl")

    output_path = tmp_path / "metrics.jsonl"
    emitter = MetricsEmitter(str(output_path))

    candidate = asdict(_make_candidate_event())
    emitter.emit(candidate)

    events = emitter.read_events_last_24h(now=time.time() + 1)

    assert len(events) == 1
    assert events[0]["event_id"] == candidate["event_id"]
    assert output_path.exists()


def test_metrics_emitter_rotate_archives_old_events(tmp_path) -> None:
    pytest.importorskip("fcntl")

    output_path = tmp_path / "metrics.jsonl"
    emitter = MetricsEmitter(str(output_path))

    past = time.time() - 9 * 24 * 3600
    old_candidate = asdict(_make_candidate_event(timestamp=past))
    fresh_candidate = asdict(_make_candidate_event(timestamp=time.time()))

    emitter.emit(old_candidate)
    emitter.emit(fresh_candidate)

    emitter.rotate(retention_days=7)

    archive_path = output_path.with_suffix(".archive.jsonl.gz")
    assert archive_path.exists()

    active_events = emitter.read_events_last_24h(now=time.time() + 1)
    assert len(active_events) == 1
    assert active_events[0]["event_id"] == fresh_candidate["event_id"]

    with gzip.open(archive_path, "rt", encoding="utf-8") as stream:
        archived_lines = [json.loads(line) for line in stream if line.strip()]

    assert len(archived_lines) == 1
    assert archived_lines[0]["event_id"] == old_candidate["event_id"]


def test_frequency_counter_increment_and_rotate(tmp_path) -> None:
    state_path = tmp_path / "counter.json"
    counter = FrequencyCounterPersistence(str(state_path))

    counter.increment("sig-a")
    counter.increment("sig-a")
    counter.increment("sig-b")

    counter.last_rotation = time.time() - counter.ROTATION_INTERVAL_SEC - 1
    rotated = counter.maybe_rotate()

    assert rotated
    assert counter.rotation_count == 1
    assert state_path.exists()

    stored = json.loads(state_path.read_text(encoding="utf-8"))
    assert stored["sig-a"]["count"] == 2
    assert stored["sig-b"]["count"] == 1

    reloaded = FrequencyCounterPersistence(str(state_path))
    reloaded.load()

    assert reloaded.map["sig-a"]["count"] == 2
    assert reloaded.map["sig-b"]["count"] == 1


@pytest.mark.skipif(sys.platform.startswith("win"), reason="fcntl unavailable on Windows")
def test_metrics_emitter_is_process_safe(tmp_path) -> None:
    """Ensure concurrent emissions remain newline delimited and JSON parseable."""

    emitter = MetricsEmitter(str(tmp_path / "metrics.jsonl"))
    payloads = [asdict(_make_candidate_event(timestamp=time.time() + idx)) for idx in range(4)]

    for payload in payloads:
        emitter.emit(payload)

    lines = (tmp_path / "metrics.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == len(payloads)
    assert all(json.loads(line)["event_id"].startswith("evt") for line in lines)
