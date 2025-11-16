"""
Non-Tiered Symmetry Structure

Separate structure for symmetries that can be applied dynamically
depending on context. Symmetries are independent of tier structure
and can be applied to any polyform.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
import json
from pathlib import Path


@dataclass(slots=True)
class SymmetryDefinition:
    """Definition of a symmetry transformation."""
    
    symmetry_id: str  # Unique symmetry identifier (e.g., "C2", "D4", "T", "O", "I")
    symmetry_group: str  # Point group notation (e.g., "C₂", "D₄", "T", "O", "I")
    order: int  # Order of symmetry (number of operations)
    is_chiral: bool = False  # Whether symmetry is chiral
    symmetry_class: Optional[str] = None  # Class: "cyclic", "dihedral", "tetrahedral", etc.
    metadata: Dict[str, object] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, object]:
        return {
            "symmetry_id": self.symmetry_id,
            "symmetry_group": self.symmetry_group,
            "order": self.order,
            "is_chiral": self.is_chiral,
            "symmetry_class": self.symmetry_class,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "SymmetryDefinition":
        return cls(
            symmetry_id=str(data["symmetry_id"]),
            symmetry_group=str(data["symmetry_group"]),
            order=int(data["order"]),
            is_chiral=bool(data.get("is_chiral", False)),
            symmetry_class=data.get("symmetry_class"),
            metadata=dict(data.get("metadata", {}))
        )


@dataclass(slots=True)
class SymmetryApplication:
    """Application of a symmetry to a polyform in a specific context."""
    
    polyform_symbol: str  # Symbol of polyform
    symmetry_id: str  # Symmetry being applied
    context: str  # Context of application (e.g., "workspace", "catalog", "user_created")
    stability_impact: float = 0.0  # Impact on stability
    metadata: Dict[str, object] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, object]:
        return {
            "polyform_symbol": self.polyform_symbol,
            "symmetry_id": self.symmetry_id,
            "context": self.context,
            "stability_impact": self.stability_impact,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "SymmetryApplication":
        return cls(
            polyform_symbol=str(data["polyform_symbol"]),
            symmetry_id=str(data["symmetry_id"]),
            context=str(data["context"]),
            stability_impact=float(data.get("stability_impact", 0.0)),
            metadata=dict(data.get("metadata", {}))
        )


class SymmetryRegistry:
    """Registry for symmetry definitions and applications."""
    
    def __init__(self):
        self.symmetries: Dict[str, SymmetryDefinition] = {}
        self.applications: Dict[str, List[SymmetryApplication]] = {}  # polyform_symbol -> applications
        self.by_context: Dict[str, List[SymmetryApplication]] = {}  # context -> applications
        self.by_group: Dict[str, List[str]] = {}  # symmetry_group -> symmetry_ids
    
    def register_symmetry(self, symmetry: SymmetryDefinition) -> None:
        """Register a symmetry definition."""
        self.symmetries[symmetry.symmetry_id] = symmetry
        
        # Index by group
        group = symmetry.symmetry_group
        if group not in self.by_group:
            self.by_group[group] = []
        self.by_group[group].append(symmetry.symmetry_id)
    
    def apply_symmetry(
        self,
        polyform_symbol: str,
        symmetry_id: str,
        context: str = "workspace",
        stability_impact: float = 0.0,
        metadata: Optional[Dict[str, object]] = None
    ) -> SymmetryApplication:
        """Apply a symmetry to a polyform in a specific context."""
        if symmetry_id not in self.symmetries:
            raise ValueError(f"Unknown symmetry: {symmetry_id}")
        
        application = SymmetryApplication(
            polyform_symbol=polyform_symbol,
            symmetry_id=symmetry_id,
            context=context,
            stability_impact=stability_impact,
            metadata=metadata or {}
        )
        
        # Index by polyform
        if polyform_symbol not in self.applications:
            self.applications[polyform_symbol] = []
        self.applications[polyform_symbol].append(application)
        
        # Index by context
        if context not in self.by_context:
            self.by_context[context] = []
        self.by_context[context].append(application)
        
        return application
    
    def get_symmetry(self, symmetry_id: str) -> Optional[SymmetryDefinition]:
        """Get symmetry definition by ID."""
        return self.symmetries.get(symmetry_id)
    
    def get_applications(
        self,
        polyform_symbol: Optional[str] = None,
        context: Optional[str] = None
    ) -> List[SymmetryApplication]:
        """Get symmetry applications, optionally filtered by polyform or context."""
        if polyform_symbol is not None:
            return self.applications.get(polyform_symbol, [])
        elif context is not None:
            return self.by_context.get(context, [])
        else:
            # Return all applications
            all_apps = []
            for apps in self.applications.values():
                all_apps.extend(apps)
            return all_apps
    
    def get_by_group(self, symmetry_group: str) -> List[SymmetryDefinition]:
        """Get all symmetries in a specific group."""
        symmetry_ids = self.by_group.get(symmetry_group, [])
        return [self.symmetries[sid] for sid in symmetry_ids]
    
    def get_available_symmetries(self) -> List[SymmetryDefinition]:
        """Get all available symmetry definitions."""
        return list(self.symmetries.values())


# Singleton instance
_symmetry_registry: Optional[SymmetryRegistry] = None


def get_symmetry_registry() -> SymmetryRegistry:
    """Get singleton symmetry registry instance."""
    global _symmetry_registry
    if _symmetry_registry is None:
        _symmetry_registry = SymmetryRegistry()
        # Initialize with common symmetries
        _initialize_default_symmetries(_symmetry_registry)
    return _symmetry_registry


def _initialize_default_symmetries(registry: SymmetryRegistry) -> None:
    """Initialize registry with default symmetry definitions."""
    default_symmetries = [
        SymmetryDefinition("C1", "C₁", 1, False, "cyclic"),
        SymmetryDefinition("C2", "C₂", 2, False, "cyclic"),
        SymmetryDefinition("C3", "C₃", 3, False, "cyclic"),
        SymmetryDefinition("C4", "C₄", 4, False, "cyclic"),
        SymmetryDefinition("D2", "D₂", 4, False, "dihedral"),
        SymmetryDefinition("D3", "D₃", 6, False, "dihedral"),
        SymmetryDefinition("D4", "D₄", 8, False, "dihedral"),
        SymmetryDefinition("T", "T", 12, False, "tetrahedral"),
        SymmetryDefinition("O", "O", 24, False, "octahedral"),
        SymmetryDefinition("I", "I", 60, False, "icosahedral"),
    ]
    
    for symmetry in default_symmetries:
        registry.register_symmetry(symmetry)


__all__ = [
    "SymmetryDefinition",
    "SymmetryApplication",
    "SymmetryRegistry",
    "get_symmetry_registry",
]

