"""Canonical estimator for Polylog assemblies.

This module computes a lightweight estimate of the canonical state count for a
polyform assembly.  The legacy system expressed the relationship as::

    N = T * n! * s**n

where ``n`` is the number of polygons, ``s`` the number of sides, and ``T`` a
transformation scaling factor that captures connectivity.  Modern assemblies may
contain multiple polygon types and symmetry adjustments, so the estimator below
extends the expression in two ways:

1. Polygon types are provided as ``(sides, count)`` pairs (or dicts with ``a``
   and ``c`` keys).  The contribution of each type is ``factorial(count)
   * sides**count`` and the final ``N`` is the product across types.
2. A symmetry factor (≤ 1.0) scales the count down to reflect indistinguishable
   configurations.

The estimator returns both ``N`` and ``logN`` plus a Shannon-style diversity
index and records results in a small in-memory cache so repeated requests can be
replayed via ``get_cached``.
"""

from __future__ import annotations

import math
from typing import Dict, List, Sequence, Tuple, Union

# Public types -----------------------------------------------------------------
PolygonType = Union[Tuple[int, int], Dict[str, Union[int, float]]]
EstimatePayload = Dict[str, Union[float, List[Tuple[int, int]], str, int]]

# Internal cache keyed by (types tuple, rounded T, rounded symmetry)
_ESTIMATE_CACHE: Dict[Tuple[Tuple[int, int], float, float], EstimatePayload] = {}


def _normalise_types(types: Sequence[PolygonType]) -> List[Tuple[int, int]]:
    """Normalise polygon types into ``(sides, count)`` tuples."""

    normalised: List[Tuple[int, int]] = []
    for entry in types:
        if isinstance(entry, dict):
            sides = int(entry.get("a") or entry.get("sides") or 0)
            count = int(entry.get("c") or entry.get("count") or 0)
        else:
            sides, count = entry
        if sides <= 0 or count <= 0:
            continue
        normalised.append((sides, count))

    # Sort by sides to keep cache keys deterministic
    normalised.sort(key=lambda item: item[0])
    return normalised


def _diversity_index(types: Sequence[Tuple[int, int]]) -> float:
    """Compute a simple Shannon diversity index for polygon composition."""

    total = sum(count for _, count in types)
    if total == 0:
        return 0.0

    proportions = [count / total for _, count in types]
    # Shannon entropy normalised by log(num_types) to keep result in 0..1 range
    entropy = -sum(p * math.log(p) for p in proportions if p > 0)
    if len(proportions) <= 1:
        return 0.0
    normaliser = math.log(len(proportions))
    return float(entropy / normaliser) if normaliser > 0 else 0.0


def _estimate_value(T: float, types: Sequence[Tuple[int, int]], symmetry_factor: float) -> float:
    """Compute canonical state count ``N`` based on the extended formula."""

    if T <= 0:
        raise ValueError("Transformation parameter T must be positive")
    if symmetry_factor <= 0:
        raise ValueError("Symmetry factor must be positive")

    value = float(T) * float(symmetry_factor)
    for sides, count in types:
        value *= math.factorial(count) * (sides ** count)
    return value


def canonical_estimate(
    *,
    T: float,
    types: Sequence[PolygonType],
    symmetry_factor: float = 1.0,
    symmetry_notes: str = "",
    agent_id: str = "api",
    cache_key: str | None = None,
) -> EstimatePayload:
    """Estimate canonical polyform counts.

    Args:
        T: Transformation parameter capturing connectivity/complexity.
        types: Polygon composition as ``(sides, count)`` pairs or dicts with
            ``a``/``c`` keys.
        symmetry_factor: Reduction factor in the range (0, 1].
        symmetry_notes: Freeform text describing detected symmetry.
        agent_id: Identifier of the caller (used for telemetry/debugging).
        cache_key: Optional external key used to alias the global cache.

    Returns:
        Dictionary containing ``N``, ``logN``, normalised ``types`` and
        additional metadata for telemetry dashboards.
    """

    normalised_types = _normalise_types(types)
    value = _estimate_value(T, normalised_types, symmetry_factor)
    log_value = math.log(value) if value > 0 else float("-inf")
    diversity = _diversity_index(normalised_types)

    payload: EstimatePayload = {
        "T": float(T),
        "symmetry_factor": float(symmetry_factor),
        "symmetry_notes": symmetry_notes,
        "types": normalised_types,
        "N": value,
        "logN": log_value,
        "diversity_index": diversity,
        "polygon_total": sum(count for _, count in normalised_types),
        "agent_id": agent_id,
    }

    # Record in cache keyed by intrinsic attributes for quick replay.
    intrinsic_key = (
        tuple(normalised_types),
        round(float(T), 6),
        round(float(symmetry_factor), 6),
    )
    _ESTIMATE_CACHE[intrinsic_key] = payload
    if cache_key is not None:
        _ESTIMATE_CACHE[(cache_key, 0.0, 0.0)] = payload

    return payload


def get_cached(*, cache_key: str | None = None, types: Sequence[PolygonType] | None = None,
               T: float | None = None, symmetry_factor: float | None = None) -> EstimatePayload | None:
    """Retrieve a cached estimate.

    Callers may provide either the explicit ``cache_key`` used when estimating or
    the canonical trio ``(types, T, symmetry_factor)``.  Returns ``None`` if no
    matching entry is stored.
    """

    if cache_key:
        return _ESTIMATE_CACHE.get((cache_key, 0.0, 0.0))

    if types is None or T is None or symmetry_factor is None:
        return None

    normalised = _normalise_types(types)
    lookup_key = (
        tuple(normalised),
        round(float(T), 6),
        round(float(symmetry_factor), 6),
    )
    return _ESTIMATE_CACHE.get(lookup_key)


def clear_cache() -> None:
    """Clear all cached estimates (useful for tests)."""

    _ESTIMATE_CACHE.clear()
