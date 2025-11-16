# Track A Sequencing & Folder Structure Lock

## Decision 1: Catalogs/ Structure (LOCKED)

**Final structure for data flow:**

```
catalogs/
├── tier0/                          # Complete, fixed
│   ├── tier0_netlib.jsonl
│   ├── unicode_mapping.json
│   └── metadata.json
│
├── tier1/                          # Track A Phase 1 output
│   ├── polyhedra.jsonl             # 110 solids (Platonic + Archimedean + Johnson)
│   ├── decompositions.json         # Tier 0 decompositions for each polyhedron
│   ├── lod_metadata.json           # LOD breakpoints for rendering
│   └── attachment_sequences.json   # How to build each polyhedron (net → solid)
│
├── tier2/                          # Future (runtime candidates)
│   └── tier_candidates.jsonl
│
├── tier3/                          # Future (promoted structures)
│   └── tier3_catalog.jsonl
│
├── attachments/                    # Track A Phase 2 output
│   ├── attachment_matrix.json      # 18×18 polygon pair matrix
│   ├── fold_angles.json            # Dihedral angles by pair
│   ├── stability_scores.json       # Stability thresholds
│   └── context_rules.json          # Context-aware attachment rules
│
├── geometry/                       # Existing (unchanged)
│   ├── geometry_catalog.json
│   ├── scaler_tables.json
│   └── scaffolding/
│       ├── compatibility_index.json
│       ├── metadata.jsonl
│       └── meshes/
│
└── schemas/                        # Existing (unchanged)
    └── attachment_schemas.json
```

**Rationale:**
- `tier1/` groups all 110 polyhedra data (library, decompositions, LOD, sequences)
- `attachments/` separates polygon pair data from polyhedra data (different generation logic)
- `tier2/` and `tier3/` reserved for future promotion pipeline
- Flat structure within each tier (no unnecessary nesting)

---

## Decision 2: Netlib Extraction Folder Paths (LOCKED)

**Scripts location:**
```
scripts/
├── netlib_extractor.py             # Parse Netlib files, extract polyhedra
├── attachment_populator.py         # Extract attachment angles, build matrix
├── lod_generator.py                # Generate LOD breakpoints
└── [other utilities]
```

**Raw data location (temporary, for extraction debugging):**
```
data/
├── netlib_raw/                     # Temporary (git-ignored)
│   ├── [downloaded Netlib files 0-114]
│   └── README.md (instructions for re-downloading)
└── [other data]
```

**Processed output location:**
```
catalogs/tier1/
├── polyhedra.jsonl                 # Final output
├── decompositions.json
├── lod_metadata.json
└── attachment_sequences.json

catalogs/attachments/
├── attachment_matrix.json          # Final output
├── fold_angles.json
├── stability_scores.json
└── context_rules.json
```

**Rationale:**
- Scripts stay in `scripts/` (no new folder needed)
- Raw Netlib files in `data/netlib_raw/` (temporary, git-ignored)
- Processed data in `catalogs/tier1/` and `catalogs/attachments/` (permanent, version-controlled)
- Clear separation: extraction scripts → raw data → processed catalogs

---

## Decision 3: Reorganization Sequencing (LOCKED)

**CHOICE: Option C (Hybrid - Reorganize only Track A-critical folders first)**

**Rationale:**
- **Unblocks Track A fastest** - Netlib extraction can begin in ~1.5 hours instead of 4.5 hours
- **Lowest risk** - Only touch folders needed for Track A; defer cosmetic changes
- **Enables parallel work** - While Track A Phase 1 runs, can work on other Track B tasks
- **Avoids rework** - Full reorganization after Track A Phase 1 completes with real data in place

**Mini-reorganization scope (1.5 hours):**

1. **Create folder structure** (15 min)
   - `mkdir catalogs/tier1 catalogs/tier2 catalogs/tier3 catalogs/attachments`
   - `mkdir data/netlib_raw`
   - Verify `scripts/` exists

2. **Move existing catalogs data** (15 min)
   - Move `catalogs/tier0_netlib.jsonl` → `catalogs/tier0/tier0_netlib.jsonl`
   - Move `catalogs/unicode_mapping.json` → `catalogs/tier0/unicode_mapping.json`
   - Move `catalogs/metadata.json` → `catalogs/tier0/metadata.json`
   - Move `catalogs/attachment_graph.json` → `catalogs/attachments/attachment_graph.json`

3. **Update imports in code** (30 min)
   - Search for references to `catalogs/tier0_netlib.jsonl` → update to `catalogs/tier0/tier0_netlib.jsonl`
   - Search for references to `catalogs/attachment_graph.json` → update to `catalogs/attachments/attachment_graph.json`
   - Update `src/polylog6/storage/` imports
   - Run tests to verify

