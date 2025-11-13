"""Unit tests for topology detector backend selection."""

from __future__ import annotations

from typing import Iterable

import pytest

from polylog6.detection.topology import TopologyDetector


class _StubSGModule:
    class Point3:  # pragma: no cover - simple container
        def __init__(self, x: float, y: float, z: float) -> None:
            self.coords = (x, y, z)

    class _Hull:
        vertices = [(0, 0, 0)] * 4
        faces = [(0, 1, 2)]
        volume = 1.5
        surface_area = 2.5

    @staticmethod
    def convex_hull(points: Iterable["_StubSGModule.Point3"]):
        assert len(list(points)) >= 3
        return _StubSGModule._Hull()


class _StubTrimeshModule:
    class Hull:
        vertices = [(0, 0, 0)] * 4
        faces = [(0, 1, 2)]
        volume = 3.0
        area = 4.0

    class points:
        class PointCloud:
            def __init__(self, coords):
                self._coords = coords

            @property
            def convex_hull(self):
                return _StubTrimeshModule.Hull()

    class Trimesh:
        def __init__(self, vertices, faces, process):
            self._vertices = vertices
            self._faces = faces

        @property
        def convex_hull(self):  # pragma: no cover - simple attribute
            return _StubTrimeshModule.Hull()


@pytest.fixture()
def square_vertices() -> list[tuple[float, float, float]]:
    return [
        (0.0, 0.0, 0.0),
        (1.0, 0.0, 0.0),
        (1.0, 1.0, 0.0),
        (0.0, 1.0, 0.0),
    ]


def test_topology_detector_prefers_scikit_geometry(square_vertices):
    detector = TopologyDetector(sg_module=_StubSGModule(), trimesh_module=False)

    summary = detector.compute_convex_hull(square_vertices)

    assert detector.primary_backend == "scikit-geometry"
    assert summary.method == "scikit-geometry"
    assert summary.volume == pytest.approx(1.5)
    assert "numpy" in detector.available_backends


def test_topology_detector_falls_back_to_trimesh(square_vertices):
    detector = TopologyDetector(sg_module=False, trimesh_module=_StubTrimeshModule())

    summary = detector.compute_convex_hull(square_vertices)

    assert detector.primary_backend == "trimesh"
    assert summary.method == "trimesh"
    assert summary.volume == pytest.approx(3.0)
    assert "numpy" in detector.available_backends


def test_topology_detector_falls_back_to_numpy(square_vertices):
    detector = TopologyDetector(sg_module=False, trimesh_module=False)

    summary = detector.compute_convex_hull(square_vertices)

    assert detector.primary_backend == "numpy"
    assert summary.method == "numpy"
    assert summary.volume == pytest.approx(0.0)


@pytest.mark.skip(reason="Requires CGAL fixture bundle; tracked in INT-014 parity checklist")
def test_topology_detector_cgal_parity_placeholder():
    """Document future CGAL parity check once fixtures are available."""

    # TODO(INT-014): Load real polyform mesh fixtures and compare CGAL vs Trimesh outputs.
    # Fixtures to capture:
    #   - Simple planar polyform (baseline volume parity)
    #   - Non-planar composite requiring CGAL for accurate surface area
    #   - Degenerate case verifying numpy fallback when CGAL unavailable
    raise NotImplementedError("CGAL parity fixtures pending")
