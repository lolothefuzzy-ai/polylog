"""
Simplified random assembly generator for visualization testing.
"""

import numpy as np
from typing import List, Dict, Any

class RandomAssemblyGenerator:
    def __init__(self):
        self.rng = np.random.default_rng()
    
    def generate_random_assembly(self, 
                               num_polyforms: int = 1,
                               allow_types: List[int] = None,
                               use_3d: bool = True) -> List[Dict[str, Any]]:
        """
        Generate random polyform assemblies.
        
        Args:
            num_polyforms: Number of polyforms to generate
            allow_types: List of allowed vertex counts (e.g. [3,4,5] for triangle/square/pentagon)
            use_3d: Whether to generate 3D coordinates
            
        Returns:
            List of polyform dictionaries with vertices and metadata
        """
        if allow_types is None:
            allow_types = [3, 4, 5, 6]  # Default to basic shapes
            
        polyforms = []
        
        for _ in range(num_polyforms):
            # Choose random number of vertices
            n_vertices = self.rng.choice(allow_types)
            
            # Generate vertices around unit circle
            angles = np.linspace(0, 2*np.pi, n_vertices, endpoint=False)
            
            # Basic 2D vertices
            vertices = np.column_stack([
                np.cos(angles),
                np.sin(angles)
            ])
            
            if use_3d:
                # Add random z-coordinates for 3D
                z = self.rng.uniform(-0.2, 0.2, size=n_vertices)
                vertices = np.column_stack([vertices, z])
            
            # Add some random variation to vertex positions
            vertices += self.rng.normal(0, 0.1, vertices.shape)
            
            # Create polyform dictionary
            polyform = {
                'vertices': vertices.tolist(),
                'n_sides': n_vertices,
                'center': [0, 0, 0] if use_3d else [0, 0],
                'type': f'{n_vertices}-gon'
            }
            
            polyforms.append(polyform)
            
        return polyforms