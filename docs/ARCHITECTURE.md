# Polylog6 Architecture

## System Overview

Polylog6 is a polyform visualization and analysis system combining geometric computation, pattern discovery, and interactive visualization.

## Architecture Components

### Backend (Python)
- **FastAPI** - REST API server
- **CGAL Integration** - Geometric computations
- **Tiered Storage** - Unicode compression system
- **Netlib Integration** - Precomputed polyhedra data

### Frontend (React + Babylon.js)
- **React** - UI framework
- **Babylon.js** - 3D rendering engine
- **Workspace Manager** - Polygon interaction system
- **Tier 0 Visualizer** - Unicode symbol rendering

### Desktop (Tauri)
- **Rust** - Desktop wrapper
- **Python Bridge** - Backend integration
- **Native Performance** - System integration

## Core Concepts

### Primitives
- 3-20 sided polygons
- Unit edge length: 1.0
- Defined by sides, internal angles, circumradius

### Tier 0
- Polygon-to-polygon attachment sequences
- Encoded using Series A/B/C/D + subscripts
- Not primitives (primitives are separate structure)

### Tier 1
- Platonic solids (5)
- Archimedean solids (13)
- Johnson solids (92+)
- Generated using symmetry operations

### Tier 2+
- Recursive polyform structures
- Dynamic decomposition
- Stability filtering

## Data Flow

1. **User Interaction** → Workspace Manager
2. **Polygon Placement** → Tier 0 Encoding
3. **Chain Detection** → Atomic Chain Library
4. **Visualization** → Babylon.js Rendering
5. **Backend Indexing** → Unicode Storage

## Key Files

- `src/polylog6/api/main.py` - API entry point
- `src/polylog6/storage/tier0_generator.py` - Tier 0 encoding
- `src/frontend/src/utils/workspaceManager.js` - Workspace management
- `src/frontend/src/components/BabylonScene.jsx` - 3D rendering

## See Also

- `docs/WORKSPACE_INTERACTION_ARCHITECTURE.md` - Interaction model
- `README.md` - Quick start guide
