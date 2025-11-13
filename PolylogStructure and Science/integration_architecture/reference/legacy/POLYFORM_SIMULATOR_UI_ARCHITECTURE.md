# Polyform Simulator: UI/UX Architecture
## Separated Visualization & Encoding Layers

**Status:** UI Architecture Definition  
**Date:** 2025-11-08  
**Focus:** Decoupling image encoding from active workspace rendering, clean visualization pipeline

---

## Executive Summary

**Goal:** Users interact with beautiful, responsive visualizations by default. Encoding/decoding toggles in separate menu (not visible during normal use).

**Architecture:**
- **Active Workspace (Default):** High-fidelity rendering (LOD system, antialiasing, lighting)
- **Generation Menu:** Same rendering, with generator algorithm parameters visible
- **Compression Inspector (Hidden):** Toggle-able debug overlay showing Unicode compression state

**Result:** Professional UX for normal use; encoding details available for advanced users/export.

---

## 1. Rendering Architecture: Three Layers

### 1.1 Layer 1: Live Viewport (Default)

```
┌─────────────────────────────────────────┐
│          POLYFORM WORKSPACE             │
│                                         │
│     [Beautifully rendered polyforms]    │
│     - Smooth shading (Phong/PBR)       │
│     - Antialiased edges                 │
│     - Soft shadows                      │
│     - Clean typography overlay          │
│                                         │
│     [Interaction hints]                 │
│     - Hover: "Drag to move"            │
│     - Right-click: "Build off..."      │
│                                         │
└─────────────────────────────────────────┘
      ↓
   User sees: 3D scene, not compression details
   Update rate: 60 FPS
   Antialiasing: MSAA 4x (native browser support)
```

**Rendering path:**
```python
# viewport_renderer.py

class HighFidelityRenderer:
    """
    Renders polyforms with professional aesthetics.
    Encoding happens separately (not visible to user).
    """
    
    def __init__(self, canvas_element):
        self.scene = THREE.Scene()
        self.camera = THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight)
        self.renderer = THREE.WebGLRenderer(
            antialias=True,
            alpha=True,
            preserveDrawingBuffer=True
        )
        self.renderer.setSize(window.innerWidth, window.innerHeight)
        self.renderer.shadowMap.enabled = True
        
        # Lighting (professional appearance)
        self.setup_lights()
    
    def setup_lights(self):
        """Three-point lighting for professional look."""
        # Key light (main)
        key_light = THREE.DirectionalLight(0xFFFFFF, 1.0)
        key_light.position.set(5, 10, 5)
        key_light.castShadow = True
        self.scene.add(key_light)
        
        # Fill light (soften shadows)
        fill_light = THREE.DirectionalLight(0xCCCCFF, 0.5)
        fill_light.position.set(-5, 5, -5)
        self.scene.add(fill_light)
        
        # Rim light (edge separation)
        rim_light = THREE.DirectionalLight(0xFFFFCC, 0.3)
        rim_light.position.set(0, 10, -10)
        self.scene.add(rim_light)
        
        # Ambient (global illumination approximation)
        ambient = THREE.AmbientLight(0xFFFFFF, 0.4)
        self.scene.add(ambient)
    
    def render_textured_polyform(self, textured_polyform, position):
        """
        Render with high fidelity.
        
        textured_polyform: TexturedPolyform instance (Ω₅₀Ἰ₁Ρ₃)
        position: (x, y, z) placement
        """
        # Decompress geometry (O(1))
        mesh_data = textured_polyform.get_geometry()
        
        # Decompress textures (O(1))
        edge_textures = textured_polyform.get_edge_pixels()
        
        # Generate texture atlas procedurally (but cache it)
        if not hasattr(textured_polyform, '_texture_atlas'):
            texture_atlas = self._generate_texture_atlas(edge_textures)
            textured_polyform._texture_atlas = texture_atlas
        else:
            texture_atlas = textured_polyform._texture_atlas
        
        # Create THREE.js mesh
        geometry = self._mesh_data_to_three_geometry(mesh_data)
        material = THREE.MeshPhongMaterial({
            map: texture_atlas,
            side: THREE.DoubleSide,
            flatShading: False,  # Smooth shading
            shadowMap: True
        })
        mesh = THREE.Mesh(geometry, material)
        mesh.position.set(*position)
        mesh.castShadow = True
        mesh.receiveShadow = True
        
        self.scene.add(mesh)
        return mesh
    
    def render_frame(self):
        """Called every frame by requestAnimationFrame."""
        self.renderer.render(self.scene, self.camera)
```

