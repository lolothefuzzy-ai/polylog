"""
Random Assembly Generator

Generates randomized assemblies with:
- Mixed polygon types (triangles, squares, pentagons, etc.)
- Intelligent placement strategies
- Adaptive updates based on usage patterns
- Learning from successful configurations
"""
import random
import time
from typing import Any, Dict, List, Tuple

import numpy as np
from polygon_utils import create_polygon, create_polygon_3d

from generator_protocol import BaseGenerator, GeneratorCapability, register_generator


@register_generator('random_assembly', [GeneratorCapability.BASIC])
class RandomAssemblyGenerator(BaseGenerator):
    """
    Generate random polyform assemblies with variety and intelligence.
    
    Features:
    - Random polygon type selection
    - Spatial distribution patterns
    - Usage-based adaptation
    - Aesthetically pleasing layouts
    """
    
    def __init__(self, assembly=None, enable_3d_mode=True):
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
        
        # Polygon type preferences (updated based on usage)
        self.type_weights = {
            3: 1.0,  # Triangles
            4: 1.2,  # Squares (slightly preferred)
            5: 0.8,  # Pentagons
            6: 0.7,  # Hexagons
            7: 0.5,  # Heptagons
            8: 0.4,  # Octagons
            9: 0.3,  # Nonagons
            10: 0.3, # Decagons
            11: 0.2, # Hendecagons
            12: 0.2, # Dodecagons
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
    
    def generate(self, **kwargs) -> List[str]:
        """
        Unified generation interface (BaseGenerator).
        
        Args:
            **kwargs:
                - num_polyforms: Number to generate
                - allow_types: List of allowed polygon sides
                - pattern: Layout pattern name
                - use_3d: Use 3D mode (default from instance)
        
        Returns:
            List of polyform IDs
        """
        start_time = time.perf_counter()
        
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
        
        # Adapt weights based on usage
        if self.generated_count % 10 == 0:
            self._adapt_weights()
        
        return polyforms
    
    def _select_polygon_type(self, allow_types: List[int]) -> int:
        """Select polygon type using weighted randomness."""
        # Filter weights
        weights = [self.type_weights[t] for t in allow_types]
        
        # Weighted choice
        total = sum(weights)
        r = random.uniform(0, total)
        
        cumulative = 0
        for t, w in zip(allow_types, weights):
            cumulative += w
            if r <= cumulative:
                return t
        
        return allow_types[-1]
    
    def _select_pattern(self) -> str:
        """Select layout pattern based on success rates."""
        patterns = list(self.pattern_success.keys())
        weights = [self.pattern_success[p] for p in patterns]
        
        total = sum(weights)
        r = random.uniform(0, total)
        
        cumulative = 0
        for p, w in zip(patterns, weights):
            cumulative += w
            if r <= cumulative:
                return p
        
        return 'circular'
    
    def _generate_positions(self, count: int, pattern: str) -> List[Tuple[float, float, float]]:
        """Generate positions based on pattern."""
        positions = []
        
        if pattern == 'circular':
            radius = 3.0 + count * 0.3
            for i in range(count):
                angle = 2 * np.pi * i / count
                x = radius * np.cos(angle)
                y = radius * np.sin(angle)
                positions.append((x, y, 0.0))
        
        elif pattern == 'grid':
            cols = int(np.ceil(np.sqrt(count)))
            spacing = 2.5
            for i in range(count):
                row = i // cols
                col = i % cols
                x = (col - cols/2) * spacing
                y = (row - cols/2) * spacing
                positions.append((x, y, 0.0))
        
        elif pattern == 'spiral':
            angle = 0
            radius = 1.0
            for i in range(count):
                x = radius * np.cos(angle)
                y = radius * np.sin(angle)
                positions.append((x, y, 0.0))
                angle += 0.8
                radius += 0.5
        
        elif pattern == 'random_cluster':
            # Gaussian cluster
            for i in range(count):
                x = random.gauss(0, 3.0)
                y = random.gauss(0, 3.0)
                positions.append((x, y, 0.0))
        
        elif pattern == 'linear':
            spacing = 2.2
            for i in range(count):
                x = (i - count/2) * spacing
                y = random.gauss(0, 0.5)  # Slight variation
                positions.append((x, y, 0.0))
        
        elif pattern == 'organic':
            # Perlin-like organic placement
            positions = self._organic_positions(count)
        
        else:
            # Default: circular
            return self._generate_positions(count, 'circular')
        
        return positions
    
    def _organic_positions(self, count: int) -> List[Tuple[float, float, float]]:
        """Generate organic, natural-looking positions."""
        positions = []
        
        # Start with seed positions
        positions.append((0.0, 0.0, 0.0))
        
        for i in range(1, count):
            # Place near existing polyforms
            if positions:
                base = random.choice(positions)
                angle = random.uniform(0, 2 * np.pi)
                distance = random.uniform(1.5, 3.0)
                
                x = base[0] + distance * np.cos(angle)
                y = base[1] + distance * np.sin(angle)
                positions.append((x, y, 0.0))
        
        return positions
    
    def _adapt_weights(self):
        """Adapt type weights based on usage patterns."""
        total_usage = sum(self.type_usage_count.values())
        
        if total_usage == 0:
            return
        
        # Slightly favor less-used types for variety
        for sides in range(3, 13):
            usage_ratio = self.type_usage_count[sides] / total_usage
            
            # If under-used, increase weight slightly
            if usage_ratio < 0.1:
                self.type_weights[sides] *= 1.1
            # If over-used, decrease weight slightly
            elif usage_ratio > 0.2:
                self.type_weights[sides] *= 0.95
    
    def report_success(self, pattern: str, success: bool):
        """Report whether a generated assembly was successful."""
        # Update pattern success rate
        current = self.pattern_success[pattern]
        
        if success:
            self.pattern_success[pattern] = current * 0.9 + 1.0 * 0.1
        else:
            self.pattern_success[pattern] = current * 0.9 + 0.0 * 0.1
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get generator statistics."""
        return {
            'generated_count': self.generated_count,
            'type_usage': self.type_usage_count.copy(),
            'type_weights': self.type_weights.copy(),
            'pattern_success': self.pattern_success.copy(),
        }


class AdaptiveAssemblyUpdater:
    """
    Updates assemblies based on usage patterns and context.
    
    When user interacts with assemblies, this learns and adapts.
    """
    
    def __init__(self, generator: RandomAssemblyGenerator):
        self.generator = generator
        self.interaction_history = []
    
    def record_interaction(self, assembly: Dict[str, Any], interaction_type: str, success: bool):
        """
        Record user interaction with an assembly.
        
        Args:
            assembly: Assembly that was interacted with
            interaction_type: 'fold', 'bond', 'save', 'delete'
            success: Whether interaction was successful
        """
        self.interaction_history.append({
            'assembly_id': assembly.get('id'),
            'pattern': assembly.get('generation_pattern'),
            'type': interaction_type,
            'success': success,
            'polyform_count': len(assembly.get('polyforms', [])),
        })
        
        # Update generator based on success
        pattern = assembly.get('generation_pattern', 'circular')
        self.generator.report_success(pattern, success)
    
    def regenerate_with_improvements(self, base_assembly: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Regenerate assembly with improvements based on learning.
        
        Keeps successful aspects, varies others.
        """
        polyforms = base_assembly.get('polyforms', [])
        
        if not polyforms:
            return self.generator.generate_random_assembly()
        
        # Analyze what worked
        type_counts = {}
        for p in polyforms:
            sides = p.get('sides', 4)
            type_counts[sides] = type_counts.get(sides, 0) + 1
        
        # Generate similar but varied
        num_polyforms = len(polyforms)
        allow_types = list(type_counts.keys())
        
        # Add some variety
        if random.random() < 0.3:
            new_type = random.randint(3, 12)
            if new_type not in allow_types:
                allow_types.append(new_type)
        
        return self.generator.generate_random_assembly(
            num_polyforms=num_polyforms,
            allow_types=allow_types,
            pattern=None,  # Let it choose
            use_3d=polyforms[0].get('has_3d_mesh', False)
        )


# Quick access functions
_global_generator = None

def get_random_assembly(
    num_polyforms: int = None,
    pattern: str = None,
    use_3d: bool = True
) -> List[Dict[str, Any]]:
    """
    Quick function to generate random assembly.
    
    Usage:
        polyforms = get_random_assembly(num_polyforms=10, pattern='spiral')
        for poly in polyforms:
            assembly.add_polyform(poly)
    """
    global _global_generator
    
    if _global_generator is None:
        _global_generator = RandomAssemblyGenerator()
    
    return _global_generator.generate_random_assembly(
        num_polyforms=num_polyforms,
        pattern=pattern,
        use_3d=use_3d
    )


def get_generator() -> RandomAssemblyGenerator:
    """Get global generator instance."""
    global _global_generator
    
    if _global_generator is None:
        _global_generator = RandomAssemblyGenerator()
    
    return _global_generator
