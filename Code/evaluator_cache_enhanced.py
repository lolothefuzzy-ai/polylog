"""
Enhanced Evaluator Cache with Connection Pooling
=================================================

Improvements over basic EvaluatorCache:
- Connection pooling (multiple DB connections)
- Query batching (group inserts/updates)
- Async support for non-blocking operations
- Database indexing for faster lookups
- LRU memory cache + SQLite disk cache hybrid
- Thread-safe operations
- Statistics tracking
"""

import sqlite3
import threading
import queue
import time
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
from dataclasses import dataclass
from collections import OrderedDict
import json


@dataclass
class CacheStats:
    """Statistics for cache performance monitoring"""
    hits: int = 0
    misses: int = 0
    inserts: int = 0
    batch_queries: int = 0
    total_queries: int = 0
    avg_query_time_ms: float = 0.0


class ConnectionPool:
    """Thread-safe SQLite connection pool"""
    
    def __init__(self, db_path: str, pool_size: int = 5):
        self.db_path = db_path
        self.pool_size = pool_size
        self._pool: queue.Queue = queue.Queue(maxsize=pool_size)
        self._lock = threading.Lock()
        
        # Pre-populate pool
        for _ in range(pool_size):
            conn = self._create_connection()
            self._pool.put(conn)
    
    def _create_connection(self) -> sqlite3.Connection:
        """Create a new SQLite connection"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.isolation_level = None  # Autocommit mode
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_connection(self, timeout: float = 5.0) -> sqlite3.Connection:
        """Get a connection from pool (blocks if unavailable)"""
        try:
            return self._pool.get(timeout=timeout)
        except queue.Empty:
            # Create a new temporary connection if pool exhausted
            return self._create_connection()
    
    def return_connection(self, conn: sqlite3.Connection):
        """Return connection to pool"""
        try:
            self._pool.put_nowait(conn)
        except queue.Full:
            conn.close()
    
    def close_all(self):
        """Close all connections in pool"""
        while not self._pool.empty():
            try:
                conn = self._pool.get_nowait()
                conn.close()
            except queue.Empty:
                break


class EnhancedEvaluatorCache:
    """
    Enhanced cache with connection pooling, batching, and async support.
    
    Hybrid approach:
    - L1: In-memory LRU cache (fast, volatile)
    - L2: SQLite disk cache (persistent, indexed)
    """
    
    def __init__(self, db_path: str = "./cache/evaluator.db", 
                 memory_cache_size: int = 5000,
                 pool_size: int = 5,
                 batch_size: int = 100):
        self.db_path = db_path
        self.memory_cache_size = memory_cache_size
        self.batch_size = batch_size
        
        # Ensure cache directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize connection pool
        self.pool = ConnectionPool(self.db_path, pool_size=pool_size)
        
        # In-memory LRU cache
        self.memory_cache: OrderedDict = OrderedDict()
        
        # Batch write queue
        self.write_queue: queue.Queue = queue.Queue()
        self.batch_lock = threading.Lock()
        
        # Statistics
        self.stats = CacheStats()
        self.stats_lock = threading.Lock()
        
        # Initialize database schema
        self._init_schema()
        
        # Start batch writer thread
        self._writer_thread = threading.Thread(target=self._batch_writer_loop, daemon=True)
        self._writer_thread.start()
        self._stop_writer = False
    
    def _init_schema(self):
        """Initialize database schema with indexes"""
        conn = self.pool.get_connection()
        try:
            cursor = conn.cursor()
            
            # Create main cache table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    cache_key TEXT PRIMARY KEY,
                    value REAL NOT NULL,
                    timestamp REAL NOT NULL,
                    hits INTEGER DEFAULT 0,
                    created_at REAL NOT NULL
                )
            """)
            
            # Create indexes for common queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp ON cache(timestamp)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_hits ON cache(hits)
            """)
            
            # Create metadata table for bulk stats
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cache_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            
            conn.commit()
        finally:
            self.pool.return_connection(conn)
    
    def get(self, key: str) -> Optional[float]:
        """
        Get value from cache (L1 memory → L2 disk).
        
        Returns:
            Cached float value or None
        """
        # Check L1 memory cache
        if key in self.memory_cache:
            self.memory_cache.move_to_end(key)
            with self.stats_lock:
                self.stats.hits += 1
            return self.memory_cache[key]
        
        # Check L2 disk cache
        conn = self.pool.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM cache WHERE cache_key = ?", (key,))
            row = cursor.fetchone()
            
            if row:
                value = row[0]
                # Update hit count and move to memory cache
                self._add_to_memory_cache(key, value)
                cursor.execute("UPDATE cache SET hits = hits + 1 WHERE cache_key = ?", (key,))
                
                with self.stats_lock:
                    self.stats.hits += 1
                
                return value
            else:
                with self.stats_lock:
                    self.stats.misses += 1
                return None
        finally:
            self.pool.return_connection(conn)
    
    def set(self, key: str, value: float):
        """
        Set value in cache (L1 + queue for L2).
        Uses batching for efficiency.
        """
        # Add to memory cache
        self._add_to_memory_cache(key, value)
        
        # Queue for batch disk write
        self.write_queue.put((key, value, time.time()))
        
        with self.stats_lock:
            self.stats.inserts += 1
    
    def batch_get(self, keys: List[str]) -> Dict[str, Optional[float]]:
        """
        Get multiple values efficiently.
        
        Returns:
            Dict mapping keys to values (None if not found)
        """
        result = {}
        disk_keys = []
        
        # Check memory cache first
        for key in keys:
            if key in self.memory_cache:
                result[key] = self.memory_cache[key]
                self.memory_cache.move_to_end(key)
                with self.stats_lock:
                    self.stats.hits += 1
            else:
                disk_keys.append(key)
        
        # Batch query disk cache
        if disk_keys:
            conn = self.pool.get_connection()
            try:
                cursor = conn.cursor()
                placeholders = ",".join("?" * len(disk_keys))
                cursor.execute(
                    f"SELECT cache_key, value FROM cache WHERE cache_key IN ({placeholders})",
                    disk_keys
                )
                
                for row in cursor.fetchall():
                    key, value = row[0], row[1]
                    result[key] = value
                    self._add_to_memory_cache(key, value)
                    cursor.execute("UPDATE cache SET hits = hits + 1 WHERE cache_key = ?", (key,))
                    with self.stats_lock:
                        self.stats.hits += 1
                
                # Record misses
                found_keys = set(result.keys())
                for key in disk_keys:
                    if key not in found_keys:
                        result[key] = None
                        with self.stats_lock:
                            self.stats.misses += 1
                
                conn.commit()
            finally:
                self.pool.return_connection(conn)
        
        with self.stats_lock:
            self.stats.batch_queries += 1
        
        return result
    
    def batch_set(self, items: Dict[str, float]):
        """Set multiple values efficiently"""
        timestamp = time.time()
        for key, value in items.items():
            self._add_to_memory_cache(key, value)
            self.write_queue.put((key, value, timestamp))
        
        with self.stats_lock:
            self.stats.inserts += len(items)
    
    def _add_to_memory_cache(self, key: str, value: float):
        """Add to L1 memory cache with LRU eviction"""
        self.memory_cache[key] = value
        self.memory_cache.move_to_end(key)
        
        # Evict oldest if size exceeded
        while len(self.memory_cache) > self.memory_cache_size:
            self.memory_cache.popitem(last=False)
    
    def _batch_writer_loop(self):
        """Background thread for batching writes to disk cache"""
        batch = []
        last_flush = time.time()
        
        while not self._stop_writer:
            try:
                # Try to get item from queue (timeout to allow periodic flush)
                try:
                    item = self.write_queue.get(timeout=1.0)
                    batch.append(item)
                except queue.Empty:
                    pass
                
                # Flush if batch full or timeout
                should_flush = (
                    len(batch) >= self.batch_size or
                    (time.time() - last_flush) > 5.0
                )
                
                if should_flush and batch:
                    self._flush_batch(batch)
                    batch = []
                    last_flush = time.time()
            
            except Exception as e:
                print(f"Error in batch writer: {e}")
        
        # Final flush
        if batch:
            self._flush_batch(batch)
    
    def _flush_batch(self, batch: List[Tuple[str, float, float]]):
        """Flush batched writes to disk cache"""
        if not batch:
            return
        
        conn = self.pool.get_connection()
        try:
            cursor = conn.cursor()
            
            # Use INSERT OR REPLACE for upsert
            for key, value, ts in batch:
                cursor.execute("""
                    INSERT OR REPLACE INTO cache (cache_key, value, timestamp, created_at)
                    VALUES (?, ?, ?, ?)
                """, (key, value, ts, ts))
            
            conn.commit()
            
            with self.stats_lock:
                self.stats.total_queries += len(batch)
        except Exception as e:
            print(f"Error flushing batch to cache: {e}")
            conn.rollback()
        finally:
            self.pool.return_connection(conn)
    
    def clear(self):
        """Clear all cache (memory + disk)"""
        self.memory_cache.clear()
        
        conn = self.pool.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM cache")
            conn.commit()
        finally:
            self.pool.return_connection(conn)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.stats_lock:
            hit_rate = (
                self.stats.hits / (self.stats.hits + self.stats.misses)
                if (self.stats.hits + self.stats.misses) > 0
                else 0.0
            )
            
            return {
                "hits": self.stats.hits,
                "misses": self.stats.misses,
                "hit_rate": hit_rate,
                "inserts": self.stats.inserts,
                "batch_queries": self.stats.batch_queries,
                "total_queries": self.stats.total_queries,
                "memory_cache_size": len(self.memory_cache),
                "memory_cache_max": self.memory_cache_size,
            }
    
    def get_disk_size(self) -> int:
        """Get disk cache size in bytes"""
        try:
            return Path(self.db_path).stat().st_size
        except:
            return 0
    
    def optimize(self):
        """Optimize database (VACUUM, analyze)"""
        conn = self.pool.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("VACUUM")
            cursor.execute("ANALYZE")
            conn.commit()
        finally:
            self.pool.return_connection(conn)
    
    def prune_old_entries(self, older_than_seconds: float = 86400):
        """Remove cache entries older than specified seconds"""
        conn = self.pool.get_connection()
        try:
            cursor = conn.cursor()
            cutoff_time = time.time() - older_than_seconds
            cursor.execute("DELETE FROM cache WHERE created_at < ?", (cutoff_time,))
            deleted = cursor.rowcount
            conn.commit()
            return deleted
        finally:
            self.pool.return_connection(conn)
    
    def shutdown(self):
        """Gracefully shutdown cache system"""
        self._stop_writer = True
        self._writer_thread.join(timeout=5.0)
        self.pool.close_all()


# Convenience function for drop-in replacement
def create_cache(db_path: str = "./cache/evaluator.db", **kwargs) -> EnhancedEvaluatorCache:
    """Create an enhanced cache instance"""
    return EnhancedEvaluatorCache(db_path, **kwargs)


if __name__ == "__main__":
    # Test the enhanced cache
    cache = create_cache(db_path="./test_cache.db")
    
    print("=== Testing Enhanced Evaluator Cache ===\n")
    
    # Test single get/set
    print("1. Single get/set:")
    cache.set("key1", 0.95)
    print(f"   get('key1') = {cache.get('key1')}")
    
    # Test batch operations
    print("\n2. Batch operations:")
    items = {f"key_{i}": i * 0.1 for i in range(10)}
    cache.batch_set(items)
    result = cache.batch_get(list(items.keys()))
    print(f"   Set 10 items, retrieved {len(result)} items")
    
    # Test statistics
    print("\n3. Cache statistics:")
    stats = cache.get_stats()
    for k, v in stats.items():
        print(f"   {k}: {v}")
    
    print(f"\n   Disk size: {cache.get_disk_size()} bytes")
    
    # Test repeated access (memory cache benefit)
    print("\n4. Memory cache benefit (repeated access):")
    for _ in range(100):
        cache.get("key1")
    
    stats = cache.get_stats()
    print(f"   Hit rate after repeated access: {stats['hit_rate']:.2%}")
    
    # Cleanup
    cache.shutdown()
    Path("./test_cache.db").unlink(missing_ok=True)
    
    print("\nCache test complete!")
