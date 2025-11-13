# Polyform Image Encoding Specification
## Edge-Pixel Mapping with Bounding Box Compression

**Status:** Architecture Definition  
**Date:** 2025-11-08  
**Focus:** One-pixel-per-edge model with 8×8 and 9×9 bounding regions

---

## Executive Summary

**Core model:** Each polyform edge gets one pixel. The bounding region between opposing edges defines a compressed image subspace.

- **20-gon (max case):** 20 pixels (one per edge) → 8×8 or 9×9 bounding box
- **Octahedron:** 12 edges → fits in 4×3 or 3×4 bounding box
- **Cube:** 12 edges → fits in 4×3 or 3×4 bounding box
- **Tetrahedron:** 6 edges → fits in 2×3 or 3×2 bounding box

**Storage model:** Each edge pixel encoded as:
- **Color:** 3 bits per channel (8-bit RGB = 9 bits) or palette index (4–8 bits)
- **Pattern/Alpha:** 3–4 bits for pattern type or transparency
- **Total per edge:** ~12–16 bits per edge = 1.5–2 bytes

**Compression:** One polyform edge = one character (Unicode tier 5) encodes both geometry + color/pattern simultaneously.

---

## 1. Edge-Pixel Mapping Model

### 1.1 Geometric Foundation

**Key insight:** Polyform faces are polygons. Each edge of the polyform can be "painted" with one pixel's worth of color/pattern information.

```
Example: Cube (6 faces, 12 edges)

   +-------+
  /|      /|
 / |     / |
+-------+  |
|  |    |  |
|  +----|-+
| /     | /
|/      |/
+-------+

Edges (12):
  - 4 vertical edges
  - 4 top edges
  - 4 bottom edges

Pixel mapping:
  Each edge → 1 pixel of color/pattern
  Bounding box: (x_min, y_min) to (x_max, y_max)
  where distance between opposing edges defines box dimensions
```

### 1.2 Bounding Box Strategy: 8×8 vs 9×9

**Model 1: 8×8 grid**
```
- Resolution: 64 pixels max
- Per pixel: 6 bits (standard: 3R + 3G + 3B = 8-color palette)
- Per pixel with alpha: 8 bits (3R + 3G + 3B + 1A)
- Pattern overlay: 4 additional bits (stripe, checkerboard, solid, gradient, etc.)
- Total: 10–12 bits per edge pixel

For 20-gon (20 edges):
  20 edges × 12 bits / 8 bits/byte = 30 bytes per textured 20-gon
  vs. 20 × 256×256 RGB naive = 3.28 MB
  Ratio: 109,000:1
```

**Model 2: 9×9 grid**
```
- Resolution: 81 pixels max
- Per pixel: 6 bits (3R + 3G + 3B)
- Allows center pixel (9,9) + 8 surrounding edge pixels
- Pattern overlay: 4 additional bits
- Total: 10 bits per edge pixel (more aligned with byte boundaries)

For 20-gon (20 edges):
  20 edges × 10 bits / 8 bits/byte = 25 bytes per textured 20-gon
  Ratio: 131,000:1
```

**Recommendation:** **9×9 for consistency**
- Centered architecture (pixel at edge-center)
- 10 bits per edge = 1.25 bytes (clean packing)
- Allows optional center pixel for blend/highlight
- Aligns naturally with symmetry operations (center = fold point)

---

## 2. Bit-Level Encoding: Per-Edge Color/Pattern Storage

### 2.1 Baseline: 10-bit Encoding (9×9 model)

```
Per-edge pixel (10 bits):
  [R₂R₁R₀ G₂G₁G₀ B₂B₁B₀ P]
   └─────────────────────┘ └┘
   8-color RGB (3+3+3)    Pattern flag (1)

Color values (3 bits each):
  000 = off (0%)
  001 = 14% intensity
  010 = 29%
  011 = 43%
  100 = 57%
  101 = 71%
  110 = 86%
  111 = on (100%)

Pattern flag (1 bit):
  0 = solid color
  1 = patterned (from shared pattern library, reference via assembly context)
```

