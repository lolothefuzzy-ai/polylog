# Code Cleanup Analysis

**Goal:** Identify and remove unused or obsolete code files

**Status:** Analyzing ~65 Python files (excluding tests and main.py)

---

## Known Active Code Paths

From `main.py`, only these imports are used:

1. **Demo mode:** `demo_library_integration.main()`
2. **API mode:** `_archive_legacy_code/polylog_main.py::start_api()`

### Demo Dependencies (from demo_library_integration.py)

```python
from random_assembly_generator import RandomAssemblyGenerator
from library_thumbnail_renderer import LibraryThumbnailRenderer
from library_drag_drop import LibraryDragDropHandler
from polyform_library import PolyformLibraryManager
from managers import RealWorkspaceManager
```

---

## Categories of Code to Audit

### 1. **Generator Modules** (Multiple - likely redundant)

- `random_assembly_generator.py` ✅ USED
- `random_polyform_generator.py` - Check if used
- `polyform_generation_engine.py` - Check if used
- `unified_generator.py` - Name suggests consolidation, likely old
- `evolutionary_generator.py` - Old/unused?
- `autonomous_generation_engine.py` - Old/unused?
- `lsystem_generator.py` - Old/unused?
- `constraint_solver_generator.py` - Old/unused?

### 2. **Manager Modules** (Multiple - likely redundant)

- `managers.py` ✅ USED (RealWorkspaceManager)
- `workspace_environments.py` - Duplicate?
- `interactive_workspace.py` - Duplicate?
- `stable_library.py` - Duplicate?

### 3. **UI/GUI Modules** (Development-only)

- `gui_enhancements_v2.py` - Merged?
- `professional_ui.py` - Old?
- `theme_manager.py` - Check if used
- `settings_dialog.py` - Used?
- `hinge_slider_ui.py` - Used?
- `polygon_range_slider.py` - Used?
- `visual_enhancement_system.py` - Old?
- `visual_tracking.py` - Old?

### 4. **Optimization/Tuning** (Experimental)

- `optuna_placement_tuner.py` - Experimental?
- `auto_tuning_profiler.py` - Old?
- `adaptive_algorithm_router.py` - Old?
- `predictive_engine.py` - Old?

### 5. **Analysis/Tracking** (Experimental)

- `convergence_tracker.py` - Used?
- `convergence_range_analyzer.py` - Used?
- `convergence_integration.py` - Used?
- `convergence_visualizer.py` - Used?
- `canonical_estimator.py` - Used?
- `example_convergence_tracking.py` - Example/demo?
- `example_range_analysis.py` - Example/demo?

### 6. **Performance/Cache** (Optimization)

- `multilevel_cache.py` - Used?
- `performance_monitor.py` - Used?
- `performance_integration.py` - Used?
- `scaler_database.py` - Used?
- `symmetry_database.py` - Used?
- `template_template_library.py` - Used?

### 7. **API/Server** (Legacy)

- `api_security.py` - Used?
- `api_server.py` - Used?
- `grpc_server.py` - Experiment?
- `polylog_main.py` (in archive) - ✅ USED for API mode

### 8. **Physics/3D** (Core or Old?)

- `physics_simulator.py` - Used?
- `bvh3d.py` - Used?
- `spatial_index.py` - Used? (duplicated in archive)
- `geometry3d.py` - Used?
- `hinge_manager.py` - Used?
- `collision_validator.py` - Used?
- `constraint_solver.py` - Used?

### 9. **Other Utilities**

- `learning_engine.py` - Old?
- `contextual_bonding_system.py` - Old?
- `evaluator_cache.py` - Old?
- `evaluator_cache_enhanced.py` - Duplicate?
- `generator_protocol.py` - Protocol/base class?
- `logging_config.py` - Used?
- `check_dependencies.py` - Used?
- `cleanup.py` - Utility?
- `polygon_utils.py` - Used?
- `validators.py` - Used?
- `STABILITY_PATCHES.py` - Patch file?

---

## Archive Directory Check

Files in `_archive_legacy_code/`:
- `polylog_main.py` - ✅ USED (for API mode)
- `run_polylog.py` - ❌ NOT USED (old CLI)
- `spatial_index.py` - DUPLICATE (exists in root too)
- `evaluator_cache.py` - Likely old

---

## Recommendations for Deletion

### Tier 1: Almost Certainly Unused
```
- autonomous_generation_engine.py
- evolutionary_generator.py
- lsystem_generator.py
- constraint_solver_generator.py
- unified_generator.py (if not consolidation point)
- example_convergence_tracking.py
- example_range_analysis.py
- auto_tuning_profiler.py
- adaptive_algorithm_router.py
- predictive_engine.py
- STABILITY_PATCHES.py
- _archive_legacy_code/run_polylog.py
```

### Tier 2: Likely Unused (Need Verification)
```
- convergence_visualizer.py
- visual_enhancement_system.py
- visual_tracking.py
- interactive_workspace.py
- workspace_environments.py
- api_security.py
- grpc_server.py
- contextual_bonding_system.py
- learning_engine.py
```

### Tier 3: Uncertain (Keep for Now)
```
- All UI modules (might be used)
- All optimization modules (might be used)
- All performance modules (might be used)
- Physics modules (core functionality?)
```

---

## Next Steps

1. **Grep search** - Find which modules are actually imported
2. **Remove Tier 1 files** - Safe deletions
3. **Test** - Run `python main.py demo` to verify everything works
4. **Remove Tier 2 files** - After verification
5. **Clean up duplicates** - spatial_index.py

---

## File Counts

- **Root Python files:** ~65
- **Test files:** ~20
- **Archive files:** 4
- **Total:** ~89 Python files

**Target:** Reduce to ~30-40 core files (50% reduction)
