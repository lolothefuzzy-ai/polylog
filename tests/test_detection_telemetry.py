"""Telemetry regression tests for ImageDetectionService fast-path wiring."""

from __future__ import annotations

import threading
import time
from typing import Any

import pytest

from polylog6.detection.candidate_generation import CandidateGenerator
from polylog6.detection.optimizer import CandidateOptimizer
from polylog6.detection.service import DetectionTask, ImageDetectionService
from polylog6.detection.topology import HullSummary


class _FakeSegmenter:
    def segment(self, image_path: str) -> list[dict[str, Any]]:  # pragma: no cover - stub
        return [
            {
                "label": 0,
                "bbox": (0, 0, 10, 10),
                "center": (5.0, 5.0),
                "area": 100,
                "color_mean": (120.0, 110.0, 100.0),
                "mask": None,
            }
        ]


class _FakePatternAnalyzer:
    def analyze(self, image_path: str, regions: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:  # pragma: no cover - stub
        return {
            0: {
                "periods": [(10.0, 10.0, 1.5)],
                "symmetries": {"horizontal": 0.9, "vertical": 0.88},
                "edge_complexity": 42,
            }
        }


class _FakeTopologyDetector:
    available_backends = ("fake",)
    primary_backend = "fake"

    def compute_convex_hull(self, vertices: list[tuple[float, float, float]]) -> HullSummary:  # pragma: no cover - stub
        return HullSummary(
            method="fake",
            vertex_count=len(vertices),
            face_count=0,
            volume=25.0,
            surface_area=None,
            bounding_box=((0.0, 0.0, 0.0), (10.0, 10.0, 0.0)),
        )


def _build_service(telemetry_sink):
    return ImageDetectionService(
        segmenter=_FakeSegmenter(),
        pattern_analyzer=_FakePatternAnalyzer(),
        candidate_generator=CandidateGenerator(polyform_library=["square", "triangle"]),
        optimizer=CandidateOptimizer(),
        telemetry_emitter=telemetry_sink,
        topology_detector=_FakeTopologyDetector(),
    )


def _await_queue_flush(service: ImageDetectionService, timeout: float = 1.0) -> None:
    queue = getattr(service, "_telemetry_queue", None)
    if queue is None:
        return
    deadline = time.perf_counter() + timeout
    while not queue.empty() and time.perf_counter() < deadline:
        time.sleep(0.01)
    queue.join()


def test_telemetry_payload_contains_cached_metrics():
    payloads: list[dict[str, Any]] = []
    service = _build_service(payloads.append)

    result = service.analyze(DetectionTask(image_path="ignored.png"))

    _await_queue_flush(service)
    assert payloads, "Telemetry payloads were not emitted"
    payload = payloads[-1]

    assert payload["schema_version"] == ImageDetectionService.TELEMETRY_SCHEMA_VERSION
    assert payload["request_id"]
    assert payload["timestamp"].endswith("Z")
    assert payload["region_count"] == 1
    assert payload["candidate_count"] >= 1
    assert payload["symmetry_score_max"] >= payload["symmetry_score_avg"] >= 0.0
    assert payload["dominant_period_strength"] >= 0.0
    assert payload["dominant_period_count"] >= 1
    assert payload["fft_peak_count"] == payload["dominant_period_count"]
    assert payload["hull_volume_total"] == pytest.approx(25.0)
    assert payload["avg_hull_volume"] == pytest.approx(25.0)
    assert payload["detection_duration_ms"] >= 0.0
    assert payload["duration_ms"] == pytest.approx(payload["detection_duration_ms"], abs=1e-6)

    metrics = result["analysis_metrics"]
    assert metrics["symmetry_score_sample_count"] >= 1
    assert result["telemetry"] == payload


def test_analyze_returns_under_latency_target():
    payloads: list[dict[str, Any]] = []
    service = _build_service(payloads.append)

    started = time.perf_counter()
    service.analyze(DetectionTask(image_path="ignored.png"))
    elapsed_ms = (time.perf_counter() - started) * 1000.0

    _await_queue_flush(service)

    assert elapsed_ms < 150.0, f"Detection pipeline latency {elapsed_ms:.2f}ms exceeded target"


def test_queue_decouples_slow_telemetry_emitter():
    payloads: list[dict[str, Any]] = []
    completed = threading.Event()

    def slow_emitter(payload: dict[str, Any]) -> None:
        try:
            time.sleep(0.2)
            payloads.append(payload)
        finally:
            completed.set()

    service = _build_service(slow_emitter)

    started = time.perf_counter()
    service.analyze(DetectionTask(image_path="ignored.png"))
    elapsed_ms = (time.perf_counter() - started) * 1000.0

    assert elapsed_ms < 150.0, "Telemetry queue should decouple slow emitters"

    assert completed.wait(1.0), "Slow emitter did not process payload in time"
    _await_queue_flush(service)


def test_metrics_cache_clears_after_emit():
    payloads: list[dict[str, Any]] = []
    service = _build_service(payloads.append)

    service.analyze(DetectionTask(image_path="ignored.png"))

    # Allow queue to drain and ensure per-request cache is cleared.
    _await_queue_flush(service)
    cache = getattr(service, "_metrics_cache")
    assert cache == {}
