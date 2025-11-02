"""Geometry helpers used by the automated placement engine.

This module reimplements the small portion of legacy ``polygon_utils`` that the
placement engine relies on: computing edge normals, generating lightweight mesh
representations, and performing basic collision checks.  The implementation is
purposefully simple so the runtime remains transportable; future iterations can
swap in a full BVH or spatial index without changing the public API exposed
here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple

import numpy as np


Vector = Tuple[float, ...]
VertexList = Sequence[Vector]


def _as_2d(vertices: VertexList) -> np.ndarray:
    """Return vertices as an Nx2 numpy array, padding with zeros if required."""

    arr = np.asarray(vertices, dtype=float)
    if arr.ndim != 2:
        raise ValueError("vertices must be an NxM array-like structure")
    if arr.shape[0] == 0:
        return np.empty((0, 2), dtype=float)
    if arr.shape[1] == 2:
        return arr
    if arr.shape[1] > 2:
        return arr[:, :2]
    # pad up to 2D
    pad = np.zeros((arr.shape[0], 2 - arr.shape[1]), dtype=float)
    return np.hstack([arr, pad])


def compute_edge_normals(vertices: VertexList) -> np.ndarray:
    """Calculate outward-facing edge normals for a polygon."""

    verts = _as_2d(vertices)
    if len(verts) < 2:
        return np.empty((0, 2), dtype=float)

    edges = np.roll(verts, -1, axis=0) - verts
    normals = np.column_stack((-edges[:, 1], edges[:, 0]))
    magnitudes = np.linalg.norm(normals, axis=1)
    magnitudes[magnitudes == 0] = 1.0
    return normals / magnitudes[:, None]


def get_polyform_mesh(vertices: VertexList) -> np.ndarray:
    """Generate a simple triangle fan mesh representing the polygon.

    For convex polygons this provides a valid triangulation.  For concave
    polygons the mesh is approximate but adequate for broad-phase collision
    checks and visualisation placeholders.
    """

    verts = _as_2d(vertices)
    if len(verts) < 3:
        return np.empty((0, 3, 2), dtype=float)

    triangles: List[np.ndarray] = []
    anchor = verts[0]
    for idx in range(1, len(verts) - 1):
        tri = np.vstack([anchor, verts[idx], verts[idx + 1]])
        triangles.append(tri)
    return np.asarray(triangles, dtype=float)


@dataclass
class PlacementCandidate:
    """Minimal polygon placement representation for validation."""

    vertices: np.ndarray
    position: Vector
    rotation: float

    def transformed(self) -> np.ndarray:
        """Return vertices transformed by rotation (radians) and translation."""

        if self.vertices.size == 0:
            return self.vertices.copy()

        rot = np.array(
            [
                [np.cos(self.rotation), -np.sin(self.rotation)],
                [np.sin(self.rotation), np.cos(self.rotation)],
            ],
            dtype=float,
        )
        rotated = self.vertices @ rot.T
        return rotated + np.asarray(self.position, dtype=float)


def _bounding_radius(vertices: np.ndarray) -> float:
    if vertices.size == 0:
        return 0.0
    centre = vertices.mean(axis=0)
    distances = np.linalg.norm(vertices - centre, axis=1)
    return float(distances.max(initial=0.0))


class PolygonBVHValidator:
    """Simplified validator that uses bounding-circle overlap checks."""

    def __init__(self, tolerance: float = 1e-6) -> None:
        self.tolerance = tolerance
        self.enabled = True

    def validate_placement(
        self,
        polygon_vertices: VertexList,
        position: Vector = (0.0, 0.0),
        rotation: float = 0.0,
        existing_meshes: Iterable[VertexList] | None = None,
    ) -> bool:
        """Validate placement by comparing bounding circles.

        Args:
            polygon_vertices: Vertices of the polyform being placed.
            position: Target translation (x, y).
            rotation: Rotation angle in radians.
            existing_meshes: Optional iterable of vertex lists representing
                existing geometry to test against.

        Returns:
            ``True`` if no bounding circles overlap beyond tolerance.
        """

        candidate = PlacementCandidate(_as_2d(polygon_vertices), position, rotation)
        transformed = candidate.transformed()
        cand_centre = transformed.mean(axis=0)
        cand_radius = _bounding_radius(transformed) + self.tolerance

        if existing_meshes is None:
            return True

        for mesh_vertices in existing_meshes:
            mesh = _as_2d(mesh_vertices)
            if mesh.size == 0:
                continue
            centre = mesh.mean(axis=0)
            radius = _bounding_radius(mesh)
            distance = np.linalg.norm(cand_centre - centre)
            if distance < (cand_radius + radius):
                return False
        return True


BVH_AVAILABLE = True
