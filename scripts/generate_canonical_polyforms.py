#!/usr/bin/env python3
"""Generate a canonical offline polyform catalog.

The script procedurally builds a diverse set of convex and star polyhedra using
``trimesh`` primitives so we can seed ``stable_polyforms.jsonl`` without network
access.  The resulting catalog (≈120 polyforms) is sufficient for INT-005 Tier 0
hydration and can later be expanded by merging external datasets with
``merge_polyform_catalogs.py``.
"""
from __future__ import annotations

import argparse
import json
import math
import uuid
from datetime import datetime, UTC
from pathlib import Path
from typing import Iterable

import numpy as np
import trimesh


def _platonic_mesh(kind: str) -> trimesh.Trimesh:
    kind = kind.lower()
    if kind == "tetrahedron":
        vertices = np.array(
            [
                [1.0, 1.0, 1.0],
                [1.0, -1.0, -1.0],
                [-1.0, 1.0, -1.0],
                [-1.0, -1.0, 1.0],
            ]
        )
        faces = np.array(
            [
                [0, 1, 2],
                [0, 3, 1],
                [0, 2, 3],
                [1, 3, 2],
            ]
        )
        return trimesh.Trimesh(vertices=vertices, faces=faces)

    if kind == "cube":
        return trimesh.creation.box(extents=(2.0, 2.0, 2.0))

    if kind == "octahedron":
        vertices = np.array(
            [
                [1.0, 0.0, 0.0],
                [-1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, -1.0, 0.0],
                [0.0, 0.0, 1.0],
                [0.0, 0.0, -1.0],
            ]
        )
        faces = np.array(
            [
                [0, 2, 4],
                [2, 1, 4],
                [1, 3, 4],
                [3, 0, 4],
                [2, 0, 5],
                [1, 2, 5],
                [3, 1, 5],
                [0, 3, 5],
            ]
        )
        return trimesh.Trimesh(vertices=vertices, faces=faces)

    if kind == "icosahedron":
        return trimesh.creation.icosahedron()

    if kind == "dodecahedron":
        ico = trimesh.creation.icosahedron()
        dual = _dual_mesh(ico)
        return dual

    raise ValueError(f"Unknown platonic solid '{kind}'")


def _dual_mesh(base: trimesh.Trimesh) -> trimesh.Trimesh:
    """Compute dual mesh via face centroids."""
    centroids = np.array([base.vertices[face].mean(axis=0) for face in base.faces])
    hull = trimesh.convex.convex_hull(centroids)
    return hull


