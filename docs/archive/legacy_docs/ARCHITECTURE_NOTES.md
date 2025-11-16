# Polylog6 Architecture Integration Notes

## Key Constraints from Documentation Review

### 1. Core Geometric Pillars
1. **Uniform Edge Length**: All edges are unit-length across the entire workspace
2. **Exact Edge-to-Edge Attachment**: Vertex-to-vertex alignment, no deformation
3. **Scaling via Polygon Count**: Larger forms = more edges, NOT longer edges
4. **Undeformed Folding**: Only at shared edges between polygons

### 2. Edge Attachment Validation

#### Attachment Graph Structure
```python
LiaisonGraphEdge:
  source_polygon_id: int
  target_polygon_id: int
  contact_face_indices: Tuple[int, int]  # (source_edge_idx, target_edge_idx)
  centroid_displacement: Vector3  # cached from source to target
  fold_angle_code: FoldCode  # how to reach this dihedral angle
  is_temporary: bool  # marked for decay?
```

#### Open Edge Registry
```python
OpenEdgeRegistry:
  edges: Dict[Tuple[polygon_id, edge_idx], EdgeState]
  
  class EdgeState:
    polygon_id: int
    edge_index: int
    edge_length: float  # MUST be unit length (1.0)
    centroid_to_edge_midpoint: Vector3
    current_orientation: Quaternion
    available_for_attachment: bool
    compatible_neighbors: Set[Tuple[polygon_type, edge_idx]]
```

### 3. Stability Visual Feedback

#### Edge Coloring System (GPU-rendered)
- **RED**: Boundary/open edges (not attached)
- **YELLOW**: Conditional/partially stable
- **GREEN**: Interior/valid (fully attached)

#### Closure Detection
- Track count of boundary edges remaining
- Display: "5 boundary edges remaining"
- Update in real-time as polygons attach

### 4. Fold Angle Constraints

#### Parametric Fold Sequences
```python
ParametricFoldSequence:
  base_codes: List[FoldCode]  # reference sequence
  parameter_constraints: Dict[str, (min_val, max_val)]  
    # e.g., {"dihedral_angle_0": (π/2 - 0.5, π/2 + 0.5)}
  centroid_sensitivity: Dict[str, Callable]  
  stability_function: Callable[[fold_sequence], stability_score]
```

#### Fold Execution Requirements
- Fold must complete < 5ms (real-time requirement)
- Validate fold angle within min/max constraints
- Check collision before applying fold
- Update mesh topology immediately

### 5. Attachment Resolver Logic

#### Scoring Heuristic
```
score = stability_score × closure_fit × collision_gate
```

#### Find Attachments Algorithm
1. Query attachment graph for compatible polygon pairs
2. Check edge length compatibility (must be unit length)
3. Validate fold angle constraints
4. Run collision detection
5. Score candidates by stability + closure fit
6. Return ranked list of valid attachments

### 6. Performance Targets

| Operation | Target | Notes |
|-----------|--------|-------|
| Edge matching validation | < 5ms | CPU to GPU handoff |
| Face merge completion | < 5ms | GPU topology update |
| LOD transition | < 20ms | GPU scope-aware shift |
| Closure detection refresh | < 10ms | CPU analyzes, GPU updates colors |
| Full frame render | < 16.67ms | 60+ FPS requirement |

### 7. Visualization Requirements

#### GPU Responsibilities
- Face folding and dihedral computation
- Real-time mesh topology updates
- Edge coloring (RED/YELLOW/GREEN)
- LOD transitions
- Smooth animations

#### CPU Responsibilities
- Validation and rule enforcement
- Attachment resolution
- Stability scoring
- Closure detection
- Cache management

### 8. Implementation Priorities for Visualizer

1. **3D Polygon Rendering** (THREE.js)
   - Proper 3D geometry, not 2D projections
   - Unit edge length enforcement
   - Vertex-level precision

2. **Edge Highlighting System**
   - Color edges by state (RED/YELLOW/GREEN)
   - Update in real-time
   - Shader-based for performance

3. **Snap-to-Edge Functionality**
   - Visual guides when edges align
   - Automatic attachment when within threshold
   - Validate unit edge length match

4. **Attachment Validation**
   - Check edge compatibility
   - Validate fold angles
   - Collision detection
   - Stability scoring

5. **Open Edge Tracking**
   - Maintain registry of all open edges
   - Display count of boundary edges
   - Update as polygons attach/detach

## Next Steps

1. Upgrade Canvas3D to use proper THREE.js 3D rendering
2. Implement edge detection and highlighting
3. Add snap-to-edge with visual feedback
4. Create attachment resolver
5. Implement stability scoring and edge coloring
6. Add closure detection counter
