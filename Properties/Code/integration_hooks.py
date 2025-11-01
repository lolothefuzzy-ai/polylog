"""
Integration Hooks - Connect canonical N tracking to your generators

Ready-to-use integration points for:
- Random assembly generators
- Genetic algorithms
- Multi-population systems
- Real-time visualization
"""

import time
from typing import Any, Callable, Dict, List

from canonical_system_integration import CanonicalSystemIntegrator


class GeneratorIntegration:
    """Integrate tracking into any generator class."""
    
    def __init__(self, generator_instance, n_value: int, name: str = None):
        """
        Wrap generator with tracking.
        
        Args:
            generator_instance: Your generator instance
            n_value: N value for tracking
            name: Display name
        """
        self.generator = generator_instance
        self.n_value = n_value
        self.name = name or f"Generator(N={n_value})"
        self.system_tracker = CanonicalSystemIntegrator()
        self.system_tracker.register_range(n_value, self.name)
        
        self.generation_count = 0
    
    def generate_with_tracking(self, *args, **kwargs):
        """Call generator and automatically track result."""
        assembly = self.generator.generate_random_assembly(*args, **kwargs)
        
        # Record tracking
        self.system_tracker.record_generation_for_range(
            self.n_value,
            assembly.get_all_polyforms() if hasattr(assembly, 'get_all_polyforms') else [],
            assembly.get_bonds() if hasattr(assembly, 'get_bonds') else [],
            self.generation_count
        )
        
        self.generation_count += 1
        return assembly
    
    def get_report(self):
        """Get tracking report."""
        return self.system_tracker.get_all_ranges_summary()


class GAIntegration:
    """Integrate canonical N tracking into genetic algorithm."""
    
    def __init__(self, n_value: int, name: str = None):
        """
        Setup GA integration.
        
        Args:
            n_value: Population size or similar
            name: Display name
        """
        self.n_value = n_value
        self.name = name or f"GA(N={n_value})"
        self.system_tracker = CanonicalSystemIntegrator()
        self.system_tracker.register_range(n_value, self.name)
        
        self.generation_count = 0
        self.start_time = time.time()
    
    def track_generation(self, best_individual, population=None):
        """
        Track GA generation.
        
        Args:
            best_individual: Best assembly in population
            population: Full population (optional)
        """
        polyforms = (best_individual.get_all_polyforms() 
                    if hasattr(best_individual, 'get_all_polyforms') else [])
        bonds = (best_individual.get_bonds() 
                if hasattr(best_individual, 'get_bonds') else [])
        
        self.system_tracker.record_generation_for_range(
            self.n_value, polyforms, bonds, self.generation_count
        )
        
        self.generation_count += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Return structured metrics for this GA tracker."""
        metrics = self.system_tracker.get_range_metrics(self.n_value)
        return metrics or {}
    
    def print_progress(self, total_generations: int = None):
        """Print current progress."""
        elapsed = time.time() - self.start_time
        
        metrics = self.system_tracker.get_range_metrics(self.n_value)
        if not metrics:
            print(f"{self.name}: No data yet")
            return
        
        logN_growth = metrics.get('logN_growth', 0)
        diversity = metrics.get('final_diversity', 0)
        
        print(f"\n{self.name}:")
        print(f"  Generation: {self.generation_count}")
        print(f"  Elapsed: {elapsed:.1f}s")
        if total_generations:
            eta = (elapsed / max(self.generation_count, 1)) * (total_generations - self.generation_count)
            print(f"  ETA: {eta:.1f}s")
        print(f"  logN Growth: {logN_growth:+.2f}")
        print(f"  Diversity: {diversity:.2f}")
    
    def finalize(self):
        """Finalize and show report."""
        self.system_tracker.finalize_all_ranges()
        return self.system_tracker.get_all_ranges_summary()


class MultiPopulationIntegration:
    """Track multiple populations simultaneously."""
    
    def __init__(self):
        self.system_tracker = CanonicalSystemIntegrator(enable_visual_tracking=True)
        self.ga_integrations: Dict[int, GAIntegration] = {}
    
    def register_population(self, pop_size: int, name: str = None) -> GAIntegration:
        """Register population for tracking."""
        ga = GAIntegration(pop_size, name or f"Population {len(self.ga_integrations)}")
        self.ga_integrations[pop_size] = ga
        return ga
    
    def get_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Collect metrics for all registered populations."""
        data: Dict[str, Dict[str, Any]] = {}
        for pop_size, ga in self.ga_integrations.items():
            data[ga.name] = ga.get_metrics()
            if "n_value" not in data[ga.name]:
                # annotate with key metadata for convenience
                data[ga.name]["n_value"] = pop_size
        return data
    
    def track_all_populations(self, populations: Dict[int, Any]):
        """Track all populations at once."""
        for pop_size, pop_data in populations.items():
            if pop_size in self.ga_integrations:
                best = pop_data.get('best') or pop_data[0]
                self.ga_integrations[pop_size].track_generation(best, pop_data)
    
    def print_comparison(self):
        """Print visual comparison across populations."""
        self.system_tracker.print_visual_comparison()
    
    def get_convergence_report(self):
        """Get convergence status for all populations."""
        return self.system_tracker.get_convergence_comparison()


