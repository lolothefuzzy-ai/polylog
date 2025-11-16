"""
Geometry API Endpoints

Exposes unified backend geometry system for frontend and other services.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from polylog6.geometry import get_unified_backend_geometry

router = APIRouter(prefix="/geometry", tags=["geometry"])


@router.get("/polyhedron/{symbol}")
async def get_polyhedron_geometry(symbol: str):
    """Get geometry data for polyhedron from Netlib."""
    backend = get_unified_backend_geometry()
    geometry = backend.get_polyhedron_geometry(symbol)
    
    if not geometry:
        raise HTTPException(status_code=404, detail=f"Polyhedron {symbol} not found")
    
    return geometry.to_dict()


@router.get("/primitive/{sides}")
async def get_primitive_geometry(sides: int):
    """Get geometry for primitive polygon (3-20 sides)."""
    if sides < 3 or sides > 20:
        raise HTTPException(status_code=400, detail="Sides must be 3-20")
    
    backend = get_unified_backend_geometry()
    geometry = backend.get_primitive_geometry(sides)
    
    return geometry.to_dict()


@router.get("/attachment/{sides_a}/{sides_b}")
async def get_attachment_geometry(sides_a: int, sides_b: int):
    """Get attachment geometry from attachment matrix."""
    if sides_a < 3 or sides_a > 20 or sides_b < 3 or sides_b > 20:
        raise HTTPException(status_code=400, detail="Sides must be 3-20")
    
    backend = get_unified_backend_geometry()
    attachment = backend.get_attachment_geometry(sides_a, sides_b)
    
    if not attachment:
        raise HTTPException(
            status_code=404,
            detail=f"Attachment data not found for {sides_a}-{sides_b}"
        )
    
    return {
        "polygon_a_sides": attachment.polygon_a_sides,
        "polygon_b_sides": attachment.polygon_b_sides,
        "fold_angle": attachment.fold_angle,
        "stability_score": attachment.stability_score,
        "attachment_points": attachment.attachment_points,
        "metadata": attachment.metadata
    }


@router.get("/fold-angle/{sides_a}/{sides_b}")
async def get_fold_angle(sides_a: int, sides_b: int):
    """Get fold angle from attachment matrix."""
    if sides_a < 3 or sides_a > 20 or sides_b < 3 or sides_b > 20:
        raise HTTPException(status_code=400, detail="Sides must be 3-20")
    
    backend = get_unified_backend_geometry()
    fold_angle = backend.get_fold_angle(sides_a, sides_b)
    
    if fold_angle is None:
        raise HTTPException(
            status_code=404,
            detail=f"Fold angle not found for {sides_a}-{sides_b}"
        )
    
    return {"fold_angle": fold_angle}


@router.get("/tier0/{symbol}")
async def get_tier0_geometry(symbol: str):
    """Get geometry for Tier 0 symbol."""
    backend = get_unified_backend_geometry()
    geometry = backend.get_tier0_geometry(symbol)
    
    if not geometry:
        raise HTTPException(status_code=404, detail=f"Tier 0 symbol {symbol} not found")
    
    return geometry.to_dict()

