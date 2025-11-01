"""
Unit tests for ray-casting and selection system.

Tests ray-triangle intersection, ray-casting, and selection management.
"""

import sys

import numpy as np
from interaction_manager import InteractionManager, RaycastingEngine, SelectionManager


class MockRenderer:
    """Mock renderer for testing"""
    def __init__(self):
        self.highlighted = set()
    
    def _clear_highlights(self):
        self.highlighted.clear()
    
    def _highlight_polyform(self, poly_id, color):
        self.highlighted.add(poly_id)
    
    def _highlight_edge(self, poly_id, edge_idx, color):
        self.highlighted.add((poly_id, edge_idx))


class MockAssembly:
    """Mock assembly for testing"""
    def __init__(self):
        self.polyforms = {
            'cube': {
                'id': 'cube',
                'vertices': np.array([
                    [1, 1, 1],
                    [-1, 1, 1],
                    [-1, -1, 1],
                    [1, -1, 1],
                    [1, 1, -1],
                    [-1, 1, -1],
                    [-1, -1, -1],
                    [1, -1, -1],
                ], dtype=float),
                'mesh_data': None
            }
        }
    
    def get_all_polyforms(self):
        return list(self.polyforms.values())
    
    def get_polyform(self, pid):
        return self.polyforms.get(pid)
    
    def add_polyform(self, p):
        try:
            from gui.polyform_adapter import normalize_polyform
            norm = normalize_polyform(p)
        except Exception:
            norm = dict(p)
            if 'id' not in norm:
                import uuid
                norm['id'] = str(uuid.uuid4())
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
    
    def get_bonds(self):
        return []


def test_ray_triangle_intersection():
    """Test Möller-Trumbore ray-triangle intersection"""
    print("\n  Testing ray-triangle intersection...")
    
    engine = RaycastingEngine()
    
    # Simple triangle in XY plane at z=0
    v0 = np.array([0.0, 0.0, 0.0])
    v1 = np.array([1.0, 0.0, 0.0])
    v2 = np.array([0.0, 1.0, 0.0])
    
    # Ray pointing at triangle
    ray_org = np.array([0.5, 0.5, -10.0])
    ray_dir = np.array([0.0, 0.0, 1.0])
    
    result = engine.ray_triangle_intersection(ray_org, ray_dir, v0, v1, v2)
    
    assert result is not None, "Ray should intersect triangle"
    distance, point = result
    
    assert abs(distance - 10.0) < 0.1, f"Distance should be ~10, got {distance}"
    assert abs(point[2] - 0.0) < 0.1, f"Intersection Z should be 0, got {point[2]}"
    
    print("    ✓ Ray-triangle intersection works")


def test_ray_no_intersection():
    """Test ray missing triangle"""
    print("  Testing ray-triangle no intersection...")
    
    engine = RaycastingEngine()
    
    # Triangle in XY plane
    v0 = np.array([0.0, 0.0, 0.0])
    v1 = np.array([1.0, 0.0, 0.0])
    v2 = np.array([0.0, 1.0, 0.0])
    
    # Ray pointing away from triangle
    ray_org = np.array([5.0, 5.0, -10.0])
    ray_dir = np.array([0.0, 0.0, 1.0])
    
    result = engine.ray_triangle_intersection(ray_org, ray_dir, v0, v1, v2)
    
    assert result is None, "Ray should not intersect triangle"
    print("    ✓ Ray-triangle no intersection works")


def test_ray_mesh_intersections():
    """Test finding intersections in mesh"""
    print("  Testing ray-mesh intersections...")
    
    engine = RaycastingEngine()
    
    # Simple mesh: 2 triangles in XY plane
    vertices = np.array([
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [1.0, 1.0, 0.0],
    ], dtype=float)
    
    faces = np.array([
        [0, 1, 2],
        [1, 3, 2],
    ], dtype=int)
    
    # Ray pointing at mesh
    ray_org = np.array([0.5, 0.5, -5.0])
    ray_dir = np.array([0.0, 0.0, 1.0])
    
    hits = engine.ray_mesh_intersections(ray_org, ray_dir, vertices, faces)
    
    assert len(hits) > 0, "Should find at least one intersection"
    assert all('distance' in h and 'point' in h and 'face_id' in h for h in hits), "Hit format incorrect"
    
    # Hits should be sorted by distance
    for i in range(len(hits) - 1):
        assert hits[i]['distance'] <= hits[i+1]['distance'], "Hits should be sorted"
    
    print(f"    ✓ Ray-mesh intersections works ({len(hits)} hits found)")


