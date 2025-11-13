# Polyform Color Visualization & Image Compression Suite
## Hierarchical Color Mapping + Separated Image Toolset

**Status:** Architecture Definition  
**Date:** 2025-11-08  
**Focus:** Semantic color assignment via primitive pairs, hue scaler controls, and independent image codec UI

---

## Executive Summary

**Color System:**
- Base unit: Primitive pair (e.g., Triangle-Square, Triangle-Triangle)
- Each pair maps to hue on adjustable color wheel
- User drags hue scaler to reorganize which pairs map to which colors
- Composed polyforms inherit color from dominant constituent primitive pair
- Hue shift factor encodes size/order (saturation or brightness modulation)

**Image Codec:**
- Separate pop-out window (never interferes with workspace)
- Import image → compress to Unicode string
- Import Unicode string → decompress to image
- Lossless compression with 9×9 edge-pixel model

**Result:** Visually appealing workspace with semantic coloring; professional image compression tool always available.

---

## 1. Color Visualization System

### 1.1 Primitive Pair Foundation

```
Primitive symbols (18 total):
  A = Triangle (3-gon)
  B = Square (4-gon)
  C = Pentagon (5-gon)
  D = Hexagon (6-gon)
  ... (up to R = 20-gon)

All possible primitive pairs (AA, AB, AC, ..., RR):
  Total combinations: 18 × 18 = 324 unique pairs
  
  Common pairs (first used):
    AA = Triangle-Triangle
    AB = Triangle-Square
    AC = Triangle-Pentagon
    BB = Square-Square
    BC = Square-Pentagon
    ...
    RR = 20-gon to 20-gon
```

### 1.2 Hue Chart: Visual Color Assignment

```
┌─────────────────────────────────────────────┐
│        PRIMITIVE PAIR → HUE MAPPING        │
├─────────────────────────────────────────────┤
│                                             │
│  0°        90°       180°      270°    360° │
│  Red  Yellow  Green  Cyan  Blue Purple Red  │
│  |—————|—————|—————|—————|—————|—————|    │
│                                             │
│  [Slider for A-A pair]      ██ 45°         │
│  [Slider for A-B pair]        ██ 60°       │
│  [Slider for A-C pair]          ██ 75°    │
│  [Slider for B-B pair]            ██ 90°  │
│  [Slider for B-C pair]              ██ 105°│
│  ...                                       │
│                                             │
│  Saturation: [████████░░] 80%             │
│  Brightness: [█████████░] 90%             │
│                                             │
│  Preview:                                  │
│  ██ Triangle-Triangle (Red)               │
│  ██ Triangle-Square (Orange)              │
│  ██ Square-Square (Yellow)                │
│  ██ Square-Pentagon (Green)               │
│  ...                                       │
│                                             │
│  [Reset to Default]  [Save Preset]        │
└─────────────────────────────────────────────┘
```

**User interaction:**
- Drag slider for each pair to adjust hue position (0–360°)
- Adjust global saturation/brightness
- Real-time preview in workspace
- Save/load custom color schemes

### 1.3 Color Inheritance: Pair → Cluster → Assembly

```
Example: Octahedron (8 triangles, primitive: A)

LEVEL 1: Primitive pair analysis
  Octahedron composition: AAAAAAAA (all triangles)
  Primary pair: A-A (Triangle-Triangle)
  From hue chart: A-A = 45° (Red hue)
  → Base color: Red

LEVEL 2: Cluster formation
  Cluster inherits color from its dominant primitive pair
  If cluster is A⁶B² (6 triangles + 2 squares):
    Primary pair: A-B
    Secondary pair: A-A, B-B (less frequent)
    From hue chart: A-B = 60° (Orange hue)
    → Cluster color: Orange

LEVEL 3: Assembly/mega-structure
  Multiple clusters combine
  Tetrahedra + Cube assembled:
    Tetrahedron (4 triangles): Primary A-A = Red
    Cube (6 squares): Primary B-B = Yellow
    Assembly contains: 4A + 6B
    Dominant pair: B-B (more polygons)
    → Assembly color: Yellow (toward dominant)
    OR: Blend Red + Yellow = Orange (if mixed display mode)

SIZE MODIFIER: Hue shift by constituent order
  Formula: final_hue = base_hue + (order_delta × hue_shift_factor)
  
  Example:
    Small cluster (2 triangles): base_hue = 45°
    Medium cluster (8 triangles): hue = 45° + (2 × 5°) = 55°
    Large cluster (20 triangles): hue = 45° + (5 × 5°) = 70°
    
    Visual effect: Larger polyforms appear slightly different hue
    Conveys size/complexity at a glance
```

