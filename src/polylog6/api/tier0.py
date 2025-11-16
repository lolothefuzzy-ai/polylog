"""
Tier 0 API endpoints for encoding/decoding and atomic chain operations.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from polylog6.storage.tier0_generator import decode_tier0_symbol, ConnectivityChain
from polylog6.storage.atomic_chains import (
    get_atomic_chain_library,
    AtomicChainDetector,
    AtomicChainType
)

router = APIRouter(prefix="/tier0", tags=["tier0"])


class Tier0DecodeRequest(BaseModel):
    symbol: str


class Tier0DecodeResponse(BaseModel):
    symbol: str
    polygons: List[int]
    positions: List[int]
    series: List[str]
    chain_length: int
    edge_signature: str


class AtomicChainDetectRequest(BaseModel):
    symbol: str


class AtomicChainDetectResponse(BaseModel):
    symbol: str
    chain_type: str
    polygon_sequence: List[int]
    length: int
    stability_score: float
    scaffold_applications: List[str]
    metadata: Dict[str, Any]


class ScaffoldCreateRequest(BaseModel):
    atomic_chains: List[str]  # Tier 0 symbols
    target_polyform_type: str


class ScaffoldCreateResponse(BaseModel):
    scaffold_symbol: str
    atomic_chains: List[str]
    target_polyform_type: str
    stability_score: float
    metadata: Dict[str, Any]


@router.post("/decode", response_model=Tier0DecodeResponse)
async def decode_tier0(request: Tier0DecodeRequest):
    """Decode a Tier 0 symbol to get polygon sequence."""
    try:
        chain = decode_tier0_symbol(request.symbol)
        
        return Tier0DecodeResponse(
            symbol=chain.symbol,
            polygons=chain.polygons,
            positions=chain.positions,
            series=chain.series,
            chain_length=len(chain.polygons),
            edge_signature="-".join(str(edge) for edge in chain.polygons)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Decoding error: {str(e)}")


@router.get("/symbols/{symbol}", response_model=Tier0DecodeResponse)
async def get_tier0_symbol(symbol: str):
    """Get Tier 0 symbol details."""
    try:
        chain = decode_tier0_symbol(symbol)
        
        return Tier0DecodeResponse(
            symbol=chain.symbol,
            polygons=chain.polygons,
            positions=chain.positions,
            series=chain.series,
            chain_length=len(chain.polygons),
            edge_signature="-".join(str(edge) for edge in chain.polygons)
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/atomic-chains/detect", response_model=AtomicChainDetectResponse)
async def detect_atomic_chain(request: AtomicChainDetectRequest):
    """Detect atomic chain pattern in Tier 0 symbol."""
    detector = AtomicChainDetector()
    atomic_chain = detector.detect_chain(request.symbol)
    
    if not atomic_chain:
        raise HTTPException(
            status_code=404, 
            detail=f"Could not detect atomic chain in symbol: {request.symbol}"
        )
    
    return AtomicChainDetectResponse(
        symbol=atomic_chain.symbol,
        chain_type=atomic_chain.chain_type.value,
        polygon_sequence=atomic_chain.polygon_sequence,
        length=atomic_chain.length,
        stability_score=atomic_chain.stability_score,
        scaffold_applications=atomic_chain.scaffold_applications,
        metadata=atomic_chain.metadata
    )


@router.get("/atomic-chains/library")
async def get_atomic_chain_library():
    """Get precomputed atomic chain library."""
    library = get_atomic_chain_library()
    
    return {
        "square_chains": [
            {
                "symbol": chain.symbol,
                "length": chain.length,
                "stability_score": chain.stability_score,
                "scaffold_applications": chain.scaffold_applications
            }
            for chain in library.chains.values()
            if chain.chain_type == AtomicChainType.SQUARE_CHAIN
        ],
        "triangle_clusters": [
            {
                "symbol": chain.symbol,
                "length": chain.length,
                "stability_score": chain.stability_score,
                "scaffold_applications": chain.scaffold_applications
            }
            for chain in library.chains.values()
            if chain.chain_type == AtomicChainType.TRIANGLE_CLUSTER
        ],
        "mixed_chains": [
            {
                "symbol": chain.symbol,
                "length": chain.length,
                "stability_score": chain.stability_score,
                "scaffold_applications": chain.scaffold_applications
            }
            for chain in library.chains.values()
            if chain.chain_type == AtomicChainType.MIXED_CHAIN
        ]
    }


@router.post("/scaffolds/create", response_model=ScaffoldCreateResponse)
async def create_scaffold(request: ScaffoldCreateRequest):
    """Create scaffold from atomic chains."""
    library = get_atomic_chain_library()
    
    # Get atomic chains
    atomic_chains = []
    for symbol in request.atomic_chains:
        chain = library.chains.get(symbol)
        if not chain:
            # Try to detect chain
            detector = AtomicChainDetector()
            chain = detector.detect_chain(symbol)
            if chain:
                library.chains[symbol] = chain
        
        if chain:
            atomic_chains.append(chain)
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Atomic chain not found: {symbol}"
            )
    
    # Create scaffold
    scaffold = library.create_scaffold(atomic_chains, request.target_polyform_type)
    
    return ScaffoldCreateResponse(
        scaffold_symbol=scaffold.symbol,
        atomic_chains=[chain.symbol for chain in scaffold.atomic_chains],
        target_polyform_type=scaffold.target_polyform_type,
        stability_score=scaffold.stability_score,
        metadata=scaffold.metadata
    )


@router.get("/scaffolds/johnson-solid/{solid_name}")
async def get_johnson_solid_scaffold(solid_name: str):
    """Get scaffold for a Johnson solid."""
    library = get_atomic_chain_library()
    scaffold = library.get_scaffold_for_johnson_solid(solid_name)
    
    if not scaffold:
        raise HTTPException(
            status_code=404,
            detail=f"Scaffold not found for Johnson solid: {solid_name}"
        )
    
    return {
        "scaffold_symbol": scaffold.symbol,
        "atomic_chains": [
            {
                "symbol": chain.symbol,
                "chain_type": chain.chain_type.value,
                "polygon_sequence": chain.polygon_sequence,
                "length": chain.length,
                "stability_score": chain.stability_score
            }
            for chain in scaffold.atomic_chains
        ],
        "target_polyform_type": scaffold.target_polyform_type,
        "stability_score": scaffold.stability_score,
        "metadata": scaffold.metadata
    }

