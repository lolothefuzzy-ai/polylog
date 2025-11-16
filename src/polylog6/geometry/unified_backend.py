"""
Unified Backend Geometry Structure

Uses Netlib's precomputed polyhedra data as the single source of truth
for all geometry operations. Integrates with all geometry engines.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set
from pathlib import Path
import json
import math

from polylog6.api.tier1_polyhedra import _load_polyhedra, _load_attachment_matrix
from polylog6.storage.tier0_generator import decode_tier0_symbol


@dataclass(slots=True)
class GeometryData:
    """Unified geometry data structure from Netlib."""
    
    symbol: str
    vertices: List[Tuple[float, float, float]]
    faces: List[List[int]]  # Face vertex indices
    edges: List[Tuple[int, int]]  # Edge vertex pairs
    dihedral_angles: List[float]  # Dihedral angles for each edge
    face_types: Dict[int, int]  # edge_count -> count
    netlib_id: Optional[int] = None
    classification: Optional[str] = None  # "platonic", "archimedean", "johnson"
    symmetry_group: Optional[str] = None
    
    def to_dict(self) -> Dict[str, any]:
        return {
            "symbol": self.symbol,
            "vertices": self.vertices,
            "faces": self.faces,
            "edges": self.edges,
            "dihedral_angles": self.dihedral_angles,
            "face_types": self.face_types,
            "netlib_id": self.netlib_id,
            "classification": self.classification,
            "symmetry_group": self.symmetry_group
        }


@dataclass(slots=True)
class AttachmentGeometry:
    """Geometry data for polygon attachment."""
    
    polygon_a_sides: int
    polygon_b_sides: int
    fold_angle: float  # Dihedral angle from attachment matrix
    stability_score: float
    attachment_points: List[Tuple[int, int]]  # (edge_a, edge_b) pairs
    metadata: Dict[str, any] = field(default_factory=dict)


class UnifiedBackendGeometry:
    """Unified backend geometry service using Netlib data."""
    
    def __init__(self):
        self._polyhedra_cache: Optional[Dict[str, Dict[str, any]]] = None
        self._attachment_matrix_cache: Optional[Dict[str, any]] = None
        self._geometry_cache: Dict[str, GeometryData] = {}
        
    def load_netlib_data(self) -> None:
        """Load Netlib polyhedra data and attachment matrix."""
        self._polyhedra_cache = _load_polyhedra()
        self._attachment_matrix_cache = _load_attachment_matrix()
        
    def get_polyhedron_geometry(self, symbol: str) -> Optional[GeometryData]:
        """Get geometry data for polyhedron from Netlib."""
        if symbol in self._geometry_cache:
            return self._geometry_cache[symbol]
        
        if not self._polyhedra_cache:
            self.load_netlib_data()
        
        if not self._polyhedra_cache or symbol not in self._polyhedra_cache:
            return None
        
        poly_data = self._polyhedra_cache[symbol]
        
        # Extract geometry from Netlib data
        vertices = poly_data.get("vertices", [])
        faces_data = poly_data.get("faces", [])
        
        # Convert faces to vertex indices
        faces = []
        for face in faces_data:
            if isinstance(face, dict):
                faces.append(face.get("vertices", []))
            elif isinstance(face, list):
                faces.append(face)
        
        # Extract edges from faces
        edges = self._extract_edges_from_faces(faces)
        
        # Get dihedral angles
        dihedral_angles = poly_data.get("dihedral_angles", [])
        
        # Extract face types
        face_types = {}
        for face in faces_data:
            if isinstance(face, dict):
                edge_count = face.get("edges", len(face.get("vertices", [])))
                face_types[edge_count] = face_types.get(edge_count, 0) + 1
        
        geometry = GeometryData(
            symbol=symbol,
            vertices=vertices,
            faces=faces,
            edges=edges,
            dihedral_angles=dihedral_angles,
            face_types=face_types,
            netlib_id=poly_data.get("netlib_id"),
            classification=poly_data.get("classification"),
            symmetry_group=poly_data.get("symmetry_group")
        )
        
        self._geometry_cache[symbol] = geometry
        return geometry
    
    def get_primitive_geometry(self, sides: int) -> GeometryData:
        """Get geometry for primitive polygon (3-20 sides)."""
        # Generate unit edge polygon geometry
        unit_edge_length = 1.0
        circumradius = unit_edge_length / (2 * math.sin(math.pi / sides))
        internal_angle = ((sides - 2) * math.pi) / sides
        
        # Generate vertices on XZ plane
        vertices = []
        for i in range(sides):
            angle = (i * 2 * math.pi) / sides
            x = circumradius * math.cos(angle)
            z = circumradius * math.sin(angle)
            vertices.append((x, 0.0, z))
        
        # Create single face (all vertices)
        faces = [list(range(sides))]
        
        # Create edges (circular)
        edges = [(i, (i + 1) % sides) for i in range(sides)]
        
        # No dihedral angles for single polygon
        dihedral_angles = []
        
        return GeometryData(
            symbol=f"primitive_{sides}",
            vertices=vertices,
            faces=faces,
            edges=edges,
            dihedral_angles=dihedral_angles,
            face_types={sides: 1}
        )
    
    def get_attachment_geometry(
        self,
        polygon_a_sides: int,
        polygon_b_sides: int
    ) -> Optional[AttachmentGeometry]:
        """Get attachment geometry from attachment matrix."""
        if not self._attachment_matrix_cache:
            self.load_netlib_data()
        
        if not self._attachment_matrix_cache:
            return None
        
        # Lookup in attachment matrix
        # Matrix structure: {symbol_a: {symbol_b: [attachment_options]}}
        symbol_a = self._sides_to_symbol(polygon_a_sides)
        symbol_b = self._sides_to_symbol(polygon_b_sides)
        
        if not symbol_a or not symbol_b:
            return None
        
        # Normalize order (smaller symbol first)
        if symbol_a > symbol_b:
            symbol_a, symbol_b = symbol_b, symbol_a
        
        matrix = self._attachment_matrix_cache
        if symbol_a not in matrix or symbol_b not in matrix[symbol_a]:
            return None
        
        options = matrix[symbol_a][symbol_b]
        if not options:
            return None
        
        # Get first (most stable) option
        option = options[0] if isinstance(options, list) else options
        
        fold_angle = option.get("fold_angle", 0.0)
        stability_score = option.get("stability", 0.5)
        
        return AttachmentGeometry(
            polygon_a_sides=polygon_a_sides,
            polygon_b_sides=polygon_b_sides,
            fold_angle=fold_angle,
            stability_score=stability_score,
            attachment_points=[]  # Would be calculated from actual geometry
        )
    
    def get_fold_angle(
        self,
        polygon_a_sides: int,
        polygon_b_sides: int
    ) -> Optional[float]:
        """Get fold angle from attachment matrix."""
        attachment = self.get_attachment_geometry(polygon_a_sides, polygon_b_sides)
        return attachment.fold_angle if attachment else None
    
    def get_tier0_geometry(self, tier0_symbol: str) -> Optional[GeometryData]:
        """Get geometry for Tier 0 symbol by decoding and combining primitives."""
        try:
            chain = decode_tier0_symbol(tier0_symbol)
        except (ValueError, AttributeError):
            return None
        
        if not hasattr(chain, 'polygons') or not chain.polygons:
            return None
        
        # Generate geometry for each polygon in chain
        all_vertices = []
        all_faces = []
        all_edges = []
        vertex_offset = 0
        
        for polygon_sides in chain.polygons:
            primitive = self.get_primitive_geometry(polygon_sides)
            
            # Add vertices with offset
            for vertex in primitive.vertices:
                all_vertices.append(vertex)
            
            # Add faces with vertex offset
            for face in primitive.faces:
                all_faces.append([v + vertex_offset for v in face])
            
            # Add edges with vertex offset
            for edge in primitive.edges:
                all_edges.append((edge[0] + vertex_offset, edge[1] + vertex_offset))
            
            vertex_offset += len(primitive.vertices)
        
        return GeometryData(
            symbol=tier0_symbol,
            vertices=all_vertices,
            faces=all_faces,
            edges=all_edges,
            dihedral_angles=[],  # Would be calculated from chain
            face_types={sides: chain.polygons.count(sides) for sides in set(chain.polygons)}
        )
    
    def _extract_edges_from_faces(self, faces: List[List[int]]) -> List[Tuple[int, int]]:
        """Extract unique edges from faces."""
        edge_set: Set[Tuple[int, int]] = set()
        
        for face in faces:
            for i in range(len(face)):
                v1 = face[i]
                v2 = face[(i + 1) % len(face)]
                # Normalize edge order (smaller vertex first)
                edge = (min(v1, v2), max(v1, v2))
                edge_set.add(edge)
        
        return sorted(list(edge_set))
    
    def _sides_to_symbol(self, sides: int) -> Optional[str]:
        """Convert polygon sides to symbol (A-R)."""
        symbol_map = {
            3: "A", 4: "B", 5: "C", 6: "D", 7: "E", 8: "F",
            9: "G", 10: "H", 11: "I", 12: "J", 13: "K", 14: "L",
            15: "M", 16: "N", 17: "O", 18: "P", 19: "Q", 20: "R"
        }
        return symbol_map.get(sides)


# Singleton instance
_unified_backend: Optional[UnifiedBackendGeometry] = None


def get_unified_backend_geometry() -> UnifiedBackendGeometry:
    """Get singleton unified backend geometry instance."""
    global _unified_backend
    if _unified_backend is None:
        _unified_backend = UnifiedBackendGeometry()
        _unified_backend.load_netlib_data()
    return _unified_backend


__all__ = [
    "GeometryData",
    "AttachmentGeometry",
    "UnifiedBackendGeometry",
    "get_unified_backend_geometry",
]