**Example encoding:**
```
Edge color: bright red with stripe pattern
  R=111 (100% red)
  G=000 (0% green)
  B=000 (0% blue)
  P=1 (patterned)
  
Binary: 1110000000 1 = 0xFC0 + pattern_id
Compact: 1 byte (with pattern lookup table)
```

### 2.2 Extended: 12-bit Encoding (per-channel precision)

```
Per-edge pixel (12 bits):
  [R₃R₂R₁R₀ G₃G₂G₁G₀ B₃B₂B₁B₀]
   └──4 bits──┘ └──4 bits──┘ └──4 bits──┘
   16-color RGB per channel

Color values (4 bits each):
  0000 = 0%
  0001 = 6.7%
  0010 = 13.3%
  ...
  1111 = 100%

Total: 12 bits / 8 = 1.5 bytes per edge
For 20-gon: 20 × 1.5 = 30 bytes per textured polyform
```

**Use case:** When finer color gradients needed (skyboxes, gradual fades, etc.)

### 2.3 Hierarchical: 8-bit Palette Index

```
Per-edge pixel (8 bits):
  [P₇P₆P₅P₄P₃P₂P₁P₀]
   └──────────────┘
   Palette index (0–255)

Palette (shared across polyform):
  256-color palette stored separately (1 tier-5 character + 256×3 bytes in external palette library)
  
Total storage:
  - Textured 20-gon: 1 char (geometry) + 1 char (palette reference) + 20 bytes (edge indices)
  - ~22 bytes per textured polyform
  - Pattern: Ω₅₀Ρ₃Ἰ₁Ἰ₂...Ἰ₂₀ where Ρ₃ = palette index 3

Use case: Photorealistic images (use full 256-color palette for smooth gradients)
```

---

## 3. Pattern/Alpha Layer: 4-Bit Encoding

### 3.1 Pattern Types (4 bits = 16 options)

```
Pattern ID (4 bits):
  0000 = solid (no pattern)
  0001 = horizontal stripes (thin, ~2 pixel period)
  0010 = vertical stripes
  0011 = diagonal stripes (45°)
  0100 = diagonal stripes (135°)
  0101 = checkerboard (2×2)
  0110 = checkerboard (4×4)
  0111 = radial gradient (from edge center outward)
  1000 = cross pattern (+ shape)
  1001 = grid (fine, ~1 pixel period)
  1010 = dots (scattered, ~3 pixel period)
  1011 = alpha blend (50% transparency with base color)
  1100 = alpha blend (25% transparency)
  1101 = alpha blend (75% transparency)
  1110 = glow (soft falloff from edge)
  1111 = reserved (future)
```

**Procedural generation:**
```python
def generate_edge_texture(color_rgb, pattern_type, edge_width=16):
    """
    Generate 9×9 texture for edge pixel.
    
    Args:
      color_rgb: (R, G, B) in 8-bit [0-255]
      pattern_type: int 0-15 (as above)
      edge_width: distance to opposite edge (varies by polyform)
    
    Returns:
      9×9 numpy array (RGB or RGBA)
    """
    texture = np.full((9, 9, 3), color_rgb, dtype=np.uint8)
    
    if pattern_type == 0x0:  # solid
        pass  # Already filled
    elif pattern_type == 0x1:  # horizontal stripes
        for y in range(9):
            if (y // 2) % 2 == 0:
                texture[y, :] = [c // 2 for c in color_rgb]  # Darken alternate rows
    elif pattern_type == 0x2:  # vertical stripes
        for x in range(9):
            if (x // 2) % 2 == 0:
                texture[:, x] = [c // 2 for c in color_rgb]
    elif pattern_type == 0x5:  # checkerboard 2×2
        for y in range(9):
            for x in range(9):
                if ((x // 2) + (y // 2)) % 2 == 0:
                    texture[y, x] = [c // 2 for c in color_rgb]
    elif pattern_type == 0x7:  # radial gradient
        center = (4, 4)
        for y in range(9):
            for x in range(9):
                dist = np.sqrt((x - center[0])**2 + (y - center[1])**2)
                alpha = 1.0 - (dist / 6.0)  # Fade from center to edge
                texture[y, x] = [int(c * alpha) for c in color_rgb]
    elif pattern_type == 0xB:  # 50% alpha blend
        texture = np.concatenate([texture, np.full((9, 9, 1), 128, dtype=np.uint8)], axis=2)
    # ... more patterns
    
    return texture
```

