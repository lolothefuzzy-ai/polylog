"""
Unified Backend Geometry System

Uses Netlib's precomputed polyhedra data as single source of truth.
Integrates with all geometry engines (workspace, GPU, interaction, generation).
"""

from polylog6.geometry.unified_backend import (
    GeometryData,
    AttachmentGeometry,
    UnifiedBackendGeometry,
    get_unified_backend_geometry,
)

__all__ = [
    "GeometryData",
    "AttachmentGeometry",
    "UnifiedBackendGeometry",
    "get_unified_backend_geometry",
]

