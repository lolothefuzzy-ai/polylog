"""Validate detection image inputs and generate synthetic fixtures (INT-014 P1).

This utility is intended for pre-integration bring-up. It verifies that real
image assets satisfy the detection pipeline's expectations and synthesises a
small curated sample set for deterministic regression tests.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, cast

try:
    import cv2  # type: ignore
except ImportError as exc:  # pragma: no cover - guard optional dependency
    cv2 = None  # type: ignore
    _cv2_error = exc
else:
    _cv2_error = None

try:
    import numpy as np
except ImportError as exc:  # pragma: no cover - guard optional dependency
    np = None  # type: ignore
    _np_error = exc
else:
    _np_error = None

FIXTURE_ROOT = Path("tests/fixtures/images")

__all__ = ["validate_image_source", "create_curated_fixtures", "FIXTURE_ROOT"]


def validate_image_source(image_path: Path) -> Dict[str, object]:
    """Check that an image can be consumed by the detection pipeline."""

    if cv2 is None or np is None:
        return {
            "valid": False,
            "error": "Required dependencies missing",
            "warnings": _dependency_warnings(),
        }

    img = cv2.imread(str(image_path))
    if img is None:
        return {"valid": False, "error": "Failed to load image", "warnings": []}

    height, width = img.shape[:2]
    size_mb = float(img.nbytes) / 1024**2

    report: Dict[str, object] = {
        "valid": True,
        "shape": tuple(int(dim) for dim in img.shape),
        "dtype": str(img.dtype),
        "size_mb": size_mb,
        "warnings": cast(List[str], []),
    }

    warnings = report["warnings"]

    if size_mb > 500:
        warnings.append(f"Large image: {size_mb:.1f} MB (spec: <500 MB)")

    if max(height, width) > 4096:
        warnings.append(
            f"High-resolution input {width}x{height}; consider downsampling to 1024x1024"
        )

    if img.dtype != np.uint8:
        warnings.append(f"Non-uint8 dtype detected: {img.dtype}")

    return report


def create_curated_fixtures() -> Path:
    """Generate a deterministic fixture suite for segmentation tests."""

    if cv2 is None or np is None:
        raise RuntimeError("OpenCV and NumPy are required to create fixtures")

    FIXTURE_ROOT.mkdir(parents=True, exist_ok=True)

    fixtures: Dict[str, object] = {
        "simple_triangle": np.zeros((512, 512, 3), dtype=np.uint8),
        "grid_pattern": np.zeros((1024, 1024, 3), dtype=np.uint8),
        "noisy_polyform": np.random.default_rng(42).integers(
            low=0, high=255, size=(800, 800, 3), dtype=np.uint8
        ),
    }

    triangle = fixtures["simple_triangle"]
    cv2.fillPoly(
        triangle,
        [np.array([[100, 400], [256, 100], [412, 400]], dtype=np.int32)],
        (255, 255, 255),
    )

    grid = fixtures["grid_pattern"]
    step = 64
    for x in range(0, grid.shape[1], step):
        cv2.line(grid, (x, 0), (x, grid.shape[0] - 1), (255, 255, 255), 2)
    for y in range(0, grid.shape[0], step):
        cv2.line(grid, (0, y), (grid.shape[1] - 1, y), (255, 255, 255), 2)

    for name, img in fixtures.items():
        path = FIXTURE_ROOT / f"{name}.png"
        cv2.imwrite(str(path), img)

    return FIXTURE_ROOT


def _dependency_warnings() -> List[str]:
    warnings: List[str] = []
    if _cv2_error is not None:
        warnings.append(f"OpenCV unavailable: {_cv2_error}")
    if _np_error is not None:
        warnings.append(f"NumPy unavailable: {_np_error}")
    return warnings


def _print_heading(title: str) -> None:
    print(f"\n=== {title} ===")


def main() -> int:
    if cv2 is None or np is None:
        _print_heading("Dependency Check")
        for warning in _dependency_warnings():
            print(f"✗ {warning}")
        return 1

    _print_heading("Dependency Check")
    print("✓ OpenCV + NumPy available")

    _print_heading("Fixture Generation")
    fixtures_dir = create_curated_fixtures()
    print(f"✓ Created fixtures in {fixtures_dir}")

    _print_heading("Fixture Validation")
    for img_path in sorted(fixtures_dir.glob("*.png")):
        report = validate_image_source(img_path)
        summary = (
            f"valid={report['valid']} shape={report.get('shape')} size={report.get('size_mb'):.2f} MB"
        )
        print(f"  {img_path.name}: {summary}")
        for warning in report.get("warnings", []):
            print(f"    ⚠ {warning}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
