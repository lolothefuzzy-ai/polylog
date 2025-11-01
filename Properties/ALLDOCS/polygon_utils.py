"""
Shared utility for creating polygon polyforms.
Used by multiple modules to avoid circular imports.
"""
from typing import Any, Dict, Optional

import numpy as np

try:
    from geometry3d import MeshData, extrude_polygon, extrude_polygon_with_centroid
    GEOMETRY3D_AVAILABLE = True
except ImportError:
    GEOMETRY3D_AVAILABLE = False
    MeshData = None


def create_polygon(sides: int, position=(0.0, 0.0, 0.0)) -> Dict[str, Any]:
    """
    Create a regular polygon polyform.
    
    Args:
        sides: Number of sides (must be >= 3)
        position: Center position (x, y, z)
    
    Returns:
        Polyform dict with vertices, sides, type, bonds, and position
    """
    if sides < 3:
        raise ValueError("Polygon must have at least 3 sides")
    
    edge_length = 1.0
    radius = edge_length / (2 * np.sin(np.pi / sides))
    verts = []
    
    for i in range(sides):
        ang = 2 * np.pi * i / sides
        x = position[0] + radius * np.cos(ang)
        y = position[1] + radius * np.sin(ang)
        z = position[2]
        verts.append([float(x), float(y), float(z)])
    
    poly_dict = {
        'type': 'polygon',
        'sides': int(sides),
        'vertices': verts,
        'bonds': [],
        'position': [float(position[0]), float(position[1]), float(position[2])]
    }
    
    return poly_dict


def add_3d_mesh_to_polyform(polyform: Dict[str, Any], thickness: float = 0.1,
                            use_centroid: bool = False) -> Dict[str, Any]:
    """
    Add 3D mesh data to a 2D polyform by extrusion.
    
    Args:
        polyform: Polyform dictionary with 'vertices' key
        thickness: Extrusion thickness in z direction
        use_centroid: If True, use centroid-based tri-fan for faces
    
    Returns:
        Updated polyform with 'mesh' key containing MeshData dict
    """
    if not GEOMETRY3D_AVAILABLE:
        return polyform
    
    verts = np.array(polyform.get('vertices', []))
    if len(verts) < 3:
        return polyform
    
    # Get current z position
    center_z = float(polyform.get('position', [0, 0, 0])[2])
    
    # Extrude polygon
    if use_centroid:
        mesh = extrude_polygon_with_centroid(verts, thickness, center_z)
    else:
        mesh = extrude_polygon(verts, thickness, center_z)
    
    # Store mesh data in polyform
    polyform['mesh'] = mesh.to_dict()
    polyform['has_3d_mesh'] = True
    polyform['mesh_thickness'] = float(thickness)
    
    return polyform


def create_polygon_3d(sides: int, position=(0.0, 0.0, 0.0),
                     thickness: float = 0.1, use_centroid: bool = False) -> Dict[str, Any]:
    """
    Create a regular polygon polyform with 3D mesh data.
    
    Args:
        sides: Number of sides (must be >= 3)
        position: Center position (x, y, z)
        thickness: Extrusion thickness in z direction
        use_centroid: If True, use centroid-based tri-fan for faces
    
    Returns:
        Polyform dict with vertices, sides, type, bonds, position, and mesh data
    """
    poly = create_polygon(sides, position)
    
    if GEOMETRY3D_AVAILABLE:
        poly = add_3d_mesh_to_polyform(poly, thickness, use_centroid)
    
    return poly


def get_polyform_mesh(polyform: Dict[str, Any]) -> Optional[object]:
    """
    Get MeshData object from a polyform if available.
    
    Args:
        polyform: Polyform dictionary
    
    Returns:
        MeshData object or None if not available
    """
    if not GEOMETRY3D_AVAILABLE or not polyform.get('has_3d_mesh'):
        return None
    
    mesh_dict = polyform.get('mesh')
    if mesh_dict is None:
        return None
    
    try:
        return MeshData.from_dict(mesh_dict)
    except Exception:
        return None


def update_polyform_mesh(polyform: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update or regenerate 3D mesh for a polyform based on current vertices.
    
    Args:
        polyform: Polyform dictionary
    
    Returns:
        Updated polyform
    """
    if not GEOMETRY3D_AVAILABLE:
        return polyform
    
    if polyform.get('has_3d_mesh'):
        thickness = polyform.get('mesh_thickness', 0.1)
        use_centroid = polyform.get('mesh_use_centroid', False)
        return add_3d_mesh_to_polyform(polyform, thickness, use_centroid)
    
    return polyform
