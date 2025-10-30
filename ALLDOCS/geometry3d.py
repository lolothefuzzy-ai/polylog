"""
3D Geometry utilities for mesh generation, extrusion, and normal calculation.

This module provides helpers for converting 2D polygons to 3D meshes with proper
face topology, normals, and extrusion operations.
"""
from typing import List, Tuple, Dict, Any, Optional
import numpy as np


class MeshData:
    """Container for 3D mesh data with vertices, faces, and normals."""
    
    def __init__(self, vertices: np.ndarray, faces: np.ndarray, normals: Optional[np.ndarray] = None):
        """
        Initialize mesh data.
        
        Args:
            vertices: Nx3 array of vertex positions
            faces: Mx3 array of triangle face indices
            normals: Nx3 array of vertex normals (optional, will be computed if None)
        """
        self.vertices = np.array(vertices, dtype=np.float32)
        self.faces = np.array(faces, dtype=np.int32)
        
        if normals is None:
            self.normals = compute_vertex_normals(self.vertices, self.faces)
        else:
            self.normals = np.array(normals, dtype=np.float32)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'vertices': self.vertices.tolist(),
            'faces': self.faces.tolist(),
            'normals': self.normals.tolist()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MeshData':
        """Create MeshData from dictionary."""
        return cls(
            vertices=np.array(data['vertices']),
            faces=np.array(data['faces']),
            normals=np.array(data.get('normals'))
        )


def tri_fan_from_polygon(vertices: np.ndarray) -> np.ndarray:
    """
    Generate triangle fan faces from a polygon using centroid.
    
    Args:
        vertices: Nx3 array of polygon vertices (assumes planar, ordered)
    
    Returns:
        Mx3 array of triangle face indices
    """
    n = len(vertices)
    if n < 3:
        return np.array([], dtype=np.int32).reshape(0, 3)
    
    # Centroid is vertex 0, original vertices are 1..n
    faces = []
    for i in range(n):
        faces.append([0, i + 1, ((i + 1) % n) + 1])
    
    return np.array(faces, dtype=np.int32)


def compute_face_normals(vertices: np.ndarray, faces: np.ndarray) -> np.ndarray:
    """
    Compute face normals for a mesh.
    
    Args:
        vertices: Nx3 array of vertex positions
        faces: Mx3 array of triangle face indices
    
    Returns:
        Mx3 array of face normals (unit vectors)
    """
    if len(faces) == 0:
        return np.array([], dtype=np.float32).reshape(0, 3)
    
    v0 = vertices[faces[:, 0]]
    v1 = vertices[faces[:, 1]]
    v2 = vertices[faces[:, 2]]
    
    # Cross product of two edges
    edge1 = v1 - v0
    edge2 = v2 - v0
    normals = np.cross(edge1, edge2)
    
    # Normalize
    lengths = np.linalg.norm(normals, axis=1, keepdims=True)
    lengths = np.where(lengths > 1e-10, lengths, 1.0)  # Avoid division by zero
    normals = normals / lengths
    
    return normals.astype(np.float32)


def compute_vertex_normals(vertices: np.ndarray, faces: np.ndarray) -> np.ndarray:
    """
    Compute smooth vertex normals by averaging adjacent face normals.
    
    Args:
        vertices: Nx3 array of vertex positions
        faces: Mx3 array of triangle face indices
    
    Returns:
        Nx3 array of vertex normals (unit vectors)
    """
    n_verts = len(vertices)
    vertex_normals = np.zeros((n_verts, 3), dtype=np.float32)
    
    if len(faces) == 0:
        return vertex_normals
    
    # Get face normals
    face_normals = compute_face_normals(vertices, faces)
    
    # Accumulate face normals to vertices
    for i, face in enumerate(faces):
        for vid in face:
            vertex_normals[vid] += face_normals[i]
    
    # Normalize
    lengths = np.linalg.norm(vertex_normals, axis=1, keepdims=True)
    lengths = np.where(lengths > 1e-10, lengths, 1.0)
    vertex_normals = vertex_normals / lengths
    
    return vertex_normals.astype(np.float32)


