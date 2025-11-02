"""
GUI Enhancement Module v2 - Polylog Desktop App
Implements: Menu Bar, Toolbar, Status Bar, Undo/Redo, Polygon Slider, Fold Animations
Focus: Library-centric layout with visual folding animations
"""
from typing import Any, Callable, Dict, List, Optional

from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import Qt, QTimer, Signal


# ======================== STATUS BAR MANAGER ========================
class StatusBarManager(QtWidgets.QStatusBar):
    """Enhanced status bar with real-time updates."""
    
    def __init__(self):
        super().__init__()
        self.setMaximumHeight(25)
        
        # Status message
        self.lbl_status = QtWidgets.QLabel("Ready")
        self.addWidget(self.lbl_status, stretch=1)
        
        # Separator
        self.addPermanentWidget(QtWidgets.QLabel("│"), 0)
        
        # Polyform count
        self.lbl_polyforms = QtWidgets.QLabel("Polyforms: 0")
        self.addPermanentWidget(self.lbl_polyforms, 0)
        
        # Separator
        self.addPermanentWidget(QtWidgets.QLabel("│"), 0)
        
        # Success rate
        self.lbl_success = QtWidgets.QLabel("Success: --")
        self.addPermanentWidget(self.lbl_success, 0)
        
        # Separator
        self.addPermanentWidget(QtWidgets.QLabel("│"), 0)
        
        # Animation status
        self.lbl_anim = QtWidgets.QLabel("Animation: Off")
        self.addPermanentWidget(self.lbl_anim, 0)
    
    def set_status(self, msg: str):
        """Update status message."""
        self.lbl_status.setText(msg)
    
    def set_polyforms(self, count: int):
        """Update polyform count."""
        self.lbl_polyforms.setText(f"Polyforms: {count}")
    
    def set_success_rate(self, rate: float):
        """Update success rate display."""
        self.lbl_success.setText(f"Success: {rate*100:.1f}%")
    
    def set_animation_status(self, status: str):
        """Update animation status."""
        self.lbl_anim.setText(f"Animation: {status}")


# ======================== UNDO/REDO MANAGER ========================
class UndoRedoManager(QtCore.QObject):
    """Manages undo/redo history for assembly operations."""
    
    undo_changed = Signal(bool)
    redo_changed = Signal(bool)
    
    def __init__(self, max_history: int = 50):
        super().__init__()
        self.max_history = max_history
        self.undo_stack: List[Dict[str, Any]] = []
        self.redo_stack: List[Dict[str, Any]] = []
    
    def push(self, state: Dict[str, Any]):
        """Push state to undo stack."""
        self.undo_stack.append(state)
        if len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0)
        self.redo_stack.clear()
        self.undo_changed.emit(len(self.undo_stack) > 0)
        self.redo_changed.emit(False)
    
    def undo(self) -> Dict[str, Any] | None:
        """Get previous state."""
        if not self.undo_stack:
            return None
        state = self.undo_stack.pop()
        self.redo_changed.emit(True)
        self.undo_changed.emit(len(self.undo_stack) > 0)
        return state
    
    def redo(self) -> Dict[str, Any] | None:
        """Get next state."""
        if not self.redo_stack:
            return None
        state = self.redo_stack.pop()
        self.undo_changed.emit(True)
        self.redo_changed.emit(len(self.redo_stack) > 0)
        return state
    
    def can_undo(self) -> bool:
        return len(self.undo_stack) > 0
    
    def can_redo(self) -> bool:
        return len(self.redo_stack) > 0
    
    def clear(self):
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.undo_changed.emit(False)
        self.redo_changed.emit(False)


# ======================== FOLD ANIMATION ENGINE ========================
class FoldAnimationEngine(QtCore.QObject):
    """Handles visual fold animations for polyforms."""
    
    animation_step = Signal(float)  # Emits progress 0-1
    animation_complete = Signal()
    
    def __init__(self):
        super().__init__()
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_animation)
        self.duration_ms = 2000  # 2 second default
        self.elapsed_ms = 0
        self.current_state = None
        self.target_state = None
        self.on_complete = None
    
    def start_fold_animation(self, start_state: Dict, end_state: Dict, 
                           duration_ms: int = 2000, callback: Optional[Callable] = None):
        """Start a fold animation from one state to another."""
        self.current_state = start_state
        self.target_state = end_state
        self.duration_ms = duration_ms
        self.elapsed_ms = 0
        self.on_complete = callback
        self.timer.start(16)  # ~60 FPS
    
    def _update_animation(self):
        """Update animation progress."""
        self.elapsed_ms += 16
        progress = min(1.0, self.elapsed_ms / self.duration_ms)
        
        # Emit progress with easing (ease-in-out)
        eased_progress = self._ease_in_out(progress)
        self.animation_step.emit(eased_progress)
        
        if progress >= 1.0:
            self.timer.stop()
            self.animation_complete.emit()
            if self.on_complete:
                self.on_complete()
    
    def _ease_in_out(self, t: float) -> float:
        """Ease-in-out cubic easing."""
        if t < 0.5:
            return 4 * t * t * t
        else:
            return 1 - pow(-2 * t + 2, 3) / 2
    
    def stop(self):
        """Stop animation."""
        self.timer.stop()


