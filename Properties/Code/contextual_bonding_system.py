"""
Contextual Auto-Bonding System

Automatically bonds edges based on:
- Historical success patterns (saved in library)
- Geometric compatibility
- Structural context
- User preferences
- Machine learning from past assemblies
"""
import numpy as np
import json
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict
import math


@dataclass
class BondPattern:
    """Learned pattern for successful bonds."""
    poly1_sides: int
    poly2_sides: int
    edge1_idx: int
    edge2_idx: int
    relative_position: Tuple[float, float, float]  # Centroid offset
    relative_angle: float  # Orientation difference
    success_count: int = 1
    total_attempts: int = 1
    avg_stability: float = 0.0
    context_tags: List[str] = None  # e.g., ['net', 'prism', 'cube']
    
    def success_rate(self) -> float:
        """Return success rate [0-1]."""
        return self.success_count / max(1, self.total_attempts)
    
    def confidence_score(self) -> float:
        """
        Confidence in this pattern.
        
        Combines success rate with sample size and stability.
        """
        # Base: success rate
        base = self.success_rate()
        
        # Boost for more samples (plateaus at ~20 samples)
        sample_boost = min(1.0, self.total_attempts / 20.0)
        
        # Stability factor
        stability_factor = self.avg_stability
        
        return base * 0.5 + sample_boost * 0.3 + stability_factor * 0.2
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return asdict(self)
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'BondPattern':
        """Deserialize from dict."""
        return BondPattern(**data)