**User experience:** Crystal clear 3D scene, no encoding artifacts visible.

---

### 1.2 Layer 2: Generation Menu (Sidebar)

```
┌──────────────────────┐
│ GENERATION CONTROLS  │
├──────────────────────┤
│ Mode:                │
│ ◉ Architecture       │
│ ○ Generation         │
├──────────────────────┤
│ Pattern:             │
│ [Dropdown: Explore]  │
├──────────────────────┤
│ Scale Geometry:      │
│ [5 options shown]    │
├──────────────────────┤
│ Symmetry:            │
│ ◉ Yes  ○ No          │
├──────────────────────┤
│ [Generate]           │
│ [Save Assembly]      │
└──────────────────────┘
      ↓
Same rendering engine as Layer 1
No encoding UI visible
```

**Code structure:**
```python
# generation_menu.py

class GenerationMenuPanel:
    """
    Sidebar control panel for generation/architecture modes.
    Rendering remains high-fidelity; menu just controls parameters.
    """
    
    def __init__(self):
        self.mode = 'architecture'  # or 'generation'
        self.current_pattern = 'explore'
        self.symmetry_enabled = True
        self.ui_elements = {}
    
    def on_generate_clicked(self):
        """User clicks Generate button."""
        if self.mode == 'generation':
            pattern = self.current_pattern
            workspace = get_active_workspace()
            
            # Generate using existing patterns
            new_polyforms = workspace.apply_generator_pattern(pattern)
            
            # Render to viewport (same HighFidelityRenderer)
            for pf in new_polyforms:
                workspace.renderer.render_textured_polyform(
                    pf, 
                    position=pf.position
                )
            
            workspace.update_library_item_count()
    
    def on_pattern_changed(self, new_pattern):
        """User selects different pattern."""
        self.current_pattern = new_pattern
        workspace = get_active_workspace()
        
        # Preview in real-time (if enabled)
        workspace.show_generator_preview(new_pattern)
```

---

### 1.3 Layer 3: Compression Inspector (Hidden)

```
┌─────────────────────────────────────┐
│ [⚙] Debug Menu                      │
├─────────────────────────────────────┤
│ ☐ Show Compression Info             │
│ ☐ Show Unicode Overlay              │
│ ☐ Show Edge Pixels (9×9 grid)      │
│ ☐ Show Symmetry Axes               │
│ ☐ Show Storage Stats               │
├─────────────────────────────────────┤
│ [Export as Unicode String]          │
│ [Import from Unicode]               │
│ [Clear Cache]                       │
└─────────────────────────────────────┘
      ↓
When enabled: Show Unicode string in corner
Show per-edge color/pattern breakdown
Show memory usage for current assembly
```

