"""
API endpoints for attachment patterns
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
import json
from pathlib import Path

router = APIRouter(prefix="/api/patterns", tags=["attachment_patterns"])

# Load patterns catalog
_patterns_cache = None
_patterns_file = None

def _load_patterns():
    """Load attachment patterns catalog"""
    global _patterns_cache, _patterns_file
    
    if _patterns_cache is not None:
        return _patterns_cache
    
    # Try multiple locations
    possible_paths = [
        Path("data/catalogs/tier1/attachment_patterns.jsonl"),
        Path("lib/catalogs/tier1/attachment_patterns.jsonl"),
        Path(__file__).parent.parent.parent.parent / "data" / "catalogs" / "tier1" / "attachment_patterns.jsonl"
    ]
    
    for path in possible_paths:
        if path.exists():
            _patterns_file = path
            break
    
    if not _patterns_file or not _patterns_file.exists():
        _patterns_cache = []
        return _patterns_cache
    
    patterns = []
    with open(_patterns_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    patterns.append(json.loads(line))
                except:
                    continue
    
    _patterns_cache = patterns
    return patterns

@router.get("/patterns")
async def get_attachment_patterns(
    pattern_type: Optional[str] = Query(None, description="Filter by pattern type"),
    min_length: Optional[int] = Query(None, description="Minimum pattern length"),
    page: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """Get attachment patterns"""
    patterns = _load_patterns()
    
    # Apply filters
    filtered = patterns
    if pattern_type:
        filtered = [p for p in filtered if p.get('pattern_type') == pattern_type]
    if min_length:
        filtered = [p for p in filtered if p.get('length', 0) >= min_length]
    
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

@router.get("/patterns/{pattern_id}")
async def get_attachment_pattern(pattern_id: str):
    """Get specific attachment pattern"""
    patterns = _load_patterns()
    
    for pattern in patterns:
        if pattern.get('pattern_id') == pattern_id:
            return pattern
    
    raise HTTPException(status_code=404, detail="Pattern not found")

@router.get("/patterns/type/{pattern_type}")
async def get_patterns_by_type(pattern_type: str):
    """Get all patterns of a specific type"""
    patterns = _load_patterns()
    
    matching = [p for p in patterns if p.get('pattern_type') == pattern_type]
    
    return {
        'pattern_type': pattern_type,
        'patterns': matching,
        'count': len(matching)
    }

