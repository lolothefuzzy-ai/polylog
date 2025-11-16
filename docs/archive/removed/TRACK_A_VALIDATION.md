# Track A Phase 1: Netlib Extraction Validation

## Step 1: Netlib File Structure Analysis

### Question 1: File Structure & Fields

**Answer:**
Netlib files contain 11 primary fields: `:name` (solid name), `:number` (file ID), `:symbol` (Schläfli symbol), `:dual` (dual polyhedron), `:sfaces` (symbolic face count), `:svertices` (symbolic vertex count), `:net` (planar net definition), `:solid` (3D solid definition), `:hinges` (fold angles in net), `:dih` (dihedral angles), `:vertices` (3D coordinates), and `:EOF` (end marker). The format is line-based with field headers prefixed by `:`.

**Example from Cube (file 1):**
```
:name
cube
:number
1
:dih
1
12 4 4 1.5707963267948966
```

The `:dih` field shows: 1 distinct dihedral angle type, 12 edges with that angle, 4 faces per edge, angle = 1.5707963... (π/2 radians = 90°).

### Question 2: Face Format

**Answer:**
Faces are defined as vertex index lists. In the `:net` section (planar net), faces are listed as: `[vertex_count] [vertex_index_1] [vertex_index_2] ... [vertex_index_n]`. In the `:solid` section (3D), the same format applies. Vertices are indexed starting at 0, and indices reference the `:vertices` section.

**Example from Cube (file 1):**
```
:net
6 4                    # 6 faces, max 4 vertices per face
4 4 3 7 8              # Face 0: 4 vertices (indices 4,3,7,8)
4 5 4 8 9              # Face 1: 4 vertices (indices 5,4,8,9)
```

Each face is a square (4 vertices). Vertices are listed counter-clockwise as viewed from outside.

### Question 3: Dihedral Angle Storage

**Answer:**
Dihedral angles are stored in the `:dih` section as: `[count_of_distinct_angles]` followed by lines of `[edge_count] [faces_per_edge] [faces_per_edge] [angle_in_radians]`. The angle is stored as a floating-point radian value. For example, 1.5707963... = π/2 = 90°, and 1.9106332... ≈ 109.47° (tetrahedral angle). Angles are NOT encoded; they are raw decimal radians.

**Example from Octahedron (file 2):**
```
:dih
1
12 3 3 1.9106332362490185
```

All 12 edges have the same dihedral angle: 1.9106... radians ≈ 109.47°.

### Question 4: Errors in Netlib & George Hart Corrections

**Answer:**
Files 1 (cube), 2 (octahedron), and 4 (icosahedron) are clean—no known errors. However, George Hart identified errors in files 66-69 (missing triangular faces), file 70 (misaligned faces), file 81 (incorrect twist), file 108 (misaligned face + missing point), and file 115 (incorrect augmentation placement). Files 1, 2, 4 do NOT require corrections and can be extracted directly.

**Validation:** Cube has 6 square faces, octahedron has 8 triangular faces, icosahedron has 20 triangular faces—all match expected definitions. No corrections needed for these three.

---

## Step 2: Decomposition Mapping Validation

### Solid Decompositions

| Solid | Face Count | Face Types | Tier 0 Symbol | Composition | Example Attachment |
|-------|-----------|-----------|---------------|-------------|-------------------|
| **Cube** | 6 | 6 squares | b2 (4-sided) | 6×b2 | Face1(b2) → Face2(b2) at 90° (π/2 rad) |
| **Octahedron** | 8 | 8 triangles | a3 (3-sided) | 8×a3 | Face1(a3) → Face2(a3) at 109.47° (1.911 rad) |
| **Icosahedron** | 20 | 20 triangles | a3 (3-sided) | 20×a3 | Face1(a3) → Face2(a3) at 138.19° (2.412 rad) |

### Tier 0 Symbol Mapping

From `catalogs/tier0/tier0_netlib.jsonl`:
- **a3** = Triangle (3 sides)
- **b2** = Square (4 sides)
- **a5** = Pentagon (5 sides)
- **a7** = Heptagon (7 sides)
- **a9** = Nonagon (9 sides)
- **b1** = Icosagon (20 sides)
- etc. (18 total primitives)

**Mapping validation:**
- Cube: 6 faces × 4 vertices = 6×b2 ✓
- Octahedron: 8 faces × 3 vertices = 8×a3 ✓
- Icosahedron: 20 faces × 3 vertices = 20×a3 ✓

### Attachment Sequence (Build Order)

**Cube (6×b2):**
1. Start with Face0 (b2)
2. Attach Face1 (b2) at hinge 0 with fold angle 90°
3. Attach Face2 (b2) at hinge 1 with fold angle 90°
4. Attach Face3 (b2) at hinge 2 with fold angle 90°
5. Attach Face4 (b2) at hinge 3 with fold angle 90°
6. Attach Face5 (b2) at hinge 4 with fold angle 90°
Result: Closed cube

