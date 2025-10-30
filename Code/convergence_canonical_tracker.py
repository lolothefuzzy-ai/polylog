"""
Canonical N Convergence Tracker

Tracks convergence of CANONICAL N (polyform count estimator) not population size.

N = T × n! / ∏c_j! × ∏a_j^{c_j} × symmetry_factor

Where:
  T = transformation parameter
  n = total polygon count (sum of c_j)
  a_j = sides of polygon type j
  c_j = count of polygon type j
  symmetry_factor = geometric indistinguishability reduction
"""

import numpy as np
from typing import Dict, List, Optional
from collections import defaultdict
from dataclasses import dataclass
import math
from canonical_estimator import canonical_estimate


@dataclass
class CanonicalConvergencePoint:
    """Single point in canonical N convergence."""
    generation: int
    T: float
    types: List[tuple]  # List of (a_j, c_j)
    symmetry_factor: float
    logN: float
    N: Optional[float]
    diversity_index: float
    s_eff_geo: float
    s_eff_arith: float
    timestamp: float


class CanonicalNTracker:
    """Track convergence of canonical N across assembly evolution."""
    
    def __init__(self, max_history: int = 500):
        self.history: List[CanonicalConvergencePoint] = []
        self.max_history = max_history
        self.generation = 0
    
    def record_assembly(self, T: float, types: List[tuple], 
                       symmetry_factor: float = 1.0, 
                       symmetry_notes: str = "") -> CanonicalConvergencePoint:
        """
        Record canonical N for current assembly.
        
        Args:
            T: Transformation parameter
            types: List of (a_j, c_j) pairs - (sides, count)
            symmetry_factor: Geometric indistinguishability (0-1]
            symmetry_notes: Description of symmetry
        """
        import time
        
        try:
            result = canonical_estimate(T, types, symmetry_factor, symmetry_notes)
        except Exception as e:
            print(f"  ⚠️  Canonical estimate failed: {e}")
            return None
        
        point = CanonicalConvergencePoint(
            generation=self.generation,
            T=T,
            types=types,
            symmetry_factor=symmetry_factor,
            logN=result['logN'],
            N=result['N'],
            diversity_index=result['diversity_index'],
            s_eff_geo=result['s_eff_geo'],
            s_eff_arith=result['s_eff_arith'],
            timestamp=time.time()
        )
        
        if len(self.history) >= self.max_history:
            self.history.pop(0)
        
        self.history.append(point)
        self.generation += 1
        return point
    
    def get_history(self) -> List[CanonicalConvergencePoint]:
        """Get all recorded points."""
        return self.history.copy()
    
    def print_convergence_summary(self) -> str:
        """Print text summary of N convergence."""
        if not self.history:
            return "No data recorded yet"
        
        lines = []
        lines.append("\n" + "="*80)
        lines.append("CANONICAL N CONVERGENCE SUMMARY")
        lines.append("="*80)
        
        first = self.history[0]
        last = self.history[-1]
        
        lines.append(f"\nTotal Generations: {len(self.history)}")
        lines.append(f"\nInitial State (Gen {first.generation}):")
        lines.append(f"  Types: {first.types}")
        lines.append(f"  T: {first.T:.6f}")
        lines.append(f"  logN: {first.logN:.4f}")
        if first.N:
            lines.append(f"  N: {first.N:.2e}")
        lines.append(f"  Diversity: {first.diversity_index:.4f}")
        lines.append(f"  s_eff (geometric): {first.s_eff_geo:.4f}")
        
        lines.append(f"\nFinal State (Gen {last.generation}):")
        lines.append(f"  Types: {last.types}")
        lines.append(f"  T: {last.T:.6f}")
        lines.append(f"  logN: {last.logN:.4f}")
        if last.N:
            lines.append(f"  N: {last.N:.2e}")
        lines.append(f"  Diversity: {last.diversity_index:.4f}")
        lines.append(f"  s_eff (geometric): {last.s_eff_geo:.4f}")
        
        # Compute change
        logN_change = last.logN - first.logN
        lines.append(f"\nChange in logN: {logN_change:+.4f}")
        
        if last.N and first.N:
            N_ratio = last.N / first.N
            lines.append(f"N ratio (final/initial): {N_ratio:.4f}x")
        
        lines.append(f"Diversity change: {last.diversity_index - first.diversity_index:+.4f}")
        
        return '\n'.join(lines)
    
    def print_ascii_graph(self) -> str:
        """Print ASCII graph of logN over generations."""
        if not self.history:
            return "No data"
        
        lines = []
        lines.append("\n" + "="*80)
        lines.append("logN CONVERGENCE OVER GENERATIONS")
        lines.append("="*80)
        
        # Extract logN values
        logNs = [p.logN for p in self.history]
        generations = [p.generation for p in self.history]
        
        min_logN = min(logNs)
        max_logN = max(logNs)
        
        height = 20
        width = 80
        
        # Create grid
        grid = [[' ' for _ in range(width)] for _ in range(height)]
        
        # Plot points
        for gen, logN in zip(generations, logNs):
            x = int((gen / max(generations)) * (width - 1)) if generations else 0
            y = int((1 - (logN - min_logN) / max(max_logN - min_logN, 0.001)) * (height - 1))
            
            if 0 <= x < width and 0 <= y < height:
                grid[y][x] = '█'
        
        # Print grid
        for row in grid:
            lines.append('│' + ''.join(row) + '│')
        
        lines.append("└" + "─"*width + "┘")
        lines.append(f"X: Generation (0-{max(generations) if generations else 0})")
        lines.append(f"Y: logN ({min_logN:.2f}-{max_logN:.2f})")
        
        return '\n'.join(lines)
    
    def compare_diversity_vs_N(self) -> str:
        """Compare diversity index against logN."""
        if len(self.history) < 2:
            return "Need at least 2 points"
        
        lines = []
        lines.append("\n" + "="*80)
        lines.append("DIVERSITY vs logN ANALYSIS")
        lines.append("="*80)
        
        diversity_vals = [p.diversity_index for p in self.history]
        logN_vals = [p.logN for p in self.history]
        
        # Compute correlation
        correlation = np.corrcoef(diversity_vals, logN_vals)[0, 1]
        
        lines.append(f"\nCorrelation (diversity vs logN): {correlation:.4f}")
        lines.append("  +1.0 = strong positive correlation (more diverse → higher N)")
        lines.append("   0.0 = no correlation")
        lines.append("  -1.0 = negative correlation (more diverse → lower N)")
        
        lines.append("\nInterpretation:")
        if correlation > 0.7:
            lines.append("  ✓ High positive: Assembly diversity drives N increase")
        elif correlation > 0.3:
            lines.append("  ✓ Moderate positive: Some diversity-N relationship")
        elif correlation > -0.3:
            lines.append("  ~ Weak/no correlation: N driven by other factors (T, symmetry)")
        else:
            lines.append("  ⚠️  Negative: Higher diversity suppresses N (symmetry reducing)")
        
        return '\n'.join(lines)


