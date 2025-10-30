# Polylog Simulator - Product Gap Analysis & Tickets

**Analysis Date:** 2025-10-30  
**Version:** 0.2.0  
**Status:** Phase 3 Complete (Drag-and-Drop), Phase 4+ Pending

---

## Executive Summary

Current product has **~40% GUI feature coverage** with core foundation in place. Major gaps exist in:
- File I/O (save/load assemblies)
- Real-time visualization features
- Collision & validation feedback
- Educational/tutorial features
- Performance monitoring
- Settings/preferences

---

## Implemented Features (Phase 1-3) ✅

- ✅ 3D viewport with OpenGL rendering
- ✅ Grid background, axes, camera controls
- ✅ Polygon selection and highlighting
- ✅ Undo/redo stack with signal system
- ✅ Library panel with sample designs
- ✅ Drag-and-drop from library to viewport
- ✅ Drag-to-create custom polygons
- ✅ Double-click quick-add
- ✅ Status bar with feedback
- ✅ Menu bar (File, Edit, View, Tools, Help)
- ✅ Generator panel (basic)
- ✅ Bonding panel (basic)
- ✅ Controls panel (sliders)

---

## PRIORITY 1: Critical Gaps (Phase 4)

### T-401: Implement Save/Load Assembly Functionality
**Severity:** CRITICAL  
**Sprint:** Phase 4, Week 1-2  
**Impact:** Users cannot persist their work

**Acceptance Criteria:**
- [ ] "Save Assembly" menu action writes JSON with polygon data
- [ ] "Load Assembly" menu action restores viewport state
- [ ] File dialog with .polylog file extension
- [ ] Status bar shows save success/error
- [ ] Undo/redo state cleared on load
- [ ] Recent files list in File menu (up to 5)

**Dependencies:**
- `gui/app.py` needs file dialog integration
- `stable_library.py` integration for persistence

**Estimated:** 8 hours

---

### T-402: Polygon Deletion & Context Menu
**Severity:** CRITICAL  
**Sprint:** Phase 4, Week 1  
**Impact:** Users cannot remove incorrect polygons

**Acceptance Criteria:**
- [ ] Right-click in viewport opens context menu
- [ ] "Delete" option removes selected polygon
- [ ] Delete key (Del) also works
- [ ] Undo supports deletion
- [ ] Status shows "Polygon deleted"
- [ ] Cannot delete if nothing selected

**Dependencies:**
- `viewport.py` needs context menu handler
- Existing selection system

**Estimated:** 4 hours

---

### T-403: Validation Feedback System
**Severity:** CRITICAL  
**Sprint:** Phase 4, Week 2  
**Impact:** Users have no feedback on polygon validity

**Acceptance Criteria:**
- [ ] Polygon collision detection prevents overlapping
- [ ] Visual feedback: red outline for invalid, green for valid
- [ ] Status bar shows "Invalid: Overlaps with polygon 2"
- [ ] Cannot add invalid polygons to library
- [ ] Polygon highlighting shows validation state

**Dependencies:**
- `collision_validator.py` (already exists)
- `viewport.py` for rendering
- Signal system for feedback

**Estimated:** 6 hours

---

### T-404: Polygon Transform Tools (Move, Rotate, Scale)
**Severity:** HIGH  
**Sprint:** Phase 4, Week 2-3  
**Impact:** Users cannot position polygons precisely

**Acceptance Criteria:**
- [ ] Click+drag moves selected polygon
- [ ] Right-drag rotates around center
- [ ] Scroll with Shift scales polygon
- [ ] Visual ghost preview during transform
- [ ] Snap-to-grid toggle (Ctrl+G)
- [ ] Status shows coordinates during transform
- [ ] Undo/redo supports transforms

**Dependencies:**
- `viewport.py` mouse handlers
- Transform property in polygon data
- Grid rendering system

**Estimated:** 10 hours

---

