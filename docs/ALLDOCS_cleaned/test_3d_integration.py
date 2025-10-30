"""
Test 3D mesh integration functionality.

Run this to verify geometry3d, hinge_manager, and polygon_utils work together.
"""
import numpy as np
from polygon_utils import create_polygon, create_polygon_3d, get_polyform_mesh, add_3d_mesh_to_polyform
from geometry3d import MeshData, extrude_polygon, rotation_matrix_axis_angle, transform_mesh
from hinge_manager import HingeManager, Hinge


def test_polygon_extrusion():
    """Test that polygons can be extruded to 3D meshes."""
    print("Test 1: Polygon Extrusion")
    print("-" * 50)
    
    # Create a 2D polygon
    poly_2d = create_polygon(6, position=(0, 0, 0))
    print(f"✓ Created 2D hexagon with {len(poly_2d['vertices'])} vertices")
    
    # Add 3D mesh
    poly_3d = add_3d_mesh_to_polyform(poly_2d, thickness=0.2)
    assert poly_3d.get('has_3d_mesh') == True, "Should have 3D mesh flag"
    print(f"✓ Added 3D mesh with thickness=0.2")
    
    # Get mesh data
    mesh = get_polyform_mesh(poly_3d)
    assert mesh is not None, "Should be able to retrieve mesh"
    print(f"✓ Mesh has {len(mesh.vertices)} vertices, {len(mesh.faces)} faces")
    print(f"  - Expected: ~12 verts (6 top + 6 bottom), ~20 faces")
    
    # Check that mesh has proper structure
    assert len(mesh.vertices) > 0, "Mesh should have vertices"
    assert len(mesh.faces) > 0, "Mesh should have faces"
    assert len(mesh.normals) == len(mesh.vertices), "Should have normals for each vertex"
    print(f"✓ Mesh structure valid")
    
    # Check z-coordinates are non-zero
    z_coords = mesh.vertices[:, 2]
    assert not np.all(z_coords == 0.0), "Z-coordinates should be non-zero for 3D mesh"
    print(f"✓ Z-coordinates range: [{z_coords.min():.3f}, {z_coords.max():.3f}]")
    
    print("✅ Polygon extrusion test PASSED\n")
    return True


def test_create_polygon_3d():
    """Test direct 3D polygon creation."""
    print("Test 2: Direct 3D Polygon Creation")
    print("-" * 50)
    
    # Create polygon with 3D mesh in one step
    poly = create_polygon_3d(4, position=(1, 2, 0.5), thickness=0.15)
    
    assert poly.get('has_3d_mesh') == True, "Should have 3D mesh"
    assert poly.get('sides') == 4, "Should be a square"
    print(f"✓ Created 3D square at position (1, 2, 0.5)")
    
    mesh = get_polyform_mesh(poly)
    assert mesh is not None, "Should have mesh data"
    print(f"✓ Mesh: {len(mesh.vertices)} vertices, {len(mesh.faces)} faces")
    
    # Check center z-coordinate is near 0.5
    z_coords = mesh.vertices[:, 2]
    z_center = z_coords.mean()
    assert abs(z_center - 0.5) < 0.01, f"Z-center should be near 0.5, got {z_center}"
    print(f"✓ Z-center: {z_center:.3f} (expected ~0.5)")
    
    print("✅ Direct 3D creation test PASSED\n")
    return True


