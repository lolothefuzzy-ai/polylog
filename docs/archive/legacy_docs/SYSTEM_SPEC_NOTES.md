# Polylog6 System Specifications - Implementation Notes

## Key Requirements from Comprehensive Specification

### 1. Unicode Tier Structure with Subscripts

**Requirement:** Unicode symbols should support subscripts from 0-999 for higher-tier polyforms.

**Format:**
```
Tier 0: A, B, C, D, E, F, G, H, I, J, K, L, M, N, O, P, Q, R (primitives)
Tier 1: Ω₀, Ω₁, Ω₂, ... Ω₉₉₉ (polyhedra - closed 3D structures)
Tier 2: Ψ₀, Ψ₁, Ψ₂, ... Ψ₉₉₉ (assemblies - multi-polyhedra)
Tier 3: Φ₀, Φ₁, Φ₂, ... Φ₉₉₉ (complex structures)
```

**Implementation:**
- Use Unicode subscript characters: ₀₁₂₃₄₅₆₇₈₉
- Generate symbols programmatically: `Ω${toSubscript(index)}`
- Store mapping in tier catalogs

### 2. Atomic Chains

**Definition:** Atomic chains are sequences of identical polygons that extend based on attachment symmetry.

**Examples:**
- **Triangle chain**: Linear extension (edge-to-edge)
- **Square chain**: Linear extension (edge-to-edge)
- **Hexagon chain**: Perimeter expansion (creates honeycomb pattern)

**Key insight:** Hexagon chains create gaps along external edges that must be:
1. Filled with other polygons, OR
2. Folded to form different polyforms

**Implementation:**
- Track chain type (linear, hexagonal, etc.)
- Detect chain patterns during assembly
- Offer auto-completion suggestions for chains
- Store chain metadata in Unicode compression

### 3. 2D-to-3D Workspace Transition

**User flow:**
1. User starts in 2D workspace (all polygons flat, z=0)
2. As polygons are added, system detects potential 3D folds
3. System automatically attempts to snap edges in 3D space
4. Workspace transitions from 2D to 3D as folds are detected

**Implementation:**
- Start with 2D mode: all polygons on XY plane
- Track fold angles between attached polygons
- When fold angle != 180°, transition to 3D
- Animate the fold transition smoothly

### 4. Auto-Snapping with Rotation

**Requirement:** When a new polygon is introduced, it should automatically rotate to snap to existing polygons.

**Algorithm:**
```
1. User drags polygon into workspace
2. System detects nearby open edges
3. For each open edge:
   a. Check attachment matrix for compatibility
   b. Calculate required rotation to align edges
   c. Compute fold angle
   d. Calculate stability score
4. Select best attachment candidate (highest stability)
5. Auto-rotate polygon to match
6. Snap to attachment point
7. Update liaison graph
```

**Visual feedback:**
- **GREEN**: Valid attachment, high stability
- **YELLOW**: Conditional attachment, medium stability
- **RED**: Invalid attachment, geometric conflict

### 5. Attachment Matrix

**Purpose:** O(1) lookup for polygon compatibility.

**Structure:**
```json
{
  "3-3": { "valid": true, "fold_angles": [60, 70.5, 109.5], "stability": 0.9 },
  "3-4": { "valid": true, "fold_angles": [90, 120], "stability": 0.8 },
  "3-5": { "valid": true, "fold_angles": [108, 120], "stability": 0.7 },
  ...
}
```

**Key:** `"${sides1}-${sides2}"`
**Value:** Attachment metadata (valid, fold angles, stability)

### 6. Liaison Graph

**Purpose:** Track all polygon connections in the assembly.

**Structure:**
```typescript
interface LiaisonGraph {
  nodes: Map<string, PolygonNode>;  // polygon_id -> node
  edges: Map<string, AttachmentEdge>;  // edge_id -> attachment
}

interface PolygonNode {
  id: string;
  sides: number;
  position: Vector3;
  rotation: Euler;
  attachments: string[];  // edge_ids
}

interface AttachmentEdge {
  id: string;
  polygon1: string;
  polygon2: string;
  edge1_index: number;
  edge2_index: number;
  fold_angle: number;
  stability: number;
}
```

### 7. Open Edge Registry

**Purpose:** Track which edges are available for attachment.

**Structure:**
```typescript
interface OpenEdgeRegistry {
  edges: Map<string, OpenEdge>;
}

interface OpenEdge {
  polygon_id: string;
  edge_index: number;
  start_vertex: Vector3;
  end_vertex: Vector3;
  normal: Vector3;
  available: boolean;
}
```

**Update rules:**
- When polygon is placed: add all edges to registry
- When edge is attached: mark as unavailable
- When polygon is removed: remove all edges from registry

### 8. GPU Optimization

**Key principle:** Defer visualization to GPU, use Unicode for compression.

**CPU responsibilities:**
- Maintain liaison graph
- Track open edges
- Validate attachments
- Compute fold angles
- Generate Unicode symbols

**GPU responsibilities:**
- Render polygons
- Apply transformations
- Handle lighting/shadows
- Perform face pruning
- Manage LOD (Level of Detail)

**Handoff protocol:**
```
CPU → GPU: [polygon_id, geometry_buffer, transform_matrix, material_props]
GPU → CPU: [render_complete, face_count, vertex_count]
```

