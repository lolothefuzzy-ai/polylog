"""
Simplified polyform visualizer using Qt5 and OpenGL.
Self-contained script for visualizing polyform data structures.
"""

import sys
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, 
    QPushButton, QOpenGLWidget, QLabel
)
from PyQt5.QtCore import pyqtSignal
from OpenGL.GL import (
    glEnable, glDisable, glViewport, glMatrixMode, glLoadIdentity,
    glFrustum, glClear, glTranslatef, glRotatef, glColor3f,
    glVertex3f, glBegin, glEnd, glPushMatrix, glPopMatrix,
    glLineWidth, glLightfv, glGenLists, glNewList, glEndList,
    glCallList, glDeleteLists,
    GL_DEPTH_TEST, GL_LIGHTING, GL_LIGHT0, GL_COLOR_MATERIAL,
    GL_POSITION, GL_AMBIENT, GL_DIFFUSE,
    GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT, GL_PROJECTION,
    GL_MODELVIEW, GL_LINES, GL_POLYGON, GL_LINE_LOOP,
    GL_COMPILE
)
from random_assembly_generator import RandomAssemblyGenerator

class Viewport3D(QOpenGLWidget):
    status_changed = pyqtSignal(str)
    polyforms_updated = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.polygons = []
        self.polygon_count = 0
        self.display_lists = {}
        self.camera_distance = 5.0
        self.camera_rotation = [45.0, 45.0, 0.0]
        
    def initializeGL(self):
        """Initialize OpenGL settings."""
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        
        # Light position and properties
        glLightfv(GL_LIGHT0, GL_POSITION, [1.0, 1.0, 1.0, 0.0])
        glLightfv(GL_LIGHT0, GL_AMBIENT, [0.2, 0.2, 0.2, 1.0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.8, 0.8, 0.8, 1.0])
        
    def resizeGL(self, width, height):
        """Handle window resize events."""
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        aspect = width / height if height > 0 else 1.0
        glFrustum(-1.0 * aspect, 1.0 * aspect, -1.0, 1.0, 1.0, 100.0)
        
    def paintGL(self):
        """Render the scene."""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        # Position camera
        glTranslatef(0.0, 0.0, -self.camera_distance)
        glRotatef(self.camera_rotation[0], 1.0, 0.0, 0.0)
        glRotatef(self.camera_rotation[1], 0.0, 1.0, 0.0)
        glRotatef(self.camera_rotation[2], 0.0, 0.0, 1.0)
        
        # Draw coordinate axes for reference
        self._draw_axes()
        
        # Draw all polygons
        for i, polygon in enumerate(self.polygons):
            self._render_polygon(polygon, i)
            
    def _draw_axes(self):
        """Draw reference axes (RGB for XYZ)."""
        glDisable(GL_LIGHTING)
        glBegin(GL_LINES)
        
        # X axis (red)
        glColor3f(1.0, 0.0, 0.0)
        glVertex3f(0.0, 0.0, 0.0)
        glVertex3f(2.0, 0.0, 0.0)
        
        # Y axis (green)
        glColor3f(0.0, 1.0, 0.0)
        glVertex3f(0.0, 0.0, 0.0)
        glVertex3f(0.0, 2.0, 0.0)
        
        # Z axis (blue)
        glColor3f(0.0, 0.0, 1.0)
        glVertex3f(0.0, 0.0, 0.0)
        glVertex3f(0.0, 0.0, 2.0)
        
        glEnd()
        glEnable(GL_LIGHTING)
        
    def _render_polygon(self, polygon, index):
        """Render a single polygon."""
        vertices = np.array(polygon['vertices'], dtype=np.float32)
        if len(vertices) < 3:
            return
            
        # Generate unique key for display list caching
        cache_key = str(vertices.tobytes())
        
        if cache_key not in self.display_lists:
            # Create new display list
            display_list = glGenLists(1)
            glNewList(display_list, GL_COMPILE)
            
            glPushMatrix()
            
            # Set color based on index
            color = [(index * 0.7 + 0.3) % 1.0, 
                    (index * 0.5 + 0.5) % 1.0,
                    (index * 0.3 + 0.7) % 1.0]
            glColor3f(*color)
            
            # Draw filled polygon
            glBegin(GL_POLYGON)
            for vertex in vertices:
                glVertex3f(float(vertex[0]), float(vertex[1]), float(vertex[2]))
            glEnd()
            
            # Draw wireframe outline
            glColor3f(0.2, 0.2, 0.2)
            glLineWidth(2.0)
            
            glBegin(GL_LINE_LOOP)
            for vertex in vertices:
                glVertex3f(float(vertex[0]), float(vertex[1]), float(vertex[2]))
            glEnd()
            
            glPopMatrix()
            glEndList()
            
            self.display_lists[cache_key] = display_list
            
        # Call the cached display list
        glCallList(self.display_lists[cache_key])
        
    def clear(self):
        """Clear all polygons from viewport."""
        # Delete display lists
        for display_list in self.display_lists.values():
            try:
                glDeleteLists(display_list, 1)
            except Exception as e:
                print(f"Warning: Failed to delete display list: {e}")
        self.display_lists.clear()
        
        self.polygons = []
        self.polygon_count = 0
        self.update()
        self.status_changed.emit("Viewport cleared")
        
    def add_polygon(self, polygon_data: dict):
        """Add a polygon to the viewport."""
        try:
            # Ensure polygon data is normalized
            from gui.polyform_adapter import normalize_polyform
            normalized_data = normalize_polyform(polygon_data)
            
            # Store normalized data
            self.polygons.append(normalized_data)
            self.polygon_count = len(self.polygons)
            
            # Emit signals
            self.polyforms_updated.emit(self.polygon_count)
            self.update()
            
            # Update status
            type_str = normalized_data.get('type', 'unknown type')
            sides_str = normalized_data.get('sides', '?')
            self.status_changed.emit(
                f"Added {sides_str}-sided {type_str} polygon ({self.polygon_count} total)"
            )
            
        except Exception as e:
            print(f"Error adding polygon: {e}")
            self.status_changed.emit(f"Error adding polygon: {str(e)}")

