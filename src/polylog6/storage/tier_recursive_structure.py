"""
Recursive Tier 0 Reference Structure

Enables Tier 1, 2, 3+ polyforms to recursively reference Tier 0 symbols,
along with separate non-tiered structures for scalars and symmetries
that can be applied dynamically based on context.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
import json
from pathlib import Path

from .tier0_generator import ConnectivityChain, decode_tier0_symbol


@dataclass(slots=True)
class Tier0Reference:
    """Reference to a Tier 0 symbol within a higher-tier polyform."""
    
    symbol: str  # Tier 0 symbol (e.g., "A11", "A115")
    position: int  # Position in the higher-tier structure
    series_path: List[str]  # Series path (e.g., ["A", "B"])
    metadata: Dict[str, object] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, object]:
        return {
            "symbol": self.symbol,
            "position": self.position,
            "series_path": self.series_path,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "Tier0Reference":
        return cls(
            symbol=str(data["symbol"]),
            position=int(data["position"]),
            series_path=list(data.get("series_path", [])),
            metadata=dict(data.get("metadata", {}))
        )


@dataclass(slots=True)
class RecursivePolyform:
    """Polyform that recursively references Tier 0 symbols."""
    
    symbol: str  # Higher-tier symbol (e.g., "Ω₁", "Ψ₂")
    tier: int  # Tier level (1, 2, 3, etc.)
    tier0_composition: List[Tier0Reference]  # Recursive Tier 0 references
    scalar_ref: Optional[str] = None  # Reference to scalar structure
    symmetry_ref: Optional[str] = None  # Reference to symmetry structure
    stability_score: float = 0.0  # Stability score for filtering
    metadata: Dict[str, object] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, object]:
        return {
            "symbol": self.symbol,
            "tier": self.tier,
            "tier0_composition": [ref.to_dict() for ref in self.tier0_composition],
            "scalar_ref": self.scalar_ref,
            "symmetry_ref": self.symmetry_ref,
            "stability_score": self.stability_score,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "RecursivePolyform":
        return cls(
            symbol=str(data["symbol"]),
            tier=int(data["tier"]),
            tier0_composition=[
                Tier0Reference.from_dict(ref_data)
                for ref_data in data.get("tier0_composition", [])
            ],
            scalar_ref=data.get("scalar_ref"),
            symmetry_ref=data.get("symmetry_ref"),
            stability_score=float(data.get("stability_score", 0.0)),
            metadata=dict(data.get("metadata", {}))
        )
    
    def expand_tier0(self) -> List[ConnectivityChain]:
        """Expand recursive Tier 0 references to actual chains."""
        chains = []
        for ref in self.tier0_composition:
            try:
                chain = decode_tier0_symbol(ref.symbol)
                chains.append(chain)
            except ValueError:
                # Invalid Tier 0 symbol, skip
                continue
        return chains
    
    def get_all_polygons(self) -> List[int]:
        """Get all polygon edge counts from recursive Tier 0 expansion."""
        polygons = []
        for chain in self.expand_tier0():
            polygons.extend(chain.polygons)
        return polygons


class RecursiveTierRegistry:
    """Registry for recursive Tier 0 references in higher tiers."""
    
    def __init__(self):
        self.registry: Dict[str, RecursivePolyform] = {}
        self.by_tier: Dict[int, List[str]] = {}
        self.by_tier0_symbol: Dict[str, List[str]] = {}  # Tier 0 symbol -> higher-tier symbols
    
    def register(self, polyform: RecursivePolyform) -> None:
        """Register a recursive polyform."""
        self.registry[polyform.symbol] = polyform
        
        # Index by tier
        tier = polyform.tier
        if tier not in self.by_tier:
            self.by_tier[tier] = []
        self.by_tier[tier].append(polyform.symbol)
        
        # Index by Tier 0 symbols
        for ref in polyform.tier0_composition:
            if ref.symbol not in self.by_tier0_symbol:
                self.by_tier0_symbol[ref.symbol] = []
            self.by_tier0_symbol[ref.symbol].append(polyform.symbol)
    
    def get(self, symbol: str) -> Optional[RecursivePolyform]:
        """Get recursive polyform by symbol."""
        return self.registry.get(symbol)
    
    def get_by_tier(self, tier: int) -> List[RecursivePolyform]:
        """Get all polyforms at a specific tier."""
        symbols = self.by_tier.get(tier, [])
        return [self.registry[s] for s in symbols]
    
    def get_by_tier0_symbol(self, tier0_symbol: str) -> List[RecursivePolyform]:
        """Get all higher-tier polyforms that reference a Tier 0 symbol."""
        symbols = self.by_tier0_symbol.get(tier0_symbol, [])
        return [self.registry[s] for s in symbols]
    
    def filter_by_stability(
        self,
        min_stability: float = 0.0,
        max_stability: float = 1.0,
        tier: Optional[int] = None
    ) -> List[RecursivePolyform]:
        """Filter polyforms by stability score."""
        candidates = (
            self.get_by_tier(tier) if tier is not None
            else list(self.registry.values())
        )
        
        return [
            p for p in candidates
            if min_stability <= p.stability_score <= max_stability
        ]


# Singleton instance
_recursive_registry: Optional[RecursiveTierRegistry] = None


def get_recursive_registry() -> RecursiveTierRegistry:
    """Get singleton recursive registry instance."""
    global _recursive_registry
    if _recursive_registry is None:
        _recursive_registry = RecursiveTierRegistry()
    return _recursive_registry


__all__ = [
    "Tier0Reference",
    "RecursivePolyform",
    "RecursiveTierRegistry",
    "get_recursive_registry",
]