### 1.4 Hue Shift Factor: Encoding Polyform Order

```
Hue shift modulation (saturation or brightness shift):

base_hue = 45°  (from hue chart for pair A-A)
size_factor = polygon_count / 10  (normalized size)
hue_shift = 10° × size_factor     (example: max 10° shift)

final_hue = base_hue + hue_shift

Small polyform (2 polygons):
  size_factor = 0.2
  hue_shift = 2°
  final_hue = 47° (subtle shift toward yellow)
  color = (R, G, B) at 47° on color wheel

Medium polyform (10 polygons):
  size_factor = 1.0
  hue_shift = 10°
  final_hue = 55° (more noticeable shift)
  color = (R, G, B) at 55°

Large polyform (50 polygons):
  size_factor = 5.0
  hue_shift = 50° (capped at max)
  final_hue = 95° (significant shift, now greenish)
  color = (R, G, B) at 95°

VISUAL RESULT:
  Small shapes: Vivid, pure colors (base hues)
  Medium shapes: Slight hue variation (indicates size)
  Large shapes: Distinct hue shift (clearly larger structures)
```

---

## 2. Color System Architecture

### 2.1 Data Model

```python
# color_system.py

class PrimitiveColorScheme:
    """
    Maps primitive pairs to hues with adjustable scaler.
    """
    
    def __init__(self):
        # Hue chart: pair_key → hue_degree (0-360)
        self.pair_hue_map = {
            'AA': 0,      # Triangle-Triangle → Red
            'AB': 30,     # Triangle-Square → Orange
            'AC': 60,     # Triangle-Pentagon → Yellow
            'AD': 90,     # Triangle-Hexagon → Green
            'BB': 120,    # Square-Square → Cyan
            'BC': 150,    # Square-Pentagon → Blue
            'BD': 180,    # Square-Hexagon → Purple
            'CC': 210,    # Pentagon-Pentagon → Pink
            'CD': 240,    # Pentagon-Hexagon → Red-ish
            'DD': 270,    # Hexagon-Hexagon → Deep Purple
            # ... (continue for all 324 pairs)
        }
        
        # Saturation/brightness modifiers
        self.saturation = 0.85  # 0-1
        self.brightness = 0.90  # 0-1
        self.hue_shift_factor = 10.0  # degrees per size unit
    
    def get_primitive_pair(self, poly1, poly2):
        """Extract primitive pair (A-A, A-B, etc.) from polygons."""
        # Normalize pair (always lower symbol first for consistency)
        symbols = sorted([poly1.symbol, poly2.symbol])
        return "".join(symbols)
    
    def get_color_for_pair(self, pair_key):
        """
        Get RGB color for primitive pair from hue chart.
        
        pair_key: 'AA', 'AB', 'AC', etc.
        Returns: (R, G, B) tuple in [0, 1] range
        """
        if pair_key not in self.pair_hue_map:
            # Default gray for unknown pairs
            return (0.5, 0.5, 0.5)
        
        hue = self.pair_hue_map[pair_key]
        return self._hsb_to_rgb(hue, self.saturation, self.brightness)
    
    def get_color_for_polyform(self, polyform):
        """
        Get color for polyform based on constituent primitives.
        
        Algorithm:
          1. Decompose to primitive pairs
          2. Find dominant pair (most frequent)
          3. Get base hue from chart
          4. Apply hue shift based on polyform size
          5. Return RGB color
        """
        # Decompose polyform to primitives
        primitive_pairs = polyform.get_primitive_pairs()
        
        # Find dominant pair (most frequent)
        dominant_pair = max(primitive_pairs, key=lambda p: len(primitive_pairs[p]))
        base_hue = self.pair_hue_map.get(dominant_pair, 0)
        
        # Apply hue shift based on size
        polygon_count = polyform.polygon_count
        size_factor = polygon_count / 10.0  # Normalize
        hue_shift = self.hue_shift_factor * min(size_factor, 5.0)  # Cap at 5x
        
        final_hue = (base_hue + hue_shift) % 360  # Wrap around
        
        # Convert to RGB
        return self._hsb_to_rgb(final_hue, self.saturation, self.brightness)
    
    def _hsb_to_rgb(self, hue, saturation, brightness):
        """
        Convert HSB (Hue, Saturation, Brightness) to RGB.
        
        hue: 0-360 degrees
        saturation, brightness: 0-1
        Returns: (R, G, B) in [0, 1]
        """
        import colorsys
        return colorsys.hsv_to_rgb(hue / 360.0, saturation, brightness)
    
    def set_pair_hue(self, pair_key, hue_degree):
        """User adjusts hue for pair (via slider)."""
        if pair_key in self.pair_hue_map:
            self.pair_hue_map[pair_key] = hue_degree % 360
            # Trigger viewport re-render
            get_workspace().request_redraw()
    
    def set_saturation(self, value):
        """User adjusts global saturation."""
        self.saturation = max(0, min(1, value))
        get_workspace().request_redraw()
    
    def set_brightness(self, value):
        """User adjusts global brightness."""
        self.brightness = max(0, min(1, value))
        get_workspace().request_redraw()
    
    def set_hue_shift_factor(self, degrees):
        """User adjusts hue shift per size unit."""
        self.hue_shift_factor = degrees
        get_workspace().request_redraw()
    
    def save_preset(self, preset_name):
        """Save current scheme as preset."""
        preset = {
            'name': preset_name,
            'pair_hue_map': self.pair_hue_map.copy(),
            'saturation': self.saturation,
            'brightness': self.brightness,
            'hue_shift_factor': self.hue_shift_factor
        }
        # Store in localStorage or file
        save_to_storage('color_presets', preset_name, preset)
    
    def load_preset(self, preset_name):
        """Load saved color preset."""
        preset = load_from_storage('color_presets', preset_name)
        if preset:
            self.pair_hue_map = preset['pair_hue_map']
            self.saturation = preset['saturation']
            self.brightness = preset['brightness']
            self.hue_shift_factor = preset['hue_shift_factor']
            get_workspace().request_redraw()
    
    def reset_to_default(self):
        """Reset to default color scheme."""
        self.__init__()  # Reinitialize
        get_workspace().request_redraw()
```