**Code structure:**
```python
# compression_inspector.py

class CompressionInspector:
    """
    Debug/advanced panel (hidden by default).
    Toggle-able via menu.
    """
    
    def __init__(self):
        self.visible = False
        self.show_unicode = False
        self.show_edge_pixels = False
        self.show_symmetry = False
        self.show_stats = False
    
    def toggle_visibility(self):
        """Keyboard shortcut or menu click: Ctrl+Shift+C"""
        self.visible = not self.visible
        if self.visible:
            self.render_overlay()
        else:
            self.hide_overlay()
    
    def render_overlay(self):
        """Render debug info on top of viewport."""
        workspace = get_active_workspace()
        selected_polyform = workspace.get_selected_polyform()
        
        if not selected_polyform:
            return
        
        # Display Unicode representation
        if self.show_unicode:
            unicode_str = selected_polyform.to_compact_string()
            self.display_text(f"Unicode: {unicode_str}")
            self.display_text(f"Size: {len(unicode_str)} bytes")
        
        # Display edge pixels as 9×9 grid
        if self.show_edge_pixels:
            edge_pixels = selected_polyform.get_edge_pixels()
            self.visualize_edge_pixels(edge_pixels)
        
        # Display symmetry axes
        if self.show_symmetry:
            geometry = selected_polyform.get_geometry()
            symmetry = geometry.symmetry_group
            self.draw_symmetry_axes(geometry)
        
        # Display storage stats
        if self.show_stats:
            stats = self.compute_stats(workspace)
            self.display_stats(stats)
    
    def compute_stats(self, workspace):
        """Calculate compression statistics for workspace."""
        polyforms = workspace.get_all_polyforms()
        
        naive_size = sum(pf.get_naive_size() for pf in polyforms)
        compressed_size = sum(len(pf.to_compact_string()) for pf in polyforms)
        
        return {
            'num_polyforms': len(polyforms),
            'naive_size_mb': naive_size / 1e6,
            'compressed_size_kb': compressed_size / 1e3,
            'compression_ratio': naive_size / max(compressed_size, 1),
            'cache_memory_mb': self._get_cache_size() / 1e6
        }
    
    def display_stats(self, stats):
        """Show stats in corner overlay."""
        overlay_text = f"""
        Polyforms: {stats['num_polyforms']}
        Naive: {stats['naive_size_mb']:.1f} MB
        Compressed: {stats['compressed_size_kb']:.1f} KB
        Ratio: {stats['compression_ratio']:.0f}:1
        Cache: {stats['cache_memory_mb']:.1f} MB
        """
        self.display_text(overlay_text, position='bottom-right')
```

**User experience:** Hidden by default. Power users can toggle via Ctrl+Shift+C to inspect compression details.

---

## 2. UI Layout: Separation of Concerns

### 2.1 Main Viewport (85% of screen)

```
┌───────────────────────────────────────────────────────┐
│                                                       │
│          [HIGH-FIDELITY 3D WORKSPACE]                │
│                                                       │
│          Beautiful rendered polyforms                │
│          Professional lighting & antialiasing        │
│          Smooth interactions (60 FPS)               │
│                                                       │
│          [Subtle UI hints on hover]                 │
│          - "Drag to move"                           │
│          - "Right-click: Build off..."              │
│          - Selection glow (soft)                    │
│                                                       │
└───────────────────────────────────────────────────────┘
```

### 2.2 Left Sidebar: Library (10% of screen)

```
┌──────────────────────┐
│ POLYFORM LIBRARY     │
├──────────────────────┤
│ [Search box]         │
│                      │
│ Platonic (5)         │
│  ☐ Tetrahedron      │
│  ☐ Cube             │
│  ☐ Octahedron       │
│  ☐ Dodecahedron     │
│  ☐ Icosahedron      │
│                      │
│ Archimedean (13)     │
│  ☐ Cuboctahedron    │
│  ☐ Snub cube        │
│  ... (collapsed)     │
│                      │
│ User (47)            │
│  ☐ My Assembly 1    │
│  ☐ My Assembly 2    │
│  ... (collapsed)     │
│                      │
│ [+ New Custom]       │
└──────────────────────┘
   ↓
 Click to drag into workspace
 Right-click for context menu
```

**Key:** No encoding UI here—just clean list of polyforms.

### 2.3 Right Sidebar: Controls (5% of screen)

```
┌────────────────────┐
│ CONTROLS           │
├────────────────────┤
│ MODE:              │
│ ◉ Architecture     │
│ ○ Generation       │
│                    │
│ [⚙ Debug Menu ▼]   │
│ [≡ Edit Menu ▼]    │
│ [File ▼]           │
│                    │
│ GENERATION:        │ (hidden if mode=Architecture)
│ Pattern:           │
│ [Dropdown]         │
│ Symmetry: ☑        │
│ Scale: [slider]    │
│                    │
│ [Generate]         │
│ [Cancel]           │
└────────────────────┘
```

