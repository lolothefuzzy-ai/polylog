"""
Demo: N Population Sizing Calculator
Shows how N is determined based on different strategies.
"""

from convergence_interactive_menu import PopulationSizingCalculator


def demo():
    """Run demonstration of N calculation."""
    calc = PopulationSizingCalculator()
    
    print("\n" + "="*80)
    print("  🔢 POPULATION SIZE (N) CALCULATION DEMO")
    print("="*80)
    
    # ═══════════════════════════════════════════════════════════════
    # 1. STATIC N
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "-"*80)
    print("1. STATIC N (Fixed population size)")
    print("-"*80)
    
    n = calc.static_n(30)
    print(f"  Input: User specifies N=30")
    print(f"  Output: {n}")
    print(f"  Use case: Known good population size for your problem")
    
    # ═══════════════════════════════════════════════════════════════
    # 2. RANGE N
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "-"*80)
    print("2. RANGE N (Logarithmic distribution)")
    print("-"*80)
    
    n_range = calc.range_n(10, 200, steps=5)
    print(f"  Input: Min=10, Max=200, Steps=5")
    print(f"  Output: {n_range}")
    print(f"  Formula: Logarithmic scale from 10 to 200")
    print(f"  Use case: Compare convergence across wide N range")
    
    # ═══════════════════════════════════════════════════════════════
    # 3. ASSEMBLY-BASED N
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "-"*80)
    print("3. ASSEMBLY-BASED N (Calculate from assembly complexity)")
    print("-"*80)
    
    print("\n  Formula:")
    print("    N = k × num_polygons × (1 + complexity)")
    print("    where k=3 (base multiplier)")
    print("          complexity = 0-1 (0=simple, 1=complex)")
    print()
    
    test_cases = [
        (3, 0.3, "Simple 3-polygon, low complexity"),
        (8, 0.5, "Medium 8-polygon, moderate complexity"),
        (15, 0.8, "Large 15-polygon, high complexity"),
        (20, 1.0, "Very large 20-polygon, very high complexity"),
    ]
    
    for num_poly, complexity, description in test_cases:
        n = calc.assembly_based_n(num_poly, complexity)
        explanation = calc.explain_n(n, num_poly)
        print(f"  {description}")
        print(f"    N = 3 × {num_poly} × (1 + {complexity}) = {n}")
        print(f"    {explanation}")
        print()
    
    # ═══════════════════════════════════════════════════════════════
    # 4. ADAPTIVE N
    # ═══════════════════════════════════════════════════════════════
    print("-"*80)
    print("4. ADAPTIVE N (Based on convergence state)")
    print("-"*80)
    
    print("\n  Adapts N based on:")
    print("    - Connectivity ratio (bonds/polygons)")
    print("    - Stagnation detection (generations without improvement)")
    print()
    
    scenarios = [
        {
            'name': 'Sparse assembly (few bonds)',
            'state': {'num_polygons': 10, 'num_bonds': 5, 'stagnation_gens': 0},
        },
        {
            'name': 'Well-connected assembly',
            'state': {'num_polygons': 10, 'num_bonds': 25, 'stagnation_gens': 0},
        },
        {
            'name': 'Stagnating assembly (not improving)',
            'state': {'num_polygons': 10, 'num_bonds': 15, 'stagnation_gens': 80},
        },
    ]
    
    for scenario in scenarios:
        n = calc.adaptive_n(scenario['state'])
        explanation = calc.explain_n(n, scenario['state']['num_polygons'])
        
        print(f"  {scenario['name']}")
        print(f"    Polygons: {scenario['state']['num_polygons']}")
        print(f"    Bonds: {scenario['state']['num_bonds']}")
        print(f"    Stagnation: {scenario['state']['stagnation_gens']} gens")
        print(f"    Recommended N: {n}")
        print(f"    {explanation}")
        print()
    
    # ═══════════════════════════════════════════════════════════════
    # COMPARISON TABLE
    # ═══════════════════════════════════════════════════════════════
    print("-"*80)
    print("COMPARISON TABLE: When to use each strategy")
    print("-"*80)
    
    comparison = f"""
    ┌─────────────────┬──────────────────┬─────────────────────────────────┐
    │ Strategy        │ Best For         │ Output                          │
    ├─────────────────┼──────────────────┼─────────────────────────────────┤
    │ STATIC          │ Known N values   │ Single N: {calc.static_n(30)}                  │
    │ RANGE           │ Comparison study │ Multiple N: {calc.range_n(10, 100, 4)}        │
    │ ASSEMBLY-BASED  │ Auto-sizing      │ Single N: ~24 (8 polys @ 0.5)   │
    │ ADAPTIVE        │ Real-time adjust │ Single N: adaptive to state     │
    ├─────────────────┼──────────────────┼─────────────────────────────────┤
    │ When to choose: │                  │                                 │
    │ STATIC          │ You know it works│ Use fixed value each time       │
    │ RANGE           │ Benchmarking     │ Test multiple N concurrently    │
    │ ASSEMBLY-BASED  │ New assemblies   │ Auto-calc from problem size     │
    │ ADAPTIVE        │ Online tuning    │ Adjust N during evolution       │
    └─────────────────┴──────────────────┴─────────────────────────────────┘
    """
    
    print(comparison)
    
    # ═══════════════════════════════════════════════════════════════
    # RECOMMENDATION ENGINE
    # ═══════════════════════════════════════════════════════════════
    print("-"*80)
    print("QUICK RECOMMENDATION ENGINE")
    print("-"*80)
    
    print("""
  Q: How many polygons do you expect in final assembly?
  
  <5 polygons?
    → Use N=10-20 (FAST) | Formula: N = 8-15
  
  5-10 polygons?
    → Use N=20-40 (BALANCED) | Formula: N = 15-40
  
  10-20 polygons?
    → Use N=40-80 (THOROUGH) | Formula: N = 40-120
  
  20+ polygons?
    → Use N=100+ (VERY THOROUGH) | Formula: N = 100-300+
  
  Need to compare multiple?
    → Use RANGE strategy: range_n(10, 200, steps=4)
      → Output: [10, 44, 97, 200]
    """)
    
    print("\n" + "="*80)
    print("✓ Demo complete. Run convergence_interactive_menu.py for interactive mode.")
    print("="*80 + "\n")


if __name__ == "__main__":
    demo()
