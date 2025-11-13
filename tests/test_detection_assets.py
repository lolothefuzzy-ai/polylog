from pathlib import Path

import json

from polylog6.detection.assets import DetectionAssets


def _write_jsonl(path: Path, records: list[dict]):
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record) + "\n")


def test_detection_assets_loads_minimal_fixture(tmp_path: Path):
    assets_dir = tmp_path / "assets"
    assets_dir.mkdir()

    _write_jsonl(
        assets_dir / "polyforms.jsonl",
        [{"uuid": "test-001", "composition": "AAA"}],
    )
    (assets_dir / "unicode_scalers.json").write_text(
        json.dumps({"tier0": ["symbol-a"]}),
        encoding="utf-8",
    )
    (assets_dir / "segmentation_config.yaml").write_text(
        "cluster_count: 6\nmin_region_pixels: 200\n",
        encoding="utf-8",
    )

    assets = DetectionAssets(assets_dir)
    report = assets.report()

    assert report.polyform_count == 1
    assert report.segmentation_config["cluster_count"] == 6
    assert report.is_ready


def test_detection_assets_missing_files_record_errors(tmp_path: Path):
    assets_dir = tmp_path / "assets"
    assets_dir.mkdir()

    assets = DetectionAssets(assets_dir, expect_files=True)
    report = assets.report()

    assert not report.is_ready
    assert report.errors  # missing files recorded
