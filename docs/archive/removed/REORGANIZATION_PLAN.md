# Polylog6 Reorganization Plan

## Current State Assessment

### ✅ Completed
- Cleanup of legacy GUI code (Properties/Code)
- Removal of outdated documentation
- GitHub configuration fixes (.mergify.yml, .gitignore, README.md)
- Tier 0 catalog fully functional

### 🔴 Critical Gaps (Blocking Tier 1-3)

**1. Attachment Graph Sparse**
- Only A↔A connections defined
- Need: 180-200 entries for 18×18 polygon pairs with fold angles
- Impact: Users can't see valid attachment options when placing polygons
- Status: Framework exists (attachment_schemas.py), data missing

**2. Tier 1 Polyhedra Missing**
- 110 known solids not encoded (5 Platonic + 13 Archimedean + 92 Johnson)
- Need: Decompositions, attachment sequences, LOD breakpoints
- Impact: No reference library for symbol generation
- Status: Netlib database accessible, extraction needed

**3. Runtime Symbol Generation Not Wired**
- tier_candidates.jsonl not receiving emissions
- Impact: Tier 2/3 promotion pipeline blocked
- Status: Infrastructure exists, integration needed

**4. LOD Metadata Incomplete**
- Only placeholder entries exist
- Need: Performance breakpoints for all 110 polyhedra
- Status: Framework ready, data generation needed

---

## Proposed Folder Reorganization

### Goal
- Reduce nesting depth (≤4 levels)
- Group by function and interaction pattern
- Separate development artifacts from runtime/deployment
- Organize by file type where beneficial

### Current Structure Issues
```
Polylog6/
├── src/
│   ├── polylog6/          # Backend Python
│   ├── components/        # Frontend React
│   ├── services/          # Frontend services
│   ├── utils/             # Frontend utils
│   ├── *.jsx/*.css        # Frontend root files (scattered)
│   └── *.ts               # Frontend types (scattered)
├── catalogs/              # Runtime data
├── config/                # Config files
├── docs/                  # Documentation (deeply nested)
├── scripts/               # Build/utility scripts
├── tests/                 # Tests (scattered)
├── build/                 # Build artifacts
├── .github/               # CI/CD
├── node_modules/          # Dependencies
└── [root files]           # Scattered config files
```

### Proposed Structure

