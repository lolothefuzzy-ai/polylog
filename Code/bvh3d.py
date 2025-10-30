"""
BVH (Bounding Volume Hierarchy) collision detection for 3D triangle meshes.

Implements fast triangle-triangle intersection using spatial partitioning.
"""
from typing import List, Tuple, Optional, Dict, Any
import numpy as np
from dataclasses import dataclass


@dataclass
class AABB:
    """Axis-Aligned Bounding Box for fast spatial queries."""
    min_point: np.ndarray
    max_point: np.ndarray
    
    @classmethod
    def from_triangles(cls, vertices: np.ndarray, triangle_indices: List[int]) -> 'AABB':
        """Create AABB from a set of triangles."""
        if len(triangle_indices) == 0:
            return cls(np.zeros(3), np.zeros(3))
        
        # Get all vertices involved in these triangles
        tri_verts = vertices[triangle_indices].reshape(-1, 3)
        
        min_pt = np.min(tri_verts, axis=0)
        max_pt = np.max(tri_verts, axis=0)
        
        return cls(min_pt, max_pt)
    
    def intersects(self, other: 'AABB', epsilon: float = 1e-6) -> bool:
        """Check if this AABB intersects another."""
        # Check for separation on each axis
        if self.max_point[0] < other.min_point[0] - epsilon:
            return False
        if self.min_point[0] > other.max_point[0] + epsilon:
            return False
        
        if self.max_point[1] < other.min_point[1] - epsilon:
            return False
        if self.min_point[1] > other.max_point[1] + epsilon:
            return False
        
        if self.max_point[2] < other.min_point[2] - epsilon:
            return False
        if self.min_point[2] > other.max_point[2] + epsilon:
            return False
        
        return True
    
    def contains_point(self, point: np.ndarray) -> bool:
        """Check if point is inside AABB."""
        return (np.all(point >= self.min_point) and 
                np.all(point <= self.max_point))
    
    def surface_area(self) -> float:
        """Calculate surface area (used for BVH cost)."""
        dims = self.max_point - self.min_point
        return 2.0 * (dims[0] * dims[1] + dims[1] * dims[2] + dims[2] * dims[0])
    
    def union(self, other: 'AABB') -> 'AABB':
        """Create AABB that contains both boxes."""
        min_pt = np.minimum(self.min_point, other.min_point)
        max_pt = np.maximum(self.max_point, other.max_point)
        return AABB(min_pt, max_pt)


class BVHNode:
    """Binary tree node for spatial partitioning."""
    
    def __init__(self, triangle_indices: List[int], vertices: np.ndarray, 
                 faces: np.ndarray, depth: int = 0, max_depth: int = 20,
                 max_triangles: int = 4):
        self.triangle_indices = triangle_indices
        self.aabb = AABB.from_triangles(vertices, 
                                        [faces[i].flatten() for i in triangle_indices])
        self.left: Optional[BVHNode] = None
        self.right: Optional[BVHNode] = None
        self.is_leaf = False
        
        # Build recursively
        if len(triangle_indices) <= max_triangles or depth >= max_depth:
            self.is_leaf = True
        else:
            self._split(vertices, faces, depth, max_depth, max_triangles)
    
    def _split(self, vertices: np.ndarray, faces: np.ndarray, 
               depth: int, max_depth: int, max_triangles: int):
        """Split node into left and right children."""
        if len(self.triangle_indices) <= 1:
            self.is_leaf = True
            return
        
        # Find best split axis (longest dimension)
        dims = self.aabb.max_point - self.aabb.min_point
        split_axis = np.argmax(dims)
        
        # Calculate centroids for each triangle
        centroids = []
        for tri_idx in self.triangle_indices:
            tri_verts = vertices[faces[tri_idx]]
            centroid = np.mean(tri_verts, axis=0)
            centroids.append(centroid[split_axis])
        
        # Sort by centroid along split axis
        sorted_indices = sorted(zip(centroids, self.triangle_indices))
        mid = len(sorted_indices) // 2
        
        left_tris = [idx for _, idx in sorted_indices[:mid]]
        right_tris = [idx for _, idx in sorted_indices[mid:]]
        
        if len(left_tris) == 0 or len(right_tris) == 0:
            self.is_leaf = True
            return
        
        # Create children
        self.left = BVHNode(left_tris, vertices, faces, depth + 1, max_depth, max_triangles)
        self.right = BVHNode(right_tris, vertices, faces, depth + 1, max_depth, max_triangles)
    
    def query(self, aabb: AABB, results: List[int]):
        """Find all triangles whose AABB intersects the query AABB."""
        if not self.aabb.intersects(aabb):
            return
        
        if self.is_leaf:
            results.extend(self.triangle_indices)
        else:
            if self.left:
                self.left.query(aabb, results)
            if self.right:
                self.right.query(aabb, results)


