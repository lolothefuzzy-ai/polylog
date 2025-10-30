"""
Simplified ASCII Convergence Viewer - No GUI required

Displays T/N convergence patterns as text graphs that update in the terminal.
Perfect for monitoring without loading PyQtGraph/PySide6.
"""

import numpy as np
from typing import Dict, List, Tuple
from collections import defaultdict
import time
from dataclasses import dataclass


@dataclass
class SimpleMetric:
    """Lightweight metric storage."""
    generation: int
    t_variance: float
    fitness_best: float
    fitness_avg: float


class ASCIIConvergenceViewer:
    """Text-based convergence visualization."""
    
    def __init__(self, width: int = 80, height: int = 20):
        self.width = width
        self.height = height
        self.data: Dict[int, List[SimpleMetric]] = defaultdict(list)
    
    def add_data(self, pop_size: int, generation: int, 
                 t_variance: float, fitness_best: float, fitness_avg: float):
        """Add a single data point."""
        self.data[pop_size].append(SimpleMetric(
            generation=generation,
            t_variance=t_variance,
            fitness_best=fitness_best,
            fitness_avg=fitness_avg
        ))
    
    def plot_fitness_curve(self) -> str:
        """Generate ASCII plot of fitness over generations."""
        if not self.data:
            return "No data yet"
        
        lines = []
        lines.append("\n" + "="*self.width)
        lines.append("FITNESS CONVERGENCE (Best Fitness vs Generation)")
        lines.append("="*self.width)
        
        # Get all data sorted by population size
        pop_sizes = sorted(self.data.keys())
        
        # Find max generation and fitness
        max_gen = max([max([m.generation for m in metrics]) 
                      for metrics in self.data.values()])
        max_fitness = max([max([m.fitness_best for m in metrics]) 
                          for metrics in self.data.values()])
        min_fitness = min([min([m.fitness_best for m in metrics]) 
                          for metrics in self.data.values()])
        
        # Create grid
        grid = [[' ' for _ in range(self.width)] for _ in range(self.height)]
        
        # Plot each population size with different character
        chars = ['█', '▓', '▒', '░', '═', '─', '┃', '┋']
        colors_map = {
            10: '█', 20: '▓', 30: '▒', 50: '░', 
            100: '═', 200: '─', 500: '┃', 1000: '┋'
        }
        
        for idx, pop_size in enumerate(pop_sizes):
            char = colors_map.get(pop_size, chars[idx % len(chars)])
            metrics = self.data[pop_size]
            
            for metric in metrics:
                # Map generation to x, fitness to y
                x = int((metric.generation / max(max_gen, 1)) * (self.width - 1))
                y = int((1 - (metric.fitness_best - min_fitness) / 
                        max(max_fitness - min_fitness, 0.001)) * (self.height - 1))
                
                if 0 <= x < self.width and 0 <= y < self.height:
                    grid[y][x] = char
        
        # Add axis labels
        for row in grid:
            lines.append('│' + ''.join(row) + '│')
        
        lines.append("└" + "─"*self.width + "┘")
        lines.append(f"X: Generations (0-{max_gen})")
        lines.append(f"Y: Fitness ({min_fitness:.2f}-{max_fitness:.2f})")
        
        # Add legend
        lines.append("\nLegend:")
        for pop_size in pop_sizes:
            char = colors_map.get(pop_size, '█')
            lines.append(f"  {char} = N={pop_size}")
        
        return '\n'.join(lines)
    
    def plot_variance_curve(self, log_scale: bool = True) -> str:
        """Generate ASCII plot of variance over generations."""
        if not self.data:
            return "No data yet"
        
        lines = []
        lines.append("\n" + "="*self.width)
        mode = "(Log Scale)" if log_scale else "(Linear)"
        lines.append(f"VARIANCE CONVERGENCE {mode}")
        lines.append("="*self.width)
        
        pop_sizes = sorted(self.data.keys())
        
        max_gen = max([max([m.generation for m in metrics]) 
                      for metrics in self.data.values()])
        variances = []
        for metrics in self.data.values():
            variances.extend([m.t_variance for m in metrics])
        
        if log_scale:
            variances = [np.log10(max(v, 1e-6)) for v in variances]
            max_var = max(variances)
            min_var = min(variances)
        else:
            max_var = max(variances)
            min_var = min(variances)
        
        grid = [[' ' for _ in range(self.width)] for _ in range(self.height)]
        
        chars = ['█', '▓', '▒', '░', '═', '─', '┃', '┋']
        colors_map = {10: '█', 20: '▓', 30: '▒', 50: '░', 100: '═'}
        
        for idx, pop_size in enumerate(pop_sizes):
            char = colors_map.get(pop_size, chars[idx % len(chars)])
            metrics = self.data[pop_size]
            
            for metric in metrics:
                x = int((metric.generation / max(max_gen, 1)) * (self.width - 1))
                
                var = metric.t_variance
                if log_scale:
                    var = np.log10(max(var, 1e-6))
                
                y = int((1 - (var - min_var) / max(max_var - min_var, 0.001)) 
                       * (self.height - 1))
                
                if 0 <= x < self.width and 0 <= y < self.height:
                    grid[y][x] = char
        
        for row in grid:
            lines.append('│' + ''.join(row) + '│')
        
        lines.append("└" + "─"*self.width + "┘")
        
        if log_scale:
            lines.append(f"X: Generations (0-{max_gen})")
            lines.append(f"Y: log₁₀(Variance) ({min_var:.2f}-{max_var:.2f})")
        else:
            lines.append(f"X: Generations (0-{max_gen})")
            lines.append(f"Y: Variance ({min_var:.4f}-{max_var:.4f})")
        
        lines.append("\nLegend:")
        for pop_size in pop_sizes:
            char = colors_map.get(pop_size, '█')
            lines.append(f"  {char} = N={pop_size}")
        
        return '\n'.join(lines)
    
    def print_statistics(self) -> str:
        """Print summary statistics."""
        if not self.data:
            return "No data yet"
        
        lines = []
        lines.append("\n" + "="*self.width)
        lines.append("STATISTICS SUMMARY")
        lines.append("="*self.width)
        
        for pop_size in sorted(self.data.keys()):
            metrics = self.data[pop_size]
            
            fitnesses = [m.fitness_best for m in metrics]
            variances = [m.t_variance for m in metrics]
            
            lines.append(f"\nPopulation Size N={pop_size}:")
            lines.append(f"  Generations:        {len(metrics)}")
            lines.append(f"  Initial Fitness:    {fitnesses[0]:.4f}")
            lines.append(f"  Final Fitness:      {fitnesses[-1]:.4f}")
            lines.append(f"  Fitness Gain:       {fitnesses[-1] - fitnesses[0]:+.4f}")
            lines.append(f"  Initial Variance:   {variances[0]:.4e}")
            lines.append(f"  Final Variance:     {variances[-1]:.4e}")
            lines.append(f"  Variance Reduction: {(1 - variances[-1]/max(variances[0], 1e-6))*100:.1f}%")
            
            # Detect convergence point (when variance stops improving significantly)
            convergence_gen = None
            for i in range(len(variances)-10, 0, -1):
                avg_recent = np.mean(variances[i:])
                if variances[i] > avg_recent * 1.1:  # Stopped improving
                    convergence_gen = i
                    break
            
            if convergence_gen:
                lines.append(f"  Convergence @ Gen:  {convergence_gen}")
            
            # Best and worst fitness in population
            avg_fitness = np.mean([m.fitness_avg for m in metrics])
            lines.append(f"  Avg Population Fit: {avg_fitness:.4f}")
        
        return '\n'.join(lines)
    
    def print_heatmap(self) -> str:
        """Print convergence heatmap."""
        if not self.data:
            return "No data yet"
        
        lines = []
        lines.append("\n" + "="*self.width)
        lines.append("CONVERGENCE HEATMAP (Gen x PopSize)")
        lines.append("="*self.width)
        
        pop_sizes = sorted(self.data.keys())
        max_gen = max([max([m.generation for m in metrics]) 
                      for metrics in self.data.values()])
        
        # Build heatmap
        intensity_chars = [' ', '░', '▒', '▓', '█']
        
        # Header
        header = "  Gen: "
        for g in range(0, max_gen + 1, max(1, max_gen // 30)):
            header += f"{g:2d}"
        lines.append(header)
        
        # Rows for each population size
        for pop_size in pop_sizes:
            metrics = self.data[pop_size]
            row = f"N={pop_size:4d} │"
            
            fitness_dict = {m.generation: m.fitness_best for m in metrics}
            max_fitness = max([m.fitness_best for m in metrics])
            min_fitness = min([m.fitness_best for m in metrics])
            
            for g in range(0, max_gen + 1, max(1, max_gen // 30)):
                if g in fitness_dict:
                    # Map fitness to intensity
                    normalized = (fitness_dict[g] - min_fitness) / max(max_fitness - min_fitness, 0.001)
                    idx = min(4, int(normalized * 5))
                    row += intensity_chars[idx]
                else:
                    row += ' '
            
            row += '│'
            lines.append(row)
        
        lines.append(f"Color intensity = Fitness level (darker = better)\n")
        
        return '\n'.join(lines)
    
    def print_all(self) -> str:
        """Print all visualizations."""
        output = []
        output.append(self.plot_fitness_curve())
        output.append(self.plot_variance_curve(log_scale=True))
        output.append(self.print_heatmap())
        output.append(self.print_statistics())
        return '\n'.join(output)
    
    def clear(self):
        """Clear all data."""
        self.data.clear()


def demo_convergence():
    """Demo showing what typical convergence looks like."""
    
    viewer = ASCIIConvergenceViewer()
    
    print("\n📊 CONVERGENCE ASCII VIEWER DEMO")
    print("="*80)
    print("Simulating evolutionary convergence across population sizes...")
    print()
    
    # Simulate data for different population sizes
    pop_sizes = [10, 20, 30, 50]
    
    for pop_size in pop_sizes:
        print(f"Generating N={pop_size} data...", end=' ', flush=True)
        
        convergence_speed = 0.015 * (50 / pop_size)
        final_fitness = 0.1 + (pop_size / 100) * 0.3
        initial_variance = 5.0 + (20 / pop_size) * 2
        
        for gen in range(100):
            t_variance = initial_variance * np.exp(-convergence_speed * gen)
            
            if gen > 0 and gen % 20 == 0:
                t_variance *= 0.3
            
            base_fitness = final_fitness * (1 / (1 + np.exp(-0.08 * (gen - 30))))
            fitness_best = 0.3 + base_fitness + np.random.normal(0, 0.02)
            fitness_best = max(0.3, min(0.95, fitness_best))
            
            fitness_avg = fitness_best * 0.8 + np.random.normal(0, 0.03)
            
            viewer.add_data(pop_size, gen, t_variance, fitness_best, fitness_avg)
        
        print("✓")
    
    # Print visualizations
    print(viewer.print_all())
    
    print("\n" + "="*80)
    print("INTERPRETATION GUIDE:")
    print("="*80)
    print("""
█ = N=10   (Small population - fast convergence, lower final fitness)
▓ = N=20   (Small-medium - balanced speed and quality)
▒ = N=30   (Medium - good exploration)
░ = N=50   (Medium-large - thorough search, high final fitness)

FITNESS GRAPH:
  - Top-left to bottom-right = convergence progressing
  - Horizontal plateaus = population converged (stopped improving)
  - Small N reaches plateau first (local optima)
  - Large N climbs higher before plateauing

VARIANCE GRAPH (log scale):
  - Steep drops = rapid position uniformity
  - Small N shows sharp cliff early on
  - Large N shows gradual exponential decline
  - Lower final variance = better spatial organization

HEATMAP:
  - Darker = better fitness
  - Shows which N reaches quality solutions fastest
  - Diagonal ridges = steady improvement
  - Flat areas = convergence plateau

Key Insight: Larger N = slower convergence but better final solutions
    """)


if __name__ == "__main__":
    demo_convergence()
