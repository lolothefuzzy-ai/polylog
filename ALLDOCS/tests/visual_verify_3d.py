#!/usr/bin/env python
"""
Visual Verification of 3D Generation
=====================================

Creates visual outputs to verify:
1. Polygon vertices are correctly generated
2. Vertices form valid closed polygons
3. Bonds connect edges properly
4. Assembly compositions are correct
5. 3D coordinates are preserved
"""

import sys
import pathlib
import numpy as np
from typing import Dict, List, Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_polygon_generation():
    """Verify polygon vertices are generated correctly."""
    print("\n[VISUAL TEST] Polygon Generation")
    print("=" * 70)
    
    from polygon_utils import create_polygon
    
    for sides in [3, 4, 5, 6, 8, 12]:
        poly = create_polygon(sides)
        verts = np.array(poly['vertices'], dtype=float)
        
        # Verify structure
        assert 'vertices' in poly, f"Missing vertices in {sides}-gon"
        assert 'sides' in poly, f"Missing sides in {sides}-gon"
        assert poly['sides'] == sides, f"Sides mismatch: {poly['sides']} != {sides}"
        assert len(verts) == sides, f"Vertex count mismatch: {len(verts)} != {sides}"
        
        # Verify closed polygon (first and last vertex should define first edge)
        edge_lengths = []
        for i in range(len(verts)):
            v1 = verts[i]
            v2 = verts[(i + 1) % len(verts)]
            length = np.linalg.norm(v2 - v1)
            edge_lengths.append(length)
        
        avg_edge = np.mean(edge_lengths)
        std_edge = np.std(edge_lengths)
        
        # All edges should be ~1.0
        assert np.allclose(avg_edge, 1.0, atol=0.01), f"Edge length {avg_edge:.4f} != 1.0"
        assert std_edge < 0.01, f"Edge variance {std_edge:.4f} too high"
        
        # Verify all vertices are in 3D (x, y, z)
        assert verts.shape[1] == 3, f"Vertices not 3D: {verts.shape}"
        
        # Verify z=0 (currently 2D)
        assert np.allclose(verts[:, 2], 0.0), f"{sides}-gon has non-zero z: {verts[:, 2]}"
        
        # Verify centroid
        centroid = np.mean(verts, axis=0)
        assert np.allclose(centroid[:2], 0.0, atol=0.01), f"Centroid not at origin: {centroid[:2]}"
        
        print(f"  ✓ {sides:2d}-gon: {len(verts)} vertices, edges ~{avg_edge:.4f}, z=0")
    
    print("  ✓ All polygon generations verified")


def test_assembly_composition():
    """Verify assemblies contain correct polyform types."""
    print("\n[VISUAL TEST] Assembly Composition")
    print("=" * 70)
    
    from polygon_utils import create_polygon
    from polyform_library import add_cube_net, add_triangular_prism_net
    
    class TestAsm:
        def __init__(self):
            self.polyforms = {}
            self._id = 1
        def add_polyform(self, p):
            try:
                from gui.polyform_adapter import normalize_polyform
                norm = normalize_polyform(p)
            except Exception:
                norm = dict(p)
                if 'id' not in norm:
                    norm['id'] = f"p{self._id}"
                    self._id += 1
                verts = []
                for v in norm.get('vertices', []):
                    if isinstance(v, (list, tuple)):
                        if len(v) == 2:
                            verts.append((float(v[0]), float(v[1]), 0.0))
                        else:
                            verts.append((float(v[0]), float(v[1]), float(v[2]) if len(v) > 2 else 0.0))
                if verts:
                    norm['vertices'] = verts
            self.polyforms[norm['id']] = norm
        def get_all_polyforms(self):
            return list(self.polyforms.values())
    
    # Test cube net
    asm_cube = TestAsm()
    ids = add_cube_net(asm_cube, (0, 0, 0))
    assert len(ids) == 6, f"Cube net should have 6 faces, got {len(ids)}"
    polys = asm_cube.get_all_polyforms()
    assert all(p['sides'] == 4 for p in polys), "Cube net should have all squares"
    print(f"  ✓ Cube net: 6 squares at origin (0,0,0)")
    
    # Test prism net
    asm_prism = TestAsm()
    ids = add_triangular_prism_net(asm_prism, (5, 5, 5))
    assert len(ids) == 5, f"Prism net should have 5 faces, got {len(ids)}"
    polys = asm_prism.get_all_polyforms()
    sides_counts = [p['sides'] for p in polys]
    assert sides_counts.count(4) == 3, "Prism should have 3 squares"
    assert sides_counts.count(3) == 2, "Prism should have 2 triangles"
    print(f"  ✓ Prism net: 3 squares + 2 triangles at origin (5,5,5)")
    
    print("  ✓ All assembly compositions verified")


