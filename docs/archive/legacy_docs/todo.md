# Polylog Visualizer TODO

## Phase 1: Project Setup
- [x] Initialize web-static project
- [x] Create project plan and todo list

## Phase 2: 3D Visualization Core
- [x] Install THREE.js dependencies
- [x] Create 3D canvas component with basic scene setup
- [x] Implement camera controls (orbit, zoom, pan)
- [x] Add lighting and grid helpers
- [x] Create polygon geometry generator (3-20 sided)
- [x] Implement polygon rendering with proper materials

## Phase 3: Polygon Library & Workspace
- [x] Create polygon palette UI (18 polygon types)
- [x] Implement click-to-place from palette to workspace
- [x] Add polygon selection and highlighting
- [x] Create transform controls (move, rotate)
- [ ] Build polyhedra library browser (97 known polyhedra) - Future enhancement
- [ ] Add polyhedra placement in workspace - Future enhancement

## Phase 4: Attachment Validation & Patterns
- [x] Implement edge detection and highlighting
- [x] Add attachment point visualization (vertex indicators)
- [x] Create edge snapping utilities
- [ ] Add stability score visualization (color-coded) - Future enhancement
- [ ] Implement snap-to-edge functionality - Future enhancement
- [ ] Create pattern templates UI (linear, triangular, hexagonal) - Future enhancement
- [ ] Add pattern application to workspace - Future enhancement

## Phase 5: Testing & Polish
- [x] Test all polygon types (3-20 sides)
- [x] Verify attachment validation accuracy
- [x] Test performance with complex assemblies
- [x] Add user instructions/help
- [x] Final visual polish and UX improvements


## Phase 6: 3D Upgrade & Edge Validation
- [x] Upgrade to full 3D visualization with THREE.js
- [x] Implement proper polygon 3D geometry (not just 2D projections)
- [x] Implement open edge tracking and closure detection
- [x] Add edge-to-edge attachment validation
- [x] Implement snap-to-edge functionality with visual guides
- [x] Create attachment resolver for finding valid connections
- [x] Add stability scoring system
- [x] Enhance edge coloring (RED/YELLOW/GREEN) with proper color coding
- [ ] Add fold angle constraints and validation
- [ ] Add collision detection for polygon placement
- [ ] Implement real-time mesh topology updates


## Phase 7: 2D-to-3D Transition & Unicode Compression
- [x] Implement polygon Unicode symbol mapping (A=Triangle, B=Square, C=Pentagon, etc.)
- [x] Add composition string generation and display
- [x] Add O/I value calculation and display
- [x] Implement symmetry group detection
- [x] Add edge signature generation
- [x] Create polyform export to Polylog6 JSON format
- [x] Create tier-based polyform representation (Tier 0, 1, 2+)
- [x] Implement Unicode compression for polyform encoding
- [x] Add export button with JSON download functionality
- [x] Update help panel with Unicode compression documentation
- [ ] Add 2D workspace view (flat polygons on XY plane)
- [ ] Create 2D-to-3D transition animation system
- [ ] Implement fold angle calculation and visualization
- [ ] Add dihedral angle display between attached polygons
- [ ] Add LOD (Level of Detail) metadata system
- [ ] Create attachment graph visualization
- [ ] Implement scaler tables for polygon scaling


## Phase 8: Advanced Unicode Tier Structure & Auto-Snapping
- [ ] Extend Unicode tier structure to support subscripts 0-999 (Ω₀ through Ω₉₉₉)
- [ ] Implement atomic chain system for linear/hexagonal polygon extension
- [ ] Add polygon range slider (3-20 sides) instead of fixed library
- [ ] Implement auto-rotation and snap-to-edge on polygon placement
- [ ] Add attachment matrix for validation (O(1) lookup)
- [ ] Create real-time snap zones with visual feedback (green/yellow/red)
- [ ] Implement fold angle calculation and display
- [ ] Add stability scoring for attachment candidates
- [ ] Create liaison graph for tracking polygon connections
- [ ] Implement open edge registry for boundary tracking
- [ ] Add undo/redo system for polygon placement
- [ ] Create 2D workspace mode (flat XY plane, z=0)
- [ ] Add 2D-to-3D transition toggle with animation
- [ ] Implement GPU-optimized rendering pipeline
- [ ] Add face pruning for internal faces in closed polyforms
- [ ] Create recursive compression system for higher-order polyforms
- [ ] Implement promotion system (Tier 0 → Tier 1 → Tier 2+)
- [ ] Add continuous generation mode for discovery
- [ ] Create polyform library gallery for discovered structures
- [ ] Implement LOD (Level of Detail) system for complex polyforms