def extrude_polygon(vertices_2d: np.ndarray, thickness: float = 0.1, 
                   center_z: float = 0.0) -> MeshData:
    """
    Extrude a 2D polygon into a 3D mesh with thickness.
    
    Creates a prism by:
    1. Creating top and bottom faces from the 2D polygon
    2. Connecting edges with quads (split into triangles)
    
    Args:
        vertices_2d: Nx2 or Nx3 array of 2D polygon vertices (z ignored if present)
        thickness: Extrusion thickness in z direction
        center_z: Z-coordinate of the center plane
    
    Returns:
        MeshData with extruded mesh
    """
    if len(vertices_2d) < 3:
        # Return empty mesh
        return MeshData(np.zeros((0, 3)), np.zeros((0, 3), dtype=np.int32))
    
    # Convert to 2D if needed
    if vertices_2d.shape[1] == 3:
        verts_2d = vertices_2d[:, :2]
    else:
        verts_2d = vertices_2d
    
    n = len(verts_2d)
    half_thick = thickness / 2.0
    
    # Create top and bottom vertices
    top_z = center_z + half_thick
    bottom_z = center_z - half_thick
    
    vertices = []
    # Bottom face vertices (0..n-1)
    for v in verts_2d:
        vertices.append([v[0], v[1], bottom_z])
    
    # Top face vertices (n..2n-1)
    for v in verts_2d:
        vertices.append([v[0], v[1], top_z])
    
    vertices = np.array(vertices, dtype=np.float32)
    
    # Create faces
    faces = []
    
    # Bottom face (pointing down: clockwise from below)
    for i in range(1, n - 1):
        faces.append([0, i + 1, i])
    
    # Top face (pointing up: counter-clockwise from above)
    for i in range(1, n - 1):
        faces.append([n, n + i, n + i + 1])
    
    # Side faces (quads split into two triangles each)
    for i in range(n):
        next_i = (i + 1) % n
        bottom_i = i
        bottom_next = next_i
        top_i = n + i
        top_next = n + next_i
        
        # Quad: bottom_i, bottom_next, top_next, top_i
        # Triangle 1: bottom_i, bottom_next, top_i
        faces.append([bottom_i, bottom_next, top_i])
        # Triangle 2: bottom_next, top_next, top_i
        faces.append([bottom_next, top_next, top_i])
    
    faces = np.array(faces, dtype=np.int32)
    
    return MeshData(vertices, faces)


def extrude_polygon_with_centroid(vertices_2d: np.ndarray, thickness: float = 0.1,
                                 center_z: float = 0.0) -> MeshData:
    """
    Extrude a 2D polygon using centroid-based tri-fan approach.
    
    Similar to extrude_polygon but uses centroid vertices for top/bottom faces.
    This can be useful for non-convex polygons or visual variety.
    
    Args:
        vertices_2d: Nx2 or Nx3 array of 2D polygon vertices
        thickness: Extrusion thickness in z direction
        center_z: Z-coordinate of the center plane
    
    Returns:
        MeshData with extruded mesh
    """
    if len(vertices_2d) < 3:
        return MeshData(np.zeros((0, 3)), np.zeros((0, 3), dtype=np.int32))
    
    # Convert to 2D if needed
    if vertices_2d.shape[1] == 3:
        verts_2d = vertices_2d[:, :2]
    else:
        verts_2d = vertices_2d
    
    n = len(verts_2d)
    half_thick = thickness / 2.0
    
    # Calculate centroid
    centroid_2d = np.mean(verts_2d, axis=0)
    
    top_z = center_z + half_thick
    bottom_z = center_z - half_thick
    
    vertices = []
    
    # Bottom centroid (index 0)
    vertices.append([centroid_2d[0], centroid_2d[1], bottom_z])
    
    # Bottom face vertices (1..n)
    for v in verts_2d:
        vertices.append([v[0], v[1], bottom_z])
    
    # Top centroid (index n+1)
    vertices.append([centroid_2d[0], centroid_2d[1], top_z])
    
    # Top face vertices (n+2..2n+1)
    for v in verts_2d:
        vertices.append([v[0], v[1], top_z])
    
    vertices = np.array(vertices, dtype=np.float32)
    
    # Create faces
    faces = []
    
    # Bottom face (tri-fan from centroid)
    for i in range(n):
        next_i = (i + 1) % n
        faces.append([0, i + 2, next_i + 1])
    
    # Top face (tri-fan from centroid)
    top_center = n + 1
    for i in range(n):
        next_i = (i + 1) % n
        faces.append([top_center, top_center + i + 1, top_center + next_i + 1])
    
    # Side faces
    for i in range(n):
        next_i = (i + 1) % n
        bottom_i = i + 1
        bottom_next = next_i + 1
        top_i = n + 2 + i
        top_next = n + 2 + next_i
        
        faces.append([bottom_i, bottom_next, top_i])
        faces.append([bottom_next, top_next, top_i])
    
    faces = np.array(faces, dtype=np.int32)
    
    return MeshData(vertices, faces)


