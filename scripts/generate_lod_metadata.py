"""Utility to scaffold lod_metadata.json with placeholder structure."""
from __future__ import annotations

from pathlib import Path
from typing import Dict

import json

CATALOG_PATH = Path("catalogs/lod_metadata.json")


def generate_lod_metadata() -> Dict[str, object]:
    polyforms: Dict[str, Dict[str, object]] = {
        "tetrahedron": {
            "symbol": "Ω₁",
            "levels": [
                {
                    "level": 1,
                    "name": "symbol_only",
                    "data": "Ω₁",
                    "memory_bytes": 12,
                    "load_time_ms": 0.1,
                },
                {
                    "level": 2,
                    "name": "metadata",
                    "includes": ["o_value", "i_value", "symmetry_group"],
                    "memory_bytes": 512,
                    "load_time_ms": 0.9,
                    "percentiles": {"p50": 0.7, "p95": 0.9, "p99": 1.5},
                },
                {
                    "level": 3,
                    "name": "geometry_bbox",
                    "includes": ["vertices", "bounding_box"],
                    "memory_bytes": 2048,
                    "load_time_ms": 5.5,
                    "percentiles": {"p50": 4.8, "p95": 5.5, "p99": 6.1},
                },
                {
                    "level": 4,
                    "name": "full_geometry",
                    "includes": ["vertices", "edges", "faces", "attachment_points"],
                    "memory_bytes": 10240,
                    "load_time_ms": 18.0,
                    "percentiles": {"p50": 17.0, "p95": 18.0, "p99": 19.5},
                },
            ],
            "decompression_hints": {
                "lazy_eval": True,
                "cache_priority": "high",
                "preload_on_focus": True,
            },
        }
    }

    catalog: Dict[str, object] = {
        "type": "lod_metadata",
        "version": "0.1.0",
        "polyforms": polyforms,
        "metadata": {
            "generation_notes": "Populate via empirical LOD profiling script.",
        },
    }
    return catalog


def main() -> None:
    CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    catalog = generate_lod_metadata()
    CATALOG_PATH.write_text(json.dumps(catalog, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
