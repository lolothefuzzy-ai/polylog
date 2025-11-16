# Polyform Simulator Backbone Architecture: Fold Angle Caching & Stable Subassembly Decomposition

## Executive Summary

Your system architecture combines three research domains into a novel approach:

1. **Fold angle caching from net-to-polyhedra research** — Pre-compute and store fold sequences for known stable configurations
2. **Stable subassembly decomposition** — Decay unstable assemblies into known stable subassemblies via AND/OR graphs and liaison graphs
3. **Dynamic constraint propagation** — Track open edges fluidly in workspace while maintaining variable placement options

These components connect via a **persistent weighted attachment graph** where edges cache: centroid-to-centroid displacements, fold angle codes, scaler symmetries, and open edge availability flags.

---

## Part 1: Fold Angle Caching — Net-to-Polyhedra Research Integration

### 1.1 Discrete Configuration Space as Pre-Computed Fold Path Graph

**Key Finding from PNAS Research (Demaine et al., 2011):**

The discrete configuration space for net-to-polyhedra folding forms a **graph where nodes are folding intermediates** and edges are valid transitions between intermediate states. Each transition represents one fold operation.

**Application to your system:**

Instead of calculating fold angles on-demand:

1. **Pre-compute fold path graphs** for each known stable configuration (cubes, pyramids, rectangular prisms, etc.)
2. **Store fold codes** on edges: each edge in the configuration space graph encodes which dihedral angles rotate to reach the next intermediate
3. **Cache as lookup codes** that can be referenced by polygon pair + attachment orientation

**Concrete Example:**
```
For a cube (6 squares):
- Configuration space node at i: partially folded state with 3 faces flat, 3 at dihedral angles
- Fold path edge i→i+1: rotate face F_k about hinge H_j by dihedral_angle θ_k
- Store as code: [polygon_id_k, hinge_j, θ_k]
- Index by: (net_topology_hash, start_intermediate_idx, target_intermediate_idx)
```

When assembly grows, reference pre-computed codes rather than recalculating.

### 1.2 Geodesic Paths & Minimum-Length Folding Sequences

**Key Finding from Geometry Caching Research:**

Pharr & Hanrahan (1996) achieved 99.9%+ cache hit rates by storing pre-computed geometry in spatial voxel grids. **The principle applies to fold sequences**: store shortest feasible paths rather than all possible paths.

**Application:**

Use Dijkstra's algorithm on the configuration space graph (computed once per polyform type) to find **shortest fold sequences**. These geodesics:
- Represent most stable folding pathways (validated experimentally)
- Can be stored as minimal fold-code sequences
- Are reusable when similar attachment geometries occur

**Data structure:**
```python
GeodesiccFoldSequence:
  polyform_type: int  # cube, pyramid, etc.
  start_net_topology: int  # hash of 2D net connectivity
  end_polyhedron_signature: int  # target 3D folded state
  fold_codes: List[FoldCode]  # sequence of (polygon_id, hinge_id, angle)
  feasibility_score: float  # experimental validation or computed stability
```

### 1.3 Variable Fold Angles as Parametric Functions

**Critical Adaptation:**

Your workspace allows **fluid 3D placement** where fold angles vary based on:
- Current assembly centroid
- Environmental constraints
- User-specified goals (stability vs. compactness)

**Solution:** Store fold sequences as **parametric templates**, not fixed values.

```python
ParametricFoldSequence:
  base_codes: List[FoldCode]  # reference sequence
  parameter_constraints: Dict[str, (min_val, max_val)]  
    # e.g., {"dihedral_angle_0": (π/2 - 0.5, π/2 + 0.5)}
  centroid_sensitivity: Dict[str, Callable]  
    # e.g., {"dihedral_angle_0": lambda centroid_dist: f(centroid_dist)}
  stability_function: Callable[[fold_sequence], stability_score]
```

When placing a polygon in workspace:
1. Retrieve parametric sequence for similar assembly
2. Evaluate sensitivity functions based on **current centroid distance** to target
3. Solve for optimal fold angles that satisfy constraints and maximize stability score
4. Store result for future similar attachments