## Phase 9: Corrected Unicode Tier Structure
- [x] Update polygon symbol mapping to A/B/C/D series format
- [x] Implement Series A (subscript 1-9): 3, 17, 9, 5, 15, 5, 7, 19, 11 sides
- [x] Implement Series B (subscript 1-9): 20, 4, 6, 8, 10, 12, 14, 16, 18 sides
- [x] Implement Series C (subscript 1-9): 3, 6, 9, 12, 15, 18, 7, 8, 10 sides
- [x] Implement Series D (subscript 1-9): 20, 4, 19, 5, 14, 17, 13, 16, 11 sides
- [x] Add subscript generation for 1-9, 10-99, 100-999 ranges
- [x] Implement two-element patterns (AB, AC, AD, BC, BD, BA, etc.)
- [x] Implement three-element patterns (ABC, ABD, ACD, etc.)
- [x] Add skip rule for X0 patterns (no 10, 20, 30, etc.)
- [x] Implement series cycling logic (A→{B,C,D}, B→{C,D,A}, etc.)
- [x] Update composition display to use correct series format
- [x] Update export to use correct Unicode structure


## Foundation Milestone: Babylon.js + Unicode Index
- [x] Replace THREE.js with Babylon.js for advanced GPU features
- [x] Create Babylon.js scene with camera and lighting
- [x] Implement polygon range slider (3-20 sides)
- [x] Add click-to-place polygon placement into 3D workspace
- [x] Add workspace rotation controls (orbit camera)
- [x] Show stats (polygons, open edges, closure %)
- [ ] Load pre-computed Tier 1 polyhedra as GPU meshes
- [ ] Implement real-time attachment validation with attachment matrix
- [ ] Store Unicode indices instead of positions in liaison graph
- [ ] Show green/red edge validation feedback

## Phase 1: Stability Detection + Async CPU Warming
- [ ] Implement closure detection (boundary edge counter)
- [ ] Create stability matrix for sub-cluster decomposition
- [ ] Build AsyncCPUPipeline class for pre-fetching attachment data
- [ ] Implement warm_attachments_for() prediction algorithm
- [ ] Add GPU polling for pre-computed attachments (non-blocking)
- [ ] Show "ASSEMBLY CLOSED" notification when boundary edges = 0
- [ ] Display latency metrics in HUD
- [ ] Ensure GPU rendering never blocks on CPU

## Phase 2: Face Pruning + Unicode Symbol Allocation
- [ ] Implement face merge pipeline for closed assemblies
- [ ] Create CompressionEngine class
- [ ] Add on_assembly_closed() trigger
- [ ] Compute symmetry groups from merged faces
- [ ] Check composition hash against known Tier 2 polyforms
- [ ] Allocate new Unicode symbols for novel polyforms
- [ ] Implement GPU face pruning (coplanar face detection)
- [ ] Extract new attachment patterns after merge
- [ ] Save discovered polyforms to tier2_catalog.jsonl
- [ ] Add polyforms to generator seed library

## Phase 3: Compression Detection + Generation Seeds
- [ ] Implement pattern detection for repeating Unicode sequences
- [ ] Create GeneratorEngine class
- [ ] Add generate_from_seed() with linear/exponential modes
- [ ] Decompose seeds into Tier 0 primitives
- [ ] Identify dominant primitives for growth
- [ ] Implement atomic chain growth (1 cube → 2 cubes → 3 cubes)
- [ ] Add generation slider (linear vs exponential)
- [ ] Compress repeating patterns to new Unicode symbols
- [ ] Prune old cache entities after compression