### T-405: Export to Image/3D Format
**Severity:** HIGH  
**Sprint:** Phase 4, Week 3  
**Impact:** Users cannot share work or use in other tools

**Acceptance Criteria:**
- [ ] "Export as PNG" saves current viewport as image
- [ ] "Export as OBJ" saves 3D mesh
- [ ] "Export as JSON" saves raw data
- [ ] File dialog with format selection
- [ ] Resolution setting for image export
- [ ] Status shows file path

**Dependencies:**
- Image rendering already working (library_thumbnail_renderer.py)
- OBJ export needs new module

**Estimated:** 8 hours

---

## PRIORITY 2: High-Value Features (Phase 5)

### T-501: Assembly Properties Panel
**Severity:** HIGH  
**Sprint:** Phase 5, Week 1  
**Impact:** Missing design information UI

**Acceptance Criteria:**
- [ ] New "Properties" panel on right side
- [ ] Shows selected polygon properties:
  - ID, type, sides, vertices count
  - Position (x, y, z)
  - Rotation, scale
  - Color, layer
- [ ] Shows assembly totals:
  - Total polygons
  - Polygon type distribution
  - Bounding box
  - Center of mass
- [ ] Edit properties in-panel
- [ ] Real-time updates

**Dependencies:**
- New panel class `PropertiesPanel`
- Polygon data structure enhancements

**Estimated:** 12 hours

---

### T-502: Layer/Group Management
**Severity:** MEDIUM  
**Sprint:** Phase 5, Week 1  
**Impact:** Complex assemblies become unmanageable

**Acceptance Criteria:**
- [ ] "Layers" panel with layer tree
- [ ] Can create/delete/rename layers
- [ ] Polygons can be assigned to layers
- [ ] Layer visibility toggle
- [ ] Layer locking (prevent edits)
- [ ] Select by layer (Ctrl+click layer)
- [ ] Render layer colors in viewport

**Dependencies:**
- New panel class `LayersPanel`
- Viewport layer rendering
- Selection system updates

**Estimated:** 14 hours

---

### T-503: Assembly Analysis Tools
**Severity:** MEDIUM  
**Sprint:** Phase 5, Week 2  
**Impact:** No insight into assembly properties

**Acceptance Criteria:**
- [ ] "Tools" menu → "Analyze Assembly"
- [ ] Shows statistics:
  - Perimeter, area, volume
  - Polygon coverage %
  - Edge-sharing metrics
  - Symmetry analysis
- [ ] Visualize metrics on polygons (heat map)
- [ ] Export analysis report as PDF/CSV

**Dependencies:**
- Analysis algorithms (geometry)
- Chart rendering library
- Report generation

**Estimated:** 16 hours

---

### T-504: Keyboard Shortcuts Panel
**Severity:** MEDIUM  
**Sprint:** Phase 5, Week 1  
**Impact:** Users don't know available shortcuts

**Acceptance Criteria:**
- [ ] Help → "Keyboard Shortcuts" shows dialog
- [ ] Categorized: Viewport, Selection, Transform, File
- [ ] Searchable shortcut list
- [ ] Shows customizable shortcuts
- [ ] Export shortcuts reference (PDF)

**Dependencies:**
- Qt dialog
- Shortcut data structure

**Estimated:** 4 hours

---

### T-505: Redo/Undo History Browser
**Severity:** LOW  
**Sprint:** Phase 5, Week 3  
**Impact:** Users can't see what undo will do

**Acceptance Criteria:**
- [ ] "Edit" menu → "History"
- [ ] Shows list of last 50 actions
- [ ] Click to jump to that state
- [ ] Thumbnail preview of polygon changes
- [ ] Color-coded action types

**Dependencies:**
- History tracking (already exists)
- Thumbnail rendering
- Tree widget

**Estimated:** 8 hours

---

## PRIORITY 3: Polish & UX (Phase 6)