```
Polylog6/
│
├── 📋 .github/            # GitHub automation (workflows, mergify)
├── 📋 .vscode/            # IDE config
├── 📋 config/             # Application config (monitoring.yaml, etc.)
│
├── 🔧 infra/              # Infrastructure & deployment
│   ├── docker-compose.yml
│   ├── build-sidecar.py
│   ├── build.ps1
│   ├── build_installer.bat
│   ├── install_dependencies.bat
│   ├── launch_api.bat
│   ├── launch_gui.bat
│   ├── start.bat
│   ├── launcher.py
│   ├── polylog_core.py
│   ├── polylog_main.py
│   └── rustup-init.exe
│
├── 📚 docs/               # Documentation (flattened)
│   ├── architecture/      # Architecture docs
│   ├── design/            # Design docs
│   ├── research/          # Research notes
│   ├── roadmap/           # Roadmap & status
│   ├── reference/         # Reference materials
│   ├── runbooks/          # Operational runbooks
│   ├── archive/           # Archived docs [DATE_reason]
│   └── README.md
│
├── 📦 catalogs/           # Runtime data (Tier 0-3)
│   ├── tier0/
│   │   ├── tier0_netlib.jsonl
│   │   ├── unicode_mapping.json
│   │   └── metadata.json
│   ├── tier1/             # NEW: Polyhedra library
│   │   ├── polyhedra.jsonl
│   │   ├── decompositions.json
│   │   └── lod_metadata.json
│   ├── tier2/             # NEW: Generated candidates
│   │   └── tier_candidates.jsonl
│   ├── tier3/             # NEW: Promoted structures
│   │   └── tier3_catalog.jsonl
│   ├── attachments/       # NEW: Attachment data
│   │   ├── attachment_graph.json
│   │   └── attachment_matrix.json
│   ├── geometry/
│   │   ├── geometry_catalog.json
│   │   ├── scaler_tables.json
│   │   └── scaffolding/
│   │       ├── compatibility_index.json
│   │       ├── metadata.jsonl
│   │       └── meshes/
│   └── schemas/           # Schema definitions
│       └── attachment_schemas.json
│
├── 🎨 frontend/           # React/TypeScript frontend
│   ├── public/
│   │   ├── index.html
│   │   └── locales/
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── services/      # API services
│   │   ├── utils/         # Utilities
│   │   ├── hooks/         # Custom hooks
│   │   ├── styles/        # CSS files
│   │   │   ├── App.css
│   │   │   └── index.css
│   │   ├── types/         # TypeScript types
│   │   │   └── api.generated.ts
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── vite.config.js
│   ├── tsconfig.json
│   ├── package.json
│   └── package-lock.json
│
├── 🐍 backend/            # Python backend
│   ├── src/
│   │   └── polylog6/
│   │       ├── api/
│   │       ├── combinatorial/
│   │       ├── detection/
│   │       ├── discovery/
│   │       ├── hardware/
│   │       ├── monitoring/
│   │       ├── simulation/
│   │       │   ├── engines/
│   │       │   │   ├── analysis/
│   │       │   │   ├── checkpointing/
│   │       │   │   ├── core/
│   │       │   │   ├── analysis.py
│   │       │   │   ├── config.py
│   │       │   │   ├── core.py
│   │       │   │   └── guardrails.py
│   │       │   ├── metrics/
│   │       │   ├── engine.py
│   │       │   ├── runtime.py
│   │       │   └── tier3_ingestion.py
│   │       ├── storage/
│   │       └── ui/
│   ├── tests/
│   ├── requirements.txt
│   └── pytest.ini
│
├── 🧪 tests/              # Test suite (consolidated)
│   ├── fixtures/
│   ├── storage/
│   ├── uat/
│   ├── conftest.py
│   └── test_*.py
│
├── 📜 scripts/            # Utility scripts
│   ├── catalog_generators.py
│   ├── compression_metrics.py
│   ├── netlib_extractor.py    # NEW: Polyhedra extraction
│   ├── attachment_populator.py # NEW: Attachment matrix generation
│   └── [other utilities]
│
├── 🔒 schemas/            # Schema definitions (if needed)
│   └── [schema files]
│
├── 💾 storage/            # Runtime storage
│   ├── chunks/
│   └── [runtime data]
│
├── 🏗️ build/              # Build artifacts (gitignored)
│   └── [build output]
│
├── 📦 node_modules/       # Dependencies (gitignored)
├── 🐍 venv/               # Python venv (gitignored)
│
├── 🔗 src-tauri/          # Tauri sidecar (if applicable)
├── 🌐 web_portal/         # Web portal (if applicable)
│
└── 📄 Root config files
    ├── .gitignore
    ├── .mergify.yml
    ├── .codecov.yml
    ├── README.md
    ├── INSTALL.md
    ├── pytest.ini
    └── [other root configs]
```

---

## Migration Steps

### Phase 1: Consolidate Infrastructure
1. Create `infra/` folder
2. Move all build/launch scripts: `build*.py`, `build*.ps1`, `launch*.bat`, `start.bat`, `launcher.py`, `polylog_*.py`
3. Move `docker-compose.yml`, `rustup-init.exe`
4. Update imports in CI/CD workflows

### Phase 2: Reorganize Frontend
1. Create `frontend/public/`, `frontend/src/styles/`, `frontend/src/types/`
2. Move `*.jsx`, `*.css` from `src/` root to `frontend/src/`
3. Move `*.ts` types to `frontend/src/types/`
4. Move `index.html` to `frontend/public/`
5. Move `locales/` to `frontend/public/locales/`
6. Move `vite.config.js`, `tsconfig.json`, `package.json` to `frontend/`
7. Update `vite.config.js` paths

### Phase 3: Reorganize Backend
1. Flatten `src/polylog6/` one level (already good)
2. Consolidate engine files:
   - `simulation/engines/analysis.py` + `analysis/` → decide merge or separate
   - `simulation/engines/core.py` + `core/` → decide merge or separate
   - `simulation/engines/checkpointing/` → keep separate (complex)
3. Move `tests/` to root level (already done)

### Phase 4: Reorganize Catalogs
1. Create `catalogs/tier1/`, `catalogs/tier2/`, `catalogs/tier3/`
2. Create `catalogs/attachments/`
3. Move existing files to appropriate tiers
4. Create `catalogs/schemas/` for schema definitions

### Phase 5: Flatten Documentation
1. Create `docs/architecture/`, `docs/design/`, `docs/research/`, `docs/roadmap/`, `docs/reference/`
2. Move docs from deeply nested `PolylogStructure and Science/` to flat structure
3. Create `docs/archive/` for old docs
4. Update cross-references