## CAD-Style Navigation & Atomic Chains
- [x] Fix Babylon.js ArcRotateCamera for proper orbit controls
- [x] Add pan controls (Ctrl+drag or middle mouse)
- [x] Implement zoom controls (mouse wheel)
- [ ] Add camera reset button to return to default view
- [ ] Implement atomic chain detection for shape clusters
- [ ] Visualize atomic chains with Unicode indexing
- [ ] Add architectural-style edge snapping (snap to grid, snap to edge)
- [ ] Implement snap zones with visual feedback
- [ ] Add attachment matrix validation for snapping
- [ ] Create atomic chain growth visualization
- [ ] Test navigation with complex polyform assemblies


## Edge Snapping & 2D-to-3D Folding
- [ ] Fix duplicate placement bug (currently placing 2 polygons instead of 1)
- [ ] Implement edge-based placement (place at nearest open edge, not random)
- [ ] Add automatic edge snapping when polygons are moved near compatible edges
- [ ] Implement polygon selection (click to select)
- [ ] Add polygon movement (drag selected polygon)
- [ ] Implement free rotation for selected polygons
- [ ] Add visual feedback for valid snap zones (green highlight)
- [ ] Detect when edges attach and trigger fold angle calculation
- [ ] Implement 2D-to-3D transition (e.g., 4 triangles → tetrahedron)
- [ ] Add fold angle visualization (dihedral angles)
- [ ] Update liaison graph when edges attach
- [ ] Prune internal faces when polyforms close


## Critical Bugs to Fix NOW
- [ ] Fix Place button not triggering handlePlacePolygon function
- [ ] Fix polygon mesh visibility (CreateDisc not rendering)
- [ ] Remove test box after polygons are working

## Drag-Drop Assembly System (Claude's Architecture)
- [ ] Implement drag-from-library functionality
- [ ] Add drag-within-workspace for repositioning
- [ ] Create template/instance dual-pattern (immutable templates, mutable instances)
- [ ] Add free rotation until snap confirmation
- [ ] Implement workspace instance management

## Unicode Attachment Cache & CPU Pre-Warming
- [ ] Create Series A/B/C/D attachment indices (different edge availability states)
- [ ] Build CPU attachment cache with pre-computed compatible edges
- [ ] Implement O(1) compatible edge lookup
- [ ] Store fold angles and scalers in attachment cache
- [ ] Add cache size tracking and optimization

## 2D→3D Progressive Folding
- [ ] Start all polygons on 2D base plane (z=0)
- [ ] Detect when edges attach and trigger folding
- [ ] Implement workspace centering (move assembly up as it grows)
- [ ] Add scalar expansion for radial/spheroid growth
- [ ] Support linear, ring, square, triangular growth patterns

## Face Pruning & Cache Compression
- [ ] Implement face pruning when assemblies close
- [ ] Add cache sampling for repeating Unicode patterns
- [ ] Compress repeating Unicode strings to new symbols
- [ ] Prune old cache entities after compression
- [ ] Track compression ratio and cache efficiency


## Precise Polygon Geometry Implementation
- [ ] Install earcut library for polygon triangulation
- [ ] Create polygon geometry with exact unit edge lengths (all edges = 1.0)
- [ ] Generate vertices on XZ plane (y=0) for 2D base
- [ ] Add vertex and edge tracking to each polygon mesh
- [ ] Store edge midpoints and normals for snap detection
- [ ] Remove test box once proper geometry is confirmed
- [ ] Implement edge highlighting on hover
- [ ] Add vertex markers for debugging attachment points


## GPU-Accelerated Tier 0 Decoder
- [ ] Create ABCD series lookup tables (validated, do not modify)
  - Series A: [11, 13, 3, 15, 5, 17, 7, 19, 9]
  - Series B: [20, 4, 6, 8, 10, 12, 14, 16, 18]
  - Series C: [3, 6, 9, 12, 15, 18, 7, 8, 10]
  - Series D: [11, 20, 13, 14, 5, 16, 17, 4, 19]
