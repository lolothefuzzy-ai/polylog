from typing import Dict, Any, List, Tuple
import math
import numpy as np

# Geometry and assembly validators for visualization stability

def check_polyform_integrity(polyform: Dict[str, Any], tol_relative: float = 1e-3) -> Tuple[bool, Dict[str, Any]]:
    issues: List[str] = []

    vertices = polyform.get('vertices', [])
    sides = int(polyform.get('sides', 0))

    if not isinstance(vertices, list) or len(vertices) < 3:
        issues.append('invalid_vertices')
        return False, { 'issues': issues }

    # Finite coordinates
    arr = np.array(vertices, dtype=float)
    if not np.isfinite(arr).all():
        issues.append('non_finite_coordinates')

    # Sides vs vertices count
    if sides and sides != len(vertices):
        issues.append('sides_vertices_mismatch')

    # Edge lengths consistency (relative tolerance)
    n = len(vertices)
    lengths = []
    for i in range(n):
        v1 = arr[i]
        v2 = arr[(i+1) % n]
        lengths.append(float(np.linalg.norm(v2 - v1)))

    mean_len = float(np.mean(lengths)) if lengths else 0.0
    max_dev = max(abs(l - mean_len) for l in lengths) if lengths else 0.0
    rel_dev = (max_dev / mean_len) if mean_len > 0 else 0.0

    if mean_len <= 0:
        issues.append('zero_or_negative_edge_length')
    if rel_dev > tol_relative:
        issues.append('edge_length_variance_exceeds_tolerance')

    ok = len(issues) == 0
    return ok, {
        'issues': issues,
        'mean_edge_length': mean_len,
        'max_edge_rel_dev': rel_dev,
    }


def check_bonds_valid(assembly) -> Tuple[bool, Dict[str, Any]]:
    issues: List[str] = []

    polyforms: Dict[str, Dict[str, Any]] = {p['id']: p for p in assembly.get_all_polyforms()}
    bonds = assembly.get_bonds()

    # Track bonds per poly edge to detect duplicates
    bonded_edges = {}

    for b in bonds:
        p1 = polyforms.get(b.get('poly1_id'))
        p2 = polyforms.get(b.get('poly2_id'))
        e1 = b.get('edge1_idx')
        e2 = b.get('edge2_idx')

        if p1 is None or p2 is None:
            issues.append('bond_references_missing_polyform')
            continue

        s1 = int(p1.get('sides', 0))
        s2 = int(p2.get('sides', 0))

        if not (isinstance(e1, int) and 0 <= e1 < max(s1, 0)):
            issues.append('edge1_idx_out_of_range')
        if not (isinstance(e2, int) and 0 <= e2 < max(s2, 0)):
            issues.append('edge2_idx_out_of_range')

        key1 = (b.get('poly1_id'), e1)
        key2 = (b.get('poly2_id'), e2)
        if key1 in bonded_edges:
            issues.append('duplicate_bond_on_edge1')
        if key2 in bonded_edges:
            issues.append('duplicate_bond_on_edge2')
        bonded_edges[key1] = True
        bonded_edges[key2] = True

    ok = len(issues) == 0
    return ok, { 'issues': issues, 'bond_count': len(bonds) }


def check_assembly_consistency(assembly, tol_relative: float = 1e-3) -> Tuple[bool, Dict[str, Any]]:
    issues: List[str] = []
    poly_issues: List[Dict[str, Any]] = []

    for p in assembly.get_all_polyforms():
        ok, meta = check_polyform_integrity(p, tol_relative=tol_relative)
        if not ok:
            issues.append('polyform_integrity_failed')
        poly_issues.append({ 'id': p.get('id'), **meta })

    bonds_ok, bonds_meta = check_bonds_valid(assembly)
    if not bonds_ok:
        issues.append('bonds_invalid')

    ok = len(issues) == 0
    return ok, {
        'issues': issues,
        'polyforms': poly_issues,
        'bonds': bonds_meta,
    }

# ---------------- Acceptance gate helpers (lightweight) ----------------

def has_nan_or_inf(vertices: np.ndarray) -> bool:
    """Return True if any vertex component is NaN or Inf."""
    if vertices is None:
        return False
    try:
        arr = np.asarray(vertices, dtype=float)
        return not np.isfinite(arr).all()
    except Exception:
        return True


def quick_self_intersection_flag(mesh_obj: Any) -> bool:
    """Best-effort self-intersection flag using bounding-box heuristics.
    Returns True if a potential self-intersection is detected.
    Uses bvh3d.TriangleCollisionDetector when available, else returns False.
    """
    try:
        from bvh3d import TriangleCollisionDetector
        vertices = np.array(mesh_obj.vertices)
        faces = np.array(mesh_obj.faces)
        det = TriangleCollisionDetector(type('M', (), {'vertices': vertices, 'faces': faces}))
        return det.check_self_intersection()
    except Exception:
        # Heuristic fallback: none
        return False


# ---------------- Visual assembly validator ----------------

def validate_visual_assembly(assembly: Any, require_3d_mesh: bool = False, check_collisions: bool = False) -> Dict[str, Any]:
    """Validate a visual assembly for automated generation (no user input required).
    Checks:
      - Topology/geometry consistency (existing validators)
      - Optional: 3D mesh presence and finiteness
      - Optional: self-intersection per-mesh and simple inter-mesh collisions
    Returns a report dict: {'is_valid': bool, 'issues': [...], 'counts': {...}}
    """
    issues: List[str] = []
    ok_cons, meta_cons = check_assembly_consistency(assembly)
    if not ok_cons:
        issues.append('assembly_consistency_failed')
    # 3D mesh checks
    mesh_count = 0
    try:
        from polygon_utils import get_polyform_mesh
    except Exception:
        get_polyform_mesh = None  # type: ignore
    meshes = []
    for p in assembly.get_all_polyforms():
        if require_3d_mesh:
            if not p.get('has_3d_mesh'):
                issues.append(f"polyform_missing_mesh:{p.get('id','?')}")
                continue
        if get_polyform_mesh:
            m = get_polyform_mesh(p)
            if m is not None:
                mesh_count += 1
                if has_nan_or_inf(m.vertices) or has_nan_or_inf(m.normals):
                    issues.append(f"mesh_non_finite:{p.get('id','?')}")
                else:
                    meshes.append((p.get('id'), m))
    # Self-intersection per mesh
    for pid, m in meshes:
        try:
            if quick_self_intersection_flag(m):
                issues.append(f"mesh_self_intersection:{pid}")
        except Exception:
            pass
    # Inter-mesh collision (coarse, optional)
    if check_collisions:
        try:
            from bvh3d import TriangleCollisionDetector
            detectors = [(pid, TriangleCollisionDetector(m)) for pid, m in meshes]
            for i in range(len(detectors)):
                for j in range(i+1, len(detectors)):
                    pid1, d1 = detectors[i]
                    pid2, d2 = detectors[j]
                    if d1.check_collision(d2):
                        issues.append(f"mesh_collision:{pid1}:{pid2}")
                        # Early-exit on first collision
                        raise StopIteration
        except StopIteration:
            pass
        except Exception:
            # BVH not available; skip
            pass
    return {
        'is_valid': len(issues) == 0,
        'issues': issues,
        'counts': {
            'polyforms': len(assembly.get_all_polyforms()),
            'bonds': len(assembly.get_bonds()),
            'meshes': mesh_count
        },
        'consistency': meta_cons
    }
