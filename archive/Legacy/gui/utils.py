"""
GUI utilities for polygon generation and rendering integration.

Provides adapters and helpers for converting between:
- GUI parameters (sides, complexity, symmetry)
- Polygon generator parameters
- Renderable vertex/face data for OpenGL
"""

from typing import Any, Dict, List, Tuple

import numpy as np


def gui_params_to_generator_params(
    sides: int,
    complexity: float,
    symmetry: float
) -> Dict[str, Any]:
    """
    Convert GUI slider parameters to polygon generator parameters.
    
    Args:
        sides: Number of polygon sides (3-12)
        complexity: Geometry complexity (0-1)
        symmetry: Symmetry level (0-1)
    
    Returns:
        Dictionary of generator parameters
    """
    # Map GUI parameters to generator-friendly values
    params = {
        'sides': max(3, min(12, int(sides))),
        'complexity': max(0.0, min(1.0, float(complexity))),
        'symmetry': max(0.0, min(1.0, float(symmetry))),
    }
    
    # Complexity affects size/scale
    scale = 0.5 + (complexity * 1.0)  # 0.5 to 1.5
    params['scale'] = scale
    
    # Symmetry affects regularity
    params['is_regular'] = symmetry > 0.5
    
    return params


def extract_vertices_3d(polygon_data: Dict[str, Any]) -> List[Tuple[float, float, float]]:
    """
    Extract 3D vertices from polygon data dictionary.
    
    Args:
        polygon_data: Polygon dictionary from generator
    
    Returns:
        List of (x, y, z) tuples
    """
    vertices = polygon_data.get('vertices', [])
    if not vertices:
        return []
    
    # Ensure 3D format
    vertices_3d = []
    for v in vertices:
        if isinstance(v, (list, tuple)):
            if len(v) == 2:
                vertices_3d.append((float(v[0]), float(v[1]), 0.0))
            elif len(v) >= 3:
                vertices_3d.append((float(v[0]), float(v[1]), float(v[2])))
        else:
            # Skip invalid vertices
            continue
    
    return vertices_3d


def get_polygon_color(polygon_id: int, style: str = 'branding') -> Tuple[float, float, float]:
    """
    Get color for polygon based on ID using Polylog branding colors.
    
    Args:
        polygon_id: Index or ID of polygon
        style: Color scheme ('branding', 'rainbow', 'grayscale')
    
    Returns:
        RGB tuple (0.0-1.0 range)
    """
    if style == 'branding':
        # Use Polylog brand colors
        colors = [
            (1.0, 0.0, 0.0),    # Red (primary)
            (0.0, 0.0, 1.0),    # Blue (secondary)
            (0.8, 0.0, 0.8),    # Purple (tertiary)
            (0.0, 1.0, 0.0),    # Green (accent)
            (1.0, 1.0, 0.0),    # Yellow
            (1.0, 0.5, 0.0),    # Orange
            (0.5, 0.0, 1.0),    # Violet
            (0.0, 1.0, 1.0),    # Cyan
        ]
    elif style == 'rainbow':
        # Rainbow gradient
        hue = (polygon_id * 0.618) % 1.0  # Golden ratio distribution
        colors = [hsv_to_rgb(hue, 1.0, 1.0)]
        return colors[0]
    elif style == 'grayscale':
        gray = 0.3 + (polygon_id * 0.1) % 0.7
        return (gray, gray, gray)
    else:
        colors = [
            (1.0, 0.0, 0.0),
            (0.0, 0.0, 1.0),
            (0.8, 0.0, 0.8),
        ]
    
    return colors[polygon_id % len(colors)]


def hsv_to_rgb(h: float, s: float, v: float) -> Tuple[float, float, float]:
    """
    Convert HSV color to RGB.
    
    Args:
        h: Hue (0-1)
        s: Saturation (0-1)
        v: Value (0-1)
    
    Returns:
        RGB tuple
    """
    import colorsys
    return colorsys.hsv_to_rgb(h, s, v)