**Key:** Generation params appear only when in Generation mode.

---

## 3. Encoding/Decoding: Decoupled from Visualization

### 3.1 Encoding Pipeline (Background, Async)

```python
# encoding_pipeline.py

class EncodingService:
    """
    Runs in background thread (web worker or async).
    Never blocks main render thread.
    """
    
    def encode_workspace_assembly(self, assembly, callback):
        """
        Encode assembly to Unicode string asynchronously.
        
        assembly: List of TexturedPolyform instances
        callback: Called when complete (unicode_str) => {}
        """
        # This runs in background
        async def _encode():
            # Step 1: Compress each polyform
            compressed_items = []
            for polyform in assembly:
                compressed = polyform.to_compact_string()  # O(1)
                compressed_items.append(compressed)
            
            # Step 2: Combine into assembly descriptor
            assembly_string = "Ψ" + "".join(compressed_items)
            
            # Step 3: Callback to main thread
            callback(assembly_string)
        
        # Schedule async task
        asyncio.create_task(_encode())
    
    def decode_unicode_string(self, unicode_str, callback):
        """
        Decode Unicode string asynchronously.
        
        unicode_str: "Ω₅₀Ἰ₁Ρ₃..."
        callback: Called when complete ([TexturedPolyform, ...]) => {}
        """
        async def _decode():
            polyforms = []
            
            # Parse unicode string
            i = 0
            while i < len(unicode_str):
                if unicode_str[i] in ['Ω', 'Ψ', 'Φ', 'Ξ']:
                    # Extract polyform symbol sequence
                    geometry_sym = unicode_str[i]
                    texture_sym = unicode_str[i+1] if i+1 < len(unicode_str) else None
                    palette_sym = unicode_str[i+2] if i+2 < len(unicode_str) else None
                    
                    polyform = TexturedPolyform(geometry_sym, texture_sym, palette_sym)
                    polyforms.append(polyform)
                    i += 3
                else:
                    i += 1
            
            # Callback
            callback(polyforms)
        
        asyncio.create_task(_decode())
```

**Key:** Encoding/decoding happens in background. Main render thread is never blocked.

### 3.2 Export/Import UI (Menu-driven)

```python
# file_menu.py

class FileMenuPanel:
    """
    File → Export/Import
    Encoding UI hidden from normal view
    """
    
    def export_assembly(self):
        """
        File → Export as Unicode String
        Opens modal with copy-to-clipboard button
        """
        workspace = get_active_workspace()
        assembly = workspace.get_all_polyforms()
        
        # Encode in background
        EncodingService.encode_workspace_assembly(
            assembly,
            callback=self._show_export_modal
        )
    
    def _show_export_modal(self, unicode_str):
        """Show export dialog."""
        modal = Modal(title="Export Assembly")
        modal.add_textarea(unicode_str, readonly=True)
        modal.add_button("Copy to Clipboard", onclick=lambda: clipboard.copy(unicode_str))
        modal.add_button("Download as .txt", onclick=lambda: download(unicode_str, "assembly.txt"))
        modal.show()
    
    def import_assembly(self):
        """
        File → Import from Unicode String
        Opens modal with paste field
        """
        modal = Modal(title="Import Assembly")
        textarea = modal.add_textarea(placeholder="Paste Unicode string here...")
        
        def on_import():
            unicode_str = textarea.value()
            workspace = get_active_workspace()
            
            # Decode in background
            EncodingService.decode_unicode_string(
                unicode_str,
                callback=lambda polyforms: workspace.load_polyforms(polyforms)
            )
        
        modal.add_button("Import", onclick=on_import)
        modal.show()
```

**User experience:**
- Normal use: Never see compression UI
- Export: Click menu → Copy Unicode string
- Import: Click menu → Paste Unicode string → Load

---

## 4. Workspace Architecture: Data Model

### 4.1 Workspace State (Decoupled from Rendering)