---

## 4. Storage Architecture: Unicode Tier 5 Integration

### 4.1 Tier 5 Symbol Allocation (Image Layer)

```
TIER 5: Image Edge Pixels
- Range: U+19000–U+197FF (2048 symbols)
- Per symbol: Encodes one polyform's complete texture layer

Encoding structure:
  Symbol = [compression_mode (2 bits) | color_depth (2 bits) | edge_data_offset (4 bits)]
  └─ 1 byte encodes mode parameters
  └─ Followed by 20 bytes (20 edges × 10 bits packed)
  └─ Total: ~21 bytes per textured polyform

Format:
  Ἰ₁ (Tier 5, symbol 1) = Encoding for first 20 textured polyforms
  Ἰ₂ (Tier 5, symbol 2) = Encoding for next 20 textured polyforms
  ...

Reverse lookup: Given a polyform Ω₅₀, find its texture via:
  texture_symbol = POLYFORM_TO_TEXTURE_MAP[Ω₅₀]
  edge_colors = decompress_texture(texture_symbol)
```

### 4.2 Compression Modes (2 bits)

```
Mode 00: Direct RGB (3+3+3 bits per edge)
  - 10 bits per edge (compact)
  - No palette lookup
  - Use case: Simple solid colors or generated patterns

Mode 01: Palette index (8 bits per edge)
  - 256-color palette (external reference)
  - Palette ID: Ρ₃ (Tier 7)
  - Use case: Photorealistic textures, smooth gradients

Mode 10: Compressed + pattern layer (10 bits + 4 bits)
  - RGB (6 bits) + pattern flag (1 bit) + pattern ID (3 bits)
  - Allows stripes, checkerboard, gradients
  - Use case: Stylized or procedurally generated images

Mode 11: Reserved
  - Future expansion (e.g., multi-layer or animation frames)
```

### 4.3 Packing Efficiency: 20 Edges → 1 Character

```
Storage breakdown (9×9 model, 10 bits/edge):

Per-polyform texture:
  - Mode bits: 2 bits
  - Color depth: 2 bits
  - Reserved: 4 bits
  - Edge data: 20 edges × 10 bits = 200 bits = 25 bytes
  - Total: 26 bytes = ~26 characters (or 13 if packed to 2-byte chars)

Optimization: Use surrogate pair encoding to store 2 polyforms per Unicode character:
  - Surrogate pairs (U+D800–U+DFFF): 1,024 code points each
  - Store 2 × 13-byte textures per surrogate pair = 26 bytes per dual-symbol
  - Effective ratio: 2,048 symbols → 4,096 polyform textures
```

---

## 5. Reconstruction Algorithm: Edge-Pixel to Mesh Texture

### 5.1 Core Reconstruction Pipeline

