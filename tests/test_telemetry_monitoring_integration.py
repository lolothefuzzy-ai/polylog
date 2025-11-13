"""Integration coverage for telemetry → monitoring wiring."""

from __future__ import annotations

import time
from typing import Any, Iterable

import pytest

from polylog6.detection.candidate_generation import CandidateGenerator
from polylog6.detection.optimizer import CandidateOptimizer
from polylog6.detection.service import DetectionTask, ImageDetectionService
from polylog6.monitoring.service import (
    MonitoringService,
    reset_monitoring_service,
    set_monitoring_service_for_testing,
)


class _FixedSegmenter:
    def __init__(self, regions: Iterable[dict[str, Any]]) -> None:
        self._regions = list(regions)

    def segment(self, image_path: str) -> list[dict[str, Any]]:  # pragma: no cover - simple stub
        return list(self._regions)


class _FixedPatternAnalyzer:
    def __init__(self, descriptors: dict[int, dict[str, Any]]) -> None:
        self._descriptors = descriptors

    def analyze(self, image_path: str, regions: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:  # pragma: no cover - simple stub
        return dict(self._descriptors)


def _drain_queue(service: ImageDetectionService, timeout: float = 1.0) -> None:
    queue = getattr(service, "_telemetry_queue", None)
    if queue is None:
        return

    deadline = time.perf_counter() + timeout
    while not queue.empty() and time.perf_counter() < deadline:
        time.sleep(0.01)
    queue.join()


@pytest.fixture()
def monitoring_stub() -> tuple[MonitoringService, list[dict[str, Any]]]:
    forwarded: list[dict[str, Any]] = []
    service = MonitoringService(telemetry_consumer=forwarded.append)
    set_monitoring_service_for_testing(service)
    try:
        yield service, forwarded
    finally:
        reset_monitoring_service()


@pytest.fixture()
def detection_service() -> ImageDetectionService:
    regions = [
        {
            "label": 0,
            "bbox": (0, 0, 10, 10),
            "center": (5.0, 5.0),
            "area": 100,
            "color_mean": (120.0, 110.0, 100.0),
            "mask": None,
        }
    ]
    descriptors = {
        0: {
            "periods": [(10.0, 10.0, 1.0)],
            "symmetries": {"horizontal": 0.9},
            "edge_complexity": 42,
        }
    }

    return ImageDetectionService(
        segmenter=_FixedSegmenter(regions),
        pattern_analyzer=_FixedPatternAnalyzer(descriptors),
        candidate_generator=CandidateGenerator(polyform_library=["square", "triangle"]),
        optimizer=CandidateOptimizer(),
    )


def test_detection_telemetry_reaches_monitoring(monitoring_stub, detection_service):
    monitoring_service, forwarded = monitoring_stub
    telemetry_payloads: list[dict[str, Any]] = []

    service = ImageDetectionService(
        segmenter=detection_service.segmenter,
        pattern_analyzer=detection_service.pattern_analyzer,
        candidate_generator=detection_service.candidate_generator,
        optimizer=detection_service.optimizer,
        telemetry_emitter=lambda payload: telemetry_payloads.append(payload),
        topology_detector=detection_service.topology_detector,
    )

    result = service.analyze(DetectionTask(image_path="ignored.png"))
    _drain_queue(service)

    assert result["telemetry"]["region_count"] == 1
    assert forwarded, "Monitoring service did not receive telemetry"
    assert telemetry_payloads, "Telemetry emitter did not receive payload"
    assert monitoring_service.alert_sink.alerts() == []


def test_slow_detection_emits_alert(monkeypatch, monitoring_stub, detection_service):
    monitoring_service, forwarded = monitoring_stub

    # Force perf_counter delta to simulate >30s detection duration.
    perf_calls = iter([0.0, 40.0])
    monkeypatch.setattr("polylog6.detection.service.time.perf_counter", lambda: next(perf_calls))

    service = detection_service
    service.analyze(DetectionTask(image_path="ignored.png"))
    _drain_queue(service)

    alerts = monitoring_service.alert_sink.alerts()
    assert alerts, "Expected slow detection alert"
    assert any(alert.metadata.get("code") == "slow_detection" for alert in alerts)
    assert forwarded, "Telemetry payload not forwarded to monitoring"


def test_zero_region_alert_via_monitoring_service(monitoring_stub):
    monitoring_service, forwarded = monitoring_stub

    payload = {
        "request_id": "zero",
        "region_count": 0,
        "duration_ms": 10.0,
        "schema_version": "0.1",
    }

    monitoring_service.ingest_telemetry(payload)

    alerts = monitoring_service.alert_sink.alerts()
    assert any(alert.metadata.get("code") == "zero_regions" for alert in alerts)
    assert forwarded[-1] == payload
