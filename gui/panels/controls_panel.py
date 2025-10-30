"""
Polygon parameter control panel with sliders.

Provides real-time polygon generation parameters:
- Sides: 3-12 sides
- Complexity: 0-1 (0=simple, 1=complex)
- Symmetry: 0-1 (0=none, 1=full)
"""

from PySide6.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QSpinBox, QPushButton
)
from PySide6.QtCore import Qt, Signal


class ControlsPanel(QGroupBox):
    """Panel for polygon influence parameter controls."""
    
    # Signals
    parameters_changed = Signal(dict)
    add_polygon_clicked = Signal()
    polygon_generated = Signal(dict)  # Emits generated polygon data
    clear_requested = Signal()  # Request to clear all polygons
    
    def __init__(self):
        super().__init__("Polygon Influence")
        self.setStyleSheet("QGroupBox { font-weight: bold; }")
        
        layout = QVBoxLayout()
        
        # Sides slider (3-12)
        sides_layout = QHBoxLayout()
        sides_layout.addWidget(QLabel("Sides:"))
        self.sides_slider = QSlider(Qt.Horizontal)
        self.sides_slider.setMinimum(3)
        self.sides_slider.setMaximum(12)
        self.sides_slider.setValue(5)
        self.sides_slider.setTickPosition(QSlider.TicksBelow)
        self.sides_slider.setTickInterval(1)
        self.sides_slider.valueChanged.connect(self._on_value_changed)
        sides_layout.addWidget(self.sides_slider, 1)
        
        self.sides_display = QSpinBox()
        self.sides_display.setMinimum(3)
        self.sides_display.setMaximum(12)
        self.sides_display.setValue(5)
        self.sides_display.setMaximumWidth(50)
        self.sides_display.valueChanged.connect(self._sync_sides)
        sides_layout.addWidget(self.sides_display)
        layout.addLayout(sides_layout)
        
        # Complexity slider (0-100 representing 0.0-1.0)
        complexity_layout = QHBoxLayout()
        complexity_layout.addWidget(QLabel("Complexity:"))
        self.complexity_slider = QSlider(Qt.Horizontal)
        self.complexity_slider.setMinimum(0)
        self.complexity_slider.setMaximum(100)
        self.complexity_slider.setValue(50)
        self.complexity_slider.setTickPosition(QSlider.TicksBelow)
        self.complexity_slider.setTickInterval(10)
        self.complexity_slider.valueChanged.connect(self._on_value_changed)
        complexity_layout.addWidget(self.complexity_slider, 1)
        
        self.complexity_display = QLabel("0.50")
        self.complexity_display.setMaximumWidth(40)
        self.complexity_display.setAlignment(Qt.AlignRight)
        complexity_layout.addWidget(self.complexity_display)
        layout.addLayout(complexity_layout)
        
        # Symmetry slider (0-100 representing 0.0-1.0)
        symmetry_layout = QHBoxLayout()
        symmetry_layout.addWidget(QLabel("Symmetry:"))
        self.symmetry_slider = QSlider(Qt.Horizontal)
        self.symmetry_slider.setMinimum(0)
        self.symmetry_slider.setMaximum(100)
        self.symmetry_slider.setValue(50)
        self.symmetry_slider.setTickPosition(QSlider.TicksBelow)
        self.symmetry_slider.setTickInterval(10)
        self.symmetry_slider.valueChanged.connect(self._on_value_changed)
        symmetry_layout.addWidget(self.symmetry_slider, 1)
        
        self.symmetry_display = QLabel("0.50")
        self.symmetry_display.setMaximumWidth(40)
        self.symmetry_display.setAlignment(Qt.AlignRight)
        symmetry_layout.addWidget(self.symmetry_display)
        layout.addLayout(symmetry_layout)
        
        layout.addSpacing(10)
        
        # Buttons layout
        buttons_layout = QHBoxLayout()
        
        # Add polygon button
        self.add_btn = QPushButton("Add Polygon")
        self.add_btn.clicked.connect(self._on_add_clicked)
        buttons_layout.addWidget(self.add_btn)
        
        # Clear button
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self._on_clear_clicked)
        buttons_layout.addWidget(self.clear_btn)
        
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
        print("✓ ControlsPanel initialized")
    
    def _on_value_changed(self):
        """Handle slider value changes."""
        # Update display labels
        complexity = self.complexity_slider.value() / 100.0
        symmetry = self.symmetry_slider.value() / 100.0
        
        self.complexity_display.setText(f"{complexity:.2f}")
        self.symmetry_display.setText(f"{symmetry:.2f}")
        
        # Sync slider and spinbox
        self.sides_slider.blockSignals(True)
        self.sides_slider.setValue(self.sides_display.value())
        self.sides_slider.blockSignals(False)
        
        # Emit signal with current parameters
        params = {
            'sides': self.sides_display.value(),
            'complexity': complexity,
            'symmetry': symmetry,
        }
        self.parameters_changed.emit(params)
        
        # Generate preview polygon
        self._generate_preview(params)
    
    def _sync_sides(self):
        """Sync spinbox changes to slider."""
        self.sides_slider.blockSignals(True)
        self.sides_slider.setValue(self.sides_display.value())
        self.sides_slider.blockSignals(False)
        self._on_value_changed()
    
    def _on_add_clicked(self):
        """Handle add polygon button click."""
        # Get current parameters
        params = self.get_parameters()
        
        # Generate polygon
        try:
            from random_assembly_generator import RandomAssemblyGenerator
            from gui.utils import format_polygon_for_display
            
            generator = RandomAssemblyGenerator()
            polygon = generator.generate_random_assembly(
                num_polyforms=1,
                allow_types=[params['sides']],
                use_3d=True
            )[0]
            
            # Format for display
            formatted = format_polygon_for_display(polygon)
            if formatted:
                # Emit polygon data
                self.polygon_generated.emit(formatted)
            
        except Exception as e:
            print(f"❌ Error generating polygon: {e}")
            import traceback
            traceback.print_exc()
        
        # Also emit signals
        self.add_polygon_clicked.emit()
    
    def _on_clear_clicked(self):
        """Handle clear button click."""
        self.clear_requested.emit()
    
    def get_parameters(self) -> dict:
        """Get current polygon parameters."""
        return {
            'sides': self.sides_display.value(),
            'complexity': self.complexity_slider.value() / 100.0,
            'symmetry': self.symmetry_slider.value() / 100.0,
        }
    
    def set_parameters(self, params: dict):
        """Set polygon parameters."""
        if 'sides' in params:
            self.sides_display.setValue(params['sides'])
        if 'complexity' in params:
            self.complexity_slider.setValue(int(params['complexity'] * 100))
        if 'symmetry' in params:
            self.symmetry_slider.setValue(int(params['symmetry'] * 100))
    
    def _generate_preview(self, params: dict):
        """Generate preview polygon silently (no emission, used by viewport)."""
        try:
            from random_assembly_generator import RandomAssemblyGenerator
            from gui.utils import format_polygon_for_display
            
            generator = RandomAssemblyGenerator()
            polygon = generator.generate_random_assembly(
                num_polyforms=1,
                allow_types=[params['sides']],
                use_3d=True
            )[0]
            
            formatted = format_polygon_for_display(polygon)
            if formatted:
                # Emit signal for live preview
                self.polygon_generated.emit(formatted)
        except Exception:
            # Silently fail - preview is optional
            pass