---

## Part 2: Stable Subassembly Decomposition — Hierarchical Decay Model

### 2.1 Contact Graph & Liaison Graph Representation

**Key Finding from Assembly Planning Research:**

Disassembly and assembly sequence planning uses **liaison graphs** where:
- **Nodes** = individual parts/polygons
- **Edges** = physical contact relationships with metadata

**Application to polyforms:**

Extend liaison graphs with:
1. **Contact surface encoding**: which edge pair connects two polygons
2. **Stability metadata**: whether this contact can support removal of other parts
3. **Open edge list**: which edges of each polygon remain unattached

```python
LiaisonGraphNode:
  polygon_id: int
  polygon_type: int  # sides
  centroid: Vector3
  orientation: Quaternion
  open_edges: Set[int]  # edge indices not yet attached
  stability_rating: float  # can this node be removed without collapse?

LiaisonGraphEdge:
  source_polygon_id: int
  target_polygon_id: int
  contact_face_indices: Tuple[int, int]  # (source_edge_idx, target_edge_idx)
  centroid_displacement: Vector3  # cached from source to target
  fold_angle_code: FoldCode  # how to reach this dihedral angle
  is_temporary: bool  # marked for decay?
```

### 2.2 AND/OR Graph Decomposition for Subassembly Identification

**Key Finding from Disassembly Research:**

AND/OR graphs represent all valid **hierarchical decompositions** of an assembly. Nodes are subassemblies, OR-edges show alternative decompositions, AND-edges show mandatory component relationships.

**Application — Decay Strategy:**

When workspace detects unstable configuration (open edges remain, assembly is not closed):

1. **Build AND/OR decomposition graph** from current liaison graph
2. **Identify maximal stable subassemblies** using hypergraph methods (where hyperedges = subassemblies)
3. **Traverse OR-nodes to find alternatives** with fewer open edges
4. **Decay to most stable subassembly** by removing (or relocating) problematic polygons

**Concrete Algorithm:**

```
function decay_unstable_assembly(liaison_graph):
  // Step 1: Identify problematic regions (high open-edge density)
  open_edge_density = {}
  for each node in liaison_graph:
    density[node] = |node.open_edges| / perimeter[node]
  
  // Step 2: Extract all connected subgraphs (potential subassemblies)
  candidates = find_connected_subgraphs(liaison_graph)
  
  // Step 3: Score each candidate for stability
  scores = {}
  for candidate in candidates:
    contact_count = |edges_in_subgraph[candidate]|
    open_edge_count = sum(|node.open_edges| for node in candidate)
    stability = contact_count / (contact_count + open_edge_count + ε)
    scores[candidate] = stability
  
  // Step 4: Select most stable subassembly
  best = max(scores)
  
  // Step 5: Identify polygons to remove/relocate
  to_remove = liaison_graph.nodes \ best.nodes
  
  return best, to_remove
```

### 2.3 Stability Matrix & Blocking Relationships

**Key Finding from Assembly Sequence Planning:**

The **blocking matrix** encodes which parts prevent removal of which others. When a part A "blocks" part B, B cannot be removed until A is removed/moved.

**Application:**

Store a **stability matrix** in the liaison graph:

```python
StabilityMatrix:
  blocking[i][j] = True if removal of polygon i destabilizes polygon j
  supporting[i][j] = True if polygon i provides critical support to polygon j
  
  // Use transitive closure to identify minimal removal sets
  // for decaying into stable subassemblies
```

When decay is triggered:
1. Find minimal removal set using blocking matrix
2. Prioritize removal of polygons that block fewest others
3. Emit removal events to workspace
4. Re-compute liaison graph for remaining polygons

### 2.4 Hierarchical Decomposition as Recursive Tree

**Key Finding from Concurrent Assembly Planning:**

Assemblies decompose recursively. The **compressed decomposition** creates a tree where:
- Leaf nodes = individual polygons
- Internal nodes = stable subassemblies
- Tree height = decomposition levels

**Application — Representation:**

