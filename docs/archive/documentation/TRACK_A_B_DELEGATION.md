# Track A & B Delegation: Clear Ownership & Roadmap

## Overview

**Track A (Core System):** Phases 1-6, 10-16 hours, sequential execution
**Track B (Advanced Features):** Phase 7+, 4-6 weeks, after Track A complete

---

## Track A: Core System Development

### Track A Phase 1: Data & API ✅ COMPLETE

**Owner:** Backend team (completed)
**Status:** Live and tested
**Deliverables:**
- ✅ 97 polyhedra extracted from Netlib
- ✅ 18×18 attachment matrix (324 pairs, 100% populated)
- ✅ Fold angles + stability scores calculated
- ✅ 6 API endpoints live
- ✅ LOD metadata generated (4 levels per polyhedron)

**What Works:**
- ✅ Static edge matching (matrix lookup)
- ✅ Face topology (fixed per polyhedron)
- ✅ LOD rendering (4 levels)
- ✅ Compression ratio calculation

**Handoff to Phase 2:** All data ready, APIs live, ready for frontend integration

---

### Track A Phase 2: Frontend Integration ⏳ 2-3 HOURS (START NOW)

**Owner:** Frontend team
**Status:** Ready to start immediately
**Blocker:** None (all data ready)

**Deliverables:**
1. Workspace component with drag-and-drop
2. Real-time edge matching validation
3. Visual feedback (green/red attachment indicators)
4. Fold angle options displayed with stability scores
5. Attachment preview (3D visualization before confirming)
6. LOD switching in viewport
7. API integration for attachment queries
8. All 97 polyhedra renderable
9. 60 FPS maintained
10. <100ms API response time

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

**Easy Wins (Quick Wins):**
1. Wire attachment validation UI (30 min)
   - Service methods exist (storageService.ts)
   - API endpoints live (GET /tier1/attachments)
   - Just need: UI components + validation logic

2. Add edge stability display (15 min)
   - Stability scores in attachment_matrix.json
   - Show stability badge (green/yellow/red)
   - Just need: Badge component

3. Implement attachment preview (1 hour)
   - THREE.js rendering works
   - Show 3D preview of attachment
   - Just need: Preview logic + UI

**Success Criteria:**
- [ ] All 97 polyhedra render correctly
- [ ] LOD switching works smoothly
- [ ] Export/import round-trip successful
- [ ] 60 FPS rendering maintained
- [ ] <100ms API response time
- [ ] Attachment validation prevents invalid placements
- [ ] Stability scores displayed correctly
- [ ] Fold angle options shown accurately

**Handoff to Phase 3:** User can place polyhedra, see valid attachments, confirm placements

---

### Track A Phase 3: Runtime Symbol Generation ⏳ 1-2 HOURS (AFTER PHASE 2)

**Owner:** Backend team
**Status:** Ready after Phase 2 complete
**Blocker:** Phase 2 must complete first (need runtime assembly data)

**Deliverables:**
1. Background analysis of user assembly
2. Composition detection (polygon count + types)
3. Symmetry analysis
4. Candidate emission to tier_candidates.jsonl
5. Frequency tracking begins
6. Display: "Analyzing... Possible new polyform discovered!"

**Edge Matching Work:**
- Validate: All edge attachments in assembly are stable
- Score: Overall assembly edge stability
- Emit: Edge stability in candidate metadata
- Reuse: If assembly matches known polyhedron, emit reference

**Face Matching Work:**
- Analyze: Face connectivity in assembly
- Detect: Are any faces already "merged"?
- Count: Total faces in assembly
- Score: Face stability contribution

**Easy Wins:**
1. Add emission code template (30 min)
   - File path defined (tier_candidates.jsonl)
   - Format documented
   - Just need: Function to emit candidate

2. Add composition analysis (1 hour)
   - Polygon count calculation
   - Symmetry detection
   - Stability scoring

**Success Criteria:**
- [ ] Candidates emitted to tier_candidates.jsonl
- [ ] Logging shows emissions
- [ ] File format valid
- [ ] No data loss
- [ ] Frequency tracking working
- [ ] Edge stability recorded in metadata

**Handoff to Phase 4:** Tier 2 candidates being generated, ready for ingestion

---

### Track A Phase 4: Tier 2 Ingestion ⏳ 1-2 HOURS (AFTER PHASE 3)

**Owner:** Backend team
**Status:** Ready after Phase 3 complete
**Blocker:** Phase 3 must emit candidates first

**Deliverables:**
1. Ingestion pipeline for tier_candidates.jsonl
2. Candidate validation
3. Storage in Tier 2 catalog
4. API access to candidates
5. Frequency tracking persistence

**Edge Matching Work:**
- Persist: Edge matching data in candidate record
- Query: "How stable are edges in this candidate?"
- Score: Use edge stability as promotion criterion

**Face Matching Work:**
- Persist: Face connectivity in candidate record
- Analyze: Are faces already optimized (merged)?
- Score: Use face count as compression criterion
- Flag: If assembly is closed (0 boundary edges)

**Easy Wins:**
1. Add candidate validation (1 hour)
   - Candidate format defined
   - Create validation function
   - Check integrity

2. Add ingestion logic (30 min)
   - Read tier_candidates.jsonl
   - Parse JSON
   - Store in Tier 2 catalog

**Success Criteria:**
- [ ] Candidates ingested correctly
- [ ] Validation working
- [ ] API returns candidates
- [ ] Data consistency verified
- [ ] Frequency tracking accurate

**Handoff to Phase 5:** Tier 2 catalog populated, ready for promotion

---

### Track A Phase 5: Tier 3 Promotion ⏳ 2-3 HOURS (AFTER PHASE 4)

