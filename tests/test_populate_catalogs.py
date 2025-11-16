"""Regression tests for catalog population helper (INT-009)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.populate_catalogs import (
    STABLE_POLYFORMS,
    compute_checksum,
    populate_all,
)


def _write_polyform(path: Path, *, uuid: str = "1234567890abcdef1234567890abcdef") -> None:
    entry = {
        "uuid": uuid,
        "composition": "AAAB",
        "O": 1,
        "I": 3,
        "unicode_char": "Ω",
        "fold_angles": [12.5],
        "stability": 0.92,
    }
    path.write_text(json.dumps(entry) + "\n", encoding="utf-8")


def test_populate_all_generates_catalogs(tmp_path: Path) -> None:
    source_path = tmp_path / STABLE_POLYFORMS.name
    catalog_dir = tmp_path / "catalogs-out"
    _write_polyform(source_path)

    outputs = populate_all(source=source_path, catalog_dir=catalog_dir, workers=1)

    assert set(outputs.keys()) == {"attachment_graph", "scaler_tables", "metadata"}

    attachment_path = outputs["attachment_graph"]
    scaler_path = outputs["scaler_tables"]
    metadata_path = outputs["metadata"]

    for path in (attachment_path, scaler_path, metadata_path):
        assert path.exists(), f"Expected artifact missing: {path}"

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert metadata["source_file"] == source_path.name
    assert metadata["source_checksum"] == compute_checksum(source_path)

    artifacts = metadata["artifacts"]
    assert set(artifacts.keys()) == {"attachment_graph", "scaler_tables", "metadata"}

    for name, info in artifacts.items():
        artifact_path = outputs[name]
        assert info["path"].endswith(str(artifact_path.relative_to(catalog_dir)))
        assert info["checksum"] == compute_checksum(artifact_path)

    attachment_payload = json.loads(attachment_path.read_text(encoding="utf-8"))
    assert attachment_payload["pairs"]

    scaler_payload = json.loads(scaler_path.read_text(encoding="utf-8"))
    assert scaler_payload


def test_populate_all_schema_validation_failure(tmp_path: Path) -> None:
    source_path = tmp_path / STABLE_POLYFORMS.name
    catalog_dir = tmp_path / "catalogs-out"

    # Missing required fields (uuid/composition) → schema violation
    source_path.write_text(json.dumps({"O": 1}) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Schema validation failed"):
        populate_all(source=source_path, catalog_dir=catalog_dir, workers=1)
