"""
Canonical N Integration Layer

Bridges canonical polyform count estimation with assembly evolution tracking.
Integrates with:
- Assembly state (polyforms, bonds)
- Evolutionary algorithm progress
- Convergence monitoring
- Performance metrics
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from convergence_canonical_tracker import CanonicalConvergencePoint, CanonicalNTracker


@dataclass
class AssemblySnapshot:
    """Snapshot of assembly at a generation."""
    generation: int
    polyform_count: int
    bond_count: int
    types: List[Tuple[int, int]]  # (sides, count)
    T: float
    symmetry_factor: float
    timestamp: float


class CanonicalIntegrator:
    """
    Integrate canonical N tracking into assembly evolution.
    
    Handles:
    - Extracting assembly composition from polyforms
    - Computing T parameter from geometry
    - Detecting symmetry
    - Tracking convergence
    """
    
    def __init__(self, enable_tracking: bool = True):
        self.enabled = enable_tracking
        self.tracker = CanonicalNTracker() if enable_tracking else None
        self.snapshots: List[AssemblySnapshot] = []
        self.generation = 0
    
    def extract_assembly_types(self, polyforms: List[Dict]) -> List[Tuple[int, int]]:
        """
        Extract (sides, count) pairs from polyform list.
        
        Args:
            polyforms: List of polyform dicts with 'sides' field
            
        Returns:
            List of (a_j, c_j) tuples sorted by sides
        """
        if not polyforms:
            return []
        
        # Count polygons by sides
        type_counts: Dict[int, int] = {}
        for poly in polyforms:
            sides = poly.get('sides') or len(poly.get('vertices', []))
            type_counts[sides] = type_counts.get(sides, 0) + 1
        
        # Convert to sorted list of tuples
        types = sorted([(sides, count) for sides, count in type_counts.items()])
        return types
    
    def compute_T_parameter(self, polyforms: List[Dict], bonds: List[Dict]) -> float:
        """
        Compute T (transformation parameter) from assembly geometry.
        
        T encodes orientation/transformation degrees of freedom.
        Increases with assembly complexity and connectivity.
        
        Args:
            polyforms: List of polyforms
            bonds: List of bonds
            
        Returns:
            T value (typically 1.0 to 2.0)
        """
        if not polyforms:
            return 1.0
        
        # Base T from number of polyforms
        n_polys = len(polyforms)
        base_T = 1.0 + (n_polys - 1) * 0.05  # ~0.05 per polygon
        
        # Connectivity bonus
        connectivity = len(bonds) / max(n_polys, 1)
        if connectivity > 1.5:
            base_T *= 1.2  # Well-connected
        elif connectivity > 0.5:
            base_T *= 1.1  # Moderately connected
        
        # Cap at reasonable range
        return max(1.0, min(2.0, base_T))
    
    def detect_symmetry_factor(self, polyforms: List[Dict], bonds: List[Dict]) -> float:
        """
        Detect geometric symmetry and return reduction factor.
        
        symmetry_factor ≤ 1 accounts for geometric indistinguishability.
        
        Args:
            polyforms: List of polyforms
            bonds: List of bonds
            
        Returns:
            symmetry_factor (0-1, where 1 = no symmetry)
        """
        if not polyforms or len(polyforms) < 2:
            return 1.0
        
        # Get positions
        positions = []
        for poly in polyforms:
            vertices = np.array(poly.get('vertices', []), dtype=float)
            if len(vertices) > 0:
                centroid = np.mean(vertices, axis=0)
                positions.append(centroid[:2])  # XY only
        
        if len(positions) < 2:
            return 1.0
        
        positions = np.array(positions)
        
        # Check for reflection symmetry (mirror across center)
        center = np.mean(positions, axis=0)
        
        # Compute reflection distance
        reflected = 2 * center - positions
        distances_to_reflected = []
        for pos in positions:
            min_dist = min(np.linalg.norm(pos - ref) for ref in reflected)
            distances_to_reflected.append(min_dist)
        
        avg_reflection_error = np.mean(distances_to_reflected)
        
        # Check for rotational symmetry
        radii = [np.linalg.norm(pos - center) for pos in positions]
        radius_std = np.std(radii) / (np.mean(radii) + 1e-6)
        
        # Assign symmetry factor
        if avg_reflection_error < 0.5 and radius_std < 0.3:
            # Strong mirror + circular symmetry
            return 0.25  # 4-fold effective
        elif avg_reflection_error < 1.0 or radius_std < 0.5:
            # Some symmetry
            return 0.5  # 2-fold
        elif avg_reflection_error < 2.0:
            # Weak symmetry
            return 0.8  # Slight reduction
        else:
            # No detectable symmetry
            return 1.0
    
    def record_assembly_state(self, polyforms: List[Dict], bonds: List[Dict],
                             generation: Optional[int] = None) -> Optional[CanonicalConvergencePoint]:
        """
        Record assembly state and compute canonical N.
        
        Args:
            polyforms: Current polyforms
            bonds: Current bonds
            generation: Generation number (auto-increment if None)
            
        Returns:
            CanonicalConvergencePoint or None if tracking disabled
        """
        if not self.enabled or self.tracker is None:
            return None
        
        if generation is None:
            generation = self.generation
            self.generation += 1
        
        # Extract assembly properties
        types = self.extract_assembly_types(polyforms)
        T = self.compute_T_parameter(polyforms, bonds)
        symmetry = self.detect_symmetry_factor(polyforms, bonds)
        
        # Record in tracker
        point = self.tracker.record_assembly(
            T=T,
            types=types,
            symmetry_factor=symmetry,
            symmetry_notes=f"Gen {generation}: {len(polyforms)} polyforms, {len(bonds)} bonds"
        )
        
        # Also store snapshot
        import time
        snapshot = AssemblySnapshot(
            generation=generation,
            polyform_count=len(polyforms),
            bond_count=len(bonds),
            types=types,
            T=T,
            symmetry_factor=symmetry,
            timestamp=time.time()
        )
        self.snapshots.append(snapshot)
        
        return point
    
    def get_convergence_report(self) -> str:
        """Get comprehensive convergence report."""
        if not self.enabled or self.tracker is None:
            return "Tracking disabled"
        
        lines = []
        lines.append("\n" + "="*80)
        lines.append("CANONICAL N CONVERGENCE REPORT")
        lines.append("="*80)
        
        # Summary
        history = self.tracker.get_history()
        if not history:
            lines.append("No data recorded")
            return '\n'.join(lines)
        
        first = history[0]
        last = history[-1]
        
        lines.append(f"\nGenerations tracked: {len(history)}")
        lines.append(f"\nInitial Assembly:")
        lines.append(f"  Composition: {first.types}")
        lines.append(f"  logN: {first.logN:.4f}")
        lines.append(f"  N: {first.N:.2e}")
        lines.append(f"  T: {first.T:.4f}")
        lines.append(f"  Diversity: {first.diversity_index:.4f}")
        
        lines.append(f"\nFinal Assembly:")
        lines.append(f"  Composition: {last.types}")
        lines.append(f"  logN: {last.logN:.4f}")
        lines.append(f"  N: {last.N:.2e}")
        lines.append(f"  T: {last.T:.4f}")
        lines.append(f"  Diversity: {last.diversity_index:.4f}")
        
        # Growth analysis
        logN_growth = last.logN - first.logN
        if first.N and last.N:
            N_multiplier = last.N / first.N
            lines.append(f"\nGrowth Analysis:")
            lines.append(f"  logN change: {logN_growth:+.4f}")
            lines.append(f"  N multiplier: {N_multiplier:.2e}x")
        
        # Convergence detection
        recent = history[-5:] if len(history) >= 5 else history
        recent_logN = [p.logN for p in recent]
        is_plateau = all(recent_logN[i] <= recent_logN[i+1] + 0.1 for i in range(len(recent_logN)-1))
        
        lines.append(f"\nConvergence Status:")
        if is_plateau and len(history) > 10:
            lines.append(f"  ✓ CONVERGED (logN plateau detected)")
        elif logN_growth > 1.0:
            lines.append(f"  ✓ IMPROVING (active growth)")
        else:
            lines.append(f"  ~ STABLE (steady state)")
        
        return '\n'.join(lines)
    
    def get_metrics_dict(self) -> Dict[str, Any]:
        """Export metrics as dictionary."""
        if not self.enabled or self.tracker is None:
            return {}
        
        history = self.tracker.get_history()
        if not history:
            return {}
        
        first = history[0]
        last = history[-1]
        
        return {
            'total_generations': len(history),
            'initial_logN': first.logN,
            'final_logN': last.logN,
            'logN_growth': last.logN - first.logN,
            'initial_N': first.N,
            'final_N': last.N,
            'initial_diversity': first.diversity_index,
            'final_diversity': last.diversity_index,
            'initial_T': first.T,
            'final_T': last.T,
            'initial_types': first.types,
            'final_types': last.types,
        }


class AssemblyObserver:
    """
    Observe assembly evolution and feed into canonical tracker.
    
    Used as callback/observer in main evolutionary loop.
    """
    
    def __init__(self, integrator: CanonicalIntegrator):
        self.integrator = integrator
        self.observation_count = 0
    
    def on_generation_complete(self, assembly: Any, generation: int):
        """
        Called after each GA generation.
        
        Args:
            assembly: Assembly object with get_all_polyforms() and get_bonds()
            generation: Generation number
        """
        try:
            polyforms = assembly.get_all_polyforms()
            bonds = assembly.get_bonds()
            
            point = self.integrator.record_assembly_state(
                polyforms, bonds, generation
            )
            
            self.observation_count += 1
            
            if self.observation_count % 10 == 0:
                # Print status every 10 generations
                if point:
                    print(f"  [Gen {generation}] logN: {point.logN:.2f}, "
                          f"Diversity: {point.diversity_index:.2f}")
        
        except Exception as e:
            print(f"Warning: Failed to record assembly state: {e}")
    
    def on_convergence_reached(self):
        """Called when convergence is detected."""
        print("\n✓ Convergence reached - Canonical N tracking complete")
        print(self.integrator.get_convergence_report())


# ============================================================================
# EXAMPLE INTEGRATION
# ============================================================================

def example_integration_with_assembly():
    """
    Example showing how to integrate canonical tracking with assembly system.
    """
    from canonical_integration import AssemblyObserver, CanonicalIntegrator
    
    # Create integrator
    integrator = CanonicalIntegrator(enable_tracking=True)
    observer = AssemblyObserver(integrator)
    
    # Simulate assembly evolution
    print("Simulating assembly evolution with canonical tracking...\n")
    
    # Initial: 1 square
    class MockAssembly0:
        def get_all_polyforms(self):
            return [{'sides': 4, 'vertices': [[0, 0], [1, 0], [1, 1], [0, 1]]}]
        def get_bonds(self):
            return []
    observer.on_generation_complete(MockAssembly0(), 0)
    
    # Gen 10: 2 squares
    class MockAssembly10:
        def get_all_polyforms(self):
            return [
                {'sides': 4, 'vertices': [[0, 0], [1, 0], [1, 1], [0, 1]]},
                {'sides': 4, 'vertices': [[2, 0], [3, 0], [3, 1], [2, 1]]}
            ]
        def get_bonds(self):
            return [{'poly1_id': '0', 'poly2_id': '1'}]
    observer.on_generation_complete(MockAssembly10(), 10)
    
    # Gen 20: 2 squares + 1 triangle
    class MockAssembly20:
        def get_all_polyforms(self):
            return [
                {'sides': 4, 'vertices': [[0, 0], [1, 0], [1, 1], [0, 1]]},
                {'sides': 4, 'vertices': [[2, 0], [3, 0], [3, 1], [2, 1]]},
                {'sides': 3, 'vertices': [[1, 1.5], [2, 1.5], [1.5, 2.5]]}
            ]
        def get_bonds(self):
            return [
                {'poly1_id': '0', 'poly2_id': '1'},
                {'poly1_id': '1', 'poly2_id': '2'}
            ]
    observer.on_generation_complete(MockAssembly20(), 20)
    
    # Report
    observer.on_convergence_reached()
    
    # Export metrics
    metrics = integrator.get_metrics_dict()
    print("\nExported Metrics:")
    for key, value in metrics.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    example_integration_with_assembly()
