"""Storage-facing API routes for Unicode tier catalogs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Response

from polylog6.storage.symbol_registry import (
    PAIR_BY_SYMBOL,
    PRIMITIVE_BY_SYMBOL,
    SymbolRegistry,
)


router = APIRouter(prefix="/storage", tags=["storage"])

_ROOT = Path(__file__).resolve().parents[3]
_CATALOG_ROOT = _ROOT / "catalogs"
_CANDIDATE_LOG = _ROOT / "storage" / "caches" / "tier_candidates.jsonl"

_registry = SymbolRegistry()


def _paginate(items: List[Dict[str, Any]], page: int, limit: int) -> Dict[str, Any]:
    total = len(items)
    start = page * limit
    end = start + limit
    page_items = items[start:end]
    pages = (total + limit - 1) // limit if limit else 1
    return {
        "symbols": page_items,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages,
    }


def _etag_response(payload: Dict[str, Any]) -> Response:
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    digest = hashlib.md5(raw).hexdigest()
    return Response(content=raw, media_type="application/json", headers={"ETag": f'"{digest}"'})


def _tier0_payload() -> List[Dict[str, Any]]:
    return [
        {
            "symbol": symbol,
            "tier": 0,
            "composition": symbol,
            "metadata": {"edges": edges},
        }
        for edges, symbol in _registry.iter_primitives()
    ]


def _pair_payload() -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for symbol, primitives in PAIR_BY_SYMBOL.items():
        if len(primitives) != 2:
            continue
        first, second = primitives
        composition = "+".join(sorted((first, second)))
        items.append(
            {
                "symbol": symbol,
                "tier": 1,
                "composition": composition,
                "metadata": {"pair": [first, second]},
            }
        )
    return items


def _load_catalog(filename: str) -> List[Dict[str, Any]]:
    path = _CATALOG_ROOT / filename
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        entries = data.get("entries")
        return entries if isinstance(entries, list) else []
    return []


def _tier_catalog_entries(tier: int) -> List[Dict[str, Any]]:
    filename = {3: "tier3_library.json", 4: "tier4_library.json"}.get(tier)
    if not filename:
        return []
    entries = _load_catalog(filename)
    normalized: List[Dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        normalized.append(
            {
                "symbol": entry.get("symbol"),
                "tier": tier,
                "composition": entry.get("base_composition") or entry.get("composition"),
                "frequency": entry.get("frequency", 0),
                "metadata": entry,
            }
        )
    return normalized


def _load_candidates() -> Dict[int, List[Dict[str, Any]]]:
    result: Dict[int, List[Dict[str, Any]]] = {3: [], 4: []}
    if not _CANDIDATE_LOG.exists():
        return result
    for line in _CANDIDATE_LOG.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        tier = record.get("tier")
        if tier in result:
            result[tier].append(record)
    return result


@router.get("/symbols")
def get_symbols(
    tier: Optional[int] = Query(None, description="Filter by tier (0,1,3,4)"),
    page: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> Response:
    """Return a paginated list of Tier-aware symbols."""

    tiers = [tier] if tier is not None else [0, 1, 3, 4]
    invalid = set(tiers) - {0, 1, 3, 4}
    if invalid:
        raise HTTPException(status_code=400, detail="Unsupported tier")

    payload: List[Dict[str, Any]] = []
    for t in tiers:
        if t == 0:
            payload.extend(_tier0_payload())
        elif t == 1:
            payload.extend(_pair_payload())
        else:
            payload.extend(_tier_catalog_entries(t))

    paginated = _paginate(payload, page, limit)
    return _etag_response(paginated)


@router.get("/polyform/{symbol}")
def expand_polyform(symbol: str) -> Dict[str, Any]:
    """Expand a symbol to its base composition and metadata."""

    if symbol in PRIMITIVE_BY_SYMBOL:
        edges = PRIMITIVE_BY_SYMBOL[symbol]
        return {
            "symbol": symbol,
            "tier": 0,
            "composition": symbol,
            "geometry": {"edges": edges},
            "metrics": {},
        }

    if symbol in PAIR_BY_SYMBOL:
        first, second = PAIR_BY_SYMBOL[symbol]
        composition = "+".join(sorted((first, second)))
        return {
            "symbol": symbol,
            "tier": 1,
            "composition": composition,
            "metadata": {"pair": [first, second]},
            "metrics": {},
        }

    for tier in (3, 4):
        for entry in _tier_catalog_entries(tier):
            if entry.get("symbol") == symbol:
                metadata = entry.get("metadata", {})
                return {
                    "symbol": symbol,
                    "tier": tier,
                    "composition": entry.get("composition"),
                    "geometry": metadata.get("geometry", {}),
                    "metrics": metadata.get("metrics", {}),
                    "metadata": metadata,
                }

    raise HTTPException(status_code=404, detail="Symbol not found")


def _to_subscript(value: int) -> str:
    table = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
    return str(value).translate(table)


@router.post("/polyform", status_code=201)
def create_polyform(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Register a new polyform composition (placeholder for promotion pipeline)."""

    composition = payload.get("composition")
    if not isinstance(composition, str) or not composition:
        raise HTTPException(status_code=400, detail="composition is required")

    provisional_symbol = f"Ξ{_to_subscript(len(composition))}"
    return {
        "symbol": provisional_symbol,
        "tier": 3,
        "composition": composition,
        "metadata": {"provisional": True},
    }


@router.get("/tier3-tier4/candidates")
def get_promotion_candidates() -> Dict[str, List[Dict[str, Any]]]:
    """Return live Tier 3/4 promotion candidates."""

    candidates = _load_candidates()
    return {
        "tier3": candidates.get(3, []),
        "tier4": candidates.get(4, []),
    }


@router.get("/stats")
def get_storage_stats() -> Dict[str, Any]:
    """Return aggregate counts for each tier."""

    tier_counts = {
        "0": len(_tier0_payload()),
        "1": len(_pair_payload()),
        "3": len(_tier_catalog_entries(3)),
        "4": len(_tier_catalog_entries(4)),
    }
    totals = {
        "symbols": sum(tier_counts.values()),
        "bytes_raw": 0,
        "bytes_compressed": 0,
    }
    return {
        "tiers": {tier: {"count": count} for tier, count in tier_counts.items()},
        "totals": totals,
    }
