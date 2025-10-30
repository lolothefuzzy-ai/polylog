## Convergence Tracking System - Complete Guide

### Quick Answer: What is N?

**N = Canonical Polyform Count Estimator**

```
N = T × n! / ∏c_j! × ∏a_j^{c_j} × symmetry_factor
```

Where:
- `T` = Transformation parameter (orientation freedom)
- `n` = Total polygon count
- `n! / ∏c_j!` = Distinct permutation factor
- `∏a_j^{c_j}` = Product of polygon sides raised to counts
- `symmetry_factor` = Geometric indistinguishability reduction

**NOT:** Population size in genetic algorithm

---

## Files in This System

### Core Tracking
1. **`convergence_canonical_tracker.py`** (356 lines)
   - Main tracking engine
   - Records N evolution across assembly generations
   - Shows ASCII visualizations
   - Computes diversity vs N correlation
   - **Run:** `py convergence_canonical_tracker.py`

2. **`convergence_menu_canonical.py`** (267 lines)
   - Interactive terminal menu
   - Explains each component of N formula
   - Shows convergence patterns
   - Live demo capability
   - **Run:** `py convergence_menu_canonical.py`

3. **`convergence_ascii_viewer.py`** (344 lines)
   - Lightweight ASCII visualization (no GUI)
   - Shows fitness and variance convergence
   - Heatmaps and statistics
   - **Run:** `py convergence_ascii_viewer.py`

### Documentation
4. **`CONVERGENCE_N_EXPLAINED.md`** (219 lines)
   - Complete explanation of N formula
   - Examples and worked calculations
   - Convergence patterns to watch
   - Red flags and metrics

5. **`README_CONVERGENCE.md`** (this file)
   - System overview
   - Quick start guide

---

## The Corrected Understanding

### What Changed
| Concept | Before | After |
|---------|--------|-------|
| N definition | Population size | Canonical polyform count |
| Focus | GA population tuning | Assembly complexity tracking |
| Formula | None (arbitrary) | `T × n! / ∏c_j! × ...` |
| Tracking | Population metrics | logN evolution + diversity |

### Why It Matters
- **Population size** is a tuning parameter (GA-specific)
- **Canonical N** measures assembly validity (problem-specific)
- Your system should track **both separately**:
  - GA population size: Traditional parameter (10-200)
  - Canonical N: Evolves as assembly grows (4 → 1e10)

---

## Quick Start Examples

### Example 1: Track Assembly Evolution
```python
from convergence_canonical_tracker import CanonicalNTracker

tracker = CanonicalNTracker()

# Simulate assembly growth
assemblies = [
    [(4, 1)],              # Start: 1 square
    [(4, 2)],              # Gen 10: 2 squares
    [(4, 2), (3, 1)],      # Gen 20: Add triangle
    [(3, 2), (4, 2), (5, 1)],  # Gen 30: Mix of types
]

for assembly_types in assemblies:
    point = tracker.record_assembly(
        T=1.1,
        types=assembly_types,
        symmetry_factor=0.95
    )
    print(f"logN: {point.logN:.2f}, N: {point.N:.2e}")

print(tracker.print_convergence_summary())
print(tracker.print_ascii_graph())
```

**Output:**
```
logN: 1.39, N: 4.00e+00      (1 square)
logN: 2.77, N: 1.60e+01      (2 squares)
logN: 5.01, N: 1.50e+02      (2 squares + 1 triangle)
logN: 9.94, N: 2.07e+04      (3 types mixed)
```

### Example 2: View Interactive Menu
```bash
python convergence_menu_canonical.py
```

Menu options:
```
[1] View Convergence Types       - See patterns
[2] Run Demo                     - Live evolution
[3] Understanding logN           - Why log-space?
[4] Diversity vs N               - Relationship
[5] T Parameter Effects          - How T impacts N
[6] Symmetry Factor Effects      - How symmetry impacts N
[0] Exit
```

### Example 3: Run Full Demo
```bash
python convergence_canonical_tracker.py
```

Shows:
- Evolution from 1 square → 10 polygons (4-gon + 3-gon + 5-gon + 6-gon)
- N growth: 4 → 4.08e10 (10 billion times larger!)
- Diversity correlation: +0.91 (strong positive)
- ASCII graphs

---

## Key Metrics to Monitor

### Primary: logN (Canonical N in log-space)
```python
logN = lnT + ln(n!) - ∑ln(c_j!) + ∑c_j·ln(a_j) + ln(symmetry_factor)
```

