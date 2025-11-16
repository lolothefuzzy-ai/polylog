"""Smoke tests for catalog generator scaffolds."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CATALOG_DIR = PROJECT_ROOT / "catalogs"


def test_run_catalog_generators() -> None:
    result = subprocess.run(
        ["python", "scripts/run_catalog_generators.py"],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr

    for name in ["geometry_catalog.json", "attachment_graph.json", "scaler_tables.json", "lod_metadata.json"]:
        path = CATALOG_DIR / name
        assert path.exists()
        data = json.loads(path.read_text(encoding="utf-8"))
        assert "type" in data
        assert "version" in data
