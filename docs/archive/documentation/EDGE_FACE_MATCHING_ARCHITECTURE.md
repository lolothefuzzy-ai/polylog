# Edge & Face Matching Architecture: Current vs. Intended

## Executive Summary

This document defines the geometric validation architecture for Polylog6 across two states:
- **Current (MVP - Phase 1):** Static edge matching via pre-computed matrix, fixed face topology
- **Intended (Full System - Phases 2-7+):** Dynamic edge/face validation, closure detection, novel polyform discovery

---

## Part 1: Edge Matching Architecture

### Current State (MVP - Phase 1) ✅

**What We Have:**
- ✅ 18×18 attachment matrix (324 pairs, 100% populated)
- ✅ Fold angles extracted from Netlib dihedral fields
- ✅ Stability scores calculated (0.0-1.0)
- ✅ Static validation: O(1) matrix lookup

**Edge Matching Rule (Current):**
```
Two polygons can attach if:
├─ Both have identical edge length (unit edges, no scaling)
├─ Dihedral angle falls within stable range (±2° tolerance)
├─ Resulting fold maintains positive volume (not inverted)
├─ Shared edge count = 1 (one edge per attachment)
└─ Stability score ≥ 0.85 (or ≥0.70 in mixed contexts)

Validation: O(1) lookup in attachment_matrix.json
```

**Example: Triangle ↔ Square**
```
Triangle (a₃): 3 edges, each length = 1 unit
Square (b₂): 4 edges, each length = 1 unit

Attachment: Share 1 edge
├─ Fold angle: 60° (from Netlib dihedral)
├─ Stability: 0.78 (conditionally stable)
└─ Result: Valid attachment (tetrahedron-like boundary)
```

**Current Limitations:**
- ❌ No runtime validation during user assembly
- ❌ No edge length scaling
- ❌ No custom fold angles
- ❌ No multi-edge attachments
- ❌ No real-time feedback

---

### Intended State (Full System - Phases 2-7+) ⏳

**What We're Building:**

**Phase 2 (Frontend):** Runtime validation
- User places polygon → System queries valid options
- Shows fold angle options with stability scores
- Real-time validation (green = valid, red = invalid)

**Phase 3 (Runtime):** Dynamic edge matching
- User assembles structure → System analyzes edges
- Detects edge connectivity
- Validates each attachment
- Scores overall stability

**Phase 7+ (Discovery):** Algorithmic edge matching
- Custom fold angles (not just Netlib pre-computed)
- Edge length scaling with polynomial growth
- Multi-edge attachments (shared faces)
- Closure detection

**Intended Edge Matching Rule (Full):**
```
Two polygons can attach via edge if:
├─ Edge lengths match (or scale by polynomial factor k)
├─ Fold angle within stable range (computed, not just lookup)
├─ Surface normal alignment ≥ threshold (geometry, not topology)
├─ Attachment preserves non-self-intersection
├─ Optional: Multi-edge attachments allowed (shared faces)
└─ Stability score ≥ threshold (context-dependent, 0.70-0.95)

Validation: O(1) lookup + O(n) geometric verification
```

---

## Part 2: Face Matching Architecture

### Current State (MVP - Phase 1) ✅

**What We Have:**
- ✅ Fixed polyhedra from Netlib (face topology pre-computed)
- ✅ Face definitions: vertex lists per polyhedron
- ✅ LOD decimation: faces can be simplified (4 levels)
- ✅ Normal direction validation

**Face Matching Rule (Current):**
```
Polyhedra faces are fixed from Netlib extraction:
├─ Each face has defined vertex sequence (e.g., [v0, v1, v2])
├─ Face normals point outward (always)
├─ Faces don't merge or split
├─ LOD simplification removes faces (doesn't create them)
└─ Assembly = collection of polyhedra (no face merging)

Validation: Static, no runtime face matching
```