### T-601: Dark/Light Theme Support
**Severity:** MEDIUM  
**Sprint:** Phase 6, Week 1  
**Impact:** Eye strain for night users

**Acceptance Criteria:**
- [ ] Settings → "Appearance" → Dark/Light theme
- [ ] Viewport background adapts
- [ ] Panel styling updates
- [ ] Persist theme preference
- [ ] Apply immediately

**Dependencies:**
- `gui/theme.py` already exists
- Settings dialog needed

**Estimated:** 4 hours

---

### T-602: Settings/Preferences Dialog
**Severity:** MEDIUM  
**Sprint:** Phase 6, Week 1  
**Impact:** No user customization options

**Acceptance Criteria:**
- [ ] Edit → "Preferences" opens dialog
- [ ] Appearance tab: theme, font size
- [ ] Viewport tab: grid on/off, snap distance, speed
- [ ] Performance tab: FPS limit, quality settings
- [ ] Behavior tab: confirm on delete, auto-save
- [ ] Save to config file

**Dependencies:**
- Qt settings system
- Config file I/O
- Dialog builder

**Estimated:** 10 hours

---

### T-603: Tooltips & Context Help
**Severity:** LOW  
**Sprint:** Phase 6, Week 2  
**Impact:** Users confused by controls

**Acceptance Criteria:**
- [ ] All buttons/controls have tooltips
- [ ] Right-click shows help for controls
- [ ] F1 opens help for selected item
- [ ] Comprehensive tooltips (100+ strings)

**Dependencies:**
- Qt help system
- String management

**Estimated:** 6 hours

---

### T-604: Performance Profiler Panel
**Severity:** MEDIUM  
**Sprint:** Phase 6, Week 2  
**Impact:** No visibility into performance issues

**Acceptance Criteria:**
- [ ] New "Profiler" panel showing:
  - Frame time (ms)
  - Polygon render count
  - Undo/redo stack size
  - Memory usage (KB)
  - OpenGL calls per frame
- [ ] Graph view of FPS over time
- [ ] Toggle V-sync
- [ ] Target FPS setting (30, 60, 120)

**Dependencies:**
- OpenGL stats extraction
- Performance monitoring code
- Chart widget

**Estimated:** 12 hours

---

## PRIORITY 4: Advanced Features (Phase 7+)

### T-701: Real-time Collaboration
**Severity:** LOW  
**Sprint:** Future  
**Impact:** Users cannot share design session

**Features:**
- [ ] Network sync between clients
- [ ] Cursor positions shown
- [ ] Live chat in sidebar
- [ ] Conflict resolution for simultaneous edits

**Estimated:** 40+ hours

---

### T-702: Animation Timeline
**Severity:** LOW  
**Sprint:** Future  
**Impact:** Cannot animate polygon transformations

**Features:**
- [ ] Timeline view at bottom of viewport
- [ ] Keyframe insertion
- [ ] Playback controls
- [ ] Preview of animation

**Estimated:** 30+ hours

---

### T-703: Procedural Generation Builder
**Severity:** LOW  
**Sprint:** Future  
**Impact:** Cannot programmatically create complex assemblies

**Features:**
- [ ] Visual node-based editor
- [ ] Math, loops, branching nodes
- [ ] Generate assembly from script
- [ ] Parameter sweep UI

**Estimated:** 50+ hours

---

### T-704: AI Shape Suggestion
**Severity:** LOW  
**Sprint:** Future  
**Impact:** Cannot get design recommendations

**Features:**
- [ ] "Suggest shapes" button
- [ ] ML model recommends next polygon
- [ ] Based on current assembly
- [ ] Confidence scores shown

**Estimated:** 20+ hours

---

## Known Issues (Bugs)

### BUG-001: Polygon Preview Rendering Offset
**Severity:** LOW  
**Status:** Open  
**Description:** Drag-to-create preview vertices appear offset from mouse position

