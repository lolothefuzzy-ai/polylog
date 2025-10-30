import sys, pathlib
import numpy as np
# Ensure project root in path
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from polygon_utils import create_polygon_3d, get_polyform_mesh


def test_mesh_extrusion_basic():
    poly = create_polygon_3d(6, position=(0, 0, 0), thickness=0.2)
    mesh = get_polyform_mesh(poly)
    assert mesh is not None, "Mesh should be present for 3D polygon"
    assert len(mesh.vertices) > 0 and len(mesh.faces) > 0, "Mesh should have vertices and faces"
    # Z should not be all zeros
    z = mesh.vertices[:, 2]
    assert not np.allclose(z, 0.0), "Extrusion should produce non-zero Z coordinates"
    # Normals should be finite and unit-ish
    norms = np.linalg.norm(mesh.normals, axis=1)
    assert np.all(np.isfinite(norms)), "Normals must be finite"
    assert np.all((norms > 0.5) & (norms <= 1.5)), "Normals should have reasonable length"
