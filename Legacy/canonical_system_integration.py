"""
Canonical N System Integration - Master Module

Full system-wide integration of canonical polyform count tracking.

Provides:
- Multi-range convergence tracking (different population/parameter sets)
- Visual tracking across N ranges (ASCII graphs)
- Real-time metrics dashboard
- Integration hooks for all generators
- Comparison across ranges
"""

from dataclasses import dataclass
from typing import Any, Dict, List

import numpy as np

from canonical_integration import CanonicalIntegrator
from convergence_range_analyzer import RangeConvergenceAnalyzer


@dataclass
class SystemMetrics:
    """System-wide convergence metrics."""
    range_name: str
    n_value: int
    generations: int
    initial_logN: float
    final_logN: float
    logN_growth: float
    diversity_change: float
    convergence_status: str
    timestamp: float


class CanonicalSystemIntegrator:
    """
    Master integration for canonical N tracking across entire system.
    
    Manages:
    - Multiple independent tracking instances (different N ranges)
    - Cross-range comparison and visualization
    - System-wide convergence analysis
    - Real-time dashboard
    """
    
    def __init__(self, enable_visual_tracking=True):
        """
        Initialize system-wide integration.
        
        Args:
            enable_visual_tracking: Enable ASCII visualization across ranges
        """
        self.enable_visual_tracking = enable_visual_tracking
        
        # Multi-range tracking
        self.range_trackers: Dict[int, CanonicalIntegrator] = {}
        self.range_names: Dict[int, str] = {}
        self.range_analyzer = RangeConvergenceAnalyzer()
        
        # Metrics aggregation
        self.all_metrics: List[SystemMetrics] = []
        
        # Track which ranges are active
        self.active_ranges: Dict[int, bool] = {}
        
        print("✅ Canonical System Integrator initialized")
    
    def register_range(self, n_value: int, name: str = None, enable_tracking: bool = True) -> CanonicalIntegrator:
        """
        Register a new N range for tracking.
        
        Args:
            n_value: N value (population size or similar)
            name: Human-readable name for this range
            enable_tracking: Enable tracking for this range
            
        Returns:
            CanonicalIntegrator for this range
        """
        if n_value in self.range_trackers:
            print(f"⚠️  Range N={n_value} already registered")
            return self.range_trackers[n_value]
        
        integrator = CanonicalIntegrator(enable_tracking=enable_tracking)
        self.range_trackers[n_value] = integrator
        self.range_names[n_value] = name or f"N={n_value}"
        self.active_ranges[n_value] = True
        
        print(f"✓ Registered range: {self.range_names[n_value]}")
        return integrator
    
    def record_generation_for_range(self, n_value: int, polyforms: List[Dict], 
                                   bonds: List[Dict], generation: int):
        """
        Record assembly state for specific N range.
        
        Args:
            n_value: N value to track
            polyforms: Current polyforms
            bonds: Current bonds
            generation: Generation number
        """
        if n_value not in self.range_trackers:
            raise ValueError(f"Range N={n_value} not registered")
        
        integrator = self.range_trackers[n_value]
        point = integrator.record_assembly_state(polyforms, bonds, generation)
        
        # Also record for range analyzer
        self.range_analyzer.record_observation(n_value, generation, polyforms, 
                                              [0.5] * len(polyforms))  # Dummy fitness
        
        return point
    
    def get_range_metrics(self, n_value: int) -> Dict[str, Any]:
        """Get metrics for specific range."""
        if n_value not in self.range_trackers:
            return {}
        return self.range_trackers[n_value].get_metrics_dict()
    
    def get_all_ranges_summary(self) -> str:
        """Get summary of all registered ranges."""
        if not self.range_trackers:
            return "No ranges registered"
        
        lines = []
        lines.append("\n" + "="*80)
        lines.append("SYSTEM-WIDE CANONICAL N TRACKING - ALL RANGES")
        lines.append("="*80)
        
        for n_value in sorted(self.range_trackers.keys()):
            name = self.range_names.get(n_value, f"N={n_value}")
            metrics = self.get_range_metrics(n_value)
            
            if not metrics:
                lines.append(f"\n{name}: (no data)")
                continue
            
            lines.append(f"\n{name}:")
            lines.append(f"  Generations: {metrics.get('total_generations', 0)}")
            lines.append(f"  logN: {metrics.get('initial_logN', 0):.2f} → "
                        f"{metrics.get('final_logN', 0):.2f}")
            lines.append(f"  Growth: {metrics.get('logN_growth', 0):+.2f}")
            lines.append(f"  Diversity: {metrics.get('initial_diversity', 0):.2f} → "
                        f"{metrics.get('final_diversity', 0):.2f}")
            lines.append(f"  T-param: {metrics.get('initial_T', 0):.2f} → "
                        f"{metrics.get('final_T', 0):.2f}")
        
        return '\n'.join(lines)
    
    def print_visual_comparison(self):
        """Print ASCII visual comparison across ranges."""
        if not self.enable_visual_tracking:
            print("Visual tracking disabled")
            return
        
        print("\n" + "="*80)
        print("VISUAL COMPARISON ACROSS N RANGES")
        print("="*80)
        
        # Collect data
        ranges = sorted(self.range_trackers.keys())
        data = []
        
        for n_value in ranges:
            metrics = self.get_range_metrics(n_value)
            if metrics:
                data.append({
                    'n': n_value,
                    'name': self.range_names.get(n_value, f"N={n_value}"),
                    'logN_growth': metrics.get('logN_growth', 0),
                    'generations': metrics.get('total_generations', 0),
                    'diversity_change': metrics.get('final_diversity', 0) - metrics.get('initial_diversity', 0),
                })
        
        if not data:
            print("No data to visualize")
            return
        
        # Find max values for scaling
        max_growth = max([d['logN_growth'] for d in data]) or 1
        max_gens = max([d['generations'] for d in data]) or 1
        
        # Print bars
        print("\nlogN Growth (log-space):")
        for d in data:
            bar_width = int(30 * d['logN_growth'] / max_growth)
            bar = "█" * bar_width
            print(f"  {d['name']:20s} {bar} {d['logN_growth']:+.2f}")
        
        print("\nGenerations Tracked:")
        for d in data:
            bar_width = int(30 * d['generations'] / max_gens)
            bar = "░" * bar_width
            print(f"  {d['name']:20s} {bar} {d['generations']}")
        
        print("\nDiversity Change:")
        for d in data:
            change = d['diversity_change']
            if change > 0:
                bar = "▲" * int(change * 10)
            else:
                bar = "▼" * int(abs(change) * 10)
            print(f"  {d['name']:20s} {bar} {change:+.2f}")
    
    def get_convergence_comparison(self) -> str:
        """Compare convergence status across ranges."""
        lines = []
        lines.append("\n" + "="*80)
        lines.append("CONVERGENCE STATUS COMPARISON")
        lines.append("="*80)
        
        for n_value in sorted(self.range_trackers.keys()):
            integrator = self.range_trackers[n_value]
            report = integrator.get_convergence_report()
            
            # Extract convergence status
            if "CONVERGED" in report:
                status = "✓ CONVERGED"
            elif "IMPROVING" in report:
                status = "↑ IMPROVING"
            else:
                status = "~ STABLE"
            
            name = self.range_names.get(n_value, f"N={n_value}")
            lines.append(f"{name:25s} {status}")
        
        return '\n'.join(lines)
    
    def export_all_metrics(self) -> Dict[int, Dict[str, Any]]:
        """Export all metrics across all ranges."""
        result = {}
        
        for n_value in self.range_trackers.keys():
            metrics = self.get_range_metrics(n_value)
            if metrics:
                result[n_value] = metrics
        
        return result
    
    def finalize_all_ranges(self):
        """Finalize tracking for all ranges."""
        print("\n" + "="*80)
        print("FINALIZING ALL RANGES")
        print("="*80)
        
        for n_value in self.range_trackers.keys():
            integrator = self.range_trackers[n_value]
            name = self.range_names.get(n_value, f"N={n_value}")
            print(f"\n{name}:")
            print(integrator.get_convergence_report())


