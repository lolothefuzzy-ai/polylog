"""Utility to extract geometry descriptors into geometry_catalog.json."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

import json
import math

from polylog6.storage import SymbolRegistry

CATALOG_PATH = Path("catalogs/geometry_catalog.json")


def _regular_polygon_vertices(sides: int, radius: float = 1.0) -> List[Tuple[float, float, float]]:
    vertices: List[Tuple[float, float, float]] = []
    for i in range(sides):
        angle = (2 * math.pi * i) / sides
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        vertices.append((round(x, 6), round(y, 6), 0.0))
    return vertices


def _walk_edges(count: int) -> List[Tuple[int, int]]:
    return [(index, (index + 1) % count) for index in range(count)]


def _bounding_box(vertices: List[Tuple[float, float, float]]) -> Dict[str, Tuple[float, float, float]]:
    xs = [vertex[0] for vertex in vertices]
    ys = [vertex[1] for vertex in vertices]
    zs = [vertex[2] for vertex in vertices]
    return {
        "min": (min(xs), min(ys), min(zs)),
        "max": (max(xs), max(ys), max(zs)),
    }


def _primitive_entries(registry: SymbolRegistry) -> Dict[str, Dict[str, object]]:
    entries: Dict[str, Dict[str, object]] = {}
    for sides, symbol in registry.iter_primitives():
        name = {
            3: "triangle",
            4: "square",
            5: "pentagon",
            6: "hexagon",
            7: "heptagon",
            8: "octagon",
            9: "nonagon",
            10: "decagon",
            11: "hendecagon",
            12: "dodecagon",
        }.get(sides, f"{sides}-gon")
        vertices = _regular_polygon_vertices(sides)
        entries[name] = {
            "sides": sides,
            "symbol": symbol,
            "vertices": vertices,
            "edges": _walk_edges(sides),
            "bounding_box": _bounding_box(vertices),
            "s_value": sides,
        }
    return entries


def generate_geometry_catalog() -> Dict[str, object]:
    registry = SymbolRegistry()
    primitives = _primitive_entries(registry)

    catalog = {
        "type": "geometry_library",
        "version": "0.1.0",
        "primitives": primitives,
        "polyhedra": {},
    }
    return catalog


def main() -> None:
    CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    catalog = generate_geometry_catalog()
    CATALOG_PATH.write_text(json.dumps(catalog, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
