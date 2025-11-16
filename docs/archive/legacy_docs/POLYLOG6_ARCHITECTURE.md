# Polylog6 Architecture for Visualizer

## Overview

Polylog6 uses a tiered Unicode compression system to represent polyforms efficiently. All polyforms start as 2D assemblies and can be folded into 3D structures through parametric fold sequences.

## Unicode Symbol Mapping

### Level 0: Primitive Polygons (3-20 sides)
```
A = Triangle (3 sides)
B = Square (4 sides)
C = Pentagon (5 sides)
D = Hexagon (6 sides)
E = Heptagon (7 sides)
F = Octagon (8 sides)
G = Nonagon (9 sides)
H = Decagon (10 sides)
I = Hendecagon (11 sides)
J = Dodecagon (12 sides)
K = Tridecagon (13 sides)
L = Tetradecagon (14 sides)
M = Pentadecagon (15 sides)
N = Hexadecagon (16 sides)
O = Heptadecagon (17 sides)
P = Octadecagon (18 sides)
Q = Enneadecagon (19 sides)
R = Icosagon (20 sides)
```

### Level 1: Pair Compression
```
AA → α (U+03B1)  # Two triangles
AB → β (U+03B2)  # Triangle + Square
BB → γ (U+03B3)  # Two squares
...
```

### Level 2: Cluster Encoding (Polyhedra)
```
Format: <symbol>⟨n=<count>, θ=<angle>°, σ=<symmetry>⟩
Example: Ω₁⟨n=6, θ=70.5°, σ=T⟩ (Tetrahedron)
```

### Level 3: Assembly Encoding
```
Format: <cluster_sequence>⟨symmetry⟩
Example: Ω₁²Ω₂⟨σ=C₂⟩ (Bridge structure)
```

## Tier System

### Tier 0: Primitives & Simple Pairs
- Single polygons (A, B, C, ...)
- Two-polygon combinations (AA, AB, AC, ...)
- Stored as: `{"symbol": "A11", "polygons": [11, 20], "tier": 0}`

### Tier 1: Polyhedra (Closed 3D structures)
- Tetrahedron, Cube, Octahedron, etc.
- 97 known polyhedra in catalog
- Stored with O/I values and symmetry groups

### Tier 2+: Complex Assemblies
- Multi-polyhedra structures
- Reference lower tiers
- Cascading compression

## 2D-to-3D Transition

### 2D Representation
- All polygons start flat on XY plane (z=0)
- Unit edge length = 1.0
- Edges can attach in 2D plane

### 3D Folding
- Fold angles calculated from dihedral angles
- Parametric fold sequences define transitions
- Example: Tetrahedron from 4 triangles
  - Start: 4 triangles in 2D net
  - Fold: Apply 70.5° dihedral angles
  - Result: Closed tetrahedron

### Fold Angle Constraints
- Dihedral angle θ between adjacent faces
- Valid range: 0° (flat) to 180° (folded back)
- Common angles:
  - Tetrahedron: 70.5°
  - Cube: 90°
  - Octahedron: 109.5°

## O/I Values

### O Value (Outer)
- Number of unique polygon types in assembly
- Example: AAAA (4 triangles) → O=1
- Example: AAAB (3 triangles, 1 square) → O=2

### I Value (Inner)
- Complexity metric based on attachment pattern
- Calculated from edge signature
- Higher I = more complex attachment

### Composition String
- Sequence of polygon symbols
- Example: "AAAA" = 4 triangles
- Example: "AAAB" = 3 triangles + 1 square

## Edge Signatures

Format: `<polygon_id>-<polygon_id>`

Examples:
- `"11-20"` = Triangle (11) attached to Square (20)
- `"3-3"` = Two triangles attached
- `"11-6"` = Triangle (11) attached to Pentagon (6)

## Attachment Graph

Tracks all edge-to-edge connections:
```json
{
  "polygon_id": "A1",
  "edges": [
    {
      "edge_index": 0,
      "attached_to": {
        "polygon_id": "A2",
        "edge_index": 1
      },
      "fold_angle": 70.5
    }
  ]
}
```

## LOD (Level of Detail) Metadata

### Level 1: Symbol Only
- Just the Unicode symbol
- Memory: ~12 bytes
- Load time: 0.1ms

### Level 2: Metadata
- O/I values, symmetry group
- Memory: ~512 bytes
- Load time: 0.9ms

### Level 3: Geometry + BBox
- Vertices, bounding box
- Memory: ~2KB
- Load time: 5.5ms

### Level 4: Full Geometry
- Vertices, edges, faces, attachment points
- Memory: ~10KB
- Load time: 18ms

## Scaler Tables

Used for polygon scaling while preserving unit edge length:
```json
{
  "3": {  // Triangle
    "radius": 0.577,  // Circumradius for unit edge
    "scale": 1.0
  },
  "4": {  // Square
    "radius": 0.707,
    "scale": 1.0
  }
}
```

## Export Format

Polylog6 JSON format:
```json
{
  "symbol": "A111",
  "polygons": [11, 3],
  "positions": [1, 1],
  "series": ["A", "C"],
  "chain_length": 2,
  "edge_signature": "11-3",
  "tier": 0,
  "range_name": "Two-Polygon AC",
  "range_code": "100-199",
  "base_series": "A",
  "attachment_hint": "base_C_connection",
  "unicode_codepoint": null,
  "symmetry_group": null,
  "frequency_rank": 0.5,
  "generated_at": "2025-11-13T03:55:05Z"
}
```

## Visualizer Implementation Notes

1. **Start in 2D**: All polygons placed flat on XY plane
2. **Track Attachments**: Build attachment graph as edges connect
3. **Calculate Fold Angles**: Determine dihedral angles from geometry
4. **Animate Transition**: Smoothly fold from 2D to 3D
5. **Validate Closure**: Check if all edges are closed
6. **Generate Symbol**: Create Unicode compression string
7. **Export**: Save as Polylog6 JSON format

## Key Constraints

- Unit edge length = 1.0 (enforced)
- Edges must align perfectly (no gaps)
- Fold angles must be geometrically valid
- Closed polyhedra have all edges attached
- Open assemblies have unattached edges
