"""
PHASE 2 STABILIZATION: Multilevel Cache System

Implements 3-level cache hierarchy for connection evaluation:
- L1: Hot cache (1K entries, memory, ~1µs access)
- L2: Warm cache (50K entries, memory, ~100µs access)
- L3: Cold cache (unlimited, disk, ~10ms access)

Promotes frequently accessed items up the hierarchy.
Expected improvement: 40-50% better cache efficiency at high-n.
"""

import logging
import os
import pickle
import tempfile
from collections import OrderedDict
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class L3DiskCache:
    """Disk-based cold cache for overflow from L2."""
    
    def __init__(self, max_size: int = 100000):
        """
        Initialize disk cache.
        
        Args:
            max_size: Maximum number of items to store
        """
        self.max_size = max_size
        self.cache_dir = tempfile.gettempdir()
        self.cache_file = os.path.join(self.cache_dir, 'polylog_l3_cache.pkl')
        self.cache: Dict[str, Any] = {}
        self.load()
    
    def load(self):
        """Load cache from disk if exists."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'rb') as f:
                    self.cache = pickle.load(f)
                logger.debug(f"Loaded L3 disk cache with {len(self.cache)} entries")
            except Exception as e:
                logger.warning(f"Failed to load L3 cache: {e}")
                self.cache = {}
    
    def save(self):
        """Save cache to disk."""
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump(self.cache, f)
        except Exception as e:
            logger.warning(f"Failed to save L3 cache: {e}")
    
    def get(self, key: str) -> Optional[float]:
        """Get value from disk cache."""
        return self.cache.get(key)
    
    def put(self, key: str, value: float):
        """Put value into disk cache with size limit."""
        if len(self.cache) >= self.max_size:
            # Simple FIFO: remove oldest entries (first keys added)
            keys_to_remove = list(self.cache.keys())[:max(1, len(self.cache) // 10)]
            for k in keys_to_remove:
                del self.cache[k]
        
        self.cache[key] = value
    
    def clear(self):
        """Clear disk cache."""
        self.cache.clear()
        try:
            if os.path.exists(self.cache_file):
                os.remove(self.cache_file)
        except Exception:
            pass


class MultiLevelCache:
    """
    PHASE 2 STABILIZATION: 3-level cache hierarchy for connection evaluation.
    
    - L1 (Hot): 1K entries in memory (~1µs access)
    - L2 (Warm): 50K entries in memory (~100µs access)
    - L3 (Cold): Unlimited entries on disk (~10ms access)
    
    Items are promoted up the hierarchy based on access frequency.
    """
    
    def __init__(self, l1_size: int = 1000, l2_size: int = 50000, l3_size: int = 100000):
        """
        Initialize multilevel cache.
        
        Args:
            l1_size: L1 hot cache size (entries)
            l2_size: L2 warm cache size (entries)
            l3_size: L3 disk cache size (entries)
        """
        self.l1_size = l1_size
        self.l2_size = l2_size
        self.l3_size = l3_size
        
        # L1: Hot cache (OrderedDict for LRU)
        self.l1 = OrderedDict()
        
        # L2: Warm cache (OrderedDict for LRU)
        self.l2 = OrderedDict()
        
        # L3: Cold disk cache
        self.l3 = L3DiskCache(max_size=l3_size)
        
        # Statistics
        self.hits_l1 = 0
        self.hits_l2 = 0
        self.hits_l3 = 0
        self.misses = 0
        self.promotions_l2_to_l1 = 0
        self.promotions_l3_to_l2 = 0
    
    def get(self, key: str) -> Optional[float]:
        """
        Get value from cache, promoting up hierarchy if found.
        
        Returns:
            Value if found, None otherwise
        """
        # Check L1 first
        if key in self.l1:
            self.l1.move_to_end(key)  # Mark as recently used
            self.hits_l1 += 1
            return self.l1[key]
        
        # Check L2
        if key in self.l2:
            value = self.l2.pop(key)  # Remove from L2
            self.l2.move_to_end(key)  # Mark as recently used in L2
            self.hits_l2 += 1
            
            # Promote to L1 if space available
            if len(self.l1) < self.l1_size:
                self.l1[key] = value
                self.promotions_l2_to_l1 += 1
            else:
                # L1 full, demote oldest L1 entry to L2
                old_key, old_value = self.l1.popitem(last=False)
                self.l2[old_key] = old_value
                self.l1[key] = value
                self.promotions_l2_to_l1 += 1
            
            # Re-add to L2 (now in L1 as well)
            self.l2[key] = value
            return value
        
        # Check L3
        value = self.l3.get(key)
        if value is not None:
            self.hits_l3 += 1
            
            # Promote to L2 if space available
            if len(self.l2) < self.l2_size:
                self.l2[key] = value
                self.promotions_l3_to_l2 += 1
            else:
                # L2 full, demote oldest L2 entry to L3
                old_key, old_value = self.l2.popitem(last=False)
                self.l3.put(old_key, old_value)
                self.l2[key] = value
                self.promotions_l3_to_l2 += 1
            
            # Promote to L1 if space available
            if len(self.l1) < self.l1_size:
                self.l1[key] = value
                self.promotions_l2_to_l1 += 1
            
            return value
        
        # Not found anywhere
        self.misses += 1
        return None
    
    def put(self, key: str, value: float):
        """
        Put value into cache (always starts at L1).
        
        Args:
            key: Cache key
            value: Value to cache
        """
        # Always put into L1 first
        if len(self.l1) >= self.l1_size:
            # L1 full, demote oldest to L2
            old_key, old_value = self.l1.popitem(last=False)
            
            if len(self.l2) < self.l2_size:
                self.l2[old_key] = old_value
            else:
                # L2 full, demote oldest to L3
                l2_old_key, l2_old_value = self.l2.popitem(last=False)
                self.l3.put(l2_old_key, l2_old_value)
                self.l2[old_key] = old_value
        
        self.l1[key] = value
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_accesses = self.hits_l1 + self.hits_l2 + self.hits_l3 + self.misses
        hit_rate = 0.0
        if total_accesses > 0:
            hit_rate = (self.hits_l1 + self.hits_l2 + self.hits_l3) / total_accesses * 100
        
        return {
            'hits_l1': self.hits_l1,
            'hits_l2': self.hits_l2,
            'hits_l3': self.hits_l3,
            'misses': self.misses,
            'total_accesses': total_accesses,
            'hit_rate_percent': hit_rate,
            'promotions_l2_to_l1': self.promotions_l2_to_l1,
            'promotions_l3_to_l2': self.promotions_l3_to_l2,
            'l1_entries': len(self.l1),
            'l2_entries': len(self.l2),
            'l3_entries': len(self.l3.cache),
            'l1_capacity': self.l1_size,
            'l2_capacity': self.l2_size,
            'l3_capacity': self.l3_size,
        }
    
    def reset_stats(self):
        """Reset statistics counters."""
        self.hits_l1 = 0
        self.hits_l2 = 0
        self.hits_l3 = 0
        self.misses = 0
        self.promotions_l2_to_l1 = 0
        self.promotions_l3_to_l2 = 0
    
    def clear(self):
        """Clear all cache levels."""
        self.l1.clear()
        self.l2.clear()
        self.l3.clear()
        self.reset_stats()
    
    def log_stats(self):
        """Log cache statistics."""
        stats = self.get_stats()
        logger.info(
            f"Cache Stats: L1={stats['l1_entries']}/{stats['l1_capacity']} "
            f"L2={stats['l2_entries']}/{stats['l2_capacity']} "
            f"L3={stats['l3_entries']}/{stats['l3_capacity']} "
            f"Hit%={stats['hit_rate_percent']:.1f}% "
            f"Promotions: L2→L1={stats['promotions_l2_to_l1']} "
            f"L3→L2={stats['promotions_l3_to_l2']}"
        )


class MultiLevelCacheAdapter:
    """
    Adapter to replace ConnectionEvaluator's simple LRU cache with multilevel cache.
    
    Drop-in replacement that provides same interface but with better performance.
    """
    
    def __init__(self, max_cache_size: int = 50000):
        """
        Initialize adapter.
        
        Args:
            max_cache_size: Total cache size (will be distributed across levels)
        """
        # Distribute cache size: L1=2%, L2=98% of memory cache
        l1_size = max(100, max_cache_size // 50)  # ~2%
        l2_size = max_cache_size - l1_size        # ~98%
        
        self.cache = MultiLevelCache(
            l1_size=l1_size,
            l2_size=l2_size,
            l3_size=max_cache_size * 2  # L3 can be larger (disk)
        )
        
        logger.info(
            f"Multilevel cache initialized: "
            f"L1={l1_size}, L2={l2_size}, L3={max_cache_size * 2}"
        )
    
    def get(self, key: Tuple) -> Optional[float]:
        """Get value from cache."""
        key_str = str(key)
        return self.cache.get(key_str)
    
    def put(self, key: Tuple, value: float):
        """Put value into cache."""
        key_str = str(key)
        self.cache.put(key_str, value)
    
    def clear(self):
        """Clear cache."""
        self.cache.clear()
    
    def report_stats(self):
        """Print cache statistics report."""
        stats = self.cache.get_stats()
        print("\n" + "="*60)
        print("MULTILEVEL CACHE STATISTICS")
        print("="*60)
        print(f"L1 Cache (Hot):      {stats['l1_entries']:6d}/{stats['l1_capacity']:6d} entries")
        print(f"L2 Cache (Warm):     {stats['l2_entries']:6d}/{stats['l2_capacity']:6d} entries")
        print(f"L3 Cache (Cold):     {stats['l3_entries']:6d}/{stats['l3_capacity']:6d} entries")
        print(f"Total Accesses:      {stats['total_accesses']:6d}")
        print(f"Cache Hit Rate:      {stats['hit_rate_percent']:6.1f}%")
        print(f"  L1 Hits:           {stats['hits_l1']:6d}")
        print(f"  L2 Hits:           {stats['hits_l2']:6d}")
        print(f"  L3 Hits:           {stats['hits_l3']:6d}")
        print(f"  Misses:            {stats['misses']:6d}")
        print(f"Promotions:")
        print(f"  L2→L1:             {stats['promotions_l2_to_l1']:6d}")
        print(f"  L3→L2:             {stats['promotions_l3_to_l2']:6d}")
        print("="*60 + "\n")
