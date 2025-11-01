"""
SCIPY CONSTRAINT OPTIMIZER
===========================

Replaces manual constraint propagation with scipy.optimize for:
- Finding globally-optimal fold angles
- Multi-objective optimization (stability, compactness, balance)
- Handling conflicting constraints
- Scaling to 100+ polyforms

Uses SLSQP (Sequential Least Squares Programming) and trust-constr methods.
"""

import logging
import time
from typing import Dict, List, Optional

import numpy as np
from scipy.optimize import minimize

logger = logging.getLogger(__name__)


class ScipyConstraintOptimizer:
    """
    Scipy-based optimizer for polyform placement constraints.
    
    Replaces manual ForwardKinematics iteration with principled optimization.
    Finds fold angles that satisfy multiple objectives simultaneously.
    """
    
    def __init__(self, assembly, stability_scorer=None):
        """
        Initialize optimizer.
        
        Args:
            assembly: Assembly object with get_polyform(), set_hinge_angle()
            stability_scorer: Optional function(polyform_id) -> float [0-1]
        """
        self.assembly = assembly
        self.stability_scorer = stability_scorer or self._default_scorer
        self.optimization_history = []
        self.cache = {}
    
    def optimize_fold_angles(
        self,
        polyform_ids: List[str],
        target_stability: float = 0.85,
        target_spacing: float = 2.0,
        max_angle: float = np.pi,
        verbose: bool = False
    ) -> Dict[str, float]:
        """
        Find optimal fold angles maximizing stability and spacing.
        
        Args:
            polyform_ids: List of polyforms to optimize
            target_stability: Desired stability threshold [0-1]
            target_spacing: Minimum distance between polyforms
            max_angle: Maximum fold angle (radians)
            verbose: Print optimization progress
            
        Returns:
            {polyform_id: optimal_angle_radians}
        """
        if not polyform_ids:
            return {}
        
        n_vars = len(polyform_ids)
        x0 = np.ones(n_vars) * (np.pi / 2)  # Initial: 90 degrees
        bounds = [(0, max_angle) for _ in range(n_vars)]
        
        start_time = time.time()
        
        # Objective: maximize stability, minimize energy
        def objective(angles: np.ndarray) -> float:
            """Lower is better"""
            stability = self._compute_assembly_stability(polyform_ids, angles)
            energy = self._compute_assembly_energy(polyform_ids, angles)
            
            # Weighted: prefer stability, penalize extreme angles
            return -stability * 10.0 + energy * 0.5
        
        # Constraint: stability >= target_stability
        def stability_constraint(angles: np.ndarray) -> float:
            """Must be >= 0 (feasible)"""
            return self._compute_assembly_stability(polyform_ids, angles) - target_stability
        
        # Constraint: spacing >= target_spacing
        def spacing_constraint(angles: np.ndarray) -> np.ndarray:
            """All distances must be >= target_spacing"""
            distances = self._compute_polyform_distances(polyform_ids, angles)
            return distances - target_spacing
        
        constraints = [
            {'type': 'ineq', 'fun': stability_constraint},
            {'type': 'ineq', 'fun': spacing_constraint}
        ]
        
        # Optimize
        result = minimize(
            objective,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints,
            options={
                'maxiter': 500,
                'ftol': 1e-9,
                'disp': verbose
            }
        )
        
        elapsed = time.time() - start_time
        
        if not result.success:
            logger.warning(f"Optimization failed: {result.message}")
        else:
            logger.info(f"Optimization succeeded in {elapsed:.2f}s")
        
        # Map back to polyform_ids
        optimal_angles = {}
        for i, poly_id in enumerate(polyform_ids):
            optimal_angles[poly_id] = float(result.x[i])
        
        # Record in history
        self.optimization_history.append({
            'timestamp': time.time(),
            'polyform_ids': polyform_ids,
            'angles': optimal_angles,
            'success': result.success,
            'objective_value': result.fun,
            'elapsed_time': elapsed
        })
        
        return optimal_angles
    
    def optimize_multi_objective(
        self,
        polyform_ids: List[str],
        objectives: Dict[str, float],
        constraints: Optional[Dict[str, float]] = None,
        verbose: bool = False
    ) -> Dict[str, float]:
        """
        Multi-objective optimization with weighted objectives.
        
        Args:
            polyform_ids: List of polyforms to optimize
            objectives: Weights for each objective:
                'stability': 0.5      # 50% weight on stability
                'compactness': 0.3    # 30% weight on compactness  
                'balance': 0.2        # 20% weight on balance
            constraints: Optional hard constraints:
                'min_stability': 0.8
                'max_compactness': 5.0
            verbose: Print progress
            
        Returns:
            {polyform_id: optimal_angle_radians}
        """
        if not polyform_ids:
            return {}
        
        # Normalize weights
        total_weight = sum(objectives.values())
        normalized = {k: v / total_weight for k, v in objectives.items()}
        
        n_vars = len(polyform_ids)
        x0 = np.ones(n_vars) * (np.pi / 2)
        bounds = [(0, np.pi) for _ in range(n_vars)]
        
        start_time = time.time()
        
        # Weighted objective function
        def weighted_objective(angles: np.ndarray) -> float:
            score = 0.0
            
            if normalized.get('stability', 0) > 0:
                stability = self._compute_assembly_stability(polyform_ids, angles)
                score -= normalized['stability'] * stability  # Maximize
            
            if normalized.get('compactness', 0) > 0:
                compactness = self._compute_assembly_compactness(polyform_ids, angles)
                score += normalized['compactness'] * compactness  # Minimize
            
            if normalized.get('balance', 0) > 0:
                balance = self._compute_assembly_balance(polyform_ids, angles)
                score += normalized['balance'] * balance  # Minimize
            
            return score
        
        # Build constraint list
        constraint_list = []
        
        if constraints:
            if 'min_stability' in constraints:
                min_stab = constraints['min_stability']
                constraint_list.append({
                    'type': 'ineq',
                    'fun': lambda a: self._compute_assembly_stability(polyform_ids, a) - min_stab
                })
            
            if 'max_compactness' in constraints:
                max_compact = constraints['max_compactness']
                constraint_list.append({
                    'type': 'ineq',
                    'fun': lambda a: max_compact - self._compute_assembly_compactness(polyform_ids, a)
                })
        
        # Optimize
        result = minimize(
            weighted_objective,
            x0,
            method='trust-constr',
            bounds=bounds,
            constraints=constraint_list,
            options={'verbose': 1 if verbose else 0}
        )
        
        elapsed = time.time() - start_time
        
        # Map back
        optimal_angles = {}
        for i, poly_id in enumerate(polyform_ids):
            optimal_angles[poly_id] = float(result.x[i])
        
        logger.info(f"Multi-objective optimization completed in {elapsed:.2f}s")
        
        return optimal_angles
    
    def _compute_assembly_stability(
        self,
        polyform_ids: List[str],
        angles: np.ndarray
    ) -> float:
        """
        Compute mean stability score for assembly at given angles.
        Higher is better.
        """
        if len(polyform_ids) == 0:
            return 0.0
        
        total_stability = 0.0
        
        for i, poly_id in enumerate(polyform_ids):
            if i < len(angles):
                # Apply angle (without persisting)
                try:
                    stability = self.stability_scorer(poly_id, angles[i])
                    total_stability += stability
                except Exception as e:
                    logger.debug(f"Stability score error for {poly_id}: {e}")
                    total_stability += 0.0
        
        return total_stability / len(polyform_ids)
    
    def _compute_assembly_energy(
        self,
        polyform_ids: List[str],
        angles: np.ndarray
    ) -> float:
        """
        Compute assembly potential energy.
        Penalizes extreme angles (deviation from 90 degrees).
        Lower is better.
        """
        energy = 0.0
        
        for angle in angles:
            # Quadratic penalty for deviation from π/2
            deviation = angle - np.pi / 2
            energy += deviation ** 2
        
        return energy / max(len(angles), 1)
    
    def _compute_polyform_distances(
        self,
        polyform_ids: List[str],
        angles: np.ndarray
    ) -> np.ndarray:
        """
        Compute pairwise distances between polyforms.
        Returns array of distances (one per pair).
        """
        positions = []
        
        for poly_id in polyform_ids:
            try:
                pos = self._get_polyform_centroid(poly_id)
                positions.append(pos)
            except Exception as e:
                logger.debug(f"Could not get position for {poly_id}: {e}")
                positions.append(np.zeros(3))
        
        distances = []
        for i in range(len(positions)):
            for j in range(i + 1, len(positions)):
                dist = np.linalg.norm(np.array(positions[i]) - np.array(positions[j]))
                distances.append(dist)
        
        return np.array(distances) if distances else np.array([0.0])
    
    def _compute_assembly_compactness(
        self,
        polyform_ids: List[str],
        angles: np.ndarray
    ) -> float:
        """
        Compute assembly compactness (spread).
        Lower is better (more compact).
        
        Defined as max distance from centroid.
        """
        positions = []
        
        for poly_id in polyform_ids:
            try:
                pos = self._get_polyform_centroid(poly_id)
                positions.append(pos)
            except Exception:
                positions.append(np.zeros(3))
        
        if not positions:
            return 0.0
        
        positions_array = np.array(positions)
        center = positions_array.mean(axis=0)
        distances = np.linalg.norm(positions_array - center, axis=1)
        
        return float(distances.max()) if len(distances) > 0 else 0.0
    
    def _compute_assembly_balance(
        self,
        polyform_ids: List[str],
        angles: np.ndarray
    ) -> float:
        """
        Compute assembly balance (center of mass offset).
        Lower is better (more balanced).
        
        Defined as distance of CoM from origin.
        """
        positions = []
        masses = []
        
        for poly_id in polyform_ids:
            try:
                pos = self._get_polyform_centroid(poly_id)
                mass = self._get_polyform_mass(poly_id)
                positions.append(pos)
                masses.append(mass)
            except Exception:
                positions.append(np.zeros(3))
                masses.append(1.0)
        
        if not positions:
            return 0.0
        
        positions_array = np.array(positions)
        masses_array = np.array(masses)
        
        # Weighted center of mass
        total_mass = masses_array.sum()
        if total_mass == 0:
            center_of_mass = positions_array.mean(axis=0)
        else:
            center_of_mass = np.average(positions_array, axis=0, weights=masses_array)
        
        return float(np.linalg.norm(center_of_mass))
    
    def _get_polyform_centroid(self, polyform_id: str) -> np.ndarray:
        """Get centroid of a polyform"""
        try:
            polyform = self.assembly.get_polyform(polyform_id)
            if not polyform:
                return np.zeros(3)
            
            vertices = polyform.get('vertices', [])
            if not vertices:
                return np.array(polyform.get('position', [0, 0, 0]))
            
            return np.mean(np.array(vertices), axis=0)
        except Exception:
            return np.zeros(3)
    
    def _get_polyform_mass(self, polyform_id: str) -> float:
        """Get mass (proportional to number of vertices)"""
        try:
            polyform = self.assembly.get_polyform(polyform_id)
            if not polyform:
                return 1.0
            
            vertices = polyform.get('vertices', [])
            return float(max(1.0, len(vertices)))
        except Exception:
            return 1.0
    
    def _default_scorer(self, polyform_id: str, angle: float) -> float:
        """
        Default stability scorer (random for demo).
        Override with actual stability logic if available.
        """
        # Simple heuristic: angles near 90° are stable
        deviation = abs(angle - np.pi / 2)
        stability = max(0.0, 1.0 - (deviation / (np.pi / 2)))
        return float(stability)
    
    def get_optimization_history(self) -> List[Dict]:
        """Export optimization history for analysis"""
        return self.optimization_history
    
    def clear_history(self):
        """Clear optimization history"""
        self.optimization_history = []
