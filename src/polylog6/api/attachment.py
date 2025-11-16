"""
Attachment sequence API - provides fold sequences for polygon pairs
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from polylog6.simulation.placement.fold_sequencer import FoldSequencer
from polylog6.simulation.placement.runtime import PlacementRuntime
from polylog6.storage.manager import PolyformStorageManager
from pathlib import Path

router = APIRouter(prefix="/api/attachment", tags=["attachment"])

# Initialize storage manager for PlacementRuntime
# Use a temporary directory for storage
_storage_base_path = Path(__file__).parent.parent.parent.parent.parent / "storage" / "caches"
_storage_manager = PolyformStorageManager(base_path=_storage_base_path)

# Provide catalog directory for PlacementRuntime
_catalog_dir = Path(__file__).parent.parent.parent.parent.parent / "catalogs"
_placement_runtime = PlacementRuntime(
    storage_manager=_storage_manager,
    catalog_dir=_catalog_dir
)
_fold_sequencer = FoldSequencer(
    geometry_catalog={},  # Will load from catalog
    scaler_catalog={}
)

class AttachmentSequenceRequest(BaseModel):
    polygonA: str
    polygonB: str
    scaler: float = 1.0

class AttachmentSequenceResponse(BaseModel):
    success: bool
    fold_sequence: Optional[List[Dict[str, Any]]] = None
    fold_angle: Optional[float] = None
    stability: Optional[float] = None
    error: Optional[str] = None

@router.post("/sequence", response_model=AttachmentSequenceResponse)
async def get_attachment_sequence(request: AttachmentSequenceRequest):
    """
    Get fold sequence for attaching two polygons
    Returns the sequence of folds needed to attach polygonB to polygonA
    """
    try:
        # Get attachment schema
        sides_a = _get_sides_from_symbol(request.polygonA)
        sides_b = _get_sides_from_symbol(request.polygonB)
        
        attachment_option = _placement_runtime.resolve_attachment_schema(
            source_sides=sides_a,
            target_sides=sides_b,
            dimension="3d"
        )
        
        if not attachment_option:
            return AttachmentSequenceResponse(
                success=False,
                error="No valid attachment found for this pair"
            )
        
        # Generate fold sequence
        polyform_id = f"{request.polygonA}+{request.polygonB}"
        fold_sequence = _fold_sequencer.generate_sequence(
            polyform_id,
            scaler=request.scaler
        )
        
        # Extract fold angle from first step
        fold_angle = 0
        if fold_sequence.steps:
            fold_angle = fold_sequence.steps[0].angle_degrees
        
        return AttachmentSequenceResponse(
            success=True,
            fold_sequence=[
                {
                    "index": step.index,
                    "polygon_symbol": step.polygon_symbol,
                    "angle_degrees": step.angle_degrees,
                    "axis": step.axis,
                    "duration_ms": step.duration_ms
                }
                for step in fold_sequence.steps
            ],
            fold_angle=fold_angle,
            stability=attachment_option.score
        )
        
    except Exception as e:
        return AttachmentSequenceResponse(
            success=False,
            error=str(e)
        )

def _get_sides_from_symbol(symbol: str) -> int:
    """Convert symbol to sides count"""
    symbol_map = {
        "A": 3, "B": 4, "C": 5, "D": 6, "E": 7, "F": 8, "G": 9, "H": 10,
        "I": 11, "J": 12, "K": 13, "L": 14, "M": 15, "N": 16, "O": 17,
        "P": 18, "Q": 19, "R": 20
    }
    return symbol_map.get(symbol.upper(), 3)

