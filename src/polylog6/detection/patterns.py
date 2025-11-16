"""Pattern analysis scaffolding for INT-014."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

try:  # pragma: no cover - optional dependency guard
    import cv2  # type: ignore
except ImportError:  # pragma: no cover - fallback path for environments without OpenCV
    cv2 = None  # type: ignore

try:  # pragma: no cover - optional dependency guard
    import numpy as np
except ImportError:  # pragma: no cover - fallback path for environments without NumPy
    np = None  # type: ignore


@dataclass(slots=True)
class PatternAnalysisOptions:
    """FFT/symmetry detector configuration."""

    enable_fft: bool = True
    symmetry_threshold: float = 0.85
    max_period_peaks: int = 12
    fft_strength_threshold: float = 0.0


PATTERN_THRESHOLD_PATH = Path("tests/fixtures/pattern_thresholds.json")


@lru_cache(maxsize=1)
def _load_threshold_recommendations(path: Path | None = None) -> dict[str, float]:
    target = path or PATTERN_THRESHOLD_PATH
    if not target.exists():
        return {}
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


class PatternAnalyzer:
    """Compute per-region descriptors used by downstream optimization."""

    def __init__(self, *, options: PatternAnalysisOptions | None = None) -> None:
        if options is None:
            options = PatternAnalysisOptions()
            recommendations = _load_threshold_recommendations()
            if recommendations:
                if "symmetry_threshold" in recommendations:
                    options.symmetry_threshold = float(recommendations["symmetry_threshold"])
                if "fft_strength_threshold" in recommendations:
                    options.fft_strength_threshold = float(recommendations["fft_strength_threshold"])
                if "fft_peak_median" in recommendations:
                    peaks = max(int(round(float(recommendations["fft_peak_median"]))), 1)
                    options.max_period_peaks = peaks
        self.options = options

    def analyze(self, image: Any, regions: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
        """Return descriptor map indexed by region label."""

        array = self._coerce_to_array(image)
        if array is None or cv2 is None or np is None:
            return {}

        descriptors: dict[int, dict[str, Any]] = {}
        gray = cv2.cvtColor(array, cv2.COLOR_BGR2GRAY)

        for region in regions:
            mask = region.get("mask")
            label = region.get("label")
            if mask is None or label is None:
                continue

            y_min, y_max = int(region["bbox"][1]), int(region["bbox"][3])
            x_min, x_max = int(region["bbox"][0]), int(region["bbox"][2])

            region_gray = gray[y_min:y_max + 1, x_min:x_max + 1]
            region_mask = mask[y_min:y_max + 1, x_min:x_max + 1]

            descriptor = {
                "periods": self._detect_periods(region_gray, region_mask),
                "symmetries": self._detect_symmetries(region_gray, region_mask),
                "edge_complexity": self._estimate_edge_complexity(region_gray, region_mask),
            }
            descriptors[label] = descriptor

        return descriptors

    def _detect_periods(self, region_gray: Any, mask: Any) -> list[tuple[float, float, float]]:
        """Infer repeating patterns via FFT magnitude peaks."""

        if not self.options.enable_fft or np is None:
            return []

        masked = np.where(mask, region_gray, 0)
        f_transform = np.fft.fft2(masked)
        f_shift = np.fft.fftshift(f_transform)
        magnitude = np.abs(f_shift)

        cy, cx = magnitude.shape[0] // 2, magnitude.shape[1] // 2
        magnitude[cy, cx] = 0  # remove DC component

        flat = magnitude.flatten()
        if flat.size == 0:
            return []

        top_count = min(max(self.options.max_period_peaks, 1), flat.size)
        top_indices = np.argpartition(flat, -top_count)[-top_count:]
        periods: list[tuple[float, float, float]] = []
        height, width = region_gray.shape

        for idx in top_indices:
            y, x = np.unravel_index(idx, magnitude.shape)
            period_x = width / max(abs(x - cx), 1)
            period_y = height / max(abs(y - cy), 1)
            strength = float(flat[idx])
            periods.append((period_x, period_y, strength))

        periods.sort(key=lambda item: item[2], reverse=True)
        return self._filter_periods(periods)

    def _detect_symmetries(self, region_gray: Any, mask: Any) -> dict[str, float]:
        """Detect mirror/rotational symmetry scores."""

        if cv2 is None or np is None:
            return {}

        threshold = self.options.symmetry_threshold
        masked_pixels = np.count_nonzero(mask)
        if masked_pixels == 0:
            return {}

        symmetries: dict[str, float] = {}

        def _score(candidate: Any) -> float:
            diff = np.where(mask, region_gray - candidate, 0)
            match_ratio = 1.0 - (np.abs(diff).sum() / (masked_pixels * 255.0))
            return float(max(0.0, min(1.0, match_ratio)))

        h_flip = cv2.flip(region_gray, 1)
        score = _score(h_flip)
        if score >= threshold:
            symmetries["horizontal"] = score

        v_flip = cv2.flip(region_gray, 0)
        score = _score(v_flip)
        if score >= threshold:
            symmetries["vertical"] = score

        rot90 = cv2.rotate(region_gray, cv2.ROTATE_90_CLOCKWISE)
        if rot90.shape != region_gray.shape:
            rot90 = cv2.resize(rot90, (region_gray.shape[1], region_gray.shape[0]))
        score = _score(rot90)
        if score >= threshold:
            symmetries["rotational_90"] = score

        rot180 = cv2.rotate(region_gray, cv2.ROTATE_180)
        score = _score(rot180)
        if score >= threshold:
            symmetries["rotational_180"] = score

        return symmetries

    def _estimate_edge_complexity(self, region_gray: Any, mask: Any) -> int:
        """Run a lightweight edge detector to approximate complexity."""

        if cv2 is None or np is None:
            return 0

        edges = cv2.Canny(region_gray, 100, 200)
        return int(np.count_nonzero(np.logical_and(edges > 0, mask)))

    def _coerce_to_array(self, image: Any) -> Optional[Any]:
        """Convert supported inputs into a NumPy/BGR array."""

        if np is None:
            return None

        if "numpy" in type(image).__module__:
            return image

        if isinstance(image, str) and cv2 is not None:
            return cv2.imread(image, cv2.IMREAD_COLOR)

        return None

    def _filter_periods(
        self, periods: list[tuple[float, float, float]]
    ) -> list[tuple[float, float, float]]:
        threshold = self.options.fft_strength_threshold
        if threshold > 0.0:
            periods = [period for period in periods if period[2] >= threshold]
        max_peaks = max(self.options.max_period_peaks, 0)
        return periods[:max_peaks] if max_peaks else []