class PolyformVisualizer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Polyform Visualizer")
        self.setGeometry(100, 100, 800, 600)

        # Create central widget and layout
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Create 3D viewport
        self.viewport = Viewport3D()
        layout.addWidget(self.viewport)

        # Create controls
        btn_add = QPushButton("Add Random Polyform")
        btn_add.clicked.connect(self.add_random_polyform)
        layout.addWidget(btn_add)

        btn_clear = QPushButton("Clear")
        btn_clear.clicked.connect(self.viewport.clear)
        layout.addWidget(btn_clear)
        
        # Status label
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
        
        # Connect signals
        self.viewport.status_changed.connect(self.status_label.setText)
        self.viewport.polyforms_updated.connect(
            lambda count: self.status_label.setText(f"Polyforms: {count}")
        )

        # Initialize generator
        self.generator = RandomAssemblyGenerator()

    def add_random_polyform(self):
        """Add a random polyform to the viewport"""
        try:
            # Generate a random polyform
            polyforms = self.generator.generate_random_assembly(
                num_polyforms=1,
                allow_types=[5], # Pentagon for testing
                use_3d=True
            )
            
            if polyforms:
                from gui.polyform_adapter import normalize_polyform
                
                # Normalize the polyform data
                polygon_data = normalize_polyform(polyforms[0])
                
                # Add to viewport
                self.viewport.add_polygon(polygon_data)
                
                self.status_label.setText(f"Added {polygon_data['sides']}-sided polyform")
                
        except Exception as e:
            print(f"Error generating polyform: {e}")
            self.status_label.setText(f"Error: {str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PolyformVisualizer()
    window.show()
    sys.exit(app.exec_())