```python
class PolyformImageReconstructor:
    """
    Reconstruct textured polyform from compressed edge-pixel encoding.
    """
    
    def __init__(self, polyform_symbol, texture_symbol):
        """
        polyform_symbol: Ω₅₀ (geometry: 12 edges)
        texture_symbol: Ἰ₁ (colors: 12 edge pixels)
        """
        self.polyform = decompress_geometry(polyform_symbol)
        self.edge_pixels = decompress_texture(texture_symbol)
        self.edge_textures = {}
    
    def reconstruct_edge_textures(self, resolution=512):
        """
        Procedurally generate 9×9 pixel texture for each edge.
        
        Args:
          resolution: Target mesh resolution (512 = 512×512 per face)
        
        Returns:
          dict: {edge_id: 9×9 RGB array}
        """
        for edge_id, pixel_data in self.edge_pixels.items():
            color_rgb = self._decode_color(pixel_data)
            pattern_type = self._decode_pattern(pixel_data)
            
            # Generate texture
            texture = generate_edge_texture(color_rgb, pattern_type)
            self.edge_textures[edge_id] = texture
        
        return self.edge_textures
    
    def apply_to_mesh(self, mesh_vertices, mesh_faces):
        """
        Map edge textures onto 3D mesh faces.
        
        Args:
          mesh_vertices: (N, 3) array of vertex positions
          mesh_faces: (F, 3) array of face vertex indices
        
        Returns:
          textured_mesh: 3D mesh with per-face texture coordinates
        """
        for face_id, face in enumerate(mesh_faces):
            # Get edges of this face
            edges = self._get_face_edges(face)
            
            # Blend edge textures across face
            face_texture = self._blend_edge_textures(edges)
            
            # Apply to UV coordinates
            self._apply_face_texture(face_id, face_texture, mesh_vertices)
        
        return mesh_vertices, mesh_faces, texture_atlas
    
    def _decode_color(self, pixel_data):
        """Extract RGB from 10-bit encoding."""
        r = ((pixel_data >> 7) & 0x7) * 255 // 7
        g = ((pixel_data >> 4) & 0x7) * 255 // 7
        b = ((pixel_data >> 1) & 0x7) * 255 // 7
        return (r, g, b)
    
    def _decode_pattern(self, pixel_data):
        """Extract pattern type from pixel_data."""
        # Pattern stored separately in Tier 6 or as metadata
        return pixel_data & 0x1  # For now: 0=solid, 1=patterned
    
    def _blend_edge_textures(self, edge_ids):
        """
        Blend textures from multiple edges of a face.
        
        For a triangular face:
          - 3 edges → 3 edge textures
          - Blend at center: average colors
          - Blend at boundaries: fade edge textures
        
        For a square face:
          - 4 edges → 4 edge textures
          - Gradient blend from each edge toward center
        """
        num_edges = len(edge_ids)
        face_texture = np.zeros((9, 9, 3), dtype=np.uint8)
        
        if num_edges == 3:  # Triangle
            edge_textures = [self.edge_textures[eid] for eid in edge_ids]
            # Barycentric interpolation
            for y in range(9):
                for x in range(9):
                    bary_coords = self._barycentric(x, y, 9, 9)
                    color = sum(
                        bc * edge_textures[i][y, x]
                        for i, bc in enumerate(bary_coords)
                    )
                    face_texture[y, x] = color
        elif num_edges == 4:  # Square
            edge_textures = [self.edge_textures[eid] for eid in edge_ids]
            # Bilinear interpolation
            for y in range(9):
                for x in range(9):
                    u = x / 9.0
                    v = y / 9.0
                    color = (
                        (1-u)*(1-v) * edge_textures[0][y, x] +
                        u*(1-v) * edge_textures[1][y, x] +
                        (1-u)*v * edge_textures[2][y, x] +
                        u*v * edge_textures[3][y, x]
                    )
                    face_texture[y, x] = color.astype(np.uint8)
        
        return face_texture
    
    def render(self, resolution=1024, format='png'):
        """
        Render textured polyform to image.
        
        Args:
          resolution: Output image size
          format: 'png', 'jpg', 'webp'
        
        Returns:
          PIL Image or numpy array
        """
        # Generate edge textures
        self.reconstruct_edge_textures()
        
        # Create 3D mesh
        mesh = self.polyform.to_mesh()
        
        # Apply textures
        textured_mesh = self.apply_to_mesh(mesh.vertices, mesh.faces)
        
        # Rasterize with WebGL/Three.js
        renderer = PolyformRenderer(resolution)
        image = renderer.render(textured_mesh)
        
        return image
```

### 5.2 Symmetry-Aware Reconstruction

```python
def reconstruct_with_symmetry(polyform_symbol, single_edge_texture):
    """
    If polyform has symmetry, some edges share texture.
    
    Example: Cube has octahedral symmetry (24 operations)
    - 12 edges, but only 3 unique edge types
    - Store texture for 1 edge per type
    - Procedurally apply to all edges via symmetry operations
    """
    polyform = decompress_geometry(polyform_symbol)
    symmetry_group = polyform.symmetry_group  # e.g., "octahedral"
    
    # Identify unique edge orbits under symmetry group
    edge_orbits = compute_edge_orbits(polyform, symmetry_group)
    
    # Store only representative texture per orbit
    orbit_textures = {}
    for orbit_id, orbit in enumerate(edge_orbits):
        representative_edge = orbit[0]
        orbit_textures[orbit_id] = single_edge_texture[representative_edge]
    
    # Reconstruct all textures by applying symmetry operations
    all_edge_textures = {}
    for orbit_id, orbit in enumerate(edge_orbits):
        for edge_id in orbit:
            # Apply symmetry operation to bring representative to this edge
            operation = find_symmetry_operation(edge_orbits[0], edge_id, symmetry_group)
            rotated_texture = apply_rotation(orbit_textures[orbit_id], operation)
            all_edge_textures[edge_id] = rotated_texture
    
    return all_edge_textures
```