```python
AssemblyDecompositionTree:
  root: DecompositionNode
  
  class DecompositionNode:
    polygons: Set[int]  # if leaf
    children: List[DecompositionNode]  # if internal
    stability_score: float
    open_edges: int  # count in this subassembly
    
    # Traversal methods
    def find_most_stable_child(): -> DecompositionNode
    def find_minimal_complete_subgraph(): -> DecompositionNode
    def expand_to_larger_assembly(): -> DecompositionNode
```

Build this tree incrementally as polygons are added to workspace.

---

## Part 3: Open Edge Tracking & Dynamic Constraint Propagation

### 3.1 Open Edge Registry as Workspace State

**Core Concept:**

Maintain a **real-time open edge registry** that tracks which edges are available for attachment.

```python
OpenEdgeRegistry:
  edges: Dict[Tuple[polygon_id, edge_idx], EdgeState]
  
  class EdgeState:
    polygon_id: int
    edge_index: int
    edge_length: float
    centroid_to_edge_midpoint: Vector3
    current_orientation: Quaternion
    
    available_for_attachment: bool
    compatible_neighbors: Set[Tuple[polygon_type, edge_idx]]
    last_attachment_attempt: float  # timestamp
    recent_failure_count: int  # avoid retry thrashing
```

When a polygon is added/removed:
1. Update its own edge states (newly available or removed)
2. Propagate constraint changes to nearby polygons
3. Update stability ratings affected by open/closed edges

### 3.2 Constraint Propagation for Fluid Placement

**Key Finding from Constraint Satisfaction Research:**

Constraint propagation iteratively narrows variable domains by propagating constraints. Applied here:

**Variables:** placement options (polygon position, orientation, fold angle)
**Domains:** valid configurations given current assembly state
**Constraints:** non-overlap, edge alignment, stability requirements, open edge feasibility

**Algorithm:**

```
function propagate_constraints(workspace):
  // Phase 1: Collect constraints from liaison graph
  constraints = []
  for edge in liaison_graph.edges:
    constraints.append(
      NonOverlapConstraint(edge.source, edge.target),
      EdgeAlignmentConstraint(edge),
      StabilityConstraint(edge.source, edge.target)
    )
  
  for node in liaison_graph.nodes:
    constraints.append(
      OpenEdgeConstraint(node)  // at least some edges open or all closed
    )
  
  // Phase 2: Initialize domains for each unplaced polygon
  candidate_placements = {}
  for polygon in unplaced_polygons:
    domain = generate_candidate_placements(polygon, open_edge_registry)
    candidate_placements[polygon] = domain
  
  // Phase 3: Propagate iteratively
  changed = True
  while changed:
    changed = False
    for constraint in constraints:
      reduced_count = constraint.propagate(candidate_placements)
      changed = changed or (reduced_count > 0)
  
  return candidate_placements
```

### 3.3 Centroid Distance Scaler Storage on Edges

**Key Innovation:**

Rather than recalculating centroid-to-centroid distances, **cache scalers on liaison graph edges**:

```python
LiaisonGraphEdge:
  source_polygon_id: int
  target_polygon_id: int
  
  # Geometric caching (computed once, reused)
  centroid_displacement_vector: Vector3
  distance_magnitude: float
  scaler_factor: float  # magnitude relative to edge length
  
  # Symmetry caching
  symmetry_group: SymmetryGroup
  orientation_codes: Dict[int, RotationMatrix]  # orientation index -> transform
  
  # Fold angle caching
  fold_code: FoldCode  # how to reach this attachment geometry
  fold_angle_variants: Dict[str, float]  # parameterized variants
```

When evaluating placement of a new polygon:
1. **Compute attachment edge pairs** (candidate attachments)
2. **Look up cached scalers** from liaison graph
3. **Apply scaler factors** to determine placement
4. **Verify against cached symmetry codes** for orientation feasibility
5. **Store new result** if it's a novel configuration

This mirrors the **geometry caching strategy** that achieved 99.9%+ hit rates.

### 3.4 Fluid Variable Selection & Workspace State Machine

**Key Finding from Dynamic Graph Research:**

Treat the workspace as a **dynamic constraint graph** that evolves as polygons are added/removed. Graph rewiring (adding/removing edges) improves message passing and constraint propagation.

