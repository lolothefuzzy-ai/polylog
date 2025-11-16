"""
API endpoints for scalar variants
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
import json
from pathlib import Path

router = APIRouter(prefix="/api/scalar", tags=["scalar_variants"])

# Load scalar variants catalog
_variants_cache = None
_variants_file = None

def _load_variants():
    """Load scalar variants catalog"""
    global _variants_cache, _variants_file
    
    if _variants_cache is not None:
        return _variants_cache
    
    # Try multiple locations
    possible_paths = [
        Path("data/catalogs/tier1/scalar_variants.jsonl"),
        Path("lib/catalogs/tier1/scalar_variants.jsonl"),
        Path(__file__).parent.parent.parent.parent / "data" / "catalogs" / "tier1" / "scalar_variants.jsonl"
    ]
    
    for path in possible_paths:
        if path.exists():
            _variants_file = path
            break
    
    if not _variants_file or not _variants_file.exists():
        _variants_cache = []
        return _variants_cache
    
    variants = []
    with open(_variants_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    variants.append(json.loads(line))
                except:
                    continue
    
    _variants_cache = variants
    return variants

@router.get("/variants")
async def get_scalar_variants(
    base_symbol: Optional[str] = Query(None, description="Filter by base symbol"),
    scale_factor: Optional[int] = Query(None, description="Filter by scale factor"),
    page: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """Get scalar variants"""
    variants = _load_variants()
    
    # Apply filters
    filtered = variants
    if base_symbol:
        filtered = [v for v in filtered if v.get('base_symbol') == base_symbol or v.get('symbol', '').startswith(base_symbol)]
    if scale_factor:
        filtered = [v for v in filtered if v.get('scale_factor') == scale_factor]
    
    # Paginate
    total = len(filtered)
    start = page * limit
    end = start + limit
    items = filtered[start:end]
    
    return {
        'items': items,
        'total': total,
        'page': page,
        'limit': limit,
        'has_more': end < total
    }

@router.get("/variants/{variant_id}")
async def get_scalar_variant(variant_id: str):
    """Get specific scalar variant"""
    variants = _load_variants()
    
    for variant in variants:
        if variant.get('variant_id') == variant_id or variant.get('symbol') == variant_id:
            return variant
    
    raise HTTPException(status_code=404, detail="Variant not found")

@router.get("/variants/base/{base_symbol}")
async def get_variants_for_base(base_symbol: str):
    """Get all variants for a base polyhedron"""
    variants = _load_variants()
    
    matching = [
        v for v in variants
        if v.get('base_symbol') == base_symbol or v.get('symbol', '').startswith(base_symbol)
    ]
    
    return {
        'base_symbol': base_symbol,
        'variants': matching,
        'count': len(matching)
    }