class CallbackBasedIntegration:
    """Use callbacks for integration (no code modification needed)."""
    
    def __init__(self, system_tracker: CanonicalSystemIntegrator = None):
        self.system_tracker = system_tracker or CanonicalSystemIntegrator()
        self.range_callbacks: Dict[int, List[Callable]] = {}
    
    def on_generation(self, n_value: int, best_individual, generation: int):
        """
        Universal generation callback.
        
        Call this from your GA after each generation.
        """
        polyforms = (best_individual.get_all_polyforms() 
                    if hasattr(best_individual, 'get_all_polyforms') else [])
        bonds = (best_individual.get_bonds() 
                if hasattr(best_individual, 'get_bonds') else [])
        
        self.system_tracker.record_generation_for_range(
            n_value, polyforms, bonds, generation
        )
        
        # Call any registered callbacks
        if n_value in self.range_callbacks:
            for callback in self.range_callbacks[n_value]:
                callback(generation, best_individual)
    
    def register_callback(self, n_value: int, callback: Callable):
        """Register callback to be called on each generation."""
        if n_value not in self.range_callbacks:
            self.range_callbacks[n_value] = []
        self.range_callbacks[n_value].append(callback)
    
    def get_tracking_function(self, n_value: int):
        """Get a tracking function for specific range."""
        def track(best_individual, generation: int):
            self.on_generation(n_value, best_individual, generation)
        return track


# ============================================================================
# PRACTICAL EXAMPLES
# ============================================================================

def example_1_simple_generator_tracking():
    """
    Example 1: Track simple random assembly generator.
    
    Most basic integration - minimal code changes needed.
    """
    print("\n" + "="*80)
    print("EXAMPLE 1: Simple Generator Tracking")
    print("="*80)
    
    # Mock generator class
    class SimpleGenerator:
        def generate_random_assembly(self):
            class MockAssembly:
                def get_all_polyforms(self):
                    return [{'sides': 4, 'vertices': [[0, 0], [1, 0], [1, 1], [0, 1]]}]
                def get_bonds(self):
                    return []
            return MockAssembly()
    
    # Create and wrap generator
    generator = SimpleGenerator()
    integration = GeneratorIntegration(generator, n_value=10, name="Simple Gen")
    
    # Generate 5 times with tracking
    for i in range(5):
        assembly = integration.generate_with_tracking()
        print(f"Generated assembly {i}")
    
    print(integration.get_report())


def example_2_ga_with_tracking():
    """
    Example 2: Track GA evolution.
    
    Track best individual at each generation.
    """
    print("\n" + "="*80)
    print("EXAMPLE 2: GA with Tracking")
    print("="*80)
    
    class MockAssembly:
        def __init__(self, fitness):
            self.fitness = fitness
        def get_all_polyforms(self):
            return [{'sides': 4 + self.fitness, 'vertices': [[0, 0], [1, 0], [1, 1], [0, 1]]}]
        def get_bonds(self):
            return []
    
    # Setup GA integration
    ga = GAIntegration(n_value=25, name="GA Population")
    
    # Simulate GA evolution
    print("\nSimulating 10 generations...")
    for gen in range(10):
        # Simulate getting better
        best = MockAssembly(fitness=gen * 0.1)
        ga.track_generation(best)
        
        if gen % 3 == 0:
            ga.print_progress(total_generations=10)
    
    print(ga.finalize())