# ======================== POLYGON SLIDER WIDGET ========================
class PolygonInfluenceSlider(QtWidgets.QWidget):
    """
    Slider to influence polygon generation parameters.
    Controls: sides, complexity, symmetry
    
    INTERACTIONS:
    - Click anywhere on slider → triggers add_polygon_clicked signal
    - Drag sliders → update values in real-time
    - Hover → visual feedback
    """
    
    sides_changed = Signal(int)
    complexity_changed = Signal(float)
    symmetry_changed = Signal(float)
    add_polygon_clicked = Signal()  # NEW: Click to add
    
    def __init__(self):
        super().__init__()
        self.setMouseTracking(True)  # NEW: Track mouse for hover effects
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Title
        title = QtWidgets.QLabel("Polygon Generation")
        title.setStyleSheet("font-weight: bold; color: #ff3333;")
        layout.addWidget(title)
        
        # Sides slider
        layout.addWidget(QtWidgets.QLabel("Sides (3-12):"))
        self.sides_slider = QtWidgets.QSlider(Qt.Horizontal)
        self.sides_slider.setRange(3, 12)
        self.sides_slider.setValue(4)
        self.sides_label = QtWidgets.QLabel("4 sides")
        self.sides_slider.valueChanged.connect(self._on_sides_changed)
        
        sides_layout = QtWidgets.QHBoxLayout()
        sides_layout.addWidget(self.sides_slider)
        sides_layout.addWidget(self.sides_label, 0, Qt.AlignRight)
        layout.addLayout(sides_layout)
        
        # Complexity slider
        layout.addWidget(QtWidgets.QLabel("Complexity:"))
        self.complexity_slider = QtWidgets.QSlider(Qt.Horizontal)
        self.complexity_slider.setRange(0, 100)
        self.complexity_slider.setValue(50)
        self.complexity_label = QtWidgets.QLabel("0.50")
        self.complexity_slider.valueChanged.connect(self._on_complexity_changed)
        
        complexity_layout = QtWidgets.QHBoxLayout()
        complexity_layout.addWidget(self.complexity_slider)
        complexity_layout.addWidget(self.complexity_label, 0, Qt.AlignRight)
        layout.addLayout(complexity_layout)
        
        # Symmetry slider
        layout.addWidget(QtWidgets.QLabel("Symmetry:"))
        self.symmetry_slider = QtWidgets.QSlider(Qt.Horizontal)
        self.symmetry_slider.setRange(0, 100)
        self.symmetry_slider.setValue(75)
        self.symmetry_label = QtWidgets.QLabel("0.75")
        self.symmetry_slider.valueChanged.connect(self._on_symmetry_changed)
        
        symmetry_layout = QtWidgets.QHBoxLayout()
        symmetry_layout.addWidget(self.symmetry_slider)
        symmetry_layout.addWidget(self.symmetry_label, 0, Qt.AlignRight)
        layout.addLayout(symmetry_layout)
        
        # Add hint text (NEW)
        hint = QtWidgets.QLabel("Click anywhere to add polygon")
        hint.setStyleSheet("color: #888888; font-size: 11px; font-style: italic;")
        hint.setAlignment(Qt.AlignCenter)
        layout.addWidget(hint)
        
        layout.addStretch()
        
        # Set widget styling to indicate clickability (NEW)
        self.setStyleSheet(
            "PolygonInfluenceSlider { "
            "background-color: #151a2b; "
            "border: 1px solid #333; "
            "border-radius: 4px; "
            "} "
            "PolygonInfluenceSlider:hover { "
            "border: 1px solid #ff3333; "
            "}"
        )
        self.setCursor(Qt.PointingHandCursor)
    
    def _on_sides_changed(self, value: int):
        self.sides_label.setText(f"{value} sides")
        self.sides_changed.emit(value)
    
    def _on_complexity_changed(self, value: int):
        complexity = value / 100.0
        self.complexity_label.setText(f"{complexity:.2f}")
        self.complexity_changed.emit(complexity)
    
    def _on_symmetry_changed(self, value: int):
        symmetry = value / 100.0
        self.symmetry_label.setText(f"{symmetry:.2f}")
        self.symmetry_changed.emit(symmetry)
    
    def get_sides(self) -> int:
        return self.sides_slider.value()
    
    def get_complexity(self) -> float:
        return self.complexity_slider.value() / 100.0
    
    def get_symmetry(self) -> float:
        return self.symmetry_slider.value() / 100.0
    
    def mousePressEvent(self, event):
        """Handle click on slider widget to add polygon (NEW)."""
        if event.button() == Qt.LeftButton:
            # Emit signal to add polygon with current values
            self.add_polygon_clicked.emit()
            
            # Visual feedback
            self.setStyleSheet(
                "PolygonInfluenceSlider { "
                "background-color: #1a2a3b; "
                "border: 2px solid #ff3333; "
                "border-radius: 4px; "
                "} "
                "PolygonInfluenceSlider:hover { "
                "border: 2px solid #ff3333; "
                "}"
            )
            
            # Reset after short delay
            QtCore.QTimer.singleShot(200, self._reset_style)
        
        super().mousePressEvent(event)
    
    def _reset_style(self):
        """Reset styling after click (NEW)."""
        self.setStyleSheet(
            "PolygonInfluenceSlider { "
            "background-color: #151a2b; "
            "border: 1px solid #333; "
            "border-radius: 4px; "
            "} "
            "PolygonInfluenceSlider:hover { "
            "border: 1px solid #ff3333; "
            "}"
        )


