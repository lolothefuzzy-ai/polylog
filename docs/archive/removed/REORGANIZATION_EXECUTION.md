# Repository Reorganization Execution Guide

## Current Situation

The repository has TWO git repositories:
1. **Root level** (`c:\Users\Nauti\AppData\Local\Programs\Windsurf\polylog6\`) - NOT a git repo
2. **Polylog6 folder** (`c:\Users\Nauti\AppData\Local\Programs\Windsurf\polylog6\Polylog6\`) - IS a git repo

---

## Strategy

### Step 1: Reorganize Polylog6 Folder (Git Repo)
Move files within Polylog6 to new structure:
- Move documentation to `Polylog6/documentation/`
- Move configs to `Polylog6/system-requirements/`
- Move code to `Polylog6/proprietary-code/`

### Step 2: Reorganize Root Level (Non-Git)
Move files from root to new structure:
- Move old docs to `documentation/`
- Move configs to `system-requirements/`
- Move code/lib to `proprietary-code/`

### Step 3: Create Root README
Point to three main folders

---

## Polylog6 Folder Reorganization

### Create Subdirectories in Polylog6
```
Polylog6/
├── documentation/
├── system-requirements/
└── proprietary-code/
```

### Move Documentation (from Polylog6 root)
```
EXECUTION_READY.md → documentation/
OPTIMIZED_PHASE_2_PLAN.md → documentation/
PROJECT_SCOPE_AND_BLOCKERS.md → documentation/
IMPLEMENTATION_ROADMAP.md → documentation/
EDGE_FACE_MATCHING_ARCHITECTURE.md → documentation/
SYSTEM_OPTIMIZATION_ANALYSIS.md → documentation/
TRACK_A_B_DELEGATION.md → documentation/
ZERO_BLOCKER_SUMMARY.md → documentation/
LIBRARY_CLEANUP_COMPLETE.md → documentation/
README.md → documentation/POLYLOG6_README.md
docs/ → documentation/
```

### Move System Requirements (from Polylog6 root)
```
requirements.txt → system-requirements/
package.json → system-requirements/
package-lock.json → system-requirements/
tsconfig.json → system-requirements/
pytest.ini → system-requirements/
vite.config.js → system-requirements/
docker-compose.yml → system-requirements/
.codecov.yml → system-requirements/
.mergify.yml → system-requirements/
.vscode/ → system-requirements/
.github/ → system-requirements/
config/ → system-requirements/
schemas/ → system-requirements/
```

### Move Proprietary Code (from Polylog6 root)
```
src/ → proprietary-code/
catalogs/ → proprietary-code/
data/ → proprietary-code/
storage/ → proprietary-code/
tests/ → proprietary-code/
scripts/ → proprietary-code/
build/ → proprietary-code/
web_portal/ → proprietary-code/
PolylogCore/ → proprietary-code/
src-tauri/ → proprietary-code/
locales/ → proprietary-code/
node_modules/ → proprietary-code/
venv/ → proprietary-code/
__pycache__/ → proprietary-code/
.pytest_cache/ → proprietary-code/
.ruff_cache/ → proprietary-code/
launcher.py → proprietary-code/
polylog_core.py → proprietary-code/
polylog_main.py → proprietary-code/
build.ps1 → proprietary-code/
build-sidecar.py → proprietary-code/
launch_api.bat → proprietary-code/
launch_gui.bat → proprietary-code/
start.bat → proprietary-code/
index.html → proprietary-code/
install_dependencies.bat → proprietary-code/
rustup-init.exe → proprietary-code/
*.jsonl → proprietary-code/
*.prof → proprietary-code/
.coverage → proprietary-code/
```

---

## Root Level Reorganization

### Move Old Docs to documentation/
```
BLOCKER_ANALYSIS.md → documentation/archive/
CLEANUP_PLAN.md → documentation/
TRACK_A_PHASE_1_COMPLETE.md → documentation/archive/
TRACK_A_READY.md → documentation/archive/
TRACK_A_SEQUENCING.md → documentation/archive/
TRACK_A_VALIDATION.md → documentation/archive/
VALIDATION_SUMMARY.md → documentation/archive/
docs/ → documentation/
```

### Move Configs to system-requirements/
```
tsconfig.json → system-requirements/
```

### Move Code/Lib to proprietary-code/
```
lib/ → proprietary-code/
src/ → proprietary-code/
testing/ → proprietary-code/
Polylog6/ → proprietary-code/
```

---

## Final Structure

```
polylog6/
├── README.md (root entry point)
├── .git/ (root git)
├── .gitignore
├── documentation/
│   ├── README.md
│   ├── EXECUTION_READY.md
│   ├── OPTIMIZED_PHASE_2_PLAN.md
│   ├── PROJECT_SCOPE_AND_BLOCKERS.md
│   ├── IMPLEMENTATION_ROADMAP.md
│   ├── EDGE_FACE_MATCHING_ARCHITECTURE.md
│   ├── SYSTEM_OPTIMIZATION_ANALYSIS.md
│   ├── TRACK_A_B_DELEGATION.md
│   ├── ZERO_BLOCKER_SUMMARY.md
│   ├── LIBRARY_CLEANUP_COMPLETE.md
│   ├── POLYLOG6_README.md
│   ├── architecture/
│   ├── design/
│   ├── research/
│   ├── roadmap/
│   ├── reference/
│   └── archive/
├── system-requirements/
│   ├── README.md
│   ├── requirements.txt
│   ├── package.json
│   ├── package-lock.json
│   ├── tsconfig.json
│   ├── pytest.ini
│   ├── vite.config.js
│   ├── docker-compose.yml
│   ├── .codecov.yml
│   ├── .mergify.yml
│   ├── .vscode/
│   ├── .github/
│   ├── config/
│   └── schemas/
└── proprietary-code/
    ├── README.md
    ├── Polylog6/
    │   ├── documentation/
    │   ├── system-requirements/
    │   └── proprietary-code/
    ├── src/
    ├── lib/
    ├── scripts/
    ├── tests/
    ├── storage/
    ├── data/
    ├── catalogs/
    ├── build/
    ├── node_modules/
    ├── venv/
    └── [other code files]
```

---

## Implementation Approach

### Option A: Manual Move (Safer)
1. Copy files to new locations
2. Verify structure
3. Delete old files
4. Commit changes

### Option B: Git Move (Preserves History)
1. Use `git mv` within Polylog6 repo
2. Commit changes
3. Move root-level files manually
4. Commit root changes

**Recommendation:** Use Option B for Polylog6 (preserves git history), Option A for root level.

---

## Next Steps

1. Create subdirectories in Polylog6
2. Move Polylog6 files using git mv
3. Commit Polylog6 changes
4. Move root-level files manually
5. Create root README.md
6. Commit root changes
7. Verify structure
8. Push all changes

---

## Status: EXECUTION GUIDE READY

Ready to execute full repository reorganization.