def demo_canonical_tracking():
    """Demo showing canonical N convergence tracking."""
    
    tracker = CanonicalNTracker()
    
    print("\n" + "="*80)
    print("  📊 CANONICAL N CONVERGENCE TRACKING DEMO")
    print("="*80)
    
    # Simulate assembly evolution
    generations_data = [
        {
            'T': 1.0,
            'types': [(4, 1)],  # 1 square
            'symmetry': 1.0,
            'name': 'Start: Single square'
        },
        {
            'T': 1.0,
            'types': [(4, 2)],  # 2 squares
            'symmetry': 1.0,
            'name': 'Gen 10: Added another square'
        },
        {
            'T': 1.1,
            'types': [(4, 2), (3, 1)],  # 2 squares + 1 triangle
            'symmetry': 0.95,
            'name': 'Gen 20: Added triangle, T increased'
        },
        {
            'T': 1.2,
            'types': [(3, 1), (4, 3), (5, 1)],  # Mixed assembly
            'symmetry': 0.9,
            'name': 'Gen 30: Complex mixed assembly'
        },
        {
            'T': 1.25,
            'types': [(3, 2), (4, 2), (5, 2), (6, 1)],  # Very diverse
            'symmetry': 0.85,
            'name': 'Gen 40: Highly diverse assembly'
        },
        {
            'T': 1.3,
            'types': [(3, 3), (4, 3), (5, 2), (6, 2)],  # Even more
            'symmetry': 0.8,
            'name': 'Gen 50: Maximum diversity reached'
        },
    ]
    
    print("\nSimulating assembly evolution...")
    print()
    
    for gen_data in generations_data:
        point = tracker.record_assembly(
            gen_data['T'],
            gen_data['types'],
            gen_data['symmetry'],
            gen_data['name']
        )
        
        if point:
            print(f"✓ {gen_data['name']}")
            print(f"    logN: {point.logN:.4f}", end="")
            if point.N:
                print(f" → N ≈ {point.N:.2e}", end="")
            print(f" | Diversity: {point.diversity_index:.4f}")
    
    # Print results
    print(tracker.print_convergence_summary())
    print(tracker.print_ascii_graph())
    print(tracker.compare_diversity_vs_N())
    
    print("\n" + "="*80)
    print("KEY INSIGHTS:")
    print("="*80)
    print("""
✓ logN tracks the TOTAL POLYFORM COUNT ESTIMATOR
  - Combines transformation (T), diversity, and symmetry
  - Higher logN = more valid polyforms in the assembly

✓ Diversity Index measures polygon type variety
  - 0 = all same type (boring)
  - Higher = more mix of different polygon types

✓ T parameter represents transformation/orientation effects
  - Increases as assembly complexity grows

✓ s_eff_geo (effective side count) is geometric mean
  - Summarizes all polygon types into single value
  - Used for compact N calculation

Use these to:
  1. Track polyform validity over evolution
  2. Detect when assembly becomes "degenerate" (logN drops)
  3. Optimize for diversity while maintaining convergence
    """)


if __name__ == "__main__":
    demo_canonical_tracking()
