# Canonical N Tracking System - Complete Reference

Full overview of integrated canonical N tracking across your polyform assembly evolution system.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Your GA / Evolution System                   │
│                  (Any population-based algorithm)               │
└────────────┬────────────────────────────────────────────────────┘
             │
             │ Pass best individual each generation
             ▼
┌─────────────────────────────────────────────────────────────────┐
│              Integration Layer (integration_hooks.py)            │
│  • GAIntegration - Single GA tracking                           │
│  • MultiPopulationIntegration - Compare multiple GAs            │
│  • GeneratorIntegration - Wrap generators                       │
│  • CallbackBasedIntegration - No code changes needed            │
└────────────┬────────────────────────────────────────────────────┘
             │
             │ Record assembly state each generation
             ▼
┌─────────────────────────────────────────────────────────────────┐
│       System Integration Layer (canonical_system_integration.py) │
│  • CanonicalSystemIntegrator - Manage multiple N ranges         │
│  • Multi-range comparison and visualization                     │
│  • System-wide metrics aggregation                              │
└────────────┬────────────────────────────────────────────────────┘
             │
             │ Record data points per range
             ▼
┌─────────────────────────────────────────────────────────────────┐
│         Core Integration (canonical_integration.py)              │
│  • CanonicalIntegrator - Single range canonical N tracking      │
│  • Assembly state recording                                     │
│  • Canonical N estimation & convergence detection               │
└────────────┬────────────────────────────────────────────────────┘
             │
             │ Calculate canonical metrics
             ▼
┌─────────────────────────────────────────────────────────────────┐
│      Canonical Estimator (canonical_estimator.py)                │
│  • Compute N = T × (n! / ∏c_j!) × ∏a_j^{c_j} × symmetry      │
│  • Track T parameter, diversity, convergence                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Components

### 1. **canonical_estimator.py**
Core mathematical computation of canonical N.

**Key function:**
```python
canonical_N = canonical_estimator.estimate_canonical_N(
    polyforms,  # List of polygon dictionaries
    bonds,      # List of bond connections
    t_param     # Transformation parameter
)
```

**Outputs:**
- `N`: Canonical polyform count (log-space to avoid overflow)
- `T`: Transformation freedom parameter
- `diversity`: Shannon entropy of polygon types
- `symmetry_factor`: Geometric symmetry reduction

---

### 2. **canonical_integration.py**
Single-range canonical N tracking and convergence detection.

**Main class:** `CanonicalIntegrator`

**Key methods:**
```python
integrator = CanonicalIntegrator(enable_tracking=True)

# Record assembly state
point = integrator.record_assembly_state(
    polyforms,
    bonds,
    generation
)

# Get metrics
metrics = integrator.get_metrics_dict()  # All metrics
report = integrator.get_convergence_report()  # Text report

# ASCII visualization
integrator.print_fitness_graph()
integrator.print_variance_graph()
```

---

### 3. **canonical_system_integration.py**
Multi-range tracking across different N values (populations, parameters, etc.).

**Main class:** `CanonicalSystemIntegrator`

**Typical workflow:**
```python
system = CanonicalSystemIntegrator(enable_visual_tracking=True)

# Register N ranges to track
integrator_10 = system.register_range(10, "Small N")
integrator_30 = system.register_range(30, "Medium N")
integrator_50 = system.register_range(50, "Large N")

# Record generations
for gen in range(num_generations):
    system.record_generation_for_range(10, polyforms, bonds, gen)
    system.record_generation_for_range(30, polyforms, bonds, gen)
    system.record_generation_for_range(50, polyforms, bonds, gen)

# Compare all ranges
print(system.get_all_ranges_summary())
print(system.get_convergence_comparison())
system.print_visual_comparison()
system.finalize_all_ranges()
```

---

### 4. **integration_hooks.py**
Easy-to-use integration points for your existing code.

**Classes:**

#### `GAIntegration` - Track single GA
```python
ga_tracker = GAIntegration(n_value=25, name="My GA")

for gen in range(num_generations):
    best = ga.get_best()
    ga_tracker.track_generation(best)
    if gen % 10 == 0:
        ga_tracker.print_progress(num_generations)

print(ga_tracker.finalize())
```

#### `MultiPopulationIntegration` - Compare multiple populations
```python
multi = MultiPopulationIntegration()

ga_1 = multi.register_population(25, "GA Population 1")
ga_2 = multi.register_population(50, "GA Population 2")

for gen in range(num_generations):
    ga_1.track_generation(best_1)
    ga_2.track_generation(best_2)

multi.print_comparison()
```

#### `GeneratorIntegration` - Wrap generators
```python
integration = GeneratorIntegration(
    my_generator,
    n_value=20,
    name="Assembly Generator"
)

for i in range(1000):
    assembly = integration.generate_with_tracking()

print(integration.get_report())
```

#### `CallbackBasedIntegration` - No code changes
```python
callback_system = CallbackBasedIntegration()
callback_system.system_tracker.register_range(20, "GA")

track_fn = callback_system.get_tracking_function(20)

for gen in range(num_generations):
    best = ga.get_best()
    track_fn(best, gen)  # One-line tracking
```

---

## Integration Checklist

### Minimum Integration (3 lines)
```python
from integration_hooks import GAIntegration

ga = GAIntegration(50, "My GA")
for gen in range(gens):
    ga.track_generation(ga.get_best())
print(ga.finalize())
```

### Full Integration (5 steps)

- [ ] Import tracking module:
  ```python
  from integration_hooks import GAIntegration
  ```

- [ ] Create tracker at GA init:
  ```python
  self.tracker = GAIntegration(self.population_size, "My GA")
  ```

- [ ] Call in generation loop:
  ```python
  self.tracker.track_generation(best_individual)
  ```