### 2.2 Rendering Integration

```python
# high_fidelity_renderer.py (updated)

class HighFidelityRenderer:
    """
    Render polyforms with colors from PrimitiveColorScheme.
    """
    
    def __init__(self, canvas_element, color_scheme=None):
        self.scene = THREE.Scene()
        self.color_scheme = color_scheme or PrimitiveColorScheme()
        # ... other initialization
    
    def render_textured_polyform(self, textured_polyform, position):
        """
        Render with color from scheme.
        If textured_polyform has image layer, use that.
        Otherwise, use semantic color from primitives.
        """
        mesh_data = textured_polyform.get_geometry()
        
        # Determine color source
        if textured_polyform.has_image_texture():
            # Use image texture
            material = THREE.MeshPhongMaterial({
                'map': textured_polyform.get_texture_atlas(),
                'side': THREE.DoubleSide
            })
        else:
            # Use semantic color from primitives
            rgb_color = self.color_scheme.get_color_for_polyform(
                textured_polyform.get_geometry()
            )
            material = THREE.MeshPhongMaterial({
                'color': THREE.Color(*rgb_color),
                'side': THREE.DoubleSide,
                'flatShading': False
            })
        
        # Create mesh
        geometry = self._mesh_data_to_three_geometry(mesh_data)
        mesh = THREE.Mesh(geometry, material)
        mesh.position.set(*position)
        mesh.castShadow = True
        mesh.receiveShadow = True
        
        self.scene.add(mesh)
        return mesh
```

---

## 3. Color Control UI Panel

### 3.1 Right Sidebar: Color Controls

```
┌────────────────────────────────────┐
│ COLOR & APPEARANCE                 │
├────────────────────────────────────┤
│ MODE:                              │
│ ◉ Semantic (Primitives)            │
│ ○ Image-based                      │
├────────────────────────────────────┤
│ PRIMITIVE PAIR HUES:               │
│                                    │
│ [Hue wheel visualization (2D)]     │
│           ██ 0° Red                │
│           ██ 30° Orange   [AA]     │
│           ██ 60° Yellow   [AB]     │
│           ██ 90° Green    [AC]     │
│                                    │
│ [Scrollable list of all pairs]     │
│                                    │
│ AA (Tri-Tri)  ─────●─────  45°    │
│ AB (Tri-Sq)   ────●────  30°       │
│ AC (Tri-Pent) ─────●───  60°       │
│ BB (Sq-Sq)    ──●──────  10°       │
│ ...                                │
│                                    │
│ Global Controls:                   │
│ Saturation  ─────●───── 80%       │
│ Brightness  ──────●──── 90%       │
│ Hue Shift   ────●───── 10°/size   │
│                                    │
│ [Reset to Default]  [Save Preset]  │
│ [Load Preset ▼]                    │
│                                    │
│ Size Encoding:                     │
│ ☑ Hue shifts with size             │
│ ☑ Brightness encodes order         │
│ ☑ Saturation for stability        │
│                                    │
└────────────────────────────────────┘
```