4. **Defer full reorganization** (after Track A Phase 1)
   - Phases 1-2 (infra + frontend): 1.5 hours
   - Phases 3-4 (backend + engines): 1 hour
   - Phase 5 (docs flatten): 1 hour
   - Phase 6 (cleanup): 1 hour

**Timeline:**
```
Now:
├─ Mini-reorganize (1.5 hours)
│  └─ catalogs/, scripts/, data/ structure locked
│
Track A Phase 1:
├─ Build Netlib extractor (2 hours)
├─ Extract polyhedra + attachment angles (1-2 hours)
└─ Output: catalogs/tier1/, catalogs/attachments/ populated
│
Track A Phase 2:
├─ Generate LOD metadata (1 hour)
├─ Wire tier_candidates.jsonl emission (1 hour)
└─ Output: tier2/ ready for runtime
│
After Track A Phase 1:
├─ Full reorganization (4.5 hours)
│  ├─ Phases 1-2: infra + frontend
│  ├─ Phases 3-4: backend + engines
│  ├─ Phase 5: docs
│  └─ Phase 6: cleanup
└─ Project structure finalized
```

---

## Decision 4: Post-Extraction Workflow (LOCKED)

**After Netlib extraction completes:**

1. **Immediate (same session):**
   - Verify `catalogs/tier1/polyhedra.jsonl` has 110 entries
   - Verify `catalogs/attachments/attachment_matrix.json` has ~180-200 entries
   - Run validation tests to confirm data integrity

2. **Next session (Track A Phase 2):**
   - Generate LOD metadata from polyhedra geometry
   - Wire runtime symbol generation to emit to `tier2/tier_candidates.jsonl`
   - Test Tier 2 candidate emission

3. **Parallel (Track B):**
   - Continue with other system improvements
   - Don't wait for full reorganization to proceed

4. **After Track A Phase 1 complete:**
   - Execute full reorganization (Phases 1-6)
   - Update all documentation
   - Commit with message: "refactor: complete project reorganization after Track A Phase 1"

---

## Action Items (Immediate)

**For IDE bot:**

1. ✅ **Execute mini-reorganization (1.5 hours)**
   - Create folder structure
   - Move tier0 files to `catalogs/tier0/`
   - Move attachment_graph.json to `catalogs/attachments/`
   - Update imports in `src/polylog6/storage/`
   - Run tests to verify

2. ✅ **Lock Netlib extraction paths**
   - Scripts: `scripts/netlib_extractor.py`, `scripts/attachment_populator.py`
   - Raw data: `data/netlib_raw/` (git-ignored)
   - Output: `catalogs/tier1/`, `catalogs/attachments/`

3. ✅ **Prepare for Track A Phase 1**
   - Verify Netlib database is accessible
   - Confirm 18 polygon types in system
   - Ready to build extractor

**For user:**

1. ✅ **Approve decisions** - All three locked above
2. ✅ **Confirm sequencing** - Option C (hybrid mini-reorganize + extract)
3. ✅ **Ready to proceed** - Mini-reorganization can start immediately

---

## Verification Checklist

After mini-reorganization:

- [ ] `catalogs/tier0/` exists with tier0_netlib.jsonl, unicode_mapping.json, metadata.json
- [ ] `catalogs/tier1/` exists (empty, ready for extraction)
- [ ] `catalogs/tier2/` exists (empty, reserved)
- [ ] `catalogs/tier3/` exists (empty, reserved)
- [ ] `catalogs/attachments/` exists with attachment_graph.json
- [ ] `data/netlib_raw/` exists (git-ignored)
- [ ] `scripts/` exists with utility scripts
- [ ] All imports updated in `src/polylog6/storage/`
- [ ] Tests pass: `pytest tests/ -v`
- [ ] Git status clean (no uncommitted changes except new folders)

---

## Git Commit Message (After Mini-Reorganization)

```
refactor: reorganize catalogs structure for Track A data flow

- Create tier0/, tier1/, tier2/, tier3/ folders in catalogs/
- Create attachments/ folder for polygon pair data
- Move tier0 files to catalogs/tier0/
- Move attachment_graph.json to catalogs/attachments/
- Update imports in src/polylog6/storage/ to reflect new paths
- Add data/netlib_raw/ for temporary Netlib extraction files
- Prepare structure for Track A Phase 1 (Netlib extraction)

This is a mini-reorganization focused on Track A critical paths.
Full project reorganization (infra/, frontend/, docs/) deferred to
after Track A Phase 1 completes.
```

