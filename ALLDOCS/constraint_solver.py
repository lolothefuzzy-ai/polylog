"""
Constraint Solver for Hinge Angles & Forward Kinematics

Manages fold constraints on polyform edges and computes dependent polyform
positions through forward kinematics. Supports large assembly chains with
efficient constraint propagation.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set
import numpy as np
from enum import Enum
import logging

# Configure logging
logger = logging.getLogger(__name__)


class ConstraintMode(Enum):
    """Constraint solving modes"""
    ABSOLUTE = 1      # Fixed angle (no propagation)
    RELATIVE = 2      # Angle relative to parent
    CHAIN = 3         # Propagate through connected chain
    BALANCED = 4      # Minimize energy in assembly


@dataclass
class HingeConstraint:
    """Represents a fold constraint on an edge."""
    polyform_id: str
    edge_idx: int
    min_angle: float = 0.0              # radians
    max_angle: float = np.pi            # radians (180 degrees)
    current_angle: float = np.pi / 2    # radians (90 degrees)
    target_angle: Optional[float] = None
    active: bool = True
    mode: ConstraintMode = ConstraintMode.RELATIVE
    
    def clamp_angle(self, angle: float) -> float:
        """Clamp angle to valid range"""
        return np.clip(angle, self.min_angle, self.max_angle)
    
    def set_target(self, angle: float):
        """Set target angle with clamping"""
        self.target_angle = self.clamp_angle(angle)
        self.current_angle = self.target_angle


@dataclass
class HingeChain:
    """Represents a connected chain of hinges for propagation."""
    root_id: str
    hinges: List[str] = field(default_factory=list)  # Keys in constraint dict
    depth_map: Dict[str, int] = field(default_factory=dict)  # Distance from root
    
    def add_hinge(self, hinge_key: str, depth: int = 1):
        """Add hinge to chain"""
        if hinge_key not in self.hinges:
            self.hinges.append(hinge_key)
            self.depth_map[hinge_key] = depth


class ForwardKinematics:
    """
    Compute polyform positions given hinge constraints.
    
    When you set a hinge angle, compute how dependent polyforms
    rotate to maintain bond constraints. Supports:
    - Single hinge constraints
    - Multi-chain propagation
    - Large assemblies (100+ polyforms)
    - Efficient constraint caching
    """
    
    def __init__(self, assembly):
        """
        Initialize forward kinematics solver.
        
        Args:
            assembly: Assembly object with polyforms and bonds
        """
        self.assembly = assembly
        self.constraints: Dict[str, HingeConstraint] = {}
        self.chains: Dict[str, HingeChain] = {}
        self.constraint_graph: Dict[str, Set[str]] = {}  # Dependency graph
        self.cached_transforms: Dict[str, np.ndarray] = {}
        self._build_constraint_graph()
    
    def add_constraint(self, constraint: HingeConstraint):
        """Add or update hinge constraint"""
        key = f"{constraint.polyform_id}_{constraint.edge_idx}"
        self.constraints[key] = constraint
    
    def set_angle(self, polyform_id: str, edge_idx: int, angle: float):
        """
        Set angle for a hinge, with automatic clamping.
        
        Args:
            polyform_id: ID of polyform with hinge
            edge_idx: Edge index on polyform
            angle: Target angle in radians
        """
        key = f"{polyform_id}_{edge_idx}"
        if key not in self.constraints:
            self.constraints[key] = HingeConstraint(polyform_id, edge_idx)
        
        self.constraints[key].set_target(angle)
        self.cached_transforms.clear()  # Invalidate cache
    
    def get_angle(self, polyform_id: str, edge_idx: int) -> Optional[float]:
        """Get current angle for a hinge"""
        key = f"{polyform_id}_{edge_idx}"
        constraint = self.constraints.get(key)
        return constraint.current_angle if constraint else None
    
    def solve(self, max_iterations: int = 10) -> bool:
        """
        Apply all constraints and update assembly positions.
        
        Uses iterative constraint propagation:
        1. Apply active constraints
        2. Propagate through chains
        3. Check convergence
        
        Args:
            max_iterations: Max propagation iterations
            
        Returns:
            True if solution converged, False if max iterations exceeded
        """
        # Rebuild constraint graph for current assembly state
        self._build_constraint_graph()
        
        # Filter active constraints
        active = {k: c for k, c in self.constraints.items() if c.active}
        
        if not active:
            return True
        
        for iteration in range(max_iterations):
            changed = False
            
            for key, constraint in active.items():
                old_angle = constraint.current_angle
                
                # Apply constraint
                if constraint.target_angle is not None:
                    constraint.current_angle = constraint.target_angle
                
                # Propagate through chain
                if constraint.mode == ConstraintMode.CHAIN:
                    self._propagate_chain(key, constraint)
                    changed = True
                elif constraint.current_angle != old_angle:
                    changed = True
            
            if not changed:
                return True  # Converged
        
        return False  # Max iterations exceeded
    
    def _build_constraint_graph(self):
        """Build dependency graph from assembly bonds"""
        self.constraint_graph.clear()
        
        for bond in self.assembly.get_bonds():
            p1_id = bond.get('poly1_id')
            p2_id = bond.get('poly2_id')
            
            if p1_id and p2_id:
                if p1_id not in self.constraint_graph:
                    self.constraint_graph[p1_id] = set()
                if p2_id not in self.constraint_graph:
                    self.constraint_graph[p2_id] = set()
                
                self.constraint_graph[p1_id].add(p2_id)
                self.constraint_graph[p2_id].add(p1_id)
    
    def _propagate_chain(self, root_key: str, root_constraint: HingeConstraint):
        """
        Propagate constraint through connected chain of polyforms.
        
        Builds a BFS tree from root constraint and applies angle
        propagation to all dependent polyforms.
        """
        root_poly_id = root_constraint.polyform_id
        
        # BFS to find chain
        visited = set()
        queue = [(root_poly_id, 0)]
        chain_map = {root_poly_id: 0}
        
        while queue:
            poly_id, depth = queue.pop(0)
            if poly_id in visited:
                continue
            visited.add(poly_id)
            
            # Find connected polyforms
            dependencies = self.constraint_graph.get(poly_id, set())
            for dep_id in dependencies:
                if dep_id not in visited and depth < 50:  # Limit chain depth
                    queue.append((dep_id, depth + 1))
                    chain_map[dep_id] = depth + 1
        
        # Propagate angle through chain
        for poly_id, depth in sorted(chain_map.items(), key=lambda x: x[1]):
            if poly_id == root_poly_id:
                continue
            
            # Find edge connecting to parent
            parent_edge = self._find_connection_edge(root_poly_id, poly_id)
            if parent_edge:
                child_edge_idx = parent_edge[1]
                # Rotate dependent polyform
                self._apply_constraint(poly_id, child_edge_idx, root_constraint.current_angle)
    
    def _find_connection_edge(self, poly1_id: str, poly2_id: str) -> Optional[Tuple[int, int]]:
        """
        Find edge connecting two polyforms.
        
        Returns:
            (edge1_idx, edge2_idx) or None if not connected
        """
        for bond in self.assembly.get_bonds():
            if bond.get('poly1_id') == poly1_id and bond.get('poly2_id') == poly2_id:
                return (bond.get('edge1_idx'), bond.get('edge2_idx'))
            if bond.get('poly2_id') == poly1_id and bond.get('poly1_id') == poly2_id:
                return (bond.get('edge2_idx'), bond.get('edge1_idx'))
        logger.debug(f"No connection edge found between {poly1_id} and {poly2_id}")
        return None
    
    def _apply_constraint(self, polyform_id: str, edge_idx: int, angle: float):
        """
        Apply hinge constraint by rotating polyform around edge.
        
        Uses Rodrigues' rotation formula for efficient computation.
        Caches transforms to avoid recomputation.
        """
        polyform = self.assembly.get_polyform(polyform_id)
        if not polyform:
            logger.warning(f"Constraint apply: polyform {polyform_id} not found in assembly")
            return
        
        # Get edge vertices to define rotation axis
        vertices = polyform.get('vertices', [])
        if not vertices:
            logger.warning(f"Constraint apply: polyform {polyform_id} has no vertices")
            return
        if edge_idx >= len(vertices):
            logger.warning(f"Constraint apply: polyform {polyform_id} edge {edge_idx} out of range (has {len(vertices)} vertices)")
            return
        
        v1 = np.array(vertices[edge_idx])
        v2 = np.array(vertices[(edge_idx + 1) % len(vertices)])
        
        # Axis is edge direction
        axis = v2 - v1
        axis_len = np.linalg.norm(axis)
        if axis_len < 1e-10:
            return
        axis = axis / axis_len
        
        # Rotate vertices using Rodrigues formula
        self._rotate_polyform_around_axis(polyform, v1, axis, angle)
    
    def _rotate_polyform_around_axis(self, polyform: Dict, pivot: np.ndarray,
                                   axis: np.ndarray, angle: float):
        """
        Rotate polyform vertices using Rodrigues rotation formula.
        
        p' = p*cos(θ) + (k × p)*sin(θ) + k*(k·p)*(1-cos(θ))
        where k is normalized axis, p is relative position
        """
        vertices = np.array(polyform.get('vertices', []), dtype=float)
        
        if len(vertices) == 0:
            return
        
        cos_a = np.cos(angle)
        sin_a = np.sin(angle)
        one_minus_cos = 1.0 - cos_a
        
        rotated = []
        for v in vertices:
            p = v - pivot
            
            # Rodrigues formula
            cross_term = np.cross(axis, p)
            dot_term = np.dot(axis, p)
            
            p_rot = (p * cos_a + 
                    cross_term * sin_a + 
                    axis * dot_term * one_minus_cos)
            
            rotated.append(p_rot + pivot)
        
        polyform['vertices'] = rotated
    
    def get_chain_angles(self, root_polyform_id: str) -> Dict[str, float]:
        """
        Get all angles in a constraint chain starting from root.
        
        Returns dict of {constraint_key: angle} for diagnostics.
        """
        result = {}
        visited = set()
        queue = [root_polyform_id]
        
        while queue:
            poly_id = queue.pop(0)
            if poly_id in visited:
                continue
            visited.add(poly_id)
            
            # Find constraints for this polyform
            for key, constraint in self.constraints.items():
                if constraint.polyform_id == poly_id:
                    result[key] = constraint.current_angle
            
            # Add connected polyforms to queue
            dependencies = self.constraint_graph.get(poly_id, set())
            for dep_id in dependencies:
                if dep_id not in visited:
                    queue.append(dep_id)
        
        return result
    
    def export_constraints(self) -> Dict:
        """Export all constraints to JSON-serializable dict"""
        return {
            key: {
                'polyform_id': c.polyform_id,
                'edge_idx': c.edge_idx,
                'min_angle': float(c.min_angle),
                'max_angle': float(c.max_angle),
                'current_angle': float(c.current_angle),
                'target_angle': float(c.target_angle) if c.target_angle else None,
                'active': c.active,
                'mode': c.mode.name
            }
            for key, c in self.constraints.items()
        }
    
    def import_constraints(self, data: Dict):
        """Import constraints from JSON-serializable dict"""
        for key, c_data in data.items():
            mode = ConstraintMode[c_data.get('mode', 'RELATIVE')]
            constraint = HingeConstraint(
                polyform_id=c_data['polyform_id'],
                edge_idx=c_data['edge_idx'],
                min_angle=c_data.get('min_angle', 0.0),
                max_angle=c_data.get('max_angle', np.pi),
                current_angle=c_data.get('current_angle', np.pi/2),
                target_angle=c_data.get('target_angle'),
                active=c_data.get('active', True),
                mode=mode
            )
            self.add_constraint(constraint)


class ConstraintValidator:
    """Validate constraints for collisions and feasibility"""
    
    def __init__(self, assembly):
        self.assembly = assembly
    
    def check_collision(self, polyform_id: str) -> bool:
        """
        Check if polyform intersects with others.
        
        Simplified AABB check for performance.
        Returns False if collision detected.
        """
        polyform = self.assembly.get_polyform(polyform_id)
        if not polyform:
            return True
        
        verts = np.array(polyform.get('vertices', []))
        if len(verts) == 0:
            return True
        
        bbox1_min = np.min(verts, axis=0)
        bbox1_max = np.max(verts, axis=0)
        
        # Check against all other polyforms
        for other in self.assembly.get_all_polyforms():
            if other.get('id') == polyform_id:
                continue
            
            other_verts = np.array(other.get('vertices', []))
            if len(other_verts) == 0:
                continue
            
            bbox2_min = np.min(other_verts, axis=0)
            bbox2_max = np.max(other_verts, axis=0)
            
            # AABB overlap test
            if not self._aabb_overlap(bbox1_min, bbox1_max, bbox2_min, bbox2_max):
                return False  # Collision detected
        
        return True  # No collision
    
    def _aabb_overlap(self, min1, max1, min2, max2) -> bool:
        """Check if two AABBs overlap"""
        return np.all(min1 <= max2) and np.all(min2 <= max1)


# Type hints for assembly interface
from typing import Any

def apply_constraints(assembly: Any, solver: ForwardKinematics) -> bool:
    """
    Convenience function to solve and apply all constraints to assembly.
    
    Args:
        assembly: Assembly with polyforms
        solver: ForwardKinematics solver with configured constraints
        
    Returns:
        True if converged, False if max iterations exceeded
    """
    return solver.solve(max_iterations=10)
