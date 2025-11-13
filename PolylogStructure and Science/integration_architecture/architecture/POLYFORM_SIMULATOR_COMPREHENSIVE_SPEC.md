# Polyform Combinatorial Simulator: Comprehensive Design Specification

**Version:** 2.0  
**Target Platform:** Desktop Application (Windows/Linux/Mac)  
**Architecture:** Cascading Reference System with Interactive 3D Visualization  
**Date:** 2025-11-06

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Mathematical Foundation](#mathematical-foundation)
3. [Cascading Reference Architecture](#cascading-reference-architecture)
4. [Desktop Application Architecture](#desktop-application-architecture)
5. [User Interaction Design](#user-interaction-design)
6. [Generator Engine with Expansion Patterns](#generator-engine-with-expansion-patterns)
7. [Memory Management & Storage Strategy](#memory-management--storage-strategy)
8. [Technical Implementation Requirements](#technical-implementation-requirements)
9. [Research Resources & References](#research-resources--references)
10. [Implementation Roadmap](#implementation-roadmap)

---

## 1. Executive Summary

### 1.1 Project Vision

A desktop simulator that enables users to:
- Generate, visualize, and manipulate 3D polyform assemblies interactively
- Calculate exact combinatorial values (O and I) for polyform configurations
- Explore design space through automated generation with multiple expansion patterns
- Save and reuse stable polyforms as building blocks for larger structures
- Achieve massive visual complexity without proportional memory overhead through cascading references

### 1.2 Core Innovation

**Cascading Reference System**: Large polyforms reference smaller stable polyforms, which reference primitives. This creates a hierarchical memory structure where:
- A 1000-polygon assembly might only store ~50 references to 20-polygon clusters
- Those clusters reference ~200 primitive polygons
- Net storage: ~250 references instead of 1000 polygon definitions
- Visual explosion without memory explosion

### 1.3 Key Capabilities

| Capability | Description |
|-----------|-------------|
| **Real-time 3D Rendering** | Interactive visualization with fold animations |
| **Combinatorial Analysis** | Compute O (distinct configs) and I (total arrangements) |
| **Automated Generation** | AI-driven exploration with 6 expansion patterns |
| **User Interaction** | Click-to-add, drag-to-rotate, toggle generators |
| **Pattern Recognition** | Detect and save stable symmetries automatically |
| **Hierarchical Storage** | Cascading references from primitives → clusters → assemblies |
| **Cross-platform** | Desktop app for Windows, Linux, Mac |

---

## 2. Mathematical Foundation

### 2.1 Core Formula for I (Total Image Arrangements)

```
I = O × s_total × Ac × C_sym
```

**Where:**

| Variable | Definition | Formula |
|----------|-----------|---------|
| **O** | Distinct topological configurations | Computed via enumeration or geometric series |
| **s_total** | Total orientation complexity | `∏_i (s_i ^ n_i)` for m polygon types |
| **Ac** | Arrangement capability (permutations) | `n! / ∏_i (n_i!)` |
| **C_sym** | Symmetry correction factor | `C_rot × C_centroid × C_reflect` |

### 2.2 Expanded Component Definitions

#### 2.2.1 O (Distinct Configurations)

**For enumeration-based calculation:**
```
O = count(unique_topologies)  // via backtracking with canonical deduplication
```

**For estimation-based calculation (large n):**
```
O_est = ∑_{k=1}^{n} a × r^k
```
Where:
- `a` = base configuration count (calibrated from small n)
- `r` = growth ratio (empirically derived)
- `n` = total polygon count

**For cascading reference estimation:**
```
O_cascading = ∏[base_clusters] O_cluster(n_i) × Φ(fold_constraints)
```
Where:
- `O_cluster(n_i)` = known O for stable cluster type i
- `Φ(fold_constraints)` = fold angle freedom factor

#### 2.2.2 Fold Angle Freedom Factor (Φ)

```
Φ = ∏[connections] (1 + α_j × DOF_j)
```
Where:
- `α_j` = angular tolerance at connection j (degrees / 5° steps)
- `DOF_j` = degrees of freedom for fold angle (typically 1-2)

**Example:** 
- Connection with 90° ± 45° range → α = 45/5 = 9 steps
- DOF = 1 (single dihedral angle)
- Φ_connection = 1 + 9 × 1 = 10

#### 2.2.3 s_total (Orientation Complexity)

```
s_total = ∏_{i=1}^{m} (s_i ^ n_i)
```

**For mixed polygon sets:**
- s_i = number of sides (and orientations) for polygon type i
- n_i = count of polygon type i

**Example:**
- 3 triangles (s=3) + 2 hexagons (s=6)
- s_total = 3^3 × 6^2 = 27 × 36 = 972

#### 2.2.4 Ac (Arrangement Capability)

```
Ac = n! / ∏_{i=1}^{m} (n_i!)
```

**Interpretation:**
- Accounts for which polygons are swappable (identical type)
- Reduces overcounting when polygons are indistinguishable

**Examples:**
| Set Composition | n | Ac Formula | Ac Value |
|----------------|---|-----------|----------|
| 6 identical squares | 6 | 6! / 6! | 1 |
| 3 triangles + 2 squares | 5 | 5! / (3! × 2!) | 10 |
| 2 tri + 2 sq + 2 hex | 6 | 6! / (2! × 2! × 2!) | 90 |

#### 2.2.5 C_sym (Symmetry Correction)

```
C_sym = C_rot × C_centroid × C_reflect
```

**Component breakdown:**

| Component | Formula | Typical Value |
|-----------|---------|---------------|
| C_rot | 1 / rotational_symmetry_group_size | 1 (asymmetric) |
| C_centroid | 2 if centroid-symmetric, 1 otherwise | 1 (typical) |
| C_reflect | 1 for asymmetric, 1/2 if reflectable | 1 (typical) |

**For 3D assemblies:**
```
C_sym_3D = 1 / |symmetry_group|
```

Common symmetry groups:
- Trivial (C_1): |G| = 1
- Cyclic (C_n): |G| = n
- Dihedral (D_n): |G| = 2n
- Tetrahedral (T): |G| = 12
- Octahedral (O): |G| = 24
- Icosahedral (I): |G| = 60

### 2.3 Validation Against Ground Truth

| Test Case | Expected O | Expected I | Formula |
|-----------|-----------|-----------|---------|
| 5 squares (pentominoes) | 18 | 18 × 4^5 × 1 × 1 = 18,432 | One-sided pentominoes |
| 6 squares (hexominoes) | 60 | 60 × 4^6 × 1 × 1 = 245,760 | One-sided hexominoes |
| Single triangle | 1 | 1 × 3 × 1 × 1 = 3 | 3 orientations |
| Tetrahedron (4 tri) | 1 | 1 × 3^4 × 1 × (1/12) ≈ 7 | Tetrahedral symmetry |

---

## 3. Cascading Reference Architecture

### 3.1 Hierarchical Storage Levels

```
Level 0: PRIMITIVES (Base Polygons)
    ↓
Level 1: STABLE CLUSTERS (Known Polyhedra)
    ↓
Level 2: COMPOUND ASSEMBLIES (User-created or generated)
    ↓
Level 3: MEGA-STRUCTURES (References to Level 2)
```

### 3.2 Data Structure Specifications

#### 3.2.1 Level 0: Primitive Polygon Schema

```json
{
  "type": "primitive",
  "id": "polygon_triangle_base",
  "sides": 3,
  "edge_length": 1.0,
  "O_value": 1,
  "s_value": 3,
  "vertices": [[0, 0, 0], [1, 0, 0], [0.5, 0.866, 0]],
  "internal_angles": [60, 60, 60],
  "design_features": {
    "face_design": "asymmetric_pattern_A",
    "null_face": true
  }
}
```

#### 3.2.2 Level 1: Stable Cluster Schema

```json
{
  "type": "stable_cluster",
  "id": "tetrahedron_4tri_standard",
  "name": "Regular Tetrahedron",
  "composition": {
    "polygon_triangle_base": 4
  },
  "O_base": 1,
  "symmetry_group": "T",
  "symmetry_order": 12,
  "fold_schema": {
    "connections": [
      {"poly_A": 0, "poly_B": 1, "edge_A": 0, "edge_B": 0, "angle": 70.5, "variability": 0},
      {"poly_A": 0, "poly_B": 2, "edge_A": 1, "edge_B": 0, "angle": 70.5, "variability": 0},
      {"poly_A": 0, "poly_B": 3, "edge_A": 2, "edge_B": 0, "angle": 70.5, "variability": 0},
      {"poly_A": 1, "poly_B": 2, "edge_A": 1, "edge_B": 1, "angle": 70.5, "variability": 0},
      {"poly_A": 1, "poly_B": 3, "edge_A": 2, "edge_B": 1, "angle": 70.5, "variability": 0},
      {"poly_A": 2, "poly_B": 3, "edge_A": 2, "edge_B": 2, "angle": 70.5, "variability": 0}
    ],
    "is_closed": true,
    "is_rigid": true
  },
  "centroid": [0.5, 0.289, 0.204],
  "bounding_box": {"min": [0, 0, 0], "max": [1, 0.866, 0.816]},
  "precomputed_attachment_points": [
    {"face_normal": [0, 0, 1], "attachment_type": "face"},
    {"edge_midpoint": [0.5, 0, 0], "attachment_type": "edge"}
  ]
}
```

#### 3.2.3 Level 2: Compound Assembly Schema

```json
{
  "type": "compound_assembly",
  "id": "user_assembly_xyz_001",
  "name": "Double Tetrahedron Bridge",
  "base_clusters": [
    {"cluster_id": "tetrahedron_4tri_standard", "count": 2, "instance_ids": ["tet_A", "tet_B"]},
    {"cluster_id": "cube_6sq_standard", "count": 1, "instance_ids": ["cube_C"]}
  ],
  "new_connections": [
    {
      "source": {"cluster_instance": "tet_A", "attachment_point": 0},
      "target": {"cluster_instance": "cube_C", "attachment_point": 2},
      "fold_angle_range": [45, 135],
      "preferred_angle": 90,
      "current_angle": 90,
      "DOF": 1
    },
    {
      "source": {"cluster_instance": "tet_B", "attachment_point": 0},
      "target": {"cluster_instance": "cube_C", "attachment_point": 5},
      "fold_angle_range": [45, 135],
      "preferred_angle": 90,
      "current_angle": 90,
      "DOF": 1
    }
  ],
  "O_estimate": 4,
  "I_estimate": 1024,
  "expansion_type": "linear",
  "stability_score": 0.87,
  "user_saved": true,
  "tags": ["bridge", "symmetric", "stable"]
}
```

#### 3.2.4 Level 3: Mega-Structure Schema

```json
{
  "type": "mega_structure",
  "id": "radial_explosion_alpha",
  "name": "Radial 12-Arm Structure",
  "base_assemblies": [
    {"assembly_id": "user_assembly_xyz_001", "count": 12, "instance_prefix": "arm"}
  ],
  "radial_pattern": {
    "center": [0, 0, 0],
    "radius": 5.0,
    "symmetry": "D_12",
    "rotation_axis": [0, 0, 1],
    "angle_step": 30
  },
  "O_estimate": 48,
  "I_estimate": 98304,
  "memory_footprint_kb": 245,
  "rendered_polygon_count": 1200,
  "expansion_type": "radial",
  "generation_history": {
    "seed_assembly": "user_assembly_xyz_001",
    "pattern": "radial_multiply",
    "iterations": 1
  }
}
```

### 3.3 Cascading O Calculation Algorithm

```python
def calculate_O_cascading(assembly):
    """
    Calculate O for an assembly by cascading from referenced components.
    """
    if assembly.type == "primitive":
        return assembly.O_value
    
    O_product = 1
    
    # Cascade from base clusters or assemblies
    for component in assembly.base_components:
        component_obj = load_component(component.id)
        O_component = calculate_O_cascading(component_obj)
        O_product *= (O_component ** component.count)
    
    # Apply fold angle freedom factor
    fold_factor = 1
    for connection in assembly.new_connections:
        if connection.fold_angle_range:
            angle_span = connection.fold_angle_range[1] - connection.fold_angle_range[0]
            discretization = angle_span / 5  # 5-degree steps
            fold_factor *= (1 + discretization * connection.DOF)
    
    # Apply symmetry reduction
    if assembly.symmetry_group:
        symmetry_order = get_symmetry_group_order(assembly.symmetry_group)
        O_product /= symmetry_order
    
    return O_product * fold_factor
```

### 3.4 Memory Savings Analysis

**Example: 1000-polygon radial structure**

| Storage Method | Memory Usage | Description |
|---------------|--------------|-------------|
| **Naive (store all)** | ~1000 polygon defs × 500 bytes ≈ 500 KB | Every polygon stored individually |
| **Cascading (Level 2)** | ~50 assembly refs × 200 bytes ≈ 10 KB | References to 20-polygon assemblies |
| **Cascading (Level 3)** | ~12 mega refs × 300 bytes ≈ 3.6 KB | References to 80-polygon structures |

**Memory savings: ~99% for large structures**

---

## 4. Desktop Application Architecture

### 4.1 Technology Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **Backend Engine** | Python 3.11+ | Existing codebase, scientific libraries |
| **3D Rendering** | Three.js / Babylon.js (via WebView) | High-performance WebGL, wide support |
| **Desktop Framework** | Electron or Tauri | Cross-platform, embeds web UI |
| **API Layer** | FastAPI (existing) | Already implemented, well-tested |
| **Database** | SQLite (local) + JSON files | Lightweight, portable, version-controllable |
| **UI Framework** | React or Vue.js | Reactive components, large ecosystem |

### 4.2 Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    Desktop Application                   │
│  ┌────────────────────────────────────────────────────┐ │
│  │              UI Layer (Electron/Tauri)             │ │
│  │  ┌──────────────────────────────────────────────┐ │ │
│  │  │   3D Viewport (Three.js/Babylon.js)          │ │ │
│  │  │   - Real-time rendering                      │ │ │
│  │  │   - User interaction (click, drag, rotate)   │ │ │
│  │  │   - Fold animations                          │ │ │
│  │  └──────────────────────────────────────────────┘ │ │
│  │  ┌──────────────────────────────────────────────┐ │ │
│  │  │   Control Panel                               │ │ │
│  │  │   - Generator toggles                         │ │ │
│  │  │   - Expansion pattern selectors              │ │ │
│  │  │   - Polygon palette (3-20 sides)             │ │ │
│  │  │   - Save/Load controls                       │ │ │
│  │  └──────────────────────────────────────────────┘ │ │
│  │  ┌──────────────────────────────────────────────┐ │ │
│  │  │   Analytics Dashboard                         │ │ │
│  │  │   - O and I display                          │ │ │
│  │  │   - Convergence graph (log scale)            │ │ │
│  │  │   - Memory usage monitor                     │ │ │
│  │  └──────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────┘ │
│                           ↕                              │
│  ┌────────────────────────────────────────────────────┐ │
│  │          API Layer (FastAPI - Local Server)        │ │
│  │   /placement  /generation  /save  /load  /analyze │ │
│  └────────────────────────────────────────────────────┘ │
│                           ↕                              │
│  ┌────────────────────────────────────────────────────┐ │
│  │              Backend Engine (Python)               │ │
│  │  ┌──────────────────────────────────────────────┐ │ │
│  │  │   Automated Placement Engine                  │ │ │
│  │  │   - Connection evaluator                      │ │ │
│  │  │   - Fold sequencer                            │ │ │
│  │  │   - Collision detection (BVH)                 │ │ │
│  │  └──────────────────────────────────────────────┘ │ │
│  │  ┌──────────────────────────────────────────────┐ │ │
│  │  │   Generator Engine                            │ │ │
│  │  │   - Expansion pattern implementations         │ │ │
│  │  │   - Stability scoring                         │ │ │
│  │  │   - Symmetry detection                        │ │ │
│  │  └──────────────────────────────────────────────┘ │ │
│  │  ┌──────────────────────────────────────────────┐ │ │
│  │  │   Combinatorial Calculator                    │ │ │
│  │  │   - O calculation (enumeration/estimation)    │ │ │
│  │  │   - I calculation (full formula)              │ │ │
│  │  │   - Cascading reference resolution           │ │ │
│  │  └──────────────────────────────────────────────┘ │ │
│  │  ┌──────────────────────────────────────────────┐ │ │
│  │  │   Storage Manager                             │ │ │
│  │  │   - Hierarchical polyform database            │ │ │
│  │  │   - Cache management                          │ │ │
│  │  │   - Export/Import (JSON, STL)                │ │ │
│  │  └──────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────┘ │
│                           ↕                              │
│  ┌────────────────────────────────────────────────────┐ │
│  │         Data Layer (SQLite + JSON Files)           │ │
│  │   primitives.db  clusters.db  assemblies.db        │ │
│  │   user_saves/    cache/       exports/             │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### 4.3 Core Module Responsibilities

#### 4.3.1 Automated Placement Engine
**Location:** `Code/automated_placement_engine.py`

**Responsibilities:**
- Accept polygon or polyform addition requests
- Evaluate all possible attachment points
- Score connections based on geometric compatibility and learned patterns
- Execute fold sequences with collision detection
- Handle failures via decay/reformation

**Key Methods:**
```python
def place_polyform(target_assembly, new_polyform, mode="3D"):
    # Returns (success, new_assembly, placement_info)
    pass

def evaluate_connections(assembly, candidate):
    # Returns list of (connection, score) tuples
    pass

def fold_sequence(assembly, connection, validate=True):
    # Returns (success, folded_assembly, collision_info)
    pass
```

#### 4.3.2 Generator Engine
**Location:** `Code/continuous_exploration_engine.py` (extend)

**Responsibilities:**
- Implement 6 expansion patterns (see Section 6)
- Maintain generation state (current assembly, iteration count)
- Apply user-selected expansion strategy
- Detect stable patterns and suggest saves
- Track convergence metrics

**Key Methods:**
```python
def generate_next(assembly, pattern="explore", params={}):
    # Returns (new_assembly, metadata)
    pass

def apply_expansion_pattern(assembly, pattern, intensity):
    # Returns (expanded_assembly, expansion_info)
    pass

def detect_stable_symmetries(assembly):
    # Returns list of (symmetry_type, save_suggestion)
    pass
```

#### 4.3.3 Combinatorial Calculator
**Location:** `Code/combinatorial_calculator.py` (new module)

**Responsibilities:**
- Calculate O using enumeration or estimation
- Calculate I using full formula
- Resolve cascading references
- Cache intermediate results
- Validate against ground truth

**Key Methods:**
```python
def calculate_O(assembly, method="auto"):
    # method: "enumeration", "estimation", "cascading"
    # Returns O value
    pass

def calculate_I(assembly, O_value=None):
    # Returns I value with breakdown
    pass

def resolve_cascading_O(assembly, cache={}):
    # Returns O with cascading resolution
    pass
```

#### 4.3.4 Storage Manager
**Location:** `Code/storage_manager.py` (new module)

**Responsibilities:**
- Load/save primitives, clusters, assemblies
- Manage hierarchical database structure
- Handle cache invalidation
- Export to STL, OBJ, JSON formats
- Import user-defined polyforms

**Key Methods:**
```python
def save_assembly(assembly, level, user_forced=False):
    # Returns save_id
    pass

def load_component(component_id, level):
    # Returns component object
    pass

def export_assembly(assembly_id, format="STL"):
    # Returns file_path
    pass
```

### 4.4 Data Flow for User Interaction

**Scenario: User clicks "Add Triangle"**

```
1. UI (React) → User clicks "Add Triangle" button
   ↓
2. API call → POST /placement {"type": "triangle", "mode": "auto"}
   ↓
3. Backend receives request → Placement Engine
   ↓
4. Connection Evaluator → Score all attachment points on current assembly
   ↓
5. Select best connection → Fold Sequencer validates
   ↓
6. Collision Detection (BVH) → Check for overlaps
   ↓
7. Update assembly → Combinatorial Calculator updates O and I
   ↓
8. Storage Manager → Cache new state
   ↓
9. API response → Return {assembly_json, O, I, placement_info}
   ↓
10. UI updates → 3D Viewport renders new assembly
    ↓
11. Analytics Dashboard → Update O/I display and convergence graph
```

---

## 5. User Interaction Design

### 5.1 UI Layout

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Polyform Simulator                                    [_][□][X]       │
├─────────────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────┐ ┌─────────────────────────────────┐ │
│ │                                 │ │  Control Panel                  │ │
│ │                                 │ │ ┌─────────────────────────────┐ │ │
│ │                                 │ │ │ Generator Controls          │ │ │
│ │                                 │ │ │ ☑ Auto-Generate             │ │ │
│ │                                 │ │ │ Pattern: [Explore    ▼]     │ │ │
│ │       3D Viewport               │ │ │ Speed: [▁▁▁▃▅▇▇━] Fast     │ │ │
│ │                                 │ │ │ [▶ Start] [⏸ Pause] [⏹ Stop]│ │ │
│ │     (Interactive 3D View)       │ │ └─────────────────────────────┘ │ │
│ │                                 │ │ ┌─────────────────────────────┐ │ │
│ │                                 │ │ │ Polygon Palette             │ │ │
│ │                                 │ │ │ [△] [▢] [⬠] [⬡] [⬢] [⬣]   │ │ │
│ │                                 │ │ │  3   4   5   6   7   8      │ │ │
│ │                                 │ │ │ Sides: [3-20 ▁▁▁━━━]       │ │ │
│ │                                 │ │ └─────────────────────────────┘ │ │
│ │                                 │ │ ┌─────────────────────────────┐ │ │
│ │                                 │ │ │ Current Assembly            │ │ │
│ │                                 │ │ │ Polygons: 47                │ │ │
│ │                                 │ │ │ O: 1,234                    │ │ │
│ │                                 │ │ │ I: 9,876,543               │ │ │
│ │                                 │ │ │ Stability: ▰▰▰▰▰▰▰▱▱▱ 78%  │ │ │
│ └─────────────────────────────────┘ │ └─────────────────────────────┘ │ │
│ ┌─────────────────────────────────┐ │ ┌─────────────────────────────┐ │ │
│ │  Convergence Graph              │ │ │ Actions                     │ │ │
│ │  10⁸┤          ╭────            │ │ │ [💾 Save] [📂 Load]         │ │ │
│ │  10⁶┤      ╭───╯                │ │ │ [⤴ Export] [⚙ Settings]     │ │ │
│ │  10⁴┤  ╭───╯                    │ │ │ [🔙 Undo] [🔄 Reset]        │ │ │
│ │  10²┤──╯                        │ │ └─────────────────────────────┘ │ │
│ │     └─────────────────> n       │ └─────────────────────────────────┘ │
│ └─────────────────────────────────┘                                     │
│ Status: Generating... | Memory: 47.2 MB / 500 MB | FPS: 60             │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Interaction Modes

#### 5.2.1 Manual Mode
**User has full control:**

| Action | Input | Result |
|--------|-------|--------|
| **Add polygon** | Click polygon in palette, click position in 3D view | Polygon added at position with connection evaluation |
| **Rotate view** | Mouse drag (left button) | 3D viewport rotates around assembly |
| **Zoom** | Mouse wheel | Camera zooms in/out |
| **Select polygon** | Click polygon in 3D view | Polygon highlighted, shows properties |
| **Delete polygon** | Select + Delete key | Polygon removed, assembly revalidated |
| **Rotate polygon** | Select + drag (right button) | Polygon rotates on attachment point |
| **Move sub-assembly** | Shift + drag selected polygons | Move group while maintaining connections |

#### 5.2.2 Automated Generation Mode
**Generator runs autonomously:**

| Setting | Options | Effect |
|---------|---------|--------|
| **Pattern** | Explore, Stable Iteration, Stable Multiplication, Linear, Cubic, Explosive, Radial | Determines expansion strategy |
| **Speed** | Slow (1/sec) → Fast (30/sec) | Generations per second |
| **Stop Condition** | Polygon count, Stability threshold, Time limit | When to halt generation |
| **Intervention** | Allow user clicks during generation | User can add/remove during auto-gen |

#### 5.2.3 Hybrid Mode
**User + generator collaboration:**

- Generator runs at low speed (1-5/sec)
- User can click to add specific polygons or sub-assemblies
- Generator adjusts next suggestions based on user input
- Seamless transition between manual and auto

### 5.3 Generator Toggle Interface

**Control Panel: Generator Section**

```
┌─────────────────────────────────────────┐
│ Generator Controls                       │
│                                          │
│ Mode: ● Auto  ○ Manual  ○ Hybrid         │
│                                          │
│ Expansion Pattern:                       │
│ ┌─────────────────────────────────────┐ │
│ │ ○ Explore (random walk)             │ │
│ │ ● Stable Iteration (small steps)    │ │
│ │ ○ Stable Multiplication (symmetry)  │ │
│ │ ○ Linear (chain extension)          │ │
│ │ ○ Cubic (3D growth)                 │ │
│ │ ○ Explosive (rapid expansion)       │ │
│ │ ○ Radial (center outward)           │ │
│ └─────────────────────────────────────┘ │
│                                          │
│ Intensity: [▁▁▁▃▅▇▇━━━] 75%            │
│                                          │
│ Stability Focus:                         │
│ Low ◯━━━━●━━━━◯ High                     │
│                                          │
│ Stop When:                               │
│ ☑ Polygon count > [1000  ]              │
│ ☑ Stability < [0.5     ]                │
│ ☐ Time > [60      ] seconds             │
│                                          │
│ [▶ Start] [⏸ Pause] [⏹ Stop] [⏭ Step]  │
└─────────────────────────────────────────┘
```

### 5.4 Save System

#### 5.4.1 Automatic Saves (Stable Detection)

**Trigger conditions:**
- Assembly reaches local stability maximum (no better additions within radius)
- Symmetry detected (C_n, D_n, or higher)
- User pauses for > 5 seconds on a configuration
- Assembly closes into polyhedron (no free edges)

**Save prompt:**
```
┌─────────────────────────────────────────┐
│ Stable Configuration Detected           │
│                                          │
│ This assembly has high stability and    │
│ symmetry. Save as reusable cluster?     │
│                                          │
│ Properties:                              │
│ • 24 polygons                           │
│ • O = 48                                │
│ • Symmetry: D_6 (dihedral)              │
│ • Stability: 94%                        │
│                                          │
│ Name: [Hexagonal Tower           ]      │
│ Tags: [tower, symmetric, stable  ]      │
│                                          │
│ [💾 Save] [↺ Continue] [✕ Dismiss]      │
└─────────────────────────────────────────┘
```

#### 5.4.2 User-Forced Saves

**Manual save dialog:**
```
┌─────────────────────────────────────────┐
│ Save Assembly                            │
│                                          │
│ Level: ● Cluster  ○ Assembly  ○ Mega    │
│                                          │
│ Name: [My Custom Structure      ]       │
│ Description:                             │
│ ┌─────────────────────────────────────┐ │
│ │                                     │ │
│ │                                     │ │
│ └─────────────────────────────────────┘ │
│ Tags: [custom, experimental      ]      │
│                                          │
│ ☑ Make available in palette             │
│ ☑ Include in future generation          │
│                                          │
│ [💾 Save] [✕ Cancel]                    │
└─────────────────────────────────────────┘
```

#### 5.4.3 Cascade Promotion

**When to promote to higher level:**

| Condition | Action | New Level |
|-----------|--------|-----------|
| Assembly uses 3+ clusters | Suggest promotion to Assembly | Level 2 |
| Assembly uses 5+ assemblies | Suggest promotion to Mega-structure | Level 3 |
| Mega-structure references | Warning: max level reached | N/A |

---

## 6. Generator Engine with Expansion Patterns

### 6.1 Pattern Overview

| Pattern | Description | Use Case | Visual Effect |
|---------|-------------|----------|---------------|
| **Explore** | Random walk with stability bias | Discovery, variety | Organic, unpredictable |
| **Stable Iteration** | Small incremental additions | Controlled growth | Smooth, gradual |
| **Stable Multiplication** | Copy-paste with symmetry | Symmetric structures | Patterned, regular |
| **Linear** | Extend in one direction | Chains, rods, filaments | Long, thin |
| **Cubic** | Fill 3D space uniformly | Dense packing | Blocky, compact |
| **Explosive** | Rapid multi-point expansion | Rapid prototyping | Chaotic, dense |
| **Radial** | Grow outward from center | Spherical, dome-like | Symmetric, centered |

### 6.2 Detailed Pattern Specifications

#### 6.2.1 Explore Pattern

**Algorithm:**
```python
def explore_pattern(assembly, intensity):
    """
    Random walk with stability-weighted selection.
    """
    # Get all possible addition sites
    sites = get_free_edges(assembly)
    
    # Get polygon library (primitives + saved clusters)
    candidates = get_polygon_library(include_clusters=True)
    
    # For each site-polygon pair, score
    scores = []
    for site in sites:
        for poly in candidates:
            stability = evaluate_stability(assembly, site, poly)
            novelty = evaluate_novelty(assembly, site, poly)
            score = (1 - intensity) * novelty + intensity * stability
            scores.append((site, poly, score))
    
    # Weighted random selection
    site, poly, _ = weighted_random(scores)
    return place_polygon(assembly, site, poly)
```

**Parameters:**
- `intensity`: 0.0 (pure random) → 1.0 (only stable)
- `novelty_bonus`: Favor polygons not yet used
- `cluster_probability`: Chance to use saved cluster vs primitive

#### 6.2.2 Stable Iteration Pattern

**Algorithm:**
```python
def stable_iteration_pattern(assembly, intensity):
    """
    Greedy best-next addition with small steps.
    """
    sites = get_free_edges(assembly)
    candidates = get_polygon_library(include_clusters=(intensity > 0.7))
    
    best_score = -inf
    best_site, best_poly = None, None
    
    for site in sites:
        for poly in candidates:
            # Score based on multiple criteria
            stability = evaluate_stability(assembly, site, poly)
            closure = evaluate_closure_potential(assembly, site, poly)
            symmetry = evaluate_symmetry_preservation(assembly, site, poly)
            
            score = 0.5 * stability + 0.3 * closure + 0.2 * symmetry
            
            if score > best_score:
                best_score = score
                best_site, best_poly = site, poly
    
    return place_polygon(assembly, best_site, best_poly)
```

**Parameters:**
- `intensity`: Affects cluster usage and score weighting
- `lookahead_depth`: How many steps to simulate ahead (0-3)
- `symmetry_preference`: Bonus for maintaining symmetry

#### 6.2.3 Stable Multiplication Pattern

**Algorithm:**
```python
def stable_multiplication_pattern(assembly, intensity):
    """
    Detect and replicate symmetry patterns.
    """
    # Detect existing symmetry
    symmetry = detect_symmetry(assembly)
    
    if symmetry.type in ["C_n", "D_n"]:
        # Rotational symmetry: replicate around axis
        subassembly = extract_fundamental_domain(assembly, symmetry)
        angle = 360 / symmetry.n
        
        new_assembly = assembly.copy()
        for i in range(1, symmetry.n):
            rotated = rotate(subassembly, symmetry.axis, angle * i)
            new_assembly = merge(new_assembly, rotated)
        
        return new_assembly
    
    elif symmetry.type in ["reflective"]:
        # Mirror across plane
        mirrored = reflect(assembly, symmetry.plane)
        return merge(assembly, mirrored)
    
    else:
        # No clear symmetry: add with symmetry preference
        return stable_iteration_pattern(assembly, intensity)
```

**Parameters:**
- `symmetry_types`: Which symmetries to detect (C_n, D_n, T, O, I)
- `replication_count`: Max multiplications per step
- `merge_tolerance`: Distance threshold for joining copies

#### 6.2.4 Linear Pattern

**Algorithm:**
```python
def linear_pattern(assembly, intensity, direction="auto"):
    """
    Extend assembly in a single direction.
    """
    if direction == "auto":
        # Find longest axis
        bbox = get_bounding_box(assembly)
        direction = max_dimension_axis(bbox)
    
    # Get extremal polygon in direction
    endpoint = get_extremal_polygon(assembly, direction)
    
    # Find free edges at endpoint facing direction
    sites = get_free_edges(endpoint, facing=direction)
    
    # Select polygon that extends furthest
    candidates = get_polygon_library()
    best_extension = -inf
    best_site, best_poly = None, None
    
    for site in sites:
        for poly in candidates:
            extension = compute_extension(site, poly, direction)
            if extension > best_extension:
                best_extension = extension
                best_site, best_poly = site, poly
    
    return place_polygon(assembly, best_site, best_poly)
```

**Parameters:**
- `direction`: Vector or "auto" for longest axis
- `intensity`: Affects cluster usage
- `deviation_tolerance`: Allow slight off-axis additions

#### 6.2.5 Cubic Pattern

**Algorithm:**
```python
def cubic_pattern(assembly, intensity):
    """
    Fill 3D space with dense packing.
    """
    # Define bounding box with margin
    bbox = get_bounding_box(assembly)
    expanded_bbox = expand_bbox(bbox, margin=2.0)
    
    # Voxelize space
    voxel_grid = create_voxel_grid(expanded_bbox, resolution=1.0)
    
    # Mark occupied voxels
    for poly in assembly.polygons:
        mark_occupied(voxel_grid, poly)
    
    # Find empty voxels adjacent to occupied
    frontier = get_frontier_voxels(voxel_grid)
    
    # Score each voxel by packing efficiency
    scores = []
    for voxel in frontier:
        sites = get_attachment_sites_near(voxel, assembly)
        for site in sites:
            for poly in get_polygon_library():
                packing = evaluate_packing_efficiency(voxel, poly)
                scores.append((site, poly, packing))
    
    site, poly, _ = max(scores, key=lambda x: x[2])
    return place_polygon(assembly, site, poly)
```

**Parameters:**
- `voxel_resolution`: Grid density (0.5 - 2.0)
- `intensity`: Affects packing tightness
- `prefer_convex_hull`: Bias toward filling holes

#### 6.2.6 Explosive Pattern

**Algorithm:**
```python
def explosive_pattern(assembly, intensity):
    """
    Rapid multi-point concurrent expansion.
    """
    # Get ALL free edges
    sites = get_free_edges(assembly)
    
    # Determine how many to add (based on intensity)
    add_count = int(len(sites) * intensity * 0.5)  # Up to 50% of free edges
    add_count = max(1, min(add_count, 20))  # Clamp to [1, 20]
    
    # Score all site-polygon pairs quickly (use heuristics, not full validation)
    candidates = get_polygon_library(primitives_only=True)  # Faster
    scores = []
    
    for site in sites:
        for poly in candidates:
            # Quick geometric score only
            score = quick_geometric_score(site, poly)
            scores.append((site, poly, score))
    
    # Select top N
    top_N = sorted(scores, key=lambda x: x[2], reverse=True)[:add_count]
    
    # Add all concurrently (with collision checks)
    new_assembly = assembly.copy()
    for site, poly, _ in top_N:
        try:
            new_assembly = place_polygon(new_assembly, site, poly, validate=True)
        except CollisionError:
            continue  # Skip if collision
    
    return new_assembly
```

**Parameters:**
- `intensity`: 0.0 (add 1) → 1.0 (add up to 50% of free edges)
- `max_per_step`: Hard limit on additions per step
- `collision_tolerance`: Stricter checking when low intensity

#### 6.2.7 Radial Pattern

**Algorithm:**
```python
def radial_pattern(assembly, intensity):
    """
    Grow outward from centroid.
    """
    centroid = compute_centroid(assembly)
    
    # Partition free edges by radial shells
    sites = get_free_edges(assembly)
    shells = {}
    for site in sites:
        distance = euclidean_distance(site.midpoint, centroid)
        shell = int(distance)  # Round to nearest integer radius
        if shell not in shells:
            shells[shell] = []
        shells[shell].append(site)
    
    # Work on outermost shell
    outermost = max(shells.keys())
    outer_sites = shells[outermost]
    
    # Distribute additions evenly around shell
    angular_positions = [compute_angle(site.midpoint, centroid) for site in outer_sites]
    
    # Select sites that maximize angular diversity
    selected_sites = select_diverse_angles(outer_sites, angular_positions, count=intensity)
    
    # For each selected site, choose polygon that extends radially
    candidates = get_polygon_library()
    additions = []
    
    for site in selected_sites:
        radial_direction = normalize(site.midpoint - centroid)
        best_poly = None
        best_extension = -inf
        
        for poly in candidates:
            extension = compute_radial_extension(site, poly, radial_direction)
            if extension > best_extension:
                best_extension = extension
                best_poly = poly
        
        additions.append((site, best_poly))
    
    # Apply additions
    new_assembly = assembly.copy()
    for site, poly in additions:
        new_assembly = place_polygon(new_assembly, site, poly)
    
    return new_assembly
```

**Parameters:**
- `intensity`: Number of simultaneous radial additions (1-12)
- `angular_symmetry`: Force C_n symmetry (e.g., 6-fold for hexagonal)
- `radial_bias`: How much to favor outward vs inward

### 6.3 Pattern Chaining & Transitions

**Users can chain patterns:**

```
Example: "Stable Iteration (10 steps) → Radial (5 steps) → Stable Multiplication (2 steps)"
```

**Transition conditions:**
- After N steps
- When stability threshold reached
- When polygon count reached
- User manual trigger

**Implementation:**
```python
class PatternSequence:
    def __init__(self, steps):
        self.steps = steps  # [(pattern, params, stop_condition), ...]
        self.current_step = 0
    
    def execute_next(self, assembly):
        if self.current_step >= len(self.steps):
            return assembly, "complete"
        
        pattern, params, stop = self.steps[self.current_step]
        new_assembly = pattern(assembly, **params)
        
        if stop.is_met(new_assembly):
            self.current_step += 1
            return new_assembly, "transition"
        
        return new_assembly, "continue"
```

---

## 7. Memory Management & Storage Strategy

### 7.1 Storage Hierarchy

```
root/
├── primitives/          # Level 0: Base polygons
│   ├── triangle.json
│   ├── square.json
│   ├── pentagon.json
│   └── ... (up to 20-sided)
│
├── clusters/            # Level 1: Stable polyhedra
│   ├── tetrahedron_4tri.json
│   ├── cube_6sq.json
│   ├── octahedron_8tri.json
│   ├── dodecahedron_12pent.json
│   ├── icosahedron_20tri.json
│   └── user_clusters/   # User-saved clusters
│       ├── cluster_001.json
│       └── cluster_002.json
│
├── assemblies/          # Level 2: Compound structures
│   ├── assembly_001.json
│   ├── assembly_002.json
│   └── ...
│
├── mega_structures/     # Level 3: Large compositions
│   ├── mega_001.json
│   └── mega_002.json
│
├── cache/               # Computed O and I values
│   ├── O_cache.db       # SQLite: {assembly_hash: O_value}
│   └── I_cache.db       # SQLite: {assembly_hash: I_value}
│
├── sessions/            # User session state
│   ├── current.json     # Current workspace
│   └── autosave_*.json  # Periodic autosaves
│
└── exports/             # User exports
    ├── export_001.stl
    ├── export_002.obj
    └── export_003.json
```

### 7.2 Caching Strategy

#### 7.2.1 O and I Value Cache

**Key structure:**
```python
cache_key = hash((
    tuple(sorted(assembly.polygon_types)),  # Composition
    tuple(sorted(assembly.connection_graph)),  # Topology
    assembly.fold_schema_hash  # Fold configuration
))
```

**Cache invalidation:**
- When assembly modified
- When new connections added
- When fold angles changed
- Max cache age: 1 hour

#### 7.2.2 Collision Detection Cache

**Spatial indexing:**
- Use BVH (Bounding Volume Hierarchy) for 3D collision
- Update incrementally when polygons added
- Full rebuild when assembly rotated

**Cache structure:**
```python
collision_cache = {
    "bvh_tree": BVHNode(...),
    "polygon_aabbs": {poly_id: AABB(...)},
    "last_update": timestamp
}
```

#### 7.2.3 Rendering Cache

**LOD (Level of Detail) system:**

| Distance from Camera | Render Detail | Technique |
|---------------------|---------------|-----------|
| < 5 units | Full detail | Individual polygons with textures |
| 5-20 units | Medium detail | Simplified meshes, no textures |
| > 20 units | Low detail | Bounding boxes or cluster icons |

**Instancing for repetitive structures:**
- Detect identical sub-assemblies
- Render once, instance multiple times
- GPU instancing for massive performance

### 7.3 Memory Limits & Graceful Degradation

**Memory budgets:**

| Component | Budget | Overflow Strategy |
|-----------|--------|-------------------|
| **Working assembly** | 100 MB | Warn user, suggest save & restart |
| **Rendering buffers** | 200 MB | Reduce LOD, cull distant objects |
| **Cache** | 150 MB | LRU eviction, write to disk |
| **Total application** | 500 MB | Hard limit, enforce via checks |

**Degradation sequence:**
1. Disable texture rendering
2. Reduce polygon detail (merge coplanar faces)
3. Use bounding boxes for distant assemblies
4. Pause auto-generation
5. Prompt user to save and reduce complexity

---

## 8. Technical Implementation Requirements

### 8.1 Dependencies

#### 8.1.1 Python Backend

| Library | Version | Purpose |
|---------|---------|---------|
| **Python** | 3.11+ | Core language |
| **NumPy** | 1.24+ | Numeric computations |
| **SciPy** | 1.10+ | Optimization, spatial structures |
| **FastAPI** | 0.104+ | API server |
| **Pydantic** | 2.0+ | Data validation |
| **SQLite3** | (built-in) | Local database |
| **Trimesh** | 3.23+ | Mesh processing, STL export |
| **Matplotlib** | 3.7+ | Convergence graphs |

#### 8.1.2 Desktop Framework

**Option A: Electron**
```json
{
  "electron": "^27.0.0",
  "electron-builder": "^24.6.0",
  "react": "^18.2.0",
  "three": "^0.157.0",
  "react-three-fiber": "^8.15.0"
}
```

**Option B: Tauri**
```toml
[dependencies]
tauri = "1.5"
serde_json = "1.0"
tokio = "1.0"
```

#### 8.1.3 Frontend

| Library | Version | Purpose |
|---------|---------|---------|
| **React** | 18.2+ | UI framework |
| **Three.js** | 0.157+ | 3D rendering |
| **React Three Fiber** | 8.15+ | React bindings for Three.js |
| **Zustand** | 4.4+ | State management |
| **Axios** | 1.5+ | API calls |
| **Recharts** | 2.8+ | Convergence graphs |

### 8.2 Build & Distribution

#### 8.2.1 Development Setup

```bash
# Clone repository
git clone https://github.com/yourorg/polyform-simulator.git
cd polyform-simulator

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Frontend setup
cd ../frontend
npm install

# Run in development mode
# Terminal 1: Backend
cd backend && uvicorn api.server:app --reload --port 8000

# Terminal 2: Frontend
cd frontend && npm start
```

#### 8.2.2 Production Build

**Electron:**
```bash
cd frontend
npm run build  # Build React app
npm run electron:build  # Package with Electron

# Outputs to:
# - dist/polyform-simulator-1.0.0-win.exe
# - dist/polyform-simulator-1.0.0.dmg
# - dist/polyform-simulator-1.0.0.AppImage
```

**Tauri:**
```bash
cd frontend
npm run tauri build

# Outputs to:
# - target/release/bundle/
```

### 8.3 Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Placement time** | < 100ms per polygon | Avg over 100 placements |
| **O calculation** | < 500ms for n < 20 | Enumeration method |
| **O estimation** | < 50ms for any n | Geometric series |
| **Rendering FPS** | > 30 FPS | With 500 polygons visible |
| **UI responsiveness** | < 16ms frame time | Event loop monitoring |
| **Memory usage** | < 500 MB | Typical session |
| **Startup time** | < 3 seconds | Cold start to interactive |

### 8.4 Testing Strategy

#### 8.4.1 Unit Tests

```python
# test_combinatorial.py
def test_O_calculation_pentomino():
    assembly = create_pentomino_set(n=5, type="square")
    O = calculate_O(assembly, method="enumeration")
    assert O == 18, f"Expected 18 pentominoes, got {O}"

def test_I_calculation_single_polygon():
    assembly = create_assembly([Polygon(sides=4)])
    I = calculate_I(assembly)
    assert I == 4, f"Single square should have I=4, got {I}"

def test_cascading_O_tetrahedron():
    tet = load_cluster("tetrahedron_4tri_standard")
    O = resolve_cascading_O(tet)
    assert O == 1, f"Tetrahedron should have O=1, got {O}"
```

#### 8.4.2 Integration Tests

```python
# test_placement.py
def test_placement_no_collision():
    assembly = create_assembly([Polygon(sides=3)])
    new_poly = Polygon(sides=3)
    result = place_polyform(assembly, new_poly, mode="3D")
    assert result.success == True
    assert len(result.assembly.polygons) == 2

def test_generation_pattern_stable_iteration():
    assembly = create_assembly([Polygon(sides=4)])
    for i in range(10):
        assembly = stable_iteration_pattern(assembly, intensity=0.8)
    assert len(assembly.polygons) == 11
    assert assembly.stability_score > 0.7
```

#### 8.4.3 Performance Tests

```python
# test_performance.py
import time

def test_placement_speed():
    assembly = create_assembly([Polygon(sides=4)] * 50)
    start = time.time()
    for _ in range(100):
        new_poly = Polygon(sides=random.randint(3, 8))
        place_polyform(assembly, new_poly)
    duration = time.time() - start
    avg = duration / 100
    assert avg < 0.1, f"Avg placement time {avg}s exceeds 100ms"

def test_rendering_fps():
    assembly = create_assembly([Polygon(sides=4)] * 500)
    fps = measure_rendering_fps(assembly, duration=5.0)
    assert fps > 30, f"FPS {fps} below target 30"
```

---

## 9. Research Resources & References

### 9.1 Polyominoes & Polyforms

**Foundational Papers:**

1. **Golomb, S. W. (1965)**  
   *Polyominoes: Puzzles, Patterns, Problems, and Packings*  
   Princeton University Press  
   → Canonical reference for polyominoes, includes enumeration algorithms

2. **Redelmeier, D. H. (1981)**  
   *Counting polyominoes: yet another attack*  
   Discrete Mathematics, 36(2), 191-203  
   → Efficient enumeration algorithm for polyominoes up to n=28

3. **Conway, J. H. & Lagarias, J. C. (1990)**  
   *Tiling with polyominoes and combinatorial group theory*  
   Journal of Combinatorial Theory, Series A, 53(2), 183-208  
   → Group theory applications to polyform symmetries

**Online Resources:**

- **OEIS (Online Encyclopedia of Integer Sequences)**  
  - Sequence A000105: Free polyominoes  
  - Sequence A000988: One-sided polyominoes  
  URL: https://oeis.org/

- **Polyform Curiosities by Torsten Sillke**  
  Comprehensive catalog of polyform properties  
  URL: http://www.mathematik.uni-bielefeld.de/~sillke/PUZZLES/polyforms

### 9.2 3D Polyhedra Databases

**Platonic Solids (5 types):**
- Tetrahedron (4 triangles)
- Cube (6 squares)
- Octahedron (8 triangles)
- Dodecahedron (12 pentagons)
- Icosahedron (20 triangles)

**Archimedean Solids (13 types):**
- Truncated tetrahedron, cuboctahedron, truncated cube, truncated octahedron, rhombicuboctahedron, etc.

**Johnson Solids (92 types):**
- Strictly convex polyhedra with regular faces but not uniform
- Full catalog: https://en.wikipedia.org/wiki/Johnson_solid

**Databases:**

1. **Netlib Polyhedra Database**  
   URL: http://www.netlib.org/polyhedra/  
   → Vertices, faces, edges for common polyhedra

2. **Virtual Polyhedra by George Hart**  
   URL: http://www.georgehart.com/virtual-polyhedra/vp.html  
   → Interactive 3D models and data

3. **Polyhedron Models by Magnus Wenninger**  
   *Polyhedron Models (1971)*  
   → Physical construction techniques applicable to fold angle estimation

### 9.3 Geometric Algorithms

**Collision Detection:**

1. **van den Bergen, G. (2003)**  
   *Collision Detection in Interactive 3D Environments*  
   Morgan Kaufmann  
   → BVH, GJK, and SAT algorithms

2. **Ericson, C. (2004)**  
   *Real-Time Collision Detection*  
   CRC Press  
   → Practical implementations, optimizations

**Spatial Indexing:**

1. **Samet, H. (2006)**  
   *Foundations of Multidimensional and Metric Data Structures*  
   Morgan Kaufmann  
   → Comprehensive coverage of spatial data structures

**Mesh Processing:**

1. **Botsch, M. et al. (2010)**  
   *Polygon Mesh Processing*  
   CRC Press  
   → Algorithms for mesh manipulation, simplification

### 9.4 Symmetry Detection

**Group Theory:**

1. **Armstrong, M. A. (1988)**  
   *Groups and Symmetry*  
   Springer  
   → Mathematical foundations

2. **Alt, H. et al. (1988)**  
   *Computing the symmetries of polyhedra*  
   Algorithmica, 3(1-4), 177-193  
   → Computational methods

**Practical Implementations:**

- **Kazhdan, M. et al. (2003)**  
  *Symmetry descriptors and 3D shape matching*  
  ACM SIGGRAPH  
  → Algorithms for automatic symmetry detection

### 9.5 Combinatorial Optimization

**General Frameworks:**

1. **Papadimitriou, C. H. & Steiglitz, K. (1998)**  
   *Combinatorial Optimization: Algorithms and Complexity*  
   Dover Publications  
   → Theoretical foundations

2. **Korte, B. & Vygen, J. (2018)**  
   *Combinatorial Optimization: Theory and Algorithms* (6th ed.)  
   Springer  
   → Modern algorithms and applications

**Machine Learning for Combinatorial Problems:**

- **Cappart, Q. et al. (2023)**  
  *Combinatorial Optimization and Reasoning with Graph Neural Networks*  
  Journal of Machine Learning Research, 24(130), 1-61  
  → GNN applications to large combinatorial spaces

- **Bengio, Y. et al. (2021)**  
  *Machine Learning for Combinatorial Optimization: a Methodological Tour d'Horizon*  
  European Journal of Operational Research, 290(2), 405-421  
  → Survey of ML techniques

### 9.6 Origami & Folding Mathematics

**Rigid Origami:**

1. **Tachi, T. (2009)**  
   *Simulation of rigid origami*  
   Origami^4, pp. 175-187  
   → Fold angle constraints, kinematic models

2. **Demaine, E. D. & O'Rourke, J. (2007)**  
   *Geometric Folding Algorithms: Linkages, Origami, Polyhedra*  
   Cambridge University Press  
   → Theoretical foundations of folding

**Practical Tools:**

- **Origami Simulator by Amanda Ghassaei**  
  URL: https://origamisimulator.org/  
  → Open-source WebGL origami simulator (useful for fold angle validation)

### 9.7 Software Libraries

**Python:**

- **Trimesh** (3D mesh processing)  
  URL: https://github.com/mikedh/trimesh

- **PyVista** (3D visualization)  
  URL: https://docs.pyvista.org/

- **NetworkX** (graph algorithms for topology)  
  URL: https://networkx.org/

- **Shapely** (2D geometric operations)  
  URL: https://shapely.readthedocs.io/

**JavaScript:**

- **Three.js** (3D rendering)  
  URL: https://threejs.org/

- **Babylon.js** (alternative 3D engine)  
  URL: https://www.babylonjs.com/

- **React Three Fiber** (React integration)  
  URL: https://docs.pmnd.rs/react-three-fiber/

### 9.8 Recommended Reading Order

For developers implementing this system:

1. **Start:** Golomb (1965) - understand polyominoes
2. **Then:** Redelmeier (1981) - enumeration algorithms
3. **Next:** van den Bergen (2003) - collision detection
4. **Advanced:** Tachi (2009) - fold angle constraints
5. **ML/Optimization:** Bengio et al. (2021) - if implementing GNN features

---

## 10. Implementation Roadmap

### 10.1 Phase 1: Core Foundation (Weeks 1-3)

**Deliverables:**
- ✅ Polygon data structures (primitives)
- ✅ Basic edge alignment validation
- ✅ Collision detection (2D, then 3D)
- ✅ Canonical form computation
- ✅ O calculation via enumeration (small n < 10)

**Validation:**
- Unit tests pass for pentominoes (O=18)
- Single polygon I calculation correct

**Files to create/modify:**
```
Code/
├── polygon.py              # Polygon class with vertices, edges, design
├── geometry_utils.py       # Edge alignment, collision detection
├── canonical_form.py       # Normalization for deduplication
└── combinatorial_calc.py   # O and I calculation functions
```

### 10.2 Phase 2: Placement Engine (Weeks 4-6)

**Deliverables:**
- ✅ Automated placement with connection scoring
- ✅ Fold sequencer with validation
- ✅ Backtracking enumeration for O
- ✅ Integration with existing `automated_placement_engine.py`

**Validation:**
- Place 20 polygons with < 100ms per placement
- Generate hexominoes (O=60) correctly

**Files to create/modify:**
```
Code/
├── automated_placement_engine.py  # (extend existing)
├── connection_evaluator.py        # Scoring logic
└── fold_sequencer.py              # Fold execution with collision check
```

### 10.3 Phase 3: Storage & Cascading (Weeks 7-9)

**Deliverables:**
- ✅ Hierarchical database schema (JSON + SQLite)
- ✅ Primitive, cluster, assembly save/load
- ✅ Cascading O calculation
- ✅ Cache system for O and I

**Validation:**
- Save tetrahedron, load and validate O=1
- Cascading O for compound assembly matches direct calculation
- Cache hit rate > 80% in typical usage

**Files to create:**
```
Code/
├── storage_manager.py      # Save/load/export functions
├── cache_manager.py        # O/I value caching
└── data/                   # Data directory
    ├── primitives/
    ├── clusters/
    ├── assemblies/
    └── cache/
```

### 10.4 Phase 4: Desktop UI (Weeks 10-14)

**Deliverables:**
- ✅ Electron or Tauri shell
- ✅ 3D viewport with Three.js
- ✅ Control panel UI
- ✅ Polygon palette
- ✅ Basic user interactions (click to add, rotate view)

**Validation:**
- UI launches in < 3 seconds
- 3D viewport renders at > 30 FPS
- User can add polygons interactively

**Files to create:**
```
frontend/
├── src/
│   ├── components/
│   │   ├── Viewport3D.jsx         # Three.js viewport
│   │   ├── ControlPanel.jsx       # Generator controls
│   │   ├── PolygonPalette.jsx     # Polygon selection
│   │   └── AnalyticsDashboard.jsx # O/I display, graphs
│   ├── services/
│   │   ├── api.js                 # FastAPI client
│   │   └── rendering.js           # Three.js helpers
│   └── App.jsx                    # Main app component
└── electron-main.js (or tauri config)
```

### 10.5 Phase 5: Generator Patterns (Weeks 15-18)

**Deliverables:**
- ✅ Implement 6 expansion patterns
- ✅ Pattern chaining
- ✅ Auto-generation engine
- ✅ Stability scoring
- ✅ Symmetry detection

**Validation:**
- Each pattern produces expected assembly characteristics
- Auto-generation runs without intervention for 10 minutes
- Stable patterns auto-detected and saved

**Files to create:**
```
Code/
├── generator_engine.py           # Main generator logic
├── patterns/
│   ├── explore.py
│   ├── stable_iteration.py
│   ├── stable_multiplication.py
│   ├── linear.py
│   ├── cubic.py
│   ├── explosive.py
│   └── radial.py
├── symmetry_detector.py          # Symmetry analysis
└── stability_scorer.py           # Stability metrics
```

### 10.6 Phase 6: Polish & Optimization (Weeks 19-22)

**Deliverables:**
- ✅ Performance profiling and optimization
- ✅ Memory limit enforcement
- ✅ LOD system for rendering
- ✅ Comprehensive testing suite
- ✅ Documentation and user guide

**Validation:**
- All performance targets met
- Memory usage < 500 MB in typical session
- Test coverage > 80%

**Files to create:**
```
Code/
├── profiler.py                   # Performance monitoring
├── memory_manager.py             # Memory limit enforcement
└── tests/
    ├── test_combinatorial.py
    ├── test_placement.py
    ├── test_generation.py
    ├── test_performance.py
    └── test_integration.py

docs/
├── USER_GUIDE.md
├── API_REFERENCE.md
└── DEVELOPER_NOTES.md
```

### 10.7 Phase 7: Distribution (Weeks 23-24)

**Deliverables:**
- ✅ Build scripts for Windows, Mac, Linux
- ✅ Installers (.exe, .dmg, .AppImage)
- ✅ Update mechanism (optional)
- ✅ Release v1.0.0

**Validation:**
- Installer works on fresh systems
- App runs without external dependencies
- Uninstaller removes all files

**Build artifacts:**
```
dist/
├── polyform-simulator-1.0.0-win.exe
├── polyform-simulator-1.0.0.dmg
└── polyform-simulator-1.0.0.AppImage
```

---

## 11. Appendix: Formula Reference Card

### Quick Reference for Agent Implementation

```
=============================================================================
CORE FORMULA: I = O × s_total × Ac × C_sym
=============================================================================

O (Distinct Configurations):
  - Enumeration: O = count(unique_topologies) via backtracking
  - Estimation: O = Σ(a × r^k) for k=1 to n
  - Cascading: O = Π[O_cluster(n_i)] × Φ(fold_constraints)

s_total (Orientation Complexity):
  - s_total = Π(s_i ^ n_i) for i=1 to m polygon types
  - s_i = number of sides for type i
  - n_i = count of type i

Ac (Arrangement Capability):
  - Ac = n! / Π(n_i!) for i=1 to m polygon types
  - n = total polygon count
  - Handles swappable identical polygons

C_sym (Symmetry Correction):
  - C_sym = C_rot × C_centroid × C_reflect
  - C_rot = 1 / |rotational_symmetry_group|
  - C_centroid = 2 if centroid-symmetric, 1 otherwise
  - C_reflect = 1 for asymmetric (typical case)

Φ (Fold Angle Freedom):
  - Φ = Π(1 + α_j × DOF_j) for each connection j
  - α_j = angular_tolerance / 5° (discretization)
  - DOF_j = degrees of freedom (typically 1)

=============================================================================
VALIDATION GROUND TRUTH:
=============================================================================

Pentominoes (5 squares):
  O = 18 (one-sided)
  I = 18 × 4^5 × 1 × 1 = 18,432

Hexominoes (6 squares):
  O = 60 (one-sided)
  I = 60 × 4^6 × 1 × 1 = 245,760

Single triangle:
  O = 1
  I = 1 × 3 × 1 × 1 = 3

Tetrahedron (4 triangles):
  O = 1 (unique structure)
  I = 1 × 3^4 × 1 × (1/12) ≈ 6.75 ≈ 7 (accounting for symmetry)

=============================================================================
```

---

## 12. Summary & Next Steps for Agent

**This specification provides:**

1. ✅ Complete mathematical foundation with formulas for O, I, and cascading references
2. ✅ Detailed cascading reference architecture (4 levels: primitives → clusters → assemblies → mega-structures)
3. ✅ Desktop application architecture with technology stack and data flow
4. ✅ Full UI/UX design with interaction modes and generator toggles
5. ✅ 6 expansion pattern algorithms (Explore, Stable Iteration, Stable Multiplication, Linear, Cubic, Explosive, Radial)
6. ✅ Memory management strategy with storage hierarchy and caching
7. ✅ Technical implementation requirements (dependencies, build, performance targets)
8. ✅ Comprehensive research resources (papers, databases, libraries)
9. ✅ Phased implementation roadmap (24 weeks)

**For the receiving agent to implement:**

- Begin with **Phase 1** (Core Foundation) to establish polygon data structures and basic geometry
- Validate each phase against ground truth cases (pentominoes, hexominoes)
- Use the cascading reference system to achieve memory efficiency
- Implement generator patterns sequentially, testing each thoroughly
- Build the desktop UI around the existing FastAPI backend
- Follow the research resources for collision detection, symmetry detection, and optimization

**Key files to create (prioritized):**

1. `Code/polygon.py` - Base polygon class
2. `Code/combinatorial_calc.py` - O and I calculation
3. `Code/storage_manager.py` - Hierarchical storage
4. `Code/generator_engine.py` - Expansion patterns
5. `frontend/src/App.jsx` - Desktop UI entry point

**Success criteria:**
- ✅ Calculate correct O and I for test cases
- ✅ Interactive 3D desktop application
- ✅ User can generate, save, and load polyforms
- ✅ Memory usage < 500 MB for large structures
- ✅ Smooth 30+ FPS rendering

**Document version: 2.0**  
**Ready for handoff to implementation agent.**