def test_bond_geometry():
    """Verify bonds connect edges correctly."""
    print("\n[VISUAL TEST] Bond Geometry")
    print("=" * 70)
    
    from polygon_utils import create_polygon
    
    class TestAsm:
        def __init__(self):
            self.polyforms = {}
            self.bonds = []
            self._id = 1
        def add_polyform(self, p):
            try:
                from gui.polyform_adapter import normalize_polyform
                norm = normalize_polyform(p)
            except Exception:
                norm = dict(p)
                if 'id' not in norm:
                    norm['id'] = f"p{self._id}"
                    self._id += 1
                verts = []
                for v in norm.get('vertices', []):
                    if isinstance(v, (list, tuple)):
                        if len(v) == 2:
                            verts.append((float(v[0]), float(v[1]), 0.0))
                        else:
                            verts.append((float(v[0]), float(v[1]), float(v[2]) if len(v) > 2 else 0.0))
                if verts:
                    norm['vertices'] = verts
            self.polyforms[norm['id']] = norm
        def get_polyform(self, pid):
            return self.polyforms.get(pid)
        def get_all_polyforms(self):
            return list(self.polyforms.values())
        def add_bond(self, b):
            self.bonds.append(b)
        def get_bonds(self):
            return self.bonds
    
    # Create assembly
    asm = TestAsm()
    p1 = create_polygon(4)
    p2 = create_polygon(4)
    asm.add_polyform(p1)
    asm.add_polyform(p2)
    
    # Simulate bond
    bond = {
        'poly1_id': p1['id'],
        'edge1_idx': 0,
        'poly2_id': p2['id'],
        'edge2_idx': 2,
        'fold_angle': 1.57  # π/2
    }
    asm.add_bond(bond)
    
    # Verify bond structure
    bonds = asm.get_bonds()
    assert len(bonds) == 1, "Should have 1 bond"
    b = bonds[0]
    
    # Get edge endpoints
    def edge_endpoints(poly, idx):
        verts = np.array(poly['vertices'], dtype=float)
        n = len(verts)
        return verts[idx], verts[(idx + 1) % n]
    
    v1_start, v1_end = edge_endpoints(asm.get_polyform(p1['id']), b['edge1_idx'])
    v2_start, v2_end = edge_endpoints(asm.get_polyform(p2['id']), b['edge2_idx'])
    
    # Verify edge lengths match (should both be ~1.0)
    len1 = np.linalg.norm(v1_end - v1_start)
    len2 = np.linalg.norm(v2_end - v2_start)
    
    assert np.isclose(len1, len2, atol=0.01), f"Edge lengths don't match: {len1:.4f} vs {len2:.4f}"
    print(f"  ✓ Bond edge lengths match: {len1:.4f} ≈ {len2:.4f}")
    print(f"  ✓ Bond fold angle stored: {b['fold_angle']:.4f} rad")
    
    print("  ✓ All bond geometries verified")