class SystemIntegrationHelper:
    """Helper class for easy integration into existing code."""
    
    # Singleton instance
    _instance = None
    
    @classmethod
    def get_instance(cls) -> CanonicalSystemIntegrator:
        """Get or create singleton system integrator."""
        if cls._instance is None:
            cls._instance = CanonicalSystemIntegrator(enable_visual_tracking=True)
        return cls._instance
    
    @classmethod
    def register_generator(cls, n_value: int, generator_name: str = None):
        """Decorator to register generator with system tracking."""
        def decorator(generator_class):
            integrator = cls.get_instance().register_range(n_value, generator_name)
            generator_class._canonical_integrator = integrator
            generator_class._canonical_n_value = n_value
            return generator_class
        return decorator


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

def example_multi_range_tracking():
    """
    Example showing multi-range canonical N tracking.
    """
    print("\n" + "="*80)
    print("MULTI-RANGE CANONICAL N TRACKING EXAMPLE")
    print("="*80)
    
    # Create system integrator
    system = CanonicalSystemIntegrator(enable_visual_tracking=True)
    
    # Register different N ranges
    integrator_small = system.register_range(10, "Small N (10)")
    integrator_medium = system.register_range(30, "Medium N (30)")
    integrator_large = system.register_range(50, "Large N (50)")
    
    print("\n" + "-"*80)
    print("Simulating evolution across 3 N ranges")
    print("-"*80)
    
    # Create mock assemblies
    class MockAssembly:
        def __init__(self, n):
            self.n = n
            self.polyforms = []
            self.bonds = []
        
        def add_poly(self, sides):
            self.polyforms.append({'sides': sides, 'vertices': [[0, 0], [1, 1], [2, 0]]})
        
        def get_all_polyforms(self):
            return self.polyforms
        
        def get_bonds(self):
            return self.bonds
    
    # Simulate multiple generations
    for generation in range(5):
        print(f"\n--- Generation {generation} ---")
        
        # Small N
        asm_small = MockAssembly(10)
        for _ in range(generation + 3):
            asm_small.add_poly(np.random.randint(3, 7))
        system.record_generation_for_range(10, asm_small.get_all_polyforms(), 
                                         asm_small.get_bonds(), generation)
        
        # Medium N
        asm_medium = MockAssembly(30)
        for _ in range(generation + 4):
            asm_medium.add_poly(np.random.randint(3, 8))
        system.record_generation_for_range(30, asm_medium.get_all_polyforms(), 
                                          asm_medium.get_bonds(), generation)
        
        # Large N
        asm_large = MockAssembly(50)
        for _ in range(generation + 5):
            asm_large.add_poly(np.random.randint(3, 9))
        system.record_generation_for_range(50, asm_large.get_all_polyforms(), 
                                          asm_large.get_bonds(), generation)
    
    # Print results
    print(system.get_all_ranges_summary())
    print(system.get_convergence_comparison())
    system.print_visual_comparison()
    
    # Finalize
    system.finalize_all_ranges()


if __name__ == "__main__":
    example_multi_range_tracking()
