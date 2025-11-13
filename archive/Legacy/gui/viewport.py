"""
3D OpenGL Viewport for polygon visualization.

Renders polygons and assembly using OpenGL through PySide6.
Phase 1: Basic placeholder with grid and camera controls.
Phase 2: Full 3D rendering implementation.
"""

from OpenGL.GL import *
from OpenGL.GLU import *
from PySide6.QtCore import QTimer, Signal
from PySide6.QtWidgets import QOpenGLWidget


class Viewport3D(QOpenGLWidget):
    """
    3D viewport for polygon visualization using OpenGL.
    
    Features:
    - Grid background
    - Camera controls (rotation, zoom, pan)
    - Polygon rendering
    - Real-time updates
    """
    
    # Signals
    status_changed = Signal(str)
    polyforms_updated = Signal(int)
    polygon_selected = Signal(int)  # Emits selected polygon index
    undo_available = Signal(bool)
    redo_available = Signal(bool)
    polygon_dropped = Signal(dict)  # Emits dropped polygon data
    
    def __init__(self):
        super().__init__()
        
        # Camera parameters
        self.camera_distance = 5.0
        self.camera_angle_x = 45.0
        self.camera_angle_y = 45.0
        self.camera_pan_x = 0.0
        self.camera_pan_y = 0.0
        
        # Mouse tracking
        self.last_mouse_x = 0
        self.last_mouse_y = 0
        self.mouse_pressed = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.is_creating_polygon = False
        self.polygon_vertices = []  # Vertices being created by drag
        
        # Viewport data
        self.polygons = []  # List of polygon objects to render
        self.polygon_count = 0
        self.display_lists = {}  # Cache of OpenGL display lists for polygons
        self.selected_polygon = None  # Currently selected polygon index
        self.undo_stack = []  # Undo history
        self.redo_stack = []  # Redo history
        
        # Animation timer
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update)
        self.animation_timer.start(16)  # ~60 FPS
        
        # Enable drag and drop
        self.setAcceptDrops(True)
        
        print("✓ Viewport3D initialized")
    
    def initializeGL(self):
        """Initialize OpenGL settings."""
        glClearColor(0.1, 0.1, 0.1, 1.0)  # Dark background
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        
        # Setup lighting
        glLight(GL_LIGHT0, GL_POSITION, (0, 0, 1, 0))
        glLight(GL_LIGHT0, GL_AMBIENT, (0.3, 0.3, 0.3, 1.0))
        glLight(GL_LIGHT0, GL_DIFFUSE, (1.0, 1.0, 1.0, 1.0))
        
        print("✓ OpenGL initialized")
    
    def resizeGL(self, w: int, h: int):
        """Handle viewport resize."""
        if h == 0:
            h = 1
        
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        
        aspect = w / h
        gluPerspective(45.0, aspect, 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)
    
    def paintGL(self):
        """Render the scene."""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        
        # Position camera
        self._setup_camera()
        
        # Draw grid background
        self._draw_grid()
        
        # Draw polygons
        self._draw_polygons()
        
        # Draw axes for reference
        self._draw_axes()
    
    def _setup_camera(self):
        """Setup camera position and orientation."""
        import math
        
        # Convert angles to radians
        rad_x = math.radians(self.camera_angle_x)
        rad_y = math.radians(self.camera_angle_y)
        
        # Calculate camera position
        cam_x = self.camera_distance * math.sin(rad_y) * math.cos(rad_x)
        cam_y = self.camera_distance * math.sin(rad_x)
        cam_z = self.camera_distance * math.cos(rad_y) * math.cos(rad_x)
        
        # Apply pan offset
        look_x = self.camera_pan_x
        look_y = self.camera_pan_y
        look_z = 0
        
        gluLookAt(cam_x + look_x, cam_y + look_y, cam_z, look_x, look_y, look_z, 0, 1, 0)
    
    def _draw_grid(self):
        """Draw reference grid on XZ plane."""
        glDisable(GL_LIGHTING)
        glColor3f(0.3, 0.3, 0.3)
        
        grid_size = 10
        grid_step = 1
        
        glBegin(GL_LINES)
        for i in range(-grid_size, grid_size + 1, grid_step):
            # Lines parallel to X axis
            glVertex3f(-grid_size, -0.01, i)
            glVertex3f(grid_size, -0.01, i)
            
            # Lines parallel to Z axis
            glVertex3f(i, -0.01, -grid_size)
            glVertex3f(i, -0.01, grid_size)
        glEnd()
        
        glEnable(GL_LIGHTING)
    
    def _draw_axes(self):
        """Draw reference axes (RGB for XYZ)."""
        glDisable(GL_LIGHTING)
        glLineWidth(2.0)
        
        axis_length = 2.0
        
        glBegin(GL_LINES)
        # X axis - Red
        glColor3f(1.0, 0.0, 0.0)
        glVertex3f(0, 0, 0)
        glVertex3f(axis_length, 0, 0)
        
        # Y axis - Green
        glColor3f(0.0, 1.0, 0.0)
        glVertex3f(0, 0, 0)
        glVertex3f(0, axis_length, 0)
        
        # Z axis - Blue
        glColor3f(0.0, 0.0, 1.0)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 0, axis_length)
        glEnd()
        
        glLineWidth(1.0)
        glEnable(GL_LIGHTING)
    
    def _draw_polygons(self):
        """Draw all polygons in the viewport."""
        for i, polygon in enumerate(self.polygons):
            self._render_polygon(polygon, i)
        
        # Draw preview of polygon being created
        if self.is_creating_polygon and len(self.polygon_vertices) >= 2:
            self._draw_polygon_preview()
    
    def _render_polygon(self, polygon, index):
        """Render a single polygon as 3D shape."""
        glPushMatrix()
        
        # Get color for this polygon
        from gui.utils import get_polygon_color
        color = get_polygon_color(index)
        
        # Brighten color if selected
        if self.selected_polygon == index:
            color = tuple(min(1.0, c * 1.5) for c in color)
        
        glColor3f(*color)
        
        # Get vertices from polygon data
        vertices = polygon.get('vertices', [])
        if not vertices:
            glPopMatrix()
            return
        
        # Convert to 3D tuples if needed
        verts_3d = []
        for v in vertices:
            if isinstance(v, (list, tuple)):
                if len(v) == 2:
                    verts_3d.append((v[0], v[1], 0.0))
                else:
                    verts_3d.append(tuple(v[:3]))
        
        if len(verts_3d) < 3:
            glPopMatrix()
            return
        
        # Create cache key for this polygon geometry
        cache_key = tuple(verts_3d)
        
        # Check if we have a cached display list
        if cache_key not in self.display_lists:
            # Create new display list
            display_list = glGenLists(1)
            glNewList(display_list, GL_COMPILE)
            
            # Draw polygon as triangle fan
            glBegin(GL_TRIANGLE_FAN)
            for vertex in verts_3d:
                glVertex3f(float(vertex[0]), float(vertex[1]), float(vertex[2]))
            glEnd()
            
            # Draw outline
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
            glColor3f(1.0, 1.0, 1.0)  # White outline
            glLineWidth(2.0)
            
            glBegin(GL_LINE_LOOP)
            for vertex in verts_3d:
                glVertex3f(float(vertex[0]), float(vertex[1]), float(vertex[2]))
            glEnd()
            
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
            glLineWidth(1.0)
            
            glEndList()
            self.display_lists[cache_key] = display_list
        
        # Call the cached display list
        glCallList(self.display_lists[cache_key])
        
        glPopMatrix()
    
    def clear(self):
        """Clear all polygons from viewport."""
        # Delete display lists
        for display_list in self.display_lists.values():
            try:
                glDeleteLists(display_list, 1)
            except:
                pass
        self.display_lists.clear()
        
        self.polygons = []
        self.polygon_count = 0
        self.update()
        self.status_changed.emit("Viewport cleared")
    
    def add_polygon(self, polygon_data: dict):
        """Add a polygon to the viewport."""
        # Save state for undo
        self.undo_stack.append([p.copy() if isinstance(p, dict) else p for p in self.polygons])
        self.redo_stack.clear()
        self.undo_available.emit(True)
        self.redo_available.emit(False)
        
        # Add polygon
        self.polygons.append(polygon_data)
        self.polygon_count = len(self.polygons)
        self.polyforms_updated.emit(self.polygon_count)
        self.update()
    
    def update_preview(self, params: dict):
        """Update preview based on polygon parameters."""
        # This will be implemented in Phase 2 with actual polygon generation
        # For now, just trigger a redraw
        self.update()
    
    def reset_view(self):
        """Reset camera to default position."""
        self.camera_distance = 5.0
        self.camera_angle_x = 45.0
        self.camera_angle_y = 45.0
        self.update()
    
    def undo(self):
        """Undo last action."""
        if self.undo_stack:
            self.redo_stack.append([p.copy() if isinstance(p, dict) else p for p in self.polygons])
            self.polygons = self.undo_stack.pop()
            self.polygon_count = len(self.polygons)
            self.polyforms_updated.emit(self.polygon_count)
            self.undo_available.emit(len(self.undo_stack) > 0)
            self.redo_available.emit(True)
            self.update()
    
    def redo(self):
        """Redo last undone action."""
        if self.redo_stack:
            self.undo_stack.append([p.copy() if isinstance(p, dict) else p for p in self.polygons])
            self.polygons = self.redo_stack.pop()
            self.polygon_count = len(self.polygons)
            self.polyforms_updated.emit(self.polygon_count)
            self.undo_available.emit(True)
            self.redo_available.emit(len(self.redo_stack) > 0)
            self.update()
    
    def select_polygon(self, index: int):
        """Select a polygon by index."""
        if 0 <= index < len(self.polygons):
            self.selected_polygon = index
            self.polygon_selected.emit(index)
            self.update()
    
    def deselect_polygon(self):
        """Deselect current polygon."""
        self.selected_polygon = None
        self.polygon_selected.emit(-1)
        self.update()
    
    def delete_polygon(self, index: int):
        """Delete a polygon at specified index."""
        if 0 <= index < len(self.polygons):
            # Save state for undo
            self.undo_stack.append([p.copy() if isinstance(p, dict) else p for p in self.polygons])
            self.redo_stack.clear()
            self.undo_available.emit(True)
            self.redo_available.emit(False)
            
            # Remove polygon
            del self.polygons[index]
            self.polygon_count = len(self.polygons)
            self.polyforms_updated.emit(self.polygon_count)
            
            # Deselect if that was the selected one
            if self.selected_polygon == index:
                self.selected_polygon = None
            elif self.selected_polygon is not None and self.selected_polygon > index:
                self.selected_polygon -= 1
            
            self.status_changed.emit(f"Polygon deleted (remaining: {self.polygon_count})")
            self.update()
    
    # Mouse interaction handlers
    
    def mousePressEvent(self, event):
        """Handle mouse press."""
        self.drag_start_x = event.position().x()
        self.drag_start_y = event.position().y()
        self.last_mouse_x = event.position().x()
        self.last_mouse_y = event.position().y()
        
        # Check for polygon selection on left click (if not starting a drag)
        if event.button() == 1:  # Left mouse button
            # Start potential drag-to-create
            self.is_creating_polygon = True
            self.polygon_vertices = [(self.drag_start_x, self.drag_start_y)]
        # Middle mouse button for panning
        elif event.button() == 4:  # Middle button
            self.mouse_pressed = True
        
        self.mouse_pressed = True
    
    def mouseMoveEvent(self, event):
        """Handle mouse movement for camera control or drag-to-create."""
        current_x = event.position().x()
        current_y = event.position().y()
        
        # Handle drag-to-create polygon
        if self.is_creating_polygon and self.mouse_pressed:
            # Calculate distance from drag start
            dist = ((current_x - self.drag_start_x) ** 2 + (current_y - self.drag_start_y) ** 2) ** 0.5
            
            # Add vertex if moved far enough (to avoid noise)
            if dist > 20:  # Minimum distance between vertices
                self.polygon_vertices.append((current_x, current_y))
                self.status_changed.emit(f"Creating polygon... {len(self.polygon_vertices)} vertices")
                self.update()
        elif self.mouse_pressed:
            dx = current_x - self.last_mouse_x
            dy = current_y - self.last_mouse_y
            
            # Check if middle mouse button is pressed
            modifiers = event.buttons()
            if modifiers & 0x04:  # Middle button
                # Pan camera
                pan_speed = 0.01
                self.camera_pan_x -= dx * pan_speed
                self.camera_pan_y += dy * pan_speed
            else:
                # Rotate camera (only if not creating polygon)
                if not self.is_creating_polygon:
                    self.camera_angle_y += dx * 0.5
                    self.camera_angle_x += dy * 0.5
                    
                    # Clamp X rotation
                    self.camera_angle_x = max(-89, min(89, self.camera_angle_x))
            
            self.update()
        
        self.last_mouse_x = current_x
        self.last_mouse_y = current_y
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release - finalize drag-to-create polygon."""
        self.mouse_pressed = False
        
        # Finalize polygon if drag-to-create was active
        if self.is_creating_polygon and len(self.polygon_vertices) >= 3:
            self._finalize_created_polygon()
        elif self.is_creating_polygon:
            # Not enough vertices - cancel
            self.polygon_vertices = []
            self.is_creating_polygon = False
            self.status_changed.emit("Polygon creation cancelled (need at least 3 vertices)")
        
        self.is_creating_polygon = False
    
    def wheelEvent(self, event):
        """Handle mouse wheel for zoom."""
        zoom_factor = 1.1 if event.angleDelta().y() > 0 else 0.9
        self.camera_distance *= zoom_factor
        self.camera_distance = max(1.0, min(50.0, self.camera_distance))
        self.update()
    
    def _try_select_polygon(self, screen_x: float, screen_y: float):
        """Try to select polygon at screen coordinates."""
        if not self.polygons:
            return
        
        # Simple heuristic: select polygon closest to center
        # In full implementation, would use ray casting
        center_x = self.width() / 2
        center_y = self.height() / 2
        
        dist_to_center = ((screen_x - center_x) ** 2 + (screen_y - center_y) ** 2) ** 0.5
        
        # If click is near center, select/deselect
        if dist_to_center < 100:
            if self.selected_polygon is not None:
                self.deselect_polygon()
            else:
                self.select_polygon(0)  # Select first polygon
        else:
            self.deselect_polygon()
    
    # Drag and Drop support
    
    def dragEnterEvent(self, event):
        """Handle drag enter - accept polygon drops from library."""
        if event.mimeData().hasFormat('text/plain'):
            # Check if the text is a valid polygon design name
            text = event.mimeData().text()
            if text and len(text.strip()) > 0:
                event.acceptProposedAction()
                self.status_changed.emit(f"Dragging '{text}' over viewport")
    
    def dragMoveEvent(self, event):
        """Handle drag move - provide visual feedback."""
        if event.mimeData().hasFormat('text/plain'):
            event.acceptProposedAction()
    
    def dragLeaveEvent(self, event):
        """Handle drag leave."""
        self.status_changed.emit("Drag cancelled")
    
    def dropEvent(self, event):
        """Handle drop from library - add polygon to viewport."""
        if event.mimeData().hasFormat('text/plain'):
            design_name = event.mimeData().text()
            
            # Get drop position
            drop_x = event.position().x()
            drop_y = event.position().y()
            
            # Create polygon data from dropped design
            polygon_data = self._create_polygon_from_design(design_name, drop_x, drop_y)
            
            if polygon_data:
                self.add_polygon(polygon_data)
                self.polygon_dropped.emit(polygon_data)
                self.status_changed.emit(f"Added '{design_name}' polygon at drop location")
            
            event.acceptProposedAction()
    
    def _create_polygon_from_design(self, design_name: str, screen_x: float, screen_y: float) -> dict:
        """Create a polygon from library design name."""
        # Map design names to basic polygon shapes
        design_map = {
            "Triangle Basic": self._create_triangle(),
            "Square Simple": self._create_square(),
            "Pentagon Star": self._create_pentagon(),
            "Hexagon Complex": self._create_hexagon(),
            "Octagon Pattern": self._create_octagon(),
            "Decagon Design": self._create_decagon(),
        }
        
        vertices = design_map.get(design_name, self._create_triangle())
        
        # Normalize vertices to unit size and position at drop location
        if vertices:
            # Scale vertices relative to viewport size
            scale = min(self.width(), self.height()) / 400
            vertices = [(x * scale, y * scale) for x, y in vertices]
        
        return {
            'name': design_name,
            'vertices': vertices,
            'sides': len(vertices) if vertices else 0,
            'position': (screen_x, screen_y),
        }
    
    def _create_triangle(self) -> list:
        """Create triangle vertices."""
        return [(0, -1), (0.866, 0.5), (-0.866, 0.5)]
    
    def _create_square(self) -> list:
        """Create square vertices."""
        return [(-1, -1), (1, -1), (1, 1), (-1, 1)]
    
    def _create_pentagon(self) -> list:
        """Create pentagon vertices."""
        import math
        angles = [2 * math.pi * i / 5 for i in range(5)]
        return [(math.cos(a), math.sin(a)) for a in angles]
    
    def _create_hexagon(self) -> list:
        """Create hexagon vertices."""
        import math
        angles = [2 * math.pi * i / 6 for i in range(6)]
        return [(math.cos(a), math.sin(a)) for a in angles]
    
    def _create_octagon(self) -> list:
        """Create octagon vertices."""
        import math
        angles = [2 * math.pi * i / 8 for i in range(8)]
        return [(math.cos(a), math.sin(a)) for a in angles]
    
    def _create_decagon(self) -> list:
        """Create decagon vertices."""
        import math
        angles = [2 * math.pi * i / 10 for i in range(10)]
        return [(math.cos(a), math.sin(a)) for a in angles]
    
    def _draw_polygon_preview(self):
        """Draw a preview of the polygon being created."""
        if len(self.polygon_vertices) < 2:
            return
        
        glDisable(GL_LIGHTING)
        glColor4f(0.0, 1.0, 0.5, 0.5)  # Semi-transparent cyan
        glLineWidth(2.0)
        
        # Convert screen coordinates to normalized preview
        preview_vertices = []
        for screen_x, screen_y in self.polygon_vertices:
            # Convert screen coordinates to normalized device coordinates
            norm_x = (screen_x / self.width()) * 2 - 1
            norm_y = 1 - (screen_y / self.height()) * 2
            preview_vertices.append((norm_x, norm_y, 0.0))
        
        # Draw lines between vertices
        glBegin(GL_LINE_STRIP)
        for vertex in preview_vertices:
            glVertex3f(vertex[0] * 0.1, vertex[1] * 0.1, vertex[2])
        glEnd()
        
        # Draw points at vertices
        glPointSize(4.0)
        glBegin(GL_POINTS)
        for vertex in preview_vertices:
            glVertex3f(vertex[0] * 0.1, vertex[1] * 0.1, vertex[2])
        glEnd()
        
        glLineWidth(1.0)
        glEnable(GL_LIGHTING)
    
    def _finalize_created_polygon(self):
        """Finalize the polygon being created and add it to viewport."""
        if len(self.polygon_vertices) < 3:
            self.status_changed.emit("Polygon needs at least 3 vertices")
            return
        
        # Convert screen coordinates to 2D normalized coordinates
        normalized_vertices = []
        for screen_x, screen_y in self.polygon_vertices:
            # Normalize to roughly -1 to 1 range based on viewport size
            norm_x = (screen_x / self.width()) * 4 - 2
            norm_y = (screen_y / self.height()) * 4 - 2
            normalized_vertices.append((norm_x, norm_y))
        
        # Create polygon data
        polygon_data = {
            'name': f'Custom Polygon {self.polygon_count + 1}',
            'vertices': normalized_vertices,
            'sides': len(normalized_vertices),
            'position': (self.polygon_vertices[0][0], self.polygon_vertices[0][1]),
            'created_by': 'drag_to_create',
        }
        
        # Add to viewport
        self.add_polygon(polygon_data)
        
        # Clear creation data
        self.polygon_vertices = []
        
        self.status_changed.emit(f"Created {len(normalized_vertices)}-sided polygon")
        self.update()