**Application — Workspace State Machine:**

```python
WorkspaceState = Enum: OPEN, PARTIALLY_ASSEMBLED, STABLE, COMPLETE, DECAY_TRIGGERED

class PolyformWorkspace:
  liaison_graph: LiaisonGraph
  open_edge_registry: OpenEdgeRegistry
  decomposition_tree: AssemblyDecompositionTree
  state: WorkspaceState
  
  def add_polygon(polygon, placement_hint=None):
    // 1. Propose placement
    candidates = propagate_constraints()
    if placement_hint: candidates = filter_by_hint(candidates)
    if not candidates: return PLACEMENT_FAILED
    
    placement = select_optimal_placement(candidates)  // scaler-guided
    
    // 2. Add to liaison graph
    node = LiaisonGraphNode(polygon, placement)
    liaison_graph.add_node(node)
    
    for nearby_polygon in open_edge_registry.nearby(node):
      if can_attach(node, nearby_polygon):
        edge = LiaisonGraphEdge(node, nearby_polygon)
        liaison_graph.add_edge(edge)  // caches centroid displacement
        update_open_edge_registry()
    
    // 3. Update state
    update_decomposition_tree()
    check_stability()
    
    return POLYGON_ADDED
  
  def remove_polygon(polygon_id):
    // Reverse of add_polygon
    // Triggers decay cascade if stability degraded
  
  def trigger_decay():
    // Invoke stable subassembly decomposition
    stable_subassembly, to_remove = decay_unstable_assembly(liaison_graph)
    
    for polygon_id in to_remove:
      emit_removal_event(polygon_id)
    
    state = DECAY_TRIGGERED
```

---

## Part 4: Integration with O(C) and I Calculation

### 4.1 Mapping Cached Structures to Combinatorial Formula

Your formula:
```
I = O × s_total × Ac × C_sym
```

**How caching supports this:**

1. **O computation:**
   - Use liaison graph as implicit enumeration of valid topologies
   - Decomposition tree pre-computes stable sub-topologies
   - Cache O values for known subassemblies (cubes: O=1 closed form, pyramids: O varies with base)

2. **s_total computation:**
   - Open edge registry tracks available orientations per polygon
   - Parametric fold sequences constrain feasible orientations
   - Cache orientation counts per topology

3. **Ac computation:**
   - Liaison graph directly encodes which polygons are identical (same type)
   - Compute Ac = n! / ∏(n_k!) from node types in current assembly

4. **C_sym computation:**
   - Symmetry codes cached on edges (orientation_codes)
   - Decomposition tree identifies symmetrical sub-assemblies
   - Apply cached symmetry group sizes to compute C_sym

### 4.2 Incremental I Estimation at Each Level

```python
def estimate_O_and_I_for_assembly(liaison_graph, decomposition_tree):
  // Step 1: Extract polygon set
  polygons = liaison_graph.nodes
  n = len(polygons)
  polygon_type_counts = count_by_type(polygons)
  
  // Step 2: Compute s_total from open edges
  s_total = 1.0
  for polygon in polygons:
    available_orientations = len(polygon.compatible_neighbors) + 1  // +1 for current
    s_total *= available_orientations
  
  // Step 3: Compute Ac from polygon types
  Ac = factorial(n)
  for count in polygon_type_counts.values():
    Ac /= factorial(count)
  
  // Step 4: Compute O from decomposition tree
  // Option A: Bottom-up composition
  O = compute_O_recursive(decomposition_tree.root)
  
  // Option B: Look up in cache if topology matches known assembly
  topology_hash = hash_liaison_graph(liaison_graph)
  if topology_hash in O_cache:
    O = O_cache[topology_hash]
  else:
    O = compute_O_recursive(decomposition_tree.root)
    O_cache[topology_hash] = O
  
  // Step 5: Compute C_sym from cached symmetry groups
  C_sym = 1.0
  for edge in liaison_graph.edges:
    C_sym *= edge.symmetry_group.order  // or /= depending on convention
  
  // Step 6: Compute I
  I = O * s_total * Ac * C_sym
  
  return I, O, s_total, Ac, C_sym
```

