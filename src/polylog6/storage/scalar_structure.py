"""
Non-Tiered Scalar Structure

Separate structure for scalars that can be applied dynamically
depending on context. Scalars are independent of tier structure
and can be applied to any polyform.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
import json
from pathlib import Path


@dataclass(slots=True)
class ScalarDefinition:
    """Definition of a scalar transformation."""
    
    scalar_id: str  # Unique scalar identifier (e.g., "k2", "k3", "linear", "quadratic")
    scale_factor: float  # Scale factor (e.g., 2.0 for 2× scaling)
    scale_type: str  # Type: "linear", "quadratic", "cubic", "polynomial", "custom"
    polynomial_order: int = 1  # For polynomial scaling: k^n where n = polynomial_order
    metadata: Dict[str, object] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, object]:
        return {
            "scalar_id": self.scalar_id,
            "scale_factor": self.scale_factor,
            "scale_type": self.scale_type,
            "polynomial_order": self.polynomial_order,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "ScalarDefinition":
        return cls(
            scalar_id=str(data["scalar_id"]),
            scale_factor=float(data["scale_factor"]),
            scale_type=str(data["scale_type"]),
            polynomial_order=int(data.get("polynomial_order", 1)),
            metadata=dict(data.get("metadata", {}))
        )
    
    def apply(self, base_length: float) -> float:
        """Apply scalar to base length."""
        if self.scale_type == "linear":
            return base_length * self.scale_factor
        elif self.scale_type == "quadratic":
            return base_length * (self.scale_factor ** 2)
        elif self.scale_type == "cubic":
            return base_length * (self.scale_factor ** 3)
        elif self.scale_type == "polynomial":
            return base_length * (self.scale_factor ** self.polynomial_order)
        else:
            return base_length * self.scale_factor


@dataclass(slots=True)
class ScalarApplication:
    """Application of a scalar to a polyform in a specific context."""
    
    polyform_symbol: str  # Symbol of polyform being scaled
    scalar_id: str  # Scalar being applied
    context: str  # Context of application (e.g., "workspace", "catalog", "user_created")
    stability_impact: float = 0.0  # Impact on stability (can be negative)
    metadata: Dict[str, object] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, object]:
        return {
            "polyform_symbol": self.polyform_symbol,
            "scalar_id": self.scalar_id,
            "context": self.context,
            "stability_impact": self.stability_impact,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "ScalarApplication":
        return cls(
            polyform_symbol=str(data["polyform_symbol"]),
            scalar_id=str(data["scalar_id"]),
            context=str(data["context"]),
            stability_impact=float(data.get("stability_impact", 0.0)),
            metadata=dict(data.get("metadata", {}))
        )


class ScalarRegistry:
    """Registry for scalar definitions and applications."""
    
    def __init__(self):
        self.scalars: Dict[str, ScalarDefinition] = {}
        self.applications: Dict[str, List[ScalarApplication]] = {}  # polyform_symbol -> applications
        self.by_context: Dict[str, List[ScalarApplication]] = {}  # context -> applications
    
    def register_scalar(self, scalar: ScalarDefinition) -> None:
        """Register a scalar definition."""
        self.scalars[scalar.scalar_id] = scalar
    
    def apply_scalar(
        self,
        polyform_symbol: str,
        scalar_id: str,
        context: str = "workspace",
        stability_impact: float = 0.0,
        metadata: Optional[Dict[str, object]] = None
    ) -> ScalarApplication:
        """Apply a scalar to a polyform in a specific context."""
        if scalar_id not in self.scalars:
            raise ValueError(f"Unknown scalar: {scalar_id}")
        
        application = ScalarApplication(
            polyform_symbol=polyform_symbol,
            scalar_id=scalar_id,
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
    
    def get_scalar(self, scalar_id: str) -> Optional[ScalarDefinition]:
        """Get scalar definition by ID."""
        return self.scalars.get(scalar_id)
    
    def get_applications(
        self,
        polyform_symbol: Optional[str] = None,
        context: Optional[str] = None
    ) -> List[ScalarApplication]:
        """Get scalar applications, optionally filtered by polyform or context."""
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
    
    def get_available_scalars(self) -> List[ScalarDefinition]:
        """Get all available scalar definitions."""
        return list(self.scalars.values())


# Singleton instance
_scalar_registry: Optional[ScalarRegistry] = None


def get_scalar_registry() -> ScalarRegistry:
    """Get singleton scalar registry instance."""
    global _scalar_registry
    if _scalar_registry is None:
        _scalar_registry = ScalarRegistry()
        # Initialize with common scalars
        _initialize_default_scalars(_scalar_registry)
    return _scalar_registry


def _initialize_default_scalars(registry: ScalarRegistry) -> None:
    """Initialize registry with default scalar definitions."""
    default_scalars = [
        ScalarDefinition("k1", 1.0, "linear", 1),
        ScalarDefinition("k2", 2.0, "linear", 1),
        ScalarDefinition("k3", 3.0, "linear", 1),
        ScalarDefinition("k4", 4.0, "linear", 1),
        ScalarDefinition("k5", 5.0, "linear", 1),
        ScalarDefinition("quadratic", 2.0, "quadratic", 2),
        ScalarDefinition("cubic", 2.0, "cubic", 3),
    ]
    
    for scalar in default_scalars:
        registry.register_scalar(scalar)


__all__ = [
    "ScalarDefinition",
    "ScalarApplication",
    "ScalarRegistry",
    "get_scalar_registry",
]