```python
# workspace.py

class Workspace:
    """
    Core workspace state (geometry, polyforms, assemblies).
    Separate from rendering.
    """
    
    def __init__(self):
        self.polyforms = []  # List of TexturedPolyform
        self.selected_polyform = None
        self.camera_position = (0, 0, 10)
        self.lighting_config = {}
        
        # Rendering engine (separate concern)
        self.renderer = HighFidelityRenderer(canvas_id='viewport')
        
        # Encoding service (background)
        self.encoder = EncodingService()
        
        # Inspector (debug overlay)
        self.inspector = CompressionInspector()
    
    def add_polyform(self, polyform, position):
        """Add to workspace and render."""
        self.polyforms.append(polyform)
        self.renderer.render_textured_polyform(polyform, position)
    
    def select_polyform(self, polyform):
        """Select and highlight."""
        self.selected_polyform = polyform
        self.renderer.highlight_mesh(polyform)
        
        # Update inspector if visible
        if self.inspector.visible:
            self.inspector.render_overlay()
    
    def apply_generator_pattern(self, pattern_name, reference_polyform):
        """Generate new polyforms from pattern."""
        if pattern_name == 'explore':
            new_polyforms = GeneratorEngine.explore(reference_polyform)
        elif pattern_name == 'radial':
            new_polyforms = GeneratorEngine.radial(reference_polyform, n=12)
        elif pattern_name == 'linear':
            new_polyforms = GeneratorEngine.linear(reference_polyform, count=5)
        # ... other patterns
        
        # Add to workspace (triggers rendering)
        for pf in new_polyforms:
            self.add_polyform(pf, position=pf.position)
        
        return new_polyforms
    
    def export_as_unicode(self, callback):
        """Export workspace assembly."""
        self.encoder.encode_workspace_assembly(self.polyforms, callback)
    
    def import_from_unicode(self, unicode_str, callback):
        """Import workspace assembly."""
        self.encoder.decode_unicode_string(unicode_str, callback)
```

---

## 5. Event Flow: User Interactions

### 5.1 Drag Polyform into Workspace

```
USER ACTION: Drag "Cube" from library onto viewport

EVENT FLOW:
  1. Drag start: libraryPanel.on_drag_start('cube')
     → Store: drag_source = 'cube'
  
  2. Mouse move over viewport: viewportRenderer.on_drag_over()
     → Show ghost preview of cube at cursor
  
  3. Drop on viewport: viewportRenderer.on_drop(position)
     → Create TexturedPolyform('cube')
     → workspace.add_polyform(polyform, position)
     → workspace.renderer.render_textured_polyform()
  
  4. Rendering: HighFidelityRenderer.render_frame()
     → Beautiful cube appears with lighting & shadows
  
  5. Encoding (background): No visible change
     → If inspector open, shows: "Ω₂₀Ἰ₁Ρ₁" (small text in corner)

RESULT: User sees smooth drag-and-drop; encoding invisible
```

### 5.2 Right-Click → Build off Shape

```
USER ACTION: Right-click selected cube

EVENT FLOW:
  1. Context menu appears (nearby)
     [Build off this shape ▶]
     [Duplicate]
     [Edit texture]
     [Delete]
  
  2. User hovers "Build off this shape"
     → Submenu appears:
        [Scale 0.5x]
        [Scale 1.0x]
        [Scale 1.5x]
        [Scale 2.0x]
        [Scale 3.0x]
  
  3. User clicks "Scale 1.5x"
     → GeneratorEngine.scale_and_attach(reference_cube, 1.5)
     → Returns new textured polyform (scaled)
     → workspace.add_polyform(scaled_pf, snap_position)
     → Renderer shows snap animation (face-to-face connection)
  
  4. Encoding (background):
     → Assembly updated: "Ψ₁Ω₂₀Ἰ₁Ω₂₀Ἰ₂" (assembly of 2 cubes, different textures)
     → Storage: 8 bytes (vs. 100+ KB naive)

RESULT: Smooth interaction; compression happens silently
```

### 5.3 Toggle Debug Inspector

