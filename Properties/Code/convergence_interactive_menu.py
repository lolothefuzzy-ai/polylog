"""
Interactive Convergence Menu - ASCII-based N selection and visualization

Features:
- Interactive menu to select/calculate N
- N determination strategies (static, dynamic, assembly-based)
- View convergence for selected N ranges
- Compare metrics across different population sizes
"""

from dataclasses import dataclass
from typing import Dict, List

import numpy as np


@dataclass
class PopulationConfig:
    """Population size configuration."""
    name: str
    population_sizes: List[int]
    rationale: str


class PopulationSizingCalculator:
    """Determine optimal N based on different strategies."""
    
    @staticmethod
    def static_n(size: int) -> List[int]:
        """Static N: User specifies fixed population size."""
        return [size]
    
    @staticmethod
    def range_n(min_n: int, max_n: int, steps: int = 4) -> List[int]:
        """Range N: Logarithmic distribution across min-max."""
        if steps < 2:
            steps = 2
        return [int(x) for x in np.logspace(np.log10(min_n), np.log10(max_n), steps)]
    
    @staticmethod
    def assembly_based_n(num_polygons: int, target_complexity: float = 0.5) -> List[int]:
        """
        Assembly-based N: Calculate N based on assembly size.
        
        Theory:
        - N = k * num_polygons / (1 - convergence_target)
        - Small assemblies (3-5 polygons): N = 8-15
        - Medium assemblies (5-15 polygons): N = 15-50
        - Large assemblies (15+ polygons): N = 50-200+
        
        Args:
            num_polygons: Expected number of polygons in assembly
            target_complexity: 0-1, higher = more complexity/diversity needed
        
        Returns:
            Recommended N value
        """
        # Base multiplier
        k = 3
        
        # Complexity factor (higher complexity needs larger population)
        complexity_factor = 1 + target_complexity
        
        # Calculate base N
        base_n = int(k * num_polygons * complexity_factor)
        
        # Clamp to reasonable ranges
        min_n = max(5, int(num_polygons * 1.5))
        max_n = max(min_n + 1, int(num_polygons * 15))
        
        return max(min_n, min(max_n, base_n))
    
    @staticmethod
    def adaptive_n(assembly_state: Dict) -> List[int]:
        """
        Adaptive N: Calculate based on current assembly state metrics.
        
        Adapts N based on:
        - Number of polygons (diversity indicator)
        - Number of bonds (connectivity indicator)
        - Fitness plateau detection
        """
        num_polygons = assembly_state.get('num_polygons', 0)
        num_bonds = assembly_state.get('num_bonds', 0)
        stagnation_gens = assembly_state.get('stagnation_gens', 0)
        
        # Connectivity ratio
        connectivity = num_bonds / max(num_polygons, 1)
        
        # If highly connected, can use smaller population
        if connectivity > 2.0:
            n_factor = 0.8
        elif connectivity > 1.0:
            n_factor = 1.0
        else:
            n_factor = 1.5  # Sparse - need more diversity
        
        # If stagnating, increase N to escape local optima
        if stagnation_gens > 50:
            n_factor *= 1.3
        
        base_n = PopulationSizingCalculator.assembly_based_n(num_polygons, 0.5)
        final_n = int(base_n * n_factor)
        
        return max(5, final_n)
    
    @staticmethod
    def explain_n(n: int, num_polygons: int) -> str:
        """Explain why N was chosen."""
        if n < 15:
            speed_char = "⚡"
            reason = "Small & fast"
        elif n < 50:
            speed_char = "⚙️"
            reason = "Balanced"
        else:
            speed_char = "🔍"
            reason = "Large & thorough"
        
        return f"{speed_char} N={n:3d} ({reason}) for ~{num_polygons} polygons"


