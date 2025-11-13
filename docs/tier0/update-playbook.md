# Tier 0 Update Playbook

This playbook keeps the Tier 0 dataset and generator in sync with the working
workspace. Use it whenever you finish an iteration that should land in Git.

## Prerequisites

- Python 3.10+ available on `PATH`
- PowerShell 7+ (or Windows PowerShell 5.1 with execution policy that allows
  running local scripts)
- `git` installed and configured with access to the remote repository
- Workspace layout
  - Active development can happen outside the repo (e.g. `../src/polylog6/...`)
  - This repository holds the curated, ready-to-commit snapshots

## Daily Workflow

1. **Sync workspace into repo**

   ```powershell
   pwsh scripts/sync_tier0.ps1 -SourceRoot ..\
   ```

   - Removes build artefacts in the repo clone (`node_modules`,
     `src-tauri/target`, cache directories)
   - Copies the stable Tier 0 files from the working directory into the repo:
     - `src/polylog6/storage/tier0_generator.py`
     - `src/polylog6/storage/tier0_enrichment.py`
     - `catalogs/tier0_netlib.jsonl`

2. **Regenerate and validate Tier 0 export**

   ```powershell
   python scripts/generate_tier0.py
   ```

   - Rebuilds the catalog using the in-repo sources
   - Writes `catalogs/tier0_netlib.jsonl`
   - Prints the entry count (should read `3276` when everything is healthy)

3. **Commit (and optionally push)**

   ```powershell
   pwsh scripts/commit_snapshot.ps1 -Branch feature/tier0-population `
       -CommitMessage "feat(tier0): refresh catalog" `
       -SourceRoot ..\ -Push
   ```

   - Runs the sync + generation steps
   - Stages curated Tier 0 files and supporting docs/scripts
   - Creates a commit only if there are staged changes
   - Pushes to the specified branch when `-Push` is supplied

## Tips

- Keep the working directory clean before syncing: rerun your export once in the
  outer workspace so the copy step brings in the verified artefacts.
- The scripts accept a `-SourceRoot` parameter. Point it at any folder that
  contains the authoritative `src/polylog6/storage/` and `catalogs/` trees.
- Expand the `TrackedPaths` array inside `commit_snapshot.ps1` if you add more
  Tier 0 related files (tests, docs, etc.).

## Troubleshooting

| Symptom | Resolution |
| --- | --- |
| `python` cannot import `polylog6.storage.tier0_generator` | Ensure the repo `src/` directory is intact and that `scripts/generate_tier0.py` is run from the repo root. |
| Export count differs from `3276` | Re-run the generator in your working directory, confirm the series table/range logic, and copy the corrected files before regenerating inside the repo. |
| `git commit` does nothing | No staged changes were detected. Confirm the sync script copied updates and that you have modified files staged with `git status`. |
| Push fails with authentication error | Run `git remote -v` to confirm the correct URL and ensure your Git credentials/token are configured. |

Maintaining this loop ensures every commit on the repository reflects a stable,
ready-to-share Tier 0 snapshot.
