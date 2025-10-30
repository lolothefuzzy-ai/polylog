"""
Random Assembly Generator WITH Canonical N Tracking

Enhanced version of random_assembly_generator.py with integrated
canonical polyform count (N) tracking.

Integrates:
- CanonicalIntegrator: Tracks N as assembly evolves
- AssemblyObserver: Observer pattern for generation loop
- Convergence monitoring: Detects when assembly reaches complexity ceiling
"""

import random
import numpy as np
import time
from typing import Dict, Any, List, Tuple, Optional
from polygon_utils import create_polygon, create_polygon_3d
from generator_protocol import BaseGenerator, register_generator, GeneratorCapability

# Import canonical tracking
from canonical_integration import CanonicalIntegrator, AssemblyObserver


@register_generator('random_assembly_tracked', [GeneratorCapability.BASIC])
class RandomAssemblyGeneratorWithTracking(BaseGenerator):
    """
    Generate random polyform assemblies with canonical N convergence tracking.
    
    Features:
    - Random polygon type selection
    - Spatial distribution patterns
    - Usage-based adaptation
    - CANONICAL N TRACKING integrated
    - Convergence detection
    - Real-time metrics
    """
    
    def __init__(self, assembly=None, enable_3d_mode=True, enable_tracking=True):
        """
        Initialize generator with optional canonical tracking.
        
        Args:
            assembly: Assembly object to add polyforms to
            enable_3d_mode: Create 3D polygons
            enable_tracking: Enable canonical N tracking (True for analysis)
        """
        # Initialize base class
        if assembly is not None:
            super().__init__(assembly, enable_3d_mode)
        else:
            # Standalone mode (no assembly)
            self.assembly = None
            self._enable_3d_mode = enable_3d_mode
            self._generation_stats = {
                'total_generated': 0,
                'total_time': 0.0,
                'success_count': 0,
                'failure_count': 0
            }
        
        # ===== CANONICAL TRACKING INTEGRATION =====
        self.enable_tracking = enable_tracking
        if enable_tracking:
            self.integrator = CanonicalIntegrator(enable_tracking=True)
            self.observer = AssemblyObserver(self.integrator)
        else:
            self.integrator = None
            self.observer = None
        
        # Polygon type preferences (updated based on usage)
        self.type_weights = {
            3: 1.0,   # Triangles
            4: 1.2,   # Squares (slightly preferred)
            5: 0.8,   # Pentagons
            6: 0.7,   # Hexagons
            7: 0.5,   # Heptagons
            8: 0.4,   # Octagons
            9: 0.3,   # Nonagons
            10: 0.3,  # Decagons
            11: 0.2,  # Hendecagons
            12: 0.2,  # Dodecagons
        }
        
        # Layout patterns
        self.patterns = [
            'circular',
            'grid',
            'spiral',
            'random_cluster',
            'linear',
            'organic'
        ]
        
        # Usage tracking
        self.generated_count = 0
        self.type_usage_count = {sides: 0 for sides in range(3, 13)}
        self.pattern_success = {pattern: 0.5 for pattern in self.patterns}
        self.generation_number = 0
    
    def generate(self, **kwargs) -> List[str]:
        """
        Unified generation interface with canonical tracking.
        
        Args:
            **kwargs:
                - num_polyforms: Number to generate
                - allow_types: List of allowed polygon sides
                - pattern: Layout pattern name
                - use_3d: Use 3D mode
                - track: Override enable_tracking setting
        
        Returns:
            List of polyform IDs
        """
        start_time = time.perf_counter()
        track_this = kwargs.pop('track', self.enable_tracking)
        
        try:
            num_polyforms = kwargs.get('num_polyforms')
            allow_types = kwargs.get('allow_types')
            pattern = kwargs.get('pattern')
            use_3d = kwargs.get('use_3d', self._enable_3d_mode)
            
            polyforms = self.generate_random_assembly(
                num_polyforms=num_polyforms,
                allow_types=allow_types,
                pattern=pattern,
                use_3d=use_3d
            )
            
            # Add to assembly if available
            poly_ids = []
            if self.assembly is not None:
                for i, poly in enumerate(polyforms):
                    if 'id' not in poly:
                        poly['id'] = f'poly_{i}_{int(time.time() * 1000) % 10000}'
                    self.assembly.add_polyform(poly)
                    poly_ids.append(poly['id'])
            else:
                poly_ids = [p.get('id', f'poly_{i}') for i, p in enumerate(polyforms)]
            
            elapsed = time.perf_counter() - start_time
            self._record_generation(len(poly_ids), True, elapsed)
            
            # ===== RECORD CANONICAL N =====
            if track_this and self.observer and self.assembly:
                self.observer.on_generation_complete(self.assembly, self.generation_number)
                self.generation_number += 1
            
            return poly_ids
            
        except Exception as e:
            elapsed = time.perf_counter() - start_time
            self._record_generation(0, False, elapsed)
            raise
    
    def generate_random_assembly(
        self,
        num_polyforms: int = None,
        allow_types: List[int] = None,
        pattern: str = None,
        use_3d: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Generate a random assembly of polyforms.
        
        Args:
            num_polyforms: Number of polyforms (random 5-15 if None)
            allow_types: Allowed polygon types (all if None)
            pattern: Layout pattern (random if None)
            use_3d: Create 3D meshes
            
        Returns:
            List of polyform dictionaries
        """
        # Defaults
        if num_polyforms is None:
            num_polyforms = random.randint(5, 15)
        
        if allow_types is None:
            allow_types = list(range(3, 13))
        
        if pattern is None:
            pattern = self._select_pattern()
        
        # Generate polyforms
        polyforms = []
        positions = self._generate_positions(num_polyforms, pattern)
        
        for i, pos in enumerate(positions):
            # Select polygon type with weighted randomness
            sides = self._select_polygon_type(allow_types)
            
            # Create polygon
            if use_3d:
                poly = create_polygon_3d(sides, pos, thickness=0.15)
            else:
                poly = create_polygon(sides, pos)
            
            # Add random rotation
            rotation = random.uniform(0, 2 * np.pi)
            poly['rotation'] = rotation
            
            # Rotate vertices
            verts = np.array(poly['vertices'])
            center = verts.mean(axis=0)
            
            # Rotation matrix around Z
            cos_r = np.cos(rotation)
            sin_r = np.sin(rotation)
            R = np.array([
                [cos_r, -sin_r, 0],
                [sin_r, cos_r, 0],
                [0, 0, 1]
            ])
            
            rotated_verts = []
            for v in verts:
                v_rel = v - center
                v_rot = R @ v_rel
                rotated_verts.append(v_rot + center)
            
            poly['vertices'] = rotated_verts
            
            # Track metadata
            poly['generation_pattern'] = pattern
            poly['generation_index'] = i
            
            polyforms.append(poly)
            
            # Update usage
            self.type_usage_count[sides] += 1
        
        self.generated_count += 1
        
        return polyforms
    
    def _select_pattern(self) -> str:
        """Select layout pattern weighted by success."""
        patterns = self.patterns
        weights = [self.pattern_success.get(p, 0.5) for p in patterns]
        return random.choices(patterns, weights=weights, k=1)[0]
    
    def _select_polygon_type(self, allow_types: List[int]) -> int:
        """Select polygon type with weighted randomness."""
        valid_types = [t for t in allow_types if t in self.type_weights]
        if not valid_types:
            return random.choice(allow_types)
        
        weights = [self.type_weights[t] for t in valid_types]
        return random.choices(valid_types, weights=weights, k=1)[0]
    
    def _generate_positions(self, count: int, pattern: str) -> List[Tuple]:
        """Generate positions based on pattern."""
        if pattern == 'circular':
            positions = []
            for i in range(count):
                angle = 2 * np.pi * i / count
                x = 5 * np.cos(angle)
                y = 5 * np.sin(angle)
                positions.append((x, y, 0))
            return positions
        
        elif pattern == 'grid':
            positions = []
            cols = int(np.ceil(np.sqrt(count)))
            for i in range(count):
                x = (i % cols) * 3
                y = (i // cols) * 3
                positions.append((x, y, 0))
            return positions
        
        elif pattern == 'spiral':
            positions = []
            for i in range(count):
                angle = 0.5 * i
                radius = 0.5 * i
                x = radius * np.cos(angle)
                y = radius * np.sin(angle)
                positions.append((x, y, 0))
            return positions
        
        elif pattern == 'random_cluster':
            center = (random.uniform(-5, 5), random.uniform(-5, 5))
            positions = []
            for _ in range(count):
                x = center[0] + random.gauss(0, 2)
                y = center[1] + random.gauss(0, 2)
                positions.append((x, y, 0))
            return positions
        
        elif pattern == 'linear':
            positions = []
            for i in range(count):
                x = i * 2
                y = random.gauss(0, 0.5)
                positions.append((x, y, 0))
            return positions
        
        else:  # 'organic'
            positions = []
            for _ in range(count):
                x = random.uniform(-10, 10)
                y = random.uniform(-10, 10)
                positions.append((x, y, 0))
            return positions
    
    def _record_generation(self, count: int, success: bool, elapsed: float):
        """Record generation statistics."""
        self._generation_stats['total_generated'] += count
        self._generation_stats['total_time'] += elapsed
        
        if success:
            self._generation_stats['success_count'] += 1
        else:
            self._generation_stats['failure_count'] += 1
    
    # ===== NEW TRACKING METHODS =====
    
    def get_convergence_report(self) -> str:
        """Get canonical N convergence report."""
        if not self.enable_tracking or not self.integrator:
            return "Tracking not enabled"
        return self.integrator.get_convergence_report()
    
    def get_tracking_metrics(self) -> Dict[str, Any]:
        """Export tracking metrics as dictionary."""
        if not self.enable_tracking or not self.integrator:
            return {}
        return self.integrator.get_metrics_dict()
    
    def print_tracking_status(self):
        """Print canonical N tracking status."""
        if not self.enable_tracking or not self.integrator:
            print("Tracking not enabled")
            return
        
        metrics = self.get_tracking_metrics()
        if not metrics:
            print("No convergence data recorded yet")
            return
        
        print("\n" + "="*60)
        print("CANONICAL N TRACKING STATUS")
        print("="*60)
        print(f"Generations tracked: {metrics.get('total_generations', 0)}")
        print(f"Initial logN: {metrics.get('initial_logN', 0):.4f}")
        print(f"Current logN: {metrics.get('final_logN', 0):.4f}")
        print(f"Growth: {metrics.get('logN_growth', 0):.4f} (log-space)")
        print(f"Diversity: {metrics.get('initial_diversity', 0):.4f} → "
              f"{metrics.get('final_diversity', 0):.4f}")
    
    def finalize_tracking(self):
        """Finalize and report canonical N tracking."""
        if self.enable_tracking and self.observer:
            self.observer.on_convergence_reached()


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

def example_usage_with_tracking():
    """
    Example showing how to use the generator with canonical tracking.
    """
    print("\n" + "="*80)
    print("RANDOM ASSEMBLY GENERATOR WITH CANONICAL N TRACKING")
    print("="*80)
    
    # Create a mock assembly
    class MockAssembly:
        def __init__(self):
            self.polyforms = []
            self.bonds = []
        
        def add_polyform(self, poly):
            self.polyforms.append(poly)
        
        def get_all_polyforms(self):
            return self.polyforms
        
        def get_bonds(self):
            return self.bonds
    
    # Initialize with tracking
    assembly = MockAssembly()
    generator = RandomAssemblyGeneratorWithTracking(
        assembly=assembly,
        enable_3d_mode=False,
        enable_tracking=True
    )
    
    print("\nGenerating random assemblies with canonical N tracking...\n")
    
    # Generate multiple times
    for iteration in range(5):
        num = random.randint(3, 8)
        print(f"Iteration {iteration + 1}: Generating {num} polyforms")
        generator.generate(num_polyforms=num, use_3d=False)
    
    # Print tracking status
    generator.print_tracking_status()
    
    # Finalize and get report
    print("\nFinalizing tracking...")
    generator.finalize_tracking()


if __name__ == "__main__":
    example_usage_with_tracking()