def calculate_polygon_center(vertices: List[Tuple[float, float, float]]) -> Tuple[float, float, float]:
    """
    Calculate center point of polygon.
    
    Args:
        vertices: List of (x, y, z) tuples
    
    Returns:
        Center point (x, y, z)
    """
    if not vertices:
        return (0.0, 0.0, 0.0)
    
    vertices_array = np.array(vertices)
    center = vertices_array.mean(axis=0)
    return tuple(float(x) for x in center)


def scale_polygon_vertices(
    vertices: List[Tuple[float, float, float]],
    scale: float,
    center: Tuple[float, float, float] = None
) -> List[Tuple[float, float, float]]:
    """
    Scale polygon vertices around a center point.
    
    Args:
        vertices: List of (x, y, z) tuples
        scale: Scale factor
        center: Center point (calculated if None)
    
    Returns:
        Scaled vertices
    """
    if center is None:
        center = calculate_polygon_center(vertices)
    
    center_array = np.array(center)
    vertices_array = np.array(vertices)
    
    # Scale around center
    scaled = (vertices_array - center_array) * scale + center_array
    
    return [tuple(float(x) for x in v) for v in scaled]


def create_polygon_mesh(vertices: List[Tuple[float, float, float]]) -> Dict[str, Any]:
    """
    Create a mesh representation for OpenGL rendering.
    
    Args:
        vertices: List of (x, y, z) tuples representing polygon outline
    
    Returns:
        Dictionary with 'vertices' and 'faces' for rendering
    """
    if len(vertices) < 3:
        return {'vertices': [], 'faces': []}
    
    # For 2D polygons, create simple triangle fan mesh
    # Vertices are in order around the perimeter
    
    mesh_verts = []
    mesh_faces = []
    
    # Add perimeter vertices
    for v in vertices:
        mesh_verts.append(v)
    
    # Create triangles from center using triangle fan
    num_verts = len(vertices)
    
    # Create face indices (triangle fan from first vertex)
    for i in range(1, num_verts - 1):
        mesh_faces.append((0, i, i + 1))
    
    return {
        'vertices': mesh_verts,
        'faces': mesh_faces,
        'vertex_count': len(mesh_verts),
        'face_count': len(mesh_faces)
    }


def validate_polygon_data(polygon_data: Dict[str, Any]) -> bool:
    """
    Validate polygon data structure.
    
    Args:
        polygon_data: Polygon dictionary
    
    Returns:
        True if valid, False otherwise
    """
    required_keys = {'sides', 'vertices', 'position'}
    
    if not isinstance(polygon_data, dict):
        return False
    
    # Check required keys
    if not required_keys.issubset(polygon_data.keys()):
        return False
    
    # Validate sides
    sides = polygon_data.get('sides')
    if not isinstance(sides, int) or sides < 3 or sides > 12:
        return False
    
    # Validate vertices
    vertices = polygon_data.get('vertices', [])
    if not isinstance(vertices, (list, tuple)) or len(vertices) != sides:
        return False
    
    # Validate position
    position = polygon_data.get('position')
    if not isinstance(position, (list, tuple)) or len(position) != 3:
        return False
    
    return True


def format_polygon_for_display(polygon_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format polygon data for GUI display.
    
    Args:
        polygon_data: Raw polygon dictionary
    
    Returns:
        Formatted display data
    """
    if not validate_polygon_data(polygon_data):
        return None
    
    vertices_3d = extract_vertices_3d(polygon_data)
    mesh = create_polygon_mesh(vertices_3d)
    
    return {
        'sides': polygon_data.get('sides'),
        'vertices': vertices_3d,
        'mesh': mesh,
        'position': tuple(polygon_data.get('position')),
        'rotation': polygon_data.get('rotation', 0.0),
        'original_data': polygon_data
    }
