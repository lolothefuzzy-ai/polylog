"""
Polyform adapter module for normalizing polygon data between different generators and viewport.

Provides a single normalize_polyform() function that converts arbitrary polygon data
to a canonical format expected by the viewport and other systems.
"""

import uuid
import warnings
from typing import Any, Dict

import numpy as np


def normalize_polyform(polyform: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert arbitrary polygon data to canonical format.
    
    Normalizes field names and ensures all required fields are present with correct types.
    Handles different field names (sides/n_sides) and adds missing fields with defaults.
    
    Args:
        polyform: Input polygon dictionary with arbitrary field names
        
    Returns:
        New dictionary with canonical fields:
            id: str - unique identifier
            type: str - generator type or label
            sides: int - number of polygon sides
            vertices: list of (x,y,z) - 3D vertex positions
            position: (x,y,z) - center position
            bonds: list - connection data (empty if missing)
            original_data: dict - original input data
            
    The adapter will:
    - Convert 2D vertices to 3D by adding z=0
    - Generate IDs if missing
    - Compute position from vertices if missing
    - Handle sides/n_sides field name variants
    - Preserve any extra fields that don't conflict
    """
    result = {}
    
    # Store original data
    result['original_data'] = dict(polyform)
    
    # Required fields with normalization
    
    # ID - generate if missing
    result['id'] = polyform.get('id', str(uuid.uuid4()))
    
    # Type - use generator type or default
    result['type'] = polyform.get('type', 'unknown')
    
    # Sides - handle different field names
    sides = polyform.get('sides', polyform.get('n_sides', None))
    if sides is None:
        # Infer from vertices if available
        vertices = polyform.get('vertices', [])
        sides = len(vertices)
    result['sides'] = int(sides)
    
    # Vertices - ensure 3D
    vertices = polyform.get('vertices', [])
    vertices_3d = []
    for v in vertices:
        if isinstance(v, (list, tuple)):
            if len(v) == 2:
                vertices_3d.append((v[0], v[1], 0.0))
            else:
                vertices_3d.append(v[:3])  # Take first 3 coords if more
        else:
            warnings.warn(f"Skipping invalid vertex: {v}")
            continue
    result['vertices'] = vertices_3d
    
    # Position - compute from vertices if missing
    position = polyform.get('position', polyform.get('center', None))
    if position is None and vertices_3d:
        # Compute centroid
        position = np.mean(vertices_3d, axis=0)
        position = tuple(float(x) for x in position)
    if position is None:
        position = (0.0, 0.0, 0.0)
    result['position'] = position[:3]  # Ensure exactly 3 coordinates
    
    # Bonds - empty list if missing
    result['bonds'] = polyform.get('bonds', [])
    
    # Copy any extra fields that don't conflict with canonical ones
    for key, value in polyform.items():
        if key not in result and key != 'original_data':
            result[key] = value
            
    return result