"""
Settings Dialog for Polylog

Provides comprehensive settings including:
- Visual preferences (materials, lighting, rendering)
- Color sensitivity modes (colorblind-friendly)
- Auto-bonding configuration
- Performance options
- Accessibility features
"""
from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtCore import Qt, Signal
from typing import Dict, Any
import json
import os


class SettingsDialog(QtWidgets.QDialog):
    """
    Comprehensive settings dialog with tabbed interface.
    
    Tabs:
    - Visual: Materials, lighting, render quality
    - Colors: Color schemes, colorblind modes
    - Auto-Bonding: Confidence thresholds, learning
    - Performance: Frame rate, caching
    - Accessibility: High contrast, text size
    """
    
    settings_changed = Signal(dict)
    
    def __init__(self, parent=None, current_settings: Dict[str, Any] = None):
        super().__init__(parent)
        self.setWindowTitle("Polylog Settings")
        self.setModal(True)
        self.setMinimumSize(600, 500)
        
        # Load or use defaults
        self.settings = current_settings or self._default_settings()
        
        self._build_ui()
        self._load_values()
    
    def _default_settings(self) -> Dict[str, Any]:
        """Default settings values."""
        return {
            # Visual settings
            'visual_preset': 'default',
            'material_quality': 'medium',
            'enable_shadows': True,
            'enable_edge_highlighting': True,
            'edge_width': 2.0,
            'lighting_intensity': 1.0,
            
            # Color settings
            'color_mode': 'normal',
            'colorblind_mode': 'none',  # none, deuteranopia, protanopia, tritanopia
            'high_contrast': False,
            'custom_palette': None,
            
            # Auto-bonding settings
            'auto_bond_enabled': True,
            'auto_bond_confidence': 0.8,
            'show_bond_suggestions': True,
            'learn_from_manual_bonds': True,
            
            # Performance settings
            'target_fps': 60,
            'enable_vsync': True,
            'cache_patterns': True,
            'max_undo_history': 50,
            
            # Accessibility
            'font_size': 'medium',
            'screen_reader_support': False,
            'keyboard_shortcuts': True,
        }
    
    def _build_ui(self):
        """Build the tabbed settings interface."""
        layout = QtWidgets.QVBoxLayout(self)
        
        # Tab widget
        self.tabs = QtWidgets.QTabWidget()
        layout.addWidget(self.tabs)
        
        # Create tabs
        self.tabs.addTab(self._create_visual_tab(), "Visual")
        self.tabs.addTab(self._create_colors_tab(), "Colors & Themes")
        self.tabs.addTab(self._create_bonding_tab(), "Auto-Bonding")
        self.tabs.addTab(self._create_performance_tab(), "Performance")
        self.tabs.addTab(self._create_accessibility_tab(), "Accessibility")
        
        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        
        self.btn_reset = QtWidgets.QPushButton("Reset to Defaults")
        self.btn_reset.clicked.connect(self._reset_to_defaults)
        button_layout.addWidget(self.btn_reset)
        
        button_layout.addStretch()
        
        self.btn_cancel = QtWidgets.QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(self.btn_cancel)
        
        self.btn_apply = QtWidgets.QPushButton("Apply")
        self.btn_apply.clicked.connect(self._apply_settings)
        button_layout.addWidget(self.btn_apply)
        
        self.btn_ok = QtWidgets.QPushButton("OK")
        self.btn_ok.clicked.connect(self._save_and_close)
        self.btn_ok.setDefault(True)
        button_layout.addWidget(self.btn_ok)
        
        layout.addLayout(button_layout)
    
    def _create_visual_tab(self) -> QtWidgets.QWidget:
        """Visual settings tab."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        
        # Visual Preset
        preset_group = QtWidgets.QGroupBox("Visual Style Preset")
        preset_layout = QtWidgets.QFormLayout(preset_group)
        
        self.combo_preset = QtWidgets.QComboBox()
        self.combo_preset.addItems([
            'Default', 'Blueprint', 'Render', 'Glass', 'Metal', 'Paper'
        ])
        preset_layout.addRow("Preset:", self.combo_preset)
        
        # Preview label
        self.lbl_preset_preview = QtWidgets.QLabel("Balanced visualization with plastic materials")
        self.lbl_preset_preview.setWordWrap(True)
        self.lbl_preset_preview.setStyleSheet("color: #888; font-style: italic;")
        preset_layout.addRow("", self.lbl_preset_preview)
        
        self.combo_preset.currentTextChanged.connect(self._update_preset_preview)
        
        layout.addWidget(preset_group)
        
        # Material Quality
        quality_group = QtWidgets.QGroupBox("Rendering Quality")
        quality_layout = QtWidgets.QFormLayout(quality_group)
        
        self.combo_quality = QtWidgets.QComboBox()
        self.combo_quality.addItems(['Low', 'Medium', 'High', 'Ultra'])
        quality_layout.addRow("Material Quality:", self.combo_quality)
        
        self.chk_shadows = QtWidgets.QCheckBox("Enable Shadows")
        quality_layout.addRow("", self.chk_shadows)
        
        self.chk_edge_highlight = QtWidgets.QCheckBox("Highlight Edges")
        quality_layout.addRow("", self.chk_edge_highlight)
        
        layout.addWidget(quality_group)
        
        # Edge Settings
        edge_group = QtWidgets.QGroupBox("Edge Display")
        edge_layout = QtWidgets.QFormLayout(edge_group)
        
        self.slider_edge_width = QtWidgets.QSlider(Qt.Horizontal)
        self.slider_edge_width.setRange(1, 5)
        self.slider_edge_width.setValue(2)
        self.lbl_edge_width = QtWidgets.QLabel("2.0")
        self.slider_edge_width.valueChanged.connect(
            lambda v: self.lbl_edge_width.setText(f"{v}.0")
        )
        
        edge_width_layout = QtWidgets.QHBoxLayout()
        edge_width_layout.addWidget(self.slider_edge_width)
        edge_width_layout.addWidget(self.lbl_edge_width)
        edge_layout.addRow("Edge Width:", edge_width_layout)
        
        layout.addWidget(edge_group)
        
        # Lighting
        light_group = QtWidgets.QGroupBox("Lighting")
        light_layout = QtWidgets.QFormLayout(light_group)
        
        self.slider_light_intensity = QtWidgets.QSlider(Qt.Horizontal)
        self.slider_light_intensity.setRange(50, 150)
        self.slider_light_intensity.setValue(100)
        self.lbl_light_intensity = QtWidgets.QLabel("100%")
        self.slider_light_intensity.valueChanged.connect(
            lambda v: self.lbl_light_intensity.setText(f"{v}%")
        )
        
        light_layout.addRow("Intensity:", self.slider_light_intensity)
        light_layout.addRow("", self.lbl_light_intensity)
        
        layout.addWidget(light_group)
        
        layout.addStretch()
        return widget
    
    def _create_colors_tab(self) -> QtWidgets.QWidget:
        """Color and theme settings tab."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        
        # Color Mode
        mode_group = QtWidgets.QGroupBox("Color Display Mode")
        mode_layout = QtWidgets.QFormLayout(mode_group)
        
        self.combo_color_mode = QtWidgets.QComboBox()
        self.combo_color_mode.addItems([
            'Normal', 'Stability-Based', 'Type-Based', 'Custom'
        ])
        mode_layout.addRow("Mode:", self.combo_color_mode)
        
        layout.addWidget(mode_group)
        
        # Colorblind Accessibility
        cb_group = QtWidgets.QGroupBox("Colorblind-Friendly Modes")
        cb_layout = QtWidgets.QVBoxLayout(cb_group)
        
        cb_info = QtWidgets.QLabel(
            "Select a mode to adjust colors for better visibility:"
        )
        cb_info.setWordWrap(True)
        cb_layout.addWidget(cb_info)
        
        self.radio_cb_none = QtWidgets.QRadioButton("None (Normal Colors)")
        self.radio_cb_none.setChecked(True)
        cb_layout.addWidget(self.radio_cb_none)
        
        self.radio_cb_deuteranopia = QtWidgets.QRadioButton(
            "Deuteranopia (Red-Green, most common)"
        )
        cb_layout.addWidget(self.radio_cb_deuteranopia)
        
        self.radio_cb_protanopia = QtWidgets.QRadioButton(
            "Protanopia (Red-Green, less common)"
        )
        cb_layout.addWidget(self.radio_cb_protanopia)
        
        self.radio_cb_tritanopia = QtWidgets.QRadioButton(
            "Tritanopia (Blue-Yellow)"
        )
        cb_layout.addWidget(self.radio_cb_tritanopia)
        
        self.radio_cb_monochrome = QtWidgets.QRadioButton(
            "Monochrome (Grayscale only)"
        )
        cb_layout.addWidget(self.radio_cb_monochrome)
        
        layout.addWidget(cb_group)
        
        # High Contrast
        contrast_group = QtWidgets.QGroupBox("Contrast")
        contrast_layout = QtWidgets.QVBoxLayout(contrast_group)
        
        self.chk_high_contrast = QtWidgets.QCheckBox("Enable High Contrast Mode")
        self.chk_high_contrast.setToolTip(
            "Increases contrast between elements for better visibility"
        )
        contrast_layout.addWidget(self.chk_high_contrast)
        
        layout.addWidget(contrast_group)
        
        layout.addStretch()
        return widget
    
    def _create_bonding_tab(self) -> QtWidgets.QWidget:
        """Auto-bonding settings tab."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        
        # Enable/Disable
        enable_group = QtWidgets.QGroupBox("Auto-Bonding")
        enable_layout = QtWidgets.QVBoxLayout(enable_group)
        
        self.chk_auto_bond = QtWidgets.QCheckBox("Enable Automatic Bonding")
        self.chk_auto_bond.setToolTip(
            "Automatically create bonds between edges when polygons are placed"
        )
        enable_layout.addWidget(self.chk_auto_bond)
        
        layout.addWidget(enable_group)
        
        # Confidence Settings
        conf_group = QtWidgets.QGroupBox("Confidence Threshold")
        conf_layout = QtWidgets.QFormLayout(conf_group)
        
        conf_info = QtWidgets.QLabel(
            "Minimum confidence required to automatically create a bond:"
        )
        conf_info.setWordWrap(True)
        conf_layout.addRow("", conf_info)
        
        self.slider_confidence = QtWidgets.QSlider(Qt.Horizontal)
        self.slider_confidence.setRange(50, 95)
        self.slider_confidence.setValue(80)
        self.lbl_confidence = QtWidgets.QLabel("80%")
        self.slider_confidence.valueChanged.connect(
            lambda v: self.lbl_confidence.setText(f"{v}%")
        )
        
        conf_slider_layout = QtWidgets.QHBoxLayout()
        conf_slider_layout.addWidget(self.slider_confidence)
        conf_slider_layout.addWidget(self.lbl_confidence)
        conf_layout.addRow("Threshold:", conf_slider_layout)
        
        layout.addWidget(conf_group)
        
        # Learning Settings
        learn_group = QtWidgets.QGroupBox("Learning Options")
        learn_layout = QtWidgets.QVBoxLayout(learn_group)
        
        self.chk_show_suggestions = QtWidgets.QCheckBox("Show Bond Suggestions")
        self.chk_show_suggestions.setToolTip(
            "Display suggested bonds as visual hints"
        )
        learn_layout.addWidget(self.chk_show_suggestions)
        
        self.chk_learn_manual = QtWidgets.QCheckBox("Learn from Manual Bonds")
        self.chk_learn_manual.setToolTip(
            "Record manual bonds to improve future suggestions"
        )
        learn_layout.addWidget(self.chk_learn_manual)
        
        # Statistics button
        self.btn_bonding_stats = QtWidgets.QPushButton("View Learned Patterns...")
        self.btn_bonding_stats.clicked.connect(self._show_bonding_stats)
        learn_layout.addWidget(self.btn_bonding_stats)
        
        layout.addWidget(learn_group)
        
        layout.addStretch()
        return widget
    
    def _create_performance_tab(self) -> QtWidgets.QWidget:
        """Performance settings tab."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        
        # Frame Rate
        fps_group = QtWidgets.QGroupBox("Frame Rate")
        fps_layout = QtWidgets.QFormLayout(fps_group)
        
        self.combo_fps = QtWidgets.QComboBox()
        self.combo_fps.addItems(['30 FPS', '60 FPS', '120 FPS', 'Unlimited'])
        fps_layout.addRow("Target FPS:", self.combo_fps)
        
        self.chk_vsync = QtWidgets.QCheckBox("Enable V-Sync")
        fps_layout.addRow("", self.chk_vsync)
        
        layout.addWidget(fps_group)
        
        # Caching
        cache_group = QtWidgets.QGroupBox("Caching")
        cache_layout = QtWidgets.QVBoxLayout(cache_group)
        
        self.chk_cache_patterns = QtWidgets.QCheckBox("Cache Bond Patterns")
        cache_layout.addWidget(self.chk_cache_patterns)
        
        self.chk_cache_renders = QtWidgets.QCheckBox("Cache Preview Renders")
        cache_layout.addWidget(self.chk_cache_renders)
        
        layout.addWidget(cache_group)
        
        # History
        history_group = QtWidgets.QGroupBox("Undo/Redo")
        history_layout = QtWidgets.QFormLayout(history_group)
        
        self.spin_undo_history = QtWidgets.QSpinBox()
        self.spin_undo_history.setRange(10, 200)
        self.spin_undo_history.setValue(50)
        self.spin_undo_history.setSuffix(" actions")
        history_layout.addRow("Max History:", self.spin_undo_history)
        
        layout.addWidget(history_group)
        
        layout.addStretch()
        return widget
    
    def _create_accessibility_tab(self) -> QtWidgets.QWidget:
        """Accessibility settings tab."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        
        # Font Size
        font_group = QtWidgets.QGroupBox("Text Size")
        font_layout = QtWidgets.QFormLayout(font_group)
        
        self.combo_font_size = QtWidgets.QComboBox()
        self.combo_font_size.addItems(['Small', 'Medium', 'Large', 'Extra Large'])
        font_layout.addRow("UI Font Size:", self.combo_font_size)
        
        layout.addWidget(font_group)
        
        # Input
        input_group = QtWidgets.QGroupBox("Input Options")
        input_layout = QtWidgets.QVBoxLayout(input_group)
        
        self.chk_keyboard_shortcuts = QtWidgets.QCheckBox("Enable Keyboard Shortcuts")
        input_layout.addWidget(self.chk_keyboard_shortcuts)
        
        self.chk_screen_reader = QtWidgets.QCheckBox("Screen Reader Support (Experimental)")
        input_layout.addWidget(self.chk_screen_reader)
        
        layout.addWidget(input_group)
        
        # Reset View Button
        reset_group = QtWidgets.QGroupBox("Quick Actions")
        reset_layout = QtWidgets.QVBoxLayout(reset_group)
        
        self.btn_reset_camera = QtWidgets.QPushButton("Reset Camera to Default")
        reset_layout.addWidget(self.btn_reset_camera)
        
        layout.addWidget(reset_group)
        
        layout.addStretch()
        return widget
    
    def _load_values(self):
        """Load current settings into UI controls."""
        s = self.settings
        
        # Visual tab
        preset_map = {
            'default': 0, 'blueprint': 1, 'render': 2,
            'glass': 3, 'metal': 4, 'paper': 5
        }
        self.combo_preset.setCurrentIndex(preset_map.get(s['visual_preset'], 0))
        
        quality_map = {'low': 0, 'medium': 1, 'high': 2, 'ultra': 3}
        self.combo_quality.setCurrentIndex(quality_map.get(s['material_quality'], 1))
        
        self.chk_shadows.setChecked(s['enable_shadows'])
        self.chk_edge_highlight.setChecked(s['enable_edge_highlighting'])
        self.slider_edge_width.setValue(int(s['edge_width']))
        self.slider_light_intensity.setValue(int(s['lighting_intensity'] * 100))
        
        # Colors tab
        mode_map = {
            'normal': 0, 'stability-based': 1,
            'type-based': 2, 'custom': 3
        }
        self.combo_color_mode.setCurrentIndex(mode_map.get(s['color_mode'], 0))
        
        cb_mode = s['colorblind_mode']
        if cb_mode == 'none':
            self.radio_cb_none.setChecked(True)
        elif cb_mode == 'deuteranopia':
            self.radio_cb_deuteranopia.setChecked(True)
        elif cb_mode == 'protanopia':
            self.radio_cb_protanopia.setChecked(True)
        elif cb_mode == 'tritanopia':
            self.radio_cb_tritanopia.setChecked(True)
        elif cb_mode == 'monochrome':
            self.radio_cb_monochrome.setChecked(True)
        
        self.chk_high_contrast.setChecked(s['high_contrast'])
        
        # Bonding tab
        self.chk_auto_bond.setChecked(s['auto_bond_enabled'])
        self.slider_confidence.setValue(int(s['auto_bond_confidence'] * 100))
        self.chk_show_suggestions.setChecked(s['show_bond_suggestions'])
        self.chk_learn_manual.setChecked(s['learn_from_manual_bonds'])
        
        # Performance tab
        fps_map = {30: 0, 60: 1, 120: 2, 0: 3}
        self.combo_fps.setCurrentIndex(fps_map.get(s['target_fps'], 1))
        self.chk_vsync.setChecked(s['enable_vsync'])
        self.chk_cache_patterns.setChecked(s['cache_patterns'])
        self.spin_undo_history.setValue(s['max_undo_history'])
        
        # Accessibility tab
        font_map = {'small': 0, 'medium': 1, 'large': 2, 'extra large': 3}
        self.combo_font_size.setCurrentIndex(font_map.get(s['font_size'], 1))
        self.chk_keyboard_shortcuts.setChecked(s['keyboard_shortcuts'])
        self.chk_screen_reader.setChecked(s['screen_reader_support'])
    
    def _save_values(self):
        """Save UI values to settings dict."""
        # Visual
        preset_names = ['default', 'blueprint', 'render', 'glass', 'metal', 'paper']
        self.settings['visual_preset'] = preset_names[self.combo_preset.currentIndex()]
        
        quality_names = ['low', 'medium', 'high', 'ultra']
        self.settings['material_quality'] = quality_names[self.combo_quality.currentIndex()]
        
        self.settings['enable_shadows'] = self.chk_shadows.isChecked()
        self.settings['enable_edge_highlighting'] = self.chk_edge_highlight.isChecked()
        self.settings['edge_width'] = float(self.slider_edge_width.value())
        self.settings['lighting_intensity'] = self.slider_light_intensity.value() / 100.0
        
        # Colors
        mode_names = ['normal', 'stability-based', 'type-based', 'custom']
        self.settings['color_mode'] = mode_names[self.combo_color_mode.currentIndex()]
        
        if self.radio_cb_none.isChecked():
            self.settings['colorblind_mode'] = 'none'
        elif self.radio_cb_deuteranopia.isChecked():
            self.settings['colorblind_mode'] = 'deuteranopia'
        elif self.radio_cb_protanopia.isChecked():
            self.settings['colorblind_mode'] = 'protanopia'
        elif self.radio_cb_tritanopia.isChecked():
            self.settings['colorblind_mode'] = 'tritanopia'
        elif self.radio_cb_monochrome.isChecked():
            self.settings['colorblind_mode'] = 'monochrome'
        
        self.settings['high_contrast'] = self.chk_high_contrast.isChecked()
        
        # Bonding
        self.settings['auto_bond_enabled'] = self.chk_auto_bond.isChecked()
        self.settings['auto_bond_confidence'] = self.slider_confidence.value() / 100.0
        self.settings['show_bond_suggestions'] = self.chk_show_suggestions.isChecked()
        self.settings['learn_from_manual_bonds'] = self.chk_learn_manual.isChecked()
        
        # Performance
        fps_values = [30, 60, 120, 0]
        self.settings['target_fps'] = fps_values[self.combo_fps.currentIndex()]
        self.settings['enable_vsync'] = self.chk_vsync.isChecked()
        self.settings['cache_patterns'] = self.chk_cache_patterns.isChecked()
        self.settings['max_undo_history'] = self.spin_undo_history.value()
        
        # Accessibility
        font_names = ['small', 'medium', 'large', 'extra large']
        self.settings['font_size'] = font_names[self.combo_font_size.currentIndex()]
        self.settings['keyboard_shortcuts'] = self.chk_keyboard_shortcuts.isChecked()
        self.settings['screen_reader_support'] = self.chk_screen_reader.isChecked()
    
    def _update_preset_preview(self, preset_name: str):
        """Update preset description."""
        descriptions = {
            'Default': 'Balanced visualization with plastic materials',
            'Blueprint': 'Technical drawing style with matte surfaces',
            'Render': 'Photo-realistic with glossy materials',
            'Glass': 'Transparent glass-like appearance',
            'Metal': 'Shiny metallic surfaces',
            'Paper': 'Origami-style paper craft look',
        }
        self.lbl_preset_preview.setText(descriptions.get(preset_name, ''))
    
    def _reset_to_defaults(self):
        """Reset all settings to defaults."""
        reply = QtWidgets.QMessageBox.question(
            self,
            "Reset Settings",
            "Reset all settings to default values?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            self.settings = self._default_settings()
            self._load_values()
    
    def _apply_settings(self):
        """Apply settings without closing."""
        self._save_values()
        self.settings_changed.emit(self.settings)
    
    def _save_and_close(self):
        """Save and close dialog."""
        self._apply_settings()
        self.accept()
    
    def _show_bonding_stats(self):
        """Show bonding pattern statistics."""
        # This would query the bonding engine
        msg = QtWidgets.QMessageBox(self)
        msg.setWindowTitle("Bonding Statistics")
        msg.setText("Learned Bond Patterns\n\nTotal patterns: 42\nHigh confidence: 28\nAvg success rate: 87%")
        msg.setDetailedText("Pattern details would go here...")
        msg.exec()
    
    def get_settings(self) -> Dict[str, Any]:
        """Get current settings."""
        return self.settings.copy()


def create_settings_menu_action(parent, callbacks: Dict) -> QtWidgets.QAction:
    """
    Create a settings menu action to add to the menu bar.
    
    Usage:
        settings_action = create_settings_menu_action(window, callbacks)
        edit_menu.addAction(settings_action)
    """
    settings_action = QtWidgets.QAction("&Preferences...", parent)
    settings_action.setShortcut("Ctrl+,")
    settings_action.setStatusTip("Open settings dialog")
    settings_action.triggered.connect(callbacks.get('settings', lambda: None))
    return settings_action
