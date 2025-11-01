"""Thread-safe caching for stability scoring calculations."""
from __future__ import annotations

import os
import threading
from dataclasses import dataclass
from typing import Any, Callable, Dict, Tuple

from cachetools import TTLCache

from common.logging_setup import get_logger

logger = get_logger(__name__)

# Feature flag - can be set via env var POLYLOG_USE_STABILITY_CACHE
USE_CACHE = os.environ.get('POLYLOG_USE_STABILITY_CACHE', 'True') == 'True'

# Cache configuration - 1000 entries max, 60 second TTL
CACHE = TTLCache(maxsize=1000, ttl=60)
CACHE_LOCK = threading.Lock()

@dataclass(frozen=True)
class StabilityMetricsInput:
    """Normalized input for stability scoring to enable caching."""
    polyform_count: int
    side_counts: Tuple[int, ...] 
    centroids: Tuple[Tuple[float, float, float], ...]
    bond_count: int
    config: Dict[str, Any]

def cached_stability_score(func: Callable) -> Callable:
    """Decorator for thread-safe cached scoring functions."""
    
    def wrapper(metrics_input: StabilityMetricsInput) -> float:
        if not USE_CACHE:
            return func(metrics_input)
            
        # Create cache key from normalized inputs
        cache_key = (
            metrics_input.polyform_count,
            metrics_input.side_counts,
            metrics_input.centroids,
            metrics_input.bond_count,
            tuple(metrics_input.config.items())
        )
        
        with CACHE_LOCK:
            if cache_key in CACHE:
                logger.debug("Cache hit for stability score")
                return CACHE[cache_key]
                
        result = func(metrics_input)
        
        with CACHE_LOCK:
            CACHE[cache_key] = result
            logger.debug("Cache miss - computed new stability score")
            
        return result
        
    return wrapper

def clear_stability_cache() -> None:
    """Clear all cached stability scores."""
    with CACHE_LOCK:
        CACHE.clear()
    logger.info("Stability cache cleared")

__all__ = ["StabilityMetricsInput", "cached_stability_score", "clear_stability_cache"]
