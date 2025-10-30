## Convergence Tracking: Corrected N Definition

### THE CONFUSION

**What N is NOT:**
- ❌ NOT population size (that was my mistake earlier)
- ❌ NOT the number of evolutionary algorithm individuals
- ❌ NOT something you select or tune

**What N ACTUALLY IS:**
- ✅ The **Canonical Polyform Count Estimator**
- ✅ A formula that computes how many valid polyforms an assembly can generate
- ✅ Mathematically derived from assembly composition
- ✅ Used to measure assembly complexity and validity

---

## The Canonical N Formula

```
N = T × n! / ∏c_j! × ∏a_j^{c_j} × symmetry_factor
```

### Components Explained:

| Component | Meaning | Example |
|-----------|---------|---------|
| `T` | Transformation parameter (orientation freedom) | 1.0 to 2.0 |
| `n` | Total polygon count (sum of c_j) | 3 (if 2 squares + 1 triangle) |
| `n! / ∏c_j!` | Distinct permutation factor | 6 / (2! × 1!) = 3 |
| `∏a_j^{c_j}` | Product of sides raised to counts | 4² × 3¹ = 48 |
| `symmetry_factor` | Reduction for geometric indistinguishability | 0.5 to 1.0 |

### Worked Example:
```
Assembly: 2 squares + 1 triangle
T = 1.1, symmetry_factor = 1.0

N = 1.1 × 6 / 2 × 48 × 1.0 = 158.4

Interpretation: This assembly can generate ~158 distinct valid polyforms
```

---

## Log-Space Version (Numerically Stable)

Used for convergence tracking to prevent overflow:

```
logN = lnT + ln(n!) - ∑ln(c_j!) + ∑c_j·ln(a_j) + ln(symmetry_factor)
```

**Why logN?**
- N can be astronomically large (1e100+)
- Direct computation → numerical overflow
- logN stays manageable for comparison
- More stable for machine learning / convergence detection

**Interpretation of logN values:**
- logN ≤ 5 → N ≈ 150 (small assembly)
- logN ≈ 10 → N ≈ 22,000 (medium)
- logN ≈ 15 → N ≈ 3.3 million (large)
- logN ≈ 20 → N ≈ 485 billion (very large)

---

## Convergence Tracking: What to Watch

### 1. **Diversity-Driven Growth**
```
Start:  [(4,1)]           → N ≈ 4         diversity = 0.0
Add:    [(3,1),(4,1)]     → N ≈ 72        diversity = 0.69
Add:    [(3,2),(4,1)]     → N ≈ 144       diversity = 1.39
```
- More polygon types = exponential N increase
- Strongest driver of N growth

### 2. **T-Driven Growth**
```
Same assembly, different T:
T = 1.0  → logN = 5.2
T = 1.5  → logN = 6.1  (50% increase)
```
- Linear relationship: logN scales with lnT
- Secondary effect, but steady

### 3. **Symmetry Suppression**
```
Assembly X (no symmetry):
  logN = 12.5 → N ≈ 3.7 million

Same assembly Y (mirror symmetry, 0.5 factor):
  logN = 11.81 → N ≈ 1.3 million (64% reduction)
```
- Geometric patterns reduce valid configurations
- Elegant symmetry = fewer degrees of freedom

### 4. **Convergence Plateau**
```
logN rises steeply initially → gradually flattens
- Early: New polygon types drive rapid growth
- Middle: T/symmetry adjustments
- Late: N stabilizes (complexity ceiling reached)
```

---

## How to Use the Tools

### 1. Track N Evolution
```python
from convergence_canonical_tracker import CanonicalNTracker

tracker = CanonicalNTracker()

# Record each generation
for generation in range(100):
    assembly_types = [(4, 2), (3, 1)]  # 2 squares, 1 triangle
    T = 1.1
    symmetry = 0.95
    
    point = tracker.record_assembly(T, assembly_types, symmetry)
    print(f"logN: {point.logN}, N: {point.N}")

# View results
print(tracker.print_convergence_summary())
print(tracker.print_ascii_graph())
print(tracker.compare_diversity_vs_N())
```

### 2. Interactive Menu
```bash
python convergence_menu_canonical.py
```

Shows:
- [1] Convergence types
- [2] Live demo
- [3] logN explanation
- [4] Diversity vs N relationship
- [5] T parameter effects
- [6] Symmetry factor effects

### 3. Demo with Data
```bash
python convergence_canonical_tracker.py
```

Simulates assembly evolution and shows how N grows from 4 → 4.08e10

---

## Metrics to Monitor

| Metric | What It Means | Ideal Behavior |
|--------|---------------|----------------|
| `logN` | Assembly complexity | Steady increase then plateau |
| `Diversity Index` | Polygon type variety | Increases with assembly growth |
| `T` | Transformation freedom | Moderate growth (1.0 → 1.5) |
| `Correlation(diversity, logN)` | Relationship strength | +0.8 to +1.0 (positive) |
| `s_eff_geo` | Geometric mean of sides | Reflects dominant polygon type |

---

## Red Flags

⚠️ **logN decreases** → Assembly becoming degenerate
⚠️ **Diversity stable but logN flattens** → T bottleneck
⚠️ **High symmetry, low N** → Constrained configuration
⚠️ **Correlation(diversity, logN) < 0** → Symmetry dominating

---

## Summary: The Aligned Understanding

**Original Confusion:** Thought N was population size in evolutionary algorithm

**Correct Understanding:** N is the canonical polyform count estimator

**What You Track:** 
- How N evolves as assembly grows
- logN (log-space stability) is the key metric
- Driven by: diversity, T parameter, symmetry factor

**How It Relates to Your System:**
1. Genetic algorithm evolves assembly (population size = traditional GA param)
2. Each generation produces new assembly composition
3. You compute N = T × n! / ∏c_j! × ∏a_j^{c_j} × symmetry_factor
4. Track logN convergence over generations
5. Understand which factors drive polyform validity

---

## Files Created

| File | Purpose |
|------|---------|
| `convergence_canonical_tracker.py` | Core N tracking engine |
| `convergence_menu_canonical.py` | Interactive explanation menu |
| `CONVERGENCE_N_EXPLAINED.md` | This document |

---

## Quick Start

```bash
# See N evolution demo
python convergence_canonical_tracker.py

# Interactive learning
python convergence_menu_canonical.py

# Use in your code
from convergence_canonical_tracker import CanonicalNTracker
tracker = CanonicalNTracker()
# ... record assemblies ...
print(tracker.print_convergence_summary())
```
