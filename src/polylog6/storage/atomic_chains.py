"""
Atomic Chains System

Atomic chains are fundamental building blocks in polyform creation:
- Triangles and squares dominate due to symmetries
- Enable stable scaling of other polygons
- Form reusable scaffolds for complex polyforms
- Represent 2D maps of polygon arrangements

Atomic chains are encoded as Tier 0 symbols and can be recombined
using the tier structure into clusters for better reference in
scaffolding and overall polyform generation, especially for Johnson solids.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum

from .tier0_generator import decode_tier0_symbol, encode_tier0_symbol, ConnectivityChain


class AtomicChainType(Enum):
    """Type of atomic chain."""
    SQUARE_CHAIN = "square_chain"  # Linear chain of squares
    TRIANGLE_CLUSTER = "triangle_cluster"  # Cluster of triangles
    MIXED_CHAIN = "mixed_chain"  # Combination of triangles and squares
    OTHER = "other"  # Other polygon types


@dataclass(slots=True)
class AtomicChain:
    """Represents an atomic chain pattern."""
    
    symbol: str  # Tier 0 symbol encoding the chain
    chain_type: AtomicChainType
    polygon_sequence: List[int]  # Edge counts (e.g., [4, 4, 4] for 3 squares)
    length: int  # Number of polygons in chain
    stability_score: float  # Overall stability of chain
    scaffold_applications: List[str]  # What polyforms this scaffold enables
    metadata: Dict[str, object]
    
    def is_square_chain(self) -> bool:
        """Check if chain is composed entirely of squares."""
        return all(sides == 4 for sides in self.polygon_sequence)
    
    def is_triangle_cluster(self) -> bool:
        """Check if chain is composed entirely of triangles."""
        return all(sides == 3 for sides in self.polygon_sequence)
    
    def can_expand_polygon(self, target_sides: int) -> bool:
        """Check if this chain can expand a polygon to target_sides."""
        if self.chain_type == AtomicChainType.SQUARE_CHAIN:
            # Square chains expand linearly: polygon_sides + chain_length = target_sides
            return True  # Can always add squares
        return False


@dataclass(slots=True)
class Scaffold:
    """Scaffold formed from atomic chains."""
    
    symbol: str  # Unique scaffold identifier
    atomic_chains: List[AtomicChain]  # Atomic chains forming scaffold
    target_polyform_type: str  # What this scaffold generates (e.g., "johnson_square_pyramid")
    stability_score: float
    metadata: Dict[str, object]


class AtomicChainDetector:
    """Detect atomic chains in polyforms."""
    
    def __init__(self):
        self.detected_chains: Dict[str, AtomicChain] = {}
    
    def detect_chain(self, tier0_symbol: str) -> Optional[AtomicChain]:
        """Detect atomic chain pattern in Tier 0 symbol."""
        try:
            chain = decode_tier0_symbol(tier0_symbol)
            if not chain or not chain.polygons:
                return None
            
            polygon_sequence = chain.polygons
            chain_type = self._classify_chain_type(polygon_sequence)
            
            # Calculate stability (simplified - would use actual geometry)
            stability_score = self._calculate_chain_stability(polygon_sequence)
            
            # Identify scaffold applications
            scaffold_applications = self._identify_scaffold_applications(
                chain_type, polygon_sequence
            )
            
            return AtomicChain(
                symbol=tier0_symbol,
                chain_type=chain_type,
                polygon_sequence=polygon_sequence,
                length=len(polygon_sequence),
                stability_score=stability_score,
                scaffold_applications=scaffold_applications,
                metadata={
                    "series": chain.series,
                    "positions": chain.positions
                }
            )
        except (ValueError, AttributeError):
            return None
    
    def _classify_chain_type(self, polygon_sequence: List[int]) -> AtomicChainType:
        """Classify chain type based on polygon sequence."""
        if all(sides == 4 for sides in polygon_sequence):
            return AtomicChainType.SQUARE_CHAIN
        elif all(sides == 3 for sides in polygon_sequence):
            return AtomicChainType.TRIANGLE_CLUSTER
        elif any(sides == 3 for sides in polygon_sequence) and any(sides == 4 for sides in polygon_sequence):
            return AtomicChainType.MIXED_CHAIN
        else:
            return AtomicChainType.OTHER
    
    def _calculate_chain_stability(self, polygon_sequence: List[int]) -> float:
        """Calculate stability score for chain."""
        # Simplified: triangles and squares are most stable
        if all(sides == 3 for sides in polygon_sequence):
            return 0.95  # Triangle clusters highly stable
        elif all(sides == 4 for sides in polygon_sequence):
            return 0.90  # Square chains stable
        elif any(sides == 3 for sides in polygon_sequence) and any(sides == 4 for sides in polygon_sequence):
            return 0.85  # Mixed chains moderately stable
        else:
            return 0.70  # Other chains less stable
    
    def _identify_scaffold_applications(
        self, 
        chain_type: AtomicChainType, 
        polygon_sequence: List[int]
    ) -> List[str]:
        """Identify what polyforms this scaffold enables."""
        applications = []
        
        if chain_type == AtomicChainType.SQUARE_CHAIN:
            length = len(polygon_sequence)
            if length <= 20:
                applications.append(f"linear_expansion_{length}_squares")
                applications.append("rectangular_structures")
        
        elif chain_type == AtomicChainType.TRIANGLE_CLUSTER:
            length = len(polygon_sequence)
            if length == 3:
                applications.append("tetrahedron_corner")
            elif length == 4:
                applications.append("tetrahedron_face")
            elif length == 8:
                applications.append("octahedron_structure")
            elif length == 20:
                applications.append("icosahedron_structure")
        
        elif chain_type == AtomicChainType.MIXED_CHAIN:
            triangle_count = sum(1 for s in polygon_sequence if s == 3)
            square_count = sum(1 for s in polygon_sequence if s == 4)
            
            if triangle_count == 1 and square_count == 1:
                applications.append("triangle_square_junction")
            elif triangle_count == 4 and square_count == 1:
                applications.append("square_pyramid_scaffold")
            elif triangle_count == 3 and square_count == 3:
                applications.append("triangular_prism_scaffold")
        
        return applications


class AtomicChainLibrary:
    """Library of precomputed atomic chains."""
    
    def __init__(self):
        self.chains: Dict[str, AtomicChain] = {}
        self.scaffolds: Dict[str, Scaffold] = {}
        self.detector = AtomicChainDetector()
    
    def generate_square_chains(self, max_length: int = 20) -> List[AtomicChain]:
        """Generate square chains (1-20 squares)."""
        chains = []
        
        for length in range(1, max_length + 1):
            # Create chain of N squares: B₁₁₁... (N times)
            polygon_sequence = [4] * length
            
            # Encode as Tier 0 symbol
            # For square chains, we use Series B (position 1 = 4 sides)
            # Pattern: B₁ repeated N times
            symbol = self._encode_square_chain(length)
            
            chain = AtomicChain(
                symbol=symbol,
                chain_type=AtomicChainType.SQUARE_CHAIN,
                polygon_sequence=polygon_sequence,
                length=length,
                stability_score=0.90,  # Square chains are stable
                scaffold_applications=[
                    f"linear_expansion_{length}_squares",
                    "rectangular_structures"
                ],
                metadata={"max_expansion": length}
            )
            
            chains.append(chain)
            self.chains[symbol] = chain
        
        return chains
    
    def generate_triangle_clusters(self) -> List[AtomicChain]:
        """Generate triangle clusters (3, 4, 8, 20 triangles)."""
        clusters = []
        cluster_sizes = [3, 4, 8, 20]
        
        for size in cluster_sizes:
            polygon_sequence = [3] * size
            
            # Encode as Tier 0 symbol
            # For triangle clusters, we use Series A (position 1 = 3 sides)
            symbol = self._encode_triangle_cluster(size)
            
            applications = []
            if size == 3:
                applications.append("tetrahedron_corner")
            elif size == 4:
                applications.append("tetrahedron_face")
            elif size == 8:
                applications.append("octahedron_structure")
            elif size == 20:
                applications.append("icosahedron_structure")
            
            chain = AtomicChain(
                symbol=symbol,
                chain_type=AtomicChainType.TRIANGLE_CLUSTER,
                polygon_sequence=polygon_sequence,
                length=size,
                stability_score=0.95,  # Triangle clusters highly stable
                scaffold_applications=applications,
                metadata={"cluster_size": size}
            )
            
            clusters.append(chain)
            self.chains[symbol] = chain
        
        return clusters
    
    def generate_mixed_chains(self) -> List[AtomicChain]:
        """Generate mixed triangle-square chains."""
        mixed_chains = []
        
        # Common patterns
        patterns = [
            ([3, 4], "triangle_square_junction"),
            ([3, 4, 4, 4], "triangle_3square_scaffold"),
            ([3, 3, 4, 4], "2triangle_2square_scaffold"),
            ([3, 3, 3, 3, 4], "4triangle_square_scaffold"),  # Square pyramid
        ]
        
        for polygon_sequence, application in patterns:
            symbol = self._encode_mixed_chain(polygon_sequence)
            
            chain = AtomicChain(
                symbol=symbol,
                chain_type=AtomicChainType.MIXED_CHAIN,
                polygon_sequence=polygon_sequence,
                length=len(polygon_sequence),
                stability_score=0.85,
                scaffold_applications=[application],
                metadata={"pattern": application}
            )
            
            mixed_chains.append(chain)
            self.chains[symbol] = chain
        
        return mixed_chains
    
    def _encode_square_chain(self, length: int) -> str:
        """Encode square chain as Tier 0 symbol."""
        # Series B, position 1 = 4 sides (square)
        # For atomic chains, we use the tier0_generator's encoding scheme
        # Single square: B₁ (Series B, position 1)
        # Two squares: B₁₁ (Series B, positions 1,1) - but this encodes differently
        # For now, use a pattern that works with tier0_generator
        # Note: Actual encoding depends on tier0_generator's rules
        # For atomic chains, we'll use a simplified pattern
        if length == 1:
            return "B1"  # Use numeric subscript
        elif length == 2:
            return "B11"  # Two-digit: tens=1 (B position 1), ones=1 (B position 1)
        else:
            # For longer chains, we need to work with tier0_generator's 3-digit encoding
            # Simplified: use pattern that represents N squares
            # This is a placeholder - actual encoding would use tier0_generator
            return f"B1{'1' * (length - 1)}"  # Simplified pattern
    
    def _encode_triangle_cluster(self, size: int) -> str:
        """Encode triangle cluster as Tier 0 symbol."""
        # Series A, position 1 = 3 sides (triangle)
        if size == 1:
            return "A1"  # Use numeric subscript
        elif size == 2:
            return "A11"  # Two-digit encoding
        else:
            # For clusters, use 3-digit encoding if needed
            return f"A1{'1' * (size - 1)}"  # Simplified pattern
    
    def _encode_mixed_chain(self, polygon_sequence: List[int]) -> str:
        """Encode mixed chain as Tier 0 symbol."""
        # For mixed chains, we need to use tier0_generator's encoding
        # This is complex - for now, create a composite symbol
        # Actual implementation would use tier0_generator properly
        
        # Simplified: encode first two polygons using two-digit pattern
        if len(polygon_sequence) >= 2:
            first_sides = polygon_sequence[0]
            second_sides = polygon_sequence[1]
            
            # Find series positions
            # Series A position 1 = 3 sides, Series B position 1 = 4 sides
            if first_sides == 3 and second_sides == 4:
                return "A11"  # A₁ + B₁ (tens=1 for A position 1, ones=1 for B position 1)
            elif first_sides == 4 and second_sides == 3:
                return "B11"  # B₁ + A₁ (but B11 encodes B₁ + B₁, so this is approximate)
            else:
                # Use simplified pattern
                return f"A1B1"  # Composite symbol
        
        # Single polygon
        if polygon_sequence[0] == 3:
            return "A1"
        elif polygon_sequence[0] == 4:
            return "B1"
        else:
            return f"A{polygon_sequence[0]}"
    
    def create_scaffold(
        self, 
        atomic_chains: List[AtomicChain], 
        target_polyform_type: str
    ) -> Scaffold:
        """Create scaffold from atomic chains."""
        # Generate scaffold symbol
        chain_symbols = [chain.symbol for chain in atomic_chains]
        scaffold_symbol = f"SCAFFOLD_{'_'.join(chain_symbols)}"
        
        # Calculate overall stability
        stability_score = sum(chain.stability_score for chain in atomic_chains) / len(atomic_chains)
        
        scaffold = Scaffold(
            symbol=scaffold_symbol,
            atomic_chains=atomic_chains,
            target_polyform_type=target_polyform_type,
            stability_score=stability_score,
            metadata={"chain_count": len(atomic_chains)}
        )
        
        self.scaffolds[scaffold_symbol] = scaffold
        return scaffold
    
    def get_scaffold_for_johnson_solid(self, solid_name: str) -> Optional[Scaffold]:
        """Get scaffold for a Johnson solid."""
        # Map Johnson solids to atomic chain patterns
        johnson_scaffolds = {
            "square_pyramid": self._create_square_pyramid_scaffold(),
            "triangular_prism": self._create_triangular_prism_scaffold(),
            # Add more mappings as needed
        }
        
        return johnson_scaffolds.get(solid_name.lower())
    
    def _create_square_pyramid_scaffold(self) -> Scaffold:
        """Create scaffold for square pyramid (4 triangles + 1 square)."""
        # 4 triangles: A₁₁₁₁
        triangle_cluster = self.chains.get("A₁₁₁₁")
        if not triangle_cluster:
            triangle_cluster = AtomicChain(
                symbol="A₁₁₁₁",
                chain_type=AtomicChainType.TRIANGLE_CLUSTER,
                polygon_sequence=[3, 3, 3, 3],
                length=4,
                stability_score=0.95,
                scaffold_applications=["tetrahedron_face"],
                metadata={}
            )
        
        # 1 square: B₁
        square = self.chains.get("B₁")
        if not square:
            square = AtomicChain(
                symbol="B₁",
                chain_type=AtomicChainType.SQUARE_CHAIN,
                polygon_sequence=[4],
                length=1,
                stability_score=0.90,
                scaffold_applications=["linear_expansion_1_squares"],
                metadata={}
            )
        
        return self.create_scaffold(
            [triangle_cluster, square],
            "johnson_square_pyramid"
        )
    
    def _create_triangular_prism_scaffold(self) -> Scaffold:
        """Create scaffold for triangular prism (2 triangles + 3 squares)."""
        # 2 triangles: A₁₁
        triangle_pair = self.chains.get("A₁₁")
        if not triangle_pair:
            triangle_pair = AtomicChain(
                symbol="A₁₁",
                chain_type=AtomicChainType.TRIANGLE_CLUSTER,
                polygon_sequence=[3, 3],
                length=2,
                stability_score=0.95,
                scaffold_applications=[],
                metadata={}
            )
        
        # 3 squares: B₁₁₁
        square_chain = self.chains.get("B₁₁₁")
        if not square_chain:
            square_chain = AtomicChain(
                symbol="B₁₁₁",
                chain_type=AtomicChainType.SQUARE_CHAIN,
                polygon_sequence=[4, 4, 4],
                length=3,
                stability_score=0.90,
                scaffold_applications=["linear_expansion_3_squares"],
                metadata={}
            )
        
        return self.create_scaffold(
            [triangle_pair, square_chain],
            "johnson_triangular_prism"
        )


# Singleton instance
_atomic_chain_library: Optional[AtomicChainLibrary] = None


def get_atomic_chain_library() -> AtomicChainLibrary:
    """Get singleton atomic chain library instance."""
    global _atomic_chain_library
    if _atomic_chain_library is None:
        _atomic_chain_library = AtomicChainLibrary()
        # Precompute common chains
        _atomic_chain_library.generate_square_chains(max_length=20)
        _atomic_chain_library.generate_triangle_clusters()
        _atomic_chain_library.generate_mixed_chains()
    return _atomic_chain_library

