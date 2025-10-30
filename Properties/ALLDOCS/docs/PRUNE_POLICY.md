Prune Policy (draft)
=====================

Goal
----
Define safe, conservative rules for removing or offloading non-essential repository files to reduce working set size while preserving recoverability.

Principles
----------
- Non-destructive first: produce lists and backups before deleting.
- Prefer deletion of regenerated caches (mypy, __pycache__, pytest, build artifacts).
- Archive or offload large legacy artifacts instead of immediate deletion where there's uncertainty.
- Record every change with checksums and a restore script.

Policy rules (recommended)
--------------------------
1. Caches: safe to remove (rebuildable)
   - `.mypy_cache/` (all versions)
   - `__pycache__/` directories and `*.pyc`/`*.pyo`
   - `.pytest_cache/`
   - `.mypy_cache` entries under ALLDOCS
2. Build artifacts: safe to remove
   - `build/`, `dist/`, `*.egg-info/`
   - `*.spec` (PyInstaller) if reproducible from source
3. Editor/IDE artifacts: safe to remove
   - `.vscode/`, `.idea/`, `*.code-workspace`
4. Large generated archives / installers
   - `archive/legacy.zip`, `archive/backups.zip` — consider offloading to external storage if retention required; otherwise move to `archive/offloaded/` then delete locally.
5. Large test artifacts / datasets
   - Directories under `tests/` or `stress_test_library/` containing large binary artifacts should be evaluated case-by-case; move to `archive/offloaded/` if older than X days (suggest 90 days).
6. Documentation and source code
   - Keep all `.md`, `.py` source, and `docs/` content. Move legacy docs into `archive/legacy` only if explicitly historical/duplicative.

Retention and thresholds
------------------------
- Default: caches and build artifacts: immediate safe deletion.
- Legacy archives: retain if modified within last 180 days; otherwise offload/archive permanently.
- Test/dataset artifacts: offload if older than 90 days.

Process (safety steps)
----------------------
1. Inventory repo sizes and produce `archive/repo_disk_inventory.txt` (done).
2. Generate `archive/prune_candidates.txt` listing candidates and sizes (read-only) — review before deletion.
3. For each approved candidate, create a timestamped zip under `archive/hold/` and record SHA256 in `archive/hold_checksums.txt`.
4. After verifying backups, delete originals and log deletions in `archive/prune_log.txt`.
5. Run sanity checks and commit `.gitignore` updates to avoid re-adding large items.

If you approve this policy, reply "approve" and I will proceed to (a) create backups for the top prune candidates, and (b) perform deletions per policy. If you want stricter or looser rules, tell me which patterns to change.
