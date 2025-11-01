#!/usr/bin/env python3
"""
Integration module - Connect convergence tracker to EvolutionaryGenerator

# JUPYTER NOTEBOOK INTEGRATION
%matplotlib inline
"""

from typing import Optional

from evolutionary_generator import EvolutionaryGenerator

from convergence_visualizer import ConvergenceVisualizerWindow
import matplotlib.pyplot as plt

class EvolutionaryGeneratorWithTracking(EvolutionaryGenerator):
    """Extended EvolutionaryGenerator with convergence tracking."""
    
    def __init__(self, assembly, population_size: int = 20, 
                 convergence_window: Optional[ConvergenceVisualizerWindow] = None):
        super().__init__(assembly, population_size)
        self.convergence_window = convergence_window
    
    def evolve(self, target_polyform_count: int = 8, 
              generations: int = 50,
              allowed_types=None):
        """Evolve with convergence tracking."""
        if allowed_types is None:
            allowed_types = [3, 4, 5, 6]
        
        print("Starting evolution:")
        print(f"   Population: {self.population_size}")
        print(f"   Generations: {generations}")
        print(f"   Target polyforms: {target_polyform_count}")
        
        # Initialize population
        population = self._initialize_population(target_polyform_count, allowed_types)
        
        best_genome = None
        best_fitness = float('-inf')
        
        # Evolution loop
        for gen in range(generations):
            # Evaluate fitness
            fitness_scores = [self._evaluate_fitness(genome) for genome in population]
            
            # Track convergence if window available
            if self.convergence_window:
                # Use best genome's polygons for tracking
                best_idx = fitness_scores.index(max(fitness_scores))
                best_gen_polygons = population[best_idx].polygons
                self.convergence_window.record_generation(
                    best_gen_polygons,
                    fitness_scores,
                    len(population)
                )
            
            # Track best
            gen_best_idx = fitness_scores.index(max(fitness_scores))
            if fitness_scores[gen_best_idx] > best_fitness:
                best_fitness = fitness_scores[gen_best_idx]
                best_genome = population[gen_best_idx].copy()
            
            # Print progress
            if gen % 10 == 0 or gen == generations - 1:
                import numpy as np
                avg_fitness = np.mean(fitness_scores)
                print(f"   Gen {gen:3d}: Best={best_fitness:.3f}, Avg={avg_fitness:.3f}")
            
            # Selection
            parents = self._tournament_selection(population, fitness_scores)
            
            # Create offspring
            offspring = []
            for i in range(0, len(parents) - 1, 2):
                child1, child2 = self._crossover(parents[i], parents[i+1])
                offspring.append(self._mutate(child1, allowed_types))
                offspring.append(self._mutate(child2, allowed_types))
            
            # Elitism: keep best individuals
            import numpy as np
            elite = [population[i] for i in np.argsort(fitness_scores)[-self.elite_size:]]
            
            # Replace population
            population = elite + offspring[:self.population_size - self.elite_size]
            self.generation += 1
        
        print(f"Evolution complete! Best fitness: {best_fitness:.3f}")
        
        return best_genome


def setup_convergence_tracking(generator: EvolutionaryGenerator, 
                              parent=None) -> ConvergenceVisualizerWindow:
    """
    Setup convergence tracking for an evolutionary generator.
    
    Args:
        generator: EvolutionaryGenerator instance
        parent: Parent widget for the window
        
    Returns:
        ConvergenceVisualizerWindow instance (not shown)
        
    Example:
        tracker_window = setup_convergence_tracking(generator)
        tracker_window.show()
        best = generator.evolve(...)
    """
    window = ConvergenceVisualizerWindow(parent)
    
    # Monkey-patch the evolve method to record convergence
    original_evolve = generator.evolve
    
    def evolve_with_tracking(*args, **kwargs):
        # Store reference to window in generator
        generator.convergence_window = window
        
        # Call original with tracking
        if allowed_types := kwargs.get('allowed_types'):
            pass
        else:
            allowed_types = [3, 4, 5, 6]
            kwargs['allowed_types'] = allowed_types
        
        generations = kwargs.get('generations', args[2] if len(args) > 2 else 50)
        target_count = kwargs.get('target_polyform_count', args[0] if len(args) > 0 else 8)
        
        print("Starting evolution with convergence tracking:")
        print(f"   Population: {generator.population_size}")
        print(f"   Generations: {generations}")
        print(f"   Target polyforms: {target_count}")
        
        population = generator._initialize_population(target_count, allowed_types)
        best_genome = None
        best_fitness = float('-inf')
        
        for gen in range(generations):
            fitness_scores = [generator._evaluate_fitness(genome) for genome in population]
            
            # Track convergence
            best_idx = fitness_scores.index(max(fitness_scores))
            window.record_generation(
                population[best_idx].polygons,
                fitness_scores,
                len(population)
            )
            
            gen_best_idx = fitness_scores.index(max(fitness_scores))
            if fitness_scores[gen_best_idx] > best_fitness:
                best_fitness = fitness_scores[gen_best_idx]
                best_genome = population[gen_best_idx].copy()
            
            if gen % 10 == 0 or gen == generations - 1:
                import numpy as np
                avg_fitness = np.mean(fitness_scores)
                print(f"   Gen {gen:3d}: Best={best_fitness:.3f}, Avg={avg_fitness:.3f}")
            
            parents = generator._tournament_selection(population, fitness_scores)
            offspring = []
            for i in range(0, len(parents) - 1, 2):
                child1, child2 = generator._crossover(parents[i], parents[i+1])
                offspring.append(generator._mutate(child1, allowed_types))
                offspring.append(generator._mutate(child2, allowed_types))
            
            import numpy as np
            elite = [population[i] for i in np.argsort(fitness_scores)[-generator.elite_size:]]
            
            population = elite + offspring[:generator.population_size - generator.elite_size]
            generator.generation += 1
        
        print(f"Evolution complete! Best fitness: {best_fitness:.3f}")
        generator.evolve = original_evolve
        return best_genome
    
    generator.evolve = evolve_with_tracking
    
    return window


def plot_convergence(history):
    """Visualize convergence history"""
    plt.figure(figsize=(10, 6))
    plt.plot(history['generation'], history['fitness'], 'b-o')
    plt.title('Convergence History')
    plt.xlabel('Generation')
    plt.ylabel('Fitness')
    plt.grid(True)
    plt.show()