class PolyformGenerator:
    """Procedurally generate canonical polyforms."""

    def __init__(self) -> None:
        self._polyforms: list[dict[str, object]] = []

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _metadata(self, family: str) -> dict[str, object]:
        return {
            "source": "procedural",
            "family": family,
            "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        }

    def _add_mesh(
        self,
        *,
        name: str,
        family: str,
        composition: str,
        mesh: trimesh.Trimesh,
        extra_metadata: dict[str, object] | None = None,
    ) -> None:
        mesh.remove_duplicate_faces()
        mesh.remove_unreferenced_vertices()

        metadata = self._metadata(family)
        if extra_metadata:
            metadata.update(extra_metadata)

        entry = {
            "uuid": str(uuid.uuid4()),
            "name": name,
            "family": family,
            "composition": composition,
            "O": 1,
            "I": 1,
            "vertices": mesh.vertices.tolist(),
            "faces": mesh.faces.tolist(),
            "edges": int(len(mesh.edges_unique)),
            "volume": float(mesh.volume if mesh.is_watertight else 0.0),
            "surface_area": float(mesh.area),
            "metadata": metadata,
        }
        self._polyforms.append(entry)
        print(f"  ✓ {name}")

    # ------------------------------------------------------------------
    # Families
    # ------------------------------------------------------------------
    def generate_platonic(self) -> None:
        print("Platonic solids…")
        self._add_mesh(
            name="Tetrahedron",
            family="Platonic",
            composition="4 triangles",
            mesh=_platonic_mesh("tetrahedron"),
        )
        self._add_mesh(
            name="Cube",
            family="Platonic",
            composition="6 squares",
            mesh=_platonic_mesh("cube"),
        )
        self._add_mesh(
            name="Octahedron",
            family="Platonic",
            composition="8 triangles",
            mesh=_platonic_mesh("octahedron"),
        )
        self._add_mesh(
            name="Dodecahedron",
            family="Platonic",
            composition="12 pentagons",
            mesh=_platonic_mesh("dodecahedron"),
        )
        self._add_mesh(
            name="Icosahedron",
            family="Platonic",
            composition="20 triangles",
            mesh=_platonic_mesh("icosahedron"),
        )

    def generate_truncated_archimedean(self) -> None:
        print("Archimedean truncations…")
        bases = [
            ("Tetrahedron", _platonic_mesh("tetrahedron")),
            ("Cube", _platonic_mesh("cube")),
            ("Octahedron", _platonic_mesh("octahedron")),
            ("Icosahedron", _platonic_mesh("icosahedron")),
        ]
        for base_name, base in bases:
            for trunc in (0.18, 0.28, 0.38):
                truncated = trimesh.creation.truncate_polyhedron(base, truncation=trunc)
                self._add_mesh(
                    name=f"Truncated {base_name} (τ={trunc:.2f})",
                    family="Archimedean",
                    composition="Truncated variant",
                    mesh=truncated,
                    extra_metadata={"truncation": trunc},
                )

    def generate_catalan(self) -> None:
        print("Catalan solids (hard-coded)…")
        # Rhombic dodecahedron via cube/octa dual (scaled for aesthetics)
        cube = trimesh.creation.box()
        dual_vertices, dual_faces = trimesh.polyhedron.dual(cube.vertices, cube.faces)
        rhombic = trimesh.Trimesh(vertices=dual_vertices * 1.2, faces=dual_faces)
        self._add_mesh(
            name="Rhombic Dodecahedron",
            family="Catalan",
            composition="12 rhombi",
            mesh=rhombic,
        )

        # Triakis tetrahedron (augment tetrahedron faces with pyramids)
        tet = trimesh.creation.tetrahedron()
        triakis = trimesh.creation.augment(tet, height=0.4)
        self._add_mesh(
            name="Triakis Tetrahedron",
            family="Catalan",
            composition="Augmented tetrahedron",
            mesh=triakis,
        )

    def generate_star_polyhedra(self) -> None:
        print("Star polyhedra (approximations)…")
        ico = trimesh.creation.icosahedron()
        dual_vertices, dual_faces = trimesh.polyhedron.dual(ico.vertices, ico.faces)
        stellated = trimesh.Trimesh(vertices=dual_vertices * 1.1, faces=dual_faces)
        self._add_mesh(
            name="Great Dodecahedron (approx)",
            family="StarPolyhedron",
            composition="Star polyhedron",
            mesh=stellated,
        )

    def generate_bipyramids(self, n_range: tuple[int, int] = (3, 12)) -> None:
        print("Bipyramids…")
        for n in range(n_range[0], n_range[1] + 1):
            angles = np.linspace(0, 2 * math.pi, n, endpoint=False)
            base = np.column_stack([np.cos(angles), np.sin(angles), np.zeros(n)])
            vertices = np.vstack([base, [0.0, 0.0, 1.0], [0.0, 0.0, -1.0]])
            faces = []
            apex_top = n
            apex_bot = n + 1
            for i in range(n):
                j = (i + 1) % n
                faces.append([i, j, apex_top])
                faces.append([i, apex_bot, j])
            mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
            self._add_mesh(
                name=f"{n}-gonal Bipyramid",
                family="Bipyramid",
                composition=f"{2 * n} triangles",
                mesh=mesh,
            )

    def generate_trapezohedra(self, n_range: tuple[int, int] = (3, 10)) -> None:
        print("Trapezohedra…")
        for n in range(n_range[0], n_range[1] + 1):
            angles_a = np.linspace(0, 2 * math.pi, n, endpoint=False)
            angles_b = angles_a + math.pi / n
            top = np.column_stack([np.cos(angles_a), np.sin(angles_a), np.ones(n)])
            bottom = np.column_stack([0.7 * np.cos(angles_b), 0.7 * np.sin(angles_b), -np.ones(n)])
            vertices = np.vstack([top, bottom])
            faces = []
            for i in range(n):
                j = (i + 1) % n
                faces.append([i, j, n + i])
                faces.append([j, n + j, n + i])
            mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
            self._add_mesh(
                name=f"{n}-gonal Trapezohedron",
                family="Trapezohedron",
                composition=f"{2 * n} kites",
                mesh=mesh,
            )

    def generate_prisms(self, n_range: tuple[int, int] = (3, 10)) -> None:
        print("Prisms…")
        for n in range(n_range[0], n_range[1] + 1):
            angles = np.linspace(0, 2 * math.pi, n, endpoint=False)
            base = np.column_stack([np.cos(angles), np.sin(angles), np.zeros(n)])
            top = base + np.array([0.0, 0.0, 2.0])
            vertices = np.vstack([base, top])
            faces = [list(range(n)), list(range(2 * n - 1, n - 1, -1))]
            for i in range(n):
                j = (i + 1) % n
                faces.append([i, j, n + j, n + i])
            mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
            self._add_mesh(
                name=f"{n}-gonal Prism",
                family="Prism",
                composition=f"{n} rectangles + 2 {n}-gons",
                mesh=mesh,
            )

    def generate_antiprisms(self, n_range: tuple[int, int] = (3, 8)) -> None:
        print("Antiprisms…")
        for n in range(n_range[0], n_range[1] + 1):
            angles = np.linspace(0, 2 * math.pi, n, endpoint=False)
            top = np.column_stack([np.cos(angles), np.sin(angles), np.ones(n)])
            bottom = np.column_stack([np.cos(angles + math.pi / n), np.sin(angles + math.pi / n), -np.ones(n)])
            vertices = np.vstack([top, bottom])
            faces: list[list[int]] = []
            for i in range(n):
                j = (i + 1) % n
                faces.append([i, j, n + i])
                faces.append([j, n + j, n + i])
            mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
            self._add_mesh(
                name=f"{n}-gonal Antiprism",
                family="Antiprism",
                composition=f"{2 * n} triangles",
                mesh=mesh,
            )

    def generate_geodesic(self, frequencies: Iterable[int] = (1, 2, 3)) -> None:
        print("Geodesic domes…")
        for freq in frequencies:
            mesh = trimesh.creation.icosahedron()
            for _ in range(max(freq - 1, 0)):
                mesh = mesh.subdivide()
            self._add_mesh(
                name=f"Geodesic Dome (freq={freq})",
                family="Geodesic",
                composition=f"Subdivision frequency {freq}",
                mesh=mesh,
            )

    def generate_pentominoes(self) -> None:
        print("Pentomino prisms…")
        pentominoes = {
            "F": [(0, 0), (1, 0), (1, 1), (1, 2), (0, 2)],
            "I": [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4)],
            "L": [(0, 0), (0, 1), (0, 2), (0, 3), (1, 3)],
            "N": [(0, 0), (1, 0), (1, 1), (1, 2), (1, 3)],
            "P": [(0, 0), (0, 1), (0, 2), (1, 1), (1, 2)],
            "T": [(0, 0), (1, 0), (2, 0), (1, 1), (1, 2)],
            "U": [(0, 0), (0, 1), (1, 1), (2, 1), (2, 0)],
            "V": [(0, 0), (0, 1), (0, 2), (1, 2), (2, 2)],
            "W": [(0, 0), (1, 0), (1, 1), (2, 1), (2, 2)],
            "X": [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)],
            "Y": [(0, 0), (1, 0), (1, 1), (1, 2), (1, 3)],
            "Z": [(0, 0), (1, 0), (1, 1), (2, 1), (2, 2)],
        }
        for name, coords in pentominoes.items():
            pts = np.array(coords, dtype=float)
            pts -= pts.mean(axis=0)
            min_vals = pts.min(axis=0)
            pts -= min_vals
            max_vals = pts.max(axis=0)
            grid_shape = (int(max_vals[0]) + 1, int(max_vals[1]) + 1, 2)
            voxels = np.zeros(grid_shape, dtype=bool)
            for (x, y) in pts.astype(int):
                voxels[x, y, :] = True
            grid = trimesh.voxel.VoxelGrid(voxels, pitch=1.0)
            mesh = grid.marching_cubes
            mesh.apply_scale(1.0 / max(mesh.extents))
            self._add_mesh(
                name=f"Pentomino {name}",
                family="Pentomino",
                composition=f"{name}-prism",
                mesh=mesh,
            )

    def generate_compounds(self) -> None:
        print("Compound polyhedra…")
        tetra = trimesh.creation.tetrahedron()
        inverted = tetra.copy()
        inverted.vertices *= -1.0
        compound = trimesh.util.concatenate([tetra, inverted])
        self._add_mesh(
            name="Stella Octangula",
            family="Compound",
            composition="Two tetrahedra",
            mesh=compound,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def generate(
        self,
        include: Iterable[str],
    ) -> None:
        generators = {
            "platonic": self.generate_platonic,
            "archimedean": self.generate_truncated_archimedean,
            "catalan": self.generate_catalan,
            "star": self.generate_star_polyhedra,
            "bipyramids": self.generate_bipyramids,
            "trapezohedra": self.generate_trapezohedra,
            "prisms": self.generate_prisms,
            "antiprisms": self.generate_antiprisms,
            "geodesic": self.generate_geodesic,
            "pentominoes": self.generate_pentominoes,
            "compounds": self.generate_compounds,
        }
        for key in include:
            generator = generators.get(key)
            if generator is None:
                raise ValueError(f"Unknown family '{key}'")
            generator()

    def write_jsonl(self, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as handle:
            for entry in self._polyforms:
                handle.write(json.dumps(entry, separators=(",", ":")) + "\n")
        print(f"\n✓ Wrote {len(self._polyforms)} polyforms to {output_path}")


DEFAULT_FAMILIES = [
    "platonic",
    "archimedean",
    "catalan",
    "star",
    "bipyramids",
    "trapezohedra",
    "prisms",
    "antiprisms",
    "geodesic",
    "pentominoes",
    "compounds",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate canonical polyforms")
    parser.add_argument("--output", type=Path, default=Path("stable_polyforms.jsonl"))
    parser.add_argument(
        "--include",
        nargs="+",
        choices=DEFAULT_FAMILIES,
        default=DEFAULT_FAMILIES,
        help="Families to include in the generated catalog",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(f"Generating polyforms → {args.output}\n")

    generator = PolyformGenerator()
    generator.generate(args.include)
    generator.write_jsonl(args.output)
    print("\n✓ Catalog ready for validation")


if __name__ == "__main__":
    main()