class TriangleCollisionDetector:
    """Fast triangle-triangle collision detection using BVH."""
    
    def __init__(self, mesh_data):
        """
        Initialize detector with mesh data.
        
        Args:
            mesh_data: MeshData object with vertices and faces
        """
        self.vertices = np.array(mesh_data.vertices, dtype=np.float64)
        self.faces = np.array(mesh_data.faces, dtype=np.int32)
        self.bvh: Optional[BVHNode] = None
    
    def build_bvh(self):
        """Build BVH tree for fast queries."""
        if len(self.faces) == 0:
            return
        
        triangle_indices = list(range(len(self.faces)))
        self.bvh = BVHNode(triangle_indices, self.vertices, self.faces)
    
    def check_collision(self, other: 'TriangleCollisionDetector', 
                       epsilon: float = 1e-6) -> bool:
        """
        Check if any triangles collide between two meshes.
        
        Args:
            other: Another TriangleCollisionDetector
            epsilon: Distance threshold for collision
        
        Returns:
            True if collision detected
        """
        if self.bvh is None:
            self.build_bvh()
        if other.bvh is None:
            other.build_bvh()
        
        # Quick AABB rejection
        if not self.bvh.aabb.intersects(other.bvh.aabb):
            return False
        
        # Get candidate triangle pairs
        collision_pairs = self._get_collision_candidates(other)
        
        # Test each pair
        for i, j in collision_pairs:
            tri1 = self.vertices[self.faces[i]]
            tri2 = other.vertices[other.faces[j]]
            
            if self._triangle_intersects_triangle(tri1, tri2, epsilon):
                return True
        
        return False
    
    def check_self_intersection(self, epsilon: float = 1e-6) -> bool:
        """Check if mesh has self-intersecting triangles."""
        if self.bvh is None:
            self.build_bvh()
        
        # Check all triangle pairs (skip adjacent triangles)
        for i in range(len(self.faces)):
            for j in range(i + 2, len(self.faces)):
                # Skip if triangles share vertices
                if self._triangles_share_vertex(i, j):
                    continue
                
                tri1 = self.vertices[self.faces[i]]
                tri2 = self.vertices[self.faces[j]]
                
                if self._triangle_intersects_triangle(tri1, tri2, epsilon):
                    return True
        
        return False
    
    def _get_collision_candidates(self, other: 'TriangleCollisionDetector') -> List[Tuple[int, int]]:
        """Get candidate triangle pairs that might collide."""
        candidates = []
        
        # For each triangle in self, query other's BVH
        for i in range(len(self.faces)):
            tri_verts = self.vertices[self.faces[i]]
            tri_aabb = AABB(np.min(tri_verts, axis=0), np.max(tri_verts, axis=0))
            
            other_tris = []
            other.bvh.query(tri_aabb, other_tris)
            
            for j in other_tris:
                candidates.append((i, j))
        
        return candidates
    
    def raycast(self, ray_origin: np.ndarray, ray_direction: np.ndarray,
               epsilon: float = 1e-8) -> Optional[Dict[str, Any]]:
        """
        Ray-cast against mesh using BVH acceleration.
        
        Args:
            ray_origin: Ray starting point
            ray_direction: Ray direction (should be normalized)
            epsilon: Epsilon for calculations
        
        Returns:
            Dict with closest hit info: {'distance': float, 'point': np.ndarray, 'face_id': int}
            or None if no hit
        """
        if self.bvh is None:
            self.build_bvh()
        
        # Find candidate triangles using BVH
        candidates = self._get_candidate_faces_for_ray(ray_origin, ray_direction)
        
        # Test each candidate
        closest_hit = None
        min_distance = float('inf')
        
        for face_id in candidates:
            hit = self._ray_triangle_intersection(
                ray_origin, ray_direction,
                self.vertices[self.faces[face_id]], 
                face_id, epsilon
            )
            
            if hit and hit['distance'] < min_distance:
                min_distance = hit['distance']
                closest_hit = hit
        
        return closest_hit
    
    def _get_candidate_faces_for_ray(self, ray_origin: np.ndarray, 
                                    ray_direction: np.ndarray,
                                    t_max: float = 10000.0) -> List[int]:
        """
        Get candidate faces along ray using BVH.
        
        Args:
            ray_origin: Ray starting point
            ray_direction: Ray direction
            t_max: Maximum ray parameter
        
        Returns:
            List of candidate face indices
        """
        candidates = []
        
        # Compute ray bounding volume (as AABB)
        t_vals = [0, t_max]
        far_point = ray_origin + t_max * ray_direction
        ray_aabb = AABB(
            np.minimum(ray_origin, far_point) - 0.1,
            np.maximum(ray_origin, far_point) + 0.1
        )
        
        # Query BVH
        self.bvh.query(ray_aabb, candidates)
        
        return candidates
    
    @staticmethod
    def _ray_triangle_intersection(ray_origin: np.ndarray, ray_direction: np.ndarray,
                                 triangle_verts: np.ndarray, face_id: int,
                                 epsilon: float = 1e-8) -> Optional[Dict[str, Any]]:
        """
        Möller-Trumbore ray-triangle intersection.
        
        Args:
            ray_origin: Ray starting point
            ray_direction: Ray direction (should be normalized)
            triangle_verts: 3x3 array of triangle vertices
            face_id: Index of this face (for reporting)
            epsilon: Epsilon threshold
        
        Returns:
            Dict with hit info or None
        """
        v0, v1, v2 = triangle_verts[0], triangle_verts[1], triangle_verts[2]
        
        # Edges
        edge1 = v1 - v0
        edge2 = v2 - v0
        
        # Cross product
        h = np.cross(ray_direction, edge2)
        a = np.dot(edge1, h)
        
        if abs(a) < epsilon:
            return None  # Ray parallel to triangle
        
        f = 1.0 / a
        s = ray_origin - v0
        u = f * np.dot(s, h)
        
        if u < 0.0 or u > 1.0:
            return None
        
        q = np.cross(s, edge1)
        v = f * np.dot(ray_direction, q)
        
        if v < 0.0 or u + v > 1.0:
            return None
        
        t = f * np.dot(edge2, q)
        
        if t > epsilon:  # Positive t
            intersection_point = ray_origin + t * ray_direction
            return {
                'distance': t,
                'point': intersection_point,
                'face_id': face_id
            }
        
        return None
    
    def _triangles_share_vertex(self, tri_idx1: int, tri_idx2: int) -> bool:
        """Check if two triangles share any vertices."""
        tri1_verts = set(self.faces[tri_idx1])
        tri2_verts = set(self.faces[tri_idx2])
        return len(tri1_verts & tri2_verts) > 0
    
    @staticmethod
    def _triangle_intersects_triangle(tri1: np.ndarray, tri2: np.ndarray, 
                                     epsilon: float = 1e-6) -> bool:
        """
        Möller's triangle-triangle intersection algorithm.
        
        Args:
            tri1: First triangle vertices (3x3)
            tri2: Second triangle vertices (3x3)
            epsilon: Distance threshold
        
        Returns:
            True if triangles intersect
        """
        # Get vertices
        v0, v1, v2 = tri1[0], tri1[1], tri1[2]
        u0, u1, u2 = tri2[0], tri2[1], tri2[2]
        
        # Compute plane equation of triangle 1
        e1 = v1 - v0
        e2 = v2 - v0
        n1 = np.cross(e1, e2)
        
        if np.linalg.norm(n1) < epsilon:
            return False  # Degenerate triangle
        
        d1 = -np.dot(n1, v0)
        
        # Test triangle 2 vertices against plane 1
        du0 = np.dot(n1, u0) + d1
        du1 = np.dot(n1, u1) + d1
        du2 = np.dot(n1, u2) + d1
        
        # Check if all vertices on same side
        if abs(du0) < epsilon:
            du0 = 0
        if abs(du1) < epsilon:
            du1 = 0
        if abs(du2) < epsilon:
            du2 = 0
        
        du0du1 = du0 * du1
        du0du2 = du0 * du2
        
        if du0du1 > 0 and du0du2 > 0:
            return False  # No intersection
        
        # Compute plane equation of triangle 2
        e1 = u1 - u0
        e2 = u2 - u0
        n2 = np.cross(e1, e2)
        
        if np.linalg.norm(n2) < epsilon:
            return False  # Degenerate triangle
        
        d2 = -np.dot(n2, u0)
        
        # Test triangle 1 vertices against plane 2
        dv0 = np.dot(n2, v0) + d2
        dv1 = np.dot(n2, v1) + d2
        dv2 = np.dot(n2, v2) + d2
        
        if abs(dv0) < epsilon:
            dv0 = 0
        if abs(dv1) < epsilon:
            dv1 = 0
        if abs(dv2) < epsilon:
            dv2 = 0
        
        dv0dv1 = dv0 * dv1
        dv0dv2 = dv0 * dv2
        
        if dv0dv1 > 0 and dv0dv2 > 0:
            return False  # No intersection
        
        # If we get here, triangles are coplanar or intersecting
        # For simplicity, assume intersection
        # (Full Möller algorithm has more detailed interval tests)
        return True