class ContextualBondingEngine:
    """
    Engine for contextual auto-bonding.
    
    Learns from:
    1. User-created bonds (tracked in real-time)
    2. Saved assemblies (loaded from library)
    3. Geometric heuristics
    """
    
    def __init__(self, library_path: str = "bond_patterns.json"):
        self.library_path = library_path
        self.patterns: List[BondPattern] = []
        
        # Real-time tracking
        self.current_session_bonds: List[Dict[str, Any]] = []
        
        # Auto-bonding settings
        self.enabled = True
        self.confidence_threshold = 0.6  # Min confidence to auto-bond
        self.max_distance = 0.1  # Max edge endpoint distance
        self.angle_tolerance = 15.0  # degrees
        
        # Context awareness
        self.current_context_tags: List[str] = []
        
        # Load existing patterns
        self.load_patterns()
    
    def load_patterns(self):
        """Load learned patterns from disk."""
        try:
            with open(self.library_path, 'r') as f:
                data = json.load(f)
                self.patterns = [BondPattern.from_dict(p) for p in data]
            print(f"Loaded {len(self.patterns)} bond patterns")
        except FileNotFoundError:
            print("No existing bond patterns found, starting fresh")
            self.patterns = []
    
    def save_patterns(self):
        """Save patterns to disk."""
        data = [p.to_dict() for p in self.patterns]
        with open(self.library_path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Saved {len(self.patterns)} bond patterns")
    
    def record_bond_attempt(self, poly1: Dict[str, Any], poly2: Dict[str, Any],
                           edge1_idx: int, edge2_idx: int, success: bool,
                           stability_score: float = 0.0):
        """
        Record a bond attempt (success or failure).
        
        Updates patterns or creates new ones.
        """
        # Extract features
        sides1 = poly1.get('sides', 0)
        sides2 = poly2.get('sides', 0)
        
        # Compute relative geometry
        pos1 = np.array(poly1.get('position', [0, 0, 0]))
        pos2 = np.array(poly2.get('position', [0, 0, 0]))
        relative_pos = tuple((pos2 - pos1).tolist())
        
        # Orientation (simplified)
        angle1 = poly1.get('rotation', 0.0)
        angle2 = poly2.get('rotation', 0.0)
        relative_angle = angle2 - angle1
        
        # Find matching pattern
        pattern = self._find_matching_pattern(
            sides1, sides2, edge1_idx, edge2_idx, relative_pos, relative_angle
        )
        
        if pattern:
            # Update existing pattern
            pattern.total_attempts += 1
            if success:
                pattern.success_count += 1
            
            # Update running average of stability
            n = pattern.success_count
            pattern.avg_stability = (pattern.avg_stability * (n - 1) + stability_score) / n
        else:
            # Create new pattern
            new_pattern = BondPattern(
                poly1_sides=sides1,
                poly2_sides=sides2,
                edge1_idx=edge1_idx,
                edge2_idx=edge2_idx,
                relative_position=relative_pos,
                relative_angle=relative_angle,
                success_count=1 if success else 0,
                total_attempts=1,
                avg_stability=stability_score if success else 0.0,
                context_tags=self.current_context_tags.copy()
            )
            self.patterns.append(new_pattern)
        
        # Track in session
        self.current_session_bonds.append({
            'poly1_id': poly1.get('id'),
            'poly2_id': poly2.get('id'),
            'edge1': edge1_idx,
            'edge2': edge2_idx,
            'success': success,
            'stability': stability_score,
        })
    
    def _find_matching_pattern(self, sides1: int, sides2: int,
                              edge1: int, edge2: int,
                              rel_pos: Tuple[float, float, float],
                              rel_angle: float,
                              tolerance: float = 0.5) -> Optional[BondPattern]:
        """Find existing pattern matching these parameters."""
        for pattern in self.patterns:
            # Exact topology match
            if (pattern.poly1_sides != sides1 or
                pattern.poly2_sides != sides2 or
                pattern.edge1_idx != edge1 or
                pattern.edge2_idx != edge2):
                continue
            
            # Geometric similarity
            pos_diff = np.linalg.norm(
                np.array(pattern.relative_position) - np.array(rel_pos)
            )
            
            angle_diff = abs(pattern.relative_angle - rel_angle)
            # Normalize angle difference to [0, 180]
            angle_diff = min(angle_diff, 360 - angle_diff)
            
            if pos_diff < tolerance and angle_diff < 30.0:
                return pattern
        
        return None
    
    def suggest_bonds(self, assembly: Any, new_poly: Dict[str, Any],
                     top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Suggest bonds for a newly placed polygon.
        
        Args:
            assembly: Current assembly
            new_poly: Newly added polygon
            top_k: Number of suggestions to return
            
        Returns:
            List of bond suggestions sorted by confidence
        """
        if not self.enabled:
            return []
        
        suggestions = []
        new_sides = new_poly.get('sides', 0)
        new_pos = np.array(new_poly.get('position', [0, 0, 0]))
        
        # Check all existing polygons
        for existing_poly in assembly.get_all_polyforms():
            if existing_poly.get('id') == new_poly.get('id'):
                continue
            
            existing_sides = existing_poly.get('sides', 0)
            existing_pos = np.array(existing_poly.get('position', [0, 0, 0]))
            
            # Quick distance filter
            distance = np.linalg.norm(new_pos - existing_pos)
            if distance > 10.0:  # Too far
                continue
            
            # Check all edge combinations using patterns
            for pattern in self.patterns:
                # Check if pattern matches this pair
                if not self._pattern_matches_pair(
                    pattern, new_sides, existing_sides, new_pos, existing_pos
                ):
                    continue
                
                # Check geometric compatibility
                compat_score = self._check_geometric_compatibility(
                    new_poly, existing_poly,
                    pattern.edge1_idx, pattern.edge2_idx
                )
                
                if compat_score < 0.3:  # Too incompatible
                    continue
                
                # Compute combined confidence
                pattern_conf = pattern.confidence_score()
                combined_conf = pattern_conf * 0.7 + compat_score * 0.3
                
                if combined_conf >= self.confidence_threshold:
                    suggestions.append({
                        'poly1_id': new_poly.get('id'),
                        'poly2_id': existing_poly.get('id'),
                        'edge1_idx': pattern.edge1_idx,
                        'edge2_idx': pattern.edge2_idx,
                        'confidence': combined_conf,
                        'pattern_confidence': pattern_conf,
                        'geometric_score': compat_score,
                        'expected_stability': pattern.avg_stability,
                        'source': 'learned_pattern',
                    })
        
        # Sort by confidence
        suggestions.sort(key=lambda x: x['confidence'], reverse=True)
        
        return suggestions[:top_k]
    
    def _pattern_matches_pair(self, pattern: BondPattern,
                             sides1: int, sides2: int,
                             pos1: np.ndarray, pos2: np.ndarray) -> bool:
        """Check if pattern topology matches this polygon pair."""
        # Check sides
        if pattern.poly1_sides != sides1 or pattern.poly2_sides != sides2:
            return False
        
        # Check approximate position match (loose)
        rel_pos = pos2 - pos1
        pattern_pos = np.array(pattern.relative_position)
        pos_diff = np.linalg.norm(rel_pos - pattern_pos)
        
        # Very loose tolerance for initial filtering
        return pos_diff < 5.0
    
    def _check_geometric_compatibility(self, poly1: Dict[str, Any],
                                      poly2: Dict[str, Any],
                                      edge1_idx: int, edge2_idx: int) -> float:
        """
        Check geometric compatibility of two edges.
        
        Returns score [0-1] where 1 = perfect alignment.
        """
        verts1 = np.array(poly1.get('vertices', []))
        verts2 = np.array(poly2.get('vertices', []))
        
        if len(verts1) <= edge1_idx or len(verts2) <= edge2_idx:
            return 0.0
        
        # Get edge endpoints
        v1a = verts1[edge1_idx]
        v1b = verts1[(edge1_idx + 1) % len(verts1)]
        
        v2a = verts2[edge2_idx]
        v2b = verts2[(edge2_idx + 1) % len(verts2)]
        
        # Edge lengths
        len1 = np.linalg.norm(v1b - v1a)
        len2 = np.linalg.norm(v2b - v2a)
        
        # Length similarity
        length_score = 1.0 - abs(len1 - len2) / max(len1, len2, 1e-6)
        
        # Distance between edges (check both orientations)
        dist_forward = (np.linalg.norm(v1a - v2a) + np.linalg.norm(v1b - v2b)) / 2.0
        dist_reverse = (np.linalg.norm(v1a - v2b) + np.linalg.norm(v1b - v2a)) / 2.0
        
        min_dist = min(dist_forward, dist_reverse)
        distance_score = max(0.0, 1.0 - min_dist / self.max_distance)
        
        # Edge direction alignment (should be opposite for bonding)
        edge1_dir = (v1b - v1a) / (len1 + 1e-8)
        edge2_dir = (v2b - v2a) / (len2 + 1e-8)
        
        # For bonding, edges should be anti-parallel
        alignment = abs(np.dot(edge1_dir, edge2_dir) + 1.0) / 2.0  # +1 for anti-parallel
        
        # Combined score
        score = length_score * 0.4 + distance_score * 0.4 + alignment * 0.2
        
        return score
    
    def auto_bond_if_confident(self, assembly: Any, new_poly: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Automatically create bonds if suggestions are confident enough.
        
        Returns list of bonds that were created.
        """
        suggestions = self.suggest_bonds(assembly, new_poly, top_k=3)
        
        created_bonds = []
        
        for sugg in suggestions:
            if sugg['confidence'] >= 0.8:  # High confidence threshold for auto
                # Create the bond
                bond = {
                    'poly1_id': sugg['poly1_id'],
                    'poly2_id': sugg['poly2_id'],
                    'edge1_idx': sugg['edge1_idx'],
                    'edge2_idx': sugg['edge2_idx'],
                    'type': 'hinge',
                    'quality': 'predicted',
                    'confidence': sugg['confidence'],
                    'auto_created': True,
                }
                
                created_bonds.append(bond)
        
        return created_bonds
    
    def learn_from_library(self, library):
        """
        Extract bond patterns from saved assemblies.
        
        Args:
            library: StableLibrary instance
        """
        entries = library.list_entries()
        
        print(f"Learning from {len(entries)} library entries...")
        
        for entry in entries:
            assembly_data = library.load_entry(entry['id'])
            if not assembly_data:
                continue
            
            polyforms = assembly_data.get('polyforms', [])
            bonds = assembly_data.get('bonds', [])
            
            # Extract context
            tags = assembly_data.get('tags', [])
            self.current_context_tags = tags
            
            # Learn from each bond
            for bond in bonds:
                poly1_id = bond.get('poly1_id')
                poly2_id = bond.get('poly2_id')
                
                # Find polygons
                poly1 = next((p for p in polyforms if p.get('id') == poly1_id), None)
                poly2 = next((p for p in polyforms if p.get('id') == poly2_id), None)
                
                if not poly1 or not poly2:
                    continue
                
                # Record as successful bond
                self.record_bond_attempt(
                    poly1, poly2,
                    bond.get('edge1_idx', 0),
                    bond.get('edge2_idx', 0),
                    success=True,
                    stability_score=bond.get('stability_score', 0.8)
                )
        
        self.current_context_tags = []
        print(f"Learned {len(self.patterns)} total patterns")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about learned patterns."""
        if not self.patterns:
            return {'total_patterns': 0}
        
        # Aggregate stats
        total = len(self.patterns)
        high_conf = len([p for p in self.patterns if p.confidence_score() > 0.8])
        avg_confidence = np.mean([p.confidence_score() for p in self.patterns])
        avg_success_rate = np.mean([p.success_rate() for p in self.patterns])
        
        # By polygon type
        type_counts = defaultdict(int)
        for p in self.patterns:
            key = f"{p.poly1_sides}-{p.poly2_sides}"
            type_counts[key] += 1
        
        return {
            'total_patterns': total,
            'high_confidence_patterns': high_conf,
            'avg_confidence': avg_confidence,
            'avg_success_rate': avg_success_rate,
            'patterns_by_type': dict(type_counts),
            'session_bonds': len(self.current_session_bonds),
        }


# Integration helper
def integrate_contextual_bonding(workspace, library):
    """
    Integrate contextual bonding into existing workspace.
    
    Usage:
        bonding_engine = integrate_contextual_bonding(workspace, library)
        
        # Learn from library
        bonding_engine.learn_from_library(library)
        
        # Auto-bond on new polygon
        new_poly = create_polygon(4, (5, 0, 0))
        bonds = bonding_engine.auto_bond_if_confident(assembly, new_poly)
    """
    engine = ContextualBondingEngine()
    
    # Attach to workspace
    workspace.bonding_engine = engine
    
    # Learn from existing library
    if library:
        engine.learn_from_library(library)
        engine.save_patterns()
    
    return engine