- [ ] Implement fold angle precomputation for all edge count pairs (3-20)
- [ ] Create WebGPU compute shader for Unicode symbol decoding
- [ ] Implement unit edge polygon generation in compute shader
- [ ] Add fold angle application with Rodrigues rotation
- [ ] Create Babylon.js integration layer for GPU decoder
- [ ] Set up storage buffers for series tables and fold angles
- [ ] Implement symbol buffer for dynamic per-frame data
- [ ] Add vertex buffer output for Babylon.js mesh consumption
- [ ] Test single polygon generation (A₁ = 11-gon)
- [ ] Test two-polygon chains (AB₂₂ = 11-gon + 4-gon)
- [ ] Test three-polygon chains (ABC₁₀₀+)
- [ ] Verify unit edge length invariant (all edges = 1.0)
- [ ] Test fold angle accuracy for known polyhedra


## This Week: Immediate Fixes (Hybrid Path)
- [x] Fix polygon visibility issue (check material.backFaceCulling)
- [x] Verify normals are computed correctly for flat polygons
- [x] Remove test box once polygons are visible
- [x] Implement EdgeSnapper.findClosestEdge() for basic snapping
- [x] Add visual feedback for snap zones (highlight compatible edges)
- [ ] Test manual assembly: 4 triangles → tetrahedron
- [ ] Verify fold angles are correct for tetrahedron (70.529°)
- [ ] Save checkpoint with working edge snapping

## Next Week: Optimize ABCD Series
- [ ] Apply optimized A-series: [3, 5, 7, 9, 11, 13, 15, 17, 19]
- [ ] Apply optimized D-series: [4, 5, 11, 13, 14, 16, 17, 19, 20]
- [ ] Validate A₁ generates triangle (3 sides)
- [ ] Validate D₁ generates square (4 sides)
- [ ] Update polygonSymbolsV2.ts with new series
- [ ] Document changes in TIER0_SPECIFICATION.md
- [ ] Test all 36 base symbols render correctly

## Future (Week 4+): GPU Decoder Enhancement
- [ ] Implement WebGPU compute shader for Tier 0 decoding
- [ ] Add Tier 1 promotion system (Ω symbols)
- [ ] Implement LOD (Level of Detail) system
- [ ] Add cache layer for discovered polyforms


## Automatic Rotation Alignment for Edge Snapping
- [x] Implement automatic polygon rotation when dragging near compatible edges
- [x] Calculate rotation angle to align moving edge with target edge (180° flip for opposite orientation)
- [x] Apply rotation smoothly during drag (not just on release)
- [x] Ensure rotation preserves unit edge length geometry
- [ ] Test rotation alignment with triangles, squares, and other polygons
- [ ] Verify edges align perfectly when snapped (visual confirmation)


## Snap-on-Release and Physical Edge Attachment
- [ ] Implement snap-on-release: move polygon to exact edge alignment when dropped near valid snap target
- [ ] Store best snap candidate during drag (don't recalculate on release)
- [ ] Apply both position AND rotation transform on release
- [ ] Test snap-on-release with triangles, squares, pentagons, hexagons
- [ ] Verify edges align perfectly after snap (visual confirmation)

## Polygon Pair Movement and Connection Tracking
- [ ] Create connection graph to track which polygons are attached
- [ ] Implement group movement: when dragging one polygon, move all connected polygons together
- [ ] Add parent-child relationships for connected polygons
- [ ] Update connection graph when edges attach
- [ ] Visualize connections with different edge colors (attached vs open)

## Automatic 2D-to-3D Folding
- [ ] Detect when 3+ polygons form a closed loop (e.g., 3 triangles around a vertex)
- [ ] Calculate dihedral angles for 3D folding (e.g., tetrahedron: 70.529°)
- [ ] Implement smooth fold animation from 2D (z=0) to 3D structure
- [ ] Apply fold angles using Rodrigues rotation formula
- [ ] Test with 4 triangles → tetrahedron
- [ ] Test with 6 squares → cube
- [ ] Verify internal angles are geometrically correct

## Architecture Documentation Updates
- [ ] Update docs to reflect Babylon.js instead of THREE.js
- [ ] Document snap-on-release behavior
- [ ] Document polygon pair movement system
- [ ] Document 2D→3D folding triggers and angle calculations
