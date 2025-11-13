"""
Convergence Menu - Canonical N Tracking

Corrected version that tracks actual N (canonical polyform count estimator)
instead of population size.

N = T × n! / ∏c_j! × ∏a_j^c_j × symmetry_factor

This menu shows:
- How N evolves during assembly evolution
- Convergence of logN (log-space for stability)
- Relationship between diversity and N
- T parameter effects
"""

def print_canonical_theory():
    """Explain canonical N in simple terms."""
    print("""
╔═ CANONICAL N - THE POLYFORM COUNT ESTIMATOR ═════════════════════════════╗
│                                                                           │
│ N is NOT population size. It's a formula that estimates valid polyforms. │
│                                                                           │
│ FORMULA:                                                                  │
│   N = T × n! / ∏c_j! × ∏a_j^c_j × symmetry_factor                       │
│                                                                           │
│ COMPONENTS:                                                               │
│   T                    = Transformation parameter (orientation freedom)   │
│   n! / ∏c_j!          = Distinct permutation factor                      │
│   ∏a_j^c_j            = Product of polygon sides raised to counts        │
│   symmetry_factor     = Reduction for geometric indistinguishability     │
│                                                                           │
│ EXAMPLE: 2 squares + 1 triangle with T=1.1, no symmetry                 │
│                                                                           │
│   types = [(4,2), (3,1)]   # 2 squares, 1 triangle                       │
│   n = 2 + 1 = 3            # total 3 polygons                            │
│   n! = 6                   # permutations of 3 items                     │
│   ∏c_j! = 2! × 1! = 2      # but 2 squares are identical                 │
│   ∏a_j^c_j = 4² × 3¹ = 48  # side product                                │
│                                                                           │
│   N = 1.1 × 6 / 2 × 48 × 1.0 = 158.4                                    │
│                                                                           │
│ INTERPRETATION:                                                           │
│   → Assembly can generate ~158 distinct valid polyforms                  │
│   → Higher N = more degrees of freedom / valid configurations            │
│   → logN used for numerical stability (prevents overflow)                │
│                                                                           │
╚═══════════════════════════════════════════════════════════════════════════╝
    """)


def print_convergence_types():
    """Explain types of N convergence you'll see."""
    print("""
╔═ TYPES OF CANONICAL N CONVERGENCE ════════════════════════════════════════╗
│                                                                           │
│ 1. DIVERSITY-DRIVEN GROWTH                                               │
│    Start: [(4,1)] → N ≈ 4                                                │
│    Add:   [(3,1),(4,1)] → N ≈ 72  (jump!)                               │
│    Add:   [(3,2),(4,1)] → N ≈ 144                                        │
│    ├─ Reason: More polygon types = exponential N increase               │
│    └─ Key metric: Diversity index rises with N                          │
│                                                                           │
│ 2. T-DRIVEN CONVERGENCE                                                  │
│    Same assembly but T: 1.0 → 1.5                                       │
│    ├─ N: 72 → 108  (50% increase)                                       │
│    ├─ Reason: More transformation freedom                                │
│    └─ logN increases linearly with T                                     │
│                                                                           │
│ 3. SYMMETRY-SUPPRESSED CONVERGENCE                                       │
│    Assembly with full diversity, symmetry_factor:                        │
│    1.0 → 0.5                                                             │
│    ├─ N: 1e7 → 5e6  (50% decrease)                                      │
│    ├─ Reason: Geometric indistinguishability reduces count               │
│    └─ Occurs when assembly has repeating patterns                        │
│                                                                           │
│ 4. PLATEAU CONVERGENCE                                                   │
│    logN rises steeply at first, then flattens                            │
│    ├─ Early gens: New polygon types drive rapid N growth                 │
│    ├─ Later gens: Only T/symmetry adjustments                            │
│    └─ Indicates assembly reached "complexity ceiling"                    │
│                                                                           │
╚═══════════════════════════════════════════════════════════════════════════╝
    """)


def print_menu():
    """Main menu."""
    print("\n" + "="*80)
    print("  📊 CANONICAL N CONVERGENCE ANALYSIS MENU")
    print("="*80)
    
    print_canonical_theory()
    
    print("\n" + "-"*80)
    print("OPTIONS:")
    print("-"*80)
    print("""
  [1] View Convergence Types
  [2] Run Demo - Track N evolution
  [3] Understanding logN (log-space)
  [4] Relationship: Diversity vs N
  [5] T Parameter Effects
  [6] Symmetry Factor Effects
  [0] Exit
    """)


def print_logN_explanation():
    """Explain logN."""
    print("""
╔═ logN: LOG-SPACE CANONICAL N ═════════════════════════════════════════════╗
│                                                                           │
│ WHY USE logN?                                                             │
│   N can be huge (1e100+) → numerical overflow                            │
│   logN stays manageable → easier computation                             │
│                                                                           │
│ FORMULA:                                                                  │
│   logN = lnT + ln(n!) - ∑ln(c_j!) + ∑c_j·ln(a_j) + ln(symmetry_factor) │
│                                                                           │
│ INTERPRETATION OF VALUES:                                                │
│   logN ≤ 5     → N ≈ 150        (small assembly)                         │
│   logN ≈ 10    → N ≈ 22,000     (medium assembly)                        │
│   logN ≈ 15    → N ≈ 3.3 million (large assembly)                        │
│   logN ≈ 20    → N ≈ 485 billion (very large)                            │
│                                                                           │
│ CONVERGENCE CHECK:                                                        │
│   If logN increases steadily → Assembly gaining complexity               │
│   If logN plateaus          → No more new structure emerging             │
│   If logN decreases         → ⚠️ Assembly becoming degenerate            │
│                                                                           │
│ COMPARISON:                                                               │
│   logN(assembly A) = 12.5                                                │
│   logN(assembly B) = 13.2                                                │
│   → B is ~2x more complex (e^{13.2}/e^{12.5} ≈ 2.0)                     │
│                                                                           │
╚═══════════════════════════════════════════════════════════════════════════╝
    """)