### 9. Face Pruning

**Purpose:** Remove internal faces when polygons are attached.

**Algorithm:**
```
1. Detect coplanar faces between attached polygons
2. Check if faces are fully overlapping
3. If yes, mark faces for removal
4. Update mesh topology on GPU
5. Reduce polygon count for performance
```

**Example:**
- Two triangles attached edge-to-edge
- Internal edges are coplanar
- Remove shared edge, merge into single quad

### 10. Recursive Compression

**Purpose:** Compress higher-order polyforms into single Unicode symbols.

**Algorithm:**
```
1. Detect stable sub-assemblies (0 open edges)
2. Check if assembly matches known polyhedra (Tier 1)
3. If yes, replace with Ω symbol
4. If no, promote to Tier 2 (Ψ symbol)
5. Store composition in catalog
6. Use new symbol in future assemblies
```

**Example:**
- User builds tetrahedron (4 triangles)
- System detects closure
- Replaces AAAA with Ω₁
- Tetrahedron now available as primitive

### 11. Polygon Range Slider

**Requirement:** Replace fixed library with dynamic slider (3-20 sides).

**UI:**
```
[Add Polygon]
Sides: [====●====] 6
       3         20
```

**Implementation:**
- Slider from 3 to 20
- Real-time preview of selected polygon
- Click "Add" to instantiate in workspace
- Polygon starts at cursor position

### 12. Workspace State Machine

**States:**
1. **BROWSING**: User selecting polygon type
2. **PREVIEW**: Showing polygon at cursor
3. **PLACING**: Validating attachment
4. **ASSEMBLING**: Multi-polygon workspace
5. **STABLE**: Closed assembly detected
6. **FACE_MERGING**: GPU pruning internal faces
7. **PROMOTED**: New Unicode symbol created
8. **LIBRARY_UPDATED**: Symbol available for reuse

### 13. O/I Calculation

**O (Orientations):** Number of unique closed topologies from given polygon set.

**I (Images):** Number of rotationally distinct orientations of an assembly.

**Formula:**
```
I = O × s_total × A_c × C_sym

Where:
- O = number of valid topologies
- s_total = product of valid orientation combinations
- A_c = accounting for identical polygons (n! / product of identical counts)
- C_sym = symmetry group order
```

**Example:**
- 2 triangles + 1 square
- O = 6 (6 ways to connect)
- s_total ≈ 3 × 3 × 4 = 36 (but constrained by attachments)
- A_c = 3! / 2! = 3 (two triangles identical)
- C_sym = 2 (mirror symmetry)
- I = 6 × 12 × 3 × 2 = 432 (simplified)

### 14. Continuous Generation Mode

**Purpose:** Background analysis for discovering new polyforms.

**Algorithm:**
```
1. User enables "Continuous Generation" toggle
2. Background thread monitors workspace
3. When stable assembly detected:
   a. Check if assembly is novel
   b. Calculate frequency score
   c. If frequency + stability ≥ threshold:
      - Promote to Tier 2/3
      - Allocate Unicode symbol
      - Add to library
4. Notify user of discovery
```

### 15. LOD (Level of Detail) System

**Purpose:** Optimize rendering of complex polyforms.

**Levels:**
1. **Symbol only**: Just Unicode character (12 bytes)
2. **Metadata**: O/I values, symmetry (512 bytes)
3. **Bounding box**: Simplified geometry (2KB)
4. **Full geometry**: All vertices/edges/faces (10KB+)

**Rules:**
- Distance > 100 units: Level 1 (symbol)
- Distance 50-100 units: Level 2 (metadata)
- Distance 10-50 units: Level 3 (bbox)
- Distance < 10 units: Level 4 (full)

## Implementation Priority

### Phase 1: Core Auto-Snapping
1. Attachment matrix
2. Liaison graph
3. Open edge registry
4. Auto-rotation algorithm
5. Visual feedback (green/yellow/red)

### Phase 2: 2D-to-3D Transition
1. 2D workspace mode
2. Fold angle detection
3. Transition animation
4. 3D rendering

### Phase 3: Unicode Tier Structure
1. Subscript generation (0-999)
2. Tier 1/2/3 catalogs
3. Promotion system
4. Recursive compression

### Phase 4: GPU Optimization
1. CPU/GPU handoff protocol
2. Face pruning
3. LOD system
4. Performance profiling

### Phase 5: Discovery Mode
1. Continuous generation toggle
2. Background analysis thread
3. Promotion criteria
4. Library gallery

## Key Constraints

1. **Unit edge length = 1.0** (always enforced)
2. **Edge-to-edge only** (no vertex-to-face)
3. **No gaps** (all edges must align perfectly)
4. **No deformation** (polygons are rigid)
5. **Geometric validity** (fold angles must be realizable)

## Success Criteria

- User can drag polygon into workspace
- Polygon auto-rotates to snap to existing edges
- Visual feedback shows attachment validity
- 2D workspace transitions to 3D when folds detected
- Closed assemblies are compressed to Unicode symbols
- System discovers and promotes new polyforms
- GPU rendering is smooth (60+ FPS)
- Face pruning reduces polygon count
- LOD system maintains performance with complex assemblies
