"""
Polyform Generator API endpoints
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
from pathlib import Path
import math

from polylog6.storage.encoder import TieredUnicodeEncoder
from polylog6.storage.polyform_storage import PolyformStorage

router = APIRouter(prefix="/api/polyform", tags=["generator"])

# Initialize encoders and calculators
_encoder = TieredUnicodeEncoder()
_storage = PolyformStorage()

# Symbol to sides mapping
SYMBOL_TO_SIDES = {
    "A": 3, "B": 4, "C": 5, "D": 6, "E": 7, "F": 8, "G": 9, "H": 10,
    "I": 11, "J": 12, "K": 13, "L": 14, "M": 15, "N": 16, "O": 17,
    "P": 18, "Q": 19, "R": 20
}


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


def _generate_regular_polygon_vertices(sides: int, radius: float = 1.0) -> List[List[float]]:
    """Generate vertices for a regular polygon"""
    vertices = []
    angle_step = 2 * math.pi / sides
    
    for i in range(sides):
        angle = i * angle_step - math.pi / 2  # Start from top
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        vertices.append([x, y, 0])
    
    return vertices


def _calculate_attachment_geometry(polyA: Dict, polyB: Dict, attachment: Dict) -> Dict:
    """Calculate combined geometry from two polygons with attachment"""
    vertices_a = polyA.get("vertices", [])
    vertices_b = polyB.get("vertices", [])
    
    # Get attachment parameters
    fold_angle = attachment.get("fold_angle", 0)
    stability = attachment.get("stability", 0.5)
    context = attachment.get("context", "edge_to_edge")
    
    # Calculate combined geometry
    if context == "edge_to_edge":
        # Place polygon B adjacent to polygon A
        # Find the rightmost point of polygon A
        if vertices_a:
            max_x = max(v[0] for v in vertices_a)
            # Offset polygon B vertices
            offset_x = max_x + 0.1  # Small gap
            vertices_b_offset = [[v[0] + offset_x, v[1], v[2]] for v in vertices_b]
        else:
            vertices_b_offset = vertices_b
    else:
        # Default: place side by side
        vertices_b_offset = [[v[0] + 2, v[1], v[2]] for v in vertices_b]
    
    # Combine vertices
    combined_vertices = vertices_a + vertices_b_offset
    
    # Calculate indices for triangulation
    indices = []
    vertex_count = len(combined_vertices)
    
    # Simple triangulation for each polygon separately
    # Polygon A
    if len(vertices_a) >= 3:
        for i in range(1, len(vertices_a) - 1):
            indices.append([0, i, i + 1])
    
    # Polygon B
    if len(vertices_b_offset) >= 3:
        offset = len(vertices_a)
        for i in range(1, len(vertices_b_offset) - 1):
            indices.append([offset, offset + i, offset + i + 1])
    
    # Calculate normals (simplified - pointing up)
    normals = [[0, 0, 1]] * len(combined_vertices)
    
    # Calculate bounding box
    if combined_vertices:
        min_coords = [min(v[i] for v in combined_vertices) for i in range(3)]
        max_coords = [max(v[i] for v in combined_vertices) for i in range(3)]
        bbox = {"min": min_coords, "max": max_coords}
    else:
        bbox = {"min": [0, 0, 0], "max": [1, 1, 1]}
    
    return {
        "vertices": combined_vertices,
        "indices": indices,
        "normals": normals,
        "bbox": bbox,
        "polygon_count": 2,
        "edge_count": polyA.get("sides", 0) + polyB.get("sides", 0)
    }


def _generate_composition(polyA: str, polyB: str) -> str:
    """Generate composition string"""
    return f"{polyA}+{polyB}"


def _calculate_stability(geometry: Dict, attachment: Dict) -> float:
    """Calculate stability score for the generated polyform"""
    # Simplified stability calculation
    stability = attachment.get("stability", 0.5)
    
    # Adjust based on geometry properties
    edge_count = geometry.get("edge_count", 0)
    if edge_count > 0:
        # More edges generally means more complex but potentially less stable
        edge_factor = max(0.3, 1.0 - (edge_count - 6) * 0.05)
        stability *= edge_factor
    
    # Ensure stability is within valid range
    return max(0.0, min(1.0, stability))


@router.post("/generate", response_model=GenerateResponse)
async def generate_polyform(request: GenerateRequest):
    """Generate a new polyform from two polygons"""
    try:
        # Load geometry catalog
        catalog = _load_geometry_catalog()
        
        # Get polygon geometries
        polyA = _get_primitive_geometry(request.polygonA, catalog)
        polyB = _get_primitive_geometry(request.polygonB, catalog)
        
        if not polyA or not polyB:
            # Generate default geometries if not found in catalog
            sides_a = SYMBOL_TO_SIDES.get(request.polygonA.upper(), 3)
            sides_b = SYMBOL_TO_SIDES.get(request.polygonB.upper(), 3)
            
            polyA = {
                "vertices": _generate_regular_polygon_vertices(sides_a),
                "sides": sides_a
            }
            polyB = {
                "vertices": _generate_regular_polygon_vertices(sides_b),
                "sides": sides_b
            }
        
        # Resolve attachment
        if request.attachmentOption:
            attachment = request.attachmentOption
        else:
            # Default attachment
            attachment = {
                "fold_angle": 0,
                "stability": 0.75,
                "context": "edge_to_edge"
            }
        
        # Calculate combined geometry
        combined_geometry = _calculate_attachment_geometry(polyA, polyB, attachment)
        
        # Generate composition and Unicode symbol
        composition = _generate_composition(request.polygonA, request.polygonB)
        
        # Calculate frequency based on mode and steps
        if request.mode == "exponential":
            frequency = 100 * (2 ** request.maxSteps)
        else:
            frequency = 100 * request.maxSteps
        
        # Allocate Unicode symbol
        unicode_symbol = _encoder.allocate(composition, frequency)
        
        # Calculate compression ratio
        original_size = len(composition) * 8  # 8 bytes per character
        compressed_size = len(unicode_symbol.encode('utf-8'))
        compression_ratio = original_size / compressed_size if compressed_size > 0 else 1.0
        
        # Calculate stability
        stability = _calculate_stability(combined_geometry, attachment)
        
        # Generate metadata
        metadata = {
            "polygon_count": combined_geometry.get("polygon_count", 2),
            "edge_count": combined_geometry.get("edge_count", 0),
            "stability": stability,
            "generation_mode": request.mode,
            "attachment_context": attachment.get("context", "edge_to_edge"),
            "fold_angle": attachment.get("fold_angle", 0),
            "max_steps": request.maxSteps
        }
        
        # Prepare geometry response
        geometry_response = {
            "lod": {
                "full": {
                    "vertices": combined_geometry.get("vertices", []),
                    "indices": combined_geometry.get("indices", []),
                    "normals": combined_geometry.get("normals", [])
                },
                "medium": {
                    "vertices": combined_geometry.get("vertices", []),  # Same for now
                    "indices": combined_geometry.get("indices", []),
                    "normals": combined_geometry.get("normals", [])
                },
                "thumbnail": {
                    "vertices": combined_geometry.get("vertices", []),  # Same for now
                    "indices": combined_geometry.get("indices", []),
                    "normals": combined_geometry.get("normals", [])
                },
                "bbox": combined_geometry.get("bbox", {"min": [-1, -1, -1], "max": [1, 1, 1]})
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
    try:
        polyforms = _storage.list_all()
        return {
            "polyforms": polyforms,
            "total": len(polyforms)
        }
    except Exception as e:
        return {
            "polyforms": [],
            "total": 0,
            "error": str(e)
        }


@router.get("/generated/{composition}")
async def get_generated_polyform(composition: str):
    """Get a specific generated polyform by composition"""
    try:
        polyform = _storage.get_by_composition(composition)
        if polyform:
            return {
                "success": True,
                "polyform": polyform
            }
        else:
            return {
                "success": False,
                "error": f"Polyform '{composition}' not found"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/stats")
async def get_storage_stats():
    """Get storage statistics"""
    try:
        stats = _storage.get_stats()
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }