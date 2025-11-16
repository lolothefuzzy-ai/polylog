"""
Tier 1 Polyhedra API Routes

Exposes extracted polyhedra from Netlib, attachment matrix, and LOD metadata
for frontend rendering and testing.
"""

import json
from pathlib import Path as PathLib
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Response, Path
import hashlib

router = APIRouter(prefix="/tier1", tags=["tier1-polyhedra"])

_ROOT = PathLib(__file__).resolve().parents[3]
_CATALOG_ROOT = _ROOT / "catalogs"
_TIER1_DIR = _CATALOG_ROOT / "tier1"
_ATTACHMENTS_DIR = _CATALOG_ROOT / "attachments"

# Cache loaded data
_polyhedra_cache: Optional[Dict[str, Dict[str, Any]]] = None
_decompositions_cache: Optional[Dict[str, Any]] = None
_attachment_matrix_cache: Optional[Dict[str, Any]] = None
_lod_metadata_cache: Optional[Dict[str, Any]] = None


def _load_polyhedra() -> Dict[str, Dict[str, Any]]:
    """Load polyhedra from JSONL file."""
    global _polyhedra_cache
    
    if _polyhedra_cache is not None:
        return _polyhedra_cache
    
    _polyhedra_cache = {}
    polyhedra_file = _TIER1_DIR / "polyhedra.jsonl"
    
    if not polyhedra_file.exists():
        return _polyhedra_cache
    
    try:
        with open(polyhedra_file, 'r') as f:
            for line in f:
                if line.strip():
                    poly = json.loads(line)
                    _polyhedra_cache[poly['symbol']] = poly
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading polyhedra: {e}")
    
    return _polyhedra_cache


def _load_decompositions() -> Dict[str, Any]:
    """Load decompositions from JSON file."""
    global _decompositions_cache
    
    if _decompositions_cache is not None:
        return _decompositions_cache
    
    decompositions_file = _TIER1_DIR / "decompositions.json"
    
    if not decompositions_file.exists():
        return {}
    
    try:
        _decompositions_cache = json.loads(decompositions_file.read_text())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading decompositions: {e}")
    
    return _decompositions_cache


def _load_attachment_matrix() -> Dict[str, Any]:
    """Load attachment matrix from JSON file."""
    global _attachment_matrix_cache
    
    if _attachment_matrix_cache is not None:
        return _attachment_matrix_cache
    
    matrix_file = _ATTACHMENTS_DIR / "attachment_matrix.json"
    
    if not matrix_file.exists():
        return {}
    
    try:
        _attachment_matrix_cache = json.loads(matrix_file.read_text())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading attachment matrix: {e}")
    
    return _attachment_matrix_cache


def _load_lod_metadata() -> Dict[str, Any]:
    """Load LOD metadata from JSON file."""
    global _lod_metadata_cache
    
    if _lod_metadata_cache is not None:
        return _lod_metadata_cache
    
    lod_file = _TIER1_DIR / "lod_metadata.json"
    
    if not lod_file.exists():
        return {}
    
    try:
        _lod_metadata_cache = json.loads(lod_file.read_text())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading LOD metadata: {e}")
    
    return _lod_metadata_cache


def _etag_response(payload: Dict[str, Any]) -> Response:
    """Generate ETag response."""
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    digest = hashlib.md5(raw).hexdigest()
    return Response(content=raw, media_type="application/json", headers={"ETag": f'"{digest}"'})


@router.get("/polyhedra")
def list_polyhedra(
    page: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> Response:
    """List all extracted Tier 1 polyhedra with pagination."""
    polyhedra = _load_polyhedra()
    
    symbols = sorted(polyhedra.keys())
    total = len(symbols)
    start = page * limit
    end = start + limit
    page_symbols = symbols[start:end]
    
    items = [
        {
            "symbol": sym,
            "name": polyhedra[sym].get("name"),
            "classification": polyhedra[sym].get("classification"),
            "composition": polyhedra[sym].get("composition"),
            "face_count": len(polyhedra[sym].get("faces", [])),
            "vertex_count": len(polyhedra[sym].get("vertices", [])),
        }
        for sym in page_symbols
    ]
    
    payload = {
        "polyhedra": items,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit,
    }
    
    return _etag_response(payload)


@router.get("/polyhedra/{symbol}")
def get_polyhedron(symbol: str) -> Dict[str, Any]:
    """Get full polyhedron data by symbol."""
    polyhedra = _load_polyhedra()
    
    if symbol not in polyhedra:
        raise HTTPException(status_code=404, detail=f"Polyhedron {symbol} not found")
    
    poly = polyhedra[symbol]
    lod_data = _load_lod_metadata().get(symbol, {})
    
    return {
        "symbol": symbol,
        "name": poly.get("name"),
        "netlib_id": poly.get("netlib_id"),
        "classification": poly.get("classification"),
        "composition": poly.get("composition"),
        "faces": poly.get("faces", []),
        "vertices": poly.get("vertices", []),
        "dihedral_angles": poly.get("dihedral_angles", []),
        "symmetry_group": poly.get("symmetry_group"),
        "compression_ratio": poly.get("compression_ratio", 1.0),
        "lod": lod_data,
    }


@router.get("/polyhedra/{symbol}/lod/{level}", response_model=dict)
def get_polyhedron_lod(symbol: str, level: str = Path(..., regex="^(full|medium|low|thumbnail)$")) -> Dict[str, Any]:
    """Get polyhedron geometry at specific LOD level."""
    polyhedra = _load_polyhedra()
    
    if symbol not in polyhedra:
        raise HTTPException(status_code=404, detail=f"Polyhedron {symbol} not found")
    
    poly = polyhedra[symbol]
    lod_data = _load_lod_metadata().get(symbol, {}).get(level)
    
    if not lod_data:
        raise HTTPException(status_code=404, detail=f"LOD level {level} not found for {symbol}")
    
    # For LOD, return reduced geometry based on level
    faces = poly.get("faces", [])
    vertices = poly.get("vertices", [])
    
    # Calculate reduction based on LOD level
    face_ratio = {
        "full": 1.0,
        "medium": 0.6,
        "low": 0.2,
        "thumbnail": 0.05,
    }.get(level, 1.0)
    
    reduced_face_count = max(1, int(len(faces) * face_ratio))
    reduced_faces = faces[:reduced_face_count]
    
    return {
        "symbol": symbol,
        "level": level,
        "faces": reduced_faces,
        "vertices": vertices,
        "metadata": lod_data,
    }


@router.get("/attachments/{polygon_a}/{polygon_b}")
def get_attachment_options(polygon_a: str, polygon_b: str) -> Dict[str, Any]:
    """Get attachment options between two polygon types."""
    matrix = _load_attachment_matrix()
    
    if polygon_a not in matrix:
        raise HTTPException(status_code=404, detail=f"Polygon type {polygon_a} not found")
    
    if polygon_b not in matrix[polygon_a]:
        raise HTTPException(status_code=404, detail=f"No attachment options for {polygon_a}↔{polygon_b}")
    
    options = matrix[polygon_a][polygon_b]
    
    return {
        "pair": f"{polygon_a}↔{polygon_b}",
        "options": options,
        "count": len(options),
        "stable_count": sum(1 for opt in options if opt.get("stability", 0) >= 0.7),
    }


@router.get("/attachments/matrix")
def get_attachment_matrix() -> Response:
    """Get full 18×18 attachment matrix."""
    matrix = _load_attachment_matrix()
    
    # Calculate statistics
    total_pairs = 0
    populated_pairs = 0
    total_options = 0
    stable_options = 0
    
    for polygon_a in matrix:
        for polygon_b in matrix[polygon_a]:
            total_pairs += 1
            options = matrix[polygon_a][polygon_b]
            if options:
                populated_pairs += 1
                total_options += len(options)
                stable_options += sum(1 for opt in options if opt.get("stability", 0) >= 0.7)
    
    payload = {
        "matrix": matrix,
        "statistics": {
            "total_pairs": total_pairs,
            "populated_pairs": populated_pairs,
            "coverage": f"{100 * populated_pairs / total_pairs:.1f}%" if total_pairs > 0 else "0%",
            "total_options": total_options,
            "stable_options": stable_options,
        },
    }
    
    return _etag_response(payload)


@router.get("/stats")
def get_tier1_stats() -> Dict[str, Any]:
    """Get statistics about Tier 1 polyhedra."""
    polyhedra = _load_polyhedra()
    matrix = _load_attachment_matrix()
    lod_data = _load_lod_metadata()
    
    # Calculate stats
    total_polyhedra = len(polyhedra)
    total_faces = sum(len(p.get("faces", [])) for p in polyhedra.values())
    total_vertices = sum(len(p.get("vertices", [])) for p in polyhedra.values())
    
    classifications = {}
    for poly in polyhedra.values():
        cls = poly.get("classification", "unknown")
        classifications[cls] = classifications.get(cls, 0) + 1
    
    # Attachment matrix stats
    total_pairs = 0
    populated_pairs = 0
    total_options = 0
    
    for polygon_a in matrix:
        for polygon_b in matrix[polygon_a]:
            total_pairs += 1
            if matrix[polygon_a][polygon_b]:
                populated_pairs += 1
                total_options += len(matrix[polygon_a][polygon_b])
    
    return {
        "polyhedra": {
            "total": total_polyhedra,
            "total_faces": total_faces,
            "total_vertices": total_vertices,
            "average_faces": round(total_faces / total_polyhedra, 1) if total_polyhedra > 0 else 0,
            "average_vertices": round(total_vertices / total_polyhedra, 1) if total_polyhedra > 0 else 0,
            "classifications": classifications,
        },
        "attachments": {
            "total_pairs": total_pairs,
            "populated_pairs": populated_pairs,
            "coverage": f"{100 * populated_pairs / total_pairs:.1f}%" if total_pairs > 0 else "0%",
            "total_options": total_options,
        },
        "lod": {
            "total_entries": len(lod_data),
            "levels": ["full", "medium", "low", "thumbnail"],
        },
    }


@router.post("/test/decode/{symbol}")
def test_decode_polyhedron(symbol: str, lod: str = Query("full", regex="^(full|medium|low|thumbnail)$")) -> Dict[str, Any]:
    """Test endpoint for frontend to decode polyhedron symbol."""
    polyhedra = _load_polyhedra()
    
    if symbol not in polyhedra:
        raise HTTPException(status_code=404, detail=f"Polyhedron {symbol} not found")
    
    poly = polyhedra[symbol]
    lod_data = _load_lod_metadata().get(symbol, {}).get(lod, {})
    
    return {
        "symbol": symbol,
        "name": poly.get("name"),
        "composition": poly.get("composition"),
        "lod_level": lod,
        "lod_metadata": lod_data,
        "faces": poly.get("faces", []),
        "vertices": poly.get("vertices", []),
        "compression_ratio": poly.get("compression_ratio", 1.0),
    }