### Phase 6: Cleanup & Verification
1. Remove old nested folders
2. Update all import paths
3. Update CI/CD references
4. Verify all tests pass
5. Commit with message: "refactor: reorganize project structure for clarity and maintainability"

---

## Engine Consolidation Analysis

### Current Engines
```
simulation/engines/
├── analysis.py           # Wrapper
├── analysis/
│   ├── optimization_engine.py
│   └── stability_analyzer.py
├── core.py               # Wrapper
├── core/
│   ├── simulation_engine.py
│   └── [other core files]
├── checkpointing/
│   ├── polyform_engine.py
│   └── [checkpoint logic]
├── config.py
├── guardrails.py
```

### Consolidation Opportunities

**✅ Merge (No linear dependencies):**
- `analysis.py` + `analysis/optimization_engine.py` + `analysis/stability_analyzer.py` → `engines/analysis.py`
  - Reason: Optimization and stability are independent analyses
  - Benefit: Reduces nesting, clearer imports

**⚠️ Keep Separate (Complex/Stateful):**
- `core/` folder → Keep separate
  - Reason: Simulation engine is complex, stateful, may grow
  - Benefit: Easier to maintain and extend
- `checkpointing/` folder → Keep separate
  - Reason: Checkpoint logic is orthogonal to core simulation
  - Benefit: Clear separation of concerns

**🔄 Refactor:**
- `config.py` → Move to `simulation/config.py` (one level up)
  - Reason: Config is used by multiple engines, not just engines
- `guardrails.py` → Move to `simulation/guardrails.py` (one level up)
  - Reason: Guardrails apply to simulation, not just engines

---

## File Type Organization

### JSON Files
```
catalogs/
├── tier0/
│   ├── tier0_netlib.jsonl
│   └── metadata.json
├── tier1/
│   └── polyhedra.jsonl
├── attachments/
│   ├── attachment_graph.json
│   └── attachment_matrix.json
└── geometry/
    ├── geometry_catalog.json
    └── scaler_tables.json
```

### CSS/JSX Files
```
frontend/src/
├── styles/
│   ├── App.css
│   └── index.css
├── components/
│   └── *.jsx
└── App.jsx
```

### Python Files
```
backend/src/polylog6/
├── api/
├── simulation/
├── detection/
└── [domain modules]
```

---

## Alignment with Project Goals

### Current Task: Populate Tier 1 & Attachment Matrix
- **Gap**: No dedicated folder for Tier 1 polyhedra data
- **Solution**: Create `catalogs/tier1/` with polyhedra.jsonl, decompositions.json, lod_metadata.json
- **Benefit**: Clear separation of Tier 0 (primitives) vs Tier 1 (reference library)

### Current Task: Wire Runtime Symbol Generation
- **Gap**: No clear path for tier_candidates.jsonl emission
- **Solution**: Create `catalogs/tier2/` for candidates, `catalogs/tier3/` for promoted structures
- **Benefit**: Clear data flow: Tier 0 → Tier 1 → Tier 2 (candidates) → Tier 3 (promoted)

### Current Task: Populate Attachment Graph
- **Gap**: attachment_graph.json in generic catalogs/ folder
- **Solution**: Move to `catalogs/attachments/` with attachment_matrix.json
- **Benefit**: Clearer intent, easier to find attachment-related data

---

## System Hygiene Rules (Per Global Rules)

During reorganization:
- ✅ Archive old docs to `docs/archive/[DATE]_[reason]/` instead of deleting
- ✅ Keep folder nesting ≤4 levels
- ✅ Verify no test files, tmp/, commented configs staged
- ✅ Update architectural docs after changes
- ✅ Commit with clear message explaining structure changes

---

## Estimated Effort

| Phase | Task | Effort | Risk |
|-------|------|--------|------|
| 1 | Move infra scripts | 30 min | Low |
| 2 | Reorganize frontend | 1 hour | Medium (path updates) |
| 3 | Reorganize backend | 30 min | Low |
| 4 | Reorganize catalogs | 30 min | Low |
| 5 | Flatten docs | 1 hour | Low |
| 6 | Cleanup & verify | 1 hour | Medium (testing) |
| **Total** | | **4.5 hours** | |

---

## Next Steps

1. **Approve structure** - Review and confirm reorganization plan
2. **Execute Phase 1-2** - Infrastructure and frontend
3. **Execute Phase 3-4** - Backend and catalogs
4. **Execute Phase 5-6** - Documentation and cleanup
5. **Begin Tier 1 population** - With clear folder structure in place
6. **Begin attachment matrix population** - With dedicated folder
7. **Wire runtime symbol generation** - With tier2/tier3 folders ready

