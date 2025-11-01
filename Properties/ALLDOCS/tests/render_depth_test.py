import pathlib
import sys

import numpy as np

# Ensure project root in path
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from polygon_utils import create_polygon_3d, get_polyform_mesh


def test_render_depth_invariant_bounds():
    # Create two 3D polygons at different Z centers
    p1 = create_polygon_3d(5, position=(0, 0, -0.2), thickness=0.1)
    m1 = get_polyform_mesh(p1)
    p2 = create_polygon_3d(5, position=(0, 0, 0.3), thickness=0.1)
    m2 = get_polyform_mesh(p2)

    assert m1 is not None and m2 is not None

    # Depth separation should be reflected in vertex Z averages
    z1 = float(m1.vertices[:, 2].mean())
    z2 = float(m2.vertices[:, 2].mean())
    assert z2 - z1 > 0.3 - 1e-2, "Average Z should reflect placement"

    # Mesh faces should index within bounds
    assert m1.faces.max() < len(m1.vertices)
    assert m2.faces.max() < len(m2.vertices)

    # No degenerate faces (area near zero)
    def tri_area(a,b,c):
        return 0.5 * np.linalg.norm(np.cross(b-a,c-a))
    areas1 = [tri_area(m1.vertices[f[0]], m1.vertices[f[1]], m1.vertices[f[2]]) for f in m1.faces]
    areas2 = [tri_area(m2.vertices[f[0]], m2.vertices[f[1]], m2.vertices[f[2]]) for f in m2.faces]
    assert np.min(areas1) > 1e-10
    assert np.min(areas2) > 1e-10