# ======================== MENU BAR BUILDER ========================
def create_menu_bar(window: QtWidgets.QMainWindow, 
                    callbacks: Dict[str, Callable]) -> QtWidgets.QMenuBar:
    """Create main menu bar."""
    menubar = window.menuBar()
    menubar.setObjectName('menuBar')
    
    # FILE MENU
    file_menu = menubar.addMenu("&File")
    
    new_action = file_menu.addAction("&New Assembly")
    new_action.setShortcut("Ctrl+N")
    new_action.triggered.connect(callbacks.get('new', lambda: None))
    
    file_menu.addSeparator()
    
    save_action = file_menu.addAction("&Save Assembly")
    save_action.setShortcut("Ctrl+S")
    save_action.triggered.connect(callbacks.get('save', lambda: None))
    
    export_menu = file_menu.addMenu("&Export")
    export_json = export_menu.addAction("Export as JSON")
    export_json.triggered.connect(callbacks.get('export_json', lambda: None))
    export_stl = export_menu.addAction("Export as STL")
    export_stl.triggered.connect(callbacks.get('export_stl', lambda: None))
    
    file_menu.addSeparator()
    
    exit_action = file_menu.addAction("E&xit")
    exit_action.setShortcut("Ctrl+Q")
    exit_action.triggered.connect(callbacks.get('exit', lambda: None))
    
    # EDIT MENU
    edit_menu = menubar.addMenu("&Edit")
    
    undo_action = edit_menu.addAction("&Undo")
    undo_action.setShortcut("Ctrl+Z")
    undo_action.triggered.connect(callbacks.get('undo', lambda: None))
    undo_action.setObjectName('undo_action')
    
    redo_action = edit_menu.addAction("&Redo")
    redo_action.setShortcut("Ctrl+Y")
    redo_action.triggered.connect(callbacks.get('redo', lambda: None))
    redo_action.setObjectName('redo_action')
    
    edit_menu.addSeparator()
    
    clear_action = edit_menu.addAction("Clear &All")
    clear_action.triggered.connect(callbacks.get('clear_all', lambda: None))
    
    # VIEW MENU
    view_menu = menubar.addMenu("&View")
    
    reset_cam_action = view_menu.addAction("&Reset Camera")
    reset_cam_action.setShortcut("C")
    reset_cam_action.triggered.connect(callbacks.get('reset_camera', lambda: None))
    
    toggle_grid_action = view_menu.addAction("Toggle &Grid")
    toggle_grid_action.setShortcut("G")
    toggle_grid_action.triggered.connect(callbacks.get('toggle_grid', lambda: None))
    
    toggle_3d_action = view_menu.addAction("Toggle 3D &Mode")
    toggle_3d_action.setShortcut("3")
    toggle_3d_action.triggered.connect(callbacks.get('toggle_3d', lambda: None))
    
    # TOOLS MENU
    tools_menu = menubar.addMenu("&Tools")
    
    stats_action = tools_menu.addAction("&Statistics")
    stats_action.triggered.connect(callbacks.get('statistics', lambda: None))
    
    # HELP MENU
    help_menu = menubar.addMenu("&Help")
    
    shortcuts_action = help_menu.addAction("&Help & Shortcuts")
    shortcuts_action.setShortcut("Ctrl+?")
    shortcuts_action.triggered.connect(callbacks.get('help_menu', lambda: None))
    
    about_action = help_menu.addAction("&About")
    about_action.triggered.connect(callbacks.get('about', lambda: None))
    
    return menubar