### 3.2 Hue Wheel Visualization

```python
# color_ui_panel.py

class ColorUIPanel:
    """
    UI for color scheme adjustment.
    """
    
    def __init__(self, workspace):
        self.workspace = workspace
        self.color_scheme = workspace.color_scheme
        self.ui_elements = {}
    
    def render_hue_wheel(self):
        """
        Interactive HSB color wheel visualization.
        User clicks/drags to set hues for pairs.
        """
        canvas = create_canvas(300, 300)  # 2D canvas for wheel
        ctx = canvas.getContext('2d')
        
        # Draw color wheel (HSV gradient)
        center_x, center_y = 150, 150
        radius = 140
        
        for angle in range(0, 360, 5):  # 5° increments
            hue_rad = angle * Math.PI / 180
            
            # Draw wedge
            ctx.fillStyle = f'hsl({angle}, {self.color_scheme.saturation*100}%, {self.color_scheme.brightness*100}%)'
            ctx.beginPath()
            ctx.arc(center_x, center_y, radius, hue_rad, hue_rad + 0.087)  # 5° wedge
            ctx.fill()
        
        # Draw indicators for each pair's current hue
        for pair_key, hue_degree in self.color_scheme.pair_hue_map.items():
            if pair_key not in ['AA', 'AB', 'AC', 'AD', 'BB', 'BC', 'BD', 'CC']:
                continue  # Skip rare pairs for clarity
            
            hue_rad = hue_degree * Math.PI / 180
            x = center_x + radius * Math.cos(hue_rad)
            y = center_y + radius * Math.sin(hue_rad)
            
            # Draw indicator dot
            ctx.fillStyle = '#FFFFFF'
            ctx.beginPath()
            ctx.arc(x, y, 8, 0, 2*Math.PI)
            ctx.fill()
            
            # Draw label
            label_r = radius - 20
            label_x = center_x + label_r * Math.cos(hue_rad)
            label_y = center_y + label_r * Math.sin(hue_rad)
            ctx.fillStyle = '#000000'
            ctx.font = 'bold 10px monospace'
            ctx.textAlign = 'center'
            ctx.fillText(pair_key, label_x, label_y)
        
        canvas.addEventListener('click', (e) => self._on_hue_wheel_click(e))
        return canvas
    
    def _on_hue_wheel_click(self, event):
        """Handle click on hue wheel."""
        canvas = event.target
        rect = canvas.getBoundingClientRect()
        
        # Get click position relative to center
        center_x, center_y = 150, 150
        click_x = event.clientX - rect.left - center_x
        click_y = event.clientY - rect.top - center_y
        
        # Calculate angle (0-360°)
        angle_rad = Math.atan2(click_y, click_x)
        angle_deg = (angle_rad * 180 / Math.PI + 360) % 360
        
        # Find which pair is closest to this angle
        closest_pair = None
        min_dist = 180
        for pair_key, hue_degree in self.color_scheme.pair_hue_map.items():
            dist = abs(hue_degree - angle_deg)
            if dist > 180:
                dist = 360 - dist
            if dist < min_dist:
                min_dist = dist
                closest_pair = pair_key
        
        # Update pair's hue
        if closest_pair and min_dist < 30:  # 30° snap radius
            self.color_scheme.set_pair_hue(closest_pair, angle_deg)
    
    def render_pair_sliders(self):
        """
        Sliders for each primitive pair to adjust hue.
        """
        container = create_div(class_='pair-sliders')
        
        common_pairs = ['AA', 'AB', 'AC', 'AD', 'BB', 'BC', 'BD', 'CC', 'CD', 'DD']
        
        for pair_key in common_pairs:
            row = create_div(class_='slider-row')
            
            # Label
            label = create_label(f"{pair_key} (Primitives)")
            row.append(label)
            
            # Slider
            slider = create_input(
                type='range',
                min=0, max=360, step=5,
                value=self.color_scheme.pair_hue_map[pair_key]
            )
            slider.addEventListener('input', (e) => 
                self.color_scheme.set_pair_hue(pair_key, int(e.target.value))
            )
            row.append(slider)
            
            # Hue readout + color preview
            hue_display = create_span(f"{self.color_scheme.pair_hue_map[pair_key]}°")
            row.append(hue_display)
            
            color_preview = create_div(
                style=f"background: hsl({self.color_scheme.pair_hue_map[pair_key]}, 85%, 90%)"
            )
            row.append(color_preview)
            
            container.append(row)
        
        return container
    
    def render_global_controls(self):
        """Saturation, brightness, hue-shift controls."""
        container = create_div(class_='global-controls')
        
        # Saturation
        sat_label = create_label("Saturation")
        sat_slider = create_input(
            type='range', min=0, max=100, step=5,
            value=self.color_scheme.saturation * 100
        )
        sat_slider.addEventListener('input', (e) =>
            self.color_scheme.set_saturation(int(e.target.value) / 100)
        )
        sat_display = create_span(f"{int(self.color_scheme.saturation * 100)}%")
        container.append(sat_label, sat_slider, sat_display)
        
        # Brightness
        bri_label = create_label("Brightness")
        bri_slider = create_input(
            type='range', min=0, max=100, step=5,
            value=self.color_scheme.brightness * 100
        )
        bri_slider.addEventListener('input', (e) =>
            self.color_scheme.set_brightness(int(e.target.value) / 100)
        )
        bri_display = create_span(f"{int(self.color_scheme.brightness * 100)}%")
        container.append(bri_label, bri_slider, bri_display)
        
        # Hue shift factor
        shift_label = create_label("Hue Shift (per size unit)")
        shift_slider = create_input(
            type='range', min=0, max=30, step=1,
            value=self.color_scheme.hue_shift_factor
        )
        shift_slider.addEventListener('input', (e) =>
            self.color_scheme.set_hue_shift_factor(int(e.target.value))
        )
        shift_display = create_span(f"{int(self.color_scheme.hue_shift_factor)}°")
        container.append(shift_label, shift_slider, shift_display)
        
        return container
```