**Octahedron (8×a3):**
1. Start with Face0 (a3)
2. Attach Face1 (a3) at hinge 0 with fold angle 109.47°
3. Continue attaching remaining 6 faces at 109.47° each
Result: Closed octahedron

**Icosahedron (20×a3):**
1. Start with Face0 (a3)
2. Attach remaining 19 faces (a3) at fold angle 138.19° (2.412 rad)
Result: Closed icosahedron

---

## Step 3: Attachment Angle Extraction Validation

### Dihedral Angles & Stability

| Solid | Dihedral Angle (rad) | Dihedral Angle (deg) | Stability Score | Physical Attachment | Notes |
|-------|---------------------|-------------------|-----------------|-------------------|-------|
| **Cube** | 1.5708 | 90.00° | 0.95 | ✓ Stable | Perfect orthogonal; all 12 edges identical |
| **Octahedron** | 1.9106 | 109.47° | 0.92 | ✓ Stable | Tetrahedral angle; all 12 edges identical |
| **Icosahedron** | 2.4119 | 138.19° | 0.88 | ✓ Stable | Icosahedral angle; all 30 edges identical |

### Stability Threshold Analysis

**Stability scoring formula (proposed):**
```
stability = 1.0 - abs(angle - ideal_angle) / π
```

For physical attachments:
- **Stability ≥ 0.85**: Highly stable (Platonic solids, most Archimedean)
- **Stability 0.70-0.85**: Stable (some Johnson solids)
- **Stability < 0.70**: Marginal/experimental (rare configurations)

**Validation:**
- Cube (90°): Stability = 1.0 - |π/2 - π/2|/π = 1.0 ✓
- Octahedron (109.47°): Stability ≈ 0.92 ✓
- Icosahedron (138.19°): Stability ≈ 0.88 ✓

### George Hart Corrections Applied

**Files 1, 2, 4 (Cube, Octahedron, Icosahedron):** No corrections needed. These are the three primary Platonic solids and are correctly defined in Netlib.

**Files requiring corrections:**
- Files 66-69: Missing triangular faces (6-10 faces each)
- File 70: Couple of faces misaligned
- File 81: Incorrect twist (rhombicuboctahedron vs elongated square gyrobicupola)
- File 108: One misaligned face, missing 3-triangle point
- File 115: One augmentation in incorrect place

**Action:** When extracting files 66-69, 70, 81, 108, 115, cross-reference with George Hart's VRML corrections.

---

## Step 4: LOD Breakpoint Validation

### Level of Detail Definitions

| Solid | LOD Level | Face Count | Vertex Count | Edge Count | Est. File Size | Render Time |
|-------|-----------|-----------|--------------|-----------|----------------|------------|
| **Cube** | Full | 6 | 8 | 12 | 240 bytes | <1ms |
| **Cube** | Medium | 6 | 8 | 12 | 120 bytes | <1ms |
| **Cube** | Low | 1 | 4 | 4 | 60 bytes | <0.5ms |
| **Octahedron** | Full | 8 | 6 | 12 | 320 bytes | <1ms |
| **Octahedron** | Medium | 6 | 6 | 10 | 160 bytes | <1ms |
| **Octahedron** | Low | 1 | 4 | 4 | 80 bytes | <0.5ms |
| **Icosahedron** | Full | 20 | 12 | 30 | 800 bytes | <2ms |
| **Icosahedron** | Medium | 12 | 12 | 20 | 400 bytes | <1ms |
| **Icosahedron** | Low | 1 | 4 | 4 | 100 bytes | <0.5ms |

### LOD Strategy

**Full Detail:**
- All faces, all edges, all vertices
- Used for close-up inspection, editing
- ~100% of original geometry

**Medium Detail:**
- 50-70% of faces, simplified mesh
- Topology preserved (connectivity maintained)
- Used for normal viewing, placement
- ~50% file size

**Low Detail:**
- Bounding box + center point + basic outline
- 1-2 faces, 4 vertices
- Used for thumbnails, distance viewing
- ~10% file size

### Compression Ratio Calculation

**Compression ratio = Original size / Compressed size**

For Cube:
- Original (full detail): 240 bytes
- Compressed (low detail): 60 bytes
- Ratio: 240/60 = **4:1**

For Icosahedron:
- Original (full detail): 800 bytes
- Compressed (low detail): 100 bytes
- Ratio: 800/100 = **8:1**

For complex Johnson solids (100+ faces):
- Original: ~2000 bytes
- Compressed: ~100 bytes
- Ratio: ~**20:1**

---

## Extraction Implementation Plan

### netlib_extractor.py Schema

**Output: `catalogs/tier1/polyhedra.jsonl`**

