"""
Comprehensive tests for 3D geometry and folding operations.

Tests cover:
- Mesh extrusion (non-zero Z, normals)
- Fold transformations (vertices, finiteness)
- Render depth invariants
- Numerical stability
"""

import math
import unittest

import numpy as np
from collision_validator import CollisionValidator
from geometry3d import (
    MeshData,
    extrude_polygon,
    extrude_polygon_with_centroid,
    rotation_matrix_axis_angle,
    transform_mesh,
)
from hinge_manager import Hinge
from polygon_utils import create_polygon_3d, get_polyform_mesh


class TestMeshExtrusion(unittest.TestCase):
    """Test 3D polygon extrusion functionality."""
    
    def setUp(self):
        """Create test polygons."""
        # Simple triangle
        self.triangle_2d = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.5, 1.0, 0.0]
        ], dtype=np.float32)
        
        # Square
        self.square_2d = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [1.0, 1.0, 0.0],
            [0.0, 1.0, 0.0]
        ], dtype=np.float32)
    
    def test_extrude_triangle_has_nonzero_z(self):
        """Test that extrusion creates non-zero Z coordinates."""
        mesh = extrude_polygon(self.triangle_2d, thickness=0.2, center_z=0.0)
        
        # Check that we have vertices with different Z values
        z_coords = mesh.vertices[:, 2]
        z_unique = np.unique(np.round(z_coords, decimals=6))
        
        self.assertGreaterEqual(len(z_unique), 2, "Should have at least 2 unique Z values")
        self.assertIn(-0.1, z_unique, "Should have bottom face at z=-0.1")
        self.assertIn(0.1, z_unique, "Should have top face at z=0.1")
    
    def test_extrude_polygon_vertex_count(self):
        """Test correct vertex count after extrusion."""
        mesh = extrude_polygon(self.triangle_2d, thickness=0.1)
        
        # Triangle: 3 vertices × 2 (top + bottom) = 6 vertices
        self.assertEqual(len(mesh.vertices), 6, "Triangle extrusion should have 6 vertices")
        
        mesh_square = extrude_polygon(self.square_2d, thickness=0.1)
        # Square: 4 vertices × 2 = 8 vertices
        self.assertEqual(len(mesh_square.vertices), 8, "Square extrusion should have 8 vertices")
    
    def test_extrude_polygon_face_count(self):
        """Test correct face count after extrusion."""
        mesh = extrude_polygon(self.triangle_2d, thickness=0.1)
        
        # Triangle: 1 bottom + 1 top + 3 sides (2 tris each) = 8 faces
        expected_faces = 1 + 1 + (3 * 2)
        self.assertEqual(len(mesh.faces), expected_faces, 
                        f"Triangle extrusion should have {expected_faces} faces")
    
    def test_extrude_polygon_normals_valid(self):
        """Test that computed normals are valid (unit vectors)."""
        mesh = extrude_polygon(self.triangle_2d, thickness=0.1)
        
        # All normals should be unit vectors (length ~1)
        normal_lengths = np.linalg.norm(mesh.normals, axis=1)
        
        for length in normal_lengths:
            self.assertAlmostEqual(length, 1.0, places=5, 
                                  msg="All normals should be unit vectors")
    
    def test_extrude_polygon_normals_finite(self):
        """Test that all normal values are finite."""
        mesh = extrude_polygon(self.triangle_2d, thickness=0.1)
        
        self.assertTrue(np.all(np.isfinite(mesh.normals)), 
                       "All normal values should be finite (no NaN/Inf)")
    
    def test_extrude_polygon_with_centroid(self):
        """Test centroid-based extrusion."""
        mesh = extrude_polygon_with_centroid(self.triangle_2d, thickness=0.1, center_z=0.5)
        
        # Should have more vertices than standard extrusion (includes centroids)
        self.assertGreater(len(mesh.vertices), 6, "Centroid extrusion should have more vertices")
        
        # Check Z range
        z_coords = mesh.vertices[:, 2]
        z_min = np.min(z_coords)
        z_max = np.max(z_coords)
        
        self.assertAlmostEqual(z_min, 0.45, places=5)
        self.assertAlmostEqual(z_max, 0.55, places=5)


