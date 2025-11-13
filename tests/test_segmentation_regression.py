"""Regression tests for segmentation calibration fixtures (INT-014 Phase 2)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

import cv2  # type: ignore
import pytest

from polylog6.detection.segmentation import ImageSegmenter, SegmentationOptions

FIXTURE_DIR = Path("tests/fixtures/images")
BASELINE_PATH = Path("tests/fixtures/expected_segmentations.json")


@pytest.fixture(scope="module")
def segmentation_baselines() -> dict[str, dict[str, object]]:
    if not BASELINE_PATH.exists():
        pytest.skip("Run `python scripts/calibrate_segmentation.py` to generate baselines")
    return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def fixture_images() -> Dict[str, "cv2.typing.MatLike"]:
    if not FIXTURE_DIR.exists():
        pytest.skip("Fixture images missing; run `python scripts/validate_detection_input.py`")

    images: dict[str, "cv2.typing.MatLike"] = {}
    for image_path in FIXTURE_DIR.glob("*.png"):
        image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
        if image is not None:
            images[image_path.name] = image
    if not images:
        pytest.skip("No fixtures could be loaded")
    return images


@pytest.mark.parametrize("fixture_name", [
    "simple_triangle.png",
    "grid_pattern.png",
    "noisy_polyform.png",
])
def test_segment_region_counts(
    fixture_name: str,
    fixture_images: Dict[str, "cv2.typing.MatLike"],
    segmentation_baselines: dict[str, dict[str, object]],
) -> None:
    if fixture_name not in fixture_images:
        pytest.skip(f"Fixture {fixture_name} not available")
    if fixture_name not in segmentation_baselines:
        pytest.skip(f"No baseline for {fixture_name}; re-run calibration")

    image = fixture_images[fixture_name]
    baseline = segmentation_baselines[fixture_name]

    params = segmentation_baselines[fixture_name].get("felzenszwalb_params", {})
    options = SegmentationOptions(**params) if params else None
    segmenter = ImageSegmenter(options=options)
    regions = segmenter.segment(image)

    expected = int(baseline["expected_regions"])
    tolerance = int(baseline.get("tolerance", 2))

    assert expected - tolerance <= len(regions) <= expected + tolerance, (
        f"Region count {len(regions)} outside tolerance ±{tolerance} (expected {expected})"
    )


@pytest.mark.parametrize("fixture_name", [
    "simple_triangle.png",
    "grid_pattern.png",
    "noisy_polyform.png",
])
def test_segment_coverage_ratio(
    fixture_name: str,
    fixture_images: Dict[str, "cv2.typing.MatLike"],
    segmentation_baselines: dict[str, dict[str, object]],
) -> None:
    if fixture_name not in fixture_images or fixture_name not in segmentation_baselines:
        pytest.skip(f"Baseline missing for {fixture_name}")

    image = fixture_images[fixture_name]
    baseline = segmentation_baselines[fixture_name]

    params = segmentation_baselines[fixture_name].get("felzenszwalb_params", {})
    options = SegmentationOptions(**params) if params else None
    segmenter = ImageSegmenter(options=options)
    regions = segmenter.segment(image)

    total_area = sum(int(region.get("area", 0)) for region in regions)
    image_area = image.shape[0] * image.shape[1]
    coverage = total_area / max(image_area, 1)

    min_coverage = float(baseline.get("min_coverage_ratio", 0.5))
    assert coverage >= min_coverage, (
        f"Coverage {coverage:.2%} below minimum {min_coverage:.2%} for {fixture_name}"
    )
