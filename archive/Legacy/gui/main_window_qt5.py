"""Main window for the Polylog application using PyQt5."""

import json
import time

from PyQt5.QtWidgets import (
    QAction,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)


class MainWindow(QMainWindow):
    """Main application window with 3D viewport and controls."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Polylog Designer")
        self.resize(1200, 800)
        
        try:
            # Create central widget and layout
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            layout = QHBoxLayout(central_widget)
            
            # Initialize viewport with error handling
            self.viewport = None
            self._init_viewport()
            if self.viewport is None:
                raise RuntimeError("Failed to initialize OpenGL viewport")
                
            layout.addWidget(self.viewport, stretch=2)
            
            # Create right panel for controls
            right_panel = QWidget()
            right_layout = QVBoxLayout(right_panel)
            layout.addWidget(right_panel, stretch=1)
            
            # Add controls to right panel
            self._setup_controls(right_layout)
            
            # Create status bar
            self.statusBar = QStatusBar()
            self.setStatusBar(self.statusBar)
            
            # Create toolbar
            self._setup_toolbar()
            
            # Connect signals with error checking
            self._connect_signals()
            
            # Setup error handling for viewport
            self.viewport.installEventFilter(self)
            
            print("✓ Main window initialized successfully")
            self.statusBar.showMessage("Ready", 3000)
            
        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Initialization Error",
                               f"Failed to initialize application window:\n{str(e)}")
            raise  # Re-raise to let the app_qt5.py handle it
    
    def _setup_controls(self, layout):
        """Setup control panel widgets."""
        # Add polygon button
        add_btn = QPushButton("Add Polygon")
        add_btn.clicked.connect(self._add_test_polygon)
        layout.addWidget(add_btn)
        
        # Reset view button
        reset_btn = QPushButton("Reset View")
        reset_btn.clicked.connect(self.viewport.reset_view)
        layout.addWidget(reset_btn)
        
        # Clear button
        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self.viewport.clear)
        layout.addWidget(clear_btn)
        
        # Status label
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
        
        # Add stretcher to push controls to top
        layout.addStretch()
    
    def _setup_toolbar(self):
        """Setup application toolbar with proper state management."""
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        # File operations
        self.new_action = QAction("New", self)
        self.new_action.setShortcut("Ctrl+N")
        self.new_action.setStatusTip("Create new assembly")
        self.new_action.triggered.connect(self._new_assembly)
        toolbar.addAction(self.new_action)
        
        self.open_action = QAction("Open", self)
        self.open_action.setShortcut("Ctrl+O")
        self.open_action.setStatusTip("Open assembly from file")
        self.open_action.triggered.connect(self._open_assembly)
        toolbar.addAction(self.open_action)
        
        self.save_action = QAction("Save", self)
        self.save_action.setShortcut("Ctrl+S")
        self.save_action.setStatusTip("Save assembly to file")
        self.save_action.triggered.connect(self._save_assembly)
        toolbar.addAction(self.save_action)
        
        toolbar.addSeparator()
        
        # Edit operations
        self.undo_action = QAction("Undo", self)
        self.undo_action.setShortcut("Ctrl+Z")
        self.undo_action.setStatusTip("Undo last action")
        self.undo_action.triggered.connect(self._safe_undo)
        self.undo_action.setEnabled(False)
        toolbar.addAction(self.undo_action)
        
        self.redo_action = QAction("Redo", self)
        self.redo_action.setShortcut("Ctrl+Shift+Z")
        self.redo_action.setStatusTip("Redo last undone action")
        self.redo_action.triggered.connect(self._safe_redo)
        self.redo_action.setEnabled(False)
        toolbar.addAction(self.redo_action)
        
        toolbar.addSeparator()
        
        # View operations
        self.reset_view_action = QAction("Reset View", self)
        self.reset_view_action.setStatusTip("Reset camera view")
        self.reset_view_action.triggered.connect(self._safe_reset_view)
        toolbar.addAction(self.reset_view_action)
    
    def _add_test_polygon(self):
        """Add a test polygon to the viewport."""
        polygon_data = {
            'name': 'Test Polygon',
            'vertices': [(-1, -1), (1, -1), (1, 1), (-1, 1)],
            'sides': 4
        }
        self.viewport.add_polygon(polygon_data)
    
    def _init_viewport(self):
        """Initialize OpenGL viewport with error handling."""
        try:
            from gui.viewport_qt5 import Viewport3D
            self.viewport = Viewport3D()
            
            # Verify viewport initialized correctly
            if not self.viewport.isValid():
                raise RuntimeError("OpenGL context initialization failed")
                
        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self, "OpenGL Error",
                               f"Failed to initialize OpenGL viewport:\n{str(e)}\n\n"
                               "Please check your graphics drivers or try setting "
                               "POLYLOG_SOFTWARE_OPENGL=1")
            raise
    
    def _connect_signals(self):
        """Connect all Qt signals with error handling."""
        try:
            # Main viewport signals
            self.viewport.status_changed.connect(self.statusBar.showMessage)
            self.viewport.polyforms_updated.connect(self._update_polygon_count)
            self.viewport.undo_available.connect(self._update_undo_state)
            self.viewport.redo_available.connect(self._update_redo_state)
            
            # Optional viewport signals
            if hasattr(self.viewport, 'polygon_selected'):
                self.viewport.polygon_selected.connect(self._handle_polygon_selection)
            if hasattr(self.viewport, 'polygon_dropped'):
                self.viewport.polygon_dropped.connect(self._handle_polygon_drop)
                
        except Exception as e:
            print(f"Warning: Failed to connect some signals: {e}")
    
    def _update_undo_state(self, available: bool):
        """Update undo action state."""
        if hasattr(self, 'undo_action'):
            self.undo_action.setEnabled(available)
    
    def _update_redo_state(self, available: bool):
        """Update redo action state."""
        if hasattr(self, 'redo_action'):
            self.redo_action.setEnabled(available)
    
    def _handle_polygon_selection(self, index: int):
        """Handle polygon selection change."""
        if index >= 0:
            self.statusBar.showMessage(f"Selected polygon {index}")
        else:
            self.statusBar.showMessage("No polygon selected")
    
    def _handle_polygon_drop(self, data: dict):
        """Handle polygon dropped from library."""
        try:
            self.statusBar.showMessage(f"Added {data.get('name', 'polygon')}")
        except Exception as e:
            print(f"Warning: Error handling polygon drop: {e}")
    
    def eventFilter(self, watched, event):
        """Event filter to catch viewport errors."""
        if watched == self.viewport:
            if event.type() == event.Paint:
                try:
                    return False  # Let the event continue
                except Exception as e:
                    self.statusBar.showMessage(f"Render error: {str(e)}")
                    return True  # Stop event propagation
        return super().eventFilter(watched, event)
    
    def _update_polygon_count(self, count):
        """Update polygon count in status label."""
        self.status_label.setText(f"Polygons: {count}")
    
    def _safe_undo(self):
        """Safely perform undo operation."""
        try:
            self.viewport.undo()
        except Exception as e:
            self.statusBar.showMessage(f"Undo failed: {str(e)}")
    
    def _safe_redo(self):
        """Safely perform redo operation."""
        try:
            self.viewport.redo()
        except Exception as e:
            self.statusBar.showMessage(f"Redo failed: {str(e)}")
    
    def _safe_reset_view(self):
        """Safely reset viewport camera."""
        try:
            self.viewport.reset_view()
            self.statusBar.showMessage("View reset")
        except Exception as e:
            self.statusBar.showMessage(f"View reset failed: {str(e)}")
    
    def _new_assembly(self):
        """Create new assembly with confirmation."""
        if self.viewport.polygons:
            from PyQt5.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                self, 'New Assembly',
                'Clear current assembly?\nUnsaved changes will be lost.',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        
        try:
            self.viewport.clear()
            self.statusBar.showMessage("Created new assembly")
        except Exception as e:
            self.statusBar.showMessage(f"Failed to create new assembly: {str(e)}")
    
    def _save_assembly(self):
        """Save current assembly to file with error handling."""
        if not self.viewport.polygons:
            self.statusBar.showMessage("Nothing to save")
            return
            
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Save Assembly",
                "",
                "Polylog Assembly (*.json);;All Files (*)"
            )
            
            if filename:
                # Ensure .json extension
                if not filename.lower().endswith('.json'):
                    filename += '.json'
                
                # Prepare assembly data
                assembly_data = {
                    'polygons': self.viewport.polygons,
                    'version': '0.1.0',
                    'metadata': {
                        'created': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'polygon_count': len(self.viewport.polygons)
                    }
                }
                
                # Save with error handling
                try:
                    with open(filename, 'w') as f:
                        json.dump(assembly_data, f, indent=2)
                    self.statusBar.showMessage(f"Saved to {filename}")
                except IOError as e:
                    raise RuntimeError(f"Failed to write file: {str(e)}")
                except Exception as e:
                    raise RuntimeError(f"Error saving assembly: {str(e)}")
                    
        except Exception as e:
            self.statusBar.showMessage(f"Save failed: {str(e)}")
            QMessageBox.warning(self, "Save Error",
                              f"Failed to save assembly:\n{str(e)}")
    
    def _open_assembly(self):
        """Load assembly from file with validation and error handling."""
        try:
            filename, _ = QFileDialog.getOpenFileName(
                self,
                "Open Assembly",
                "",
                "Polylog Assembly (*.json);;All Files (*)"
            )
            
            if filename:
                # Load and validate file
                try:
                    with open(filename, 'r') as f:
                        data = json.load(f)
                except IOError as e:
                    raise RuntimeError(f"Failed to read file: {str(e)}")
                except json.JSONDecodeError:
                    raise RuntimeError("Invalid JSON format")
                
                # Validate structure
                if not isinstance(data, dict):
                    raise RuntimeError("Invalid assembly file format")
                if 'polygons' not in data:
                    raise RuntimeError("No polygon data found")
                if not isinstance(data['polygons'], list):
                    raise RuntimeError("Invalid polygon data format")
                
                # Load polygons
                try:
                    self.viewport.clear()
                    for polygon in data['polygons']:
                        if not isinstance(polygon, dict):
                            continue
                        self.viewport.add_polygon(polygon)
                    
                    count = len(data['polygons'])
                    self.statusBar.showMessage(
                        f"Loaded {count} polygon{'s' if count != 1 else ''} from {filename}"
                    )
                    
                except Exception as e:
                    raise RuntimeError(f"Error loading polygons: {str(e)}")
                    
        except Exception as e:
            self.statusBar.showMessage(f"Open failed: {str(e)}")
            QMessageBox.warning(self, "Open Error",
                              f"Failed to open assembly:\n{str(e)}")