# ======================== TOOLBAR BUILDER ========================
def create_toolbar(window: QtWidgets.QMainWindow,
                   callbacks: Dict[str, Callable]) -> QtWidgets.QToolBar:
    """Create main toolbar."""
    toolbar = window.addToolBar("Main Toolbar")
    toolbar.setObjectName('mainToolbar')
    toolbar.setIconSize(QtCore.QSize(24, 24))
    toolbar.setMovable(False)
    
    new_btn = toolbar.addAction("New")
    new_btn.setToolTip("Create new assembly (Ctrl+N)")
    new_btn.triggered.connect(callbacks.get('new', lambda: None))
    
    toolbar.addSeparator()
    
    # Start/Stop Exploration (Place button removed - now integrated with library click)
    explore_start_btn = toolbar.addAction("Explore")
    explore_start_btn.setToolTip("Start autonomous exploration (Space)")
    explore_start_btn.triggered.connect(callbacks.get('explore_start', lambda: None))
    
    explore_stop_btn = toolbar.addAction("Stop")
    explore_stop_btn.setToolTip("Stop exploration")
    explore_stop_btn.triggered.connect(callbacks.get('explore_stop', lambda: None))
    explore_stop_btn.setObjectName('explore_stop_btn')
    
    toolbar.addSeparator()
    
    # Undo/Redo
    undo_btn = toolbar.addAction("Undo")
    undo_btn.setToolTip("Undo last action (Ctrl+Z)")
    undo_btn.triggered.connect(callbacks.get('undo', lambda: None))
    undo_btn.setObjectName('undo_btn')
    
    redo_btn = toolbar.addAction("Redo")
    redo_btn.setToolTip("Redo last undone action (Ctrl+Y)")
    redo_btn.triggered.connect(callbacks.get('redo', lambda: None))
    redo_btn.setObjectName('redo_btn')
    
    toolbar.addSeparator()
    
    # Add stretch using a spacer widget (QToolBar doesn't have addStretch)
    spacer = QtWidgets.QWidget()
    spacer.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
    toolbar.addWidget(spacer)
    
    # Help
    help_btn = toolbar.addAction("Help")
    help_btn.setToolTip("Show help (Ctrl+?)")
    help_btn.triggered.connect(callbacks.get('help_menu', lambda: None))
    
    return toolbar


# ======================== HELP DROPDOWN MENU ========================
def create_help_dropdown_menu(parent: QtWidgets.QWidget) -> QtWidgets.QMenu:
    """Create comprehensive help dropdown menu with tooltips."""
    menu = QtWidgets.QMenu(parent)
    menu.setWindowTitle("Help & Tooltips")
    
    # Create tips
    tips = {
        "Polygon Slider": "Control sides (3-12), complexity, and symmetry for generation",
        "Add Polygon": "Add new polygon to assembly with current slider settings",
        "Place Button": "Place selected candidate onto target polyform",
        "Explore": "Start autonomous exploration of placement possibilities",
        "Stop": "Stop the current exploration process",
        "Library": "Double-click to add saved assembly\nRight-click for options\nDrag to organize",
        "Settings Tab": "Workspace parameters (snap tolerance, cell size, 3D mode)",
        "Learning Tab": "Track pattern recognition and success rates",
        "3D View": "Left-drag: rotate | Scroll: zoom | Double-click: focus",
        "Keyboard": "Ctrl+N=New, Ctrl+S=Save, Ctrl+Z=Undo, Ctrl+Q=Exit\nC=Reset Camera, G=Toggle Grid, Space=Explore",
        "Animations": "Watch polyforms fold and transform in real-time",
    }
    
    for title, tip in tips.items():
        action = menu.addAction(title)
        action.setToolTip(tip)
    
    return menu
