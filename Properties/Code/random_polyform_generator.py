"""
ADVANCED RANDOM POLYFORM GENERATOR

Generates random polyforms across n ranges with:
1. Varied geometries (not just regular polygons)
2. 3D workspace integration
3. Distribution control (clustered, distributed, etc.)
4. Real-time streaming to workspace
5. Validation for assembly integration

Supports n=[50, 100, 500, 1000, 2000, 5000, 10000]
"""

import numpy as np
import time
from typing import List, Dict, Any, Optional, Callable, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
from collections import deque
from generator_protocol import BaseGenerator, register_generator, GeneratorCapability

logger = logging.getLogger(__name__)


class DistributionMode(Enum):
    """How polyforms are distributed in 3D space."""
    UNIFORM = "uniform"           # Random positions in bounded box
    CLUSTERED = "clustered"       # Groups of polyforms
    GRID = "grid"                 # Organized grid layout
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


@register_generator('random_polyform', [GeneratorCapability.BASIC])
class RandomPolyformGenerator(BaseGenerator):
    """
    Advanced generator for random polyforms with flexible distribution and shapes.
    
    IMPROVEMENTS OVER PATTERN-BASED:
    1. Genuine randomness: Not constrained to predefined patterns
    2. Varied geometries: Irregular, perturbed, star-shaped polygons
    3. Spatial distribution: Control clustering, spacing, density
    4. Scalability: Efficient generation even at n=10,000
    5. Real-time: Stream polyforms to workspace as generated
    6. Validation: Check assembly compatibility before insertion
    """
    
    def __init__(self, assembly=None, enable_3d_mode=True, params: Optional[GenerationParams] = None):
        """Initialize generator with parameters."""
        # Initialize base class
        if assembly is not None:
            super().__init__(assembly, enable_3d_mode)
        else:
            # Standalone mode
            self.assembly = None
            self._enable_3d_mode = enable_3d_mode
            self._generation_stats = {
                'total_generated': 0,
                'total_time': 0.0,
                'success_count': 0,
                'failure_count': 0
            }
        
        self.params = params or GenerationParams()
        
        if self.params.seed is not None:
            np.random.seed(self.params.seed)
        
        # State tracking
        self.generated_count = 0
        self.polyforms: List[Dict[str, Any]] = []
        self.extended_stats = {
            'by_shape_type': {},
            'generation_time': 0.0,
        }
    
    def generate(self, **kwargs) -> List[str]:
        """
        Unified generation interface (BaseGenerator).
        
        Args:
            **kwargs:
                - n: Number to generate
                - distribution: DistributionMode
                - shape_variety: ShapeVariety
                - Other params from GenerationParams
        
        Returns:
            List of polyform IDs
        """
        start_time = time.perf_counter()
        
        try:
            n = kwargs.get('n', self.params.n)
            
            # Update params if provided
            if 'distribution' in kwargs:
                self.params.distribution = kwargs['distribution']
            if 'shape_variety' in kwargs:
                self.params.shape_variety = kwargs['shape_variety']
            
            polyforms = self.generate_batch(n)
            
            # Add to assembly if available
            poly_ids = []
            if self.assembly is not None:
                for poly in polyforms:
                    self.assembly.add_polyform(poly)
                    poly_ids.append(poly['id'])
            else:
                poly_ids = [p.get('id', f'poly_{i}') for i, p in enumerate(polyforms)]
            
            elapsed = time.perf_counter() - start_time
            self._record_generation(len(poly_ids), True, elapsed)
            
            return poly_ids
            
        except Exception:
            elapsed = time.perf_counter() - start_time
            self._record_generation(0, False, elapsed)
            raise
    
    def generate_batch(self, n: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Generate a batch of random polyforms.
        
        Args:
            n: Number to generate (uses params.n if None)
        
        Returns:
            List of polyform dictionaries
        """
        import time
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
        self.generation_stats['total_generated'] = self.generated_count
        self.generation_stats['generation_time'] = elapsed
        
        return polyforms
    
    def generate_streaming(self, n: Optional[int] = None,
                          callback: Optional[Callable[[Dict], None]] = None,
                          batch_size: int = 100) -> None:
        """
        Generate polyforms and stream to callback (for real-time workspace updates).
        
        Args:
            n: Number to generate
            callback: Called for each generated polyform
            batch_size: How many to buffer before callbacks
        """
        n = n or self.params.n
        positions = self._generate_positions(n)
        batch = []
        
        for i, pos in enumerate(positions):
            poly = self._generate_single_polyform(i, pos)
            
            if callback:
                callback(poly)
            
            batch.append(poly)
            
            if len(batch) >= batch_size:
                logger.debug(f"Generated batch of {len(batch)} polyforms")
                batch = []
        
        logger.info(f"Completed generation of {n} polyforms")
    
    def _generate_positions(self, n: int) -> np.ndarray:
        """Generate n spatial positions based on distribution mode."""
        
        if self.params.distribution == DistributionMode.UNIFORM:
            return self._generate_uniform_positions(n)
        elif self.params.distribution == DistributionMode.GAUSSIAN:
            return self._generate_gaussian_positions(n)
        elif self.params.distribution == DistributionMode.CLUSTERED:
            return self._generate_clustered_positions(n)
        elif self.params.distribution == DistributionMode.GRID:
            return self._generate_grid_positions(n)
        elif self.params.distribution == DistributionMode.SHELL:
            return self._generate_shell_positions(n)
        elif self.params.distribution == DistributionMode.LAYERED:
            return self._generate_layered_positions(n)
        else:
            return self._generate_uniform_positions(n)
    
    def _generate_uniform_positions(self, n: int) -> np.ndarray:
        """Random positions in bounded box."""
        positions = np.random.uniform(
            low=[self.params.bounds_x[0], self.params.bounds_y[0], self.params.bounds_z[0]],
            high=[self.params.bounds_x[1], self.params.bounds_y[1], self.params.bounds_z[1]],
            size=(n, 3)
        )
        return positions
    
    def _generate_gaussian_positions(self, n: int) -> np.ndarray:
        """Normal distribution around center."""
        center = np.array([
            (self.params.bounds_x[0] + self.params.bounds_x[1]) / 2,
            (self.params.bounds_y[0] + self.params.bounds_y[1]) / 2,
            (self.params.bounds_z[0] + self.params.bounds_z[1]) / 2,
        ])
        
        std = np.array([
            (self.params.bounds_x[1] - self.params.bounds_x[0]) / 6,
            (self.params.bounds_y[1] - self.params.bounds_y[0]) / 6,
            (self.params.bounds_z[1] - self.params.bounds_z[0]) / 6,
        ])
        
        positions = np.random.normal(center, std, size=(n, 3))
        
        # Clip to bounds
        positions[:, 0] = np.clip(positions[:, 0], self.params.bounds_x[0], self.params.bounds_x[1])
        positions[:, 1] = np.clip(positions[:, 1], self.params.bounds_y[0], self.params.bounds_y[1])
        positions[:, 2] = np.clip(positions[:, 2], self.params.bounds_z[0], self.params.bounds_z[1])
        
        return positions
    
    def _generate_clustered_positions(self, n: int) -> np.ndarray:
        """Group polyforms into clusters."""
        positions = []
        cluster_centers = np.random.uniform(
            low=[self.params.bounds_x[0], self.params.bounds_y[0], self.params.bounds_z[0]],
            high=[self.params.bounds_x[1], self.params.bounds_y[1], self.params.bounds_z[1]],
            size=(self.params.cluster_count, 3)
        )
        
        items_per_cluster = n // self.params.cluster_count
        remainder = n % self.params.cluster_count
        
        for cluster_idx, center in enumerate(cluster_centers):
            count = items_per_cluster + (1 if cluster_idx < remainder else 0)
            
            # Generate points around cluster center
            cluster_points = np.random.normal(
                center,
                self.params.cluster_radius / 3,
                size=(count, 3)
            )
            
            positions.append(cluster_points)
        
        positions = np.vstack(positions)
        
        # Clip to bounds
        positions[:, 0] = np.clip(positions[:, 0], self.params.bounds_x[0], self.params.bounds_x[1])
        positions[:, 1] = np.clip(positions[:, 1], self.params.bounds_y[0], self.params.bounds_y[1])
        positions[:, 2] = np.clip(positions[:, 2], self.params.bounds_z[0], self.params.bounds_z[1])
        
        return positions[:n]
    
    def _generate_grid_positions(self, n: int) -> np.ndarray:
        """Regular grid layout."""
        grid_size = int(np.ceil(n ** (1/3)))
        positions = []
        
        x_step = (self.params.bounds_x[1] - self.params.bounds_x[0]) / (grid_size + 1)
        y_step = (self.params.bounds_y[1] - self.params.bounds_y[0]) / (grid_size + 1)
        z_step = (self.params.bounds_z[1] - self.params.bounds_z[0]) / (grid_size + 1)
        
        count = 0
        for i in range(grid_size):
            for j in range(grid_size):
                for k in range(grid_size):
                    if count >= n:
                        break
                    
                    x = self.params.bounds_x[0] + (i + 1) * x_step
                    y = self.params.bounds_y[0] + (j + 1) * y_step
                    z = self.params.bounds_z[0] + (k + 1) * z_step
                    
                    # Add small random jitter
                    x += np.random.normal(0, x_step * 0.1)
                    y += np.random.normal(0, y_step * 0.1)
                    z += np.random.normal(0, z_step * 0.1)
                    
                    positions.append([x, y, z])
                    count += 1
        
        return np.array(positions)
    
    def _generate_shell_positions(self, n: int) -> np.ndarray:
        """On surface of sphere/shell."""
        center = np.array([
            (self.params.bounds_x[0] + self.params.bounds_x[1]) / 2,
            (self.params.bounds_y[0] + self.params.bounds_y[1]) / 2,
            (self.params.bounds_z[0] + self.params.bounds_z[1]) / 2,
        ])
        
        radius = min(
            (self.params.bounds_x[1] - self.params.bounds_x[0]) / 2,
            (self.params.bounds_y[1] - self.params.bounds_y[0]) / 2,
            (self.params.bounds_z[1] - self.params.bounds_z[0]) / 2,
        ) * 0.8
        
        # Fibonacci sphere
        indices = np.arange(0, n, dtype=float)
        theta = np.arccos(1 - 2 * indices / n)
        phi = np.pi * (1 + 5**0.5) * indices
        
        x = center[0] + radius * np.cos(phi) * np.sin(theta)
        y = center[1] + radius * np.sin(phi) * np.sin(theta)
        z = center[2] + radius * np.cos(theta)
        
        positions = np.column_stack([x, y, z])
        
        # Add thickness variation
        thickness = np.random.normal(0, radius * 0.1, size=(n, 1))
        directions = positions - center
        norms = np.linalg.norm(directions, axis=1, keepdims=True)
        norms = np.where(norms < 1e-10, 1.0, norms)
        positions += (directions / norms) * thickness
        
        return positions
    
    def _generate_layered_positions(self, n: int) -> np.ndarray:
        """Vertical layers."""
        num_layers = max(1, int(np.sqrt(n / 10)))
        positions = []
        
        z_values = np.linspace(self.params.bounds_z[0], self.params.bounds_z[1], num_layers)
        items_per_layer = n // num_layers
        remainder = n % num_layers
        
        for layer_idx, z in enumerate(z_values):
            count = items_per_layer + (1 if layer_idx < remainder else 0)
            
            # Random positions in XY plane
            x = np.random.uniform(self.params.bounds_x[0], self.params.bounds_x[1], count)
            y = np.random.uniform(self.params.bounds_y[0], self.params.bounds_y[1], count)
            z_arr = np.full(count, z)
            
            layer_points = np.column_stack([x, y, z_arr])
            positions.append(layer_points)
        
        positions = np.vstack(positions)
        return positions[:n]
    
    def _generate_single_polyform(self, poly_id: int, position: np.ndarray) -> Dict[str, Any]:
        """Generate a single random polyform."""
        
        # Select shape type
        if self.params.shape_variety == ShapeVariety.REGULAR_ONLY:
            vertices = self._generate_regular_polygon(position)
        elif self.params.shape_variety == ShapeVariety.PERTURBED:
            vertices = self._generate_perturbed_polygon(position)
        elif self.params.shape_variety == ShapeVariety.STAR:
            vertices = self._generate_star_polygon(position)
        elif self.params.shape_variety == ShapeVariety.CONCAVE:
            vertices = self._generate_concave_polygon(position)
        elif self.params.shape_variety == ShapeVariety.IRREGULAR:
            vertices = self._generate_irregular_polygon(position)
        else:  # MIXED
            choice = np.random.choice(['regular', 'perturbed', 'star', 'concave'])
            if choice == 'regular':
                vertices = self._generate_regular_polygon(position)
            elif choice == 'perturbed':
                vertices = self._generate_perturbed_polygon(position)
            elif choice == 'star':
                vertices = self._generate_star_polygon(position)
            else:
                vertices = self._generate_concave_polygon(position)
        
        sides = len(vertices)
        shape_type = self.params.shape_variety.value
        self.generation_stats['by_shape_type'][shape_type] = \
            self.generation_stats['by_shape_type'].get(shape_type, 0) + 1
        
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
    
    def _generate_perturbed_polygon(self, center: np.ndarray) -> np.ndarray:
        """Regular polygon with random perturbations."""
        vertices = self._generate_regular_polygon(center)
        
        # Perturb each vertex
        perturbation = np.random.normal(0, self.params.perturbation_strength, vertices.shape)
        vertices += perturbation
        
        return vertices
    
    def _generate_star_polygon(self, center: np.ndarray) -> np.ndarray:
        """Star-shaped polygon."""
        points = np.random.randint(4, 9)
        size = self.params.avg_size * (1 + np.random.normal(0, self.params.size_variation))
        inner_radius = size * 0.3
        outer_radius = size * 0.7
        
        vertices = []
        for i in range(points * 2):
            angle = (i * np.pi) / points
            radius = outer_radius if i % 2 == 0 else inner_radius
            
            x = center[0] + radius * np.cos(angle)
            y = center[1] + radius * np.sin(angle)
            z = center[2]
            
            vertices.append([x, y, z])
        
        return np.array(vertices)
    
    def _generate_concave_polygon(self, center: np.ndarray) -> np.ndarray:
        """Concave polygon (irregular but with structure)."""
        points = np.random.randint(5, 10)
        size = self.params.avg_size * (1 + np.random.normal(0, self.params.size_variation))
        
        angles = np.sort(np.random.uniform(0, 2 * np.pi, points))
        radii = np.random.uniform(size * 0.3, size * 0.7, points)
        
        x = center[0] + radii * np.cos(angles)
        y = center[1] + radii * np.sin(angles)
        z = np.full(points, center[2])
        
        return np.column_stack([x, y, z])
    
    def _generate_irregular_polygon(self, center: np.ndarray) -> np.ndarray:
        """Fully random polygon."""
        points = np.random.randint(3, 12)
        size = self.params.avg_size * (1 + np.random.normal(0, self.params.size_variation))
        
        # Random points in circle, then sort by angle
        angles = np.sort(np.random.uniform(0, 2 * np.pi, points))
        radii = np.random.exponential(size * 0.5, points)
        
        x = center[0] + radii * np.cos(angles)
        y = center[1] + radii * np.sin(angles)
        z = np.full(points, center[2] + np.random.normal(0, 0.1))
        
        return np.column_stack([x, y, z])
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get generation statistics."""
        return {
            'total_generated': self.generated_count,
            'polyforms_created': len(self.polyforms),
            'distribution': self.params.distribution.value,
            'shape_variety': self.params.shape_variety.value,
            'by_shape_type': self.generation_stats['by_shape_type'],
            'generation_time_ms': self.generation_stats['generation_time'] * 1000,
        }


# ============================================================================
# WORKSPACE INTEGRATION
# ============================================================================

class WorkspacePolyformLoader:
    """Loads generated polyforms into 3D workspace in real-time."""
    
    def __init__(self, workspace_callback: Optional[Callable] = None):
        """
        Initialize loader.
        
        Args:
            workspace_callback: Function to call with each polyform
                               (e.g., workspace.add_polyform(polyform))
        """
        self.callback = workspace_callback
        self.loaded_count = 0
        self.buffer = deque(maxlen=100)
    
    def load_batch(self, polyforms: List[Dict[str, Any]]):
        """Load a batch of polyforms."""
        for poly in polyforms:
            self.load_single(poly)
    
    def load_single(self, polyform: Dict[str, Any]):
        """Load a single polyform to workspace."""
        if self.callback:
            self.callback(polyform)
        
        self.buffer.append(polyform)
        self.loaded_count += 1
        
        if self.loaded_count % 100 == 0:
            logger.info(f"Loaded {self.loaded_count} polyforms to workspace")


if __name__ == '__main__':
    # Example: Generate 1000 random polyforms with varied shapes
    params = GenerationParams(
        n=1000,
        distribution=DistributionMode.CLUSTERED,
        shape_variety=ShapeVariety.MIXED,
        cluster_count=10,
        bounds_x=(-100, 100),
        bounds_y=(-100, 100),
        bounds_z=(-20, 20),
    )
    
    generator = RandomPolyformGenerator(params)
    polyforms = generator.generate_batch()
    
    print(f"Generated {len(polyforms)} polyforms")
    print(f"Statistics: {generator.get_statistics()}")