---

## 4. Separated Image Compression Suite

### 4.1 Pop-Out Window: Always Separate

```
┌─────────────────────────────────────────────┐
│ POLYFORM IMAGE COMPRESSION SUITE            │
│                                   [×]       │
├─────────────────────────────────────────────┤
│                                             │
│ MODE:                                      │
│ ◉ Compress Image → Unicode                 │
│ ○ Decompress Unicode → Image               │
│                                             │
│ INPUT:                                     │
│ [📁 Select Image] or [Paste Unicode]       │
│                                             │
│ TARGET POLYFORM (Compress mode):           │
│ ◉ Auto-detect best fit                     │
│ ○ Manual: [Octahedron ▼]                   │
│                                             │
│ COMPRESSION OPTIONS:                       │
│ Color depth: [10-bit RGB ▼]                │
│ Pattern layer: ☑ Enabled                   │
│ Palette: ◉ Embedded  ○ Reference           │
│ Quality: [████████░░] 80%                  │
│                                             │
│ OUTPUT:                                    │
│ [────────────────────────────────────────] │
│ Ω₅₀Ἰ₁Ἰ₂Ἰ₃Ἰ₄Ἰ₅Ἰ₆Ἰ₇Ἰ₈Ρ₃                    │
│                                             │
│ Compression ratio: 12,860:1                │
│ Original size: 786 KB                      │
│ Compressed size: 61 bytes                  │
│                                             │
│ [Copy]  [Download]  [Process]              │
│                                             │
├─────────────────────────────────────────────┤
│ PREVIEW:                                    │
│                                             │
│  [Thumbnail of compressed result]           │
│                                             │
└─────────────────────────────────────────────┘
```

### 4.2 ImageCompressionSuite Class