**Root Cause:** Screen-to-world coordinate conversion in `_draw_polygon_preview()`

**Fix:** Implement proper ray casting from camera through mouse position

**Estimated:** 3 hours

---

### BUG-002: Library Drag Doesn't Work Sometimes
**Severity:** MEDIUM  
**Status:** Open  
**Description:** After deleting polygon, library drag sometimes fails silently

**Root Cause:** Signal disconnection issue or memory state

**Steps to Reproduce:**
1. Create polygon via drag-to-create
2. Delete it
3. Try to drag from library
4. Drop doesn't work

**Fix:** Check signal/slot connections after deletion

**Estimated:** 4 hours

---

### BUG-003: Viewport Doesn't Clear on "Clear All"
**Severity:** MEDIUM  
**Status:** Open  
**Description:** Some polygons remain visible after Clear All

**Root Cause:** Display list caching not properly invalidated

**Fix:** Force-clear all display lists in `clear()`

**Estimated:** 2 hours

---

### BUG-004: Camera Rotation Jumps at Extreme Angles
**Severity:** LOW  
**Status:** Open  
**Description:** Camera gimbal lock at 90° rotation

**Root Cause:** Euler angle singularity in `_setup_camera()`

**Fix:** Use quaternion rotation instead

**Estimated:** 6 hours

---

### BUG-005: Status Bar Text Doesn't Update on Rapid Changes
**Severity:** LOW  
**Status:** Open  
**Description:** During fast polygon creation, status text queues up

**Root Cause:** Qt signal buffering

**Fix:** Throttle status updates to 10Hz max

**Estimated:** 2 hours

---

## Integration Gaps

### Missing Modules
- ❌ `save_assembly()` - File I/O
- ❌ `load_assembly()` - File I/O
- ❌ `export_to_image()` - Image export
- ❌ `export_to_obj()` - 3D mesh export
- ❌ `PropertiesPanel` - Properties UI
- ❌ `LayersPanel` - Layer management
- ❌ `AnalysisTools` - Assembly metrics
- ❌ `SettingsDialog` - Preferences UI

### Incomplete Implementations
- ⚠️ `Generator Panel` - Only framework, no actual generation parameters
- ⚠️ `Bonding Panel` - Mock data only, no real bond discovery
- ⚠️ `Library Panel` - Sample data only, not connected to StableLibrary
- ⚠️ `Collision Validator` - Exists but not integrated to viewport
- ⚠️ `HingeManager` - Exists but not used in UI

### Backend/API Gaps
- ❌ Assembly persistence to disk
- ❌ Library database queries
- ❌ Batch operations API
- ❌ Collision detection in viewport
- ❌ Real-time physics preview

---

## Dependency Chain (Recommended Implementation Order)

```
Phase 4 (Critical):
├── T-401 (Save/Load) → Enables all persistence
├── T-402 (Delete) → Essential for UX
├── T-403 (Validation) → Prevents errors
├── T-404 (Transform) → Essential for design
└── T-405 (Export) → Enables sharing

Phase 5 (High-Value):
├── T-501 (Properties) → Info panel
├── T-502 (Layers) → Complex assemblies
├── T-503 (Analysis) → Design insights
└── T-504 (Help) → UX polish

Phase 6 (Polish):
├── T-601 (Theme) → User comfort
├── T-602 (Settings) → Customization
├── T-603 (Tooltips) → Discoverability
└── T-604 (Profiler) → Performance debugging

Phase 7+ (Advanced):
├── T-701 (Collab) → Team features
├── T-702 (Animation) → Advanced UX
├── T-703 (Procedural) → Power-user tools
└── T-704 (AI) → Intelligence features
```

---

## Testing Requirements

### Regression Test Suite Needed
- [ ] File I/O (save/load/export)
- [ ] Undo/redo all operations
- [ ] Drag-and-drop edge cases
- [ ] Selection state consistency
- [ ] Camera control precision
- [ ] Performance under 1000 polygons

