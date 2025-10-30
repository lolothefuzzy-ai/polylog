"""
Unified engine for creating polyforms from any source.
Ensures all polyforms have correct vertex/edge tracking and 3D mesh data.
"""
from typing import Dict, List, Tuple, Optional, Any
import numpy as np
import time

from polygon_utils import create_polygon, create_polygon_3d, add_3d_mesh_to_polyform
from scaler_database import ScalerDatabase
from symmetry_database import SymmetryDatabase
from learning_engine import LearningEngine
from template_library import TemplateLibrary
from generator_protocol import BaseGenerator, register_generator, GeneratorCapability


@register_generator('basic', [GeneratorCapability.BASIC, GeneratorCapability.TEMPLATE_BASED, GeneratorCapability.LEARNING])
class PolyformGenerationEngine(BaseGenerator):
    """
    Unified engine for creating polyforms from any source.
    Ensures all polyforms have correct vertex/edge tracking.
    """
    
    def __init__(self, assembly, enable_3d_mode=True):
        # Initialize base class
        super().__init__(assembly, enable_3d_mode)
        
        self.scaler_db = ScalerDatabase()
        self.symmetry_db = SymmetryDatabase()
        self.learning_engine = LearningEngine(self.scaler_db, self.symmetry_db)
        
        # Link assembly to learning engine
        self.learning_engine.assembly = assembly
        
        # Extended statistics (base class provides standard ones)
        self.extended_stats = {
            'successful_bonds': 0,
            'failed_bonds': 0,
            'learned_patterns': 0
        }
    
    def generate_single(self, sides: int, position=None, 
                       apply_symmetry=True, scale=1.0, thickness=0.15) -> str:
        """
        Generate a single polygon with learned properties.
        
        Args:
            sides: Number of sides for the polygon
            position: Optional (x, y, z) position
            apply_symmetry: Whether to apply learned symmetries
            scale: Scale factor for the polygon
            thickness: Thickness for 3D mesh extrusion
        
        Returns:
            poly_id: ID of created polyform
        """
        # Create base polygon
        if position is None:
            position = self._get_smart_spawn_position(sides)
        
        if self.is_3d_mode():
            poly = create_polygon_3d(sides, position, thickness=thickness)
        else:
            poly = create_polygon(sides, position)
        
        # Apply learned scale factors
        if apply_symmetry and scale == 1.0:
            learned_scale = self.scaler_db.get_optimal_scaler(sides)
            poly = self._apply_scaler(poly, learned_scale)
        elif scale != 1.0:
            poly = self._apply_scaler(poly, scale)
        
        # Apply learned symmetry transformations
        if apply_symmetry:
            symmetry = self.symmetry_db.get_likely_symmetry(sides)
            poly = self._apply_symmetry(poly, symmetry)
        
        # Add to assembly
        self.assembly.add_polyform(poly)
        
        # Register for learning
        self.learning_engine.observe_creation(poly)
        
        # Record statistics (base class method)
        self._record_generation(1, True, 0.0)
        
        return poly['id']
    
    def generate_range(self, min_sides: int, max_sides: int,
                      layout='circular', spacing=3.0) -> List[str]:
        """
        Generate range of polygons with intelligent placement.
        
        Args:
            min_sides: Minimum number of sides
            max_sides: Maximum number of sides
            layout: Layout type ('circular', 'linear', 'grid')
            spacing: Spacing between polygons
        
        Returns:
            poly_ids: List of created polyform IDs
        """
        poly_ids = []
        
        # Learn optimal layout from history
        learned_layout = self.learning_engine.suggest_layout(
            min_sides, max_sides, layout
        )
        
        positions = self._compute_layout_positions(
            min_sides, max_sides, learned_layout, spacing
        )
        
        for sides, position in zip(range(min_sides, max_sides + 1), positions):
            poly_id = self.generate_single(sides, position)
            poly_ids.append(poly_id)
        
        # Learn from this batch
        self.learning_engine.observe_batch(poly_ids)
        
        return poly_ids
    
    def generate_from_template(self, template_name: str, 
                              position=None, scale=1.0) -> List[str]:
        """
        Generate polyforms from built-in template (e.g., cube net).
        
        Args:
            template_name: Name of the template
            position: Optional offset position
            scale: Scale factor for entire template
        
        Returns:
            poly_ids: List of created polyform IDs
        """
        template = TemplateLibrary.get(template_name)
        if not template:
            raise ValueError(f"Unknown template: {template_name}")
        
        poly_ids = []
        
        for poly_spec in template['polyforms']:
            sides = poly_spec['sides']
            rel_pos = poly_spec['position']
            
            # Adjust position
            if position:
                abs_pos = (position[0] + rel_pos[0] * scale,
                          position[1] + rel_pos[1] * scale,
                          position[2] + rel_pos[2] * scale)
            else:
                abs_pos = rel_pos
            
            poly_id = self.generate_single(sides, abs_pos, 
                                          apply_symmetry=False,
                                          scale=scale)
            poly_ids.append(poly_id)
        
        # Apply template bonds (if bond creation method is available)
        # This would require integration with bond creation system
        # For now, just track the template usage
        
        # Learn from this template instantiation
        self.learning_engine.observe_template(template_name, poly_ids)
        
        return poly_ids
    
    def generate_from_learned_pattern(self, pattern_id: str) -> List[str]:
        """
        Generate polyforms using learned pattern.
        
        Learned patterns are discovered from user's successful assemblies.
        
        Args:
            pattern_id: ID of the learned pattern
        
        Returns:
            poly_ids: List of created polyform IDs
        """
        pattern = self.learning_engine.get_pattern(pattern_id)
        if not pattern:
            raise ValueError(f"Unknown pattern: {pattern_id}")
        
        poly_ids = []
        
        for poly_spec in pattern['polyforms']:
            poly_id = self.generate_single(
                sides=poly_spec['sides'],
                position=poly_spec['position'],
                scale=poly_spec.get('scale', 1.0)
            )
            poly_ids.append(poly_id)
        
        # Apply learned bonds and folds would go here
        # (requires integration with bond/hinge systems)
        
        return poly_ids
    
    def generate(self, **kwargs) -> List[str]:
        """
        Unified generation method (BaseGenerator interface).
        
        Dispatches to appropriate generation method based on kwargs.
        
        Args:
            **kwargs: Generation parameters
                - method: 'single', 'range', 'template', or 'pattern'
                - sides: Number of sides (for single)
                - min_sides, max_sides: Range (for range)
                - template_name: Template name (for template)
                - pattern_id: Pattern ID (for pattern)
                - position: Position tuple
                - scale: Scale factor
                - Other method-specific parameters
        
        Returns:
            List of generated polyform IDs
        """
        start_time = time.perf_counter()
        
        method = kwargs.get('method', 'single')
        
        try:
            if method == 'single':
                sides = kwargs.get('sides', 4)
                position = kwargs.get('position')
                scale = kwargs.get('scale', 1.0)
                thickness = kwargs.get('thickness', 0.15)
                poly_id = self.generate_single(sides, position, scale=scale, thickness=thickness)
                result = [poly_id]
                
            elif method == 'range':
                min_sides = kwargs.get('min_sides', 3)
                max_sides = kwargs.get('max_sides', 8)
                layout = kwargs.get('layout', 'circular')
                spacing = kwargs.get('spacing', 3.0)
                result = self.generate_range(min_sides, max_sides, layout, spacing)
                
            elif method == 'template':
                template_name = kwargs.get('template_name', 'cube_net')
                position = kwargs.get('position')
                scale = kwargs.get('scale', 1.0)
                result = self.generate_from_template(template_name, position, scale)
                
            elif method == 'pattern':
                pattern_id = kwargs.get('pattern_id')
                if not pattern_id:
                    raise ValueError("pattern_id required for pattern generation")
                result = self.generate_from_learned_pattern(pattern_id)
                
            else:
                raise ValueError(f"Unknown generation method: {method}")
            
            elapsed = time.perf_counter() - start_time
            self._record_generation(len(result), True, elapsed)
            return result
            
        except Exception as e:
            elapsed = time.perf_counter() - start_time
            self._record_generation(0, False, elapsed)
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Get extended statistics including base stats."""
        base_stats = super().get_stats()
        base_stats.update(self.extended_stats)
        return base_stats
    
    # Helper methods
    
    def _get_smart_spawn_position(self, sides: int) -> Tuple[float, float, float]:
        """Learn optimal spawn positions from user behavior."""
        # Query learning engine for typical placement
        learned_position = self.learning_engine.predict_spawn_position(sides)
        
        if learned_position:
            return learned_position
        
        # Fallback: near assembly centroid or origin
        if len(self.assembly.get_all_polyforms()) > 0:
            cx, cy, cz = self._assembly_centroid()
            return (cx + 3.0, cy, cz)
        
        return (0.0, 0.0, 0.0)
    
    def _assembly_centroid(self) -> Tuple[float, float, float]:
        """Compute centroid of all polyforms in assembly."""
        all_verts = []
        for poly in self.assembly.get_all_polyforms():
            all_verts.extend(poly['vertices'])
        
        if not all_verts:
            return (0.0, 0.0, 0.0)
        
        centroid = np.mean(all_verts, axis=0)
        return tuple(centroid)
    
    def _apply_scaler(self, poly: Dict, scaler: float) -> Dict:
        """Apply scale transformation to polygon."""
        if abs(scaler - 1.0) < 0.001:
            return poly
        
        verts = np.array(poly['vertices'])
        centroid = np.mean(verts, axis=0)
        
        # Scale relative to centroid
        scaled_verts = (verts - centroid) * scaler + centroid
        poly['vertices'] = scaled_verts.tolist()
        
        # Update position
        poly['position'] = centroid.tolist()
        
        # Update mesh if exists
        if poly.get('has_3d_mesh'):
            thickness = poly.get('mesh_thickness', 0.15) * scaler
            add_3d_mesh_to_polyform(poly, thickness=thickness)
        
        return poly
    
    def _apply_symmetry(self, poly: Dict, symmetry: Optional[Dict]) -> Dict:
        """Apply symmetry transformation (rotation, reflection)."""
        if not symmetry:
            return poly
        
        verts = np.array(poly['vertices'])
        centroid = np.mean(verts, axis=0)
        
        # Apply rotation symmetry
        if 'rotation' in symmetry:
            angle = symmetry['rotation']
            R = self._rotation_matrix_z(angle)
            verts = np.dot(verts - centroid, R.T) + centroid
        
        # Apply reflection symmetry
        if 'reflection_axis' in symmetry:
            axis = symmetry['reflection_axis']
            verts = self._reflect_across_axis(verts, axis, centroid)
        
        poly['vertices'] = verts.tolist()
        
        # Update mesh
        if poly.get('has_3d_mesh'):
            thickness = poly.get('mesh_thickness', 0.15)
            add_3d_mesh_to_polyform(poly, thickness=thickness)
        
        return poly
    
    def _rotation_matrix_z(self, angle: float) -> np.ndarray:
        """Create rotation matrix around z-axis."""
        c, s = np.cos(angle), np.sin(angle)
        return np.array([
            [c, -s, 0],
            [s,  c, 0],
            [0,  0, 1]
        ])
    
    def _reflect_across_axis(self, verts: np.ndarray, axis: str, 
                            centroid: np.ndarray) -> np.ndarray:
        """Reflect vertices across axis."""
        centered = verts - centroid
        
        if axis == 'x':
            # Reflect across x-axis (negate y)
            centered[:, 1] *= -1
        elif axis == 'y':
            # Reflect across y-axis (negate x)
            centered[:, 0] *= -1
        elif axis == 'z':
            # Reflect across z-axis (negate x and y)
            centered[:, 0] *= -1
            centered[:, 1] *= -1
        
        return centered + centroid
    
    def _compute_layout_positions(self, min_sides: int, max_sides: int,
                                 layout: Dict, spacing: float) -> List[Tuple[float, float, float]]:
        """Compute positions for polygon range based on layout."""
        count = max_sides - min_sides + 1
        layout_type = layout.get('type', 'circular')
        
        if layout_type == 'circular':
            return self._circular_layout(count, spacing)
        elif layout_type == 'linear':
            return self._linear_layout(count, spacing)
        elif layout_type == 'grid':
            return self._grid_layout(count, spacing)
        else:
            # Default to circular
            return self._circular_layout(count, spacing)
    
    def _circular_layout(self, count: int, radius: float) -> List[Tuple[float, float, float]]:
        """Arrange positions in a circle."""
        positions = []
        for i in range(count):
            angle = 2 * np.pi * i / count
            x = radius * np.cos(angle)
            y = radius * np.sin(angle)
            positions.append((float(x), float(y), 0.0))
        return positions
    
    def _linear_layout(self, count: int, spacing: float) -> List[Tuple[float, float, float]]:
        """Arrange positions in a line."""
        positions = []
        start_x = -(count - 1) * spacing / 2
        for i in range(count):
            x = start_x + i * spacing
            positions.append((float(x), 0.0, 0.0))
        return positions
    
    def _grid_layout(self, count: int, spacing: float) -> List[Tuple[float, float, float]]:
        """Arrange positions in a grid."""
        positions = []
        cols = int(np.ceil(np.sqrt(count)))
        rows = int(np.ceil(count / cols))
        
        start_x = -(cols - 1) * spacing / 2
        start_y = -(rows - 1) * spacing / 2
        
        for i in range(count):
            row = i // cols
            col = i % cols
            x = start_x + col * spacing
            y = start_y + row * spacing
            positions.append((float(x), float(y), 0.0))
        
        return positions
    
    def get_statistics(self) -> Dict[str, int]:
        """Get generation statistics."""
        return self.stats.copy()
    
    def reset_statistics(self):
        """Reset generation statistics."""
        for key in self.stats:
            self.stats[key] = 0
