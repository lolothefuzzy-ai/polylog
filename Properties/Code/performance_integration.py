"""
Performance Integration - Integrates performance monitoring and visual tracking into desktop app.
Provides convenient utilities and Qt integration for the main application.
"""
from typing import Optional

import numpy as np
import pyqtgraph.opengl as gl
from PySide6 import QtCore, QtWidgets

from performance_monitor import (
    AdaptiveFramerateController,
    FramerateMonitor,
    PerformanceProfiler,
    SystemMetricsMonitor,
)
from visual_tracking import VisualTrackingManager

try:
    from common.unity_bridge import FrameUpdate, UnityBridge
except Exception:  # Unity bridge optional
    FrameUpdate = None
    UnityBridge = None


class PerformanceHUD(QtCore.QObject):
    """Heads-up display for performance metrics."""
    
    def __init__(
        self,
        status_bar: QtWidgets.QStatusBar,
        overlay_parent: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        super().__init__(overlay_parent)
        """
        Initialize performance HUD.
        
        Args:
            status_bar: Status bar to display metrics in
        """
        self.status_bar = status_bar
        self.fps_label = QtWidgets.QLabel("FPS: -- | Render: --ms")
        self.fps_label.setMinimumWidth(200)
        self.perf_warning_label = QtWidgets.QLabel("")
        self.perf_warning_label.setStyleSheet("color: #ff6600;")

        # Track widget lifecycle
        self._widgets_added = False

        # Overlay for lightweight FPS display
        self.overlay_parent = overlay_parent
        self.overlay_label: Optional[QtWidgets.QLabel] = None
        self._overlay_visible = False
        if self.overlay_parent is not None:
            self.overlay_label = QtWidgets.QLabel(self.overlay_parent)
            self.overlay_label.setObjectName("polylog-fps-overlay")
            self.overlay_label.setStyleSheet(
                "color: #ff3b30; font-size: 9px; background: transparent;"
            )
            self.overlay_label.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
            self.overlay_label.hide()
            self.overlay_parent.installEventFilter(self)

    def ensure_widgets_visible(self):
        """Ensure widgets are in status bar."""
        if not self._widgets_added and self.status_bar is not None:
            try:
                self.status_bar.addPermanentWidget(self.fps_label, 0)
                self.status_bar.addPermanentWidget(self.perf_warning_label, 0)
                self._widgets_added = True
            except Exception as e:
                print(f"Warning: Could not add status bar widgets: {e}")

    def set_overlay_visible(self, visible: bool) -> None:
        self._overlay_visible = visible
        if self.overlay_label is None:
            return
        if visible:
            self.overlay_label.show()
            self._reposition_overlay()
        else:
            self.overlay_label.hide()

    def update(self, stats: dict, warning: str = ""):
        """Update HUD with performance stats."""
        self.ensure_widgets_visible()

        if not self._widgets_added:
            return  # Skip update if widgets not visible

        try:
            fps_text = f"FPS: {stats['current_fps']:.0f} ({stats['avg_fps']:.0f}) | Render: {stats['render_time_ms']:.1f}ms"
            self.fps_label.setText(fps_text)

            if warning:
                self.perf_warning_label.setText(f"⚠ {warning}")
                self.perf_warning_label.setStyleSheet("color: #ff6600; font-weight: bold;")
            else:
                self.perf_warning_label.setText("")
                self.perf_warning_label.setStyleSheet("color: #ff6600;")

            if self.overlay_label is not None:
                if self._overlay_visible:
                    self.overlay_label.setText(f"{stats['current_fps']:.0f} FPS")
                    self.overlay_label.adjustSize()
                    self.overlay_label.show()
                    self._reposition_overlay()
                else:
                    self.overlay_label.hide()
        except Exception as e:
            print(f"Warning: HUD update failed: {e}")

    def eventFilter(self, watched, event):
        if watched is self.overlay_parent and event.type() == QtCore.QEvent.Resize:
            self._reposition_overlay()
        return super().eventFilter(watched, event)

    def _reposition_overlay(self) -> None:
        if not self._overlay_visible or self.overlay_label is None or self.overlay_parent is None:
            return
        margin = 8
        width = self.overlay_parent.width()
        x = max(margin, width - self.overlay_label.width() - margin)
        self.overlay_label.move(x, margin)


class PerformancePanel(QtWidgets.QWidget):
    """Panel for detailed performance metrics and profiling."""
    
    def __init__(self, parent=None):
        """Initialize performance panel."""
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """Build UI."""
        layout = QtWidgets.QVBoxLayout(self)
        
        # Title
        title = QtWidgets.QLabel("Performance Metrics")
        title.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(title)
        
        # Stats display
        self.stats_text = QtWidgets.QPlainTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setMaximumHeight(150)
        layout.addWidget(self.stats_text)
        
        # Profiling report
        self.profile_text = QtWidgets.QPlainTextEdit()
        self.profile_text.setReadOnly(True)
        self.profile_text.setMaximumHeight(150)
        layout.addWidget(self.profile_text)
        
        # Controls
        controls_layout = QtWidgets.QHBoxLayout()
        
        self.btn_reset = QtWidgets.QPushButton("Reset Stats")
        self.btn_profile = QtWidgets.QPushButton("Toggle Profiling")
        
        controls_layout.addWidget(self.btn_reset)
        controls_layout.addWidget(self.btn_profile)
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        layout.addStretch()
    
    def update_stats(self, stats: dict, system_stats: dict):
        """Update statistics display."""
        text = f"""Framerate Metrics:
  Current: {stats['current_fps']:.1f} FPS
  Average: {stats['avg_fps']:.1f} FPS
  Min/Max: {stats['min_fps']:.1f} / {stats['max_fps']:.1f} FPS
  Frame Time: {stats['frame_time_ms']:.2f} ms
  
Render Breakdown:
  Render Time: {stats['render_time_ms']:.2f} ms ({stats['render_ratio']:.1f}%)
  Update Time: {stats['update_time_ms']:.2f} ms
  
System:
  CPU: {system_stats['cpu_percent']:.1f}% (avg: {system_stats['avg_cpu']:.1f}%)
  Memory: {system_stats['memory_mb']:.1f} MB ({system_stats['memory_percent']:.1f}%)
"""
        self.stats_text.setPlainText(text)
    
    def update_profile(self, profile_report: dict):
        """Update profiling report."""
        if not profile_report:
            self.profile_text.setPlainText("No profiling data yet.")
            return
        
        lines = ["Performance Profiling Report:"]
        for op_name, data in sorted(profile_report.items(), key=lambda x: x[1]['percent_of_frame'], reverse=True):
            lines.append(f"\n{op_name}:")
            lines.append(f"  Avg: {data['avg_ms']:.2f}ms | "
                        f"Min/Max: {data['min_ms']:.2f}/{data['max_ms']:.2f}ms | "
                        f"Std: {data['std_dev']:.2f}ms")
            lines.append(f"  % of Frame: {data['percent_of_frame']:.1f}%")
        
        self.profile_text.setPlainText("\n".join(lines))


class IntegratedPerformanceManager:
    """Master performance manager integrating all components."""
    
    def __init__(self, main_window, view: gl.GLViewWidget, status_bar: QtWidgets.QStatusBar):
        """
        Initialize integrated performance manager.
        
        Args:
            main_window: Reference to main application window
            view: GL view widget
            status_bar: Status bar for HUD display
        """
        self.main_window = main_window
        self.view = view
        
        # Performance monitoring
        self.framerate_monitor = FramerateMonitor(history_size=120)
        self.system_monitor = SystemMetricsMonitor()
        self.framerate_controller = AdaptiveFramerateController()
        self.profiler = PerformanceProfiler()
        
        # Visual tracking
        self.tracking_manager = VisualTrackingManager(view)
        
        # HUD
        self.hud = PerformanceHUD(status_bar, view)
        self.hud.set_overlay_visible(True)

        # Unity bridge
        self.unity_bridge = None
        if UnityBridge is not None:
            bridge = UnityBridge()
            if bridge.start():
                self.unity_bridge = bridge
            else:
                bridge.stop()

        # Settings
        self.enable_profiling = False
        self.target_fps = 30
        self.profiling_enabled = False
    
    def frame_start(self):
        """Call at start of each frame."""
        if self.enable_profiling:
            self.profiler.start("frame_total")
    
    def frame_end(self):
        """Call at end of each frame."""
        self.framerate_monitor.frame_tick()
        
        if self.enable_profiling:
            self.profiler.end()
        
        # Update system metrics periodically
        if self.framerate_monitor.frame_count % 30 == 0:
            self.system_monitor.update()
        
        # Update HUD every 10 frames
        if self.framerate_monitor.frame_count % 10 == 0:
            self._update_hud()
    
    def record_render_time(self, render_time: float):
        """Record rendering time."""
        self.framerate_monitor.record_render_time(render_time)
    
    def record_update_time(self, update_time: float):
        """Record update time."""
        self.framerate_monitor.record_update_time(update_time)
    
    def profile_operation(self, operation_name: str):
        """Context manager for profiling operations."""
        class ProfileContext:
            def __init__(self, profiler, name):
                self.profiler = profiler
                self.name = name
            
            def __enter__(self):
                self.profiler.start(self.name)
                return self
            
            def __exit__(self, *args):
                self.profiler.end()
        
        return ProfileContext(self.profiler, operation_name)
    
    def _update_hud(self):
        """Update HUD display."""
        stats = self.framerate_monitor.get_stats()
        warning = self.framerate_monitor.check_performance_warning(self.target_fps)
        self.hud.update(stats, warning)

        if self.unity_bridge and FrameUpdate is not None:
            system_stats = self.system_monitor.get_stats()
            stability = self._estimate_stability()
            kpi_snapshot = {
                "avg_fps": stats.get("avg_fps", 0.0),
                "min_fps": stats.get("min_fps", 0.0),
                "max_fps": stats.get("max_fps", 0.0),
                "frame_time_ms": stats.get("frame_time_ms", 0.0),
                "render_time_ms": stats.get("render_time_ms", 0.0),
                "update_time_ms": stats.get("update_time_ms", 0.0),
                "cpu_percent": system_stats.get("cpu_percent", 0.0),
                "memory_mb": system_stats.get("memory_mb", 0.0),
                "warning": warning,
            }
            frame_update = FrameUpdate(
                frame=self.framerate_monitor.frame_count,
                fps=stats.get("current_fps", 0.0),
                stability_score=stability,
                kpi_snapshot=kpi_snapshot,
            )
            self.unity_bridge.queue_update(frame_update)

    def _estimate_stability(self) -> float:
        """Return best-effort stability estimate for Unity bridge."""
        analyzer = getattr(self.main_window, "stability_analyzer", None)
        assembly = getattr(self.main_window, "assembly", None)
        if callable(getattr(analyzer, "calculate_stability", None)) and assembly is not None:
            try:
                return float(analyzer.calculate_stability(assembly))
            except Exception:
                pass
        return 0.0
    
    def start_tracking_polyform(self, poly_id: str, position: np.ndarray = None):
        """Start tracking a polyform."""
        self.tracking_manager.start_tracking(poly_id)
        if position is not None:
            self.tracking_manager.update_tracker(poly_id, position)
    
    def update_polyform_position(self, poly_id: str, position: np.ndarray):
        """Update polyform tracking position."""
        self.tracking_manager.update_tracker(poly_id, position)
    
    def stop_tracking_polyform(self, poly_id: str):
        """Stop tracking a polyform."""
        self.tracking_manager.stop_tracking(poly_id)
    
    def follow_polyform(self, poly_id: str, position: np.ndarray, offset: np.ndarray = None):
        """Start camera following a polyform."""
        self.tracking_manager.follow_polyform(poly_id, position, offset)
    
    def update_camera_follow(self, position: np.ndarray):
        """Update camera following."""
        self.tracking_manager.update_camera(position)
    
    def stop_camera_follow(self):
        """Stop camera following."""
        self.tracking_manager.stop_following()
    
    def update_trails_visualization(self):
        """Update trail visualizations."""
        self.tracking_manager.update_trails_visualization()
    
    def set_profiling_enabled(self, enabled: bool):
        """Enable or disable profiling."""
        self.enable_profiling = enabled
        if not enabled:
            self.profiler.reset()
    
    def get_performance_report(self):
        """Get complete performance report."""
        return {
            'framerate': self.framerate_monitor.get_stats(),
            'system': self.system_monitor.get_stats(),
            'profile': self.profiler.get_report(),
            'bottleneck': self.profiler.get_bottleneck(),
        }
    
    def get_adaptive_target_fps(self) -> int:
        """Get adaptive target FPS based on current performance."""
        stats = self.framerate_monitor.get_stats()
        
        # Safely get polyform count
        polyform_count = 0
        try:
            if (hasattr(self.main_window, 'assembly') and 
                self.main_window.assembly and
                hasattr(self.main_window.assembly, 'get_all_polyforms')):
                polyforms = self.main_window.assembly.get_all_polyforms()
                polyform_count = len(polyforms) if polyforms else 0
        except Exception as e:
            print(f"Warning: Could not get polyform count: {e}")
        
        # Safely check animation state
        is_animating = False
        try:
            if (hasattr(self.main_window, 'exploration') and 
                self.main_window.exploration and 
                hasattr(self.main_window.exploration, 'is_running')):
                is_animating = bool(self.main_window.exploration.is_running)
        except Exception as e:
            print(f"Warning: Could not check animation state: {e}")
        
        # Update complexity factors
        self.framerate_controller.update_complexity(polyform_count, is_animating)
        
        # Calculate adaptive FPS
        return self.framerate_controller.calculate_adaptive_fps(
            stats['current_fps'], 
            stats['avg_fps']
        )
    
    def reset_stats(self):
        """Reset all performance statistics."""
        self.framerate_monitor.reset()
        self.profiler.reset()


def create_performance_info_dialog(parent, performance_manager: IntegratedPerformanceManager):
    """Create a detailed performance information dialog."""
    dialog = QtWidgets.QDialog(parent)
    dialog.setWindowTitle("Performance Analysis")
    dialog.resize(600, 500)
    
    layout = QtWidgets.QVBoxLayout(dialog)
    
    # Performance panel
    perf_panel = PerformancePanel()
    layout.addWidget(perf_panel)
    
    # Buttons
    btn_layout = QtWidgets.QHBoxLayout()
    btn_close = QtWidgets.QPushButton("Close")
    btn_close.clicked.connect(dialog.close)
    btn_export = QtWidgets.QPushButton("Export Report")
    
    def export_report():
        pass
    
    btn_export.clicked.connect(export_report)
    btn_layout.addStretch()
    btn_layout.addWidget(btn_export)
    btn_layout.addWidget(btn_close)
    layout.addLayout(btn_layout)
    
    # Update function
    def update_display():
        report = performance_manager.get_performance_report()
        perf_panel.update_stats(report['framerate'], report['system'])
        perf_panel.update_profile(report['profile'])
        
        # Schedule next update
        QtCore.QTimer.singleShot(500, update_display)
    
    # Start updates when shown
    dialog.showEvent = lambda e: (
        QtCore.QTimer.singleShot(0, update_display),
        QtWidgets.QDialog.showEvent(dialog, e)
    )
    
    return dialog
