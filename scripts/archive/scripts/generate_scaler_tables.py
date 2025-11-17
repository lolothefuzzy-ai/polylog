"""Utility to scaffold scaler_tables.json with placeholder structure."""
from __future__ import annotations

from pathlib import Path
from typing import Dict

import json

CATALOG_PATH = Path("catalogs/scaler_tables.json")


def generate_scaler_tables() -> Dict[str, object]:
    polyforms: Dict[str, Dict[str, object]] = {
        "tetrahedron": {
            "symbol": "Ω₁",
            "composition": {"triangle": 4},
            "base_scale": 1.0,
            "size_variants": [0.5, 0.75, 1.0, 1.25, 1.5],
            "o_value": 1,
            "i_value": 7,
            "symmetry": {"point_group": "T", "order": 12},
            "scaler_factors": {
                "vertices_scale": 1.0,
                "edge_scale": 1.0,
                "angle_scale": 1.0,
            },
            "attachment_scaler_ranges": {
                "triangle_to_triangle": {
                    "min_scale": 0.8,
                    "max_scale": 1.2,
                    "preferred_scale": 1.0,
                }
            },
            "node_swapping_potential": 1.0,
        },
        "cube": {
            "symbol": "Ω₂",
            "composition": {"square": 6},
            "base_scale": 1.0,
            "size_variants": [0.5, 1.0, 1.5, 2.0],
            "o_value": 1,
            "i_value": 24,
            "symmetry": {"point_group": "O", "order": 24},
            "scaler_factors": {
                "vertices_scale": 1.0,
                "edge_scale": 1.0,
                "angle_scale": 1.0,
            },
            "attachment_scaler_ranges": {
                "square_to_square": {
                    "min_scale": 0.9,
                    "max_scale": 1.3,
                    "preferred_scale": 1.0,
                }
            },
            "node_swapping_potential": 1.0,
        },
    }

    catalog: Dict[str, object] = {
        "type": "scaler_library",
        "version": "0.1.0",
        "polyforms": polyforms,
        "metadata": {
            "generation_notes": "Populate via cascading O/I computation script.",
        },
    }
    return catalog


def main() -> None:
    CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    catalog = generate_scaler_tables()
    CATALOG_PATH.write_text(json.dumps(catalog, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