```
USER ACTION: Press Ctrl+Shift+C

EVENT FLOW:
  1. CompressionInspector.toggle_visibility()
     → inspector.visible = True
  
  2. Render debug overlay (in corner):
     ────────────────────────
     Unicode: Ω₂₀Ἰ₁Ρ₁
     Size: 3 bytes
     
     Edge colors (9×9):
     [R] [O] [Y] [Y] [O] [O] [Y] [O] [O]
     [O] [Y] [Y] [R] [O] [Y] [O] [Y] [Y]
     [Y] [O] [R] [O] [Y] [O] [O] [R] [O]
     ... (pattern visible)
     
     Geometry: Cube (12 edges, O symmetry)
     ────────────────────────
  
  3. Normal rendering unaffected
     → Main viewport still beautiful and smooth
     → Encoding info just in corner (non-intrusive)
  
  4. Press Ctrl+Shift+C again
     → Toggle off; overlay disappears
     → Back to normal professional view

RESULT: Debug info available without cluttering main UI
```

---

## 6. Implementation Phases

### Phase 1: Separate Rendering from Encoding (Week 1)

- [ ] Create HighFidelityRenderer class (THREE.js wrapper)
- [ ] Implement 3-point lighting + antialiasing
- [ ] Decouple from TexturedPolyform encoding logic
- [ ] Test: Render 10+ polyforms at 60 FPS

### Phase 2: Layout & UI Structure (Week 2)

- [ ] Implement main viewport layout (85% center)
- [ ] Implement sidebar library (10% left)
- [ ] Implement control panel (5% right)
- [ ] No encoding UI visible by default

### Phase 3: Encoding Pipeline (Background) (Week 2)

- [ ] Create EncodingService (async, non-blocking)
- [ ] Implement encode_workspace_assembly()
- [ ] Implement decode_unicode_string()
- [ ] Test: Import/export without frame drops

### Phase 4: Debug Inspector (Week 3)

- [ ] Create CompressionInspector class
- [ ] Implement toggle (Ctrl+Shift+C)
- [ ] Show Unicode string in corner (when enabled)
- [ ] Show edge pixels as 9×9 grid
- [ ] Show storage stats

### Phase 5: File Menu (Import/Export) (Week 3)

- [ ] File → Export as Unicode String (modal with copy)
- [ ] File → Import from Unicode String (modal with paste)
- [ ] Test: Round-trip (export → import → identical workspace)

### Phase 6: Polish & Optimization (Week 4)

- [ ] Profile rendering pipeline
- [ ] Optimize THREE.js scene graph
- [ ] GPU caching for texture atlases
- [ ] Smooth animations for placements

---

## 7. Design Principles

### 7.1 User-Facing Constraints

✓ **Clean viewport:** No encoding UI visible during normal use  
✓ **Responsive:** 60 FPS interactions (drag, rotate, zoom)  
✓ **Professional:** High-fidelity lighting and antialiasing  
✓ **Intuitive:** Right-click menus, drag-and-drop  
✓ **Non-intrusive:** Debug inspector hidden by default  

### 7.2 Developer-Friendly

✓ **Modular:** Separate rendering, encoding, UI concerns  
✓ **Testable:** Workspace state independent of rendering  
✓ **Extensible:** Easy to add new generators, materials, patterns  
✓ **Debuggable:** Inspector available for compression inspection  

### 7.3 Performance Targets

| Action | Target FPS | Max Frame Time |
|--------|-----------|----------------|
| Viewport pan/rotate | 60 | 16 ms |
| Drag polyform | 60 | 16 ms |
| Add polyform | 60 | 16 ms |
| Switch mode | 30+ | 30 ms |
| Show inspector | 60 | 16 ms (overlay doesn't block) |

---

## 8. Conclusion

**Key separation:**

1. **Visualization layer** (HighFidelityRenderer) → Beautiful, responsive, no encoding visible
2. **UI/Control layer** (Sidebar + Generator menu) → Clean, focused on interaction
3. **Encoding layer** (EncodingService) → Background, async, never blocks rendering
4. **Debug layer** (CompressionInspector) → Hidden by default, Ctrl+Shift+C to toggle

**Result:** Users enjoy professional experience; advanced features available without cluttering UI.

---

**End of UI/UX Architecture Document**
