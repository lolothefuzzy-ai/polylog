"""Segmentation primitives for the INT-014 detection pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

try:  # pragma: no cover - import guarded to keep optional dependency
    import cv2  # type: ignore
except ImportError:  # pragma: no cover - fallback path for environments without OpenCV
    cv2 = None  # type: ignore

try:  # pragma: no cover - optional dependency guard
    import numpy as np
except ImportError:  # pragma: no cover - fallback path for environments without NumPy
    np = None  # type: ignore

try:  # pragma: no cover - optional dependency guard
    from skimage.segmentation import felzenszwalb
except ImportError:  # pragma: no cover
    felzenszwalb = None  # type: ignore


@dataclass(slots=True)
class SegmentationOptions:
    """Configurable segmentation parameters."""

    cluster_count: int = 6
    min_region_pixels: int = 250
    kmeans_attempts: int = 3
    use_felzenszwalb: bool = True
    felzenszwalb_scale: float = 100.0
    felzenszwalb_sigma: float = 0.8
    felzenszwalb_min_size: int = 150
    auto_tune_min_region: bool = True
    min_region_ratio: float = 0.005


@dataclass(slots=True)
class SegmentedRegion:
    """Structured metadata describing a segmented region."""

    label: int
    bbox: tuple[int, int, int, int]
    area: int
    center: tuple[float, float]
    color_mean: tuple[float, float, float]
    mask: Any  # numpy.ndarray when available


class ImageSegmenter:
    """Partition images into homogeneous regions using K-means + CC labeling."""

    __all__ = ["ImageSegmenter", "SegmentationOptions", "SegmentedRegion"]

    def __init__(self, *, options: SegmentationOptions | None = None) -> None:
        self.options = options or SegmentationOptions()
        self._last_array: Optional[Any] = None

    def segment(self, image: Any) -> list[dict[str, Any]]:
        """Run segmentation and return region dictionaries.

        The return shape mirrors the structure defined in the detection spec so
        downstream pattern analysis can operate without changes. When OpenCV or
        NumPy are unavailable, the method falls back to an empty result instead
        of raising, allowing environments without native deps to continue running.
        """

        array = self._coerce_to_array(image)
        if array is None or np is None:
            self._last_array = None
            return []

        tuned_min_region, tuned_felz_min = self._resolve_thresholds(array)

        if self.options.use_felzenszwalb and felzenszwalb is not None:
            regions = self._segment_with_felzenszwalb(array, tuned_min_region, tuned_felz_min)
            if regions:
                self._last_array = array
                return regions

        lab = cv2.cvtColor(array, cv2.COLOR_BGR2LAB)
        flat = lab.reshape((-1, 3)).astype(np.float32)

        cluster_count = max(1, min(self.options.cluster_count, flat.shape[0]))
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)

        _compactness, labels, centers = cv2.kmeans(
            flat,
            cluster_count,
            None,
            criteria,
            self.options.kmeans_attempts,
            cv2.KMEANS_PP_CENTERS,
        )

        label_image = labels.reshape(array.shape[:2]).astype(np.int32)
        regions: list[dict[str, Any]] = []
        current_label = 0

        for cluster_idx in range(cluster_count):
            cluster_mask = label_image == cluster_idx
            if int(cluster_mask.sum()) < tuned_min_region:
                continue

            num_labels, component_image = cv2.connectedComponents(cluster_mask.astype(np.uint8))
            for component_idx in range(1, num_labels):  # skip background (0)
                component_mask = component_image == component_idx
                area = int(component_mask.sum())
                if area < tuned_min_region:
                    continue

                ys, xs = np.nonzero(component_mask)
                y_min, y_max = int(ys.min()), int(ys.max())
                x_min, x_max = int(xs.min()), int(xs.max())

                bbox = (x_min, y_min, x_max, y_max)
                center = ((x_min + x_max) / 2.0, (y_min + y_max) / 2.0)
                color_mean = tuple(map(float, array[component_mask].mean(axis=0)))  # B, G, R means

                regions.append(
                    {
                        "label": current_label,
                        "bbox": bbox,
                        "center": center,
                        "area": area,
                        "color_mean": color_mean,
                        "mask": component_mask,
                    }
                )
                current_label += 1

        self._last_array = array
        return regions

    def _segment_with_felzenszwalb(
        self,
        array: Any,
        min_region_pixels: int,
        felzenszwalb_min_size: int,
    ) -> list[dict[str, Any]]:
        if felzenszwalb is None or np is None:
            return []

        float_img = array.astype(np.float32) / 255.0
        labels = felzenszwalb(
            float_img,
            scale=self.options.felzenszwalb_scale,
            sigma=self.options.felzenszwalb_sigma,
            min_size=felzenszwalb_min_size,
        )

        regions: list[dict[str, Any]] = []
        unique_labels = np.unique(labels)
        current_label = 0

        for felz_label in unique_labels:
            mask = labels == felz_label
            area = int(mask.sum())
            if area < min_region_pixels:
                continue

            ys, xs = np.nonzero(mask)
            y_min, y_max = int(ys.min()), int(ys.max())
            x_min, x_max = int(xs.min()), int(xs.max())

            bbox = (x_min, y_min, x_max, y_max)
            center = ((x_min + x_max) / 2.0, (y_min + y_max) / 2.0)
            color_mean = tuple(map(float, array[mask].mean(axis=0)))

            regions.append(
                {
                    "label": current_label,
                    "bbox": bbox,
                    "center": center,
                    "area": area,
                    "color_mean": color_mean,
                    "mask": mask,
                }
            )
            current_label += 1

        return regions

    def _resolve_thresholds(self, array: Any) -> tuple[int, int]:
        """Derive tuned thresholds for the current image."""

        base_min_region = self.options.min_region_pixels
        base_felz_min = self.options.felzenszwalb_min_size

        if not self.options.auto_tune_min_region or np is None:
            return base_min_region, base_felz_min

        height, width = array.shape[:2]
        pixel_count = max(int(height * width), 1)
        dynamic_min = max(int(pixel_count * self.options.min_region_ratio), 1)

        tuned_min = dynamic_min if dynamic_min < base_min_region else base_min_region
        tuned_felz = dynamic_min if dynamic_min < base_felz_min else base_felz_min

        return tuned_min, tuned_felz

    def _coerce_to_array(self, image: Any) -> Optional[Any]:
        """Convert supported inputs into a NumPy array."""

        if np is None:
            return None

        if isinstance(image, str):
            if cv2 is None:
                return None
            loaded = cv2.imread(image, cv2.IMREAD_COLOR)
            return loaded

        if "numpy" in type(image).__module__:
            return image

        return None

    @property
    def last_array(self) -> Optional[Any]:
        """Expose the last processed NumPy image."""

        return self._last_array
