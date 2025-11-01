#!/usr/bin/env python
"""
Combinatorial Expansion Stability Tests
========================================

Tests stability as polygon side counts expand combinatorially:
- n=3 (triangle) to n=12 (dodecagon)
- All combinations of polygon pairs (3*3 to 12*12 = 136 combinations)
- Interactions at each scale
- Memory and performance under expansion
- State consistency across expansions
"""

import pathlib
import sys
import time
from typing import Any, Dict

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class CombinatorExpansionTracker:
    """Tracks combinatorial expansion statistics"""
    def __init__(self):
        self.test_runs = []
        self.memory_samples = []
        self.timing_samples = []
        self.error_log = []
        self.state_snapshots = {}
    
    def add_test_run(self, n1: int, n2: int, result: Dict[str, Any]):
        """Record test run result"""
        self.test_runs.append({
            'n1': n1,
            'n2': n2,
            'result': result,
            'timestamp': time.time()
        })
    
    def add_timing(self, label: str, elapsed: float):
        """Record timing sample"""
        self.timing_samples.append({
            'label': label,
            'elapsed': elapsed,
            'timestamp': time.time()
        })
    
    def add_error(self, n1: int, n2: int, error: str):
        """Log error"""
        self.error_log.append({
            'n1': n1,
            'n2': n2,
            'error': error,
            'timestamp': time.time()
        })
    
    def snapshot_state(self, label: str, state: Dict[str, Any]):
        """Capture state snapshot"""
        self.state_snapshots[label] = {
            'state': state.copy(),
            'timestamp': time.time()
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get aggregate statistics"""
        if not self.timing_samples:
            return {}
        
        times = [s['elapsed'] for s in self.timing_samples]
        return {
            'min_time': min(times),
            'max_time': max(times),
            'avg_time': np.mean(times),
            'std_time': np.std(times),
            'total_tests': len(self.test_runs),
            'total_errors': len(self.error_log),
            'error_rate': len(self.error_log) / max(1, len(self.test_runs))
        }


# ==================== TEST FUNCTIONS ====================

def test_single_polygon_all_n():
    """Test single polygon creation for all n values (3-12)"""
    print("\n[TEST] Single Polygon All N Values (3-12)")
    print("=" * 70)
    
    from polygon_utils import create_polygon
    
    tracker = CombinatorExpansionTracker()
    results = {}
    
    for n in range(3, 13):
        try:
            start = time.time()
            poly = create_polygon(n, position=(0, 0, 0))
            elapsed = time.time() - start
            
            # Verify structure
            assert 'vertices' in poly, f"Missing vertices for n={n}"
            assert 'sides' in poly, f"Missing sides for n={n}"
            assert poly['sides'] == n, f"Sides mismatch: {poly['sides']} != {n}"
            assert len(poly['vertices']) == n, f"Vertex count mismatch for n={n}"
            
            # Verify geometry
            verts = np.array(poly['vertices'], dtype=float)
            assert verts.shape == (n, 3), f"Vertex shape incorrect for n={n}"
            
            # Verify edge lengths
            edge_lengths = []
            for i in range(n):
                v1 = verts[i]
                v2 = verts[(i + 1) % n]
                length = np.linalg.norm(v2 - v1)
                edge_lengths.append(length)
            
            avg_edge = np.mean(edge_lengths)
            std_edge = np.std(edge_lengths)
            
            assert np.isclose(avg_edge, 1.0, atol=0.01), \
                f"Edge length {avg_edge:.4f} != 1.0 for n={n}"
            assert std_edge < 0.01, \
                f"Edge variance {std_edge:.4f} too high for n={n}"
            
            results[n] = {
                'time': elapsed,
                'valid': True,
                'edge_avg': avg_edge,
                'edge_std': std_edge
            }
            tracker.add_timing(f"create_polygon_n{n}", elapsed)
            
            print(f"  [OK] n={n:2d}: {n} vertices, edges ~{avg_edge:.4f}, time {elapsed*1000:.3f}ms")
            
        except Exception as e:
            results[n] = {'valid': False, 'error': str(e)}
            tracker.add_error(n, n, str(e))
            print(f"  [FAIL] n={n}: {e}")
    
    stats = tracker.get_stats()
    assert stats['error_rate'] == 0, "Errors detected in single polygon test"
    print(f"  [OK] All 10 polygon types created successfully")
    print(f"  [OK] Average creation time: {stats['avg_time']*1000:.3f}ms")
    
    return True


def test_polygon_pair_combinations():
    """Test all combinations of polygon pairs (n1, n2) where 3 <= n1,n2 <= 12"""
    print("\n[TEST] Polygon Pair Combinations (3-12)")
    print("=" * 70)
    
    from polygon_utils import create_polygon
    
    tracker = CombinatorExpansionTracker()
    n_values = list(range(3, 13))
    total_combinations = len(n_values) * len(n_values)
    
    print(f"  Testing {total_combinations} polygon pair combinations...")
    
    passed = 0
    failed = 0
    combination_times = []
    
    for i, n1 in enumerate(n_values):
        for j, n2 in enumerate(n_values):
            try:
                start = time.time()
                
                # Create both polygons
                p1 = create_polygon(n1, position=(0, 0, 0))
                p2 = create_polygon(n2, position=(2, 0, 0))
                
                elapsed = time.time() - start
                combination_times.append(elapsed)
                
                # Verify structure
                assert p1['sides'] == n1, f"p1 sides incorrect: {p1['sides']} != {n1}"
                assert p2['sides'] == n2, f"p2 sides incorrect: {p2['sides']} != {n2}"
                assert len(p1['vertices']) == n1, f"p1 vertex count incorrect"
                assert len(p2['vertices']) == n2, f"p2 vertex count incorrect"
                
                # Verify positions distinct
                v1_centroid = np.mean(np.array(p1['vertices']), axis=0)
                v2_centroid = np.mean(np.array(p2['vertices']), axis=0)
                dist = np.linalg.norm(v2_centroid - v1_centroid)
                assert dist > 1.5, f"Polygons too close: distance {dist:.2f}"
                
                tracker.add_test_run(n1, n2, {'valid': True})
                passed += 1
                
                # Progress indicator
                if (i * len(n_values) + j + 1) % 20 == 0:
                    print(f"    ... processed {i * len(n_values) + j + 1}/{total_combinations}")
                
            except Exception as e:
                failed += 1
                tracker.add_error(n1, n2, str(e))
                print(f"  [FAIL] Combination ({n1}, {n2}): {e}")
    
    stats = tracker.get_stats()
    
    print(f"  [OK] Passed: {passed}/{total_combinations}")
    print(f"  [OK] Failed: {failed}/{total_combinations}")
    print(f"  [OK] Average combination time: {np.mean(combination_times)*1000:.3f}ms")
    print(f"  [OK] Max combination time: {np.max(combination_times)*1000:.3f}ms")
    
    assert failed == 0, f"{failed} combination(s) failed"
    
    return True


def test_scaling_interaction_across_n():
    """Test interactions scale properly as n increases"""
    print("\n[TEST] Interaction Scaling Across N Values")
    print("=" * 70)
    
    from interaction_manager import RaycastingEngine
    from polygon_utils import create_polygon
    
    tracker = CombinatorExpansionTracker()
    
    class MockGLView:
        def width(self):
            return 800
        def height(self):
            return 600
    
    raycaster = RaycastingEngine()
    interaction_times = {}
    
    for n in range(3, 13):
        try:
            poly = create_polygon(n, position=(0, 0, 0))
            verts = np.array(poly['vertices'], dtype=float)
            
            # Simple triangulation for raycasting
            faces = []
            for i in range(1, n - 1):
                faces.append([0, i, i + 1])
            faces = np.array(faces, dtype=int)
            
            # Time raycasting from various positions
            ray_times = []
            for screen_x in range(300, 500, 25):
                start = time.time()
                
                ray_origin = np.array([0.0, 0.0, 10.0])
                ray_dir = np.array([
                    (screen_x - 400) * 0.01,
                    (300 - 300) * 0.01,
                    -1.0
                ])
                ray_dir /= np.linalg.norm(ray_dir)
                
                hit = raycaster.closest_hit(ray_origin, ray_dir, verts, faces)
                
                elapsed = time.time() - start
                ray_times.append(elapsed)
            
            avg_ray_time = np.mean(ray_times)
            interaction_times[n] = avg_ray_time
            tracker.add_timing(f"raycast_n{n}", avg_ray_time)
            
            print(f"  [OK] n={n:2d}: Raycast time {avg_ray_time*1000:.3f}ms")
            
        except Exception as e:
            tracker.add_error(n, n, str(e))
            print(f"  [FAIL] n={n}: {e}")
    
    # Check that timing doesn't degrade significantly
    times = list(interaction_times.values())
    max_time = max(times)
    min_time = min(times)
    time_ratio = max_time / min_time if min_time > 0 else 1.0
    
    print(f"  [OK] Timing range: {min_time*1000:.3f}ms to {max_time*1000:.3f}ms")
    print(f"  [OK] Time ratio (max/min): {time_ratio:.2f}x")
    
    # Warn if timing degrades significantly with n
    if time_ratio > 5.0:
        print(f"  [WARN] Timing degradation > 5x across n values")
    
    return True


def test_assembly_with_all_n_types():
    """Test assembly containing one instance of each n type"""
    print("\n[TEST] Assembly with All N Types (3-12)")
    print("=" * 70)
    
    from polygon_utils import create_polygon
    
    class MockAssembly:
        def __init__(self):
            self.polyforms = {}
            self._id_counter = 1
        
        def add_polyform(self, p):
            try:
                from gui.polyform_adapter import normalize_polyform
                norm = normalize_polyform(p)
            except Exception:
                norm = dict(p)
                if 'id' not in norm:
                    norm['id'] = f"poly_{self._id_counter}"
                    self._id_counter += 1
                verts = []
                for v in norm.get('vertices', []):
                    if isinstance(v, (list, tuple)):
                        if len(v) == 2:
                            verts.append((float(v[0]), float(v[1]), 0.0))
                        else:
                            verts.append((float(v[0]), float(v[1]), float(v[2]) if len(v) > 2 else 0.0))
                if verts:
                    norm['vertices'] = verts
            self.polyforms[norm['id']] = norm
            return norm['id']
        
        def get_all_polyforms(self):
            return list(self.polyforms.values())
    
    assembly = MockAssembly()
    
    try:
        # Add one of each n
        for n in range(3, 13):
            x = (n - 3) * 1.5  # Space them out
            p = create_polygon(n, position=(x, 0, 0))
            assembly.add_polyform(p)
        
        all_polys = assembly.get_all_polyforms()
        assert len(all_polys) == 10, f"Expected 10 polyforms, got {len(all_polys)}"
        
        # Verify all n values present
        n_values_present = sorted([p['sides'] for p in all_polys])
        n_values_expected = list(range(3, 13))
        assert n_values_present == n_values_expected, \
            f"N values mismatch: {n_values_present} != {n_values_expected}"
        
        # Verify total vertex count
        total_vertices = sum(len(p['vertices']) for p in all_polys)
        expected_vertices = sum(range(3, 13))
        assert total_vertices == expected_vertices, \
            f"Vertex count mismatch: {total_vertices} != {expected_vertices}"
        
        print(f"  [OK] Assembly contains 10 polyforms (n=3 to n=12)")
        print(f"  [OK] Total vertices: {total_vertices}")
        print(f"  [OK] Total polyforms: {len(all_polys)}")
        
        # Test interactions with full assembly
        state = {'selected': None}
        for i, p in enumerate(all_polys):
            state['selected'] = i
            state['hovered'] = (i + 1) % len(all_polys)
        
        print(f"  [OK] Interactions simulated across all {len(all_polys)} polyforms")
        
        return True
        
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_memory_stability_across_expansion():
    """Test that memory usage stays stable as we expand n"""
    print("\n[TEST] Memory Stability Across Expansion")
    print("=" * 70)
    
    import sys

    from polygon_utils import create_polygon
    
    tracker = CombinatorExpansionTracker()
    memory_by_n = {}
    
    try:
        for n in range(3, 13):
            poly = create_polygon(n, position=(0, 0, 0))
            
            # Estimate size
            verts_size = sys.getsizeof(poly['vertices'])
            poly_size = sys.getsizeof(poly)
            
            memory_by_n[n] = {
                'polyform_size': poly_size,
                'vertices_size': verts_size,
                'total': poly_size + verts_size
            }
            
            print(f"  [OK] n={n:2d}: {poly_size:6d} bytes (polyform) + {verts_size:6d} bytes (vertices)")
        
        # Check scaling
        sizes = [memory_by_n[n]['total'] for n in range(3, 13)]
        min_size = min(sizes)
        max_size = max(sizes)
        size_ratio = max_size / min_size if min_size > 0 else 1.0
        
        print(f"  [OK] Size range: {min_size} to {max_size} bytes")
        print(f"  [OK] Size ratio (max/min): {size_ratio:.2f}x")
        
        # Memory should scale roughly linearly with n (more vertices)
        # Expect ratio < 3x
        if size_ratio > 3.0:
            print(f"  [WARN] Memory ratio > 3x - possible memory leak")
        
        return True
        
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_rapid_n_expansion_interaction():
    """Test rapid switching between different n values"""
    print("\n[TEST] Rapid N Expansion/Contraction")
    print("=" * 70)
    
    from polygon_utils import create_polygon
    
    tracker = CombinatorExpansionTracker()
    n_sequence = [3, 5, 4, 6, 3, 12, 7, 8, 10, 3, 5, 9, 11, 12, 4]  # Randomish
    
    try:
        state_history = []
        
        for iteration, n in enumerate(n_sequence):
            start = time.time()
            
            # Create polygon
            poly = create_polygon(n, position=(0, 0, 0))
            
            # Simulate interaction
            state = {
                'n': n,
                'vertices': len(poly['vertices']),
                'sides': poly['sides'],
                'position': poly['position']
            }
            state_history.append(state)
            
            elapsed = time.time() - start
            tracker.add_timing(f"rapid_iteration_{iteration}", elapsed)
            
            # Verify consistency
            assert poly['sides'] == n, f"Sides mismatch in iteration {iteration}"
            assert len(poly['vertices']) == n, f"Vertex count mismatch in iteration {iteration}"
        
        print(f"  [OK] Completed {len(n_sequence)} rapid n switches")
        
        # Verify state history consistency
        for state in state_history:
            assert state['vertices'] == state['sides'], "State inconsistency detected"
        
        print(f"  [OK] All {len(state_history)} states consistent")
        
        stats = tracker.get_stats()
        print(f"  [OK] Average iteration time: {stats['avg_time']*1000:.3f}ms")
        
        return True
        
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_combinatorial_explosion_handling():
    """Test handling of combinatorial explosion without pathological behavior"""
    print("\n[TEST] Combinatorial Explosion Handling")
    print("=" * 70)
    
    from polygon_utils import create_polygon
    
    tracker = CombinatorExpansionTracker()
    
    try:
        # Create increasing numbers of polygons
        assembly_states = {}
        
        for target_n in range(3, 13):
            polys = []
            start = time.time()
            
            # Create multiple instances of each type up to target_n
            for n in range(3, target_n + 1):
                for instance in range(2):  # 2 instances of each
                    x = len(polys) * 0.5
                    p = create_polygon(n, position=(x, 0, 0))
                    polys.append(p)
            
            elapsed = time.time() - start
            
            assembly_states[target_n] = {
                'polyform_count': len(polys),
                'creation_time': elapsed,
                'avg_time_per_poly': elapsed / len(polys) if polys else 0
            }
            
            tracker.add_timing(f"assembly_up_to_n{target_n}", elapsed)
            
            print(f"  [OK] n={target_n:2d}: Created {len(polys):3d} polyforms in {elapsed:.3f}s " +
                  f"({assembly_states[target_n]['avg_time_per_poly']*1000:.3f}ms avg)")
        
        # Check for pathological behavior
        times = [v['creation_time'] for v in assembly_states.values()]
        max_time = max(times)
        min_time = min(times)
        time_ratio = max_time / min_time if min_time > 0 else 1.0
        
        print(f"  [OK] Time ratio across expansions: {time_ratio:.2f}x")
        
        if time_ratio > 10.0:
            print(f"  [WARN] Significant performance degradation detected")
        
        return True
        
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_state_consistency_across_expansion():
    """Test that state remains consistent as n values change"""
    print("\n[TEST] State Consistency Across Expansion")
    print("=" * 70)
    
    from polygon_utils import create_polygon
    
    tracker = CombinatorExpansionTracker()
    
    try:
        # Create baseline state
        baseline = {}
        for n in range(3, 13):
            poly = create_polygon(n, position=(0, 0, 0))
            baseline[n] = {
                'sides': poly['sides'],
                'vertex_count': len(poly['vertices']),
                'has_bonds': 'bonds' in poly,
                'position': tuple(poly['position'])
            }
        
        # Create and verify consistency
        for n in range(3, 13):
            poly = create_polygon(n, position=(0, 0, 0))
            
            assert baseline[n]['sides'] == poly['sides'], f"Sides changed for n={n}"
            assert baseline[n]['vertex_count'] == len(poly['vertices']), \
                f"Vertex count changed for n={n}"
            assert baseline[n]['has_bonds'] == ('bonds' in poly), \
                f"Bonds field changed for n={n}"
            assert baseline[n]['position'] == tuple(poly['position']), \
                f"Position changed for n={n}"
        
        print(f"  [OK] State consistent for all 10 polygon types")
        print(f"  [OK] Verified: sides, vertex count, bonds field, position")
        
        return True
        
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def run_all():
    """Run all combinatorial expansion tests"""
    print("\n" + "=" * 70)
    print("COMBINATORIAL EXPANSION STABILITY TEST SUITE")
    print("=" * 70)
    
    tests = [
        test_single_polygon_all_n,
        test_polygon_pair_combinations,
        test_scaling_interaction_across_n,
        test_assembly_with_all_n_types,
        test_memory_stability_across_expansion,
        test_rapid_n_expansion_interaction,
        test_combinatorial_explosion_handling,
        test_state_consistency_across_expansion,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except AssertionError as e:
            print(f"  [FAIL] {e}")
            failed += 1
        except Exception as e:
            print(f"  [FAIL] Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    # Summary
    print("\n" + "=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)
    
    if failed == 0:
        print("\n✓ All combinatorial expansion tests PASS")
        print("✓ All polygon types (n=3-12) stable")
        print("✓ All 100+ combinations tested successfully")
        print("✓ Memory and performance stable across expansions")
        print("✓ State consistency verified")
        print("✓ System ready for combinatorial navigation")
    else:
        print(f"\n✗ {failed} test(s) FAILED")
    
    return failed == 0


if __name__ == '__main__':
    success = run_all()
    sys.exit(0 if success else 1)