**Current Limitations:**
- ❌ No face-to-face contact detection
- ❌ No face merging (coplanar faces)
- ❌ No hole detection (boundary loops)
- ❌ No closure validation
- ❌ No real-time mesh optimization

---

### Intended State (Full System - Phases 2-7+) ⏳

**What We're Building:**

**Phase 2 (Frontend):** Face contact detection
- Detect face-to-face contact
- Validate if faces are coplanar
- Prepare for merging

**Phase 4-5 (Runtime):** Face merging & closure
- Adjacent coplanar faces merge into single face
- Reduces vertex/edge count
- Improves compression ratio
- Detects when assembly "closes" (no boundary edges)

**Phase 7+ (Discovery):** Closure detection & polyform discovery
- Validates closure is geometrically sound
- Scores novel polyforms
- Auto-promotes if stable

**Intended Face Matching Rule (Full):**
```
Two faces can match/merge if:
├─ Edge sequence is compatible (shared edge exists)
├─ Face normals point outward (not inward or parallel)
├─ Faces are coplanar (or within tolerance)
├─ Merging preserves convexity (or marks as concave)
├─ Resulting face is non-degenerate (area > 0)
└─ Optional: Merge multiple coplanar faces into single face

Closure validation:
├─ All boundary edges must have a matching edge somewhere
├─ No edge is left unmatched ("boundary loop")
└─ If all edges matched: assembly is closed/valid
```

---

## Part 3: Implementation Roadmap

### Phase 1: Data & API ✅ COMPLETE
- ✅ Extract polyhedra from Netlib
- ✅ Build 18×18 attachment matrix
- ✅ Compute edge fold angles + stability
- ✅ Expose via 6 API endpoints
- ✅ Deploy LOD metadata

**What Works:**
- ✅ Static edge matching (matrix lookup)
- ✅ Face topology (fixed per polyhedron)
- ✅ LOD rendering (4 levels)
- ✅ Compression ratio calculation

---

### Phase 2: Frontend Integration ⏳ 2-3 HOURS

**Edge Matching Work:**
- Implement: Query GET /tier1/attachments/{a}/{b} when user places polygon
- Display: Fold angle options with stability scores
- Validate: Attachment is ≥0.85 stable (or user chooses conditionally stable)
- Prevent: Placement of invalid attachments
- Visual: Show attachment preview before confirming

**Face Matching Work:**
- Detect: When faces are adjacent (not yet merged)
- Display: Face normal vectors in viewport
- Prepare: Foundation for future face merging

**Easy Wins:**
- ✅ Service methods already exist (storageService.ts)
- ✅ API endpoints live (GET /tier1/attachments)
- ✅ Data ready (attachment_matrix.json)
- ⏳ Just need: UI components + real-time validation logic

---

### Phase 3: Runtime Symbol Generation ⏳ 1-2 HOURS

**Edge Matching Work:**
- Validate: All edge attachments in assembly are stable
- Score: Overall assembly edge stability
- Emit: Edge stability in candidate metadata

**Face Matching Work:**
- Analyze: Face connectivity in assembly
- Detect: Are any faces already "merged"?
- Count: Total faces in assembly
- Score: Face stability contribution

---

### Phase 4: Tier 2 Ingestion ⏳ 1-2 HOURS

**Edge Matching Work:**
- Persist: Edge matching data in candidate record
- Query: "How stable are edges in this candidate?"
- Score: Use edge stability as promotion criterion

**Face Matching Work:**
- Persist: Face connectivity in candidate record
- Analyze: Are faces already optimized (merged)?
- Score: Use face count as compression criterion
- Flag: If assembly is closed (0 boundary edges)

---

### Phase 5: Tier 3 Promotion ⏳ 2-3 HOURS

**Edge Matching Work:**
- Check: All edge attachments ≥0.85 stable?
- Validate: Edge matching rules are sound
- Archive: Store edge rules in Tier 3 symbol

**Face Matching Work:**
- Optimize: Attempt face merging (coplanar faces)
- Benefit: Merged assembly may have better compression
- Archive: Store optimized face topology in Tier 3