def print_diversity_relationship():
    """Explain diversity vs N."""
    print("""
╔═ DIVERSITY vs CANONICAL N ════════════════════════════════════════════════╗
│                                                                           │
│ DIVERSITY INDEX measures polygon type variation (Shannon entropy):        │
│                                                                           │
│   diversity = -∑(p_i × ln(p_i))                                         │
│   where p_i = c_i / n (proportion of type i)                            │
│                                                                           │
│ RELATIONSHIP TO N:                                                        │
│   All 4-gons:          diversity = 0.00    → N low (boring)             │
│   3-gons & 4-gons:     diversity = 0.69    → N higher                   │
│   3,4,5,6-gons:        diversity = 1.39    → N much higher              │
│                                                                           │
│ WHAT THIS MEANS:                                                          │
│   Higher diversity usually drives higher N                               │
│   But T and symmetry also matter!                                        │
│                                                                           │
│ EXAMPLES:                                                                 │
│   ✓ Assembly diversifies → logN ↑ (positive correlation)                 │
│   ✗ Symmetry increases → logN ↓ (despite same diversity)                 │
│   ✓ T increases → logN ↑ (independent of diversity)                      │
│                                                                           │
╚═══════════════════════════════════════════════════════════════════════════╝
    """)


def print_T_effects():
    """Explain T parameter."""
    print("""
╔═ T PARAMETER: TRANSFORMATION EFFECTS ═════════════════════════════════════╗
│                                                                           │
│ T represents transformation/orientation freedom in polyform assembly     │
│                                                                           │
│ WHAT T ENCODES:                                                           │
│   - Rotation angles allowed                                              │
│   - Reflection symmetries                                                │
│   - Spatial orientation degrees of freedom                               │
│                                                                           │
│ TYPICAL VALUES:                                                           │
│   T = 1.0     → Minimal transformation (simple assembly)                │
│   T = 1.2     → Moderate (standard case)                                │
│   T = 1.5     → High (complex interactions)                             │
│   T > 2.0     → Very high (rare, highly constrained)                    │
│                                                                           │
│ EFFECT ON N:                                                              │
│   logN = ... + lnT + ...                                                 │
│   → logN scales linearly with T                                          │
│   → Doubling T roughly doubles N                                         │
│                                                                           │
│ CONVERGENCE PATTERN:                                                      │
│   Gen 0: T = 1.0,  logN = 5.2                                            │
│   Gen 10: T = 1.1, logN = 5.3  (slight increase)                        │
│   Gen 20: T = 1.2, logN = 5.5  (steady growth)                          │
│   Gen 30: T = 1.5, logN = 6.1  (T becoming dominant)                    │
│                                                                           │
╚═══════════════════════════════════════════════════════════════════════════╝
    """)


def print_symmetry_effects():
    """Explain symmetry factor."""
    print("""
╔═ SYMMETRY FACTOR: GEOMETRIC INDISTINGUISHABILITY ═════════════════════════╗
│                                                                           │
│ symmetry_factor ≤ 1 reduces N when assembly has repeating patterns       │
│                                                                           │
│ HOW IT WORKS:                                                             │
│   If assembly can be rotated/reflected without changing structure         │
│   → It represents same configuration multiple ways                       │
│   → symmetry_factor accounts for this over-counting                      │
│                                                                           │
│ TYPICAL SCENARIOS:                                                        │
│   symmetry_factor = 1.0    → No geometric symmetry (generic)             │
│   symmetry_factor = 0.95   → Slight diagonal symmetry                    │
│   symmetry_factor = 0.5    → Mirror symmetry (2-fold)                    │
│   symmetry_factor = 0.25   → 4-fold rotational symmetry                  │
│                                                                           │
│ EXAMPLE EFFECT:                                                           │
│   Assembly X (no symmetry):                                               │
│     logN = 12.5 → N ≈ 3.7 million                                        │
│                                                                           │
│   Same assembly Y (mirror symmetry, 0.5 factor):                         │
│     logN = 12.5 + ln(0.5) = 12.5 - 0.69 = 11.81                         │
│     → N ≈ 1.3 million  (64% reduction)                                   │
│                                                                           │
│ INTERPRETATION:                                                           │
│   Higher symmetry → Lower N                                              │
│   Asymmetric assemblies have more degrees of freedom                     │
│   Symmetric assemblies are more constrained but more elegant             │
│                                                                           │
╚═══════════════════════════════════════════════════════════════════════════╝
    """)


def run_menu():
    """Run interactive menu."""
    while True:
        print_menu()
        
        choice = input("\nEnter choice [0-6]: ").strip()
        
        if choice == '0':
            print("\n👋 Exiting canonical N menu.\n")
            break
        elif choice == '1':
            print_convergence_types()
        elif choice == '2':
            print("\n🚀 Running demo...\n")
            from convergence_canonical_tracker import demo_canonical_tracking
            demo_canonical_tracking()
        elif choice == '3':
            print_logN_explanation()
        elif choice == '4':
            print_diversity_relationship()
        elif choice == '5':
            print_T_effects()
        elif choice == '6':
            print_symmetry_effects()
        else:
            print("❌ Invalid choice.")
        
        input("\nPress Enter to continue...")


if __name__ == "__main__":
    run_menu()
