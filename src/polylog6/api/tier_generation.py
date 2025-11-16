"""
Tier Generation API

Endpoints for Tier 1 symmetry-based generation and Tier 2 decomposition.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel

from polylog6.generation.tier1_symmetry_generator import (
    get_tier1_generator,
    Tier1Solid
)
from polylog6.generation.tier2_decomposition import (
    get_tier2_decomposition,
    DecompositionCandidate
)
from polylog6.storage.tier_recursive_structure import RecursivePolyform
from polylog6.storage.atomic_chains import get_atomic_chain_library


router = APIRouter(prefix="/api/generation", tags=["generation"])


class GenerateTier1Request(BaseModel):
    """Request to generate Tier 1 solid."""
    symbol: str
    solid_type: str  # "platonic", "archimedean", "johnson"
    use_scaffold: bool = True  # Use atomic chain scaffolds for Johnson solids


class DecomposeTier2Request(BaseModel):
    """Request to decompose Tier 2 polyform."""
    polyform_symbol: str
    workspace_context: Optional[Dict[str, Any]] = None


@router.post("/tier1/generate")
async def generate_tier1_solid(request: GenerateTier1Request) -> Dict[str, Any]:
    """Generate Tier 1 solid using symmetry operations."""
    generator = get_tier1_generator()
    
    try:
        if request.solid_type == "platonic":
            solid = generator.generate_platonic(request.symbol)
        elif request.solid_type == "archimedean":
            solid = generator.generate_archimedean(request.symbol)
        elif request.solid_type == "johnson":
            # For Johnson solids, try to get scaffold if use_scaffold is True
            if request.use_scaffold:
                atomic_chain_library = get_atomic_chain_library()
                # Try common Johnson solid names
                solid_name = request.symbol.lower().replace("_", " ").replace("-", " ")
                scaffold = atomic_chain_library.get_scaffold_for_johnson_solid(solid_name)
                if scaffold:
                    return {
                        "symbol": request.symbol,
                        "name": solid_name,
                        "solid_type": "johnson",
                        "scaffold": {
                            "scaffold_symbol": scaffold.symbol,
                            "atomic_chains": [chain.symbol for chain in scaffold.atomic_chains],
                            "stability_score": scaffold.stability_score,
                            "metadata": scaffold.metadata
                        },
                        "message": "Scaffold found - full generation requires definition"
                    }
            # Would need definition passed in request for full generation
            raise HTTPException(status_code=400, detail="Johnson solid definition required")
        else:
            raise HTTPException(status_code=400, detail=f"Unknown solid type: {request.solid_type}")
        
        if not solid:
            raise HTTPException(status_code=404, detail=f"Could not generate {request.symbol}")
        
        return {
            "symbol": solid.symbol,
            "name": solid.name,
            "solid_type": solid.solid_type,
            "symmetry": {
                "symmetry_id": solid.symmetry.symmetry_id,
                "symmetry_group": solid.symmetry.symmetry_group,
                "order": solid.symmetry.order
            },
            "tier0_composition": [
                {
                    "symbol": ref.symbol,
                    "position": ref.position,
                    "series_path": ref.series_path
                }
                for ref in solid.tier0_composition
            ],
            "stability_score": solid.stability_score,
            "metadata": solid.metadata
        }
        
        # Add scaffold info if present in metadata
        if "scaffold_symbol" in solid.metadata:
            response["scaffold"] = {
                "scaffold_symbol": solid.metadata.get("scaffold_symbol"),
                "atomic_chains": solid.metadata.get("atomic_chains", []),
                "stability_score": solid.metadata.get("stability_score", solid.stability_score)
            }
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tier2/analyze")
async def analyze_tier2_polyform(
    polyform: RecursivePolyform,
    workspace_context: Optional[Dict[str, Any]] = Body(None)
) -> Dict[str, Any]:
    """Analyze Tier 2 polyform and suggest decompositions."""
    decomposition_engine = get_tier2_decomposition()
    
    try:
        candidates = decomposition_engine.analyze_polyform(
            polyform,
            workspace_context
        )
        
        return {
            "polyform_symbol": polyform.symbol,
            "candidates": [
                {
                    "decomposition_type": c.decomposition_type,
                    "subforms": c.subforms,
                    "stability_improvement": c.stability_improvement,
                    "reason": c.reason
                }
                for c in candidates
            ],
            "has_ring_structure": polyform.symbol in decomposition_engine.ring_structures
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tier2/decompose")
async def decompose_tier2_polyform(request: DecomposeTier2Request) -> Dict[str, Any]:
    """Decompose Tier 2 polyform into stable subforms."""
    decomposition_engine = get_tier2_decomposition()
    
    try:
        # Would need to load polyform from registry
        # For now, return placeholder
        return {
            "polyform_symbol": request.polyform_symbol,
            "decomposed": True,
            "subforms": []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tier1/platonic")
async def list_platonic_solids() -> Dict[str, Any]:
    """List all Platonic solids."""
    generator = get_tier1_generator()
    
    return {
        "solids": [
            {
                "symbol": symbol,
                "name": definition["name"],
                "symmetry": definition["symmetry"],
                "faces": definition["faces"],
                "vertices": definition.get("vertices", 0)
            }
            for symbol, definition in generator.platonic_definitions.items()
        ]
    }


@router.get("/tier1/archimedean")
async def list_archimedean_solids() -> Dict[str, Any]:
    """List all Archimedean solids."""
    generator = get_tier1_generator()
    
    return {
        "solids": [
            {
                "symbol": symbol,
                "name": definition["name"],
                "symmetry": definition["symmetry"],
                "faces": definition["faces"]
            }
            for symbol, definition in generator.archimedean_definitions.items()
        ]
    }

