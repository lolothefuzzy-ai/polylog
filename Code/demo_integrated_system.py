"""
Complete Integrated System Demo

End-to-end demonstration of canonical N tracking fully integrated
with genetic algorithm simulation.

This shows:
1. Multi-population GA simulation
2. Real-time canonical N tracking
3. Visual comparison across populations
4. Convergence analysis
5. Data export
"""

import numpy as np
from typing import List, Dict, Any
import random
import time

# Import integration modules
from integration_hooks import (
    GAIntegration, 
    MultiPopulationIntegration
)


# ============================================================================
# MOCK GA CLASSES (Simulating your actual GA)
# ============================================================================

class MockAssembly:
    """Mock polyform assembly for simulation."""
    
    def __init__(self, num_polygons: int, polygon_types: List[int]):
        self.num_polygons = num_polygons
        self.polygon_types = polygon_types
        self.fitness = 0.0
        self._polyforms_cache = None
        self._bonds_cache = None
    
    def get_all_polyforms(self) -> List[Dict]:
        """Return mock polyform list."""
        if self._polyforms_cache is not None:
            return self._polyforms_cache
        
        self._polyforms_cache = [
            {
                'id': i,
                'sides': poly_type,
                'vertices': [[random.random(), random.random()] for _ in range(poly_type)]
            }
            for i, poly_type in enumerate(self.polygon_types)
        ]
        return self._polyforms_cache
    
    def get_bonds(self) -> List[Dict]:
        """Return mock bonds list."""
        if self._bonds_cache is not None:
            return self._bonds_cache
        
        # Random bonds between polygons
        self._bonds_cache = [
            {'from': i, 'to': j, 'strength': random.random()}
            for i in range(self.num_polygons)
            for j in range(i + 1, min(i + 3, self.num_polygons))
        ]
        return self._bonds_cache
    
    def mutate(self) -> 'MockAssembly':
        """Create mutated copy."""
        new_types = list(self.polygon_types)
        
        # Random mutation: change a polygon type
        if random.random() < 0.3:
            idx = random.randint(0, len(new_types) - 1)
            new_types[idx] = random.randint(3, 8)
        
        # Random mutation: add polygon
        if random.random() < 0.2 and len(new_types) < 10:
            new_types.append(random.randint(3, 8))
        
        assembly = MockAssembly(len(new_types), new_types)
        assembly._polyforms_cache = None
        assembly._bonds_cache = None
        return assembly
    
    def evaluate_fitness(self) -> float:
        """Evaluate fitness (more polygons + more variety = better)."""
        n_polygons = len(self.polygon_types)
        variety = len(set(self.polygon_types))
        
        # Simple fitness function
        self.fitness = np.log(n_polygons + 1) + 0.5 * np.log(variety + 1) + random.gauss(0, 0.1)
        return self.fitness


class SimpleGA:
    """Mock simple genetic algorithm for testing."""
    
    def __init__(self, population_size: int = 20):
        self.population_size = population_size
        self.population: List[MockAssembly] = []
        self.generation = 0
        self._initialize_population()
    
    def _initialize_population(self):
        """Initialize with random assemblies."""
        self.population = [
            MockAssembly(
                num_polygons=random.randint(2, 6),
                polygon_types=[random.randint(3, 8) for _ in range(random.randint(2, 6))]
            )
            for _ in range(self.population_size)
        ]
        self._evaluate()
    
    def _evaluate(self):
        """Evaluate all individuals."""
        for individual in self.population:
            individual.evaluate_fitness()
        
        # Sort by fitness (best first)
        self.population.sort(key=lambda x: x.fitness, reverse=True)
    
    def step(self):
        """Perform one generation."""
        # Selection: keep top 30%
        elite_size = max(1, int(self.population_size * 0.3))
        new_population = self.population[:elite_size].copy()
        
        # Mutation: fill rest of population
        while len(new_population) < self.population_size:
            parent = random.choice(self.population[:elite_size])
            child = parent.mutate()
            new_population.append(child)
        
        self.population = new_population
        self._evaluate()
        self.generation += 1
    
    def get_best(self) -> MockAssembly:
        """Get best individual."""
        return self.population[0]


# ============================================================================
# DEMO 1: SINGLE GA WITH TRACKING
# ============================================================================

def demo_1_single_ga():
    """Demo 1: Single GA with integrated tracking."""
    
    print("\n" + "="*80)
    print("DEMO 1: Single GA with Canonical N Tracking")
    print("="*80)
    
    # Create GA
    ga = SimpleGA(population_size=30)
    
    # Create tracker
    tracker = GAIntegration(n_value=30, name="Simple GA (Pop=30)")
    
    print(f"\nRunning GA for 50 generations...")
    print(f"Population size: 30")
    print(f"-" * 80)
    
    # Evolution loop
    for gen in range(50):
        ga.step()
        best = ga.get_best()
        
        # Track this generation
        tracker.track_generation(best)
        
        # Print progress every 10 generations
        if gen % 10 == 0 or gen == 49:
            tracker.print_progress(total_generations=50)
    
    # Get final report
    print("\n" + "-" * 80)
    print("FINAL REPORT:")
    print(tracker.finalize())


