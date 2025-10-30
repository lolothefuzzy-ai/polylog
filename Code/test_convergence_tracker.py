"""
Test script for ConvergenceTracker with simulated assembly growth.

Demonstrates:
- T estimation with contextual updates
- Convergence tracking with confidence intervals
- N bounds estimation using the expanded form
- Visualization of convergence quality
"""
import numpy as np
from canonical_estimator import canonical_estimate
from convergence_tracker import ConvergenceTracker


def simulate_assembly_growth():
    """Simulate assembly growth with varying compositions."""
    tracker = ConvergenceTracker(window_size=20)
    
    print("=" * 70)
    print("Simulating Assembly Growth with T Estimation & Convergence Tracking")
    print("=" * 70)
    print()
    
    # Simulate adding polyforms over time
    compositions = [
        # (types, description)
        ([{'a': 3, 'c': 1}], "Single triangle"),
        ([{'a': 3, 'c': 2}], "Two triangles"),
        ([{'a': 3, 'c': 2}, {'a': 4, 'c': 1}], "2 triangles + 1 square"),
        ([{'a': 3, 'c': 3}, {'a': 4, 'c': 1}], "3 triangles + 1 square"),
        ([{'a': 3, 'c': 3}, {'a': 4, 'c': 2}], "3 triangles + 2 squares"),
        ([{'a': 3, 'c': 4}, {'a': 4, 'c': 2}], "4 triangles + 2 squares"),
        ([{'a': 3, 'c': 5}, {'a': 4, 'c': 2}], "5 triangles + 2 squares"),
        ([{'a': 3, 'c': 5}, {'a': 4, 'c': 3}], "5 triangles + 3 squares"),
        ([{'a': 3, 'c': 6}, {'a': 4, 'c': 3}], "6 triangles + 3 squares"),
        ([{'a': 3, 'c': 6}, {'a': 4, 'c': 4}], "6 triangles + 4 squares"),
    ]
    
    for i, (types, desc) in enumerate(compositions):
        # Derive T from context (simulating _derive_T_from_context)
        n = sum(t['c'] for t in types)
        # Simulate bond density growth
        bond_density = min(0.3 + i * 0.05, 0.8)
        T = (1.0 + 0.5 * np.log1p(n)) * (1.0 + bond_density)
        
        # Compute estimate
        est = canonical_estimate(T=T, types=types, symmetry_factor=1.0)
        
        # Track convergence
        tracker.add_sample(est, T)
        
        # Get statistics
        stats = tracker.get_current_statistics()
        
        print(f"\nStep {i+1}: {desc}")
        print(f"  n={n}, T={T:.3f}, logN={est['logN']:.3f}")
        
        if stats['sample_count'] >= 3:
            print(f"  T bounds (95% CI): [{stats['T_bounds'][0]:.3f}, {stats['T_bounds'][1]:.3f}]")
            print(f"  logN bounds: [{stats['logN_bounds'][0]:.3f}, {stats['logN_bounds'][1]:.3f}]")
            print(f"  Convergence: {stats['convergence_score']:.1%} ({'✓ CONVERGED' if stats['converged'] else '⋯ converging'})")
            
            # Estimate N bounds
            n_bounds = tracker.estimate_N_bounds(est)
            if 'N_lower' in n_bounds and 'N_upper' in n_bounds:
                print(f"  N bounds: [{n_bounds['N_lower']:.2e}, {n_bounds['N_upper']:.2e}]")
    
    print("\n" + "=" * 70)
    print("Final Convergence Report")
    print("=" * 70)
    print(tracker.get_convergence_report())
    
    # Test smoothed history
    print("\n" + "=" * 70)
    print("Smoothed History (last 5 points)")
    print("=" * 70)
    indices, smoothed, bands = tracker.get_smoothed_history(smoothing_window=3)
    if len(indices) > 0:
        for i in range(max(0, len(indices) - 5), len(indices)):
            print(f"  Point {i}: logN={smoothed[i]:.3f}, CI=[{bands[0][i]:.3f}, {bands[1][i]:.3f}]")


def test_convergence_detection():
    """Test convergence detection with stable vs unstable sequences."""
    print("\n" + "=" * 70)
    print("Testing Convergence Detection")
    print("=" * 70)
    
    # Stable sequence (should converge)
    print("\n--- Stable sequence (should converge) ---")
    tracker_stable = ConvergenceTracker(window_size=15)
    
    base_types = [{'a': 4, 'c': 5}]
    base_T = 2.5
    
    for i in range(20):
        # Add small noise
        T = base_T + np.random.normal(0, 0.01)
        est = canonical_estimate(T=T, types=base_types)
        tracker_stable.add_sample(est, T)
    
    stats = tracker_stable.get_current_statistics()
    print(f"  Samples: {stats['sample_count']}")
    print(f"  Mean T: {stats['mean_T']:.4f} ± {stats['std_T']:.4f}")
    print(f"  Convergence score: {stats['convergence_score']:.1%}")
    print(f"  Status: {'✓ CONVERGED' if stats['converged'] else '✗ NOT CONVERGED'}")
    
    # Unstable sequence (should not converge)
    print("\n--- Unstable sequence (should NOT converge) ---")
    tracker_unstable = ConvergenceTracker(window_size=15)
    
    for i in range(20):
        # Large variations
        T = base_T + np.random.normal(0, 0.5)
        types = [{'a': 4, 'c': 3 + i % 3}]  # Varying composition
        est = canonical_estimate(T=T, types=types)
        tracker_unstable.add_sample(est, T)
    
    stats = tracker_unstable.get_current_statistics()
    print(f"  Samples: {stats['sample_count']}")
    print(f"  Mean T: {stats['mean_T']:.4f} ± {stats['std_T']:.4f}")
    print(f"  Convergence score: {stats['convergence_score']:.1%}")
    print(f"  Status: {'✓ CONVERGED' if stats['converged'] else '✗ NOT CONVERGED'}")


if __name__ == '__main__':
    simulate_assembly_growth()
    test_convergence_detection()
    
    print("\n" + "=" * 70)
    print("✓ All tests completed")
    print("=" * 70)