---

## 6. Data Model: Polyform + Texture Pairing

### 6.1 Association Schema

```python
class TexturedPolyform:
    """
    Combines geometry and image in single compressed representation.
    """
    
    def __init__(self, geometry_symbol: str, texture_symbol: str = None):
        self.geometry = geometry_symbol  # Ω₅₀
        self.texture = texture_symbol    # Ἰ₁ (optional)
        self.color_palette = None        # Ρ₃ (optional, for palette mode)
        
        # Lazy-loaded caches
        self._mesh = None
        self._edge_pixels = None
        self._rendered_image = None
    
    def to_compact_string(self) -> str:
        """
        Serialize to minimal Unicode string.
        
        Format: Ω₅₀Ἰ₁Ρ₃ (geometry + texture + palette)
        or: Ω₅₀ (geometry only, monochrome)
        """
        if self.texture and self.color_palette:
            return f"{self.geometry}{self.texture}{self.color_palette}"
        elif self.texture:
            return f"{self.geometry}{self.texture}"
        else:
            return self.geometry
    
    @staticmethod
    def from_compact_string(s: str):
        """Parse compact string back to components."""
        geometry = s[0]  # First character is always geometry
        texture = s[1] if len(s) > 1 else None
        palette = s[2] if len(s) > 2 else None
        return TexturedPolyform(geometry, texture, palette)
    
    def get_geometry(self):
        """Lazy-load geometry."""
        if self._mesh is None:
            self._mesh = decompress_geometry(self.geometry)
        return self._mesh
    
    def get_edge_pixels(self):
        """Lazy-load texture data."""
        if self._edge_pixels is None and self.texture:
            self._edge_pixels = decompress_texture(self.texture)
        return self._edge_pixels
    
    def render_to_image(self, resolution=512):
        """Lazy-render to image."""
        if self._rendered_image is None:
            reconstructor = PolyformImageReconstructor(self.geometry, self.texture)
            self._rendered_image = reconstructor.render(resolution=resolution)
        return self._rendered_image
```

### 6.2 Storage Example: Library of Textured Polyforms

```
USER WORKSPACE LIBRARY:

[TexturedPolyform] 
  Ω₅₀Ἰ₁Ρ₃  → Textured octahedron (red, stripes)
  Ω₂₀Ἰ₂Ρ₁  → Textured cube (blue, solid)
  Ω₆₀Ἰ₃     → Textured dodecahedron (green, no palette)

STORAGE PER ITEM:
  Geometry symbol: 1 byte
  Texture symbol: 1 byte
  Palette ref: 1 byte
  Total: 3 bytes per textured polyform

LIBRARY OF 1000 ITEMS:
  3,000 bytes = 3 KB vs. naive 1,000 × (50 KB mesh + 512×512 texture) = 265 MB
  Ratio: 88,000:1
```

---

## 7. Procedural Image Generation: Artist Pipeline

### 7.1 Direct Input: Image → Polyform

```python
def image_to_polyform(image_path, target_geometry=None):
    """
    Convert image to TexturedPolyform.
    
    Args:
      image_path: Path to PNG/JPG
      target_geometry: Optional; if None, auto-detect best-fit polyform
    
    Returns:
      TexturedPolyform instance
    """
    # Load image
    img = PIL.Image.open(image_path)
    img_array = np.array(img)
    
    # Step 1: Feature detection
    edges = cv2.Canny(img_array, 100, 200)
    
    # Step 2: Auto-detect polyform if not specified
    if target_geometry is None:
        silhouette = img_array.mean(axis=2) > 128  # Binary mask
        best_fit_polyform = fit_polyform_to_silhouette(silhouette)
    else:
        best_fit_polyform = target_geometry
    
    # Step 3: Extract edge pixels
    polyform_mesh = decompress_geometry(best_fit_polyform)
    edge_pixel_colors = extract_colors_at_edges(img_array, polyform_mesh)
    
    # Step 4: Quantize to 10-bit RGB (3+3+3)
    quantized_colors = [quantize_rgb_3bit(color) for color in edge_pixel_colors]
    
    # Step 5: Detect patterns (optional)
    pattern_types = detect_edge_patterns(img_array, polyform_mesh)
    
    # Step 6: Encode to texture symbol
    texture_symbol = encode_texture_layer(quantized_colors, pattern_types)
    
    return TexturedPolyform(best_fit_polyform, texture_symbol)
```