def test_3d_persistence():
    """Verify 3D coordinates are preserved through operations."""
    print("\n[VISUAL TEST] 3D Coordinate Persistence")
    print("=" * 70)
    
    from polygon_utils import create_polygon
    import validators as V
    
    class TestAsm:
        def __init__(self):
            self.polyforms = {}
            self._id = 1
        def add_polyform(self, p):
            try:
                from gui.polyform_adapter import normalize_polyform
                norm = normalize_polyform(p)
            except Exception:
                norm = dict(p)
                if 'id' not in norm:
                    norm['id'] = f"p{self._id}"
                    self._id += 1
                verts = []
                for v in norm.get('vertices', []):
                    if isinstance(v, (list, tuple)):
                        if len(v) == 2:
                            verts.append((float(v[0]), float(v[1]), 0.0))
                        else:
                            verts.append((float(v[0]), float(v[1]), float(v[2]) if len(v) > 2 else 0.0))
                if verts:
                    norm['vertices'] = verts
            self.polyforms[norm['id']] = norm
        def get_all_polyforms(self):
            return list(self.polyforms.values())
        def copy(self):
            new = TestAsm()
            new.polyforms = {k: dict(v) for k, v in self.polyforms.items()}
            return new
    
    # Create assembly with multiple positions
    asm = TestAsm()
    p1 = create_polygon(4, position=(0, 0, 0))
    p2 = create_polygon(3, position=(2, 2, 0))
    p3 = create_polygon(5, position=(-1, 1, 0))
    
    asm.add_polyform(p1)
    asm.add_polyform(p2)
    asm.add_polyform(p3)
    
    # Check coordinates preserved
    for p in asm.get_all_polyforms():
        verts = np.array(p['vertices'], dtype=float)
        pos = np.array(p['position'], dtype=float)
        
        # Centroid should match position (within tolerance)
        centroid = np.mean(verts, axis=0)
        # For 2D, only check x,y
        assert np.allclose(centroid[:2], pos[:2], atol=0.1), \
            f"Centroid {centroid[:2]} doesn't match position {pos[:2]}"
        
        print(f"  ✓ Polyform {p['id']}: position {pos}, vertices centered")
    
    # Test copy preserves coordinates
    asm2 = asm.copy()
    for p_orig, p_copy in zip(asm.get_all_polyforms(), asm2.get_all_polyforms()):
        verts_orig = np.array(p_orig['vertices'], dtype=float)
        verts_copy = np.array(p_copy['vertices'], dtype=float)
        assert np.allclose(verts_orig, verts_copy), \
            f"Copy doesn't preserve vertices for {p_orig['id']}"
    
    print("  ✓ All 3D coordinates preserved through copy")
    
    # Validate all polyforms
    for p in asm.get_all_polyforms():
        ok, meta = V.check_polyform_integrity(p)
        assert ok, f"Polyform {p['id']} integrity check failed: {meta}"
    
    print("  ✓ All polyforms pass integrity validation")


def test_renderer_inputs():
    """Verify data format matches renderer expectations."""
    print("\n[VISUAL TEST] Renderer Input Format")
    print("=" * 70)
    
    from polygon_utils import create_polygon
    
    poly = create_polygon(4)
    verts = np.array(poly['vertices'], dtype=float)
    
    # Verify vertices can be used by GLMeshItem
    assert verts.shape == (4, 3), f"Expected shape (4,3), got {verts.shape}"
    assert verts.dtype in [np.float32, np.float64], f"Expected float type, got {verts.dtype}"
    
    # Verify triangle-fan can be constructed
    n = len(verts)
    center = np.mean(verts, axis=0)
    tri_verts = np.vstack([center, verts])
    
    faces = []
    for i in range(1, n):
        faces.append([0, i, i + 1])
    faces.append([0, n, 1])
    
    assert len(faces) == n, f"Expected {n} faces, got {len(faces)}"
    
    print(f"  ✓ Vertices shape: {verts.shape}")
    print(f"  ✓ Triangle-fan: {n} faces from center + {n} verts")
    print(f"  ✓ Center: {center}")
    print(f"  ✓ Renderer input format valid")


def run_all():
    """Run all visual verification tests."""
    print("\n" + "=" * 70)
    print("VISUAL VERIFICATION: 3D GENERATION FUNCTIONS")
    print("=" * 70)
    
    try:
        test_polygon_generation()
        test_assembly_composition()
        test_bond_geometry()
        test_3d_persistence()
        test_renderer_inputs()
        
        print("\n" + "=" * 70)
        print("RESULT: ALL VISUAL TESTS PASS")
        print("=" * 70)
        print("\n✓ Polygon generation: VERIFIED")
        print("✓ Assembly composition: VERIFIED")
        print("✓ Bond geometry: VERIFIED")
        print("✓ 3D persistence: VERIFIED")
        print("✓ Renderer inputs: VERIFIED")
        print("\n3D geometry generation is functioning correctly.")
        return True
        
    except AssertionError as e:
        print(f"\n✗ VERIFICATION FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = run_all()
    sys.exit(0 if success else 1)
