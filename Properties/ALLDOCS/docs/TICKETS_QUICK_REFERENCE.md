# Polylog GUI - Tickets Quick Reference

**Current Status:** Phase 3 Complete ✅ | Product Coverage: ~40%

---

## Critical Path (Next 2 weeks - Phase 4)

| Ticket | Task | Hours | Blocker |
|--------|------|-------|---------|
| **T-401** | Save/Load Assemblies | 8h | 🔴 NO |
| **T-402** | Polygon Deletion + Context Menu | 4h | 🔴 NO |
| **T-403** | Validation Feedback | 6h | 🔴 NO |
| **T-404** | Transform Tools (Move/Rotate/Scale) | 10h | 🟡 YES |
| **T-405** | Export (PNG/OBJ/JSON) | 8h | 🔴 NO |

**Total Phase 4:** ~36 hours (~2-3 dev weeks)

---

## Why These Matter

### T-401: Save/Load (MOST CRITICAL)
- **Current:** Users lose all work on close
- **After:** Can persist designs
- **Enables:** T-405, T-501, future cloud sync

### T-402: Delete (ESSENTIAL UX)
- **Current:** Can't remove mistakes
- **After:** Can clean up workspace
- **Dependency:** Needed before other edits

### T-403: Validation (PREVENTS ERRORS)
- **Current:** Invalid designs pass silently
- **After:** Red outlines on bad polygons
- **Prevents:** Data corruption, user frustration

### T-404: Transforms (POWER USER FEATURE)
- **Current:** Can only drag-create
- **After:** Full position/rotation/scale control
- **Unlocks:** Professional design workflows

### T-405: Export (SHARING)
- **Current:** Can't share designs
- **After:** PNG, OBJ, JSON export
- **Enables:** Sharing with others, 3D printing

---

## High-Value Features (Phase 5 - Next 3 weeks)

- **T-501** — Properties panel (12h)
- **T-502** — Layer management (14h)
- **T-503** — Analysis tools (16h)
- **T-504** — Keyboard shortcuts help (4h)

---

## Quick Wins (Polish Phase 6)

- **T-601** — Dark/light theme (4h)
- **T-602** — Settings dialog (10h)
- **T-603** — Tooltips (6h)
- **T-604** — Performance profiler (12h)

---

## Known Bugs (5 Total)

| Bug | Severity | Fix Time | Impact |
|-----|----------|----------|--------|
| BUG-001: Preview offset | LOW | 3h | Visual only |
| BUG-002: Library drag fails | MEDIUM | 4h | Intermittent |
| BUG-003: Clear not working | MEDIUM | 2h | Data integrity |
| BUG-004: Camera gimbal lock | LOW | 6h | UX friction |
| BUG-005: Status text queue | LOW | 2h | UX friction |

**Total bug fixes:** ~17 hours (should do with T-402)

---

## Feature Completeness by Area

```
Viewport & Rendering:        ████████░░ 80%  (2-3 missing features)
Polygon Creation/Editing:    ██████░░░░ 60%  (needs transforms)
File I/O & Persistence:      ░░░░░░░░░░  0%  ⚠️ CRITICAL
User Feedback & Validation:  ████░░░░░░ 40%  (needs validation)
Design Tools:                ██░░░░░░░░ 20%  (only drag-create)
Library & Collections:       █████░░░░░ 50%  (sample only)
Settings & Preferences:      ░░░░░░░░░░  0%  (needed for UX)
Help & Documentation:        ░░░░░░░░░░  0%  (zero user docs)
Export & Interop:            ░░░░░░░░░░  0%  ⚠️ NEEDED
Performance & Optimization:  ██████░░░░ 60%  (adequate for now)
─────────────────────────────────────────────
OVERALL:                     ███████░░░ 37%  (target: 80%)
```

---

## Recommended Execution Order

### Week 1 (T-401, T-402, BUG-003)
- Implement file dialog and save/load JSON
- Add context menu with delete
- Fix display list caching bug
- **Result:** Users can now persist work and clean up

