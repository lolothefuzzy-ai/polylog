# Integration Guide: Canonical N Tracking into Continuous Exploration Engine

How to integrate canonical N tracking into your existing continuous exploration and generation systems.

---

## Your Current Architecture

Your polyform system uses:
- **Random Assembly Generator** - Creates random polyform assemblies
- **Continuous Exploration Engine** - Autonomous background exploration
- **Suggestion Engine** - Proposes next polyforms based on assembly state
- **Library System** - Stores and manages polyforms
- **Main GUI** - Desktop interface for visualization

---

## Integration Points

### Integration Point 1: Random Assembly Generator

Track canonical N every time a random assembly is generated.

**File:** `random_assembly_generator.py`

Add at the top:
```python
from integration_hooks import GeneratorIntegration

# Create tracker (once, at module level or in __init__)
_canonical_tracker = None

def _get_tracker():
    global _canonical_tracker
    if _canonical_tracker is None:
        _canonical_tracker = GeneratorIntegration(
            None,  # Will be set later
            n_value=50,
            name="Random Assembly Generator"
        )
    return _canonical_tracker
```

Then in `generate_random_assembly()`:
```python
def generate_random_assembly(self, ...):
    # ... existing generation logic ...
    polyforms = [...]  # generated polyforms
    
    # Add tracking
    tracker = _get_tracker()
    tracker.system_tracker.record_generation_for_range(
        50,
        polyforms,
        [],  # no bonds yet
        self._generation_count
    )
    
    return polyforms
```

---

### Integration Point 2: Continuous Exploration Engine

Track assembly progression through exploration stages.

**File:** `continuous_exploration_engine.py`

In the `ContinuousExplorationEngine` class:

```python
from integration_hooks import GAIntegration

class ContinuousExplorationEngine:
    def __init__(self, config, ...):
        self.config = config
        
        # Add canonical N tracker
        self.canonical_tracker = GAIntegration(
            n_value=config.max_order,  # Use max order as population metric
            name="Continuous Exploration"
        )
        
        # ... existing init code ...
    
    def run(self, assembly, workspace, ...):
        """Main exploration loop"""
        iteration = 0
        
        while self._should_continue():
            # ... existing exploration logic ...
            
            # Track assembly state after successful placement
            if placement_successful:
                self.canonical_tracker.track_generation(assembly)
            
            iteration += 1
        
        # Finalize and show report
        print(self.canonical_tracker.finalize())
```

---

### Integration Point 3: Suggestion Engine

Track quality of suggestions vs actual outcomes.

**File:** `continuous_exploration_engine.py` (SuggestionEngine class)

```python
class SuggestionEngine:
    def __init__(self, ...):
        # ... existing init ...
        
        # Add outcome tracking
        from canonical_system_integration import CanonicalSystemIntegrator
        self.outcome_tracker = CanonicalSystemIntegrator()
        self.outcome_tracker.register_range(5, "Suggestion Outcomes")
    
    def suggest_next_polyforms(self, assembly, strategy, n_suggestions=5):
        """Generate suggestions - track quality"""
        suggestions = [...]  # existing code
        
        # Track current assembly state before suggestions
        self.outcome_tracker.record_generation_for_range(
            5,
            assembly.get_all_polyforms(),
            assembly.get_bonds() if hasattr(assembly, 'get_bonds') else [],
            self._suggestion_count
        )
        
        self._suggestion_count += 1
        return suggestions
```

---

## Complete Integration Example

### Scenario: Track Exploration Convergence

```python
# In continuous_exploration_engine.py

from integration_hooks import GAIntegration, MultiPopulationIntegration

class ContinuousExplorationEngine:
    def __init__(self, config, memory_manager, chain_manager):
        self.config = config
        
        # Track each exploration strategy separately
        self.strategy_trackers = MultiPopulationIntegration()
        
        for strategy in ExplorationStrategy:
            self.strategy_trackers.register_population(
                len(ExplorationStrategy),
                f"Strategy: {strategy.value}"
            )
        
        self.current_strategy_idx = 0
    
    def run_strategy(self, assembly, workspace, strategy):
        """Run exploration with specific strategy"""
        
        # Get tracker for this strategy
        tracker = list(self.strategy_trackers.ga_integrations.values())[
            list(ExplorationStrategy).index(strategy)
        ]
        
        iteration = 0
        while iteration < self.config.max_iterations:
            # Perform exploration step
            next_polyforms = self.suggestion_engine.suggest_next_polyforms(
                assembly, strategy
            )
            
            best = self._try_placements(assembly, next_polyforms)
            
            if best:
                assembly = best
                tracker.track_generation(assembly)
            
            iteration += 1
        
        return assembly
    
    def compare_strategies(self):
        """Compare convergence across all strategies"""
        print(self.strategy_trackers.get_convergence_report())
        self.strategy_trackers.print_comparison()
```

---

## Method 1: Simple (Minimal Changes)

Just track the best assembly periodically:

```python
# Add to ContinuousExplorationEngine.__init__
from integration_hooks import GAIntegration

self.tracker = GAIntegration(10, "Exploration")

# In main loop
if iteration % 10 == 0:
    self.tracker.track_generation(current_best_assembly)

# At end
print(self.tracker.finalize())
```

---

## Method 2: Comprehensive (Full Tracking)

Track all strategies and outcomes:

