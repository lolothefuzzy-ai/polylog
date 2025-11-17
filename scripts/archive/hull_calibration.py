"""Calibrate convex-hull metrics across available topology backends.

This helper compares the primary topology backend (Trimesh / scikit-geometry /
NumPy fallback) against the guaranteed NumPy fallback implementation so that we
can quantify drift and capture regression fixtures for INT-014 Phase 4.

Usage
-----
    $ PYTHONPATH=src python scripts/hull_calibration.py \
        --output tests/fixtures/hull_metrics.json

The script emits a JSON summary containing per-sample measurements together with
aggregate statistics and deviation percentages. A companion regression test
(`tests/test_hull_metrics_regression.py`) ensures the primary backend remains
within tolerance over time.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean
from typing import Dict, Iterable, Mapping

from polylog6.detection.candidate_generation import CandidateGenerator
from polylog6.detection.topology import HullSummary, TopologyDetector

# Synthetic vertex samples (bounded, deterministic) used for calibration. Each
# entry is a list of 3D points representing a simple polyform footprint.
SAMPLE_VERTICES: Mapping[str, list[list[float]]] = {
    "unit_cube": [
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [1.0, 1.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
        [1.0, 0.0, 1.0],
        [1.0, 1.0, 1.0],
        [0.0, 1.0, 1.0],
    ],
    "rect_prism": [
        [0.0, 0.0, 0.0],
        [2.5, 0.0, 0.0],
        [2.5, 1.5, 0.0],
        [0.0, 1.5, 0.0],
        [0.0, 0.0, 0.5],
        [2.5, 0.0, 0.5],
        [2.5, 1.5, 0.5],
        [0.0, 1.5, 0.5],
    ],
    # Thin plate with a slight extrusion to force non-zero thickness.
    "thin_plate": [
        [0.0, 0.0, 0.0],
        [3.0, 0.0, 0.0],
        [3.0, 2.0, 0.0],
        [0.0, 2.0, 0.0],
        [0.0, 0.0, 0.1],
        [3.0, 0.0, 0.1],
        [3.0, 2.0, 0.1],
        [0.0, 2.0, 0.1],
    ],
}

OUTPUT_DEFAULT = Path("tests/fixtures/hull_metrics.json")
FALLBACK_LABEL = "numpy"

def _metrics_from_summary(summary: HullSummary) -> Dict[str, float]:
    """Reuse candidate generator heuristics to derive hull metrics."""

    generator = CandidateGenerator(polyform_library=[])
    return generator._compute_hull_metrics(summary)  # type: ignore[attr-defined]

def _summarize(summary: HullSummary) -> Dict[str, float | int | None]:
    metrics = _metrics_from_summary(summary)
    data: Dict[str, float | int | None] = {
        "method": summary.method,
        "vertex_count": summary.vertex_count,
        "face_count": summary.face_count,
        "volume": summary.volume,
        "surface_area": summary.surface_area,
    }
    data.update({
        "planar_area": metrics.get("planar_area"),
        "thickness": metrics.get("thickness"),
        "compactness": metrics.get("compactness"),
        "density": metrics.get("density"),
    })
    return data

def _percent_deviation(baseline: float | None, candidate: float | None) -> float:
    if baseline is None:
        return 0.0 if (candidate is None or candidate == 0.0) else 100.0
    if baseline == 0.0:
        return 0.0 if candidate in (None, 0.0) else 100.0
    candidate = candidate or 0.0
    return abs(candidate - baseline) / abs(baseline) * 100.0

def _aggregate_metrics(samples: Mapping[str, Dict[str, Dict[str, float | int | None]]]) -> Dict[str, Dict[str, float]]:
    primary_accumulator: Dict[str, list[float]] = {}
    fallback_accumulator: Dict[str, list[float]] = {}
    deviation_accumulator: Dict[str, list[float]] = {}

    for sample in samples.values():
        primary = sample["primary"]
        fallback = sample["fallback"]
        deviations = sample["deviation_pct"]
        for key, value in primary.items():
            if isinstance(value, (int, float)) and key not in {"face_count", "vertex_count"}:
                primary_accumulator.setdefault(key, []).append(float(value))
        for key, value in fallback.items():
            if isinstance(value, (int, float)) and key not in {"face_count", "vertex_count"}:
                fallback_accumulator.setdefault(key, []).append(float(value))
        for key, value in deviations.items():
            deviation_accumulator.setdefault(key, []).append(float(value))

    def _averages(acc: Dict[str, list[float]]) -> Dict[str, float]:
        return {key: mean(values) for key, values in acc.items() if values}

    def _maxima(acc: Dict[str, list[float]]) -> Dict[str, float]:
        return {key: max(values) for key, values in acc.items() if values}

    return {
        "primary": _averages(primary_accumulator),
        "fallback": _averages(fallback_accumulator),
        "max_deviation_pct": _maxima(deviation_accumulator),
    }

def calibrate_hulls(output: Path) -> Dict[str, object]:
    detector = TopologyDetector()
    fallback_detector = TopologyDetector(sg_module=False, trimesh_module=False)

    results: Dict[str, Dict[str, Dict[str, float | int | None]]] = {}

    for name, vertices in SAMPLE_VERTICES.items():
        primary_summary = detector.compute_convex_hull(vertices)
        fallback_summary = fallback_detector.compute_convex_hull(vertices)

        primary_data = _summarize(primary_summary)
        fallback_data = _summarize(fallback_summary)

        deviations: Dict[str, float] = {}
        for key in ("volume", "planar_area", "thickness", "compactness", "density"):
            deviations[key] = _percent_deviation(
                primary_data.get(key),
                fallback_data.get(key),
            )

        results[name] = {
            "primary": primary_data,
            "fallback": fallback_data,
            "deviation_pct": deviations,
        }

    payload = {
        "primary_backend": detector.primary_backend,
        "fallback_backend": FALLBACK_LABEL,
        "samples": results,
    }
    payload.update(_aggregate_metrics(results))

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True))
    return payload

def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Calibrate hull metrics across topology backends")
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_DEFAULT,
        help="Path to write calibration JSON (default: tests/fixtures/hull_metrics.json)",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    payload = calibrate_hulls(args.output)
    primary = payload.get("primary_backend")
    fallback = payload.get("fallback_backend")
    max_dev = payload.get("max_deviation_pct", {})
    volume_dev = max_dev.get("volume", 0.0)
    print(f"✓ Hull calibration complete (primary={primary}, fallback={fallback}, max volume deviation={volume_dev:.2f}% )")
    print(f"  → Wrote {args.output}")
    return 0


if __name__ == "__main__":  # pragma: no cover - script entry point
    raise SystemExit(main())
