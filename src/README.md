# Source Code

This directory contains all source code for the Polylog6 project.

## Structure

- `polylog6/` - Main Python package containing:
  - `api/` - REST API layer
  - `core/` - Core business logic
  - `detection/` - Image detection algorithms
  - `discovery/` - Pattern discovery engine
  - `storage/` - Data storage and retrieval
  - `simulation/` - Physics simulation
  - `combinatorial/` - Combinatorial calculations

- `frontend/` - React/Babylon.js web frontend
- `desktop/` - Tauri desktop application wrapper
- `shared/` - Shared types, schemas, and utilities

## Entry Points

- Python API: `src/polylog6/api/main.py`
- Frontend: `src/frontend/src/index.tsx`
- Desktop: `src/desktop/src-tauri/src/main.rs`