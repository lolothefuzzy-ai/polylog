"""Integration harness for exercising the detection pipeline on real images.

Run after generating fixtures via ``scripts/validate_detection_input.py``. The
script is intentionally outside pytest so we can iterate quickly during bring-up
without polluting unit test output.
"""

from __future__ import annotations

from pathlib import Path
import json
import sys
from typing import Any, Callable

import cv2  # type: ignore

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from polylog6.detection import DetectionTask, ImageDetectionService  # noqa: E402
from polylog6.detection.assets import default_assets_dir  # noqa: E402
from polylog6.monitoring import DetectionTelemetryBridge, monitoring_enabled  # noqa: E402

FIXTURES_DIR = Path("tests/fixtures/images")
SEGMENTATION_VIZ_DIR = Path("tests/fixtures/segmentation_snapshots")


def _print_heading(title: str) -> None:
    print(f"\n=== {title} ===")


def _emit_telemetry(payload: dict[str, Any]) -> None:
    print(f"[TELEMETRY] {payload}")


def _ensure_dirs() -> None:
    SEGMENTATION_VIZ_DIR.mkdir(parents=True, exist_ok=True)


def _visualise_segmentation(image, regions, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    if not regions:
        return

    viz = image.copy()
    for region in regions:
        bbox = region.get("bbox")
        if bbox is None:
            continue
        x_min, y_min, x_max, y_max = map(int, bbox)
        cv2.rectangle(viz, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)

    output_path = output_dir / "segmentation_overlay.png"
    cv2.imwrite(str(output_path), viz)


def run_detection_on_fixture(
    image_path: Path, *, emit_telemetry: Callable[[dict[str, Any]], None]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    print(f"\n>>> Processing {image_path.name}")
    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError(f"Could not load {image_path}")

    print(f"Image shape: {img.shape}, dtype: {img.dtype}")

    telemetry_emitter = emit_telemetry
    bridge: DetectionTelemetryBridge | None = None
    if monitoring_enabled():
        bridge = DetectionTelemetryBridge()
        telemetry_emitter = bridge.sink()

    service = ImageDetectionService(
        assets_dir=default_assets_dir(),
        expect_assets=False,
        telemetry_emitter=telemetry_emitter,
    )

    task = DetectionTask(image_path=str(image_path))
    result = service.analyze(task)

    print(f"Regions detected: {len(result['regions'])}")
    print(f"Candidates generated: {len(result['plan'].candidates)}")

    topology = result.get("topology", {})
    print(f"Topology backends: {topology.get('backends', [])}")
    hulls = topology.get("regions", {})
    print(f"Hull summaries: {len(hulls)} regions")

    _visualise_segmentation(img, result["regions"], SEGMENTATION_VIZ_DIR / image_path.stem)

    telemetry_snapshots = bridge.snapshots() if bridge is not None else []

    return result, telemetry_snapshots


def main() -> int:
    if not FIXTURES_DIR.exists():
        print("Fixtures missing. Run scripts/validate_detection_input.py first.")
        return 1

    _ensure_dirs()
    _print_heading("Real Image Detection Harness")

    failures: list[tuple[str, Exception]] = []
    telemetry_payloads: list[dict[str, Any]] = []
    telemetry_snapshots: list[dict[str, Any]] = []
    for img_path in sorted(FIXTURES_DIR.glob("*.png")):
        try:
            result, snapshots = run_detection_on_fixture(
                img_path,
                emit_telemetry=lambda payload, _telemetry=telemetry_payloads: _telemetry.append(
                    payload
                ),
            )
            if snapshots:
                telemetry_snapshots.extend([snap.to_dict() for snap in snapshots])
            print(f"✓ {img_path.name} succeeded")
        except Exception as exc:  # pragma: no cover - diagnostic harness
            failures.append((img_path.name, exc))
            print(f"✗ {img_path.name} failed: {exc}")

    if telemetry_payloads:
        print("Telemetry emitted:")
        for payload in telemetry_payloads:
            print(json.dumps(payload, indent=2))

    if telemetry_snapshots:
        print("Monitoring snapshots:")
        for snapshot in telemetry_snapshots:
            print(json.dumps(snapshot, indent=2))

    if failures:
        _print_heading("Summary")
        for name, exc in failures:
            print(f"  {name}: {exc}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
