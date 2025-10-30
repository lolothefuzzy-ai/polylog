## Canonical N Integration Guide

How to integrate canonical polyform count tracking into your assembly evolution system.

---

## Quick Integration (3 Steps)

### Step 1: Import the Integrator
```python
from canonical_integration import CanonicalIntegrator, AssemblyObserver

# Create integrator
integrator = CanonicalIntegrator(enable_tracking=True)
observer = AssemblyObserver(integrator)
```

### Step 2: Call after each GA Generation
```python
# Inside your evolutionary algorithm loop
for generation in range(num_generations):
    # ... your GA code ...
    
    # After you generate new assembly
    observer.on_generation_complete(assembly, generation)
```

### Step 3: Get Results
```python
# At end of evolution
observer.on_convergence_reached()

# Or export as dict
metrics = integrator.get_metrics_dict()
print(f"logN grew from {metrics['initial_logN']} to {metrics['final_logN']}")
```

---

## What the Integrator Automatically Computes

### 1. Assembly Types Extraction
```python
polyforms = assembly.get_all_polyforms()
# Automatically counts: 2 squares + 1 triangle = [(3, 1), (4, 2)]
```

### 2. T Parameter Calculation
```python
# Computes from:
# - Number of polyforms (base)
# - Connectivity (bonds/polyforms ratio)
# - Result: T typically 1.0 to 2.0
```

### 3. Symmetry Detection
```python
# Automatically detects:
# - Reflection symmetry (mirror)
# - Rotational symmetry (circular)
# - Returns: symmetry_factor (0.25 to 1.0)
```

### 4. Canonical N Computation
```python
# Computes: N = T × n! / ∏c_j! × ∏a_j^c_j × symmetry_factor
# Returns: logN (numerically stable) and N (if small enough)
```

---

## Integration Points

### With Evolution Loop
```python
class MyEvolutionaryAlgorithm:
    def __init__(self):
        self.integrator = CanonicalIntegrator(enable_tracking=True)
        self.observer = AssemblyObserver(self.integrator)
    
    def run(self, assembly, num_generations):
        for gen in range(num_generations):
            # Evaluate population
            fitness = self.evaluate_population()
            
            # Select parents
            parents = self.select(fitness)
            
            # Breed offspring
            offspring = self.breed(parents)
            assembly.merge(offspring)
            
            # TRACK CONVERGENCE
            self.observer.on_generation_complete(assembly, gen)
            
            # Check convergence
            if self.should_stop():
                self.observer.on_convergence_reached()
                break
```

### With API/Server
```python
# api_server.py
from canonical_integration import CanonicalIntegrator

integrator = CanonicalIntegrator()

@app.post("/api/generation")
def record_generation(assembly_data: dict):
    """Record assembly state after each generation."""
    polyforms = assembly_data['polyforms']
    bonds = assembly_data['bonds']
    generation = assembly_data['generation']
    
    point = integrator.record_assembly_state(polyforms, bonds, generation)
    
    return {
        'logN': point.logN,
        'N': point.N,
        'diversity': point.diversity_index,
        'T': point.T
    }

@app.get("/api/convergence-report")
def get_report():
    """Get convergence report."""
    return {'report': integrator.get_convergence_report()}
```

### With GUI
```python
# gui_window.py
class MainWindow:
    def __init__(self):
        self.integrator = CanonicalIntegrator()
    
    def on_generation_callback(self, assembly):
        """Called when GUI updates assembly."""
        point = self.integrator.record_assembly_state(
            assembly.get_all_polyforms(),
            assembly.get_bonds()
        )
        
        # Update GUI display
        self.update_status_bar(f"logN: {point.logN:.2f}")
        self.plot_convergence(self.integrator.tracker)
```

---

## Data Available During Tracking

### Per-Generation Data
```python
point = integrator.record_assembly_state(polyforms, bonds, generation)

# Access metrics:
point.generation          # Generation number
point.T                   # Transformation parameter
point.logN                # Log of canonical N
point.N                   # Canonical N (if not too large)
point.diversity_index     # Shannon entropy of polygon types
point.s_eff_geo          # Geometric mean of polygon sides
point.s_eff_arith        # Arithmetic mean of polygon sides
point.types              # List of (sides, count) tuples
point.symmetry_factor    # Geometric symmetry reduction
point.timestamp          # When this was recorded
```

### Full History
```python
history = integrator.tracker.get_history()

# Analyze growth
first = history[0]
last = history[-1]
growth = last.logN - first.logN
print(f"logN grew by {growth:.2f}")

# Find convergence point
for i in range(len(history)-5):
    recent = history[i:i+5]
    recent_logN = [p.logN for p in recent]
    if all(recent_logN[j] <= recent_logN[j+1] + 0.1 for j in range(4)):
        print(f"Converged at generation {recent[0].generation}")
        break
```