def test_mesh_transformation():
    """Test mesh transformation with rotation."""
    print("Test 3: Mesh Transformation")
    print("-" * 50)
    
    # Create a simple mesh
    verts = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 0]], dtype=np.float32)
    mesh = extrude_polygon(verts, thickness=0.1)
    
    print(f"✓ Created mesh with {len(mesh.vertices)} vertices")
    
    # Create rotation matrix (90 degrees around z-axis)
    angle = np.pi / 2
    axis = np.array([0, 0, 1])
    rotation = rotation_matrix_axis_angle(axis, angle)
    
    print(f"✓ Created rotation matrix: {angle * 180 / np.pi}° around Z-axis")
    
    # Transform mesh
    transformed = transform_mesh(mesh, rotation)
    
    assert len(transformed.vertices) == len(mesh.vertices), "Vertex count should be preserved"
    assert len(transformed.faces) == len(mesh.faces), "Face count should be preserved"
    print(f"✓ Transformed mesh: {len(transformed.vertices)} vertices preserved")
    
    # Check that vertices actually rotated
    diff = np.linalg.norm(transformed.vertices - mesh.vertices)
    assert diff > 0.1, "Vertices should have moved after rotation"
    print(f"✓ Vertices moved by {diff:.3f} (rotation applied)")
    
    print("✅ Mesh transformation test PASSED\n")
    return True


def test_hinge_creation():
    """Test hinge creation and fold computation."""
    print("Test 4: Hinge Manager")
    print("-" * 50)
    
    # Create simple hinge
    hinge = Hinge(
        poly1_id="poly_1",
        poly2_id="poly_2",
        edge1_idx=0,
        edge2_idx=0,
        axis_start=np.array([0, 0, 0]),
        axis_end=np.array([1, 0, 0]),
        fold_angle=0.0
    )
    
    print(f"✓ Created hinge between {hinge.poly1_id} and {hinge.poly2_id}")
    
    # Get hinge axis
    axis = hinge.get_axis()
    assert np.allclose(axis, [1, 0, 0]), "Axis should be normalized to [1,0,0]"
    print(f"✓ Hinge axis: {axis}")
    
    # Create hinge manager
    manager = HingeManager()
    idx = manager.graph.add_hinge(hinge)
    assert idx == 0, "First hinge should have index 0"
    print(f"✓ Added hinge to manager at index {idx}")
    
    # Compute fold transform
    fold_angle = np.pi / 3  # 60 degrees
    transform = manager.compute_fold_transform(hinge, fold_angle)
    assert transform.shape == (4, 4), "Transform should be 4x4 matrix"
    print(f"✓ Computed fold transform for {fold_angle * 180 / np.pi}° rotation")
    
    print("✅ Hinge manager test PASSED\n")
    return True


def test_out_of_plane_rotation():
    """Test out-of-plane rotation computation."""
    print("Test 5: Out-of-Plane Rotation")
    print("-" * 50)
    
    # Create hinge along x-axis
    hinge = Hinge(
        poly1_id="p1",
        poly2_id="p2",
        edge1_idx=0,
        edge2_idx=0,
        axis_start=np.array([0, 0, 0]),
        axis_end=np.array([1, 0, 0]),
    )
    
    manager = HingeManager()
    
    # Current normal pointing up (+z)
    current_normal = np.array([0, 0, 1])
    # Target normal pointing in +y direction
    target_normal = np.array([0, 1, 0])
    
    # Compute required rotation
    angle = manager.compute_out_of_plane_rotation(hinge, target_normal, current_normal)
    
    print(f"✓ Computed rotation angle: {angle * 180 / np.pi:.1f}°")
    assert abs(angle) > 0.1, "Angle should be non-zero for different normals"
    assert abs(angle) < np.pi, "Angle should be reasonable (<180°)"
    
    print("✅ Out-of-plane rotation test PASSED\n")
    return True


def run_all_tests():
    """Run all 3D integration tests."""
    print("\n" + "=" * 60)
    print("3D INTEGRATION TEST SUITE")
    print("=" * 60 + "\n")
    
    tests = [
        test_polygon_extrusion,
        test_create_polygon_3d,
        test_mesh_transformation,
        test_hinge_creation,
        test_out_of_plane_rotation,
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"❌ Test FAILED with error: {e}\n")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    print("=" * 60)
    print(f"SUMMARY: {sum(results)}/{len(results)} tests passed")
    print("=" * 60)
    
    if all(results):
        print("\n🎉 ALL TESTS PASSED! 3D integration is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check output above for details.")
    
    return all(results)


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