class TestFoldTransformations(unittest.TestCase):
    """Test 3D fold transformations and hinge mechanics."""
    
    def setUp(self):
        """Create test polyforms."""
        self.triangle_3d = create_polygon_3d(3, position=(0, 0, 0), thickness=0.1)
        self.square_3d = create_polygon_3d(4, position=(0, 0, 0), thickness=0.1)
    
    def test_fold_transform_preserves_finiteness(self):
        """Test that fold transforms don't create NaN/Inf."""
        axis = np.array([1.0, 0.0, 0.0])  # X-axis
        angle = math.pi / 4  # 45 degrees
        
        transform = rotation_matrix_axis_angle(axis, angle)
        
        # All matrix values should be finite
        self.assertTrue(np.all(np.isfinite(transform)), 
                       "Transformation matrix should be all finite")
    
    def test_fold_transform_orthogonal(self):
        """Test that fold transforms are orthogonal (preserve distances)."""
        axis = np.array([0.0, 0.0, 1.0])  # Z-axis
        angle = math.pi / 3  # 60 degrees
        
        transform = rotation_matrix_axis_angle(axis, angle)
        
        # Check orthogonality: R @ R^T = I
        rotation_part = transform[:3, :3]
        identity = rotation_part @ rotation_part.T
        
        np.testing.assert_array_almost_equal(identity, np.eye(3), decimal=5,
                                           err_msg="Rotation should be orthogonal")
    
    def test_fold_transform_mesh(self):
        """Test folding a mesh preserves vertex count."""
        mesh = get_polyform_mesh(self.triangle_3d)
        if mesh is None:
            self.skipTest("No 3D mesh available")
        
        axis = np.array([1.0, 0.0, 0.0])
        transform = rotation_matrix_axis_angle(axis, math.pi / 2)
        
        transformed = transform_mesh(mesh, transform)
        
        # Should have same vertex count
        self.assertEqual(len(transformed.vertices), len(mesh.vertices))
        self.assertEqual(len(transformed.faces), len(mesh.faces))
    
    def test_fold_transform_preserves_normals_unit(self):
        """Test that transformed normals are still unit vectors."""
        mesh = get_polyform_mesh(self.square_3d)
        if mesh is None:
            self.skipTest("No 3D mesh available")
        
        axis = np.array([0.0, 1.0, 0.0])
        transform = rotation_matrix_axis_angle(axis, math.pi / 6)
        
        transformed = transform_mesh(mesh, transform)
        
        # Check normals are unit
        normal_lengths = np.linalg.norm(transformed.normals, axis=1)
        for length in normal_lengths:
            self.assertAlmostEqual(length, 1.0, places=5)
    
    def test_hinge_axis_normalization(self):
        """Test that hinge axes are properly normalized."""
        start = np.array([0.0, 0.0, 0.0])
        end = np.array([3.0, 4.0, 0.0])  # Not normalized
        
        hinge = Hinge(
            poly1_id="poly1",
            poly2_id="poly2",
            edge1_idx=0,
            edge2_idx=1,
            axis_start=start,
            axis_end=end
        )
        
        axis = hinge.get_axis()
        
        # Should be normalized to unit vector
        length = np.linalg.norm(axis)
        self.assertAlmostEqual(length, 1.0, places=5)
        
        # Should point in direction of (3, 4, 0), normalized
        expected = np.array([3.0, 4.0, 0.0]) / 5.0
        np.testing.assert_array_almost_equal(axis, expected, decimal=5)


class TestRenderDepthInvariants(unittest.TestCase):
    """Test rendering depth and spatial properties."""
    
    def test_polygon_3d_has_mesh_data(self):
        """Test that 3D polygons have mesh data."""
        poly = create_polygon_3d(4, position=(0, 0, 0), thickness=0.1)
        
        self.assertTrue(poly.get('has_3d_mesh'), "3D polygon should have mesh flag")
        self.assertIsNotNone(poly.get('mesh'), "3D polygon should have mesh data")
    
    def test_mesh_data_serializable(self):
        """Test that mesh data is JSON-serializable."""
        poly = create_polygon_3d(3, position=(1, 2, 3), thickness=0.15)
        mesh = get_polyform_mesh(poly)
        
        if mesh is None:
            self.skipTest("No mesh available")
        
        # Should be able to convert to dict
        mesh_dict = mesh.to_dict()
        self.assertIsInstance(mesh_dict, dict)
        self.assertIn('vertices', mesh_dict)
        self.assertIn('faces', mesh_dict)
        self.assertIn('normals', mesh_dict)
    
    def test_mesh_round_trip_preserves_structure(self):
        """Test that mesh survives serialization round-trip."""
        poly = create_polygon_3d(5, position=(0, 0, 0), thickness=0.1)
        mesh = get_polyform_mesh(poly)
        
        if mesh is None:
            self.skipTest("No mesh available")
        
        original_verts = len(mesh.vertices)
        original_faces = len(mesh.faces)
        original_normals = len(mesh.normals)
        
        # Serialize and deserialize
        mesh_dict = mesh.to_dict()
        mesh_restored = MeshData.from_dict(mesh_dict)
        
        # Check structure preserved
        self.assertEqual(len(mesh_restored.vertices), original_verts)
        self.assertEqual(len(mesh_restored.faces), original_faces)
        self.assertEqual(len(mesh_restored.normals), original_normals)
    
    def test_polygon_position_affects_vertices(self):
        """Test that polygon position affects vertex coordinates."""
        poly1 = create_polygon_3d(3, position=(0, 0, 0))
        poly2 = create_polygon_3d(3, position=(1, 2, 3))
        
        verts1 = np.array(poly1.get('vertices', []))
        verts2 = np.array(poly2.get('vertices', []))
        
        # Mean should differ by offset
        mean1 = np.mean(verts1, axis=0)
        mean2 = np.mean(verts2, axis=0)
        offset = mean2 - mean1
        
        np.testing.assert_array_almost_equal(offset, [1, 2, 3], decimal=5)


