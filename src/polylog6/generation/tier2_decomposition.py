"""
Tier 2 Dynamic Decomposition System

Recursively utilizes Tier 1 + Tier 0 or other Tier 1 polyforms by:
- Dynamic decomposition of polyforms in workspace
- Decompose to more stable subforms when:
  - Edge alignment is unlikely
  - Low stability angles
  - Angles < 60 degrees between any two angles
- Exception: Ring structures (snowflake patterns) with empty centers
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
import math

from polylog6.storage.tier_recursive_structure import RecursivePolyform, Tier0Reference
from polylog6.generation.tier1_symmetry_generator import Tier1Solid, get_tier1_generator
from polylog6.geometry import get_unified_backend_geometry


@dataclass(slots=True)
class AngleMeasurement:
    """Measurement of angle between two edges/faces."""
    
    angle: float  # Angle in radians
    edge_a: int  # First edge index
    edge_b: int  # Second edge index
    polygon_id: str  # Polygon identifier
    stability_score: float  # Stability score for this angle


@dataclass(slots=True)
class RingStructure:
    """Ring structure (snowflake pattern) with empty center."""
    
    center_point: Tuple[float, float, float]
    ring_polygons: List[str]  # Polygon IDs forming the ring
    axes_lines: List[Tuple[Tuple[float, float, float], Tuple[float, float, float]]]  # Axes from center
    gap_angles: List[float]  # Angles between ring segments (excluded from <60° rule)
    is_valid: bool  # Whether ring structure is valid


@dataclass(slots=True)
class DecompositionCandidate:
    """Candidate for decomposition into stable subforms."""
    
    polyform_symbol: str
    decomposition_type: str  # "tier1_tier0", "tier1_tier1", "tier0_only"
    subforms: List[str]  # Symbols of stable subforms
    stability_improvement: float  # Improvement in stability score
    reason: str  # Reason for decomposition


class Tier2DecompositionEngine:
    """Engine for dynamic decomposition of Tier 2 polyforms."""
    
    MIN_ANGLE_THRESHOLD = math.radians(60)  # 60 degrees minimum
    LOW_STABILITY_THRESHOLD = 0.5  # Below this, consider decomposition
    EDGE_ALIGNMENT_THRESHOLD = 0.1  # Maximum deviation for edge alignment
    
    def __init__(self):
        self.tier1_generator = get_tier1_generator()
        self.geometry_backend = get_unified_backend_geometry()
        self.decomposition_cache: Dict[str, List[DecompositionCandidate]] = {}
        self.ring_structures: Dict[str, RingStructure] = {}
    
    def analyze_polyform(
        self,
        polyform: RecursivePolyform,
        workspace_context: Optional[Dict[str, object]] = None
    ) -> List[DecompositionCandidate]:
        """Analyze polyform and suggest decompositions."""
        candidates = []
        
        # Check for low stability
        if polyform.stability_score < self.LOW_STABILITY_THRESHOLD:
            candidates.extend(
                self._suggest_stability_decomposition(polyform)
            )
        
        # Check for angle violations (< 60 degrees)
        angle_violations = self._detect_angle_violations(polyform)
        if angle_violations:
            candidates.extend(
                self._suggest_angle_decomposition(polyform, angle_violations)
            )
        
        # Check for edge alignment issues
        alignment_issues = self._detect_edge_alignment_issues(polyform)
        if alignment_issues:
            candidates.extend(
                self._suggest_alignment_decomposition(polyform, alignment_issues)
            )
        
        # Check for ring structures (exclude from decomposition)
        ring_structure = self._detect_ring_structure(polyform)
        if ring_structure and ring_structure.is_valid:
            # Ring structures are valid, don't decompose
            self.ring_structures[polyform.symbol] = ring_structure
            return []  # No decomposition needed
        
        return candidates
    
    def decompose_polyform(
        self,
        polyform: RecursivePolyform,
        candidate: DecompositionCandidate
    ) -> List[RecursivePolyform]:
        """Decompose polyform into stable subforms."""
        subforms = []
        
        if candidate.decomposition_type == "tier1_tier0":
            # Decompose into Tier 1 + Tier 0 components
            subforms.extend(
                self._decompose_tier1_tier0(polyform, candidate)
            )
        elif candidate.decomposition_type == "tier1_tier1":
            # Decompose into multiple Tier 1 components
            subforms.extend(
                self._decompose_tier1_tier1(polyform, candidate)
            )
        elif candidate.decomposition_type == "tier0_only":
            # Decompose into Tier 0 only
            subforms.extend(
                self._decompose_tier0_only(polyform, candidate)
            )
        
        return subforms
    
    def _detect_angle_violations(
        self,
        polyform: RecursivePolyform
    ) -> List[AngleMeasurement]:
        """Detect angles < 60 degrees between any two angles."""
        violations = []
        
        # Expand Tier 0 references to get actual polygons
        tier0_chains = polyform.expand_tier0()
        
        for chain in tier0_chains:
            for i in range(len(chain.polygons) - 1):
                # Calculate angle between adjacent polygons
                angle = self._calculate_angle_between_polygons(
                    chain.polygons[i],
                    chain.polygons[i + 1]
                )
                
                if angle < self.MIN_ANGLE_THRESHOLD:
                    violations.append(
                        AngleMeasurement(
                            angle=angle,
                            edge_a=i,
                            edge_b=i + 1,
                            polygon_id=chain.symbol,
                            stability_score=self._angle_stability_score(angle)
                        )
                    )
        
        return violations
    
    def _detect_edge_alignment_issues(
        self,
        polyform: RecursivePolyform
    ) -> List[Tuple[str, str, float]]:
        """Detect edge alignment issues (unlikely alignments)."""
        issues = []
        
        tier0_chains = polyform.expand_tier0()
        
        for chain in tier0_chains:
            for i in range(len(chain.polygons) - 1):
                alignment_score = self._calculate_edge_alignment(
                    chain.polygons[i],
                    chain.polygons[i + 1]
                )
                
                if alignment_score < self.EDGE_ALIGNMENT_THRESHOLD:
                    issues.append((
                        chain.symbol,
                        f"edge_{i}",
                        alignment_score
                    ))
        
        return issues
    
    def _detect_ring_structure(
        self,
        polyform: RecursivePolyform
    ) -> Optional[RingStructure]:
        """Detect ring structure (snowflake pattern) with empty center."""
        # Check if polyform forms a ring
        tier0_chains = polyform.expand_tier0()
        
        if len(tier0_chains) < 6:  # Minimum for ring structure
            return None
        
        # Check for circular arrangement
        # Simplified: would use actual geometry analysis
        center_point = self._calculate_center_point(tier0_chains)
        ring_polygons = [chain.symbol for chain in tier0_chains]
        axes_lines = self._calculate_axes_lines(center_point, tier0_chains)
        gap_angles = self._calculate_gap_angles(tier0_chains)
        
        # Validate ring structure
        is_valid = (
            len(ring_polygons) >= 6 and
            len(axes_lines) > 0 and
            self._has_empty_center(center_point, tier0_chains)
        )
        
        return RingStructure(
            center_point=center_point,
            ring_polygons=ring_polygons,
            axes_lines=axes_lines,
            gap_angles=gap_angles,
            is_valid=is_valid
        )
    
    def _suggest_stability_decomposition(
        self,
        polyform: RecursivePolyform
    ) -> List[DecompositionCandidate]:
        """Suggest decomposition based on low stability."""
        candidates = []
        
        # Try Tier 1 + Tier 0 decomposition
        if len(polyform.tier0_composition) > 1:
            candidates.append(
                DecompositionCandidate(
                    polyform_symbol=polyform.symbol,
                    decomposition_type="tier1_tier0",
                    subforms=["tier1_base", "tier0_chain"],
                    stability_improvement=0.2,
                    reason="Low stability score, decompose into Tier 1 + Tier 0"
                )
            )
        
        return candidates
    
    def _suggest_angle_decomposition(
        self,
        polyform: RecursivePolyform,
        violations: List[AngleMeasurement]
    ) -> List[DecompositionCandidate]:
        """Suggest decomposition based on angle violations."""
        candidates = []
        
        # Decompose at violation points
        for violation in violations:
            candidates.append(
                DecompositionCandidate(
                    polyform_symbol=polyform.symbol,
                    decomposition_type="tier0_only",
                    subforms=[f"subform_{violation.edge_a}", f"subform_{violation.edge_b}"],
                    stability_improvement=violation.stability_score,
                    reason=f"Angle violation: {math.degrees(violation.angle):.1f}° < 60°"
                )
            )
        
        return candidates
    
    def _suggest_alignment_decomposition(
        self,
        polyform: RecursivePolyform,
        issues: List[Tuple[str, str, float]]
    ) -> List[DecompositionCandidate]:
        """Suggest decomposition based on edge alignment issues."""
        candidates = []
        
        for symbol, edge, score in issues:
            candidates.append(
                DecompositionCandidate(
                    polyform_symbol=polyform.symbol,
                    decomposition_type="tier1_tier1",
                    subforms=["tier1_part1", "tier1_part2"],
                    stability_improvement=0.15,
                    reason=f"Edge alignment issue: {score:.3f} < {self.EDGE_ALIGNMENT_THRESHOLD}"
                )
            )
        
        return candidates
    
    def _calculate_angle_between_polygons(
        self,
        polygon_a: int,
        polygon_b: int
    ) -> float:
        """Calculate angle between two polygons using unified backend."""
        # Try to get fold angle from backend attachment matrix
        fold_angle = self.geometry_backend.get_fold_angle(polygon_a, polygon_b)
        if fold_angle is not None:
            return abs(fold_angle)
        
        # Fallback to local calculation
        internal_angle_a = ((polygon_a - 2) * math.pi) / polygon_a
        internal_angle_b = ((polygon_b - 2) * math.pi) / polygon_b
        
        # Dihedral angle approximation
        return math.pi - (internal_angle_a + internal_angle_b) / 2
    
    def _calculate_edge_alignment(
        self,
        polygon_a: int,
        polygon_b: int
    ) -> float:
        """Calculate edge alignment score (0-1, higher is better)."""
        # Simplified: would use actual geometry
        # For now, return a placeholder
        return 0.8  # Default alignment score
    
    def _angle_stability_score(self, angle: float) -> float:
        """Calculate stability score based on angle."""
        # Angles closer to 60° or 90° are more stable
        ideal_angles = [math.radians(60), math.radians(90), math.radians(120)]
        min_distance = min(abs(angle - ideal) for ideal in ideal_angles)
        return max(0.0, 1.0 - (min_distance / math.pi))
    
    def _calculate_center_point(
        self,
        chains: List
    ) -> Tuple[float, float, float]:
        """Calculate center point of ring structure."""
        # Simplified: would use actual geometry
        return (0.0, 0.0, 0.0)
    
    def _calculate_axes_lines(
        self,
        center: Tuple[float, float, float],
        chains: List
    ) -> List[Tuple[Tuple[float, float, float], Tuple[float, float, float]]]:
        """Calculate axes lines extending from center."""
        # Simplified: would use actual geometry
        return []
    
    def _calculate_gap_angles(self, chains: List) -> List[float]:
        """Calculate gap angles between ring segments."""
        # Simplified: would use actual geometry
        return []
    
    def _has_empty_center(
        self,
        center: Tuple[float, float, float],
        chains: List
    ) -> bool:
        """Check if center is empty (no polygons)."""
        # Simplified: would use actual geometry
        return True
    
    def _decompose_tier1_tier0(
        self,
        polyform: RecursivePolyform,
        candidate: DecompositionCandidate
    ) -> List[RecursivePolyform]:
        """Decompose into Tier 1 + Tier 0 components."""
        # Implementation would split polyform
        return []
    
    def _decompose_tier1_tier1(
        self,
        polyform: RecursivePolyform,
        candidate: DecompositionCandidate
    ) -> List[RecursivePolyform]:
        """Decompose into multiple Tier 1 components."""
        # Implementation would split polyform
        return []
    
    def _decompose_tier0_only(
        self,
        polyform: RecursivePolyform,
        candidate: DecompositionCandidate
    ) -> List[RecursivePolyform]:
        """Decompose into Tier 0 only."""
        # Implementation would split polyform
        return []


# Singleton instance
_tier2_decomposition: Optional[Tier2DecompositionEngine] = None


def get_tier2_decomposition() -> Tier2DecompositionEngine:
    """Get singleton Tier 2 decomposition engine instance."""
    global _tier2_decomposition
    if _tier2_decomposition is None:
        _tier2_decomposition = Tier2DecompositionEngine()
    return _tier2_decomposition


__all__ = [
    "Tier2DecompositionEngine",
    "DecompositionCandidate",
    "RingStructure",
    "get_tier2_decomposition",
]