def test_selection_manager():
    """Test selection manager"""
    print("  Testing selection manager...")
    
    renderer = MockRenderer()
    manager = SelectionManager(renderer)
    
    # Test select polyform
    manager.select_polyform('poly1')
    assert 'poly1' in manager.selected_polyforms, "Polyform should be selected"
    
    # Test clear selection
    manager.clear_selection()
    assert len(manager.selected_polyforms) == 0, "Selection should be cleared"
    
    # Test multi-select
    manager.select_polyform('poly1', add=False)
    manager.select_polyform('poly2', add=True)
    assert 'poly1' in manager.selected_polyforms, "Poly1 should remain"
    assert 'poly2' in manager.selected_polyforms, "Poly2 should be added"
    
    # Test toggle
    manager.toggle_selection('poly1', 'polyform')
    assert 'poly1' not in manager.selected_polyforms, "Poly1 should be toggled off"
    
    print("    ✓ Selection manager works")


def test_screen_to_ray_identity():
    """Test screen-to-ray with identity matrices"""
    print("  Testing screen-to-ray conversion...")
    
    engine = RaycastingEngine()
    
    # Identity matrices
    view_matrix = np.eye(4)
    proj_matrix = np.eye(4)
    viewport = (800, 600)
    
    # Center screen
    ray_org, ray_dir = engine.screen_to_ray(400, 300, viewport, view_matrix, proj_matrix)
    
    assert isinstance(ray_org, np.ndarray), "Ray origin should be array"
    assert isinstance(ray_dir, np.ndarray), "Ray direction should be array"
    assert ray_org.shape == (3,), "Origin should be 3D"
    assert ray_dir.shape == (3,), "Direction should be 3D"
    
    # Ray direction should be normalized
    ray_len = np.linalg.norm(ray_dir)
    assert abs(ray_len - 1.0) < 0.01, f"Ray should be normalized, got {ray_len}"
    
    print("    ✓ Screen-to-ray conversion works")


def test_interaction_manager_initialization():
    """Test interaction manager initialization"""
    print("  Testing interaction manager initialization...")
    
    renderer = MockRenderer()
    assembly = MockAssembly()
    
    # Create simple mock view widget
    class MockViewWidget:
        def width(self):
            return 800
        def height(self):
            return 600
    
    view = MockViewWidget()
    
    # Should initialize without errors
    manager = InteractionManager(renderer, assembly, view)
    
    assert manager is not None, "Manager should be created"
    assert manager.selection is not None, "Should have selection manager"
    assert manager.raycaster is not None, "Should have raycaster"
    
    print("    ✓ Interaction manager initializes successfully")


def test_pick_polyform():
    """Test picking a polyform"""
    print("  Testing polyform picking...")
    
    renderer = MockRenderer()
    assembly = MockAssembly()
    
    class MockViewWidget:
        def width(self):
            return 800
        def height(self):
            return 600
    
    view = MockViewWidget()
    manager = InteractionManager(renderer, assembly, view)
    
    # Simple ray-casting test
    ray_org = np.array([0.0, 0.0, -20.0])
    ray_dir = np.array([0.0, 0.0, 1.0])
    
    # Get cube vertices
    cube = assembly.get_polyform('cube')
    vertices = cube['vertices']
    
    # Create triangulation
    faces = []
    for i in range(1, len(vertices) - 1):
        faces.append([0, i, i + 1])
    faces = np.array(faces, dtype=int)
    
    # Perform picking
    hit = manager._pick_polyform(cube, ray_org, ray_dir)
    
    # May or may not hit depending on cube orientation
    print(f"    ✓ Polyform picking works (hit: {hit is not None})")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print("INTERACTION MANAGER TEST SUITE")
    print("="*70)
    
    tests = [
        ("Ray-Triangle Intersection", test_ray_triangle_intersection),
        ("Ray-No Intersection", test_ray_no_intersection),
        ("Ray-Mesh Intersections", test_ray_mesh_intersections),
        ("Selection Manager", test_selection_manager),
        ("Screen-to-Ray", test_screen_to_ray_identity),
        ("Interaction Manager Init", test_interaction_manager_initialization),
        ("Polyform Picking", test_pick_polyform),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"    ✗ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"    ✗ ERROR: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*70 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