---

### Phase 6: Testing & Validation ⏳ 4-6 HOURS

**Edge Matching Tests:**
- Test case 1: Place tetrahedron (4 triangles, all stable)
- Test case 2: Place invalid attachment (should reject)
- Test case 3: Mixed stability (user chooses conditionally stable)
- Test case 4: Assembly recreated → same symbol generated
- Performance: Edge matching <5ms per lookup

**Face Matching Tests:**
- Test case 1: Cube (6 separate faces, no merging)
- Test case 2: Two coplanar triangles (can merge → quad)
- Test case 3: Closed assembly (0 boundary edges detected)
- Test case 4: Open assembly (boundary edges tracked)
- Performance: Face analysis <10ms per assembly

---

### Phase 7+: Discovery & Advanced Matching ⏳ FUTURE

**Edge Matching Work:**
- Allow: Custom fold angles (not just Netlib pre-computed)
- Validate: Will custom angle close assembly?
- Compute: Dihedral angle dynamically
- Cache: Successful custom angles

**Face Matching Work:**
- Implement: Face merging for coplanar faces
- Detect: When assembly reaches closure
- Optimize: Merge faces to reduce polygon count
- Promote: Closed polyforms automatically to Tier 2
- Publish: Novel discoveries to research library

---

## Part 4: Track A vs. Track B Delegation

### Track A: Core System Development (Current Focus)

**Track A Phase 1:** Data & API ✅ COMPLETE
- Deliverables: 97 polyhedra, 18×18 matrix, 6 API endpoints
- Status: Live and tested

**Track A Phase 2:** Frontend Integration (NEXT - 2-3 hours)
- Deliverables:
  - React workspace component with drag-and-drop
  - Real-time edge matching validation
  - Visual feedback (green/red attachment indicators)
  - LOD switching in viewport
  - API integration for attachment queries
- Owner: Frontend team
- Blocker: None (all data ready)
- Easy wins:
  - Service methods exist (just wire them)
  - API endpoints live (just call them)
  - Attachment data ready (just display it)

**Track A Phase 3:** Runtime Symbol Generation (1-2 hours after Phase 2)
- Deliverables:
  - Background analysis of user assembly
  - Composition detection (polygon count + types)
  - Symmetry analysis
  - Emit candidates to tier_candidates.jsonl
- Owner: Backend team
- Blocker: Phase 2 must complete first
- Easy wins:
  - Emission code structure exists (just wire it)
  - Candidate format defined (just populate it)
  - File path ready (just write to it)

**Track A Phase 4:** Tier 2 Ingestion (1-2 hours after Phase 3)
- Deliverables:
  - Read tier_candidates.jsonl
  - Validate candidates
  - Store in Tier 2 catalog
  - API access to candidates
- Owner: Backend team
- Blocker: Phase 3 must emit candidates first

**Track A Phase 5:** Tier 3 Promotion (2-3 hours after Phase 4)
- Deliverables:
  - Promotion criteria implementation
  - Promotion algorithm
  - Tier 3 catalog population
  - API access to promoted structures
- Owner: Backend team
- Blocker: Phase 4 must ingest candidates first

**Track A Phase 6:** Testing & Validation (4-6 hours, parallel with Phase 5)
- Deliverables:
  - Unit tests for all components
  - Integration tests for full pipeline
  - Performance tests
  - Data validation tests
  - End-to-end tests
- Owner: QA team
- Blocker: None (can start immediately)

---

### Track B: Advanced Features & Discovery (Future Focus)

**Track B Phase 7+:** Discovery & Advanced Matching
- Deliverables:
  - Dynamic edge angles (user-specified fold angles)
  - Face merging implementation
  - Closure detection
  - Novel polyform discovery
  - Research library integration
- Owner: Research team
- Blocker: Track A Phases 1-6 must complete first
- Timeline: 4-6 weeks after Track A complete

