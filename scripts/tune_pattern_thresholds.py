"""Analyze pattern descriptors to recommend symmetry/FFT thresholds.

Usage:
    python scripts/tune_pattern_thresholds.py [fixtures_dir]

The script iterates through calibrated segmentation fixtures, computes pattern
statistics, and prints heuristic threshold recommendations. Optionally writes
results to ``tests/fixtures/pattern_thresholds.json`` if that directory exists.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from statistics import median
from typing import Iterable

try:  # pragma: no cover - optional dependencies
    import cv2  # type: ignore
except ImportError:  # pragma: no cover
    raise SystemExit("✗ OpenCV not installed. Run `pip install opencv-python`.\n")

try:  # pragma: no cover
    import numpy as np
except ImportError:  # pragma: no cover
    raise SystemExit("✗ NumPy not installed. Run `pip install numpy`.\n")

from polylog6.detection.patterns import PatternAnalyzer, PatternAnalysisOptions
from polylog6.detection.segmentation import ImageSegmenter, SegmentationOptions

SEGMENTATION_BASELINES = Path("tests/fixtures/expected_segmentations.json")
FIXTURE_DIR = Path("tests/fixtures/images")
OUTPUT_JSON = Path("tests/fixtures/pattern_thresholds.json")


def _load_segmentation_baselines() -> dict[str, dict[str, object]]:
    if not SEGMENTATION_BASELINES.exists():
        raise SystemExit(
            "✗ Segmentation baselines not found. Run `python scripts/calibrate_segmentation.py` first."
        )
    return json.loads(SEGMENTATION_BASELINES.read_text(encoding="utf-8"))


def _iter_fixture_images(path: Path) -> Iterable[tuple[str, "cv2.typing.MatLike"]]:
    for img_path in sorted(path.glob("*.png")):
        image = cv2.imread(str(img_path), cv2.IMREAD_COLOR)
        if image is not None:
            yield img_path.name, image


def analyze_fixtures(fixtures_path: Path) -> dict[str, float]:
    baselines = _load_segmentation_baselines()
    segmenter_cache: dict[str, ImageSegmenter] = {}
    analyzer = PatternAnalyzer()

    symmetry_scores: list[float] = []
    fft_strengths: list[float] = []
    fft_counts: list[int] = []

    for image_name, image in _iter_fixture_images(fixtures_path):
        baseline = baselines.get(image_name)
        if baseline is None:
            continue

        params = baseline.get("felzenszwalb_params", {})
        options = SegmentationOptions(**params) if params else None
        segmenter = segmenter_cache.setdefault(image_name, ImageSegmenter(options=options))

        regions = segmenter.segment(image)
        descriptors = analyzer.analyze(image, regions)

        for descriptor in descriptors.values():
            symmetries = descriptor.get("symmetries", {})
            if symmetries:
                symmetry_scores.extend(symmetries.values())

            periods = descriptor.get("periods", [])
            fft_counts.append(len(periods))
            if periods:
                fft_strengths.extend(period[2] for period in periods)

    if not symmetry_scores:
        raise SystemExit("✗ No symmetry scores produced; verify fixtures and segmentation baselines.")

    if not fft_strengths:
        raise SystemExit("✗ No FFT peaks detected; ensure PatternAnalyzer FFT is enabled.")

    symmetry_threshold = float(np.percentile(symmetry_scores, 75))
    fft_strength_threshold = float(np.percentile(fft_strengths, 75))
    fft_peak_median = float(median(fft_counts)) if fft_counts else 0.0

    return {
        "symmetry_threshold": symmetry_threshold,
        "fft_strength_threshold": fft_strength_threshold,
        "fft_peak_median": fft_peak_median,
    }


def main(args: list[str]) -> int:
    fixtures_path = Path(args[0]) if args else FIXTURE_DIR
    if not fixtures_path.exists():
        print(f"✗ Fixture directory not found: {fixtures_path}")
        return 1

    recommendations = analyze_fixtures(fixtures_path)

    print("Pattern threshold recommendations:")
    print(f"  symmetry_threshold      ≈ {recommendations['symmetry_threshold']:.2f}")
    print(f"  fft_strength_threshold  ≈ {recommendations['fft_strength_threshold']:.2f}")
    print(f"  fft_peak_median         ≈ {recommendations['fft_peak_median']:.0f}")

    if OUTPUT_JSON.parent.exists():
        OUTPUT_JSON.write_text(json.dumps(recommendations, indent=2), encoding="utf-8")
        print(f"✓ Wrote {OUTPUT_JSON}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