def transform_mesh(mesh: MeshData, matrix: np.ndarray) -> MeshData:
    """
    Transform a mesh by a 4x4 transformation matrix.
    
    Args:
        mesh: Input MeshData
        matrix: 4x4 transformation matrix
    
    Returns:
        New MeshData with transformed vertices and normals
    """
    # Transform vertices (homogeneous coordinates)
    verts_homo = np.hstack([mesh.vertices, np.ones((len(mesh.vertices), 1))])
    verts_transformed = (matrix @ verts_homo.T).T[:, :3]
    
    # Transform normals (use upper 3x3, no translation)
    rotation = matrix[:3, :3]
    normals_transformed = (rotation @ mesh.normals.T).T
    
    # Re-normalize normals
    lengths = np.linalg.norm(normals_transformed, axis=1, keepdims=True)
    lengths = np.where(lengths > 1e-10, lengths, 1.0)
    normals_transformed = normals_transformed / lengths
    
    return MeshData(verts_transformed, mesh.faces.copy(), normals_transformed)


def rotation_matrix_axis_angle(axis: np.ndarray, angle: float) -> np.ndarray:
    """
    Create a 4x4 rotation matrix from axis and angle (Rodrigues' formula).
    
    Args:
        axis: 3D rotation axis (will be normalized)
        angle: Rotation angle in radians
    
    Returns:
        4x4 transformation matrix
    """
    axis = np.array(axis, dtype=np.float64)
    axis = axis / (np.linalg.norm(axis) + 1e-10)
    
    cos_a = np.cos(angle)
    sin_a = np.sin(angle)
    t = 1.0 - cos_a
    
    x, y, z = axis
    
    rot = np.array([
        [t*x*x + cos_a,    t*x*y - sin_a*z,  t*x*z + sin_a*y,  0.0],
        [t*x*y + sin_a*z,  t*y*y + cos_a,    t*y*z - sin_a*x,  0.0],
        [t*x*z - sin_a*y,  t*y*z + sin_a*x,  t*z*z + cos_a,    0.0],
        [0.0,              0.0,              0.0,              1.0]
    ], dtype=np.float64)
    
    return rot


def get_mesh_bounds(mesh: MeshData) -> Tuple[np.ndarray, np.ndarray]:
    """
    Get axis-aligned bounding box of a mesh.
    
    Args:
        mesh: Input MeshData
    
    Returns:
        Tuple of (min_point, max_point) as 3D arrays
    """
    if len(mesh.vertices) == 0:
        return np.zeros(3), np.zeros(3)
    
    min_pt = np.min(mesh.vertices, axis=0)
    max_pt = np.max(mesh.vertices, axis=0)
    
    return min_pt, max_pt