```python
# image_compression_suite.py

class ImageCompressionSuite:
    """
    Standalone window for image ↔ Unicode compression.
    Never interferes with main workspace.
    """
    
    def __init__(self):
        self.window = create_floating_window(
            title='Polyform Image Compression Suite',
            width=500, height=700,
            position='right'  # Float on right side
        )
        self.mode = 'compress'  # or 'decompress'
        self.input_file = None
        self.input_unicode = None
        self.output_unicode = None
        self.output_image = None
        self.preview_canvas = None
        
        self._build_ui()
    
    def _build_ui(self):
        """Construct UI elements."""
        container = self.window.content_div
        
        # Mode selector
        mode_section = self._build_mode_selector()
        container.append(mode_section)
        
        # Input section
        input_section = self._build_input_section()
        container.append(input_section)
        
        # Options section
        options_section = self._build_options_section()
        container.append(options_section)
        
        # Output section
        output_section = self._build_output_section()
        container.append(output_section)
        
        # Preview section
        preview_section = self._build_preview_section()
        container.append(preview_section)
        
        # Action buttons
        buttons = self._build_action_buttons()
        container.append(buttons)
    
    def _build_input_section(self):
        """Input: file upload or Unicode paste."""
        section = create_div(class_='input-section')
        
        if self.mode == 'compress':
            # File upload
            label = create_label("Select Image to Compress")
            file_input = create_input(type='file', accept='image/*')
            file_input.addEventListener('change', self._on_image_selected)
            
            info = create_span("PNG, JPG, WebP supported")
            section.append(label, file_input, info)
        
        else:  # decompress
            # Unicode paste
            label = create_label("Paste Unicode String")
            textarea = create_textarea(
                placeholder='Ω₅₀Ἰ₁Ἰ₂...',
                rows=3
            )
            textarea.addEventListener('input', self._on_unicode_pasted)
            section.append(label, textarea)
        
        return section
    
    def _on_image_selected(self, event):
        """User selected image file."""
        file = event.target.files[0]
        if not file:
            return
        
        # Read file
        reader = FileReader()
        reader.onload = (e) => self._process_image(e.target.result)
        reader.readAsDataURL(file)
    
    def _process_image(self, image_data_url):
        """Convert image to polyform + compress."""
        img = Image()
        img.onload = () => {
            # Image → Polyform pipeline
            from image_processing_pipeline import image_to_polyform
            
            textured_polyform = image_to_polyform(
                img,
                target_geometry=self._get_selected_polyform() if hasattr(self, 'manual_polyform') else None
            )
            
            # Compress to Unicode
            self.output_unicode = textured_polyform.to_compact_string()
            
            # Show output
            self._display_output()
            self._show_preview(textured_polyform)
        }
        img.src = image_data_url
    
    def _on_unicode_pasted(self, event):
        """User pasted Unicode string."""
        unicode_str = event.target.value
        self.input_unicode = unicode_str
        
        # Decompress to image
        try:
            polyforms = decode_unicode_string(unicode_str)
            if polyforms:
                self.output_image = polyforms[0].render_to_image()
                self._display_output()
                self._show_preview(polyforms[0])
        except Exception as e:
            self._show_error(f"Invalid Unicode: {str(e)}")
    
    def _build_options_section(self):
        """Compression options."""
        section = create_div(class_='options-section')
        
        if self.mode == 'compress':
            # Polyform selection
            label1 = create_label("Target Polyform")
            auto_radio = create_radio('polyform', 'auto', True)
            auto_label = create_label("Auto-detect best fit")
            manual_radio = create_radio('polyform', 'manual', False)
            manual_label = create_label("Manual")
            polyform_select = create_select(
                options=['Octahedron', 'Cube', 'Dodecahedron', 'Icosahedron', ...],
                disabled=True
            )
            manual_radio.addEventListener('change', () => polyform_select.disabled = False)
            auto_radio.addEventListener('change', () => polyform_select.disabled = True)
            
            section.append(label1, auto_radio, auto_label, manual_radio, manual_label, polyform_select)
            
            # Color depth
            label2 = create_label("Color Depth")
            color_select = create_select(
                options=['8-bit (256 colors)', '10-bit RGB (512 colors)', '12-bit RGB (4096 colors)'],
                value='10-bit RGB (512 colors)'
            )
            section.append(label2, color_select)
            
            # Pattern layer
            pattern_checkbox = create_checkbox(label='Include pattern layer', checked=True)
            section.append(pattern_checkbox)
            
            # Quality slider
            label3 = create_label("Compression Quality")
            quality_slider = create_range_slider(min=50, max=100, value=80, step=5)
            quality_display = create_span("80%")
            quality_slider.addEventListener('input', (e) => {
                quality_display.textContent = f"{e.target.value}%"
            })
            section.append(label3, quality_slider, quality_display)
        
        return section
    
    def _build_output_section(self):
        """Output display."""
        section = create_div(class_='output-section')
        
        label = create_label("Compressed Output")
        output_textarea = create_textarea(
            placeholder='(Output will appear here)',
            readonly=True,
            rows=3
        )
        self.output_textarea = output_textarea
        
        # Stats
        stats_div = create_div(class_='stats')
        self.stats_display = create_span()
        stats_div.append(self.stats_display)
        
        section.append(label, output_textarea, stats_div)
        return section
    
    def _display_output(self):
        """Show compressed output and stats."""
        if self.mode == 'compress' and self.output_unicode:
            self.output_textarea.value = self.output_unicode
            
            # Calculate stats
            naive_size = 786000  # Approx 512×512 PNG RGB
            compressed_size = len(self.output_unicode)
            ratio = naive_size / max(compressed_size, 1)
            
            stats_text = f"""
            Original: ~{naive_size/1024:.0f} KB
            Compressed: {compressed_size} bytes
            Ratio: {ratio:.0f}:1
            """
            self.stats_display.textContent = stats_text
    
    def _show_preview(self, textured_polyform):
        """Render preview in canvas."""
        if self.preview_canvas is None:
            self.preview_canvas = create_canvas(200, 200)
        
        # Render polyform to canvas
        renderer = PolyformRenderer(200)
        image = renderer.render(textured_polyform)
        
        # Display in preview
        ctx = self.preview_canvas.getContext('2d')
        ctx.drawImage(image, 0, 0)
    
    def _build_preview_section(self):
        """Preview thumbnail."""
        section = create_div(class_='preview-section')
        label = create_label("Preview")
        self.preview_canvas = create_canvas(200, 200)
        section.append(label, self.preview_canvas)
        return section
    
    def _build_action_buttons(self):
        """Process, copy, download buttons."""
        buttons = create_div(class_='action-buttons')
        
        process_btn = create_button("Process", onclick=self._on_process)
        copy_btn = create_button("Copy", onclick=self._on_copy)
        download_btn = create_button("Download", onclick=self._on_download)
        
        buttons.append(process_btn, copy_btn, download_btn)
        return buttons
    
    def _on_process(self):
        """Process with current options."""
        if self.mode == 'compress':
            self._process_image(self.input_file)
        else:
            self._on_unicode_pasted({'target': self.output_textarea})
    
    def _on_copy(self):
        """Copy output to clipboard."""
        text = self.output_textarea.value
        navigator.clipboard.writeText(text).then(
            () => self._show_notification("Copied!"),
            () => self._show_error("Copy failed")
        )
    
    def _on_download(self):
        """Download output."""
        if self.mode == 'compress':
            # Download Unicode string as .txt
            text = self.output_textarea.value
            blob = Blob([text], {'type': 'text/plain'})
            url = URL.createObjectURL(blob)
            link = create_link(href=url, download='polyform.txt')
            link.click()
        else:
            # Download image as PNG
            canvas = self.preview_canvas
            link = create_link(href=canvas.toDataURL(), download='polyform.png')
            link.click()
    
    def _build_mode_selector(self):
        """Radio buttons for compress/decompress."""
        section = create_div(class_='mode-selector')
        
        compress_radio = create_radio('mode', 'compress', True)
        compress_label = create_label("Compress Image → Unicode")
        
        decompress_radio = create_radio('mode', 'decompress', False)
        decompress_label = create_label("Decompress Unicode → Image")
        
        compress_radio.addEventListener('change', () => self._on_mode_changed('compress'))
        decompress_radio.addEventListener('change', () => self._on_mode_changed('decompress'))
        
        section.append(
            compress_radio, compress_label,
            decompress_radio, decompress_label
        )
        return section
    
    def _on_mode_changed(self, new_mode):
        """Switch between compress/decompress."""
        self.mode = new_mode
        self._build_ui()  # Rebuild UI for new mode
```

