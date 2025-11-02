"""
Unified Bonding System

Consolidates all bonding mechanisms:
- Manual bond creation
- Automated bond discovery  
- Contextual bonding
- Hinge-based 3D bonds
- Edge alignment detection

Provides single interface for bond management across 2D and 3D modes.
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


@dataclass
class BondCandidate:
    """Potential bond between two polyforms."""
    poly1_id: str
    poly2_id: str
    edge1_idx: int
    edge2_idx: int
    alignment_score: float
    distance: float
    is_3d: bool = False
    hinge_data: Optional[Dict[str, Any]] = None


class UnifiedBondingSystem:
    """
    Unified interface for all bonding operations.
    
    Handles:
    - Bond creation and validation
    - Edge alignment detection
    - Hinge creation for 3D bonds
    - Bond strength scoring
    - Automatic bond discovery
    """
    
    def __init__(self, hinge_manager=None):
        """
        Initialize bonding system.
        
        Args:
            hinge_manager: Optional HingeManager for 3D mode
        """
        self.hinge_manager = hinge_manager
        self._enable_3d = hinge_manager is not None
        
        # Bond validation thresholds
        self.distance_threshold = 0.1
        self.alignment_threshold = 0.95  # cos(angle) threshold
        self.min_overlap = 0.8  # Minimum edge overlap ratio
    
    def create_bond(self, poly1_id: str, edge1_idx: int,
                   poly2_id: str, edge2_idx: int,
                   assembly, auto_create_hinge: bool = True) -> Optional[Dict[str, Any]]:
        """
        Create a bond between two polyforms.
        
        Args:
            poly1_id: First polyform ID
            edge1_idx: Edge index on first polyform
            poly2_id: Second polyform ID
            edge2_idx: Edge index on second polyform
            assembly: Assembly object
            auto_create_hinge: Automatically create 3D hinge
        
        Returns:
            Bond dict or None if invalid
        """
        poly1 = assembly.get_polyform(poly1_id)
        poly2 = assembly.get_polyform(poly2_id)
        
        if not poly1 or not poly2:
            return None
        
        # Validate bond
        valid, reason = self.validate_bond(poly1, edge1_idx, poly2, edge2_idx)
        if not valid:
            return None
        
        # Create bond dict
        bond = {
            'poly1_id': poly1_id,
            'poly2_id': poly2_id,
            'edge1_idx': edge1_idx,
            'edge2_idx': edge2_idx,
            'creation_mode': 'manual',
            'is_3d': self._enable_3d
        }
        
        # Add to assembly
        assembly.add_bond(bond)
        
        # Create hinge for 3D
        if self._enable_3d and auto_create_hinge and self.hinge_manager:
            hinge_idx = self.hinge_manager.add_bond_as_hinge(bond, assembly)
            if hinge_idx is not None:
                bond['hinge_idx'] = hinge_idx
        
        return bond
    
    def discover_bonds(self, assembly, max_distance: Optional[float] = None) -> List[BondCandidate]:
        """
        Discover potential bonds in an assembly.
        
        Args:
            assembly: Assembly to search
            max_distance: Maximum distance for bond candidates
        
        Returns:
            List of bond candidates sorted by quality
        """
        if max_distance is None:
            max_distance = self.distance_threshold
        
        candidates = []
        polyforms = assembly.get_all_polyforms()
        
        # Check all polyform pairs
        for i, poly1 in enumerate(polyforms):
            for poly2 in polyforms[i+1:]:
                # Check all edge pairs
                edges1 = self._get_edges(poly1)
                edges2 = self._get_edges(poly2)
                
                for e1_idx, edge1 in enumerate(edges1):
                    for e2_idx, edge2 in enumerate(edges2):
                        # Compute alignment and distance
                        score, dist = self._score_edge_pair(edge1, edge2)
                        
                        if dist <= max_distance and score >= self.alignment_threshold:
                            candidate = BondCandidate(
                                poly1_id=poly1['id'],
                                poly2_id=poly2['id'],
                                edge1_idx=e1_idx,
                                edge2_idx=e2_idx,
                                alignment_score=score,
                                distance=dist,
                                is_3d=self._enable_3d
                            )
                            candidates.append(candidate)
        
        # Sort by quality (high score, low distance)
        candidates.sort(key=lambda c: (c.alignment_score, -c.distance), reverse=True)
        
        return candidates
    
    def auto_bond(self, assembly, apply_threshold: float = 0.98) -> List[Dict[str, Any]]:
        """
        Automatically create bonds for well-aligned edges.
        
        Args:
            assembly: Assembly to process
            apply_threshold: Minimum alignment score to auto-bond
        
        Returns:
            List of created bonds
        """
        candidates = self.discover_bonds(assembly)
        created_bonds = []
        
        for candidate in candidates:
            if candidate.alignment_score >= apply_threshold:
                bond = self.create_bond(
                    candidate.poly1_id, candidate.edge1_idx,
                    candidate.poly2_id, candidate.edge2_idx,
                    assembly, auto_create_hinge=True
                )
                if bond:
                    created_bonds.append(bond)
        
        return created_bonds
    
    def validate_bond(self, poly1: Dict, edge1_idx: int,
                     poly2: Dict, edge2_idx: int) -> Tuple[bool, Optional[str]]:
        """
        Validate if a bond is geometrically valid.
        
        Args:
            poly1, poly2: Polyform dicts
            edge1_idx, edge2_idx: Edge indices
        
        Returns:
            (is_valid, reason) tuple
        """
        edges1 = self._get_edges(poly1)
        edges2 = self._get_edges(poly2)
        
        if edge1_idx >= len(edges1):
            return False, "edge1_idx out of range"
        if edge2_idx >= len(edges2):
            return False, "edge2_idx out of range"
        
        edge1 = edges1[edge1_idx]
        edge2 = edges2[edge2_idx]
        
        # Check edge lengths match
        len1 = np.linalg.norm(edge1[1] - edge1[0])
        len2 = np.linalg.norm(edge2[1] - edge2[0])
        
        if abs(len1 - len2) / max(len1, len2) > 0.1:  # 10% tolerance
            return False, "edge_length_mismatch"
        
        # Check alignment
        score, dist = self._score_edge_pair(edge1, edge2)
        
        if dist > self.distance_threshold:
            return False, "distance_too_large"
        
        if score < self.alignment_threshold:
            return False, "poor_alignment"
        
        return True, None
    
    def remove_bond(self, poly1_id: str, edge1_idx: int,
                   poly2_id: str, edge2_idx: int, assembly) -> bool:
        """
        Remove a bond and associated hinge.
        
        Args:
            poly1_id, edge1_idx, poly2_id, edge2_idx: Bond identifiers
            assembly: Assembly object
        
        Returns:
            True if bond was removed
        """
        # Find and remove bond
        bonds = assembly.get_bonds()
        bond_to_remove = None
        
        for bond in bonds:
            if (bond['poly1_id'] == poly1_id and bond['edge1_idx'] == edge1_idx and
                bond['poly2_id'] == poly2_id and bond['edge2_idx'] == edge2_idx):
                bond_to_remove = bond
                break
        
        if not bond_to_remove:
            return False
        
        # Remove hinge if exists
        if 'hinge_idx' in bond_to_remove and self.hinge_manager:
            self.hinge_manager.graph.remove_hinge(bond_to_remove['hinge_idx'])
        
        # Remove bond
        assembly.remove_bond(bond_to_remove)
        
        return True
    
    def get_bond_strength(self, bond: Dict, assembly) -> float:
        """
        Compute strength/quality score for a bond.
        
        Args:
            bond: Bond dict
            assembly: Assembly object
        
        Returns:
            Strength score (0.0 to 1.0)
        """
        poly1 = assembly.get_polyform(bond['poly1_id'])
        poly2 = assembly.get_polyform(bond['poly2_id'])
        
        if not poly1 or not poly2:
            return 0.0
        
        edges1 = self._get_edges(poly1)
        edges2 = self._get_edges(poly2)
        
        edge1 = edges1[bond['edge1_idx']]
        edge2 = edges2[bond['edge2_idx']]
        
        score, dist = self._score_edge_pair(edge1, edge2)
        
        # Combine alignment and distance into strength score
        distance_score = max(0, 1.0 - dist / self.distance_threshold)
        strength = (score + distance_score) / 2.0
        
        return strength
    
    def update_bond_with_hinge(self, bond: Dict, assembly) -> bool:
        """
        Update or create hinge for an existing bond.
        
        Args:
            bond: Bond dict
            assembly: Assembly object
        
        Returns:
            True if hinge was created/updated
        """
        if not self._enable_3d or not self.hinge_manager:
            return False
        
        # Remove old hinge if exists
        if 'hinge_idx' in bond:
            self.hinge_manager.graph.remove_hinge(bond['hinge_idx'])
        
        # Create new hinge
        hinge_idx = self.hinge_manager.add_bond_as_hinge(bond, assembly)
        
        if hinge_idx is not None:
            bond['hinge_idx'] = hinge_idx
            return True
        
        return False
    
    # Helper methods
    
    def _get_edges(self, poly: Dict) -> List[Tuple[np.ndarray, np.ndarray]]:
        """Get edges as (start, end) vertex pairs."""
        verts = np.array(poly.get('vertices', []))
        n = len(verts)
        
        if n < 2:
            return []
        
        edges = []
        for i in range(n):
            edges.append((verts[i], verts[(i+1) % n]))
        
        return edges
    
    def _score_edge_pair(self, edge1: Tuple[np.ndarray, np.ndarray],
                        edge2: Tuple[np.ndarray, np.ndarray]) -> Tuple[float, float]:
        """
        Score alignment and distance between two edges.
        
        Returns:
            (alignment_score, distance) tuple
        """
        # Edge vectors
        v1 = edge1[1] - edge1[0]
        v2 = edge2[1] - edge2[0]
        
        # Normalize
        v1_norm = v1 / (np.linalg.norm(v1) + 1e-10)
        v2_norm = v2 / (np.linalg.norm(v2) + 1e-10)
        
        # Alignment: edges should be anti-parallel (pointing opposite directions)
        dot = np.dot(v1_norm, v2_norm)
        alignment = abs(dot)  # 1.0 = parallel or anti-parallel
        
        # Distance: average distance between edge midpoints
        mid1 = (edge1[0] + edge1[1]) / 2.0
        mid2 = (edge2[0] + edge2[1]) / 2.0
        distance = np.linalg.norm(mid1 - mid2)
        
        return alignment, distance