# ============================================================================
# DEMO 2: MULTI-POPULATION GA COMPARISON
# ============================================================================

def demo_2_multi_population():
    """Demo 2: Compare two different GA configurations."""
    
    print("\n" + "="*80)
    print("DEMO 2: Multi-Population GA Comparison")
    print("="*80)
    
    # Create two GA instances with different population sizes
    ga_small = SimpleGA(population_size=15)
    ga_large = SimpleGA(population_size=50)
    
    # Create multi-population tracker
    multi = MultiPopulationIntegration()
    
    ga_small_tracker = multi.register_population(15, "GA Small (Pop=15)")
    ga_large_tracker = multi.register_population(50, "GA Large (Pop=50)")
    
    print(f"\nRunning two GA instances for 40 generations...")
    print(f"Configuration 1: Population size = 15")
    print(f"Configuration 2: Population size = 50")
    print(f"-" * 80)
    
    # Evolution loop
    for gen in range(40):
        ga_small.step()
        ga_large.step()
        
        # Track both
        ga_small_tracker.track_generation(ga_small.get_best())
        ga_large_tracker.track_generation(ga_large.get_best())
        
        # Print progress every 10 generations
        if gen % 10 == 0 or gen == 39:
            print(f"\nGeneration {gen}:")
            ga_small_tracker.print_progress(total_generations=40)
            ga_large_tracker.print_progress(total_generations=40)
    
    # Compare results
    print("\n" + "-" * 80)
    print("CONVERGENCE COMPARISON:")
    print(multi.get_convergence_report())
    
    print("\nVISUAL COMPARISON:")
    multi.print_comparison()


# ============================================================================
# DEMO 3: TRACKING ACROSS MULTIPLE N VALUES
# ============================================================================

def demo_3_multi_range():
    """Demo 3: Track same GA with different N ranges."""
    
    print("\n" + "="*80)
    print("DEMO 3: Convergence Across N Ranges")
    print("="*80)
    
    from canonical_system_integration import CanonicalSystemIntegrator
    
    # Create system tracker
    system = CanonicalSystemIntegrator(enable_visual_tracking=True)
    
    # Register different population sizes
    pop_sizes = [10, 20, 40, 80]
    for size in pop_sizes:
        system.register_range(size, f"Population Size {size}")
    
    print(f"\nRunning GA with 4 different population sizes for 30 generations...")
    print(f"-" * 80)
    
    # Create GA instances
    ga_instances = {size: SimpleGA(population_size=size) for size in pop_sizes}
    
    # Evolution loop
    for gen in range(30):
        for size in pop_sizes:
            ga = ga_instances[size]
            ga.step()
            best = ga.get_best()
            
            # Track
            system.record_generation_for_range(
                size,
                best.get_all_polyforms(),
                best.get_bonds(),
                gen
            )
        
        # Print every 10 generations
        if gen % 10 == 0 or gen == 29:
            print(f"\nGeneration {gen} Summary:")
            for size in pop_sizes:
                metrics = system.get_range_metrics(size)
                if metrics:
                    print(f"  N={size:3d}: logN_growth={metrics.get('logN_growth', 0):+.2f}, "
                          f"diversity={metrics.get('final_diversity', 0):.2f}")
    
    # Final analysis
    print("\n" + "-" * 80)
    print("ALL RANGES SUMMARY:")
    print(system.get_all_ranges_summary())
    
    print("\nCONVERGENCE COMPARISON:")
    print(system.get_convergence_comparison())
    
    print("\nVISUAL COMPARISON:")
    system.print_visual_comparison()
    
    # Export metrics
    metrics = system.export_all_metrics()
    print(f"\nMetrics exported for {len(metrics)} ranges")


# ============================================================================
# DEMO 4: REAL-TIME MONITORING WITH METRICS EXPORT
# ============================================================================