### 7.2 Drag-and-Drop Workflow (Architecture Mode)

```
USER ACTION: Drag polyform from library, position in workspace

SYSTEM RESPONSE:
  1. Load geometry: decompress_geometry(Ω₅₀)
  2. Load texture: decompress_texture(Ἰ₁)
  3. Render to viewport (LOD: low/medium)
  4. Place in workspace
  
  If user adjusts position → re-render (cache hit)
  If user edits texture → regenerate edge pixels → re-render

USER ACTION: Right-click → "Build off this shape"

SYSTEM RESPONSE:
  1. Get current polyform: Ω₅₀Ἰ₁
  2. Duplicate in workspace (new instance)
  3. Offer connection point suggestions (based on symmetry)
  4. Show available scaling geometries for attachment
  5. User selects → Snap with optimal face/edge matching
  6. New assembly: Ω₅₀Ἰ₁ + [scaled polyform] → Ψ₁ (assembly symbol)
```

---

## 8. Scaling Path: 20-Gon Edge Case

### 8.1 20-Gon Encoding Details

```
Polygon: 20-gon (regular icosagon)
Edges per face: 20
Total faces (if 20-gon is a single face): 1
Storage per face:
  - 20 edge pixels
  - 10 bits per pixel (9×9 bounding box model)
  - Total: 200 bits = 25 bytes

9×9 bounding box layout (20-gon inscribed):
  Polygon vertices project to 9×9 grid
  Each edge → pixel at (x_center, y_center) of bounding region
  Distance to opposite edge → ~4–5 pixels (half of 9)
```

### 8.2 Rendering: 20-Gon with Edge Textures

```python
def render_20gon_textured(edge_pixels_array, resolution=512):
    """
    Render 20-gon with 20 edge textures procedurally.
    """
    # Create 20-gon mesh
    angles = np.linspace(0, 2*np.pi, 21)[:-1]  # 20 vertices
    radius = 1.0
    vertices = np.array([[radius * np.cos(a), radius * np.sin(a), 0] for a in angles])
    
    # Create face (single polygon)
    face = np.arange(20)
    
    # Apply edge textures
    edge_colors = [decode_color(px) for px in edge_pixels_array]
    
    # Procedural UV mapping: each edge gets a strip
    uv_map = []
    for edge_id in range(20):
        # Edge strip from vertex i to vertex i+1
        u_start = edge_id / 20.0
        u_end = (edge_id + 1) / 20.0
        v_range = [0, 1]  # Radial (center to edge)
        uv_map.append((u_start, u_end, v_range))
    
    # Create texture atlas
    atlas = create_edge_texture_atlas(edge_colors, pattern_types=(0,)*20)
    
    # Render
    mesh = Mesh(vertices, face, uv_map, atlas)
    image = renderer.render(mesh, resolution=resolution)
    
    return image
```

---

## 9. Integration: Tier 5 Character Encoding

### 9.1 Complete Example Flow

```
INPUT: User loads textured octahedron from library

Unicode representation: Ω₅₀Ἰ₁Ρ₃

DECOMPRESSION:
  1. Ω₅₀ → decompress_geometry()
     Returns: 8 triangular faces, 12 edges, O symmetry, angles=[70.5°, 109.47°]
  
  2. Ἰ₁ → decompress_texture()
     Returns: [
       Edge 0: RGB(255, 0, 0) pattern=solid,
       Edge 1: RGB(255, 128, 0) pattern=stripes,
       ...
       Edge 11: RGB(0, 0, 255) pattern=checkerboard
     ]
  
  3. Ρ₃ → get_palette(3)
     Returns: 256-color palette (for high-fidelity blending)

RENDERING:
  1. Generate 8-triangular mesh from geometry
  2. For each triangle:
     - Get 3 edge textures (9×9 each)
     - Blend via barycentric interpolation
     - Map to triangle UV space
  3. Generate texture atlas
  4. Render at 512×512 resolution
  
OUTPUT: Rendered image in viewport
```

