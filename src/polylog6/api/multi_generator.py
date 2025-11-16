"""
Multi-polygon generation API (3+ polygons)
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
from pathlib import Path

from polylog6.storage.encoder import TieredUnicodeEncoder
from polylog6.storage.polyform_storage import PolyformStorage
from polylog6.simulation.placement.runtime import PlacementRuntime
from polylog6.simulation.stability.calculator import StabilityCalculator

router = APIRouter(prefix="/api/polyform", tags=["multi_generator"])

_encoder = TieredUnicodeEncoder()
_storage = PolyformStorage()
_placement_runtime = PlacementRuntime()
_stability_calc = StabilityCalculator()

SYMBOL_TO_SIDES = {
    "A": 3, "B": 4, "C": 5, "D": 6, "E": 7, "F": 8, "G": 9, "H": 10,
    "I": 11, "J": 12, "K": 13, "L": 14, "M": 15, "N": 16, "O": 17,
    "P": 18, "Q": 19, "R": 20
}

class MultiGenerateRequest(BaseModel):
    polygons: List[str]  # List of polygon symbols
    mode: str = "linear"  # "linear", "exponential", "pattern"
    pattern_type: Optional[str] = None  # For pattern mode
    max_steps: int = 10

class MultiGenerateResponse(BaseModel):
    success: bool
    symbol: Optional[str] = None
    unicode: Optional[str] = None
    composition: Optional[str] = None
    geometry: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    compressionRatio: Optional[float] = None
    error: Optional[str] = None

def _load_geometry_catalog():
    """Load geometry catalog"""
    possible_paths = [
        Path("data/catalogs/geometry_catalog.json"),
        Path("lib/catalogs/geometry_catalog.json"),
        Path(__file__).parent.parent.parent.parent / "data" / "catalogs" / "geometry_catalog.json"
    ]
    
    for path in possible_paths:
        if path.exists():
            with open(path, 'r') as f:
                return json.load(f)
    
    return {"primitives": {}}

def _get_primitive_geometry(symbol: str, catalog: Dict) -> Optional[Dict[str, Any]]:
    """Get primitive geometry from catalog"""
    for name, data in catalog.get("primitives", {}).items():
        if data.get("symbol") == symbol.upper():
            return {
                "vertices": data.get("vertices", []),
                "indices": [],
                "sides": data.get("sides", 3)
            }
    return None

def _generate_regular_polygon_vertices(sides: int, radius: float = 1.0) -> List[List[float]]:
    """Generate regular polygon vertices"""
    import math
    vertices = []
    for i in range(sides):
        angle = 2 * math.pi * i / sides
        vertices.append([radius * math.cos(angle), radius * math.sin(angle), 0.0])
    return vertices

def _combine_geometries(geometries: List[Dict[str, Any]], attachment_sequence: List[Dict]) -> Dict[str, Any]:
    """Combine multiple geometries based on attachment sequence"""
    if not geometries:
        return {"vertices": [], "indices": [], "normals": []}
    
    if len(geometries) == 1:
        return geometries[0]
    
    # Start with first geometry
    combined_vertices = geometries[0].get("vertices", [])[:]
    offset = len(combined_vertices)
    
    # Add subsequent geometries with offsets
    for i, geom in enumerate(geometries[1:], 1):
        vertices = geom.get("vertices", [])
        # Simple translation for now (would use attachment sequence in full implementation)
        translation = [i * 2.5, 0, 0]  # Place side by side
        translated_vertices = [
            [v[0] + translation[0], v[1] + translation[1], v[2] + translation[2]]
            for v in vertices
        ]
        combined_vertices.extend(translated_vertices)
    
    # Generate indices
    indices = []
    vertex_idx = 0
    for geom in geometries:
        vertex_count = len(geom.get("vertices", []))
        # Simple triangulation
        for j in range(1, vertex_count - 1):
            indices.extend([vertex_idx, vertex_idx + j, vertex_idx + j + 1])
        vertex_idx += vertex_count
    
    return {
        "vertices": combined_vertices,
        "indices": indices,
        "normals": [[0, 0, 1]] * len(combined_vertices),
        "polygon_count": len(geometries),
        "edge_count": sum(g.get("sides", 0) for g in geometries)
    }

@router.post("/generate-multi", response_model=MultiGenerateResponse)
async def generate_multi_polyform(request: MultiGenerateRequest):
    """Generate a polyform from 3+ polygons"""
    try:
        if len(request.polygons) < 3:
            return MultiGenerateResponse(
                success=False,
                error="Multi-polygon generation requires at least 3 polygons"
            )
        
        catalog = _load_geometry_catalog()
        
        # Load geometries for all polygons
        geometries = []
        for symbol in request.polygons:
            geom = _get_primitive_geometry(symbol, catalog)
            if not geom:
                # Generate default
                sides = SYMBOL_TO_SIDES.get(symbol.upper(), 3)
                geom = {
                    "vertices": _generate_regular_polygon_vertices(sides),
                    "sides": sides
                }
            geometries.append(geom)
        
        # Generate attachment sequence
        attachment_sequence = []
        for i in range(len(request.polygons) - 1):
            attachment_sequence.append({
                "from": i,
                "to": i + 1,
                "edge_a": 0,
                "edge_b": 0
            })
        
        # Combine geometries
        combined_geometry = _combine_geometries(geometries, attachment_sequence)
        
        # Generate composition string
        composition = "+".join(request.polygons)
        
        # Calculate overall stability (simplified)
        stability = 0.75  # Would calculate from attachment sequence
        
        # Allocate Unicode symbol
        frequency = int(stability * 1000)
        unicode_symbol = _encoder.allocate(composition, frequency)
        
        # Calculate compression ratio
        original_size = len(composition) * 8
        compressed_size = len(unicode_symbol.encode('utf-8'))
        compression_ratio = original_size / compressed_size if compressed_size > 0 else 1.0
        
        # Prepare metadata
        metadata = {
            "polygon_count": len(request.polygons),
            "edge_count": combined_geometry.get("edge_count", 0),
            "stability": stability,
            "generation_mode": request.mode,
            "composition": composition,
            "attachment_count": len(attachment_sequence)
        }
        
        # Prepare geometry response
        geometry_response = {
            "lod": {
                "full": {
                    "vertices": combined_geometry.get("vertices", []),
                    "indices": combined_geometry.get("indices", []),
                    "normals": combined_geometry.get("normals", [])
                }
            },
            "folds": [],
            "metadata": metadata
        }
        
        # Store generated polyform
        storage_data = {
            "composition": composition,
            "geometry": geometry_response,
            "metadata": metadata,
            "unicode": unicode_symbol,
            "compression_ratio": compression_ratio
        }
        _storage.add(composition, storage_data, frequency)
        
        return MultiGenerateResponse(
            success=True,
            symbol=composition,
            unicode=unicode_symbol,
            composition=composition,
            geometry=geometry_response,
            metadata=metadata,
            compressionRatio=compression_ratio
        )
        
    except Exception as e:
        return MultiGenerateResponse(
            success=False,
            error=str(e)
        )