### UI Automation Tests
- [ ] Menu navigation
- [ ] Keyboard shortcuts
- [ ] Dialog workflows
- [ ] Error handling

---

## Documentation Gaps

### Missing User Documentation
- [ ] Quick Start Guide (5 min tutorial)
- [ ] Keyboard Shortcuts Reference
- [ ] FAQ (10 common questions)
- [ ] Video Tutorials (YouTube playlist)
- [ ] API Documentation for scripting

### Missing Developer Documentation
- [ ] Architecture guide for new contributors
- [ ] Panel development template
- [ ] Viewport rendering pipeline
- [ ] Signal/slot connection conventions
- [ ] Testing guidelines

---

## Performance Targets

### Current (Measured Oct 30, 2025)
- Viewport: ~60 FPS (empty)
- Polygons: 1-10 rendered smoothly
- Drag-to-create: Smooth feedback at 60 FPS

### Targets for Phase 5+
- Viewport: ≥60 FPS with 100 polygons
- Memory: <200MB for typical assembly
- Load time: <1s for saved assembly
- Export: <5s for PNG/OBJ export

---

## Success Metrics (Product Readiness)

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| GUI feature coverage | 40% | 80% | ❌ Phase 4 needed |
| File I/O support | 0% | 100% | ❌ Critical gap |
| User can save work | ❌ | ✅ | ❌ T-401 |
| User can delete polygons | ❌ | ✅ | ❌ T-402 |
| Design validation shown | ❌ | ✅ | ❌ T-403 |
| Transform tools | 50% (drag-create only) | 100% | ⚠️ T-404 |
| Export capability | 0% | 100% | ❌ T-405 |
| User documentation | 0% | 100% | ❌ Phase 6+ |
| Performance @ 100 polys | Unknown | ≥60 FPS | ⚠️ Needs test |

---

## Estimated Timeline

| Phase | Duration | Tickets | Status |
|-------|----------|---------|--------|
| Phase 1-3 | ✅ Complete | T-101...T-302 | ✅ DONE |
| Phase 4 | 2 weeks | T-401...T-405 | 📋 READY |
| Phase 5 | 3 weeks | T-501...T-505 | 📅 PLANNED |
| Phase 6 | 2 weeks | T-601...T-604 | 📅 PLANNED |
| Phase 7+ | Future | T-701+ | 🔮 IDEAS |

**Critical Path:** T-401 → T-402 → T-404  
**Estimated MVP:** 4-5 weeks from start of Phase 4

---

## Appendix: Feature Completeness Matrix

```
┌─────────────────────────────────────────────┬──────────┬──────────┬─────────┐
│ Feature Area                                │ Current  │ Desired  │ Gap     │
├─────────────────────────────────────────────┼──────────┼──────────┼─────────┤
│ Viewport & Rendering                        │    80%   │  100%    │   20%   │
│ Polygon Creation & Editing                  │    60%   │  100%    │   40%   │
│ File I/O & Persistence                      │     0%   │  100%    │  100%   │
│ User Feedback & Validation                  │    40%   │  100%    │   60%   │
│ Design Tools (transform, analysis)          │    20%   │  100%    │   80%   │
│ Library & Collections                       │    50%   │  100%    │   50%   │
│ Settings & Preferences                      │     0%   │  100%    │  100%   │
│ Help & Documentation                        │     0%   │  100%    │  100%   │
│ Export & Interop                            │     0%   │  100%    │  100%   │
│ Performance & Optimization                  │    60%   │  100%    │   40%   │
├─────────────────────────────────────────────┼──────────┼──────────┼─────────┤
│ OVERALL                                     │    37%   │  100%    │   63%   │
└─────────────────────────────────────────────┴──────────┴──────────┴─────────┘
```

---

**Next Step:** Review Phase 4 critical tickets and begin sprint planning.
