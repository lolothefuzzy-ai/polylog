"""
Generator Selection Panel for Polylog GUI.

Provides UI controls for:
- Selecting generator type from registry
- Configuring generator-specific parameters
- Viewing generator statistics
- Toggling 3D mode
"""

from typing import Dict, Any, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QComboBox, QSpinBox, QDoubleSpinBox, QPushButton, QCheckBox,
    QFormLayout, QFrame
)
from PySide6.QtCore import Signal, Qt

from generator_protocol import get_generator_registry, GeneratorCapability


class GeneratorPanel(QWidget):
    """
    Panel for selecting and configuring polyform generators.
    
    Signals:
        generator_selected(str): Emitted when a generator is selected
        generate_requested(dict): Emitted when user requests generation with parameters
        mode_3d_toggled(bool): Emitted when 3D mode is toggled
    """
    
    generator_selected = Signal(str)
    generate_requested = Signal(dict)
    mode_3d_toggled = Signal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.registry = get_generator_registry()
        self.current_generator = None
        self.current_params = {}
        self._setup_ui()
        self._load_generators()
    
    def _setup_ui(self):
        """Build the UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # === Generator Selection Group ===
        selection_group = QGroupBox("Generator Selection")
        selection_layout = QVBoxLayout()
        
        # Generator dropdown
        gen_layout = QHBoxLayout()
        gen_layout.addWidget(QLabel("Generator:"))
        
        self.generator_combo = QComboBox()
        self.generator_combo.setToolTip("Select which generator to use for creating polyforms")
        self.generator_combo.currentTextChanged.connect(self._on_generator_changed)
        gen_layout.addWidget(self.generator_combo, 1)
        selection_layout.addLayout(gen_layout)
        
        # 3D Mode toggle
        self.mode_3d_checkbox = QCheckBox("Enable 3D Mode")
        self.mode_3d_checkbox.setToolTip("Generate polyforms with 3D meshes (required for fold validation)")
        self.mode_3d_checkbox.setChecked(True)
        self.mode_3d_checkbox.toggled.connect(self._on_3d_mode_toggled)
        selection_layout.addWidget(self.mode_3d_checkbox)
        
        # Capabilities display
        self.capabilities_label = QLabel("Capabilities: None")
        self.capabilities_label.setWordWrap(True)
        self.capabilities_label.setStyleSheet("color: #666; font-size: 10px;")
        selection_layout.addWidget(self.capabilities_label)
        
        selection_group.setLayout(selection_layout)
        layout.addWidget(selection_group)
        
        # === Parameters Group (Dynamic) ===
        self.params_group = QGroupBox("Parameters")
        self.params_layout = QFormLayout()
        self.params_group.setLayout(self.params_layout)
        layout.addWidget(self.params_group)
        
        # === Generation Controls ===
        controls_layout = QHBoxLayout()
        
        self.generate_btn = QPushButton("Generate")
        self.generate_btn.setToolTip("Generate polyforms with current parameters (or press G)")
        self.generate_btn.clicked.connect(self._on_generate_clicked)
        controls_layout.addWidget(self.generate_btn)
        
        self.clear_btn = QPushButton("Clear Params")
        self.clear_btn.setToolTip("Reset parameters to default values")
        self.clear_btn.clicked.connect(self._on_clear_params)
        controls_layout.addWidget(self.clear_btn)
        
        layout.addLayout(controls_layout)
        
        # === Statistics Group ===
        self.stats_group = QGroupBox("Statistics")
        stats_layout = QFormLayout()
        
        self.total_label = QLabel("0")
        stats_layout.addRow("Total Generated:", self.total_label)
        
        self.success_rate_label = QLabel("0%")
        stats_layout.addRow("Success Rate:", self.success_rate_label)
        
        self.avg_time_label = QLabel("0ms")
        stats_layout.addRow("Avg Time:", self.avg_time_label)
        
        self.stats_group.setLayout(stats_layout)
        layout.addWidget(self.stats_group)
        
        layout.addStretch()
    
    def _load_generators(self):
        """Load available generators from registry."""
        generators = self.registry.list_generators()
        self.generator_combo.clear()
        
        if not generators:
            self.generator_combo.addItem("(No generators available)")
            self.generator_combo.setEnabled(False)
            return
        
        for gen_name in sorted(generators):
            # Get capabilities for display
            gen_class = self.registry.get(gen_name)
            caps = getattr(gen_class, '_capabilities', [])
            display_name = f"{gen_name.replace('_', ' ').title()}"
            
            self.generator_combo.addItem(display_name, gen_name)
        
        print(f"✓ Loaded {len(generators)} generators")
    
    def _on_generator_changed(self, display_name: str):
        """Handle generator selection change."""
        if not display_name or display_name.startswith("("):
            return
        
        gen_name = self.generator_combo.currentData()
        if not gen_name:
            return
        
        self.current_generator = gen_name
        self.generator_selected.emit(gen_name)
        
        # Update capabilities display
        gen_class = self.registry.get(gen_name)
        if gen_class:
            caps = getattr(gen_class, '_capabilities', [])
            caps_text = ", ".join(caps) if caps else "None"
            self.capabilities_label.setText(f"Capabilities: {caps_text}")
        
        # Load appropriate parameter controls
        self._load_parameters(gen_name)
        
        print(f"✓ Selected generator: {gen_name}")
    
    def _load_parameters(self, gen_name: str):
        """Load parameter controls for the selected generator."""
        # Clear existing params
        while self.params_layout.rowCount() > 0:
            self.params_layout.removeRow(0)
        
        self.current_params = {}
        
        # Define parameters for each generator type
        if gen_name == 'basic':
            # PolyformGenerationEngine parameters
            self._add_combo_param("method", ["single", "range", "template", "pattern"], "single")
            self._add_spin_param("sides", 3, 12, 4)
            self._add_spin_param("min_sides", 3, 12, 3)
            self._add_spin_param("max_sides", 3, 12, 8)
            self._add_double_param("scale", 0.1, 10.0, 1.0, 0.1)
            self._add_double_param("thickness", 0.01, 1.0, 0.15, 0.01)
            
        elif gen_name == 'random_assembly':
            # RandomAssemblyGenerator parameters
            self._add_spin_param("count", 1, 50, 5)
            self._add_combo_param("distribution", ["uniform", "normal", "custom"], "uniform")
            self._add_double_param("spread", 1.0, 20.0, 10.0, 1.0)
            
        elif gen_name == 'random_polyform':
            # RandomPolyformGenerator parameters
            self._add_spin_param("count", 1, 50, 5)
            self._add_spin_param("min_sides", 3, 12, 3)
            self._add_spin_param("max_sides", 3, 12, 8)
            self._add_combo_param("distribution", ["uniform", "weighted", "gaussian"], "uniform")
            
        elif gen_name == 'physics':
            # PhysicsBasedGenerator parameters
            self._add_double_param("target_height", 1.0, 50.0, 10.0, 1.0)
            self._add_spin_param("min_polygons", 1, 20, 3)
            self._add_double_param("base_radius", 1.0, 20.0, 5.0, 0.5)
        
        else:
            # Generic parameters
            self._add_spin_param("count", 1, 20, 5)
    
    def _add_spin_param(self, name: str, min_val: int, max_val: int, default: int):
        """Add an integer spin box parameter."""
        spinbox = QSpinBox()
        spinbox.setRange(min_val, max_val)
        spinbox.setValue(default)
        spinbox.valueChanged.connect(lambda v: self._update_param(name, v))
        self.params_layout.addRow(f"{name.replace('_', ' ').title()}:", spinbox)
        self.current_params[name] = default
    
    def _add_double_param(self, name: str, min_val: float, max_val: float,
                          default: float, step: float = 0.1):
        """Add a double spin box parameter."""
        spinbox = QDoubleSpinBox()
        spinbox.setRange(min_val, max_val)
        spinbox.setValue(default)
        spinbox.setSingleStep(step)
        spinbox.setDecimals(2)
        spinbox.valueChanged.connect(lambda v: self._update_param(name, v))
        self.params_layout.addRow(f"{name.replace('_', ' ').title()}:", spinbox)
        self.current_params[name] = default
    
    def _add_combo_param(self, name: str, options: list, default: str):
        """Add a combo box parameter."""
        combo = QComboBox()
        combo.addItems(options)
        combo.setCurrentText(default)
        combo.currentTextChanged.connect(lambda v: self._update_param(name, v))
        self.params_layout.addRow(f"{name.replace('_', ' ').title()}:", combo)
        self.current_params[name] = default
    
    def _update_param(self, name: str, value: Any):
        """Update parameter value."""
        self.current_params[name] = value
    
    def _on_3d_mode_toggled(self, checked: bool):
        """Handle 3D mode toggle."""
        self.mode_3d_toggled.emit(checked)
        print(f"✓ 3D mode: {'enabled' if checked else 'disabled'}")
    
    def _on_generate_clicked(self):
        """Handle generate button click."""
        if not self.current_generator:
            print("❌ No generator selected")
            return
        
        params = dict(self.current_params)
        params['enable_3d_mode'] = self.mode_3d_checkbox.isChecked()
        
        print(f"✓ Requesting generation: {self.current_generator} with {params}")
        self.generate_requested.emit(params)
    
    def _on_clear_params(self):
        """Clear/reset parameters to defaults."""
        self._load_parameters(self.current_generator)
        print("✓ Parameters reset to defaults")
    
    def update_statistics(self, stats: Dict[str, Any]):
        """Update the statistics display."""
        self.total_label.setText(str(stats.get('total_generated', 0)))
        
        success_rate = stats.get('success_rate', 0.0)
        self.success_rate_label.setText(f"{success_rate * 100:.1f}%")
        
        avg_time = stats.get('avg_time', 0.0)
        self.avg_time_label.setText(f"{avg_time * 1000:.1f}ms")
    
    def get_current_generator(self) -> Optional[str]:
        """Get the currently selected generator name."""
        return self.current_generator
    
    def get_parameters(self) -> Dict[str, Any]:
        """Get current parameters."""
        params = dict(self.current_params)
        params['enable_3d_mode'] = self.mode_3d_checkbox.isChecked()
        return params
    
    def is_3d_mode(self) -> bool:
        """Check if 3D mode is enabled."""
        return self.mode_3d_checkbox.isChecked()
