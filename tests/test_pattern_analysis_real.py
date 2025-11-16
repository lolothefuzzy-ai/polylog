"""Pattern analysis regression tests using calibrated segmentation fixtures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

import cv2  # type: ignore
import pytest

from polylog6.detection.patterns import PatternAnalyzer, PATTERN_THRESHOLD_PATH
from polylog6.detection.segmentation import ImageSegmenter, SegmentationOptions

FIXTURE_DIR = Path("tests/fixtures/images")
PATTERN_BASELINES = Path("tests/fixtures/expected_patterns.json")
SEGMENTATION_BASELINES = Path("tests/fixtures/expected_segmentations.json")


@pytest.fixture(scope="module")
def fixture_images() -> Dict[str, "cv2.typing.MatLike"]:
    if not FIXTURE_DIR.exists():
        pytest.skip("Fixture images missing; run `python scripts/validate_detection_input.py`")

    images: Dict[str, "cv2.typing.MatLike"] = {}
    for image_path in FIXTURE_DIR.glob("*.png"):
        image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
        if image is not None:
            images[image_path.name] = image
    if not images:
        pytest.skip("No fixtures could be loaded")
    return images


@pytest.fixture(scope="module")
def pattern_baselines() -> dict[str, dict[str, float]]:
    if not PATTERN_BASELINES.exists():
        pytest.skip("Pattern baselines missing; populate `expected_patterns.json`")
    return json.loads(PATTERN_BASELINES.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def tuned_analyzer() -> PatternAnalyzer:
    return PatternAnalyzer()


@pytest.fixture(scope="module")
def tuned_options(tuned_analyzer: PatternAnalyzer) -> PatternAnalyzer.options.__class__:
    return tuned_analyzer.options


@pytest.fixture(scope="module")
def threshold_recommendations() -> dict[str, float]:
    if not PATTERN_THRESHOLD_PATH.exists():
        pytest.skip("Pattern threshold recommendations missing; run tuning helper")
    return json.loads(PATTERN_THRESHOLD_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def segmentation_baselines() -> dict[str, dict[str, object]]:
    if not SEGMENTATION_BASELINES.exists():
        pytest.skip("Segmentation baselines missing; run calibration script first")
    return json.loads(SEGMENTATION_BASELINES.read_text(encoding="utf-8"))


def _extract_region_key(image_name: str, idx: int) -> str:
    return f"{image_name}:region_{idx}"


def _segmenter_for_fixture(
    fixture_name: str,
    baselines: dict[str, dict[str, object]],
) -> ImageSegmenter:
    params = baselines.get(fixture_name, {}).get("felzenszwalb_params", {})
    options = SegmentationOptions(**params) if params else None
    return ImageSegmenter(options=options)


def test_analyzer_options_match_recommendations(
    tuned_options: PatternAnalyzer.options.__class__,
    threshold_recommendations: dict[str, float],
) -> None:
    if "symmetry_threshold" in threshold_recommendations:
        assert tuned_options.symmetry_threshold == pytest.approx(
            threshold_recommendations["symmetry_threshold"], rel=0.01
        )
    if "fft_strength_threshold" in threshold_recommendations:
        assert tuned_options.fft_strength_threshold == pytest.approx(
            threshold_recommendations["fft_strength_threshold"], rel=0.01
        )
    if "fft_peak_median" in threshold_recommendations:
        expected_peaks = max(int(round(threshold_recommendations["fft_peak_median"])), 1)
        assert tuned_options.max_period_peaks == expected_peaks


def test_symmetry_scores_within_range(
    fixture_images: Dict[str, "cv2.typing.MatLike"],
    segmentation_baselines: dict[str, dict[str, object]],
    tuned_analyzer: PatternAnalyzer,
) -> None:
    for image_name, image in fixture_images.items():
        segmenter = _segmenter_for_fixture(image_name, segmentation_baselines)
        regions = segmenter.segment(image)
        descriptors = tuned_analyzer.analyze(image, regions)
        for label, descriptor in descriptors.items():
            symmetry = descriptor.get("symmetries", {})
            for axis, score in symmetry.items():
                assert 0.0 <= score <= 1.0, (
                    f"Symmetry score {score:.2f} ({axis}) out of range for {image_name}"
                )


def test_fft_peak_count_reasonable(
    fixture_images: Dict[str, "cv2.typing.MatLike"],
    segmentation_baselines: dict[str, dict[str, object]],
    tuned_analyzer: PatternAnalyzer,
    tuned_options: PatternAnalyzer.options.__class__,
) -> None:
    for image_name, image in fixture_images.items():
        segmenter = _segmenter_for_fixture(image_name, segmentation_baselines)
        regions = segmenter.segment(image)
        descriptors = tuned_analyzer.analyze(image, regions)
        for descriptor in descriptors.values():
            peaks = descriptor.get("periods", [])
            assert len(peaks) <= tuned_options.max_period_peaks, (
                f"Excessive FFT peaks ({len(peaks)}) detected for {image_name}"
            )
            for peak in peaks:
                assert len(peak) == 3
                magnitude = peak[2]
                assert magnitude >= 0.0


def test_patterns_against_baseline(
    fixture_images: Dict[str, "cv2.typing.MatLike"],
    pattern_baselines: dict[str, dict[str, float]],
    segmentation_baselines: dict[str, dict[str, object]],
    tuned_analyzer: PatternAnalyzer,
    tuned_options: PatternAnalyzer.options.__class__,
) -> None:
    for image_name, image in fixture_images.items():
        segmenter = _segmenter_for_fixture(image_name, segmentation_baselines)
        regions = segmenter.segment(image)
        descriptors = tuned_analyzer.analyze(image, regions)
        for idx, descriptor in descriptors.items():
            region_key = _extract_region_key(image_name, idx)
            if region_key not in pattern_baselines:
                continue
            expected = pattern_baselines[region_key]
            symmetry = descriptor.get("symmetries", {})
            for axis, target in expected.get("symmetry", {}).items():
                if axis in symmetry:
                    assert abs(symmetry[axis] - target) <= 0.2, (
                        f"Symmetry deviation {symmetry[axis]:.2f} vs {target:.2f}"
                    )
                    assert symmetry[axis] >= tuned_options.symmetry_threshold - 1e-6
            peaks = descriptor.get("periods", [])
            if "fft_peak_count" in expected:
                assert abs(len(peaks) - expected["fft_peak_count"]) <= 3, (
                    f"FFT peak count {len(peaks)} drift for {region_key}"
                )
