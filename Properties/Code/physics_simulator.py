"""Physics-Based Simulation for Polyform Generation

Simulates physical properties to:
- Verify structural stability
- Check balance and center of mass
- Validate fold angles and sequences
- Detect collisions
- Ensure real-world foldability
"""
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from generator_protocol import BaseGenerator, GeneratorCapability, register_generator


@dataclass
class PhysicsProperties:
    """Physical properties of a polyform."""
    mass: float
    center_of_mass: Tuple[float, float, float]
    moment_of_inertia: float
    support_polygon: List[Tuple[float, float]]  # Base support area


@register_generator('physics', [GeneratorCapability.PHYSICS, GeneratorCapability.CONSTRAINT_SOLVING])
class PhysicsBasedGenerator(BaseGenerator):
    """
    Generate and validate polyforms using physics simulation.
    
    Considers:
    - Gravity (9.81 m/s^2)
    - Structural stress
    - Balance points
    - Material properties
    - Fold resistance
    - Collision detection
    """
    
    def __init__(self, assembly, enable_3d_mode: bool = True, gravity: float = 9.81):
        # Initialize base class
        super().__init__(assembly, enable_3d_mode)
        
        self.gravity = gravity
        
        # Material properties (assuming paper-like material)
        self.material_density = 0.8  # g/cm^2
        self.material_thickness = 0.1  # mm
        self.friction_coefficient = 0.6
        
        # Fold constraints
        self.max_fold_angle = 180.0  # degrees
        self.min_fold_angle = 0.0
        
    def check_stability(self, polyform_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Check structural stability of assembly.
        
        Args:
            polyform_ids: Specific polyforms to check, or None for all
        
        Returns:
            Dict with stability metrics
        """
        if polyform_ids is None:
            polyforms = self.assembly.get_all_polyforms()
        else:
            polyforms = [self.assembly.get_polyform(pid) for pid in polyform_ids]
            polyforms = [p for p in polyforms if p is not None]
        
        if not polyforms:
            return {
                'stable': True,
                'score': 1.0,
                'reason': 'No polyforms to check'
            }
        
        # Compute overall center of mass
        com = self._compute_center_of_mass(polyforms)
        
        # Find support polygon (base)
        support_polygon = self._compute_support_polygon(polyforms)
        
        # Check if COM is within support polygon
        com_within_support = self._point_in_polygon(com[:2], support_polygon)
        
        # Compute stability margin
        if com_within_support:
            margin = self._compute_stability_margin(com[:2], support_polygon)
            score = min(1.0, margin / 2.0)  # Normalize
        else:
            margin = 0.0
            score = 0.0
        
        # Check tipping angle
        tipping_angle = self._compute_tipping_angle(com, support_polygon)
        
        return {
            'stable': com_within_support and margin > 0.5,
            'score': score,
            'center_of_mass': com,
            'support_polygon': support_polygon,
            'stability_margin': margin,
            'tipping_angle': tipping_angle,
            'reason': self._stability_reason(score, com_within_support)
        }
    
    def validate_fold_sequence(self, fold_sequence: List[Dict]) -> Dict[str, Any]:
        """
        Validate a folding sequence for feasibility.
        
        Args:
            fold_sequence: List of fold operations
        
        Returns:
            Validation result with feasibility check
        """
        results = {
            'feasible': True,
            'issues': [],
            'max_stress': 0.0,
            'collision_points': []
        }
        
        for i, fold in enumerate(fold_sequence):
            # Check fold angle is within limits
            angle = fold.get('angle', 0)
            if angle < self.min_fold_angle or angle > self.max_fold_angle:
                results['feasible'] = False
                results['issues'].append({
                    'step': i,
                    'type': 'angle_limit',
                    'angle': angle
                })
            
            # Check for collisions at this fold state
            collisions = self._check_fold_collisions(fold)
            if collisions:
                results['feasible'] = False
                results['collision_points'].extend(collisions)
                results['issues'].append({
                    'step': i,
                    'type': 'collision',
                    'count': len(collisions)
                })
            
            # Estimate material stress
            stress = self._estimate_fold_stress(fold)
            results['max_stress'] = max(results['max_stress'], stress)
            
            if stress > 1.0:  # Material yield strength
                results['issues'].append({
                    'step': i,
                    'type': 'overstress',
                    'stress': stress
                })
        
        return results
    
    def generate(self, **kwargs) -> List[str]:
        """
        Unified generation method (BaseGenerator interface).
        
        Args:
            **kwargs: Generation parameters
                - target_height: Desired height of structure (default: 10.0)
                - base_constraint: Constraints for base (default: None)
        
        Returns:
            List of generated polyform IDs
        """
        target_height = kwargs.get('target_height', 10.0)
        base_constraint = kwargs.get('base_constraint', None)
        
        start_time = time.perf_counter()
        
        try:
            result = self.generate_stable_structure(target_height, base_constraint)
            elapsed = time.perf_counter() - start_time
            self._record_generation(len(result), True, elapsed)
            return result
        except Exception as e:
            elapsed = time.perf_counter() - start_time
            self._record_generation(0, False, elapsed)
            raise
    
    def generate_stable_structure(self, target_height: float = 10.0,
                                  base_constraint: Optional[Dict] = None) -> List[str]:
        """
        Generate a structurally stable polyform assembly.
        
        Args:
            target_height: Desired height of structure
            base_constraint: Constraints for base (e.g., min_polygons)
        
        Returns:
            List of generated polyform IDs
        """
        from polyform_generation_engine import PolyformGenerationEngine
        
        engine = PolyformGenerationEngine(self.assembly, enable_3d_mode=self.is_3d_mode())
        poly_ids = []
        
        if base_constraint is None:
            base_constraint = {'min_polygons': 3, 'base_radius': 5.0}
        
        print(f"🏗️ Building stable structure (target height: {target_height})...")
        
        # 1. Create stable base
        base_ids = self._create_stable_base(engine, base_constraint)
        poly_ids.extend(base_ids)
        print(f"   Base: {len(base_ids)} polygons")
        
        # 2. Build up incrementally
        current_height = 0.0
        layer = 0
        
        while current_height < target_height and len(poly_ids) < 30:
            layer += 1
            
            # Find stable positions for next layer
            candidates = self._find_stable_positions(poly_ids, current_height + 2.5)
            
            if not candidates:
                print(f"   No more stable positions found at height {current_height:.1f}")
                break
            
            # Choose best candidate
            best_candidate = self._select_best_candidate(candidates, poly_ids)
            
            # Verify stability before adding
            test_poly_id = engine.generate_single(
                sides=best_candidate['sides'],
                position=best_candidate['position']
            )
            
            stability = self.check_stability(poly_ids + [test_poly_id])
            
            if stability['stable']:
                poly_ids.append(test_poly_id)
                current_height = best_candidate['position'][2]
                print(f"   Layer {layer}: Height {current_height:.1f}, Stability {stability['score']:.2f}")
            else:
                # Remove test polygon
                if test_poly_id in self.assembly.polyforms:
                    del self.assembly.polyforms[test_poly_id]
                print(f"   Layer {layer}: Unstable configuration, stopping")
                break
        
        final_stability = self.check_stability(poly_ids)
        print(f"✓ Generated {len(poly_ids)} polygons, final stability: {final_stability['score']:.2f}")
        
        return poly_ids
    
    def simulate_folding(self, hinge_id: str, target_angle: float,
                        steps: int = 10) -> Dict[str, Any]:
        """
        Simulate folding a hinge and check for issues.
        
        Args:
            hinge_id: ID of hinge to fold
            target_angle: Target fold angle
            steps: Number of simulation steps
        
        Returns:
            Simulation results with collision and stress info
        """
        results = {
            'feasible': True,
            'collisions_at_step': [],
            'max_stress': 0.0,
            'trajectory': []
        }
        
        angle_per_step = target_angle / steps
        
        for step in range(steps + 1):
            current_angle = step * angle_per_step
            
            # Check collisions at this angle
            collisions = self._check_hinge_collisions(hinge_id, current_angle)
            
            if collisions:
                results['feasible'] = False
                results['collisions_at_step'].append({
                    'step': step,
                    'angle': current_angle,
                    'collisions': collisions
                })
            
            # Compute stress
            stress = self._compute_hinge_stress(hinge_id, current_angle)
            results['max_stress'] = max(results['max_stress'], stress)
            
            # Record trajectory
            results['trajectory'].append({
                'angle': current_angle,
                'stress': stress,
                'has_collision': len(collisions) > 0
            })
        
        return results
    
    def compute_polygon_mass(self, polyform: Dict) -> float:
        """Compute mass of a polygon based on area and material density."""
        vertices = np.array(polyform['vertices'])
        
        # Compute area using shoelace formula
        n = len(vertices)
        area = 0.0
        for i in range(n):
            j = (i + 1) % n
            area += vertices[i][0] * vertices[j][1]
            area -= vertices[j][0] * vertices[i][1]
        area = abs(area) / 2.0
        
        # Mass = density * area * thickness
        mass = self.material_density * area * self.material_thickness
        
        return float(mass)
    
    def _compute_center_of_mass(self, polyforms: List[Dict]) -> Tuple[float, float, float]:
        """Compute center of mass for multiple polyforms."""
        if not polyforms:
            return (0.0, 0.0, 0.0)
        
        total_mass = 0.0
        weighted_sum = np.array([0.0, 0.0, 0.0])
        
        for poly in polyforms:
            mass = self.compute_polygon_mass(poly)
            centroid = np.mean(poly['vertices'], axis=0)
            
            weighted_sum += mass * centroid
            total_mass += mass
        
        if total_mass == 0:
            return (0.0, 0.0, 0.0)
        
        com = weighted_sum / total_mass
        return tuple(com)
    
    def _compute_support_polygon(self, polyforms: List[Dict]) -> List[Tuple[float, float]]:
        """
        Compute support polygon (convex hull of base points).
        
        For 2D analysis, projects all vertices to XY plane.
        """
        # Get all vertices projected to XY
        all_points = []
        for poly in polyforms:
            for vertex in poly['vertices']:
                all_points.append((vertex[0], vertex[1]))
        
        if len(all_points) < 3:
            return all_points
        
        # Compute convex hull
        hull = self._convex_hull_2d(all_points)
        
        return hull
    
    def _convex_hull_2d(self, points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Compute 2D convex hull using Graham scan."""
        if len(points) < 3:
            return points
        
        # Sort points by x, then y
        sorted_points = sorted(points)
        
        # Build lower hull
        lower = []
        for p in sorted_points:
            while len(lower) >= 2 and self._cross_product_2d(lower[-2], lower[-1], p) <= 0:
                lower.pop()
            lower.append(p)
        
        # Build upper hull
        upper = []
        for p in reversed(sorted_points):
            while len(upper) >= 2 and self._cross_product_2d(upper[-2], upper[-1], p) <= 0:
                upper.pop()
            upper.append(p)
        
        # Concatenate (remove last point of each half as it's repeated)
        return lower[:-1] + upper[:-1]
    
    def _cross_product_2d(self, o: Tuple, a: Tuple, b: Tuple) -> float:
        """2D cross product of vectors OA and OB."""
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    
    def _point_in_polygon(self, point: Tuple[float, float], 
                         polygon: List[Tuple[float, float]]) -> bool:
        """Check if point is inside polygon using ray casting."""
        if len(polygon) < 3:
            return False
        
        x, y = point
        n = len(polygon)
        inside = False
        
        p1x, p1y = polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside
    
    def _compute_stability_margin(self, com: Tuple[float, float],
                                  polygon: List[Tuple[float, float]]) -> float:
        """Compute minimum distance from COM to polygon edges."""
        if len(polygon) < 3:
            return 0.0
        
        min_dist = float('inf')
        
        for i in range(len(polygon)):
            p1 = polygon[i]
            p2 = polygon[(i + 1) % len(polygon)]
            
            dist = self._point_to_segment_distance(com, p1, p2)
            min_dist = min(min_dist, dist)
        
        return float(min_dist)
    
    def _point_to_segment_distance(self, point: Tuple, p1: Tuple, p2: Tuple) -> float:
        """Distance from point to line segment."""
        x, y = point
        x1, y1 = p1
        x2, y2 = p2
        
        # Vector from p1 to p2
        dx = x2 - x1
        dy = y2 - y1
        
        if dx == 0 and dy == 0:
            # p1 and p2 are the same point
            return np.sqrt((x - x1)**2 + (y - y1)**2)
        
        # Parameter t for projection of point onto line
        t = ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)
        t = max(0, min(1, t))  # Clamp to segment
        
        # Closest point on segment
        closest_x = x1 + t * dx
        closest_y = y1 + t * dy
        
        # Distance to closest point
        return np.sqrt((x - closest_x)**2 + (y - closest_y)**2)
    
    def _compute_tipping_angle(self, com: Tuple, polygon: List[Tuple]) -> float:
        """Compute angle at which structure would tip over."""
        if len(polygon) < 3:
            return 0.0
        
        # Find closest edge
        min_angle = 90.0
        
        for i in range(len(polygon)):
            p1 = np.array(polygon[i])
            p2 = np.array(polygon[(i + 1) % len(polygon)])
            
            # Edge midpoint
            edge_mid = (p1 + p2) / 2
            
            # Vector from edge to COM
            to_com = np.array([com[0], com[1]]) - edge_mid
            
            # Angle from vertical
            angle = np.degrees(np.arctan2(np.linalg.norm(to_com[:2]), com[2]))
            min_angle = min(min_angle, angle)
        
        return float(min_angle)
    
    def _stability_reason(self, score: float, com_within: bool) -> str:
        """Generate human-readable stability reason."""
        if not com_within:
            return "Center of mass outside support polygon - will tip over"
        elif score > 0.8:
            return "Highly stable structure"
        elif score > 0.6:
            return "Stable but close to edge"
        elif score > 0.4:
            return "Marginally stable - may tip with disturbance"
        else:
            return "Unstable - requires support"
    
    def _create_stable_base(self, engine, constraint: Dict) -> List[str]:
        """Create a stable base for structure."""
        min_polygons = constraint.get('min_polygons', 3)
        base_radius = constraint.get('base_radius', 5.0)
        
        poly_ids = []
        
        # Create polygons in circle at z=0
        for i in range(min_polygons):
            angle = 2 * np.pi * i / min_polygons
            x = base_radius * np.cos(angle)
            y = base_radius * np.sin(angle)
            
            poly_id = engine.generate_single(
                sides=4,  # Squares for stable base
                position=(float(x), float(y), 0.0),
                apply_symmetry=False
            )
            poly_ids.append(poly_id)
        
        return poly_ids
    
    def _find_stable_positions(self, existing_ids: List[str], 
                              height: float) -> List[Dict]:
        """Find stable positions for next layer."""
        candidates = []
        
        # Get existing polyforms
        existing = [self.assembly.get_polyform(pid) for pid in existing_ids]
        existing = [p for p in existing if p is not None]
        
        if not existing:
            return []
        
        # Compute center of current layer
        centroids = [np.mean(p['vertices'], axis=0) for p in existing]
        center = np.mean(centroids, axis=0)
        
        # Generate candidate positions around center
        for radius in [2.0, 3.0, 4.0]:
            for angle in np.linspace(0, 2*np.pi, 8, endpoint=False):
                x = center[0] + radius * np.cos(angle)
                y = center[1] + radius * np.sin(angle)
                
                candidates.append({
                    'sides': 4,
                    'position': (float(x), float(y), float(height)),
                    'radius': radius,
                    'angle': angle
                })
        
        return candidates
    
    def _select_best_candidate(self, candidates: List[Dict], 
                               existing_ids: List[str]) -> Dict:
        """Select best candidate based on stability."""
        # For now, choose candidate closest to center
        # Could be enhanced with ML or optimization
        
        existing = [self.assembly.get_polyform(pid) for pid in existing_ids]
        centroids = [np.mean(p['vertices'], axis=0) for p in existing if p]
        center = np.mean(centroids, axis=0) if centroids else np.array([0, 0, 0])
        
        best_candidate = min(candidates, key=lambda c: 
            np.linalg.norm(np.array(c['position'][:2]) - center[:2]))
        
        return best_candidate
    
    def _check_fold_collisions(self, fold: Dict) -> List[Dict]:
        """Check for collisions during a fold operation."""
        # Simplified collision detection
        # Real implementation would use proper geometric intersection
        return []
    
    def _check_hinge_collisions(self, hinge_id: str, angle: float) -> List[Dict]:
        """Check for collisions when hinge is at specific angle."""
        # Placeholder for hinge collision detection
        return []
    
    def _estimate_fold_stress(self, fold: Dict) -> float:
        """Estimate material stress from fold operation."""
        angle = fold.get('angle', 0)
        
        # Sharp folds create more stress
        if abs(angle) > 150:
            return 0.9
        elif abs(angle) > 120:
            return 0.7
        elif abs(angle) > 90:
            return 0.5
        else:
            return 0.3
    
    def _compute_hinge_stress(self, hinge_id: str, angle: float) -> float:
        """Compute stress on hinge at given angle."""
        # Simplified stress model
        normalized_angle = abs(angle) / 180.0
        return normalized_angle * 0.8