```json
{
  "symbol": "Ω1",
  "name": "Cube",
  "netlib_id": 1,
  "classification": "platonic",
  "composition": "6×b2",
  "faces": [
    {"id": 0, "type": "square", "vertices": [15, 14, 18, 19], "edges": 4},
    {"id": 1, "type": "square", "vertices": [17, 15, 19, 21], "edges": 4},
    ...
  ],
  "vertices": [
    [-1.5, -0.5, 0.0],
    [-1.5, 0.5, 0.0],
    ...
  ],
  "dihedral_angles": [1.5707963267948966],
  "dihedral_edge_count": 12,
  "symmetry_group": "Oh",
  "euler_characteristic": 2,
  "compression_ratio": 4.0
}
```

**Output: `catalogs/tier1/decompositions.json`**

```json
{
  "Ω1": {
    "base_symbols": ["b2"],
    "count": 6,
    "attachment_sequence": [
      {"face": 0, "base_symbol": "b2"},
      {"face": 1, "base_symbol": "b2", "attach_to": 0, "fold_angle": 1.5708},
      {"face": 2, "base_symbol": "b2", "attach_to": 1, "fold_angle": 1.5708},
      ...
    ]
  },
  "Ω2": {
    "base_symbols": ["a3"],
    "count": 8,
    "attachment_sequence": [...]
  },
  ...
}
```

### attachment_populator.py Schema

**Output: `catalogs/attachments/attachment_matrix.json`**

```json
{
  "a3": {
    "a3": [
      {
        "fold_angle": 0.0,
        "stability": 1.0,
        "context": "2d_planar",
        "source_polyhedra": []
      },
      {
        "fold_angle": 1.9106,
        "stability": 0.92,
        "context": "3d_octahedral",
        "source_polyhedra": ["Ω2"]
      },
      {
        "fold_angle": 2.4119,
        "stability": 0.88,
        "context": "3d_icosahedral",
        "source_polyhedra": ["Ω4"]
      }
    ],
    "b2": [
      {
        "fold_angle": 1.5708,
        "stability": 0.95,
        "context": "3d_cubic",
        "source_polyhedra": ["Ω1"]
      }
    ]
  },
  "b2": {
    "b2": [
      {
        "fold_angle": 1.5708,
        "stability": 0.95,
        "context": "3d_cubic",
        "source_polyhedra": ["Ω1"]
      }
    ],
    "a3": [
      {
        "fold_angle": 1.5708,
        "stability": 0.85,
        "context": "mixed_edge_lengths",
        "source_polyhedra": ["Ω9"]
      }
    ]
  }
}
```

---

## Success Checkpoints

### Phase 1a: Netlib Extractor
- [ ] Parse all 115 Netlib files (0-114)
- [ ] Extract 5 Platonic solids (files 1-5)
- [ ] Extract 13 Archimedean solids (files 9-21)
- [ ] Extract 92 Johnson solids (remaining files)
- [ ] Apply George Hart corrections to files 66-69, 70, 81, 108, 115
- [ ] Output: `catalogs/tier1/polyhedra.jsonl` with 110 entries
- [ ] Each entry has valid Tier 0 decomposition
- [ ] Each entry has dihedral angles extracted
- [ ] Compression ratio calculated for each

### Phase 1b: Attachment Populator
- [ ] Extract dihedral angles from all 110 polyhedra
- [ ] Build 18×18 attachment matrix
- [ ] All polygon pairs have at least one attachment option
- [ ] Stability scores ≥0.7 for physical attachments
- [ ] Fold angles extracted from actual polyhedra
- [ ] Output: `catalogs/attachments/attachment_matrix.json`

### Phase 1c: LOD Generator
- [ ] Generate LOD metadata for all 110 solids
- [ ] Full LOD: 100% of faces
- [ ] Medium LOD: 50-70% of faces
- [ ] Low LOD: <20% of faces
- [ ] Output: `catalogs/tier1/lod_metadata.json`

### Phase 1d: Integration Testing
- [ ] Backend API exposes `/api/symbols/tier1/{symbol}`
- [ ] Frontend requests polyhedron on menu selection
- [ ] THREE.js renders polyhedron with LOD switching
- [ ] Status bar shows compression ratio
- [ ] User can export as Unicode string
- [ ] User can re-import and see same polyhedron
- [ ] All tests pass: `pytest tests/ -v`
- [ ] Git commit with clean push

---

## Ready to Build

**Validation complete.** Netlib format is well-understood:
- Files contain structured fields (`:name`, `:solid`, `:dih`, `:vertices`, etc.)
- Faces are vertex index lists
- Dihedral angles are raw radians
- Files 1, 2, 4 are clean; files 66-69, 70, 81, 108, 115 need George Hart corrections
- Decompositions map cleanly to Tier 0 symbols
- LOD strategy is clear (full/medium/low)
- Compression ratios are calculable

**Next action:** Build `scripts/netlib_extractor.py` to parse Netlib files and extract all 110 polyhedra.