### 9.2 Performance Targets

| Operation | Target Time | Notes |
|-----------|-------------|-------|
| Decompress geometry | <0.1 ms | O(1) lookup |
| Decompress texture | <0.1 ms | O(1) lookup |
| Generate 9×9 edge texture | <1 ms | Procedural, single pixel logic |
| Blend 3 edge textures (triangle) | <2 ms | Barycentric interpolation |
| Render to 512×512 | <50 ms | Three.js/WebGL optimized |
| Full pipeline (Unicode → image) | <100 ms | Acceptable for interactive dragging |

---

## 10. Storage Comparison

### Scenario: Textured library of 100 polyforms

**Naive approach:**
```
- 100 × (geometry mesh: 50 KB + texture PNG: 512×512×3 bytes)
- Total: 100 × (50 + 786 KB) = 83.6 MB
```

**Synesthetic approach (9×9 model):**
```
- Geometry: 100 × 1 byte = 100 bytes
- Textures: 100 × 25 bytes = 2.5 KB
- Palettes: 5 shared palettes × 768 bytes = 3.84 KB
- Total: ~6.5 KB
```

**Compression ratio: 12,860:1**

---

## 11. Research & Implementation Checklist

### Phase 1: Bit-Level Encoding (Week 1)

- [ ] Define 10-bit RGB encoding functions (to_10bit, from_10bit)
- [ ] Define pattern type constants (0x0–0xF)
- [ ] Implement pack/unpack functions for 20 edges into 25 bytes
- [ ] Unit tests: verify round-trip encoding/decoding

### Phase 2: Procedural Generation (Week 2)

- [ ] Implement generate_edge_texture() for all 16 pattern types
- [ ] Implement blend_edge_textures() (barycentric + bilinear)
- [ ] Implement render pipeline (mesh → texture atlas → image)
- [ ] Verify output against reference images

### Phase 3: Tier 5 Integration (Week 2–3)

- [ ] Allocate Tier 5 Unicode range (U+19000–U+197FF)
- [ ] Implement compress_texture_symbol() / decompress_texture_symbol()
- [ ] Build TexturedPolyform class (geometry + texture pairing)
- [ ] Integrate with existing Tier 2–4 architecture

### Phase 4: Image-to-Polyform Pipeline (Week 3–4)

- [ ] Implement image_to_polyform() (feature detection → fit → extract)
- [ ] Implement fit_polyform_to_silhouette() (Procrustes alignment)
- [ ] Test on 50 sample images; measure fit accuracy
- [ ] Tune quantization for acceptable fidelity

### Phase 5: Architecture Mode UI (Week 4–5)

- [ ] Drag-and-drop polyform from library
- [ ] Real-time texture rendering (LOD system)
- [ ] Right-click → "Build off this shape" workflow
- [ ] Save textured assembly as new library item

### Phase 6: Performance Optimization (Week 5–6)

- [ ] Profile render pipeline; identify bottlenecks
- [ ] Cache edge textures (LRU)
- [ ] Parallel texture generation (GPU if available)
- [ ] Benchmark: 100 textured polyforms at 60 FPS

---

## 12. Conclusion

**9×9 bounding box model is optimal** for your use case:
- 20 edges × 10 bits = 25 bytes per textured polyform
- Clean bit-packing (1.25 bytes per edge)
- Aligns with symmetry fold points (center pixel)
- Procedural reconstruction is straightforward

**Storage efficiency:** 12,860:1 compression (100 textured polyforms: 83.6 MB → 6.5 KB)

**Next:** Implement Phase 1 (bit encoding) → validate on test suite → integrate with drag-and-drop UI.

---

**End of Polyform Image Encoding Specification**