```python
# Add to ContinuousExplorationEngine
from integration_hooks import MultiPopulationIntegration
from canonical_system_integration import CanonicalSystemIntegrator

def __init__(self):
    # Multi-population: compare strategies
    self.strategy_multi = MultiPopulationIntegration()
    
    # System: track different parameters
    self.param_system = CanonicalSystemIntegrator()
    
    # Register each strategy
    for strategy in ExplorationStrategy:
        self.strategy_multi.register_population(10, f"Strategy: {strategy.value}")
    
    # Register different order levels
    for order in range(1, 6):
        self.param_system.register_range(order, f"Max Order: {order}")

def run_with_tracking(self):
    """Full tracking during exploration"""
    iteration = 0
    
    while self._should_continue():
        strategy = self._select_strategy()
        assembly = self._explore_with_strategy(strategy)
        order = self._estimate_order(assembly)
        
        # Track strategy effectiveness
        tracker = self.strategy_multi.ga_integrations[strategy]
        tracker.track_generation(assembly)
        
        # Track by order
        self.param_system.record_generation_for_range(
            order,
            assembly.get_all_polyforms(),
            assembly.get_bonds(),
            iteration
        )
        
        iteration += 1
    
    # Generate reports
    print(self.strategy_multi.get_convergence_report())
    self.param_system.print_visual_comparison()
```

---

## Method 3: Callback-Based (No Code Changes)

Minimal invasive approach:

```python
# Create tracker externally
from integration_hooks import CallbackBasedIntegration

tracker = CallbackBasedIntegration()
tracker.system_tracker.register_range(50, "My Exploration")

get_tracking_fn = tracker.get_tracking_function(50)

# Inject into engine
engine.on_assembly_update = get_tracking_fn

# In engine, call hook when assembly updates
def update_assembly(self, new_assembly):
    self.current_assembly = new_assembly
    if hasattr(self, 'on_assembly_update'):
        self.on_assembly_update(new_assembly, self.iteration)
```

---

## Integration Checklist

- [ ] Copy `integration_hooks.py` and `canonical_system_integration.py` to project
- [ ] Choose integration method (1, 2, or 3 above)
- [ ] Add import statement to your engine
- [ ] Create tracker instance in `__init__`
- [ ] Call `track_generation()` in main loop
- [ ] Add `print(tracker.finalize())` after exploration
- [ ] Run test exploration
- [ ] Verify metrics output
- [ ] Adjust tracking frequency if needed

---

## Quick Reference

### Track Single Exploration Run
```python
tracker = GAIntegration(pop_size, "My Exploration")
for iteration in range(max_iterations):
    assembly = explore_step()
    tracker.track_generation(assembly)
print(tracker.finalize())
```

### Compare Strategies
```python
multi = MultiPopulationIntegration()
greedy = multi.register_population(10, "Greedy")
random = multi.register_population(10, "Random")

for iteration in range(100):
    greedy.track_generation(run_greedy_exploration())
    random.track_generation(run_random_exploration())

multi.print_comparison()
```

### Track by Parameter
```python
system = CanonicalSystemIntegrator()
for max_order in [3, 5, 10]:
    system.register_range(max_order, f"Max Order {max_order}")

for iteration in range(100):
    for max_order in [3, 5, 10]:
        assembly = explore_with_limit(max_order)
        system.record_generation_for_range(max_order, assembly.polyforms, assembly.bonds, iteration)

system.print_visual_comparison()
```

---

## Expected Output

After running exploration with tracking:

```
GA Population:
  Generation: 500
  Elapsed: 125.3s
  logN Growth: +4.5
  Diversity: 3.2
  Status: ✓ CONVERGED

VISUAL COMPARISON ACROSS STRATEGIES

logN Growth:
  Greedy       ██████░░░░ +3.2
  Random       ████░░░░░░ +2.1
  Balanced     ████████░░ +3.8

Diversity:
  Greedy       ▲▲▲░░░░░░░ +2.1
  Random       ▲▲▲▲▲░░░░░ +2.8
  Balanced     ▲▲▲▲▲▲▲░░░ +3.2
```

---

## Integration Points Summary

| Component | File | Integration Point | Effort |
|-----------|------|-------------------|--------|
| Random Generator | random_assembly_generator.py | Track after generation | Low |
| Exploration Engine | continuous_exploration_engine.py | Track after iterations | Medium |
| Suggestion Engine | continuous_exploration_engine.py | Track suggestions | Medium |
| GUI | main.py / gui/app.py | Display metrics | Medium |
| Library | polyform_library.py | Track library growth | Low |

---

## Testing Your Integration

### Test 1: Verify imports
```python
python -c "from integration_hooks import GAIntegration; print('✓ Imports working')"
```

### Test 2: Run quick test
```python
from integration_hooks import GAIntegration
tracker = GAIntegration(10, "Test")
# Create mock assembly
class MockAssembly:
    def get_all_polyforms(self): return [{'sides': 4}]
    def get_bonds(self): return []
for i in range(10):
    tracker.track_generation(MockAssembly())
print(tracker.finalize())
```

### Test 3: Integrate into your engine
1. Add 3-5 lines to ContinuousExplorationEngine
2. Run exploration loop
3. Check for tracking output
4. Verify metrics appear

---

## Next Steps

1. **Choose method** (1=simple, 2=comprehensive, 3=callback)
2. **Add imports** to your engine file
3. **Create tracker** instance in __init__
4. **Add tracking call** in main loop
5. **Test** with small exploration run
6. **Verify** output metrics make sense
7. **Deploy** to full exploration

---

## Support

- Need help? Check `INTEGRATION_GUIDE.md` for detailed patterns
- See `demo_integrated_system.py` for working examples
- Run `python demo_integrated_system.py` to see system in action
- Read `SYSTEM_REFERENCE.md` for architecture details

---

**Ready to integrate!** Choose your method above and start with 3 lines of code.
