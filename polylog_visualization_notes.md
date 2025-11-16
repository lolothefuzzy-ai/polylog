# Polylog6 Visualization - Key Findings

## Core Principles (from slideshow)

### 1. Rigid Equilateral Principles
- Built from **perfectly equilateral polygons** (triangles, squares, hexagons, etc.)
- **Identical unit edge length** for all edges in the workspace
- Precise **edge-to-edge attachment** ensures compatibility
- **Undeformed folding** only at shared edges; individual polygons remain pristine
- Naturally preserves **geometric symmetry** of forms like Johnson and Archimedean solids

### 2. Polygon Range
- **18 polygon types**: 3-20 sided polygons
- Each polygon is a **standardized node** for assembly
- All polygons maintain **perfect geometric shape** with equal internal angles
- **No deformation or stretching** permitted

### 3. Attachment Rules
- Connections are strictly **vertex-to-vertex, edge-to-edge**
- Folding occurs **only at shared edges** between distinct polygons
- **18×18 Attachment Matrix** defines all possible connections
- ~448 attachment options with fold angles
- Stability scores: 140 stable (≥0.85), 120 conditionally stable (0.70-0.85), 64 unstable (<0.70)

### 4. System Architecture
- **Tier 0**: 18 primitive polygons (3-20 sides)
- **Tier 1**: 97 known polyhedra (5 Platonic + 13 Archimedean + 79 Johnson)
- **Full System Vision**: 2,916+ symbols
- **Current MVP**: 18 primitives + 97 polyhedra

## Backend Architecture

### Data Available
- **97 base polyhedra** with full decompositions
- **485 scalar variants** (k=1,2,3,4,5 edge length scaling)
- **750 attachment patterns** (linear, triangular, hexagonal, cubic, tetrahedral)
- **47,000+ valid attachment pairs** in matrix
- **LOD metadata** (4 levels per polyhedron)
- **Total data**: ~55 MB (compressible to ~15 MB)

### API Endpoints
- `GET /tier1/polyhedra` - List all 97 polyhedra
- `GET /tier1/polyhedra/{symbol}` - Get full polyhedron data
- `GET /tier1/polyhedra/{symbol}/lod/{level}` - Get LOD geometry
- `GET /tier1/attachments/{a}/{b}` - Get attachment options
- `GET /tier1/attachments/matrix` - Get full 18×18 matrix
- `GET /tier1/stats` - Get Tier 1 statistics

## Visualization Requirements

### Must Demonstrate
1. **Non-deformable polygons** - individual polygons maintain perfect shape
2. **Edge-to-edge attachment** - connections only at shared edges
3. **Identical unit edge length** - all edges same length
4. **No gaps** - gaps can only be filled by valid polygons (3-20 sides)
5. **Folding at shared edges** - 3D structures form by folding between polygons
6. **Interactive assembly** - user can place and connect polygons
7. **Attachment validation** - show valid/invalid connections in real-time
8. **Stability visualization** - color-code connections by stability score

### Visualization Features
- **Polygon palette**: Browse 18 primitive polygons
- **Polyhedra library**: Browse 97 known polyhedra
- **Workspace canvas**: THREE.js 3D rendering
- **Drag-and-drop placement**: Place polygons in workspace
- **Attachment preview**: Show valid attachment points when hovering
- **Stability indicators**: Color-code by stability score
- **Pattern templates**: Apply common patterns (linear, triangular, hexagonal)
- **LOD switching**: Performance optimization for complex assemblies

### Performance Targets
- 99.9% geometric accuracy
- <100ms validation latency
- 100x discovery speed vs manual
- 2,916+ polyform capacity
- <16ms render time (60 FPS)

## Technical Stack
- **Frontend**: React + THREE.js
- **Backend**: Python (existing API)
- **3D Rendering**: THREE.js with LOD support
- **Data Format**: JSONL catalogs
- **Validation**: Real-time geometric validation via attachment matrix
