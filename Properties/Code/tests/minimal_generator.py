"""
Quick fix for RandomPolyformGenerator
Fixes the generation_stats attribute issue
"""

import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


class DistributionMode(Enum):
    """How polyforms are distributed in 3D space."""
    UNIFORM = "uniform"           # Random positions in bounded box
    CLUSTERED = "clustered"       # Groups of polyforms
    GRID = "grid"                # Organized grid layout
    GAUSSIAN = "gaussian"         # Normal distribution around center
    SHELL = "shell"               # On surface of sphere/shell
    LAYERED = "layered"           # Vertical layers


class ShapeVariety(Enum):
    """Types of polyforms to generate."""
    REGULAR_ONLY = "regular"      # Only regular polygons (fast)
    PERTURBED = "perturbed"       # Regular + slight perturbations
    STAR = "star"                 # Star-shaped polygons
    CONCAVE = "concave"           # Concave polygons
    IRREGULAR = "irregular"       # Fully random (challenging)
    MIXED = "mixed"               # Mix of all types


@dataclass
class GenerationParams:
    """Parameters for polyform generation."""
    n: int = 100
    distribution: DistributionMode = DistributionMode.UNIFORM
    shape_variety: ShapeVariety = ShapeVariety.REGULAR_ONLY
    
    # Spatial bounds
    bounds_x: Tuple[float, float] = (-50.0, 50.0)
    bounds_y: Tuple[float, float] = (-50.0, 50.0)
    bounds_z: Tuple[float, float] = (-10.0, 10.0)
    
    # Polygon properties
    min_sides: int = 3
    max_sides: int = 8
    avg_size: float = 1.0
    size_variation: float = 0.3
    
    # Clustering
    cluster_count: int = 5
    cluster_radius: float = 10.0
    
    # Perturbation (for non-regular shapes)
    perturbation_strength: float = 0.15
    
    # Seed for reproducibility
    seed: Optional[int] = None


class RandomPolyformGenerator:
    """Minimal version for testing."""
    
    def __init__(self, params: Optional[GenerationParams] = None):
        """Initialize generator with parameters."""
        self.params = params or GenerationParams()
        
        if self.params.seed is not None:
            np.random.seed(self.params.seed)
        
        # State tracking
        self.generated_count = 0
        self.polyforms: List[Dict[str, Any]] = []
        self._generation_stats = {
            'total_generated': 0,
            'total_time': 0.0,
            'success_count': 0,
            'failure_count': 0,
            'by_shape_type': {},
            'generation_time': 0.0
        }
    
    def generate_batch(self, n: Optional[int] = None) -> List[Dict[str, Any]]:
        """Generate a batch of random polyforms."""
        start = time.perf_counter()
        
        n = n or self.params.n
        polyforms = []
        
        # Get spatial positions
        positions = self._generate_positions(n)
        
        # Generate polyforms with varied geometries
        for i, pos in enumerate(positions):
            poly = self._generate_single_polyform(i, pos)
            polyforms.append(poly)
            self.generated_count += 1
        
        elapsed = time.perf_counter() - start
        self._generation_stats['total_generated'] = self.generated_count
        self._generation_stats['generation_time'] = elapsed
        
        return polyforms
    
    def _generate_positions(self, n: int) -> np.ndarray:
        """Generate n spatial positions based on distribution mode."""
        return self._generate_uniform_positions(n)
    
    def _generate_uniform_positions(self, n: int) -> np.ndarray:
        """Random positions in bounded box."""
        positions = np.random.uniform(
            low=[self.params.bounds_x[0], self.params.bounds_y[0], self.params.bounds_z[0]],
            high=[self.params.bounds_x[1], self.params.bounds_y[1], self.params.bounds_z[1]],
            size=(n, 3)
        )
        return positions
    
    def _generate_single_polyform(self, poly_id: int, position: np.ndarray) -> Dict[str, Any]:
        """Generate a single random polyform."""
        vertices = self._generate_regular_polygon(position)
        sides = len(vertices)
        shape_type = self.params.shape_variety.value
        
        self._generation_stats['by_shape_type'][shape_type] = \
            self._generation_stats['by_shape_type'].get(shape_type, 0) + 1
        
        polyform = {
            'id': f'rand_{self.generated_count:06d}',
            'type': 'random_polygon',
            'sides': sides,
            'vertices': vertices.tolist(),
            'position': position.tolist(),
            'bonds': [],
            'shape_variety': shape_type,
            'size': float(self.params.avg_size * (1 + np.random.normal(0, self.params.size_variation))),
        }
        
        self.polyforms.append(polyform)
        return polyform
    
    def _generate_regular_polygon(self, center: np.ndarray) -> np.ndarray:
        """Generate regular polygon."""
        sides = np.random.randint(self.params.min_sides, self.params.max_sides + 1)
        size = self.params.avg_size * (1 + np.random.normal(0, self.params.size_variation))
        radius = size / (2 * np.sin(np.pi / sides))
        
        angles = np.linspace(0, 2 * np.pi, sides, endpoint=False)
        x = center[0] + radius * np.cos(angles)
        y = center[1] + radius * np.sin(angles)
        z = np.full(sides, center[2])
        
        return np.column_stack([x, y, z])
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get generation statistics."""
        return {
            'total_generated': self.generated_count,
            'polyforms_created': len(self.polyforms),
            'distribution': self.params.distribution.value,
            'shape_variety': self.params.shape_variety.value,
            'by_shape_type': self._generation_stats['by_shape_type'],
            'generation_time_ms': self._generation_stats['generation_time'] * 1000,
        }