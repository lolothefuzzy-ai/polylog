"""
Workspace Stability Filter

Filters polyforms by stability for workspace context,
leveraging four-track system benefits for recombination.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass

from .tier_recursive_structure import RecursivePolyform, get_recursive_registry
from .scalar_structure import get_scalar_registry
from .symmetry_structure import get_symmetry_registry
from .tier0_generator import ConnectivityChain, Tier0Generator


@dataclass(slots=True)
class WorkspaceContext:
    """Context for workspace stability filtering."""
    
    min_stability: float = 0.7
    max_stability: float = 1.0
    preferred_scalar: Optional[str] = None  # e.g., "k1", "k2"
    preferred_symmetry: Optional[str] = None  # e.g., "D4", "T"
    chain_length: Optional[int] = None  # Filter by chain length
    series_combinations: Optional[List[str]] = None  # e.g., ["ABC", "ABD", "ACD"]
    tier: Optional[int] = None  # Filter by tier level


class WorkspaceStabilityFilter:
    """Filter polyforms by stability for workspace context."""
    
    def __init__(self):
        self.recursive_registry = get_recursive_registry()
        self.scalar_registry = get_scalar_registry()
        self.symmetry_registry = get_symmetry_registry()
        self.tier0_generator = Tier0Generator()
    
    def filter_tier0_by_stability(
        self,
        min_stability: float = 0.7,
        max_stability: float = 1.0,
        series_combinations: Optional[List[str]] = None
    ) -> List[ConnectivityChain]:
        """Filter Tier 0 symbols by stability."""
        all_chains = self.tier0_generator.generate_all()
        stable_chains = []
        
        for symbol, chain in all_chains.items():
            # Filter by series combinations if specified
            if series_combinations:
                chain_pattern = self._get_chain_pattern(chain)
                if chain_pattern not in series_combinations:
                    continue
            
            # Compute stability (simplified - replace with actual computation)
            stability = self._compute_tier0_stability(chain)
            
            if min_stability <= stability <= max_stability:
                stable_chains.append(chain)
        
        return stable_chains
    
    def filter_recursive_by_stability(
        self,
        context: WorkspaceContext
    ) -> List[RecursivePolyform]:
        """Filter recursive polyforms (Tier 1+) by stability."""
        # Get all polyforms at specified tier
        if context.tier is not None:
            candidates = self.recursive_registry.get_by_tier(context.tier)
        else:
            candidates = list(self.recursive_registry.registry.values())
        
        # Filter by stability
        stable = [
            p for p in candidates
            if context.min_stability <= p.stability_score <= context.max_stability
        ]
        
        # Filter by chain length if specified
        if context.chain_length is not None:
            stable = [
                p for p in stable
                if len(p.tier0_composition) == context.chain_length
            ]
        
        # Apply context-specific scalars and symmetries
        for polyform in stable:
            if context.preferred_scalar:
                self.scalar_registry.apply_scalar(
                    polyform.symbol,
                    context.preferred_scalar,
                    context="workspace"
                )
            
            if context.preferred_symmetry:
                self.symmetry_registry.apply_symmetry(
                    polyform.symbol,
                    context.preferred_symmetry,
                    context="workspace"
                )
        
        return stable
    
    def filter_for_workspace(
        self,
        context: WorkspaceContext
    ) -> Dict[str, List]:
        """Filter both Tier 0 and recursive polyforms for workspace."""
        result = {
            "tier0": [],
            "recursive": []
        }
        
        # Filter Tier 0
        tier0_stable = self.filter_tier0_by_stability(
            min_stability=context.min_stability,
            max_stability=context.max_stability,
            series_combinations=context.series_combinations
        )
        result["tier0"] = tier0_stable
        
        # Filter recursive
        recursive_stable = self.filter_recursive_by_stability(context)
        result["recursive"] = recursive_stable
        
        return result
    
    def _get_chain_pattern(self, chain: ConnectivityChain) -> str:
        """Get series pattern string (e.g., "ABC", "ABD")."""
        if len(chain.series) == 1:
            return chain.series[0]
        elif len(chain.series) == 2:
            return "".join(chain.series)
        elif len(chain.series) == 3:
            return "".join(chain.series)
        else:
            return "".join(chain.series[:3])  # Truncate for longer chains
    
    def _compute_tier0_stability(self, chain: ConnectivityChain) -> float:
        """Compute stability score for Tier 0 chain.
        
        Simplified implementation - replace with actual stability computation.
        """
        # Placeholder: stability based on chain length and series combination
        base_stability = 0.8
        
        # Longer chains may be less stable
        length_penalty = len(chain.polygons) * 0.05
        
        # Certain series combinations may be more stable
        series_bonus = 0.0
        if len(chain.series) >= 2:
            if chain.series[1] == "C":  # Series C (multiples of 3) may be more stable
                series_bonus = 0.1
            elif chain.series[1] == "D":  # Series D (complementary) may be more stable
                series_bonus = 0.05
        
        stability = base_stability - length_penalty + series_bonus
        return max(0.0, min(1.0, stability))  # Clamp to [0, 1]


# Singleton instance
_workspace_filter: Optional[WorkspaceStabilityFilter] = None


def get_workspace_filter() -> WorkspaceStabilityFilter:
    """Get singleton workspace stability filter instance."""
    global _workspace_filter
    if _workspace_filter is None:
        _workspace_filter = WorkspaceStabilityFilter()
    return _workspace_filter


__all__ = [
    "WorkspaceContext",
    "WorkspaceStabilityFilter",
    "get_workspace_filter",
]