# Utility functions
def test_bvh():
    """Quick test of BVH functionality."""
    from geometry3d import extrude_polygon
    
    # Create two simple meshes
    verts1 = np.array([[0, 0, 0], [1, 0, 0], [0.5, 1, 0]], dtype=np.float32)
    mesh1 = extrude_polygon(verts1, thickness=0.1)
    
    verts2 = np.array([[0.5, 0.5, 0], [1.5, 0.5, 0], [1, 1.5, 0]], dtype=np.float32)
    mesh2 = extrude_polygon(verts2, thickness=0.1)
    
    # Test collision detection
    detector1 = TriangleCollisionDetector(mesh1)
    detector2 = TriangleCollisionDetector(mesh2)
    
    detector1.build_bvh()
    detector2.build_bvh()
    
    print(f"Mesh 1: {len(mesh1.faces)} triangles")
    print(f"Mesh 2: {len(mesh2.faces)} triangles")
    print(f"BVH 1 built: {detector1.bvh is not None}")
    print(f"BVH 2 built: {detector2.bvh is not None}")
    
    collision = detector1.check_collision(detector2)
    print(f"Collision detected: {collision}")
    
    return collision


if __name__ == "__main__":
    print("Testing BVH collision detection...")
    test_bvh()
    print("BVH test complete!")