- [ ] Periodic monitoring:
  ```python
  if generation % 10 == 0:
      self.tracker.print_progress(max_generations)
  ```

- [ ] Final report:
  ```python
  print(self.tracker.finalize())
  ```

---

## Output Interpretation

### logN Growth
- **Positive**: Canonical N increasing = assembly complexity growing
- **Negative**: Canonical N decreasing = simplification
- **Zero**: Stable complexity plateau

### Diversity Change
- **Positive**: More polygon variety being used
- **Negative**: Convergence to fewer polygon types
- **Zero**: Stable polygon type usage

### T Parameter (Transformation Freedom)
- **Increasing**: More transformation flexibility achieved
- **Decreasing**: Constraints tightening
- **High values**: Well-structured, highly transformable assemblies

### Convergence Status
- **CONVERGED**: logN and diversity plateaued
- **IMPROVING**: Still evolving upward
- **STABLE**: Small oscillations, not converging

---

## Real-Time Monitoring Options

### Option 1: Console Printing
```python
# Every 10 generations
if generation % 10 == 0:
    ga_tracker.print_progress(total_generations)
```

Output shows: generation, elapsed time, ETA, logN growth, diversity

### Option 2: Live Metrics Export
```python
# Export to CSV after every 50 generations
if generation % 50 == 0:
    metrics = system_tracker.export_all_metrics()
    save_to_csv(metrics)
```

### Option 3: Visual Comparison
```python
# Show ASCII bars every 25 generations
if generation % 25 == 0:
    system_tracker.print_visual_comparison()
```

Shows bar charts of logN growth, generations, diversity change across ranges

### Option 4: Custom Callbacks
```python
def my_callback(generation, individual):
    print(f"Gen {generation}: N={estimate_N(individual)}")

callback_system.register_callback(20, my_callback)
```

---

## Common Patterns

### Pattern: Compare Two GA Variants
```python
multi = MultiPopulationIntegration()
ga_baseline = multi.register_population(50, "Baseline GA")
ga_improved = multi.register_population(50, "Improved GA")

for gen in range(generations):
    ga_baseline.track_generation(run_baseline_ga())
    ga_improved.track_generation(run_improved_ga())

multi.print_comparison()  # Side-by-side comparison
```

### Pattern: Track Convergence Across Population Sizes
```python
system = CanonicalSystemIntegrator()
for pop_size in [10, 25, 50, 100, 200]:
    system.register_range(pop_size, f"Pop Size {pop_size}")

# Run same GA with different population sizes
for pop_size in [10, 25, 50, 100, 200]:
    best = run_ga(population_size=pop_size)
    system.record_generation_for_range(
        pop_size, best.polyforms, best.bonds, generation
    )

system.print_visual_comparison()
```

### Pattern: Multi-Objective Tracking
```python
system = CanonicalSystemIntegrator()
objectives = ['maximize_N', 'minimize_bonds', 'maximize_symmetry']

for obj in objectives:
    system.register_range(len(objectives), f"Objective: {obj}")

for gen in range(generations):
    for i, obj in enumerate(objectives):
        best = run_ga_for_objective(obj)
        system.record_generation_for_range(
            len(objectives), best.polyforms, best.bonds, gen
        )
```

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| "Range not registered" | Trying to record before registering | Call `register_range()` first |
| No data in metrics | No assembly state recorded | Verify polyforms/bonds are valid dicts |
| Slow tracking | Recording every generation | Track every N generations instead |
| Wrong N values | Assembly structure invalid | Validate polyform format |
| Can't import modules | Missing dependencies | Check all .py files in directory |

---

## File Dependency Graph

```
your_ga_code.py
    ↓
integration_hooks.py
    ├─→ canonical_system_integration.py
    │   ├─→ canonical_integration.py
    │   │   ├─→ canonical_estimator.py
    │   │   └─→ convergence_range_analyzer.py
    │   └─→ convergence_range_analyzer.py
    └─→ canonical_integration.py
        └─→ canonical_estimator.py
```

All tracking modules already depend on the core estimator, so just import what you need:
- For single GA: `from integration_hooks import GAIntegration`
- For multi-GA: `from integration_hooks import MultiPopulationIntegration`
- For direct control: `from canonical_system_integration import CanonicalSystemIntegrator`

---

## Quick Reference: Method Signatures

```python
# Register a range
system.register_range(n_value: int, name: str = None) -> CanonicalIntegrator

# Record assembly state
system.record_generation_for_range(
    n_value: int,
    polyforms: List[Dict],
    bonds: List[Dict],
    generation: int
)

# Get data
metrics = system.get_range_metrics(n_value: int) -> Dict
all_metrics = system.export_all_metrics() -> Dict

# Display results
system.print_visual_comparison()  # ASCII bars
print(system.get_all_ranges_summary())  # Text summary
print(system.get_convergence_comparison())  # Convergence status
system.finalize_all_ranges()  # Final detailed reports
```

---

## Integration Testing Checklist

After adding tracking to your code:

- [ ] Code imports without errors
- [ ] Tracker initializes without errors
- [ ] Assembly state records without errors (generation 0)
- [ ] Metrics show reasonable values after 1 generation
- [ ] Reports print without errors
- [ ] No memory leaks after 100 generations
- [ ] Performance acceptable (track every N gens if needed)

---

## Next Steps

1. **Choose integration style:**
   - Simple: Use `GAIntegration` directly
   - Complex: Use `MultiPopulationIntegration` or `CanonicalSystemIntegrator`

2. **Add 1-3 lines to your GA loop**

3. **Run evolution and check output**

4. **Customize visualization frequency**

5. **Export metrics if desired**

See `integration_hooks.py` for 4 complete working examples.