### 4.3 Window Management

```python
# window_manager.py

class WindowManager:
    """
    Manage floating windows (ImageCompressionSuite, etc.).
    """
    
    def __init__(self):
        self.open_windows = {}
    
    def open_image_compression_suite(self):
        """
        Open image compression in separate window.
        Prevent multiple instances.
        """
        if 'image_suite' in self.open_windows:
            # Bring to front if already open
            self.open_windows['image_suite'].window.focus()
            return
        
        suite = ImageCompressionSuite()
        self.open_windows['image_suite'] = suite
        
        # Handle window close
        suite.window.addEventListener('close', () => {
            del self.open_windows['image_suite']
        })
    
    def close_all(self):
        """Close all floating windows."""
        for key, window in self.open_windows.items():
            window.window.close()
        self.open_windows.clear()
```

---

## 5. Menu Integration

### 5.1 Tools Menu

```
Tools ▼
├─ Image Compression Suite   [Ctrl+I]
├─ Separator
├─ Color Scheme
│  ├─ Load Preset ▼
│  ├─ Save Preset as...
│  └─ Reset to Default       [Ctrl+Alt+C]
├─ Debug Inspector           [Ctrl+Shift+D]
```

### 5.2 Menu Handler

```python
# menu_handler.py

class MenuHandler:
    """
    Handle menu clicks.
    """
    
    def on_tools_image_compression(self):
        """Tools → Image Compression Suite"""
        window_manager = get_window_manager()
        window_manager.open_image_compression_suite()
    
    def on_tools_reset_colors(self):
        """Tools → Color Scheme → Reset to Default"""
        color_scheme = get_workspace().color_scheme
        color_scheme.reset_to_default()
```