---

## Part 5: Easy Wins (Immediate Actions)

### Easy Win 1: Wire Attachment Validation UI (Phase 2)
**Current State:** API endpoint exists, returns valid fold angles
**Action:** Create React component showing fold angle options
**Effort:** 30 minutes
**Blocker:** None
**Owner:** Frontend team

### Easy Win 2: Add Edge Stability Display (Phase 2)
**Current State:** Stability scores in attachment_matrix.json
**Action:** Show stability badge (green/yellow/red) on each fold angle option
**Effort:** 15 minutes
**Blocker:** None
**Owner:** Frontend team

### Easy Win 3: Implement Attachment Preview (Phase 2)
**Current State:** THREE.js rendering works
**Action:** Show 3D preview of attachment before confirming
**Effort:** 1 hour
**Blocker:** None
**Owner:** Frontend team

### Easy Win 4: Add Emission Code Template (Phase 3)
**Current State:** File path defined, format documented
**Action:** Create function to emit candidate to tier_candidates.jsonl
**Effort:** 30 minutes
**Blocker:** None
**Owner:** Backend team

### Easy Win 5: Add Candidate Validation (Phase 4)
**Current State:** Candidate format defined
**Action:** Create validation function to check candidate integrity
**Effort:** 1 hour
**Blocker:** None
**Owner:** Backend team

### Easy Win 6: Add Promotion Criteria Check (Phase 5)
**Current State:** Criteria defined (frequency ≥10, stability ≥0.85)
**Action:** Create function to check if candidate meets criteria
**Effort:** 30 minutes
**Blocker:** None
**Owner:** Backend team

---

## Part 6: Cleanup & Organization

### Documents to Archive (No Longer Needed)
- ❌ VISUAL_BRIEF_ALIGNMENT_ANALYSIS.md (handoff complete, move to archive)
- ❌ CORRECTED_VISUAL_BRIEF.md (handoff complete, move to archive)
- ❌ VISUAL_GENERATION_HANDOFF.md (handoff complete, move to archive)

### Documents to Keep (Active Development)
- ✅ PROJECT_SCOPE_AND_BLOCKERS.md (reference for scope)
- ✅ IMPLEMENTATION_ROADMAP.md (reference for phases)
- ✅ ZERO_BLOCKER_SUMMARY.md (reference for status)
- ✅ ALIGNMENT_REPORT.md (reference for alignment)
- ✅ EDGE_FACE_MATCHING_ARCHITECTURE.md (this document - active)

### New Documents to Create
- ⏳ TRACK_A_PHASE_2_TASKS.md (detailed Phase 2 tasks)
- ⏳ TRACK_B_ROADMAP.md (Track B planning)
- ⏳ EASY_WINS_CHECKLIST.md (quick wins for immediate action)

---

## Part 7: Updated Project Intent

### Original Intent
"Build a hierarchical polyform compression and discovery system enabling users to design, compose, and discover novel geometric structures through tiered symbolic representation."

### Updated Intent (With Edge/Face Matching)
"Build a hierarchical polyform compression and discovery system with geometric validation architecture enabling:

1. **Static Validation (MVP - Phase 1):** Pre-computed edge matching via 18×18 attachment matrix with fold angles and stability scores
2. **Runtime Validation (Phases 2-3):** Real-time edge matching during user assembly with visual feedback and dynamic stability scoring
3. **Face Topology (Phases 4-5):** Face-to-face contact detection, coplanar face merging, and closure validation
4. **Algorithmic Discovery (Phase 7+):** Custom fold angles, edge length scaling, multi-edge attachments, and novel polyform discovery

Users can design, compose, and discover novel geometric structures through interactive assembly with full geometric validation, automatic symbol generation, and promotion through tiered archive system."

---

## Part 8: Success Criteria (Updated)

