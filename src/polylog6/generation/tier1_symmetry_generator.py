"""
Tier 1 Symmetry-Based Generator

Uses symmetries to create:
1. Platonic solids (5)
2. Archimedean solids (13)
3. Johnson solids (92)

Each solid is generated using symmetry operations applied to Tier 0 primitives.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import math

from polylog6.storage.tier0_generator import ConnectivityChain, decode_tier0_symbol
from polylog6.storage.symmetry_structure import SymmetryDefinition, get_symmetry_registry
from polylog6.storage.tier_recursive_structure import RecursivePolyform, Tier0Reference
from polylog6.geometry import get_unified_backend_geometry
from polylog6.storage.atomic_chains import get_atomic_chain_library


@dataclass(slots=True)
class SymmetryOperation:
    """Symmetry operation for generating polyhedra."""
    
    symmetry_id: str
    operation_type: str  # "rotation", "reflection", "translation"
    axis: Tuple[float, float, float]  # Rotation/reflection axis
    angle: float  # Rotation angle (if rotation)
    order: int  # Order of symmetry operation


@dataclass(slots=True)
class Tier1Solid:
    """Tier 1 solid generated from symmetry operations."""
    
    symbol: str
    name: str
    solid_type: str  # "platonic", "archimedean", "johnson"
    symmetry: SymmetryDefinition
    tier0_composition: List[Tier0Reference]
    vertices: List[Tuple[float, float, float]]
    faces: List[List[int]]
    stability_score: float
    metadata: Dict[str, object] = field(default_factory=dict)


class Tier1SymmetryGenerator:
    """Generate Tier 1 solids using symmetry operations."""
    
    def __init__(self):
        self.symmetry_registry = get_symmetry_registry()
        self.generated_solids: Dict[str, Tier1Solid] = {}
        self.geometry_backend = get_unified_backend_geometry()
        
        # Platonic solids definitions
        self.platonic_definitions = {
            "Ω₁": {"name": "Tetrahedron", "symmetry": "T", "faces": 4, "vertices": 4},
            "Ω₂": {"name": "Cube", "symmetry": "O", "faces": 6, "vertices": 8},
            "Ω₃": {"name": "Octahedron", "symmetry": "O", "faces": 8, "vertices": 6},
            "Ω₄": {"name": "Dodecahedron", "symmetry": "I", "faces": 12, "vertices": 20},
            "Ω₅": {"name": "Icosahedron", "symmetry": "I", "faces": 20, "vertices": 12},
        }
        
        # Archimedean solids definitions (13 total)
        self.archimedean_definitions = {
            "Ω₆": {"name": "Truncated Tetrahedron", "symmetry": "T", "faces": 8},
            "Ω₇": {"name": "Cuboctahedron", "symmetry": "O", "faces": 14},
            "Ω₈": {"name": "Truncated Cube", "symmetry": "O", "faces": 14},
            "Ω₉": {"name": "Truncated Octahedron", "symmetry": "O", "faces": 14},
            "Ω₁₀": {"name": "Rhombicuboctahedron", "symmetry": "O", "faces": 26},
            "Ω₁₁": {"name": "Truncated Cuboctahedron", "symmetry": "O", "faces": 26},
            "Ω₁₂": {"name": "Snub Cube", "symmetry": "O", "faces": 38},
            "Ω₁₃": {"name": "Icosidodecahedron", "symmetry": "I", "faces": 32},
            "Ω₁₄": {"name": "Truncated Dodecahedron", "symmetry": "I", "faces": 32},
            "Ω₁₅": {"name": "Truncated Icosahedron", "symmetry": "I", "faces": 32},
            "Ω₁₆": {"name": "Rhombicosidodecahedron", "symmetry": "I", "faces": 62},
            "Ω₁₇": {"name": "Truncated Icosidodecahedron", "symmetry": "I", "faces": 62},
            "Ω₁₈": {"name": "Snub Dodecahedron", "symmetry": "I", "faces": 92},
        }
    
    def generate_platonic(self, symbol: str) -> Optional[Tier1Solid]:
        """Generate Platonic solid using symmetry operations."""
        if symbol not in self.platonic_definitions:
            return None
        
        definition = self.platonic_definitions[symbol]
        symmetry = self.symmetry_registry.get_symmetry(definition["symmetry"])
        
        if not symmetry:
            return None
        
        # Generate Tier 0 composition based on solid type
        tier0_composition = self._generate_platonic_tier0(symbol, definition)
        
        # Try to get geometry from Netlib first, fallback to symmetry operations
        geometry = self.geometry_backend.get_polyhedron_geometry(symbol)
        if geometry:
            vertices = geometry.vertices
            faces = geometry.faces
        else:
            # Generate vertices and faces using symmetry operations
            vertices, faces = self._apply_symmetry_operations(
                symbol, definition, symmetry
            )
        
        # Calculate stability score
        stability_score = self._calculate_platonic_stability(symbol, definition)
        
        return Tier1Solid(
            symbol=symbol,
            name=definition["name"],
            solid_type="platonic",
            symmetry=symmetry,
            tier0_composition=tier0_composition,
            vertices=vertices,
            faces=faces,
            stability_score=stability_score
        )
    
    def generate_archimedean(self, symbol: str) -> Optional[Tier1Solid]:
        """Generate Archimedean solid using symmetry operations."""
        if symbol not in self.archimedean_definitions:
            return None
        
        definition = self.archimedean_definitions[symbol]
        symmetry = self.symmetry_registry.get_symmetry(definition["symmetry"])
        
        if not symmetry:
            return None
        
        # Generate Tier 0 composition
        tier0_composition = self._generate_archimedean_tier0(symbol, definition)
        
        # Try to get geometry from Netlib first, fallback to symmetry operations
        geometry = self.geometry_backend.get_polyhedron_geometry(symbol)
        if geometry:
            vertices = geometry.vertices
            faces = geometry.faces
        else:
            # Generate vertices and faces using symmetry operations
            vertices, faces = self._apply_symmetry_operations(
                symbol, definition, symmetry
            )
        
        # Calculate stability score
        stability_score = self._calculate_archimedean_stability(symbol, definition)
        
        return Tier1Solid(
            symbol=symbol,
            name=definition["name"],
            solid_type="archimedean",
            symmetry=symmetry,
            tier0_composition=tier0_composition,
            vertices=vertices,
            faces=faces,
            stability_score=stability_score
        )
    
    def generate_johnson(self, symbol: str, definition: Dict[str, object]) -> Optional[Tier1Solid]:
        """Generate Johnson solid using symmetry operations and atomic chain scaffolds."""
        # Johnson solids typically have lower symmetry (C1-C4, D2-D4)
        symmetry_id = definition.get("symmetry", "C1")
        symmetry = self.symmetry_registry.get_symmetry(symmetry_id)
        
        if not symmetry:
            symmetry = self.symmetry_registry.get_symmetry("C1")  # Default
        
        # Try to get scaffold from atomic chain library first
        atomic_chain_library = get_atomic_chain_library()
        scaffold = atomic_chain_library.get_scaffold_for_johnson_solid(
            definition.get("name", symbol)
        )
        
        # Generate Tier 0 composition (use scaffold if available)
        if scaffold:
            # Use scaffold's atomic chains for Tier 0 composition
            tier0_composition = [
                Tier0Reference(symbol=chain.symbol, position=1, series_path=[chain.symbol[0]])
                for chain in scaffold.atomic_chains
            ]
            # Store scaffold metadata
            scaffold_metadata = {
                "scaffold_symbol": scaffold.symbol,
                "atomic_chains": [chain.symbol for chain in scaffold.atomic_chains],
                "stability_score": scaffold.stability_score
            }
        else:
            # Fallback to standard Tier 0 generation
            tier0_composition = self._generate_johnson_tier0(symbol, definition)
            scaffold_metadata = {}
        
        # Try to get geometry from Netlib first, fallback to symmetry operations
        geometry = self.geometry_backend.get_polyhedron_geometry(symbol)
        if geometry:
            vertices = geometry.vertices
            faces = geometry.faces
        else:
            # Generate vertices and faces using symmetry operations
            vertices, faces = self._apply_symmetry_operations(
                symbol, definition, symmetry
            )
        
        # Calculate stability score (use scaffold stability if available)
        if scaffold:
            stability_score = scaffold.stability_score
        else:
            stability_score = self._calculate_johnson_stability(symbol, definition)
        
        # Merge scaffold metadata into definition
        metadata = {**definition.get("metadata", {}), **scaffold_metadata}
        
        return Tier1Solid(
            symbol=symbol,
            name=definition.get("name", symbol),
            solid_type="johnson",
            symmetry=symmetry,
            tier0_composition=tier0_composition,
            vertices=vertices,
            faces=faces,
            stability_score=stability_score,
            metadata=metadata
        )
    
    def _generate_platonic_tier0(self, symbol: str, definition: Dict[str, object]) -> List[Tier0Reference]:
        """Generate Tier 0 composition for Platonic solid."""
        compositions = {
            "Ω₁": [("A3", 1), ("A3", 2), ("A3", 3), ("A3", 4)],  # 4 triangles
            "Ω₂": [("A4", 1), ("A4", 2), ("A4", 3), ("A4", 4), ("A4", 5), ("A4", 6)],  # 6 squares
            "Ω₃": [("A3", 1), ("A3", 2), ("A3", 3), ("A3", 4), ("A3", 5), ("A3", 6), ("A3", 7), ("A3", 8)],  # 8 triangles
            "Ω₄": [("A5", 1), ("A5", 2), ("A5", 3), ("A5", 4), ("A5", 5), ("A5", 6), ("A5", 7), ("A5", 8), ("A5", 9), ("A5", 10), ("A5", 11), ("A5", 12)],  # 12 pentagons
            "Ω₅": [("A3", 1), ("A3", 2), ("A3", 3), ("A3", 4), ("A3", 5), ("A3", 6), ("A3", 7), ("A3", 8), ("A3", 9), ("A3", 10), ("A3", 11), ("A3", 12), ("A3", 13), ("A3", 14), ("A3", 15), ("A3", 16), ("A3", 17), ("A3", 18), ("A3", 19), ("A3", 20)],  # 20 triangles
        }
        
        if symbol not in compositions:
            return []
        
        tier0_refs = []
        for tier0_symbol, position in compositions[symbol]:
            tier0_refs.append(
                Tier0Reference(
                    symbol=tier0_symbol,
                    position=position,
                    series_path=["A"]
                )
            )
        
        return tier0_refs
    
    def _generate_archimedean_tier0(self, symbol: str, definition: Dict[str, object]) -> List[Tier0Reference]:
        """Generate Tier 0 composition for Archimedean solid."""
        # Archimedean solids use mixed polygon types
        # Simplified: use common patterns
        # In practice, this would be more complex based on actual face types
        return []  # Placeholder - would be populated from actual solid definitions
    
    def _generate_johnson_tier0(self, symbol: str, definition: Dict[str, object]) -> List[Tier0Reference]:
        """Generate Tier 0 composition for Johnson solid."""
        # Johnson solids have varied compositions
        # Would be populated from actual solid definitions
        return []  # Placeholder
    
    def _apply_symmetry_operations(
        self,
        symbol: str,
        definition: Dict[str, object],
        symmetry: SymmetryDefinition
    ) -> Tuple[List[Tuple[float, float, float]], List[List[int]]]:
        """Apply symmetry operations to generate vertices and faces."""
        # Simplified: would use actual symmetry operations
        # This is a placeholder - actual implementation would:
        # 1. Start with base polygon/face
        # 2. Apply rotation/reflection operations
        # 3. Generate all vertices and faces
        
        vertices: List[Tuple[float, float, float]] = []
        faces: List[List[int]] = []
        
        # Placeholder implementation
        return vertices, faces
    
    def _calculate_platonic_stability(self, symbol: str, definition: Dict[str, object]) -> float:
        """Calculate stability score for Platonic solid."""
        # Platonic solids are highly stable
        return 0.95
    
    def _calculate_archimedean_stability(self, symbol: str, definition: Dict[str, object]) -> float:
        """Calculate stability score for Archimedean solid."""
        # Archimedean solids are stable but less than Platonic
        return 0.85
    
    def _calculate_johnson_stability(self, symbol: str, definition: Dict[str, object]) -> float:
        """Calculate stability score for Johnson solid."""
        # Johnson solids vary in stability
        return 0.70


# Singleton instance
_tier1_generator: Optional[Tier1SymmetryGenerator] = None


def get_tier1_generator() -> Tier1SymmetryGenerator:
    """Get singleton Tier 1 generator instance."""
    global _tier1_generator
    if _tier1_generator is None:
        _tier1_generator = Tier1SymmetryGenerator()
    return _tier1_generator


__all__ = [
    "Tier1Solid",
    "Tier1SymmetryGenerator",
    "get_tier1_generator",
]

