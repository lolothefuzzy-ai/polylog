# Repository Reorganization Plan

**Goal:** Organize entire repository into 3 main folders:
1. **documentation/** - All documentation
2. **system-requirements/** - Configuration, dependencies, requirements
3. **proprietary-code/** - All source code and project files

---

## Current State

### Root Level Files (Scattered)
- BLOCKER_ANALYSIS.md
- CLEANUP_PLAN.md
- TRACK_A_PHASE_1_COMPLETE.md
- TRACK_A_READY.md
- TRACK_A_SEQUENCING.md
- TRACK_A_VALIDATION.md
- VALIDATION_SUMMARY.md
- tsconfig.json
- package.json
- package-lock.json

### Root Level Folders
- .github/ (CI/CD)
- .vscode/ (IDE config)
- docs/ (documentation)
- lib/ (data/catalogs)
- Polylog6/ (main project)
- src/ (source code)
- testing/ (tests)

---

## Target Structure

```
polylog6/
├── documentation/
│   ├── README.md (entry point)
│   ├── CURRENT_STATUS.md (active)
│   ├── IMPLEMENTATION_ROADMAP.md
│   ├── PROJECT_SCOPE_AND_BLOCKERS.md
│   ├── EDGE_FACE_MATCHING_ARCHITECTURE.md
│   ├── SYSTEM_OPTIMIZATION_ANALYSIS.md
│   ├── OPTIMIZED_PHASE_2_PLAN.md
│   ├── TRACK_A_B_DELEGATION.md
│   ├── ZERO_BLOCKER_SUMMARY.md
│   ├── LIBRARY_CLEANUP_COMPLETE.md
│   ├── architecture/
│   │   ├── architecture_overview.md
│   │   ├── polyform_compression_architecture.md
│   │   ├── polyform_dictionary_system.md
│   │   ├── polyform_simulator_spec.md
│   │   ├── unicode_symbol_allocation.md
│   │   └── [other architecture docs]
│   ├── design/
│   │   ├── catalog_generation.md
│   │   ├── engine_requirements.md
│   │   └── structure_science_synthesis.md
│   ├── research/
│   │   ├── detection_monitoring.md
│   │   ├── polyform_simulator_research.md
│   │   ├── visualization_optimization.md
│   │   └── [other research]
│   ├── roadmap/
│   │   └── polylog_development_status.md
│   ├── reference/
│   │   ├── legacy/ (old docs)
│   │   └── polyform_storage_encoding.pdf
│   └── archive/
│       └── [old handoff docs]
│
├── system-requirements/
│   ├── README.md
│   ├── requirements.txt (Python dependencies)
│   ├── package.json (Node dependencies)
│   ├── package-lock.json
│   ├── tsconfig.json (TypeScript config)
│   ├── pytest.ini (Test config)
│   ├── vite.config.js (Build config)
│   ├── docker-compose.yml
│   ├── install_dependencies.bat
│   ├── .codecov.yml
│   ├── .mergify.yml
│   ├── .vscode/
│   │   └── settings.json
│   ├── .github/
│   │   └── workflows/
│   │       └── storage-regression.yml
│   ├── config/
│   │   └── monitoring.yaml
│   └── schemas/
│       └── [schema files]
│
└── proprietary-code/
    ├── README.md
    ├── src/
    │   └── polylog6/
    │       ├── combinatorial/
    │       ├── detection/
    │       ├── discovery/
    │       ├── api/
    │       ├── storage/
    │       ├── simulation/
    │       ├── telemetry/
    │       ├── ui/
    │       ├── monitoring/
    │       └── hardware/
    ├── Polylog6/
    │   ├── src/
    │   ├── catalogs/
    │   ├── data/
    │   ├── storage/
    │   ├── tests/
    │   ├── scripts/
    │   ├── build/
    │   ├── web_portal/
    │   ├── PolylogCore/
    │   ├── src-tauri/
    │   ├── locales/
    │   ├── build.ps1
    │   ├── build-sidecar.py
    │   ├── launcher.py
    │   ├── polylog_core.py
    │   ├── polylog_main.py
    │   ├── launch_api.bat
    │   ├── launch_gui.bat
    │   ├── start.bat
    │   ├── index.html
    │   ├── vite.config.js
    │   ├── tsconfig.json
    │   ├── docker-compose.yml
    │   └── [other project files]
    ├── lib/
    │   ├── catalogs/
    │   ├── config/
    │   └── [data files]
    ├── scripts/
    │   ├── generate_scalar_variants.py
    │   ├── generate_attachment_patterns.py
    │   ├── update_attachment_matrix_full.py
    │   ├── run_compression_metrics.py
    │   ├── [other scripts]
    │   └── benchmark_*.py
    ├── tests/
    │   ├── conftest.py
    │   ├── test_*.py
    │   ├── fixtures/
    │   ├── storage/
    │   └── uat/
    ├── storage/
    │   ├── chunks/
    │   └── caches/
    ├── data/
    │   └── polyhedra/
    ├── catalogs/
    │   ├── tier0/
    │   ├── tier1/
    │   ├── tier2/
    │   ├── tier3/
    │   ├── attachments/
    │   └── [other catalogs]
    ├── build/
    │   └── [build artifacts]
    ├── node_modules/
    │   └── [dependencies]
    ├── venv/
    │   └── [Python venv]
    ├── .pytest_cache/
    ├── .ruff_cache/
    ├── __pycache__/
    ├── .coverage
    ├── *.prof (profiling)
    ├── *.jsonl (data files)
    ├── *.json (config/data)
    └── [other project files]
```

---

## Migration Steps

### Phase 1: Create Folder Structure
1. Create `documentation/` folder
2. Create `system-requirements/` folder
3. Create `proprietary-code/` folder

### Phase 2: Move Documentation
Move all `.md` files to `documentation/`:
- Active status docs (EXECUTION_READY.md, etc.)
- Reference docs (PROJECT_SCOPE_AND_BLOCKERS.md, etc.)
- Archive docs (docs/archive/)
- Architecture docs (docs/PolylogStructure and Science/)

### Phase 3: Move System Requirements
Move all config/dependency files to `system-requirements/`:
- requirements.txt
- package.json, package-lock.json
- tsconfig.json
- pytest.ini
- vite.config.js
- docker-compose.yml
- .codecov.yml, .mergify.yml
- .vscode/
- .github/
- config/
- schemas/

### Phase 4: Move Proprietary Code
Move all source code to `proprietary-code/`:
- src/ (entire folder)
- Polylog6/ (entire folder)
- lib/ (entire folder)
- scripts/ (entire folder)
- tests/ (entire folder)
- storage/ (entire folder)
- data/ (entire folder)
- catalogs/ (entire folder)
- build/ (entire folder)
- node_modules/ (entire folder)
- venv/ (entire folder)
- All .py, .js, .ts, .tsx files
- All cache/build artifacts

### Phase 5: Update Root README
Create new root README.md pointing to:
- documentation/README.md
- system-requirements/README.md
- proprietary-code/README.md

### Phase 6: Cleanup
- Remove old root-level .md files
- Remove old root-level config files
- Keep only .gitignore and new README.md at root

---

## Benefits

✅ **Clear Organization:**
- Documentation separate from code
- System requirements clearly identified
- Proprietary code organized

✅ **Easy Navigation:**
- Know exactly where to find documentation
- Know exactly where to find requirements
- Know exactly where to find code

✅ **Research Ready:**
- External teams can access documentation easily
- System requirements clear
- Code organization transparent

✅ **Maintenance:**
- Easy to update documentation
- Easy to manage dependencies
- Easy to organize code

---

## Implementation Notes

### What NOT to Move
- .git/ (keep at root)
- .gitignore (keep at root)
- New root README.md (keep at root)

### What to Update
- All import paths in code
- All relative paths in documentation
- All CI/CD workflows (.github/workflows/)

### Git Strategy
- Use `git mv` to preserve history
- Commit in phases
- Push after each phase

---

## Status: REORGANIZATION PLAN READY

Ready to execute full repository reorganization into 3 main folders.