def demo_4_real_time_monitoring():
    """Demo 4: Real-time monitoring with periodic metric export."""
    
    print("\n" + "="*80)
    print("DEMO 4: Real-Time Monitoring with Metrics Export")
    print("="*80)
    
    from canonical_system_integration import CanonicalSystemIntegrator
    import json
    
    # Create system tracker
    system = CanonicalSystemIntegrator(enable_visual_tracking=True)
    
    # Register multiple configurations
    configs = [
        (25, "GA with High Mutation"),
        (40, "GA with Low Mutation"),
        (60, "GA with Adaptive Mutation"),
    ]
    
    for n_val, name in configs:
        system.register_range(n_val, name)
    
    # Create GA instances
    ga_instances = {n_val: SimpleGA(population_size=n_val) for n_val, _ in configs}
    
    print(f"\nRunning GA with metrics export every 5 generations...")
    print(f"Total generations: 50")
    print(f"-" * 80)
    
    export_points = []
    
    # Evolution loop
    start_time = time.time()
    
    for gen in range(50):
        for n_val, _ in configs:
            ga = ga_instances[n_val]
            ga.step()
            best = ga.get_best()
            
            system.record_generation_for_range(
                n_val,
                best.get_all_polyforms(),
                best.get_bonds(),
                gen
            )
        
        # Export metrics every 5 generations
        if gen % 5 == 0 or gen == 49:
            elapsed = time.time() - start_time
            metrics = system.export_all_metrics()
            export_points.append({
                'generation': gen,
                'elapsed_time': elapsed,
                'metrics': {
                    str(n_val): {
                        'logN_growth': m.get('logN_growth', 0),
                        'diversity_change': m.get('final_diversity', 0) - m.get('initial_diversity', 0)
                    }
                    for n_val, m in metrics.items()
                }
            })
            
            print(f"Gen {gen:3d} (t={elapsed:6.1f}s): ", end="")
            for n_val, m in metrics.items():
                print(f"N={n_val} logN={m.get('logN_growth', 0):+.2f} ", end="")
            print()
    
    # Print final report
    print("\n" + "-" * 80)
    print("FINAL REPORT:")
    system.finalize_all_ranges()
    
    # Show export history
    print("\nExport History (selected generations):")
    print(json.dumps(export_points[-3:], indent=2))


# ============================================================================
# DEMO 5: COMPARATIVE ANALYSIS - GA VS RANDOM
# ============================================================================

def demo_5_ga_vs_random():
    """Demo 5: Compare GA evolution vs random generation."""
    
    print("\n" + "="*80)
    print("DEMO 5: GA Evolution vs Random Generation")
    print("="*80)
    
    from integration_hooks import GAIntegration, GeneratorIntegration
    
    # GA tracker
    ga = SimpleGA(population_size=30)
    ga_tracker = GAIntegration(n_value=30, name="GA Evolution")
    
    # Random generator tracker
    class RandomGenerator:
        def generate_random_assembly(self):
            return MockAssembly(
                num_polygons=random.randint(2, 8),
                polygon_types=[random.randint(3, 8) for _ in range(random.randint(2, 8))]
            )
    
    random_gen = RandomGenerator()
    random_tracker = GeneratorIntegration(
        random_gen,
        n_value=30,
        name="Random Generation"
    )
    
    print(f"\nComparing GA evolution vs random generation for 40 iterations...")
    print(f"-" * 80)
    
    # Run both in parallel
    for iteration in range(40):
        # GA evolution
        ga.step()
        ga_tracker.track_generation(ga.get_best())
        
        # Random generation
        random_assembly = random_tracker.generate_with_tracking()
        
        if iteration % 10 == 0 or iteration == 39:
            print(f"\nIteration {iteration}:")
            ga_tracker.print_progress(total_generations=40)
    
    # Compare
    print("\n" + "-" * 80)
    print("GA RESULTS:")
    print(ga_tracker.finalize())
    
    print("\n" + "-" * 80)
    print("RANDOM GENERATION RESULTS:")
    print(random_tracker.get_report())


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def run_all_demos():
    """Run all demos in sequence."""
    
    print("\n" + "="*80)
    print("CANONICAL N TRACKING SYSTEM - INTEGRATED DEMOS")
    print("="*80)
    print("\nThis demonstrates the complete integrated system with:")
    print("  • Single GA tracking")
    print("  • Multi-population comparison")
    print("  • Multi-range convergence analysis")
    print("  • Real-time monitoring with metrics export")
    print("  • GA vs Random comparison")
    print("\nEach demo shows different integration patterns.\n")
    
    # Run demos
    demo_1_single_ga()
    demo_2_multi_population()
    demo_3_multi_range()
    demo_4_real_time_monitoring()
    demo_5_ga_vs_random()
    
    print("\n" + "="*80)
    print("ALL DEMOS COMPLETED")
    print("="*80)
    print("\nFor integration into your actual system:")
    print("  1. Review SYSTEM_REFERENCE.md for architecture overview")
    print("  2. See INTEGRATION_GUIDE.md for integration patterns")
    print("  3. Check integration_hooks.py for detailed API reference")
    print("  4. Choose an integration pattern that fits your workflow")
    print("\nQuick start example:")
    print("  from integration_hooks import GAIntegration")
    print("  tracker = GAIntegration(pop_size, 'My GA')")
    print("  for gen in range(gens):")
    print("      tracker.track_generation(best_individual)")
    print("  print(tracker.finalize())")
    print()


if __name__ == "__main__":
    run_all_demos()