def ray_triangle_intersection(
    ray_origin: np.ndarray, 
    ray_dir: np.ndarray,
    v0: np.ndarray, 
    v1: np.ndarray, 
    v2: np.ndarray
) -> Optional[Tuple[float, np.ndarray]]:
    """
    Möller-Trumbore ray-triangle intersection algorithm.
    
    Args:
        ray_origin: Ray origin point (3D)
        ray_dir: Ray direction (3D, should be normalized)
        v0, v1, v2: Triangle vertices (3D)
    
    Returns:
        (distance, hit_point) if intersection occurs, None otherwise
    """
    epsilon = 1e-6
    
    # Ensure inputs are numpy arrays
    ray_origin = np.asarray(ray_origin, dtype=np.float64)
    ray_dir = np.asarray(ray_dir, dtype=np.float64)
    v0 = np.asarray(v0, dtype=np.float64)
    v1 = np.asarray(v1, dtype=np.float64)
    v2 = np.asarray(v2, dtype=np.float64)
    
    # Compute edge vectors
    edge1 = v1 - v0
    edge2 = v2 - v0
    
    # Compute determinant
    h = np.cross(ray_dir, edge2)
    a = np.dot(edge1, h)
    
    # Ray parallel to triangle
    if abs(a) < epsilon:
        return None
    
    f = 1.0 / a
    s = ray_origin - v0
    u = f * np.dot(s, h)
    
    # Intersection outside triangle
    if u < 0.0 or u > 1.0:
        return None
    
    q = np.cross(s, edge1)
    v = f * np.dot(ray_dir, q)
    
    # Intersection outside triangle
    if v < 0.0 or u + v > 1.0:
        return None
    
    # Compute intersection distance
    t = f * np.dot(edge2, q)
    
    # Ray intersection exists
    if t > epsilon:
        hit_point = ray_origin + t * ray_dir
        return (float(t), hit_point)
    
    # Line intersection but not ray
    return None


def screen_to_ray(
    screen_x: int, screen_y: int,
    viewport_width: int, viewport_height: int,
    view_matrix: np.ndarray, 
    proj_matrix: np.ndarray
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Convert screen coordinates to world-space ray.
    
    Args:
        screen_x, screen_y: Screen pixel coordinates
        viewport_width, viewport_height: Viewport dimensions
        view_matrix: 4x4 view matrix
        proj_matrix: 4x4 projection matrix
    
    Returns:
        (ray_origin, ray_direction) both as 3D numpy arrays
    """
    # Normalize screen coords to [-1, 1] (NDC)
    x_ndc = (2.0 * screen_x) / viewport_width - 1.0
    y_ndc = 1.0 - (2.0 * screen_y) / viewport_height  # Flip Y
    
    # Compute inverse matrices
    inv_proj = np.linalg.inv(proj_matrix)
    inv_view = np.linalg.inv(view_matrix)
    
    # Near and far points in clip space
    near_point_clip = np.array([x_ndc, y_ndc, -1.0, 1.0])
    far_point_clip = np.array([x_ndc, y_ndc, 1.0, 1.0])
    
    # Transform to world space
    near_point_world = inv_proj @ near_point_clip
    near_point_world /= near_point_world[3]  # Perspective divide
    near_point_world = inv_view @ near_point_world
    near_point_world /= near_point_world[3]
    
    far_point_world = inv_proj @ far_point_clip
    far_point_world /= far_point_world[3]
    far_point_world = inv_view @ far_point_world
    far_point_world /= far_point_world[3]
    
    # Extract 3D coordinates
    ray_origin = near_point_world[:3]
    ray_dir = far_point_world[:3] - near_point_world[:3]
    
    # Normalize direction
    ray_dir = ray_dir / (np.linalg.norm(ray_dir) + 1e-10)
    
    return (ray_origin, ray_dir)