def example_3_multi_population():
    """
    Example 3: Track multiple populations.
    
    Compare different GA runs or mutation rates.
    """
    print("\n" + "="*80)
    print("EXAMPLE 3: Multi-Population Tracking")
    print("="*80)
    
    class MockAssembly:
        def __init__(self, mutation_rate):
            self.mutation_rate = mutation_rate
        def get_all_polyforms(self):
            return [{'sides': 4, 'vertices': [[0, 0], [1, 0], [1, 1], [0, 1]]}]
        def get_bonds(self):
            return []
    
    # Setup multi-population tracking
    multi = MultiPopulationIntegration()
    
    mutation_rates = [0.01, 0.05, 0.1]
    ga_instances = {}
    
    for rate in mutation_rates:
        ga = multi.register_population(
            int(rate * 1000), 
            f"GA Mutation={rate}"
        )
        ga_instances[rate] = ga
    
    # Simulate evolution
    print("\nSimulating 10 generations across 3 GA configs...")
    for gen in range(10):
        for rate in mutation_rates:
            best = MockAssembly(mutation_rate=rate)
            ga_instances[rate].track_generation(best)
    
    print(multi.get_convergence_report())
    multi.print_comparison()


def example_4_callback_integration():
    """
    Example 4: Callback-based integration.
    
    No direct code changes to your GA needed - use callbacks.
    """
    print("\n" + "="*80)
    print("EXAMPLE 4: Callback-Based Integration")
    print("="*80)
    
    class MockAssembly:
        def __init__(self, value):
            self.value = value
        def get_all_polyforms(self):
            return [{'sides': 4, 'vertices': [[0, 0], [1, 0], [1, 1], [0, 1]]}]
        def get_bonds(self):
            return []
    
    # Setup callback integration
    callback_system = CallbackBasedIntegration()
    
    # Register a callback to print stats
    def print_stats(generation, individual):
        print(f"  Gen {generation}: value={individual.value}")
    
    n_value = 20
    callback_system.system_tracker.register_range(n_value, "Callback GA")
    callback_system.register_callback(n_value, print_stats)
    
    # Get tracking function for your GA
    track_fn = callback_system.get_tracking_function(n_value)
    
    # Simulate GA - pass best_individual and generation to track_fn
    print("\nSimulating GA with callbacks...")
    for gen in range(5):
        best = MockAssembly(value=gen * 2)
        track_fn(best, gen)
    
    print(callback_system.system_tracker.get_all_ranges_summary())


# ============================================================================
# QUICK START TEMPLATE
# ============================================================================

QUICK_START_TEMPLATE = '''
"""
Quick start template for integrating canonical N tracking into your code.
Copy and modify as needed.
"""

from integration_hooks import GAIntegration

# 1. Create GA integration
ga_tracker = GAIntegration(
    n_value=50,  # Change to your population size
    name="My GA"
)

# 2. In your GA loop, call track_generation with best individual
for generation in range(num_generations):
    # ... your GA code ...
    best_individual = my_ga.get_best()
    
    # Add this line:
    ga_tracker.track_generation(best_individual)
    
    # Optional: print progress
    if generation % 10 == 0:
        ga_tracker.print_progress(num_generations)

# 3. After GA completes, get report
report = ga_tracker.finalize()
print(report)
'''


if __name__ == "__main__":
    example_1_simple_generator_tracking()
    example_2_ga_with_tracking()
    example_3_multi_population()
    example_4_callback_integration()
    
    print("\n" + "="*80)
    print("QUICK START TEMPLATE")
    print("="*80)
    print(QUICK_START_TEMPLATE)