### Phase 1 ✅ COMPLETE
- ✅ 97 polyhedra extracted
- ✅ 18×18 attachment matrix (100% populated)
- ✅ Edge fold angles + stability scores calculated
- ✅ 6 API endpoints live
- ✅ LOD metadata generated

### Phase 2 ⏳ READY TO START
- [ ] Workspace component with drag-and-drop
- [ ] Real-time edge matching validation
- [ ] Visual feedback (green/red indicators)
- [ ] Fold angle options displayed
- [ ] Stability scores shown
- [ ] Attachment preview working
- [ ] LOD switching functional
- [ ] All 97 polyhedra renderable
- [ ] 60 FPS maintained
- [ ] <100ms API response time

### Phase 3 ⏳ AFTER PHASE 2
- [ ] Background composition analysis
- [ ] Edge stability scoring
- [ ] Candidate emission to tier_candidates.jsonl
- [ ] Frequency tracking begins
- [ ] Symbol generation working

### Phase 4 ⏳ AFTER PHASE 3
- [ ] Candidate ingestion from file
- [ ] Validation of candidate format
- [ ] Storage in Tier 2 catalog
- [ ] API access to candidates

### Phase 5 ⏳ AFTER PHASE 4
- [ ] Promotion criteria checking
- [ ] Promotion algorithm working
- [ ] Tier 3 catalog populated
- [ ] API access to promoted structures

### Phase 6 ⏳ PARALLEL WITH PHASE 5
- [ ] All unit tests passing
- [ ] All integration tests passing
- [ ] Performance targets met
- [ ] Data consistency verified
- [ ] End-to-end flow working

### Phase 7+ ⏳ FUTURE
- [ ] Dynamic edge angles supported
- [ ] Face merging implemented
- [ ] Closure detection working
- [ ] Novel polyforms discovered
- [ ] Research library populated

---

## Part 9: Current Blockers (None for Phase 2)

**Phase 2 Blockers:** None
- ✅ All data ready
- ✅ All APIs live
- ✅ All service methods exist
- ✅ Ready to start immediately

**Phase 3 Blockers:** Phase 2 must complete
- ⏳ Need runtime assembly data
- ⏳ Need user composition tracking

**Phase 4 Blockers:** Phase 3 must emit candidates
- ⏳ Need tier_candidates.jsonl populated
- ⏳ Need candidate format validated

**Phase 5 Blockers:** Phase 4 must ingest candidates
- ⏳ Need Tier 2 catalog populated
- ⏳ Need frequency tracking data

---

## Part 10: Handoff to Track A/B Teams

### For Track A (Core System)

**Immediate (Phase 2 - Start Now):**
1. Create workspace component
2. Wire attachment validation UI
3. Implement fold angle display
4. Add stability score badges
5. Create attachment preview
6. Test with all 97 polyhedra

**Next (Phase 3 - After Phase 2):**
1. Add background composition analysis
2. Implement edge stability scoring
3. Create candidate emission code
4. Wire frequency tracking
5. Test symbol generation

**Then (Phase 4-5 - Sequential):**
1. Implement candidate ingestion
2. Add promotion criteria checking
3. Implement promotion algorithm
4. Create Tier 3 catalog
5. Wire API endpoints

**Finally (Phase 6 - Parallel):**
1. Create comprehensive test suite
2. Performance testing
3. Data validation
4. End-to-end testing
5. Deployment readiness

### For Track B (Advanced Features)

**Future (Phase 7+ - After Track A Complete):**
1. Research dynamic edge angles
2. Implement face merging algorithm
3. Build closure detection
4. Create discovery pipeline
5. Integrate research library

---

## Status: READY FOR TRACK A/B EXECUTION

**Track A Phase 2 Ready:** All blockers cleared, easy wins identified, 2-3 hour estimate
**Track B Planning:** Roadmap defined, dependencies clear, 4-6 week estimate after Track A
**Project Intent Updated:** Edge/face matching architecture integrated
**Delegation Clear:** Track A owns Phases 1-6, Track B owns Phase 7+

