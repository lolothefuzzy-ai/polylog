"""
Polygon Range Slider Widget

Allows users to specify a range of polygon sides (e.g., 3-8) and instantly
generate all variants with 3D folding and particle generation animations.

Features:
- Min/max side sliders with real-time display
- Combination count indicator
- Instant generation with smooth animations
- Particle effects and fade-in
- Integration with HingeManager for fold animations
"""

import time
from typing import Any, Callable, Dict, List, Optional

import numpy as np
import pyqtgraph.opengl as gl
from geometry3d import rotation_matrix_axis_angle
from polygon_utils import create_polygon_3d
from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)


class PolygonRangeSliderWidget(QGroupBox):
    """
    Widget for selecting and generating a range of polygon sides.
    
    Signals:
        - generation_started(min_sides, max_sides)
        - generation_completed(polygon_ids)
        - generation_progress(current, total)
    """
    
    generation_started = Signal(int, int)  # min_sides, max_sides
    generation_completed = Signal(list)    # polygon_ids
    generation_progress = Signal(int, int)  # current, total
    
    def __init__(self, parent=None):
        super().__init__("Polygon Range Generator", parent)
        self.min_sides = 3
        self.max_sides = 8
        self.generated_polygons: List[Dict[str, Any]] = []
        self._setup_ui()
    
    def _setup_ui(self):
        """Build UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # Min sides control
        min_layout = QHBoxLayout()
        min_layout.addWidget(QLabel("Min Sides:"))
        self.spin_min = QSpinBox()
        self.spin_min.setRange(3, 12)
        self.spin_min.setValue(self.min_sides)
        self.spin_min.valueChanged.connect(self._on_min_changed)
        min_layout.addWidget(self.spin_min)
        min_layout.addStretch()
        layout.addLayout(min_layout)
        
        # Max sides control
        max_layout = QHBoxLayout()
        max_layout.addWidget(QLabel("Max Sides:"))
        self.spin_max = QSpinBox()
        self.spin_max.setRange(3, 12)
        self.spin_max.setValue(self.max_sides)
        self.spin_max.valueChanged.connect(self._on_max_changed)
        max_layout.addWidget(self.spin_max)
        max_layout.addStretch()
        layout.addLayout(max_layout)
        
        # Separator
        sep = QtWidgets.QFrame()
        sep.setFrameShape(QtWidgets.QFrame.HLine)
        sep.setFrameShadow(QtWidgets.QFrame.Sunken)
        layout.addWidget(sep)
        
        # Info display
        self.lbl_count = QLabel("Combinations: 0")
        self.lbl_count.setStyleSheet("font-weight: bold; color: #00ff00;")
        layout.addWidget(self.lbl_count)
        
        self.lbl_info = QLabel("Configure range above and click Generate")
        self.lbl_info.setStyleSheet("color: #888888;")
        self.lbl_info.setWordWrap(True)
        layout.addWidget(self.lbl_info)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)
        
        # Generate button
        self.btn_generate = QPushButton("Generate Range")
        self.btn_generate.setStyleSheet(
            "QPushButton { padding: 8px; font-weight: bold; "
            "background-color: #1a4d2e; color: #00ff00; border-radius: 4px; } "
            "QPushButton:hover { background-color: #2d7a3d; }"
        )
        self.btn_generate.clicked.connect(self.on_generate)
        layout.addWidget(self.btn_generate)
        
        # Status display
        self.lbl_status = QLabel("Ready")
        self.lbl_status.setStyleSheet("color: #00aa00; font-size: 11px;")
        layout.addWidget(self.lbl_status)
        
        layout.addStretch()
        
        # Update count display
        self._update_count_display()
    
    def _on_min_changed(self, value: int):
        """Handle min sides change."""
        self.min_sides = value
        if self.min_sides > self.max_sides:
            self.max_sides = self.min_sides
            self.spin_max.blockSignals(True)
            self.spin_max.setValue(self.max_sides)
            self.spin_max.blockSignals(False)
        self._update_count_display()
    
    def _on_max_changed(self, value: int):
        """Handle max sides change."""
        self.max_sides = value
        if self.max_sides < self.min_sides:
            self.min_sides = self.max_sides
            self.spin_min.blockSignals(True)
            self.spin_min.setValue(self.min_sides)
            self.spin_min.blockSignals(False)
        self._update_count_display()
    
    def _update_count_display(self):
        """Update combination count display."""
        count = max(0, self.max_sides - self.min_sides + 1)
        self.lbl_count.setText(f"Combinations: {count} polygons")
        
        sides_list = list(range(self.min_sides, self.max_sides + 1))
        sides_str = ", ".join(str(s) for s in sides_list)
        self.lbl_info.setText(f"Will generate: {sides_str}-sided polygons")
    
    @Slot()
    def on_generate(self):
        """Trigger polygon generation."""
        if self.min_sides > self.max_sides:
            self.lbl_status.setText("ERROR: Min > Max")
            return
        
        self.generation_started.emit(self.min_sides, self.max_sides)
        self.btn_generate.setEnabled(False)
        self.lbl_status.setText("Generating...")
        self.progress.setVisible(True)
        self.progress.setValue(0)
    
    def set_generation_progress(self, current: int, total: int):
        """Update generation progress."""
        if total > 0:
            progress = int(100 * current / total)
            self.progress.setValue(progress)
            self.generation_progress.emit(current, total)
    
    def on_generation_complete(self, polygon_ids: List[str]):
        """Handle generation completion."""
        self.generated_polygons = polygon_ids
        self.progress.setVisible(False)
        self.btn_generate.setEnabled(True)
        self.lbl_status.setText(f"✓ Generated {len(polygon_ids)} polygons")
        self.generation_completed.emit(polygon_ids)
    
    def on_generation_error(self, error_msg: str):
        """Handle generation error."""
        self.progress.setVisible(False)
        self.btn_generate.setEnabled(True)
        self.lbl_status.setText(f"ERROR: {error_msg}")


class PolygonGenerationAnimator:
    """
    Handles smooth animations for polygon generation including:
    - Particle burst effects from centroid
    - Folding animation (flat -> 3D)
    - Fade-in effects
    - Staggered timing for multiple polygons
    """
    
    def __init__(self, view, renderer, assembly, hinge_manager, 
                 on_progress: Optional[Callable] = None):
        """
        Initialize animator.
        
        Args:
            view: GLViewWidget for rendering
            renderer: GLRenderer for drawing
            assembly: Assembly object
            hinge_manager: HingeManager for fold transforms
            on_progress: Optional callback(current, total)
        """
        self.view = view
        self.renderer = renderer
        self.assembly = assembly
        self.hinge_manager = hinge_manager
        self.on_progress = on_progress
        
        self.anim_timers: Dict[str, QtCore.QTimer] = {}
        self.particle_items: List = []
    
    def animate_polygon_generation(self, polygons: List[Dict[str, Any]], 
                                   duration_ms: int = 1000,
                                   stagger_ms: int = 200):
        """
        Animate generation of multiple polygons with staggered timing.
        
        Args:
            polygons: List of polyform dicts to animate
            duration_ms: Duration of each polygon's animation
            stagger_ms: Time offset between polygon animations
        """
        total = len(polygons)
        
        for idx, poly in enumerate(polygons):
            poly_id = poly.get('id')
            if not poly_id:
                continue
            
            delay_ms = idx * stagger_ms
            
            # Schedule animation
            timer = QtCore.QTimer()
            timer.setSingleShot(True)
            timer.timeout.connect(
                lambda pid=poly_id, p=poly, d=duration_ms: 
                self._animate_single_polygon(pid, p, d)
            )
            timer.start(delay_ms)
            self.anim_timers[poly_id] = timer
            
            # Report progress
            if self.on_progress:
                self.on_progress(idx + 1, total)
    
    def _animate_single_polygon(self, poly_id: str, poly: Dict[str, Any], 
                               duration_ms: int):
        """
        Animate a single polygon:
        1. Particle burst from centroid
        2. Fold from flat to 3D
        3. Fade in
        """
        # Get polygon centroid
        verts = np.array(poly.get('vertices', []))
        if len(verts) == 0:
            return
        
        centroid = np.mean(verts, axis=0)
        
        # Phase 1: Particle burst (0-200ms)
        self._emit_particles(centroid, count=30, duration_ms=200)
        
        # Phase 2: Fold animation (starting at 100ms, lasting 600ms)
        if poly.get('has_3d_mesh'):
            self._animate_fold_sequence(poly_id, poly, duration_ms - 100)
        
        # Phase 3: Fade in (entire duration)
        self._animate_fade_in(poly_id, duration_ms)
    
    def _emit_particles(self, origin: np.ndarray, count: int = 30, 
                       duration_ms: int = 200):
        """
        Emit particles from origin point with radial spread.
        
        Args:
            origin: 3D point to emit from
            count: Number of particles
            duration_ms: Duration of particle animation
        """
        # Create particle positions (slight offset from origin)
        positions = np.tile(origin, (count, 1)).astype(np.float32)
        
        # Random velocities pointing outward
        velocities = np.random.randn(count, 3).astype(np.float32) * 0.08
        velocities[:, 2] += 0.05  # Slight upward bias
        
        # Particle colors (orange -> yellow gradient)
        colors = np.ones((count, 4), dtype=np.float32)
        colors[:, 0] = 1.0  # Red
        colors[:, 1] = np.random.uniform(0.5, 1.0, count)  # Green varies
        colors[:, 2] = 0.0  # No blue
        colors[:, 3] = 1.0  # Full alpha
        
        # Create scatter item
        scatter = gl.GLScatterPlotItem(
            pos=positions, color=colors, size=4, pxMode=True
        )
        self.view.addItem(scatter)
        self.particle_items.append(scatter)
        
        start_time = time.time()
        
        def particle_step():
            elapsed = (time.time() - start_time) * 1000
            progress = min(1.0, elapsed / duration_ms)
            
            if progress >= 1.0:
                self.view.removeItem(scatter)
                if scatter in self.particle_items:
                    self.particle_items.remove(scatter)
                return
            
            # Update positions
            new_positions = positions + velocities * progress * 2.0
            scatter.setData(pos=new_positions)
            
            # Fade out
            colors[:, 3] = 1.0 - progress
            scatter.setData(color=colors)
        
        timer = QtCore.QTimer()
        timer.timeout.connect(particle_step)
        timer.start(16)  # ~60 FPS
    
    def _animate_fold_sequence(self, poly_id: str, poly: Dict[str, Any],
                              duration_ms: int):
        """
        Animate polygon folding from flat to 3D form.
        
        Uses hinge-based rotation to demonstrate fold mechanics.
        """
        from polygon_utils import get_polyform_mesh
        
        initial_mesh = get_polyform_mesh(poly)
        if initial_mesh is None:
            return
        
        # Get vertices for hinge axis (use first edge)
        verts = np.array(poly.get('vertices', []))
        if len(verts) < 2:
            return
        
        axis_start = verts[0]
        axis_end = verts[1]
        axis = axis_end - axis_start
        axis = axis / (np.linalg.norm(axis) + 1e-10)
        
        # Target fold angle (90 degrees)
        target_angle = np.pi / 2
        
        start_time = time.time()
        
        def fold_step():
            elapsed = (time.time() - start_time) * 1000
            progress = min(1.0, elapsed / duration_ms)
            
            if progress >= 1.0:
                return
            
            # Interpolate fold angle
            current_angle = target_angle * progress
            
            # Apply rotation to mesh using Rodrigues formula
            transform = rotation_matrix_axis_angle(axis, current_angle)
            
            # Update vertices by applying transform with pivot
            transformed_verts = []
            for v in verts:
                # Translate to origin, rotate, translate back
                v_rel = v - axis_start
                v_homo = np.append(v_rel, 1.0)
                v_rot = transform @ v_homo
                v_final = v_rot[:3] + axis_start
                transformed_verts.append(v_final)
            
            poly['vertices'] = [list(v) for v in transformed_verts]
            
            # Refresh rendering
            self.renderer.draw_polyform(poly)
        
        timer = QtCore.QTimer()
        timer.timeout.connect(fold_step)
        timer.start(16)  # ~60 FPS
    
    def _animate_fade_in(self, poly_id: str, duration_ms: int):
        """
        Fade in polygon by adjusting opacity.
        
        Args:
            poly_id: ID of polygon to fade in
            duration_ms: Duration of fade in milliseconds
        """
        if poly_id not in self.renderer.poly_items:
            return
        
        item = self.renderer.poly_items[poly_id]
        start_time = time.time()
        initial_color = (0.2, 0.7, 1.0, 0.0)  # Start transparent
        
        def fade_step():
            elapsed = (time.time() - start_time) * 1000
            progress = min(1.0, elapsed / duration_ms)
            
            if progress >= 1.0:
                return
            
            # Interpolate opacity
            alpha = progress
            color = (0.2, 0.7, 1.0, alpha)
            
            try:
                verts = item.pos
                item.setData(pos=verts, color=color, width=2)
            except Exception:
                pass
        
        timer = QtCore.QTimer()
        timer.timeout.connect(fade_step)
        timer.start(16)  # ~60 FPS


def integrate_polygon_range_slider_into_gui(main_window):
    """
    Helper function to integrate PolygonRangeSlider into MainWindow.
    
    Args:
        main_window: MainWindow instance (desktop_app.py)
    """
    # Create slider widget
    slider_widget = PolygonRangeSliderWidget()
    
    # Connect signals
    def on_generation_start(min_sides: int, max_sides: int):
        """Handle generation start."""
        try:
            animator = PolygonGenerationAnimator(
                main_window.view,
                main_window.renderer,
                main_window.assembly,
                main_window.hinge_manager,
                on_progress=slider_widget.set_generation_progress
            )
            
            # Generate polygons
            polygons = []
            for sides in range(min_sides, max_sides + 1):
                # Calculate offset for layout
                angle = 2 * np.pi * len(polygons) / (max_sides - min_sides + 1)
                offset_x = 5.0 * np.cos(angle)
                offset_y = 5.0 * np.sin(angle)
                cx, cy, cz = main_window._assembly_centroid()
                
                poly = create_polygon_3d(
                    sides, 
                    (cx + offset_x, cy + offset_y, cz),
                    thickness=0.15
                )
                main_window.assembly.add_polyform(poly)
                polygons.append(poly)
            
            # Animate generation
            animator.animate_polygon_generation(
                polygons, duration_ms=1200, stagger_ms=200
            )
            
            # Update UI
            main_window.refresh_lists()
            main_window.refresh_scene()
            
            slider_widget.on_generation_complete([p.get('id') for p in polygons])
            
        except Exception as e:
            slider_widget.on_generation_error(str(e))
    
    slider_widget.generation_started.connect(on_generation_start)
    
    return slider_widget