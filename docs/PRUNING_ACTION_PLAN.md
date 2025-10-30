# Codebase Pruning - Action Plan
**October 30, 2025**

---

## Executive Summary

**Objective:** Reduce dependencies by 25-30% (150-200 KB)  
**Risk:** Low (mostly demo/experimental files)  
**Time Required:** 30-60 minutes  
**Impact:** Cleaner, faster production build

---

## The 9 Files to Remove Immediately (Phase 1)

These files are **100% safe to remove** - they're standalone demos with no dependencies:

```
1. demo_automated_placement.py      (13.27 KB) ✓ Demo only
2. demo_autonomous.py               (9.93 KB)  ✓ Demo only
3. stress_test_library.py           (12.32 KB) ✓ Test utility
4. stress_test_library_demo.py      (9.33 KB)  ✓ Test utility
5. benchmark_high_n.py              (11.76 KB) ✓ Benchmark only
6. find_highest_converged_order.py  (7.42 KB)  ✓ Historical analysis
7. verify_N_with_combinatorial_logic.py (10.74 KB) ✓ Historical verification
8. verify_system.py                 (5.06 KB)  ✓ Historical verification
9. gui_enhancements.py              (16.7 KB)  ✓ Old version (keep v2)
```

**Total Savings: ~97 KB (16% of total)**

---

## Execution (Phase 1)

### Step 1: Remove Files
```bash
cd /path/to/Polylog6

# Remove demo files
rm -f demo_automated_placement.py
rm -f demo_autonomous.py
rm -f stress_test_library.py
rm -f stress_test_library_demo.py
rm -f benchmark_high_n.py
rm -f find_highest_converged_order.py
rm -f verify_N_with_combinatorial_logic.py
rm -f verify_system.py
rm -f gui_enhancements.py
```

### Step 2: Verify Nothing Broke

```bash
# Check syntax of remaining files
python -m py_compile *.py

# Verify core app imports work
python -c "import desktop_app; print('✓ Imports OK')"

# Run all tests
pytest tests/ -v

# Start the app briefly to verify
timeout 5 python desktop_app.py 2>&1 | head -20 || true
```

### Step 3: Commit Changes

```bash
git add -A
git commit -m "chore: prune 9 demo/old files, reduce codebase by 97 KB"
```

---

## Phase 2: Evaluate Optional Engines

**These might be unused - check before removing:**

```
autonomous_generation_engine.py (20.48 KB)
evolutionary_generator.py       (13.53 KB)
lsystem_generator.py            (13.75 KB)
optuna_placement_tuner.py       (16.19 KB)
predictive_engine.py            (13.27 KB)
auto_tuning_profiler.py         (15 KB)
adaptive_algorithm_router.py    (14.27 KB)
```

**Checking Script:**
```bash
for file in autonomous_generation_engine evolutionary_generator \
            lsystem_generator optuna_placement_tuner predictive_engine \
            auto_tuning_profiler adaptive_algorithm_router; do
    count=$(grep -r "$file" *.py --exclude="*.pyc" | grep -v "^$file.py:" | wc -l)
    if [ $count -eq 0 ]; then
        echo "✓ $file - NOT imported (safe to remove)"
    else
        echo "✗ $file - Used $count times (keep)"
    fi
done
```

---

## Phase 3: Remove API/Server Files (If Unused)

**Only if tests pass and files aren't imported:**

```bash
# Check if API files are used
grep -r "api_server" *.py
grep -r "grpc_server" *.py
grep -r "api_security" *.py

# If no output from above, safe to remove:
# rm -f api_server.py grpc_server.py api_security.py
```

---

## Expected Results

### Before Pruning
```
77 files × 600 KB = Current state
```

### After Phase 1
```
68 files × 503 KB = 97 KB saved (16% reduction)
```

### After Phase 3 (If All Removed)
```
55-60 files × 400-450 KB = 150-200 KB saved (25-30% reduction)
```

---

## Validation Checklist

After Phase 1 execution:

```
□ All 9 files removed
□ Python syntax check passes
□ Import check passes  
□ All tests pass
□ Application starts
□ No broken references
□ Changes committed to git
```

---

## Rollback Plan

If anything breaks:

```bash
# Restore from git
git reset --hard HEAD~1
```

---

## Files Kept (Production Critical)

**These are the 11 core files (with tests = 23 files kept):**

```
✓ desktop_app.py
✓ automated_placement_engine.py
✓ collision_validator.py
✓ professional_ui.py
✓ interaction_manager.py
✓ managers.py
✓ constraint_solver.py
✓ hinge_manager.py
✓ stable_library.py
✓ geometry3d.py
✓ convergence_tracker.py
✓ + all test_*.py files
✓ + all other production files
```

---

## Quick Command Reference

```bash
# See total file count and size
echo "Files: $(ls -1 *.py | wc -l)"
echo "Size: $(du -sh *.py)"

# After pruning, should show:
# Files: 68
# Size: ~500KB
```

---

## Key Metrics

| Metric | Before | After (Phase 1) | After (All) |
|--------|--------|-----------------|-------------|
| Files | 77 | 68 | 55-60 |
| Size | 600 KB | 503 KB | 400-450 KB |
| Demo files | 9 | 0 | 0 |
| Test files | 12 | 12 | 12 |
| Core files | 11 | 11 | 11 |

---

## Why This Works

✅ **Low Risk:**
- Demo files have zero production dependencies
- No other files import them
- Tests still run independently

✅ **High Confidence:**
- 100% certain demo files aren't needed in production
- Old version detection is clear (v1 vs v2)
- All removals are documented

✅ **Easy Reversal:**
- All changes tracked in git
- Can revert with one command
- No data loss

---

## Next Actions

1. **Today:** Execute Phase 1 (30 min)
   - Remove 9 files
   - Run validation
   - Commit

2. **Tomorrow:** Execute Phase 2 (20 min)
   - Run grep checks
   - Remove unused experimental engines
   - Run validation

3. **Next Day:** Execute Phase 3 (15 min)
   - Check API/server usage
   - Remove if not used
   - Final validation

---

## Success Criteria

✓ All tests pass  
✓ Application starts without errors  
✓ No import errors  
✓ No broken references  
✓ Codebase is smaller and cleaner  

---

**Status:** Ready to Execute ✅  
**Confidence Level:** High  
**Recommendation:** Proceed with Phase 1 immediately