---

## Part 5: Data Structures & Implementation Strategy

### 5.1 Core Data Structures

```python
# Fold Angle Caching
class FoldCode:
  polygon_source_id: int
  polygon_target_id: int
  hinge_pair: Tuple[int, int]  # which edges to fold along
  dihedral_angle: float
  angle_constraints: Dict[str, (float, float)]  # parameter ranges
  
class ParametricFoldSequence:
  polyform_type: str  # "cube", "octahedron", etc.
  fold_codes: List[FoldCode]
  stability_score: float
  
# Graph Storage
class LiaisonGraph:
  nodes: Dict[int, LiaisonGraphNode]
  edges: Dict[Tuple[int, int], LiaisonGraphEdge]
  
  def add_node(node): ...
  def add_edge(edge): ...
  def remove_node(node_id): ...
  def get_neighbors(node_id): List[int]
  def compute_open_edges(): Set[Tuple[int, int]]

# Decomposition & Stability
class AssemblyDecompositionTree:
  root: DecompositionNode
  stability_matrix: np.ndarray
  
  def find_stable_subassembly(): DecompositionNode
  def identify_removal_set(): Set[int]

# Workspace State
class PolyformWorkspace:
  liaison_graph: LiaisonGraph
  open_edge_registry: OpenEdgeRegistry
  decomposition_tree: AssemblyDecompositionTree
  
  fold_code_cache: Dict[str, ParametricFoldSequence]
  O_cache: Dict[int, float]  # topology_hash -> O value
  
  def add_polygon(polygon, placement): WorkspaceState
  def trigger_decay(): (stable_assembly, removed_polygons)
  def estimate_I(): (I, O, s_total, Ac, C_sym)
```

### 5.2 Backend Integration Points

**CGAL Integration:**
- Use CGAL's arrangement and polygon mesh for collision detection
- Use BGL property maps to attach FoldCode and scaler data to edges
- Compute centroid and symmetries via CGAL geometric algorithms

**Database/Cache Layer:**
- Store fold sequences in lightweight key-value store (Redis, LevelDB)
- Key: `fold_seq:{polyform_type}:{topology_hash}` → ParametricFoldSequence
- Key: `O_value:{topology_hash}` → float

**Visualization:**
- Render liaison graph as 3D assembly diagram
- Color edges by scaler magnitude (strong/weak connections)
- Highlight open edges in workspace
- Animate decomposition tree expansion/contraction during decay

---

## Part 6: Validation Strategy

### 6.1 Ground Truth Against Enumerated Polyforms

For known sets (hexominoes, polycubes), validate:

1. **O values**: Compare liaison graph topology count vs. published enumeration
2. **s_total**: Verify orientation counts match mathematical formula
3. **I values**: Compare full calculation vs. empirical enumeration

### 6.2 Stability Testing

- Verify decay algorithm produces stable sub-assemblies
- Check that fold angle caching produces geometrically valid folds
- Validate constraint propagation narrows placement domains correctly

### 6.3 Performance Benchmarking

- Measure cache hit rate for fold codes (target: 95%+)
- Track centroid displacement reuse (target: 99%+ as per Pharr & Hanrahan)
- Profile constraint propagation time vs. exhaustive search

---

## Part 7: Recommendation

**Suggested Implementation Order:**

1. **Phase 1:** Implement LiaisonGraph, OpenEdgeRegistry, and basic workspace state machine
2. **Phase 2:** Integrate CGAL for collision detection and centroid computation
3. **Phase 3:** Build fold code caching layer and ParametricFoldSequence evaluation
4. **Phase 4:** Implement AssemblyDecompositionTree and decay algorithm
5. **Phase 5:** Add constraint propagation and fluid placement
6. **Phase 6:** Integrate O/I calculation and log-scale visualization
7. **Phase 7:** Optimize cache hit rates and benchmark against enumerated datasets

This backbone integrates net-to-polyhedra folding research, assembly planning stability theory, and geometric caching optimization into a unified system for your polyform simulator.