### Week 2 (T-403)
- Integrate collision validator
- Add green/red outline rendering
- Emit validation signals to status bar
- **Result:** Design validation feedback

### Week 3 (T-404, T-405)
- Implement move/rotate/scale on selected polygon
- Add snap-to-grid
- Implement PNG/OBJ/JSON export
- **Result:** Full design workflow and sharing

---

## Success Criteria for Phase 4

- [ ] Users can create, save, load assemblies
- [ ] Users can delete and modify polygons
- [ ] Invalid polygons are highlighted
- [ ] Full transform controls present
- [ ] Can export to multiple formats
- [ ] All 5 bugs fixed
- [ ] Feature coverage > 60%
- [ ] No regressions in Phase 3 features

---

## Resource Requirements

| Role | Phase 4 | Phase 5 | Phase 6 | Notes |
|------|---------|---------|---------|-------|
| Dev (Full-stack) | 1 FTE | 1 FTE | 1 FTE | Lead critical path |
| QA/Testing | 0.25 FTE | 0.5 FTE | 0.5 FTE | Regression suite |
| Design | 0.1 FTE | 0.2 FTE | 0.3 FTE | UI/UX reviews |

---

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|-----------|
| File I/O corruption | HIGH | MEDIUM | Validate JSON before save |
| Performance drop @ 100 polys | MEDIUM | MEDIUM | Profile & optimize early |
| Qt version incompatibility | MEDIUM | LOW | Lock PySide6 version |
| Transform math errors | LOW | MEDIUM | Unit test transforms |

---

## Dependencies & Blockers

```
None of Phase 4 tickets are blocked.

Phase 4 → Phase 5:
  T-401 enables: T-501, T-502 (persistence needed)
  
Phase 4 → Phase 6:
  T-402 enables: T-602 (settings dialog)
```

---

## File Locations for Reference

| Ticket | Main File | Related |
|--------|-----------|---------|
| T-401 | `gui/main_window.py` | `stable_library.py` |
| T-402 | `gui/viewport.py` | `gui/main_window.py` |
| T-403 | `gui/viewport.py` | `collision_validator.py` |
| T-404 | `gui/viewport.py` | Transform properties |
| T-405 | `gui/main_window.py` | `library_thumbnail_renderer.py` |

---

## Phase 4 Acceptance Tests

```python
def test_save_load_roundtrip():
    """Save and load should preserve polygon data"""
    original = create_test_assembly(3)
    save_assembly(original, 'test.polylog')
    loaded = load_assembly('test.polylog')
    assert_equal(original, loaded)

def test_delete_with_undo():
    """Deleted polygons should be recoverable"""
    assembly = create_test_assembly(5)
    delete_polygon(assembly, 2)
    assert len(assembly) == 4
    undo()
    assert len(assembly) == 5

def test_validation_red_outline():
    """Invalid polygons should render red"""
    assembly.add(valid_poly)
    assembly.add(overlapping_poly)
    assert get_outline_color(assembly[1]) == RED

def test_transform_precision():
    """Transforms should be accurate to pixel"""
    poly = create_polygon((0, 0))
    move_to((10, 20))
    assert poly.position == (10, 20)

def test_export_formats():
    """All export formats should work"""
    assert export_png('test.png')
    assert export_obj('test.obj')
    assert export_json('test.json')
```

---

## Communication Plan

### Stakeholders
- **Users:** Emphasize T-401 (persistence) and T-402 (deletion)
- **Team:** Weekly sprints with demo at each checkpoint
- **Product:** Update roadmap after Phase 4 completion

### Status Updates
- Daily: 15-min standup (blockers only)
- Weekly: Demo + retrospective
- Bi-weekly: Stakeholder review

---

**Generated:** 2025-10-30  
**Next Review:** After T-401 completion  
**Questions?** See TICKETS.md for full details
