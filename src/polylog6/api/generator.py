"""
Polyform Generator API endpoints
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
from pathlib import Path

from polylog6.storage.encoder import TieredUnicodeEncoder
from polylog6.simulation.placement.attachment_resolver import AttachmentResolver
from polylog6.simulation.stability.calculator import StabilityCalculator

router = APIRouter(prefix="/api/polyform", tags=["generator"])

# Initialize encoders and calculators
_encoder = TieredUnicodeEncoder()
_stability_calc = StabilityCalculator()


class GenerateRequest(BaseModel):
    polygonA: str
    polygonB: str
    mode: str = "linear"  # 'linear' or 'exponential'
    maxSteps: int = 5
    attachmentOption: Optional[Dict[str, Any]] = None


class GenerateResponse(BaseModel):
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
    catalog_path = Path(__file__).parent.parent.parent.parent / "catalogs" / "geometry_catalog.json"
    if not catalog_path.exists():
        # Try alternative path
        catalog_path = Path(__file__).parent.parent.parent.parent.parent / "catalogs" / "geometry_catalog.json"
    
    if catalog_path.exists():
        with open(catalog_path, "r") as f:
            return json.load(f)
    return {}


def _get_primitive_geometry(symbol: str, catalog: Dict) -> Optional[Dict]:
    """Get geometry for a primitive polygon symbol"""
    if "primitives" not in catalog:
        return None
    
    for name, data in catalog["primitives"].items():
        if data.get("symbol") == symbol.upper():
            return {
                "vertices": data.get("vertices", []),
                "sides": data.get("sides", 0),
                "bounding_box": data.get("bounding_box", {})
            }
    return None


def _calculate_attachment_geometry(polyA: Dict, polyB: Dict, attachment: Dict) -> Dict:
    """Calculate combined geometry from two polygons with attachment"""
    # This is a simplified version - full implementation would use AttachmentResolver
    vertices_a = polyA.get("vertices", [])
    vertices_b = polyB.get("vertices", [])
    
    # For now, return combined vertices (simplified)
    # Real implementation would apply fold angle and position correctly
    combined_vertices = vertices_a + vertices_b
    
    return {
        "vertices": combined_vertices,
        "polygon_count": 2,
        "edge_count": polyA.get("sides", 0) + polyB.get("sides", 0)
    }


def _generate_composition(polyA: str, polyB: str) -> str:
    """Generate composition string"""
    return f"{polyA}+{polyB}"


@router.post("/generate", response_model=GenerateResponse)
async def generate_polyform(request: GenerateRequest):
    """
    Generate a new polyform from two selected polygons
    """
    try:
        catalog = _load_geometry_catalog()
        
        # Get geometries for both polygons
        geom_a = _get_primitive_geometry(request.polygonA, catalog)
        geom_b = _get_primitive_geometry(request.polygonB, catalog)
        
        if not geom_a or not geom_b:
            return GenerateResponse(
                success=False,
                error=f"Could not find geometry for {request.polygonA} or {request.polygonB}"
            )
        
        # Calculate attachment geometry
        attachment_data = request.attachmentOption or {}
        combined_geometry = _calculate_attachment_geometry(geom_a, geom_b, attachment_data)
        
        # Generate composition string
        composition = _generate_composition(request.polygonA, request.polygonB)
        
        # Calculate stability (simplified)
        stability = attachment_data.get("stability", 0.75) if attachment_data else 0.75
        
        # Allocate Unicode symbol
        # Use frequency based on stability (higher stability = higher frequency)
        frequency = int(stability * 1000)
        unicode_symbol = _encoder.allocate(composition, frequency)
        
        # Calculate compression ratio
        # Simplified: ratio = original_size / compressed_size
        original_size = len(composition) * 8  # bytes
        compressed_size = len(unicode_symbol.encode('utf-8'))
        compression_ratio = original_size / compressed_size if compressed_size > 0 else 1.0
        
        # Prepare metadata
        metadata = {
            "polygon_count": combined_geometry.get("polygon_count", 2),
            "edge_count": combined_geometry.get("edge_count", 0),
            "stability": stability,
            "generation_mode": request.mode,
            "composition": composition
        }
        
        # Prepare geometry response
        geometry_response = {
            "lod": {
                "full": {
                    "vertices": combined_geometry.get("vertices", []),
                    "indices": [],
                    "normals": []
                },
                "medium": {"vertices": [], "indices": []},
                "bbox": {
                    "min": [-1, -1, -1],
                    "max": [1, 1, 1]
                }
            },
            "folds": [],
            "metadata": metadata
        }
        
        return GenerateResponse(
            success=True,
            symbol=composition,
            unicode=unicode_symbol,
            composition=composition,
            geometry=geometry_response,
            metadata=metadata,
            compressionRatio=compression_ratio
        )
        
    except Exception as e:
        return GenerateResponse(
            success=False,
            error=str(e)
        )


@router.get("/generated")
async def list_generated_polyforms():
    """List all generated polyforms"""
    # TODO: Implement storage lookup for generated polyforms
    return {
        "polyforms": [],
        "total": 0
    }

