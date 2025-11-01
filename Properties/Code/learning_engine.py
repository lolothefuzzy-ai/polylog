"""
Learning engine that observes user activity and progressively learns:
- Optimal scale factors for polygons
- Common symmetry patterns
- Successful assembly topologies
- Preferred fold angles
- Efficient workflows
"""
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from scaler_database import ScalerDatabase
from symmetry_database import SymmetryDatabase


class LearningEngine:
    """
    Observes user activity and learns:
    - Optimal scale factors for polygons
    - Common symmetry patterns
    - Successful assembly topologies
    - Preferred fold angles
    - Efficient workflows
    """
    
    def __init__(self, scaler_db: ScalerDatabase, symmetry_db: SymmetryDatabase):
        self.scaler_db = scaler_db
        self.symmetry_db = symmetry_db
        
        # Observation buffers
        self.recent_creations = []
        self.recent_bonds = []
        self.recent_folds = []
        
        # Learning parameters
        self.learning_rate = 0.1
        self.confidence_threshold = 0.7
        
        # Reference to assembly (set externally)
        self.assembly = None
        
    def observe_creation(self, poly: Dict[str, Any]):
        """Record polygon creation for learning."""
        observation = {
            'timestamp': time.time(),
            'sides': len(poly['vertices']),
            'position': np.mean(poly['vertices'], axis=0).tolist(),
            'scale': self._estimate_scale(poly),
            'context': self._get_current_context()
        }
        self.recent_creations.append(observation)
        
        # Update scalers
        self._update_scaler_estimate(observation)
    
    def observe_batch(self, poly_ids: List[str]):
        """Learn from batch generation patterns."""
        if not self.assembly:
            return
        
        # Analyze spatial layout
        layout_pattern = self._analyze_layout(poly_ids)
        
        # Store if it's a coherent pattern
        if layout_pattern['coherence'] > 0.8:
            self.symmetry_db.add_layout_pattern(layout_pattern)
    
    def observe_bond(self, poly1_id: str, edge1: int, 
                    poly2_id: str, edge2: int, success: bool):
        """Learn from bond creation attempts."""
        if not self.assembly:
            return
        
        observation = {
            'timestamp': time.time(),
            'poly1_sides': self._get_sides(poly1_id),
            'poly2_sides': self._get_sides(poly2_id),
            'edge1': edge1,
            'edge2': edge2,
            'success': success,
            'stability': self._compute_bond_stability(poly1_id, poly2_id)
        }
        self.recent_bonds.append(observation)
        
        # Update bond probability model
        self._update_bond_model(observation)
    
    def observe_fold(self, hinge_id: str, angle: float, stability: float):
        """Learn optimal fold angles for structures."""
        observation = {
            'timestamp': time.time(),
            'hinge_id': hinge_id,
            'angle': angle,
            'stability': stability,
            'poly_types': self._get_hinged_poly_types(hinge_id)
        }
        self.recent_folds.append(observation)
        
        # Update fold angle preferences
        self._update_fold_preferences(observation)
    
    def observe_template(self, template_name: str, poly_ids: List[str]):
        """Learn from template instantiation."""
        # Track which templates are used most
        self.symmetry_db.increment_template_usage(template_name)
        
        # If user modifies template, learn the modifications
        # (tracked in subsequent observe_bond/observe_fold calls)
    
    def suggest_layout(self, min_sides: int, max_sides: int, 
                      default_layout: str) -> Dict:
        """Suggest optimal layout based on learned patterns."""
        # Query database for similar past generations
        similar_patterns = self.symmetry_db.query_similar_ranges(
            min_sides, max_sides
        )
        
        if similar_patterns:
            # Return most successful pattern
            return similar_patterns[0]
        
        return {'type': default_layout}
    
    def predict_spawn_position(self, sides: int) -> Optional[Tuple]:
        """Predict where user typically spawns polygon of given sides."""
        # Analyze recent_creations for patterns
        similar_creations = [
            obs for obs in self.recent_creations[-50:]
            if obs['sides'] == sides
        ]
        
        if len(similar_creations) < 3:
            return None
        
        # Average position (weighted by recency)
        positions = np.array([obs['position'] for obs in similar_creations])
        weights = np.exp(-0.1 * np.arange(len(positions)))[::-1]
        avg_position = np.average(positions, axis=0, weights=weights)
        
        return tuple(avg_position)
    
    def get_pattern(self, pattern_id: str) -> Optional[Dict]:
        """Retrieve learned pattern by ID."""
        return self.symmetry_db.get_pattern(pattern_id)
    
    # Private learning methods
    
    def _update_scaler_estimate(self, observation: Dict):
        """Update scale factor estimates."""
        sides = observation['sides']
        scale = observation['scale']
        
        # Get current estimate
        current_scaler = self.scaler_db.get_optimal_scaler(sides)
        
        # Update with exponential moving average
        new_scaler = (1 - self.learning_rate) * current_scaler + \
                     self.learning_rate * scale
        
        self.scaler_db.set_optimal_scaler(sides, new_scaler)
    
    def _update_bond_model(self, observation: Dict):
        """Update bond success probability model."""
        # Key: (sides1, sides2, edge1, edge2)
        key = (observation['poly1_sides'], 
               observation['poly2_sides'],
               observation['edge1'],
               observation['edge2'])
        
        success = observation['success']
        
        # Update probability estimate
        self.scaler_db.update_bond_probability(key, success)
    
    def _update_fold_preferences(self, observation: Dict):
        """Learn preferred fold angles for poly types."""
        poly_types = observation['poly_types']
        angle = observation['angle']
        stability = observation['stability']
        
        # Only learn from stable folds
        if stability > 0.7:
            key = tuple(sorted(poly_types))
            self.symmetry_db.add_fold_preference(key, angle, stability)
    
    def _estimate_scale(self, poly: Dict) -> float:
        """Estimate scale of polygon relative to standard size."""
        verts = np.array(poly['vertices'])
        edge_lengths = []
        n = len(verts)
        
        for i in range(n):
            v1 = verts[i]
            v2 = verts[(i + 1) % n]
            edge_lengths.append(np.linalg.norm(v2 - v1))
        
        avg_edge_length = np.mean(edge_lengths)
        
        # Standard edge length is 1.0 (based on create_polygon)
        return avg_edge_length / 1.0
    
    def _analyze_layout(self, poly_ids: List[str]) -> Dict:
        """Analyze spatial layout of polygons."""
        if not self.assembly:
            return {'type': 'unknown', 'coherence': 0.0}
        
        positions = []
        for poly_id in poly_ids:
            poly = self.assembly.get_polyform(poly_id)
            if poly:
                centroid = np.mean(poly['vertices'], axis=0)
                positions.append(centroid[:2])  # XY only
        
        if len(positions) < 2:
            return {'type': 'unknown', 'coherence': 0.0}
        
        positions = np.array(positions)
        center = np.mean(positions, axis=0)
        
        # Check for circular layout
        radii = [np.linalg.norm(pos - center) for pos in positions]
        radii_std = np.std(radii)
        
        # Check for grid layout
        grid_score = self._compute_grid_score(positions)
        
        # Check for linear layout
        linear_score = self._compute_linear_score(positions)
        
        layout_type = 'circular' if radii_std < 0.5 else \
                     'grid' if grid_score > 0.8 else \
                     'linear' if linear_score > 0.8 else \
                     'random'
        
        return {
            'type': layout_type,
            'coherence': max(1.0 - radii_std, grid_score, linear_score),
            'center': center.tolist(),
            'spacing': float(np.mean(radii)) if layout_type == 'circular' else None
        }
    
    def _compute_grid_score(self, positions: np.ndarray) -> float:
        """Compute how well positions fit a grid layout."""
        if len(positions) < 3:
            return 0.0
        
        # Check if x and y coordinates cluster around specific values
        x_coords = positions[:, 0]
        y_coords = positions[:, 1]
        
        # Use clustering tolerance
        tolerance = 0.5
        
        x_clusters = self._count_clusters(x_coords, tolerance)
        y_clusters = self._count_clusters(y_coords, tolerance)
        
        # Good grid has few distinct x and y values
        expected_clusters = max(2, int(np.sqrt(len(positions))))
        x_score = 1.0 - abs(x_clusters - expected_clusters) / expected_clusters
        y_score = 1.0 - abs(y_clusters - expected_clusters) / expected_clusters
        
        return (x_score + y_score) / 2.0
    
    def _compute_linear_score(self, positions: np.ndarray) -> float:
        """Compute how well positions fit a linear layout."""
        if len(positions) < 3:
            return 0.0
        
        # Fit a line and check variance perpendicular to it
        centered = positions - np.mean(positions, axis=0)
        
        # SVD to find principal axis
        _, _, vh = np.linalg.svd(centered)
        principal_axis = vh[0]
        
        # Project points onto line
        projections = np.dot(centered, principal_axis)
        reconstructed = np.outer(projections, principal_axis)
        
        # Compute perpendicular variance
        residuals = centered - reconstructed
        variance = np.mean(np.sum(residuals**2, axis=1))
        
        # Low variance = good linear fit
        return max(0.0, 1.0 - variance)
    
    def _count_clusters(self, values: np.ndarray, tolerance: float) -> int:
        """Count number of clusters in 1D data."""
        if len(values) == 0:
            return 0
        
        sorted_vals = np.sort(values)
        clusters = 1
        
        for i in range(1, len(sorted_vals)):
            if sorted_vals[i] - sorted_vals[i-1] > tolerance:
                clusters += 1
        
        return clusters
    
    def _get_current_context(self) -> Dict:
        """Get current workspace context."""
        if not self.assembly:
            return {'polyform_count': 0}
        
        return {
            'polyform_count': len(self.assembly.get_all_polyforms()),
            'bond_count': len(self.assembly.get_bonds())
        }
    
    def _get_sides(self, poly_id: str) -> int:
        """Get number of sides for a polyform."""
        if not self.assembly:
            return 0
        
        poly = self.assembly.get_polyform(poly_id)
        if poly:
            return poly.get('sides', len(poly.get('vertices', [])))
        return 0
    
    def _compute_bond_stability(self, poly1_id: str, poly2_id: str) -> float:
        """Compute stability score for a bond."""
        # Placeholder: could use fold validator or other metrics
        return 0.8
    
    def _get_hinged_poly_types(self, hinge_id: str) -> List[int]:
        """Get polygon types connected by a hinge."""
        # Placeholder: would need hinge manager integration
        return []