**Owner:** Backend team
**Status:** Ready after Phase 4 complete
**Blocker:** Phase 4 must ingest candidates first

**Deliverables:**
1. Promotion criteria implementation (frequency ≥10, stability ≥0.85)
2. Promotion algorithm
3. Tier 3 catalog population
4. API access to promoted structures
5. Symbol assignment (Φₙ)

**Edge Matching Work:**
- Check: All edge attachments ≥0.85 stable?
- Validate: Edge matching rules are sound
- Archive: Store edge rules in Tier 3 symbol

**Face Matching Work:**
- Optimize: Attempt face merging (coplanar faces)
- Benefit: Merged assembly may have better compression
- Archive: Store optimized face topology in Tier 3

**Easy Wins:**
1. Add promotion criteria check (30 min)
   - Criteria defined (frequency ≥10, stability ≥0.85)
   - Create function to check
   - Return promotion decision

2. Add promotion algorithm (1 hour)
   - Iterate through Tier 2 candidates
   - Check criteria
   - Promote if eligible
   - Assign symbol

**Success Criteria:**
- [ ] Promotion criteria applied
- [ ] Structures promoted to Tier 3
- [ ] API returns promoted structures
- [ ] Promotion history tracked
- [ ] Symbols assigned correctly

**Handoff to Phase 6:** Tier 3 catalog populated, ready for testing

---

### Track A Phase 6: Testing & Validation ⏳ 4-6 HOURS (PARALLEL WITH PHASE 5)

**Owner:** QA team
**Status:** Can start immediately (no blockers)
**Blocker:** None

**Deliverables:**
1. Unit tests for all components
2. Integration tests for full pipeline
3. Performance tests
4. Data validation tests
5. End-to-end tests
6. Deployment readiness verification

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

**Success Criteria:**
- [ ] All tests passing
- [ ] Performance targets met
- [ ] Data consistency verified
- [ ] Edge cases handled
- [ ] Documentation complete
- [ ] Deployment checklist complete

**Handoff to Track B:** Track A complete, ready for advanced features

---

## Track B: Advanced Features & Discovery

### Track B Phase 7+: Discovery & Advanced Matching ⏳ FUTURE (AFTER TRACK A)

**Owner:** Research team
**Status:** Planning phase (starts after Track A complete)
**Blocker:** All Track A phases must complete first

**Deliverables:**
1. Dynamic edge angles (user-specified fold angles)
2. Face merging implementation
3. Closure detection
4. Novel polyform discovery
5. Research library integration
6. Community publishing

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

**Timeline:** 4-6 weeks after Track A complete

---

## Parallel Work Opportunities

### Can Start Immediately (No Blockers)
- ✅ Phase 2 (Frontend) - All data ready
- ✅ Phase 6 (Testing) - Can write tests now

### Can Start After Phase 2
- ⏳ Phase 3 (Runtime) - Needs assembly data from Phase 2

### Can Start After Phase 3
- ⏳ Phase 4 (Ingestion) - Needs candidates from Phase 3

### Can Start After Phase 4
- ⏳ Phase 5 (Promotion) - Needs Tier 2 catalog from Phase 4

### Can Start After Track A Complete
- ⏳ Phase 7+ (Discovery) - Needs all Track A phases

---

## Easy Wins Checklist (Quick Wins for Immediate Action)

### Frontend Team (Phase 2)
- [ ] Easy Win 1: Wire attachment validation UI (30 min)
- [ ] Easy Win 2: Add edge stability display (15 min)
- [ ] Easy Win 3: Implement attachment preview (1 hour)

### Backend Team (Phase 3)
- [ ] Easy Win 4: Add emission code template (30 min)
- [ ] Easy Win 5: Add composition analysis (1 hour)

### Backend Team (Phase 4)
- [ ] Easy Win 6: Add candidate validation (1 hour)
- [ ] Easy Win 7: Add ingestion logic (30 min)

### Backend Team (Phase 5)
- [ ] Easy Win 8: Add promotion criteria check (30 min)
- [ ] Easy Win 9: Add promotion algorithm (1 hour)

### QA Team (Phase 6)
- [ ] Easy Win 10: Create unit test suite (2 hours)
- [ ] Easy Win 11: Create integration tests (2 hours)
- [ ] Easy Win 12: Create performance tests (1 hour)

**Total Easy Wins Effort:** 10-11 hours (can be done in parallel)

---

## Document Cleanup

### Archive (Handoff Complete)
- Move to archive/: VISUAL_BRIEF_ALIGNMENT_ANALYSIS.md
- Move to archive/: CORRECTED_VISUAL_BRIEF.md
- Move to archive/: VISUAL_GENERATION_HANDOFF.md
- Move to archive/: ALIGNMENT_REPORT.md

### Keep (Active Development)
- ✅ PROJECT_SCOPE_AND_BLOCKERS.md (reference)
- ✅ IMPLEMENTATION_ROADMAP.md (reference)
- ✅ ZERO_BLOCKER_SUMMARY.md (reference)
- ✅ EDGE_FACE_MATCHING_ARCHITECTURE.md (active)
- ✅ TRACK_A_B_DELEGATION.md (this document - active)

### Create (New)
- ⏳ TRACK_A_PHASE_2_TASKS.md (detailed Phase 2 tasks)
- ⏳ TRACK_B_ROADMAP.md (Track B planning)
- ⏳ EASY_WINS_CHECKLIST.md (quick wins tracking)

---

## Status: READY FOR EXECUTION

**Track A Phase 2:** Ready to start immediately (2-3 hours, no blockers)
**Track B Phase 7+:** Planning complete, starts after Track A (4-6 weeks)
**Easy Wins:** 10-11 hours of quick wins identified
**Delegation:** Clear ownership, sequential dependencies, parallel opportunities

