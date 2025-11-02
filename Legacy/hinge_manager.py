"""
Hinge Manager for tracking fold relationships and 3D rotations.

This module maintains a graph of hinge connections between polyforms
and provides utilities for computing and applying 3D rotations around hinge axes.
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from geometry3d import MeshData, rotation_matrix_axis_angle, transform_mesh


@dataclass
class Hinge:
    """Represents a fold hinge between two polyforms."""
    poly1_id: str
    poly2_id: str
    edge1_idx: int
    edge2_idx: int
    axis_start: np.ndarray  # 3D point
    axis_end: np.ndarray    # 3D point
    fold_angle: float = 0.0  # Radians
    is_active: bool = True
    
    def get_axis(self) -> np.ndarray:
        """Get normalized hinge axis vector."""
        axis = self.axis_end - self.axis_start
        length = np.linalg.norm(axis)
        if length < 1e-10:
            return np.array([0.0, 0.0, 1.0])  # Default to z-axis
        return axis / length
    
    def get_axis_midpoint(self) -> np.ndarray:
        """Get midpoint of hinge axis."""
        return (self.axis_start + self.axis_end) / 2.0


class HingeGraph:
    """Graph structure for managing hinge relationships in an assembly."""
    
    def __init__(self):
        self.hinges: List[Hinge] = []
        self.poly_to_hinges: Dict[str, List[int]] = {}  # poly_id -> list of hinge indices
    
    def add_hinge(self, hinge: Hinge) -> int:
        """
        Add a hinge to the graph.
        
        Args:
            hinge: Hinge object to add
        
        Returns:
            Index of the added hinge
        """
        idx = len(self.hinges)
        self.hinges.append(hinge)
        
        # Update poly_to_hinges mapping
        for poly_id in [hinge.poly1_id, hinge.poly2_id]:
            if poly_id not in self.poly_to_hinges:
                self.poly_to_hinges[poly_id] = []
            self.poly_to_hinges[poly_id].append(idx)
        
        return idx
    
    def get_hinges_for_poly(self, poly_id: str) -> List[Hinge]:
        """Get all hinges connected to a polyform."""
        indices = self.poly_to_hinges.get(poly_id, [])
        return [self.hinges[i] for i in indices if i < len(self.hinges)]
    
    def get_hinge(self, index: int) -> Optional[Hinge]:
        """Get hinge by index."""
        if 0 <= index < len(self.hinges):
            return self.hinges[index]
        return None
    
    def remove_hinge(self, index: int):
        """Remove a hinge from the graph."""
        if 0 <= index < len(self.hinges):
            hinge = self.hinges[index]
            hinge.is_active = False
    
    def compact(self) -> Dict[int, int]:
        """
        Remove inactive hinges and rebuild indices.
        
        Returns:
            Mapping of old indices to new indices for hinges that remain
        """
        # Collect active hinges
        new_hinges = [h for h in self.hinges if h.is_active]
        
        if len(new_hinges) == len(self.hinges):
            # No compaction needed
            return {i: i for i in range(len(self.hinges))}
        
        # Build old->new index mapping
        index_map = {}
        new_idx = 0
        for old_idx, hinge in enumerate(self.hinges):
            if hinge.is_active:
                index_map[old_idx] = new_idx
                new_idx += 1
        
        # Replace hinge list
        self.hinges = new_hinges
        
        # Rebuild poly_to_hinges with new indices
        self.poly_to_hinges.clear()
        
        for new_idx, hinge in enumerate(self.hinges):
            for poly_id in [hinge.poly1_id, hinge.poly2_id]:
                if poly_id not in self.poly_to_hinges:
                    self.poly_to_hinges[poly_id] = []
                self.poly_to_hinges[poly_id].append(new_idx)
        
        return index_map
    
    def should_compact(self, threshold: float = 0.5) -> bool:
        """
        Check if compaction would be beneficial.
        
        Args:
            threshold: Compact if inactive hinges exceed this fraction (0-1)
        
        Returns:
            True if compaction recommended
        """
        if len(self.hinges) == 0:
            return False
        
        active_count = sum(1 for h in self.hinges if h.is_active)
        inactive_fraction = 1.0 - (active_count / len(self.hinges))
        return inactive_fraction > threshold
    
    def clear(self):
        """Clear all hinges."""
        self.hinges.clear()
        self.poly_to_hinges.clear()
    
    def get_connected_component(self, start_poly_id: str) -> List[str]:
        """
        Get all polyform IDs connected to start_poly_id via hinges.
        
        Args:
            start_poly_id: Starting polyform ID
        
        Returns:
            List of connected polyform IDs (including start)
        """
        visited = set()
        queue = [start_poly_id]
        
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            
            # Find all hinges connected to current
            for hinge in self.get_hinges_for_poly(current):
                if not hinge.is_active:
                    continue
                
                # Add the other polyform to queue
                other_id = hinge.poly2_id if hinge.poly1_id == current else hinge.poly1_id
                if other_id not in visited:
                    queue.append(other_id)
        
        return list(visited)


class HingeManager:
    """Manages hinge transformations and fold operations."""
    
    def __init__(self, auto_compact: bool = True, compact_threshold: float = 0.5):
        """
        Initialize hinge manager.
        
        Args:
            auto_compact: Automatically compact hinge graph when beneficial
            compact_threshold: Fraction of inactive hinges triggering compaction (0-1)
        """
        self.graph = HingeGraph()
        self.auto_compact = auto_compact
        self.compact_threshold = compact_threshold
    
    def create_hinge_from_bond(self, bond: Dict[str, Any], assembly) -> Optional[Hinge]:
        """
        Create a hinge from a bond in an assembly.
        
        Args:
            bond: Bond dictionary with poly1_id, poly2_id, edge1_idx, edge2_idx
            assembly: Assembly object to get polyform data
        
        Returns:
            Hinge object or None if invalid
        """
        poly1 = assembly.get_polyform(bond['poly1_id'])
        poly2 = assembly.get_polyform(bond['poly2_id'])
        
        if poly1 is None or poly2 is None:
            return None
        
        # Get edge endpoints
        v1_start, v1_end = self._get_edge_endpoints(poly1, int(bond['edge1_idx']))
        v2_start, v2_end = self._get_edge_endpoints(poly2, int(bond['edge2_idx']))
        
        # Average the two edges to get hinge axis
        # (assumes edges are aligned after bonding)
        axis_start = (v1_start + v2_start) / 2.0
        axis_end = (v1_end + v2_end) / 2.0
        
        hinge = Hinge(
            poly1_id=bond['poly1_id'],
            poly2_id=bond['poly2_id'],
            edge1_idx=int(bond['edge1_idx']),
            edge2_idx=int(bond['edge2_idx']),
            axis_start=axis_start,
            axis_end=axis_end,
            fold_angle=0.0
        )
        
        return hinge
    
    def add_bond_as_hinge(self, bond: Dict[str, Any], assembly) -> Optional[int]:
        """
        Add a bond as a hinge to the graph.
        
        Args:
            bond: Bond dictionary
            assembly: Assembly object
        
        Returns:
            Hinge index or None if failed
        """
        hinge = self.create_hinge_from_bond(bond, assembly)
        if hinge is not None:
            idx = self.graph.add_hinge(hinge)
            # Check if compaction is needed
            if self.auto_compact and self.graph.should_compact(self.compact_threshold):
                self.graph.compact()
            return idx
        return None
    
    def compute_fold_transform(self, hinge: Hinge, fold_angle: float,
                              pivot_point: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Compute 4x4 transformation matrix for folding around a hinge.
        
        Args:
            hinge: Hinge to fold around
            fold_angle: Fold angle in radians
            pivot_point: Optional pivot point (default: hinge midpoint)
        
        Returns:
            4x4 transformation matrix
        """
        if pivot_point is None:
            pivot_point = hinge.get_axis_midpoint()
        
        axis = hinge.get_axis()
        
        # Create transformation: translate to origin, rotate, translate back
        # T = T(pivot) * R(axis, angle) * T(-pivot)
        
        # Translation matrices
        translate_to_origin = np.eye(4)
        translate_to_origin[:3, 3] = -pivot_point
        
        translate_back = np.eye(4)
        translate_back[:3, 3] = pivot_point
        
        # Rotation matrix
        rotation = rotation_matrix_axis_angle(axis, fold_angle)
        
        # Combine: translate back * rotate * translate to origin
        transform = translate_back @ rotation @ translate_to_origin
        
        return transform
    
    def apply_fold_to_mesh(self, mesh: MeshData, hinge: Hinge, fold_angle: float) -> MeshData:
        """
        Apply a fold transformation to a mesh.
        
        Args:
            mesh: Input MeshData
            hinge: Hinge to fold around
            fold_angle: Fold angle in radians
        
        Returns:
            Transformed MeshData
        """
        transform = self.compute_fold_transform(hinge, fold_angle)
        return transform_mesh(mesh, transform)
    
    def compute_out_of_plane_rotation(self, hinge: Hinge, target_normal: np.ndarray,
                                     current_normal: np.ndarray) -> float:
        """
        Compute fold angle needed to rotate current_normal to align with target_normal.
        
        This is used for out-of-plane folding where a polyform needs to rotate
        around a hinge to match a target orientation.
        
        Args:
            hinge: Hinge axis to rotate around
            target_normal: Desired normal direction
            current_normal: Current normal direction
        
        Returns:
            Fold angle in radians
        """
        axis = hinge.get_axis()
        
        # Project normals onto plane perpendicular to hinge axis
        target_proj = target_normal - np.dot(target_normal, axis) * axis
        current_proj = current_normal - np.dot(current_normal, axis) * axis
        
        # Normalize projections
        target_proj = target_proj / (np.linalg.norm(target_proj) + 1e-10)
        current_proj = current_proj / (np.linalg.norm(current_proj) + 1e-10)
        
        # Compute angle between projections
        dot = np.clip(np.dot(target_proj, current_proj), -1.0, 1.0)
        angle = np.arccos(dot)
        
        # Determine sign using cross product
        cross = np.cross(current_proj, target_proj)
        if np.dot(cross, axis) < 0:
            angle = -angle
        
        return angle
    
    def rebuild_from_assembly(self, assembly):
        """
        Rebuild hinge graph from all bonds in an assembly.
        
        Args:
            assembly: Assembly object with bonds
        """
        self.graph.clear()
        
        for bond in assembly.get_bonds():
            self.add_bond_as_hinge(bond, assembly)
    
    def get_fold_chain(self, from_poly_id: str, to_poly_id: str) -> List[Hinge]:
        """
        Find chain of hinges connecting two polyforms.
        
        Uses BFS to find shortest path.
        
        Args:
            from_poly_id: Starting polyform ID
            to_poly_id: Target polyform ID
        
        Returns:
            List of hinges forming the connection path (empty if no path)
        """
        if from_poly_id == to_poly_id:
            return []
        
        # BFS to find path
        queue = [(from_poly_id, [])]  # (current_id, hinge_path)
        visited = {from_poly_id}
        
        while queue:
            current_id, path = queue.pop(0)
            
            for hinge in self.graph.get_hinges_for_poly(current_id):
                if not hinge.is_active:
                    continue
                
                # Get the other polyform
                other_id = hinge.poly2_id if hinge.poly1_id == current_id else hinge.poly1_id
                
                if other_id == to_poly_id:
                    # Found the target
                    return path + [hinge]
                
                if other_id not in visited:
                    visited.add(other_id)
                    queue.append((other_id, path + [hinge]))
        
        return []  # No path found
    
    def _get_edge_endpoints(self, poly: Dict[str, Any], edge_idx: int) -> Tuple[np.ndarray, np.ndarray]:
        """Get start and end points of an edge."""
        verts = np.array(poly.get('vertices', []), dtype=np.float64)
        n = len(verts)
        if n < 2:
            return np.zeros(3), np.zeros(3)
        
        i = edge_idx % n
        j = (i + 1) % n
        
        return verts[i], verts[j]
    
    def clear(self):
        """Clear all hinges."""
        self.graph.clear()


# Utility functions for common hinge operations

def compute_hinge_axis_from_vertices(v1_start: np.ndarray, v1_end: np.ndarray,
                                     v2_start: np.ndarray, v2_end: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute hinge axis by averaging two edge segments.
    
    Args:
        v1_start, v1_end: First edge endpoints
        v2_start, v2_end: Second edge endpoints
    
    Returns:
        Tuple of (axis_start, axis_end)
    """
    axis_start = (v1_start + v2_start) / 2.0
    axis_end = (v1_end + v2_end) / 2.0
    return axis_start, axis_end


def is_valid_hinge(axis_start: np.ndarray, axis_end: np.ndarray, min_length: float = 1e-6) -> bool:
    """
    Check if a hinge axis is valid (has sufficient length).
    
    Args:
        axis_start: Hinge start point
        axis_end: Hinge end point
        min_length: Minimum acceptable length
    
    Returns:
        True if valid, False otherwise
    """
    length = np.linalg.norm(axis_end - axis_start)
    return length >= min_length
