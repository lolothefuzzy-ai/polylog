"""Calibrate Felzenszwalb segmentation parameters on curated fixtures.

Usage:
    python scripts/calibrate_segmentation.py

Outputs:
    - Segmentation overlays in ``tests/fixtures/segmentation_snapshots/<fixture>/``.
    - Recommended parameters written to ``tests/fixtures/expected_segmentations.json``.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

try:  # pragma: no cover - optional dependency guard
    import cv2  # type: ignore
except ImportError:  # pragma: no cover - handled gracefully below
    cv2 = None  # type: ignore

try:  # pragma: no cover
    import numpy as np
except ImportError:  # pragma: no cover
    np = None  # type: ignore

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from polylog6.detection.segmentation import ImageSegmenter, SegmentationOptions  # noqa: E402

FIXTURE_DIR = Path("tests/fixtures/images")
SNAPSHOT_DIR = Path("tests/fixtures/segmentation_snapshots")
OUTPUT_JSON = Path("tests/fixtures/expected_segmentations.json")

SCALE_VALUES = (50.0, 100.0, 200.0, 400.0)
SIGMA_VALUES = (0.5, 0.8, 1.0)
MIN_SIZE_VALUES = (20, 50, 100)
TARGET_REGION_COUNT = 10


@dataclass(slots=True)
class CalibrationResult:
    params: SegmentationOptions
    num_regions: int
    avg_area: float
    coverage_ratio: float

    def score(self) -> float:
        """Heuristic score favouring ~10 regions with decent coverage."""

        region_score = 1.0 - (abs(self.num_regions - TARGET_REGION_COUNT) / TARGET_REGION_COUNT)
        coverage_score = min(self.coverage_ratio, 1.0)
        return (0.6 * region_score) + (0.4 * coverage_score)


def _dependencies_ready() -> bool:
    if cv2 is None:
        print("✗ OpenCV (cv2) is not installed. Install opencv-python to run calibration.")
        return False
    if np is None:
        print("✗ NumPy is not installed. Install numpy to run calibration.")
        return False
    return True


def calibrate_fixture(image_path: Path) -> CalibrationResult | None:
    if cv2 is None or np is None:
        return None

    image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
    if image is None:
        print(f"✗ Could not load fixture: {image_path}")
        return None

    results: list[CalibrationResult] = []
    for scale in SCALE_VALUES:
        for sigma in SIGMA_VALUES:
            for min_size in MIN_SIZE_VALUES:
                options = SegmentationOptions(
                    felzenszwalb_scale=scale,
                    felzenszwalb_sigma=sigma,
                    felzenszwalb_min_size=min_size,
                    use_felzenszwalb=True,
                )
                segmenter = ImageSegmenter(options=options)
                regions = segmenter.segment(image)
                if not regions:
                    continue

                areas = [int(region.get("area", 0)) for region in regions]
                total_area = float(sum(areas))
                image_area = float(image.shape[0] * image.shape[1]) or 1.0
                coverage_ratio = total_area / image_area
                avg_area = float(np.mean(areas)) if areas else 0.0

                _save_segmentation_viz(
                    image,
                    regions,
                    SNAPSHOT_DIR / image_path.stem / f"seg_s{int(scale)}_sig{sigma}_min{min_size}.png",
                )

                results.append(
                    CalibrationResult(
                        params=options,
                        num_regions=len(regions),
                        avg_area=avg_area,
                        coverage_ratio=coverage_ratio,
                    )
                )

    if not results:
        print(f"⚠ No segmentation results produced for {image_path.name}")
        return None

    results.sort(key=lambda r: r.score(), reverse=True)
    best = results[0]

    print(
        f"→ {image_path.name}: regions={best.num_regions} avg_area={best.avg_area:.1f} "
        f"coverage={best.coverage_ratio:.2%} params=(scale={best.params.felzenszwalb_scale}, "
        f"sigma={best.params.felzenszwalb_sigma}, min_size={best.params.felzenszwalb_min_size})"
    )
    return best


def _save_segmentation_viz(image: "np.ndarray", regions: list[dict[str, object]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    overlay = image.copy()

    for region in regions:
        color = tuple(int(c) for c in np.random.default_rng(int(region.get("label", 0))).integers(50, 255, 3))
        mask = region.get("mask")
        if mask is not None and np is not None:
            overlay[mask] = color
        else:
            bbox = region.get("bbox")
            if bbox is not None:
                x_min, y_min, x_max, y_max = map(int, bbox)
                cv2.rectangle(overlay, (x_min, y_min), (x_max, y_max), color, 2)

    blended = cv2.addWeighted(image, 0.5, overlay, 0.5, 0)
    cv2.imwrite(str(output_path), blended)


def _load_existing_recommendations() -> dict[str, dict[str, object]]:
    if OUTPUT_JSON.exists():
        try:
            return json.loads(OUTPUT_JSON.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {}


def _record_recommendation(
    accumulator: dict[str, dict[str, object]],
    image_name: str,
    result: CalibrationResult,
) -> None:
    accumulator[image_name] = {
        "felzenszwalb_params": {
            "felzenszwalb_scale": result.params.felzenszwalb_scale,
            "felzenszwalb_sigma": result.params.felzenszwalb_sigma,
            "felzenszwalb_min_size": result.params.felzenszwalb_min_size,
        },
        "expected_regions": result.num_regions,
        "tolerance": max(2, int(result.num_regions * 0.3)),
        "min_coverage_ratio": round(result.coverage_ratio * 0.8, 3),
    }


def main() -> int:
    if not _dependencies_ready():
        return 1
    if not FIXTURE_DIR.exists():
        print(f"✗ Fixture directory not found: {FIXTURE_DIR}. Run scripts/validate_detection_input.py first.")
        return 1

    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    recommendations = _load_existing_recommendations()

    for image_path in sorted(FIXTURE_DIR.glob("*.png")):
        print(f"\nCalibrating {image_path.name} …")
        result = calibrate_fixture(image_path)
        if result is None:
            continue
        _record_recommendation(recommendations, image_path.name, result)

    if recommendations:
        OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_JSON.write_text(json.dumps(recommendations, indent=2), encoding="utf-8")
        print(f"\n✓ Saved recommendations to {OUTPUT_JSON}")
    else:
        print("⚠ No recommendations were generated.")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
