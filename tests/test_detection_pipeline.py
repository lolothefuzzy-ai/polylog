import time

import numpy as np
import pytest

from polylog6.detection import patterns as patterns_module
from polylog6.detection import segmentation as segmentation_module
from polylog6.detection.candidate_generation import CandidateGenerator
from polylog6.detection.optimizer import CandidateOptimizer
from polylog6.detection.service import DetectionTask, ImageDetectionService
from polylog6.detection.topology import HullSummary


class _FakeSegmenter:
    def segment(self, image_path):  # pragma: no cover - simple stub
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
    def analyze(self, image_path, regions):  # pragma: no cover - simple stub
        return {
            0: {
                "periods": [(10.0, 10.0, 1.0)],
                "symmetries": {"horizontal": 0.9},
                "edge_complexity": 42,
            }
        }


def _await_queue_flush(service: ImageDetectionService, timeout: float = 1.0) -> None:
    queue = getattr(service, "_telemetry_queue", None)
    if queue is None:
        return

    deadline = time.perf_counter() + timeout
    while not queue.empty() and time.perf_counter() < deadline:
        time.sleep(0.01)
    queue.join()


def test_detection_service_returns_plan(monkeypatch):
    telemetry_payloads = []

    service = ImageDetectionService(
        segmenter=_FakeSegmenter(),
        pattern_analyzer=_FakePatternAnalyzer(),
        candidate_generator=CandidateGenerator(polyform_library=["square", "triangle"]),
        optimizer=CandidateOptimizer(),
        telemetry_emitter=lambda payload: telemetry_payloads.append(payload),
    )

    result = service.analyze(DetectionTask(image_path="ignored.png"))
    _await_queue_flush(service)

    assert result["plan"].coverage_percent == 100.0
    assert len(result["plan"].candidates) == 1
    candidate = result["plan"].candidates[0]
    assert candidate.polyform_type == "square"
    assert candidate.metadata["hull_metrics"]["compactness"] == pytest.approx(1.0)
    assert pytest.approx(result["plan"].stats["avg_score"], rel=1e-3) == 3.116
    assert result["plan"].stats.get("hull", {}).get("hull_count") == 1

    assert "topology" in result
    assert result["topology"]["regions"]

    assert telemetry_payloads
    telemetry = telemetry_payloads[0]
    assert telemetry["candidate_count"] >= len(result["plan"].candidates)
    assert pytest.approx(telemetry["avg_candidate_score"], rel=1e-3) == 3.116
    assert telemetry["hull_region_count"] == 1
    assert telemetry["hull_volume_total"] == 0.0


def test_candidate_generator_hull_metrics_influence_scoring():
    generator = CandidateGenerator(polyform_library=["square"])

    regions = [
        {
            "label": 1,
            "bbox": (0, 0, 20, 10),
        }
    ]
    descriptors = {
        1: {
            "periods": [(8.0, 8.0, 1.0)],
            "symmetries": {"horizontal": 0.8},
            "edge_complexity": 60,
        }
    }
    hull = HullSummary(
        method="numpy",
        vertex_count=4,
        face_count=0,
        volume=150.0,
        surface_area=None,
        bounding_box=((0.0, 0.0, 0.0), (20.0, 10.0, 0.0)),
    )

    candidates = generator.generate(regions, descriptors, {1: hull})

    assert len(candidates) == 1
    metadata = candidates[0].metadata
    metrics = metadata["hull_metrics"]
    assert metrics["planar_area"] == pytest.approx(200.0)
    assert metrics["compactness"] == pytest.approx(0.5)
    assert metrics["density"] == pytest.approx(min(1.0, 150.0 / 200.0))
    assert candidates[0].score >= 2.9


def test_detection_pipeline_completes_under_time_budget():
    service = ImageDetectionService(
        segmenter=_FakeSegmenter(),
        pattern_analyzer=_FakePatternAnalyzer(),
        candidate_generator=CandidateGenerator(polyform_library=["square"]),
        optimizer=CandidateOptimizer(),
    )

    start = time.perf_counter()
    service.analyze(DetectionTask(image_path="ignored.png"))
    duration = time.perf_counter() - start

    assert duration < 0.5, f"Detection pipeline took too long: {duration:.4f}s"


def test_segmentation_returns_empty_without_optional_dependencies(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(segmentation_module, "cv2", None, raising=False)
    monkeypatch.setattr(segmentation_module, "np", None, raising=False)

    segmenter = segmentation_module.ImageSegmenter()
    assert segmenter.segment("dummy.png") == []


def test_pattern_analyzer_returns_empty_without_optional_dependencies(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(patterns_module, "cv2", None, raising=False)
    monkeypatch.setattr(patterns_module, "np", None, raising=False)

    analyzer = patterns_module.PatternAnalyzer()
    assert analyzer.analyze("dummy.png", []) == {}


def test_detection_task_options_override_optimizer(monkeypatch: pytest.MonkeyPatch):
    telemetry_payloads = []

    service = ImageDetectionService(
        segmenter=_FakeSegmenter(),
        pattern_analyzer=_FakePatternAnalyzer(),
        candidate_generator=CandidateGenerator(polyform_library=["square", "triangle", "hexagon"]),
        optimizer=CandidateOptimizer(),
        telemetry_emitter=lambda payload: telemetry_payloads.append(payload),
    )

    monkeypatch.setattr(service, "_segmenter_for_task", lambda task: _FakeSegmenter())

    result = service.analyze(
        DetectionTask(
            image_path="ignored.png",
            options={"optimizer": {"max_candidates_per_region": 2}},
        )
    )

    _await_queue_flush(service)

    assert len(result["plan"].candidates) == 2
    assert telemetry_payloads[0]["candidate_count"] == 3


def test_segmenter_prefers_felzenszwalb_when_available(monkeypatch: pytest.MonkeyPatch):
    def fake_felzenszwalb(array, *, scale, sigma, min_size):  # type: ignore[override]
        labels = np.zeros((array.shape[0], array.shape[1]), dtype=int)
        labels[:, array.shape[1] // 2 :] = 1
        return labels

    monkeypatch.setattr(segmentation_module, "felzenszwalb", fake_felzenszwalb, raising=False)

    segmenter = segmentation_module.ImageSegmenter(
        options=segmentation_module.SegmentationOptions(min_region_pixels=10)
    )
    image = np.ones((8, 8, 3), dtype=np.uint8) * 255

    regions = segmenter.segment(image)

    assert len(regions) == 2