---

## Output Reports

### Console Report
```python
observer.on_convergence_reached()
# Prints:
# ================================================================================
# CANONICAL N CONVERGENCE REPORT
# ================================================================================
# 
# Generations tracked: 50
# 
# Initial Assembly:
#   Composition: [(4, 1)]
#   logN: 1.3863
#   N: 4.00e+00
#   ...
# Final Assembly:
#   Composition: [(3, 2), (4, 2), (5, 2), (6, 1)]
#   logN: 24.4309
#   N: 4.08e+10
#   ...
```

### Metrics Dictionary
```python
metrics = integrator.get_metrics_dict()
# Returns:
{
    'total_generations': 50,
    'initial_logN': 1.3863,
    'final_logN': 24.4309,
    'logN_growth': 23.0446,
    'initial_N': 4.0,
    'final_N': 4.08e+10,
    'initial_diversity': 0.0,
    'final_diversity': 1.3662,
    'initial_T': 1.0,
    'final_T': 1.3,
    'initial_types': [(4, 1)],
    'final_types': [(3, 2), (4, 2), (5, 2), (6, 1)]
}
```

### Full Visualization
```python
# Use convergence tracker's built-in visualization
integrator.tracker.print_convergence_summary()
integrator.tracker.print_ascii_graph()
integrator.tracker.compare_diversity_vs_N()
```

---

## Configuration Options

### Disable Tracking (Zero Overhead)
```python
integrator = CanonicalIntegrator(enable_tracking=False)
# record_assembly_state() will return None
# No computation or memory overhead
```

### Custom Metrics Export
```python
# Export to JSON
import json
metrics = integrator.get_metrics_dict()
with open('metrics.json', 'w') as f:
    json.dump(metrics, f)

# Export snapshots
snapshots = [
    {
        'gen': s.generation,
        'types': s.types,
        'T': s.T,
        'logN': s.polyform_count,  # Approx
        'bonds': s.bond_count,
    }
    for s in integrator.snapshots
]
```

### Performance Impact
- **Computation:** ~1ms per call (fast)
- **Memory:** ~1KB per generation tracked
- **500 generations:** ~500KB memory
- Can easily track thousands of generations

---

## Troubleshooting

### "assembly.get_all_polyforms() not found"
Your assembly object needs these methods:
```python
class AssemblyInterface:
    def get_all_polyforms(self) -> List[Dict]:
        """Return list of polyforms with 'sides' and 'vertices' keys."""
    
    def get_bonds(self) -> List[Dict]:
        """Return list of bonds."""
```

### "TypeError: canonical_estimate() missing required argument"
Make sure you're passing correct types:
```python
# ✓ Correct
tracker.record_assembly(T=1.1, types=[(4, 2), (3, 1)], symmetry_factor=0.95)

# ✗ Wrong
tracker.record_assembly(1.1, [(4, 2), (3, 1)], 0.95)  # Missing keyword args
```

### Memory usage growing
The tracker keeps 500 most recent points by default:
```python
# Change history limit
integrator.tracker = CanonicalNTracker(max_history=100)  # Keep last 100
```

---

## Example: Complete Integration

```python
from canonical_integration import CanonicalIntegrator, AssemblyObserver

class PolyformEvolution:
    def __init__(self, assembly):
        self.assembly = assembly
        self.integrator = CanonicalIntegrator(enable_tracking=True)
        self.observer = AssemblyObserver(self.integrator)
    
    def run_evolution(self, num_generations: int):
        """Run evolutionary algorithm with canonical tracking."""
        
        for generation in range(num_generations):
            # Evolution step
            self.assembly.step()
            
            # Track canonical N
            self.observer.on_generation_complete(self.assembly, generation)
            
            # Optional: Print status
            if generation % 10 == 0:
                metrics = self.integrator.get_metrics_dict()
                if metrics:
                    print(f"Gen {generation}: "
                          f"logN={metrics.get('final_logN', 0):.2f}")
        
        # Final report
        self.observer.on_convergence_reached()
        
        # Return metrics
        return self.integrator.get_metrics_dict()


# Usage
assembly = load_assembly()
evolution = PolyformEvolution(assembly)
metrics = evolution.run_evolution(num_generations=100)

print(f"\n✓ Evolution complete")
print(f"  Initial N: {metrics['initial_N']:.2e}")
print(f"  Final N: {metrics['final_N']:.2e}")
print(f"  Growth: {metrics['logN_growth']:.2f} (log-space)")
```

---

## Next Steps

1. **Run demo:** `python canonical_integration.py`
2. **Integrate:** Copy the 3-step pattern above
3. **Monitor:** Check metrics during evolution
4. **Analyze:** Use convergence reports to understand assembly growth

For more info: See `CONVERGENCE_N_EXPLAINED.md` and `README_CONVERGENCE.md`
