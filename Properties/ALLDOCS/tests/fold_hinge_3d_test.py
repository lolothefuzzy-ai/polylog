import pathlib
import sys

import numpy as np

# Ensure project root in path
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from geometry3d import extrude_polygon
from hinge_manager import Hinge, HingeManager


def test_fold_hinge_transform_changes_vertices():
    # Create two simple triangles extruded to thin prisms
    verts = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], dtype=float)
    mesh = extrude_polygon(verts, thickness=0.05)

    # Define a hinge along x-axis at origin
    hinge = Hinge(
        poly1_id="p1", poly2_id="p2",
        edge1_idx=0, edge2_idx=0,
        axis_start=np.array([0.0, 0.0, 0.0]),
        axis_end=np.array([1.0, 0.0, 0.0]),
    )

    mgr = HingeManager()
    angle = np.pi / 4

    transformed = mgr.apply_fold_to_mesh(mesh, hinge, angle)

    assert len(transformed.vertices) == len(mesh.vertices)
    assert np.linalg.norm(transformed.vertices - mesh.vertices) > 1e-3, "Vertices should move after fold"
    assert np.isfinite(transformed.vertices).all(), "No NaN/Inf in transformed vertices"