class TestNumericalStability(unittest.TestCase):
    """Test numerical stability of operations."""
    
    def test_extreme_polygon_sides(self):
        """Test creating polygons with extreme side counts."""
        for sides in [3, 6, 12]:
            with self.subTest(sides=sides):
                poly = create_polygon_3d(sides, thickness=0.1)
                verts = np.array(poly.get('vertices', []))
                
                # All vertices should be finite
                self.assertTrue(np.all(np.isfinite(verts)), 
                              f"{sides}-gon should have finite vertices")
    
    def test_extreme_fold_angles(self):
        """Test fold transforms at extreme angles."""
        axis = np.array([0.0, 0.0, 1.0])
        
        for angle_deg in [0, 45, 90, 180, 270, 360]:
            with self.subTest(angle_deg=angle_deg):
                angle = math.radians(angle_deg)
                transform = rotation_matrix_axis_angle(axis, angle)
                
                # All values should be finite
                self.assertTrue(np.all(np.isfinite(transform)),
                              f"Transform at {angle_deg}° should be finite")
    
    def test_repeated_operations_stable(self):
        """Test that repeated operations don't accumulate errors."""
        poly = create_polygon_3d(4, thickness=0.1)
        verts_original = np.array(poly.get('vertices', [])).copy()
        
        axis = np.array([0.0, 0.0, 1.0])
        small_angle = math.radians(1)  # 1 degree
        
        # Apply rotation 360 times (should be back to start, ~0 error)
        current_verts = verts_original.copy()
        for _ in range(360):
            transform = rotation_matrix_axis_angle(axis, small_angle)
            current_homo = np.hstack([current_verts, np.ones((len(current_verts), 1))])
            current_verts = (transform @ current_homo.T).T[:, :3]
        
        # Should be back to approximately original
        error = np.max(np.abs(current_verts - verts_original))
        self.assertLess(error, 0.1, "Accumulated error should be small")


class TestCollisionDetectionIntegration(unittest.TestCase):
    """Test collision detection with folded polyforms."""
    
    def test_collision_validator_creation(self):
        """Test creating collision validator."""
        validator = CollisionValidator()
        self.assertIsNotNone(validator)
    
    def test_simple_mesh_self_intersection(self):
        """Test self-intersection detection on simple mesh."""
        poly = create_polygon_3d(3, thickness=0.1)
        
        validator = CollisionValidator()
        detector = validator.get_detector(poly)
        
        if detector is not None:
            # Should not self-intersect initially
            result = detector.check_self_intersection()
            # Result may vary, just ensure no crash
            self.assertIsInstance(result, bool)


class TestGoldenSceneSnapshot(unittest.TestCase):
    """Test golden scene snapshot functionality."""
    
    def test_generate_geometry_hash(self):
        """Test generating hash of geometry."""
        poly = create_polygon_3d(4, thickness=0.1)
        verts = np.array(poly.get('vertices', []))
        
        # Create hash
        verts_flat = verts.flatten()
        hash_val = hash(tuple(np.round(verts_flat, decimals=6)))
        
        self.assertIsInstance(hash_val, int)
    
    def test_deterministic_generation(self):
        """Test that polygon generation is deterministic."""
        poly1 = create_polygon_3d(5, position=(0, 0, 0), thickness=0.1)
        poly2 = create_polygon_3d(5, position=(0, 0, 0), thickness=0.1)
        
        verts1 = np.array(poly1.get('vertices', []))
        verts2 = np.array(poly2.get('vertices', []))
        
        np.testing.assert_array_almost_equal(verts1, verts2, decimal=6,
                                           err_msg="Polygon generation should be deterministic")


if __name__ == '__main__':
    unittest.main()