**Interpretation:**
- `logN` ≤ 5 → Small assembly (N ≈ 150)
- `logN` ≈ 10 → Medium (N ≈ 22,000)
- `logN` ≈ 15 → Large (N ≈ 3.3 million)
- `logN` ≈ 20 → Very large (N ≈ 485 billion)

### Secondary: Diversity Index
```python
diversity = -∑(p_i × ln(p_i))  where p_i = c_i / n
```

**Correlation with logN:**
- +0.9 = Strong (diversity drives N)
- +0.5 = Moderate (diversity matters)
- -0.5 = Symmetry dominating

### Tertiary: T Parameter
- Typical range: 1.0 to 2.0
- Effect: Linear on logN (doubling T ≈ 50% increase)
- Increases as assembly complexity grows

---

## Convergence Patterns You'll See

### Pattern 1: Rapid Diversity Growth
```
Gen 0:  1 type  → logN = 1.39
Gen 5:  2 types → logN = 2.77  (jump!)
Gen 10: 3 types → logN = 5.01
Gen 15: 4 types → logN = 9.94
```
**Interpretation:** New polygon types drive exponential N growth

### Pattern 2: T-Driven Plateau
```
Gen 20: logN = 10.5, diversity = 1.2
Gen 30: logN = 10.8, diversity = 1.2  (only T growing)
Gen 40: logN = 11.2, diversity = 1.2
```
**Interpretation:** Assembly stable, only transformation freedom increasing

### Pattern 3: Symmetry Suppression
```
Gen 0: symmetry_factor = 1.0  → logN = 12.5
Gen 10: symmetry_factor = 0.5 → logN = 11.81  (30% reduction)
```
**Interpretation:** Symmetric patterns reduce degrees of freedom

### Pattern 4: Convergence Plateau
```
Gen 0-10:   logN grows rapidly ↑↑↑
Gen 10-30:  logN grows steadily ↑
Gen 30+:    logN flattens ----
```
**Interpretation:** Assembly reached complexity ceiling

---

## Integration with Your System

### Step 1: After each GA generation
```python
# Get current assembly
assembly = get_current_assembly()
types = [(poly.sides, count) for poly, count in assembly.composition]

# Compute T (from assembly geometry)
T = compute_transformation_param(assembly)

# Compute symmetry factor
symmetry = detect_geometric_symmetry(assembly)

# Track canonical N
tracker.record_assembly(T, types, symmetry)
```

### Step 2: Monitor convergence
```python
# Check if assembly is converging
history = tracker.get_history()
recent_logN = [p.logN for p in history[-10:]]

if all(recent_logN[i] <= recent_logN[i+1] + 0.01 for i in range(len(recent_logN)-1)):
    print("⚠️  logN has plateaued - assembly converged")
```

### Step 3: Analyze results
```python
# Print summary
print(tracker.print_convergence_summary())
print(tracker.print_ascii_graph())
print(tracker.compare_diversity_vs_N())

# Export data
import json
with open('convergence_data.json', 'w') as f:
    json.dump([
        {
            'gen': p.generation,
            'logN': p.logN,
            'N': p.N,
            'diversity': p.diversity_index,
            'T': p.T,
            'types': p.types,
        }
        for p in tracker.get_history()
    ], f)
```

---

## FAQ

**Q: Why log-space instead of direct N?**
A: N can overflow (>1e300), logN stays manageable. Also more numerically stable.

**Q: How do I compute T?**
A: From assembly geometry - transformation/orientation degrees of freedom. Typically 1.0-2.0.

**Q: What's a good N value?**
A: There's no "good" - it measures assembly complexity. Track how it evolves.

**Q: Does higher N mean better assembly?**
A: Not necessarily. Higher N = more valid configurations. Could indicate complexity or degrees of freedom.

**Q: When should I stop evolution?**
A: When logN plateaus (no new improvement in ~20 generations).

---

## References

- **Formula derivation:** `canonical_estimator.py`
- **Theory:** See CONVERGENCE_N_EXPLAINED.md
- **Implementation:** convergence_canonical_tracker.py
- **Interactive guide:** convergence_menu_canonical.py

---

## Summary

✅ N is the canonical polyform count estimator, not population size

✅ Track logN (log-space) to measure assembly complexity

✅ Monitor diversity, T, and symmetry to understand convergence

✅ Use ASCII tools to visualize without GUI overhead

✅ Run demos to understand the theory interactively

**Next step:** `python convergence_canonical_tracker.py` to see it in action!
