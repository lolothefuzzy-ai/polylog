"""
HingeSliderUI - Interactive Qt widget for controlling hinge angles.

Provides:
- Slider-based angle control for each hinge
- Real-time angle display and bounds visualization
- Connect/disconnect slots for constraint solver integration
- Group organization by polyform
"""

import math
from typing import TYPE_CHECKING, Callable, Dict, List, Optional

import numpy as np
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    # Type hints only - avoid circular imports
    from constraint_solver import ForwardKinematics, HingeConstraint

# Lazy imports for runtime
HingeConstraint = None
ForwardKinematics = None


class HingeSliderWidget(QWidget):
    """Single hinge angle control widget."""
    
    angle_changed = Signal(str, int, float)  # polyform_id, edge_idx, angle
    
    def __init__(self, constraint: HingeConstraint, parent=None):
        super().__init__(parent)
        self.constraint = constraint
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        
        # Label: "Edge X"
        self.lbl_edge = QLabel(f"Edge {self.constraint.edge_idx}")
        layout.addWidget(self.lbl_edge, 0)
        
        # Min angle label
        self.lbl_min = QLabel(f"{math.degrees(self.constraint.min_angle):.1f}°")
        layout.addWidget(self.lbl_min, 0)
        
        # Slider
        self.slider = QSlider(Qt.Horizontal)
        min_deg = int(math.degrees(self.constraint.min_angle))
        max_deg = int(math.degrees(self.constraint.max_angle))
        self.slider.setRange(min_deg, max_deg)
        self.slider.setValue(int(math.degrees(self.constraint.current_angle)))
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setTickInterval(max(1, (max_deg - min_deg) // 10))
        self.slider.sliderMoved.connect(self._on_slider_moved)
        layout.addWidget(self.slider, 1)
        
        # Current angle display
        self.lbl_current = QLabel(f"{math.degrees(self.constraint.current_angle):.1f}°")
        self.lbl_current.setMinimumWidth(60)
        layout.addWidget(self.lbl_current, 0)
        
        # Max angle label
        self.lbl_max = QLabel(f"{math.degrees(self.constraint.max_angle):.1f}°")
        layout.addWidget(self.lbl_max, 0)
        
        # Reset button
        self.btn_reset = QPushButton("Reset")
        self.btn_reset.setMaximumWidth(60)
        self.btn_reset.clicked.connect(self._on_reset)
        layout.addWidget(self.btn_reset, 0)
    
    def _on_slider_moved(self):
        """Handle slider movement and update display."""
        slider_deg = self.slider.value()
        angle_rad = math.radians(slider_deg)
        
        # Update label
        self.lbl_current.setText(f"{slider_deg}°")
        
        # Emit signal
        self.angle_changed.emit(
            self.constraint.polyform_id,
            self.constraint.edge_idx,
            angle_rad
        )
    
    def _on_reset(self):
        """Reset slider to default angle."""
        default_deg = int(math.degrees(np.pi / 2))  # 90 degrees
        self.slider.setValue(default_deg)
        self._on_slider_moved()
    
    def set_angle(self, angle_rad: float):
        """Set slider angle externally (in radians)."""
        angle_deg = int(math.degrees(angle_rad))
        self.slider.blockSignals(True)
        self.slider.setValue(angle_deg)
        self.lbl_current.setText(f"{angle_deg}°")
        self.slider.blockSignals(False)
    
    def get_angle(self) -> float:
        """Get current angle in radians."""
        return math.radians(self.slider.value())


class HingeSliderGroup(QGroupBox):
    """Group of hinge sliders for a single polyform."""
    
    angle_changed = Signal(str, int, float)  # polyform_id, edge_idx, angle
    
    def __init__(self, polyform_id: str, constraints: List[HingeConstraint], parent=None):
        super().__init__(f"Polyform: {polyform_id}", parent)
        self.polyform_id = polyform_id
        self.constraints = constraints
        self.sliders: Dict[int, HingeSliderWidget] = {}
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        if not self.constraints:
            layout.addWidget(QLabel("No hinges for this polyform"))
            return
        
        for constraint in self.constraints:
            slider = HingeSliderWidget(constraint, self)
            slider.angle_changed.connect(self._on_angle_changed)
            layout.addWidget(slider)
            self.sliders[constraint.edge_idx] = slider
        
        layout.addStretch()
    
    def _on_angle_changed(self, polyform_id: str, edge_idx: int, angle: float):
        """Forward angle changes to parent."""
        self.angle_changed.emit(polyform_id, edge_idx, angle)
    
    def set_angles(self, angles_dict: Dict[int, float]):
        """Set multiple angles from dict {edge_idx: angle_rad}."""
        for edge_idx, angle in angles_dict.items():
            if edge_idx in self.sliders:
                self.sliders[edge_idx].set_angle(angle)
    
    def get_angles(self) -> Dict[int, float]:
        """Get all angles as {edge_idx: angle_rad}."""
        return {idx: slider.get_angle() for idx, slider in self.sliders.items()}


class HingeSliderUI(QWidget):
    """
    Main widget for controlling all hinges in an assembly.
    
    Features:
    - Organized by polyform
    - Real-time angle display
    - Bounds enforcement
    - Solver integration
    """
    
    angles_updated = Signal()  # Emitted when any angle changes
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.solver: Optional[ForwardKinematics] = None
        self.assembly = None
        self.groups: Dict[str, HingeSliderGroup] = {}
        self._on_angle_changed_callback: Optional[Callable] = None
        self._setup_ui()
    
    def _setup_ui(self):
        """Build UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Header
        header = QHBoxLayout()
        self.lbl_title = QLabel("Hinge Angle Controls")
        font = self.lbl_title.font()
        font.setPointSize(12)
        font.setBold(True)
        self.lbl_title.setFont(font)
        header.addWidget(self.lbl_title)
        
        self.btn_reset_all = QPushButton("Reset All")
        self.btn_reset_all.clicked.connect(self._on_reset_all)
        header.addWidget(self.btn_reset_all)
        
        self.btn_apply = QPushButton("Apply Constraints")
        self.btn_apply.clicked.connect(self._on_apply_constraints)
        header.addWidget(self.btn_apply)
        
        layout.addLayout(header)
        
        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        layout.addWidget(sep)
        
        # Scroll area for groups
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(scroll_widget)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll, 1)
        
        # Status bar
        self.lbl_status = QLabel("Ready")
        self.lbl_status.setStyleSheet("color: #00aa00; font-weight: bold;")
        layout.addWidget(self.lbl_status)
    
    def set_solver(self, solver: ForwardKinematics, assembly):
        """Set the constraint solver and assembly to control."""
        self.solver = solver
        self.assembly = assembly
        self._rebuild_ui()
    
    def set_on_angle_changed(self, callback: Callable):
        """Set callback to run when angles change."""
        self._on_angle_changed_callback = callback
    
    def _rebuild_ui(self):
        """Rebuild slider groups based on current solver constraints."""
        # Clear existing groups
        for group in self.groups.values():
            group.deleteLater()
        self.groups.clear()
        
        # Clear scroll layout
        while self.scroll_layout.count():
            self.scroll_layout.takeAt(0).widget().deleteLater()
        
        if not self.solver or not self.assembly:
            self.lbl_status.setText("No solver or assembly set")
            return
        
        # Group constraints by polyform_id
        poly_constraints: Dict[str, List[HingeConstraint]] = {}
        for constraint in self.solver.constraints.values():
            if constraint.polyform_id not in poly_constraints:
                poly_constraints[constraint.polyform_id] = []
            poly_constraints[constraint.polyform_id].append(constraint)
        
        # Create groups
        for poly_id in sorted(poly_constraints.keys()):
            constraints = sorted(poly_constraints[poly_id], key=lambda c: c.edge_idx)
            group = HingeSliderGroup(poly_id, constraints, self)
            group.angle_changed.connect(self._on_angle_changed)
            self.scroll_layout.addWidget(group)
            self.groups[poly_id] = group
        
        self.scroll_layout.addStretch()
        
        if self.groups:
            self.lbl_status.setText(f"Controlling {len(self.groups)} polyforms")
        else:
            self.lbl_status.setText("No hinges to control")
    
    @Slot(str, int, float)
    def _on_angle_changed(self, polyform_id: str, edge_idx: int, angle: float):
        """Handle angle change from slider."""
        if not self.solver:
            return  # Silently ignore if no solver
        
        # Update constraint in solver
        self.solver.set_angle(polyform_id, edge_idx, angle)
        
        # Call external callback if set
        if self._on_angle_changed_callback:
            self._on_angle_changed_callback(polyform_id, edge_idx, angle)
        
        # Emit signal for external listeners
        self.angles_updated.emit()
    
    @Slot()
    def _on_reset_all(self):
        """Reset all sliders to default angles."""
        for group in self.groups.values():
            for slider in group.sliders.values():
                slider._on_reset()
        self.lbl_status.setText("All sliders reset")
    
    @Slot()
    def _on_apply_constraints(self):
        """Apply all current constraints to the assembly."""
        if not self.solver or not self.assembly:
            self.lbl_status.setText("ERROR: No solver or assembly")
            return
        
        try:
            converged = self.solver.solve(max_iterations=10)
            if converged:
                self.lbl_status.setText("Constraints applied successfully")
            else:
                self.lbl_status.setText("WARNING: Did not converge")
        except Exception as e:
            self.lbl_status.setText(f"ERROR: {str(e)[:50]}")
    
    def get_all_angles(self) -> Dict[str, Dict[int, float]]:
        """Get all angles as nested dict {polyform_id: {edge_idx: angle_rad}}."""
        if not self.groups:
            return {}
        return {
            poly_id: group.get_angles()
            for poly_id, group in self.groups.items()
        }
    
    def set_all_angles(self, angles_dict: Dict[str, Dict[int, float]]):
        """Set all angles from nested dict."""
        if not angles_dict or not self.groups:
            return
        for poly_id, edge_angles in angles_dict.items():
            if poly_id in self.groups:
                self.groups[poly_id].set_angles(edge_angles)
    
    def refresh(self):
        """Rebuild UI (call after assembly changes)."""
        if not self.solver or not self.assembly:
            return  # No solver/assembly set yet
        self._rebuild_ui()


# Initialize lazy imports at module load time
def _init_imports():
    """Load constraint_solver imports after module initialization."""
    global HingeConstraint, ForwardKinematics
    try:
        from constraint_solver import ForwardKinematics as FK
        from constraint_solver import HingeConstraint as HC
        HingeConstraint = HC
        ForwardKinematics = FK
    except ImportError as e:
        import warnings
        warnings.warn(f"Could not import constraint_solver: {e}")

_init_imports()


# Utility functions for integrating with desktop app

def create_hinge_slider_dock(solver, assembly,
                             on_angle_changed: Optional[Callable] = None) -> HingeSliderUI:
    """
    Create a hinge slider UI for a dock widget.
    
    Args:
        solver: ForwardKinematics solver
        assembly: Assembly object
        on_angle_changed: Optional callback(polyform_id, edge_idx, angle)
    
    Returns:
        HingeSliderUI widget ready for docking
    """
    ui = HingeSliderUI()
    ui.set_solver(solver, assembly)
    if on_angle_changed:
        ui.set_on_angle_changed(on_angle_changed)
    return ui
