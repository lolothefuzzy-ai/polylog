"""Geometry utilities with optional CGAL/scikit-geometry acceleration."""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import List, Optional, Sequence, Tuple

import numpy as np


@dataclass(slots=True)
class HullSummary:
    """Thin wrapper describing convex hull properties returned by detectors."""

    method: str
    vertex_count: int
    face_count: int
    volume: Optional[float] = None
    surface_area: Optional[float] = None
    bounding_box: Optional[Tuple[Tuple[float, float, float], Tuple[float, float, float]]] = None


class TopologyDetector:
    """Hybrid convex-hull detector with optional scikit-geometry / Trimesh backends."""

    def __init__(
        self,
        *,
        sg_module: Optional[object] = None,
        trimesh_module: Optional[object] = None,
    ) -> None:
        self._sg = self._resolve_module("skgeom", sg_module)
        self._trimesh = self._resolve_module("trimesh", trimesh_module)

        self._backends: List[str] = []
        if self._sg is not None:
            self._backends.append("scikit-geometry")
        if self._trimesh is not None:
            self._backends.append("trimesh")
        self._backends.append("numpy")  # Always available fallback

    @property
    def available_backends(self) -> List[str]:
        return list(self._backends)

    @property
    def primary_backend(self) -> str:
        return self._backends[0]

    def compute_convex_hull(self, vertices: Sequence[Sequence[float]]) -> HullSummary:
        """Compute a convex hull summary using the best available backend."""

        coords = self._to_numpy(vertices)
        last_error: Optional[Exception] = None

        for backend in self._backends:
            try:
                if backend == "scikit-geometry":
                    return self._convex_hull_skgeom(coords)
                if backend == "trimesh":
                    return self._convex_hull_trimesh(coords)
                return self._convex_hull_numpy(coords)
            except Exception as exc:  # pragma: no cover - fallback safety
                last_error = exc
                continue

        raise RuntimeError("No topology backend succeeded") from last_error

    # Internal helpers -------------------------------------------------

    def _convex_hull_skgeom(self, coords: np.ndarray) -> HullSummary:
        sg = self._sg
        if sg is None:
            raise RuntimeError("scikit-geometry unavailable")

        try:
            points = [sg.Point3(float(x), float(y), float(z)) for x, y, z in coords]
            hull = sg.convex_hull(points)
        except AttributeError as exc:  # pragma: no cover - API mismatch safety
            raise RuntimeError("Failed to call scikit-geometry convex_hull") from exc

        vertex_count = self._len_attr(hull, "vertices", default=len(points))
        face_count = self._len_attr(hull, "faces", default=0)
        volume = self._float_attr(hull, "volume")
        surface_area = self._float_attr(hull, "surface_area")

        bbox = self._bounding_box(coords)
        return HullSummary(
            method="scikit-geometry",
            vertex_count=vertex_count,
            face_count=face_count,
            volume=volume,
            surface_area=surface_area,
            bounding_box=bbox,
        )

    def _convex_hull_trimesh(self, coords: np.ndarray) -> HullSummary:
        tm = self._trimesh
        if tm is None:
            raise RuntimeError("trimesh unavailable")

        hull = None
        # Prefer PointCloud if available because it is tolerant of missing faces
        point_cloud = getattr(getattr(tm, "points", None), "PointCloud", None)
        if point_cloud is not None:
            cloud = point_cloud(coords)
            hull = getattr(cloud, "convex_hull", None)
        if hull is None:
            mesh = tm.Trimesh(vertices=coords, faces=[], process=False)
            hull = getattr(mesh, "convex_hull", mesh)

        vertex_count = self._len_attr(hull, "vertices", default=len(coords))
        face_count = self._len_attr(hull, "faces", default=0)
        volume = self._float_attr(hull, "volume")
        surface_area = self._float_attr(hull, "area")
        bbox = self._bounding_box(coords)

        return HullSummary(
            method="trimesh",
            vertex_count=vertex_count,
            face_count=face_count,
            volume=volume,
            surface_area=surface_area,
            bounding_box=bbox,
        )

    def _convex_hull_numpy(self, coords: np.ndarray) -> HullSummary:
        bbox = self._bounding_box(coords)
        min_corner, max_corner = bbox
        span = np.maximum(np.subtract(max_corner, min_corner), 0.0)
        volume = float(np.prod(span)) if np.any(span) else None

        return HullSummary(
            method="numpy",
            vertex_count=int(coords.shape[0]),
            face_count=0,
            volume=volume,
            surface_area=None,
            bounding_box=bbox,
        )

    @staticmethod
    def _resolve_module(name: str, override: Optional[object]) -> Optional[object]:
        if override is not None or override is False:
            return override or None
        try:
            return import_module(name)
        except ImportError:  # pragma: no cover - optional dependency
            return None

    @staticmethod
    def _to_numpy(vertices: Sequence[Sequence[float]]) -> np.ndarray:
        arr = np.asarray(vertices, dtype=float)
        if arr.ndim != 2:
            raise ValueError("vertices must be a 2D sequence")
        if arr.shape[1] == 2:
            arr = np.column_stack([arr, np.zeros(arr.shape[0], dtype=float)])
        elif arr.shape[1] != 3:
            raise ValueError("vertices must have 2 or 3 columns")
        return arr

    @staticmethod
    def _len_attr(obj: object, attr: str, default: int = 0) -> int:
        value = getattr(obj, attr, None)
        if value is None:
            return default
        try:
            return len(value)
        except TypeError:
            return default

    @staticmethod
    def _float_attr(obj: object, attr: str) -> Optional[float]:
        value = getattr(obj, attr, None)
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _bounding_box(coords: np.ndarray) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
        mins = tuple(np.min(coords, axis=0).tolist())
        maxs = tuple(np.max(coords, axis=0).tolist())
        return mins, maxs


__all__ = ["TopologyDetector", "HullSummary"]