---

## 6. Data Flow Diagram

```
COMPRESS MODE:
  User selects image
    ↓
  image_to_polyform() [feature detection, fit, extract]
    ↓
  TexturedPolyform instance (Ω₅₀Ἰ₁...Ρ₃)
    ↓
  to_compact_string()
    ↓
  Display Unicode + stats
    ↓
  User copies/downloads

DECOMPRESS MODE:
  User pastes Unicode
    ↓
  decode_unicode_string()
    ↓
  TexturedPolyform instance (reconstructed)
    ↓
  render_to_image() [procedural reconstruction]
    ↓
  Display preview
    ↓
  User downloads

COLOR SYSTEM (Separate Process):
  Workspace renders polyforms
    ↓
  For each polyform:
    - Get primitive pairs
    - Query color_scheme.get_color_for_polyform()
    - Apply semantic color (from hue chart + size modifier)
    ↓
  THREE.js material color set
    ↓
  Render frame (60 FPS)
```

---

## 7. Implementation Checklist

### Phase 1: Color System Foundation (Week 1)

- [ ] Implement PrimitiveColorScheme class
- [ ] Define all 324 primitive pairs with default hue assignments
- [ ] Implement HSB → RGB conversion
- [ ] Implement hue shift based on polyform size
- [ ] Unit tests: verify color calculation

### Phase 2: Color UI Panel (Week 2)

- [ ] Render interactive hue wheel (2D canvas)
- [ ] Implement pair sliders (list of all pairs)
- [ ] Implement global controls (saturation, brightness, shift factor)
- [ ] Add save/load preset functionality
- [ ] Test: adjust colors → see real-time viewport changes

### Phase 3: Rendering Integration (Week 2)

- [ ] Update HighFidelityRenderer to use PrimitiveColorScheme
- [ ] Verify: polyforms render with semantic colors
- [ ] Test: image-textured polyforms use texture color (override semantic)

### Phase 4: Image Compression Suite Window (Week 3)

- [ ] Create floating window container (no interference with workspace)
- [ ] Implement mode selector (compress/decompress)
- [ ] Implement image upload (compress mode)
- [ ] Implement Unicode paste (decompress mode)
- [ ] Wire to image_to_polyform() and decode_unicode_string()

### Phase 5: Compression Options (Week 3)

- [ ] Color depth selector (8-bit, 10-bit, 12-bit)
- [ ] Pattern layer toggle
- [ ] Palette mode selector (embedded vs. reference)
- [ ] Quality slider

### Phase 6: Output & Export (Week 3–4)

- [ ] Display compressed Unicode in textarea
- [ ] Calculate compression stats (ratio, sizes)
- [ ] Copy to clipboard button
- [ ] Download button (text for compress, image for decompress)
- [ ] Preview thumbnail

### Phase 7: Polish (Week 4)

- [ ] Profile color calculations (target: <1ms per frame)
- [ ] Optimize hue wheel rendering
- [ ] Test round-trip: image → compress → decompress → image
- [ ] Verify fidelity loss is acceptable

---

## 8. Key Design Principles

✓ **Semantic coloring:** Colors encode polyform composition (primitive pairs)  
✓ **Adjustable:** User controls hue assignments via sliders or hue wheel  
✓ **Visual hierarchy:** Size modifier (hue shift) conveys polyform order/size  
✓ **Separate tooling:** Image codec in pop-out window (never interferes)  
✓ **Non-intrusive:** No encoding UI in main workspace during normal use  
✓ **Professional:** High-fidelity rendering regardless of color scheme  

---

## 9. Conclusion

**Color System:**
- Primitive pairs (AA, AB, etc.) map to hues via adjustable chart
- User-controllable scaler reorganizes which pairs → which colors
- Size/order encoding via hue shift (larger = different hue)
- Visually appealing, semantically meaningful coloring

**Image Compression Suite:**
- Separate pop-out window (always available, never in way)
- Image → Unicode compression with quality/depth options
- Unicode → Image decompression with preview
- Professional export (copy/download)

**Result:** Beautiful workspace with intelligent color coding + powerful image codec always one click away.

---

**End of Color Visualization & Image Compression Suite Specification**