class InteractiveConvergenceMenu:
    """Interactive menu for N selection and convergence viewing."""
    
    def __init__(self):
        self.selected_configs: List[PopulationConfig] = []
        self.calc = PopulationSizingCalculator()
        
        # Pre-defined configurations
        self.presets = {
            'fast': PopulationConfig(
                name='Fast (Small N)',
                population_sizes=[10, 15, 20],
                rationale='Quick convergence, finds local optima fast'
            ),
            'balanced': PopulationConfig(
                name='Balanced (Medium N)',
                population_sizes=[30, 40, 50],
                rationale='Good exploration-exploitation trade-off'
            ),
            'thorough': PopulationConfig(
                name='Thorough (Large N)',
                population_sizes=[80, 100, 150],
                rationale='Better final solutions, more computation'
            ),
            'custom_range': PopulationConfig(
                name='Custom Range (User-defined)',
                population_sizes=[],
                rationale='User specifies min and max N'
            ),
            'assembly_based': PopulationConfig(
                name='Assembly-Based (Auto)',
                population_sizes=[],
                rationale='N calculated from assembly complexity'
            ),
        }
    
    def print_header(self):
        """Print menu header."""
        print("\n" + "="*80)
        print("  📊 CONVERGENCE INTERACTIVE MENU - Population Size (N) Selection")
        print("="*80)
    
    def print_theory(self):
        """Print theory about N."""
        print("""
╔═ POPULATION SIZE (N) THEORY ═══════════════════════════════════════════╗
│                                                                         │
│ N = population size in evolutionary algorithm                          │
│                                                                         │
│ SMALL N (5-20):                                                         │
│  ├─ Pros: Fast convergence, low computation                            │
│  └─ Cons: Gets stuck in local optima, limited diversity               │
│                                                                         │
│ MEDIUM N (30-60):                                                       │
│  ├─ Pros: Balanced speed/quality, maintains diversity                  │
│  └─ Cons: Moderate computation                                         │
│                                                                         │
│ LARGE N (100+):                                                         │
│  ├─ Pros: Better solutions, explores more thoroughly                   │
│  └─ Cons: Slow convergence, high computation                           │
│                                                                         │
│ N CALCULATION (Assembly-Based):                                        │
│  N = k × num_polygons × (1 + complexity) / (1 - target_convergence)   │
│                                                                         │
│  Example: 8 polygons, medium complexity                                │
│    → N ≈ 3 × 8 × 1.5 = 36 (use 30-50)                                 │
│                                                                         │
╚═════════════════════════════════════════════════════════════════════════╝
        """)
    
    def print_menu(self):
        """Print main menu options."""
        print("\n" + "-"*80)
        print("SELECT POPULATION STRATEGY:")
        print("-"*80)
        
        options = [
            ('1', 'Fast (N=10-20)', 'Quick convergence, local optima'),
            ('2', 'Balanced (N=30-50)', 'Good exploration-exploitation'),
            ('3', 'Thorough (N=80-150)', 'Better solutions, more time'),
            ('4', 'Custom Range', 'Specify min and max N'),
            ('5', 'Assembly-Based', 'Auto-calculate from assembly size'),
            ('6', 'Adaptive', 'Dynamic N based on convergence state'),
            ('7', 'Compare All', 'Run convergence for all presets'),
            ('0', 'Exit', 'Quit menu'),
        ]
        
        for code, name, desc in options:
            print(f"  [{code}] {name:25s} - {desc}")
    
    def get_user_choice(self) -> str:
        """Get user input."""
        print("\n" + "-"*80)
        choice = input("Enter choice [0-7]: ").strip()
        return choice
    
    def handle_fast(self):
        """Handle fast preset."""
        config = self.presets['fast']
        self.selected_configs = [config]
        self.print_selection(config)
    
    def handle_balanced(self):
        """Handle balanced preset."""
        config = self.presets['balanced']
        self.selected_configs = [config]
        self.print_selection(config)
    
    def handle_thorough(self):
        """Handle thorough preset."""
        config = self.presets['thorough']
        self.selected_configs = [config]
        self.print_selection(config)
    
    def handle_custom_range(self):
        """Get custom N range from user."""
        try:
            min_n = int(input("  Enter minimum N (default 10): ") or "10")
            max_n = int(input("  Enter maximum N (default 100): ") or "100")
            steps = int(input("  Number of steps (default 4): ") or "4")
            
            pop_sizes = self.calc.range_n(min_n, max_n, steps)
            
            config = PopulationConfig(
                name=f'Custom Range ({min_n}-{max_n})',
                population_sizes=pop_sizes,
                rationale=f'User-specified range with {steps} logarithmic steps'
            )
            self.selected_configs = [config]
            self.print_selection(config)
        except ValueError:
            print("  ❌ Invalid input. Please enter integers.")
    
    def handle_assembly_based(self):
        """Calculate N based on assembly."""
        try:
            num_polygons = int(input("  Enter expected number of polygons: "))
            complexity = float(input("  Enter target complexity (0-1, default 0.5): ") or "0.5")
            
            n = self.calc.assembly_based_n(num_polygons, complexity)
            explanation = self.calc.explain_n(n, num_polygons)
            
            config = PopulationConfig(
                name=f'Assembly-Based N={n}',
                population_sizes=[n],
                rationale=explanation
            )
            self.selected_configs = [config]
            self.print_selection(config)
        except ValueError:
            print("  ❌ Invalid input.")
    
    def handle_adaptive(self):
        """Calculate adaptive N."""
        print("""
  Enter assembly state (leave blank for defaults):
        """)
        try:
            num_polygons = int(input("  Polygons (default 8): ") or "8")
            num_bonds = int(input("  Bonds (default 8): ") or "8")
            stagnation = int(input("  Stagnation generations (default 0): ") or "0")
            
            state = {
                'num_polygons': num_polygons,
                'num_bonds': num_bonds,
                'stagnation_gens': stagnation
            }
            
            n = self.calc.adaptive_n(state)
            explanation = self.calc.explain_n(n, num_polygons)
            
            config = PopulationConfig(
                name=f'Adaptive N={n}',
                population_sizes=[n],
                rationale=explanation
            )
            self.selected_configs = [config]
            self.print_selection(config)
        except ValueError:
            print("  ❌ Invalid input.")
    
    def handle_compare_all(self):
        """Compare all presets."""
        self.selected_configs = list(self.presets.values())
        print("\n" + "="*80)
        print("COMPARISON OF ALL PRESETS:")
        print("="*80)
        for config in self.selected_configs:
            self.print_selection(config)
    
    def print_selection(self, config: PopulationConfig):
        """Print selected configuration."""
        print(f"\n✓ Selected: {config.name}")
        print(f"  Rationale: {config.rationale}")
        print(f"  Population Sizes: {config.population_sizes}")
        
        # Show convergence prediction
        print(f"\n  Expected Convergence Behavior:")
        for n in config.population_sizes:
            if n < 20:
                speed = "⚡ Fast"
                quality = "Lower"
                gens = "~15-30"
            elif n < 60:
                speed = "⚙️  Medium"
                quality = "Good"
                gens = "~30-60"
            else:
                speed = "🔍 Slow"
                quality = "High"
                gens = "~60-100+"
            
            print(f"    N={n:3d}: {speed:10s} | Quality: {quality:5s} | ~{gens} generations")
    
    def run_interactive(self):
        """Run interactive menu loop."""
        while True:
            self.print_header()
            self.print_theory()
            self.print_menu()
            
            choice = self.get_user_choice()
            
            if choice == '0':
                print("\n👋 Exiting convergence menu.")
                break
            elif choice == '1':
                self.handle_fast()
            elif choice == '2':
                self.handle_balanced()
            elif choice == '3':
                self.handle_thorough()
            elif choice == '4':
                self.handle_custom_range()
            elif choice == '5':
                self.handle_assembly_based()
            elif choice == '6':
                self.handle_adaptive()
            elif choice == '7':
                self.handle_compare_all()
            else:
                print("  ❌ Invalid choice. Try again.")
            
            if self.selected_configs and choice != '7':
                print("\n" + "="*80)
                proceed = input("Proceed with these settings? (y/n): ").strip().lower()
                if proceed == 'y':
                    print(f"\n✅ Configuration confirmed. Ready to run convergence analysis.")
                    print(f"\nYou can now pass these N values to the convergence visualizer:")
                    for config in self.selected_configs:
                        print(f"  N values: {config.population_sizes}")
                    break


def main():
    """Main entry point."""
    menu = InteractiveConvergenceMenu()
    menu.run_interactive()


if __name__ == "__main__":
    main()
