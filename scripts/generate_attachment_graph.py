"""Utility to scaffold attachment_graph.json with placeholder structure."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

import json

CATALOG_PATH = Path("catalogs/attachment_graph.json")


def generate_attachment_graph() -> Dict[str, object]:
    edges: List[Dict[str, object]] = [
        {
            "id": "tri_tri_midpoint",
            "source_polygon": "triangle",
            "target_polygon": "triangle",
            "source_edge_index": 0,
            "target_edge_index": 0,
            "edge_length": 1.0,
            "fold_angle_range": {"min": 0, "max": 180, "preferred": 70.5},
            "alignment_type": "midpoint_to_midpoint",
            "collision_constraints": "planar_no_overlap",
            "stability_score": 0.95,
        },
        {
            "id": "tri_square_edge_match",
            "source_polygon": "triangle",
            "target_polygon": "square",
            "source_edge_index": 1,
            "target_edge_index": 2,
            "edge_length": "compatible",
            "fold_angle_range": {"min": 15, "max": 135, "preferred": 60.0},
            "alignment_type": "partial_edge_overlap",
            "collision_constraints": "3d_space_check",
            "stability_score": 0.78,
        },
    ]

    forbidden: List[Dict[str, object]] = [
        {
            "source": "triangle",
            "target": "heptagon",
            "reason": "edge_length_mismatch",
        }
    ]

    edge_buckets: Dict[str, List[Tuple[str, str]]] = {
        "1.0": [("triangle", "triangle")],
        "compatible": [("triangle", "square")],
    }

    catalog: Dict[str, object] = {
        "type": "attachment_graph",
        "version": "0.1.0",
        "edges": edges,
        "forbidden_connections": forbidden,
        "metadata": {
            "edge_length_buckets": edge_buckets,
            "generation_notes": "Populate via parallel enumeration script.",
        },
    }
    return catalog


def main() -> None:
    CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    catalog = generate_attachment_graph()
    CATALOG_PATH.write_text(json.dumps(catalog, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
