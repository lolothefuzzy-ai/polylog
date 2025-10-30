"""
Convergence Visualizer - Real-time tracking of T (transformation) and N (population) metrics

Displays log graphs showing:
- T-position convergence (variance reduction over generations)
- N-population fitness convergence
- Generation progress
- Live statistics panel
"""

from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtCore import Qt, QTimer, Signal
import pyqtgraph as pg
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass
from collections import deque


@dataclass
class ConvergenceMetrics:
    """Store convergence data for a single generation."""
    generation: int
    t_position_variance: float  # Variance in polygon positions
    t_angle_variance: float     # Variance in angles
    fitness_best: float
    fitness_avg: float
    fitness_std: float
    population_size: int
    timestamp: float


class ConvergenceTracker:
    """Track convergence metrics over generations."""
    
    def __init__(self, max_history: int = 500):
        self.metrics: deque = deque(maxlen=max_history)
        self.generation = 0
        
    def record_generation(self, 
                         polygons: List[Dict],
                         fitness_scores: List[float],
                         population_size: int) -> ConvergenceMetrics:
        """Record metrics for current generation."""
        import time
        
        # Compute T metrics (position variance)
        positions = np.array([p['position'][:2] for p in polygons])
        t_position_variance = float(np.var(positions))
        
        # Compute angle variance
        center = np.mean(positions, axis=0) if len(positions) > 0 else np.array([0, 0])
        angles = []
        for pos in positions:
            angle = np.arctan2(pos[1] - center[1], pos[0] - center[0])
            angles.append(angle)
        t_angle_variance = float(np.var(angles)) if angles else 0.0
        
        # Compute N metrics (fitness)
        fitness_best = float(np.max(fitness_scores))
        fitness_avg = float(np.mean(fitness_scores))
        fitness_std = float(np.std(fitness_scores))
        
        metric = ConvergenceMetrics(
            generation=self.generation,
            t_position_variance=t_position_variance,
            t_angle_variance=t_angle_variance,
            fitness_best=fitness_best,
            fitness_avg=fitness_avg,
            fitness_std=fitness_std,
            population_size=population_size,
            timestamp=time.time()
        )
        
        self.metrics.append(metric)
        self.generation += 1
        return metric
    
    def get_history(self) -> List[ConvergenceMetrics]:
        """Get all recorded metrics."""
        return list(self.metrics)


class ConvergenceVisualizerWindow(QtWidgets.QMainWindow):
    """Popout window displaying convergence graphs."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📊 Convergence Tracking")
        self.setGeometry(100, 100, 1200, 700)
        self.tracker = ConvergenceTracker()
        
        # Setup UI
        self._setup_ui()
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_graphs)
        self.update_timer.start(500)  # Update every 500ms
        
    def _setup_ui(self):
        """Setup UI layout with graphs and stats."""
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        
        # Dark theme
        central_widget.setStyleSheet("""
            QMainWindow { background-color: #0a0e27; }
            QWidget { background-color: #0a0e27; }
            QLabel { color: #e0e6ff; }
        """)
        
        layout = QtWidgets.QVBoxLayout(central_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title = QtWidgets.QLabel("T and N Convergence Tracking")
        title.setStyleSheet("color: #ff3333; font-weight: bold; font-size: 14px;")
        layout.addWidget(title)
        
        # Create graph layout
        graph_layout = QtWidgets.QHBoxLayout()
        
        # Setup PyQtGraph plots with dark theme
        pg.setConfigOption('background', '#0a0e27')
        pg.setConfigOption('foreground', '#e0e6ff')
        
        # T Convergence Plot (log scale)
        self.plot_t = pg.PlotWidget(
            title="T Convergence (Position Variance - Log Scale)",
            labels={'left': 'Variance (log)', 'bottom': 'Generation'}
        )
        self.plot_t.setLogMode(False, True)  # Log scale on Y
        self.plot_t.setStyleSheet("border: 1px solid #2a3550;")
        self.curve_t_pos = self.plot_t.plot([], [], pen=pg.mkPen('#ff3333', width=2), name='T Position')
        self.curve_t_ang = self.plot_t.plot([], [], pen=pg.mkPen('#4169e1', width=2), name='T Angle')
        self.plot_t.addLegend()
        
        # N Convergence Plot
        self.plot_n = pg.PlotWidget(
            title="N Convergence (Population Fitness)",
            labels={'left': 'Fitness', 'bottom': 'Generation'}
        )
        self.plot_n.setStyleSheet("border: 1px solid #2a3550;")
        self.curve_n_best = self.plot_n.plot([], [], pen=pg.mkPen('#00ff00', width=2), name='Best')
        self.curve_n_avg = self.plot_n.plot([], [], pen=pg.mkPen('#ffaa00', width=2), name='Average')
        self.plot_n.addLegend()
        
        graph_layout.addWidget(self.plot_t)
        graph_layout.addWidget(self.plot_n)
        
        layout.addLayout(graph_layout)
        
        # Statistics panel
        stats_group = QtWidgets.QGroupBox("Live Statistics")
        stats_group.setStyleSheet("""
            QGroupBox { 
                background-color: #151a2b; 
                border: 1px solid #2a3550; 
                color: #e0e6ff;
                border-radius: 6px;
                padding: 10px;
                margin-top: 8px;
            }
        """)
        
        stats_layout = QtWidgets.QGridLayout(stats_group)
        
        # Stats labels
        self.stat_gen = QtWidgets.QLabel("Generation: 0")
        self.stat_t_var = QtWidgets.QLabel("T Variance: --")
        self.stat_n_best = QtWidgets.QLabel("N Best Fitness: --")
        self.stat_n_avg = QtWidgets.QLabel("N Avg Fitness: --")
        self.stat_convergence = QtWidgets.QLabel("Convergence: 0%")
        
        stats_layout.addWidget(self.stat_gen, 0, 0)
        stats_layout.addWidget(self.stat_t_var, 0, 1)
        stats_layout.addWidget(self.stat_n_best, 0, 2)
        stats_layout.addWidget(self.stat_n_avg, 1, 0)
        stats_layout.addWidget(self.stat_convergence, 1, 1)
        
        layout.addWidget(stats_group)
        
        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        
        clear_btn = QtWidgets.QPushButton("Clear Data")
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff3333;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #ff5555; }
        """)
        clear_btn.clicked.connect(self._clear_data)
        
        export_btn = QtWidgets.QPushButton("Export Data")
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #4169e1;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #5a7fff; }
        """)
        export_btn.clicked.connect(self._export_data)
        
        button_layout.addStretch()
        button_layout.addWidget(clear_btn)
        button_layout.addWidget(export_btn)
        
        layout.addLayout(button_layout)
    
    def record_generation(self, 
                         polygons: List[Dict],
                         fitness_scores: List[float],
                         population_size: int):
        """Record metrics for a generation."""
        self.tracker.record_generation(polygons, fitness_scores, population_size)
    
    def _update_graphs(self):
        """Update graph data from tracker."""
        history = self.tracker.get_history()
        
        if not history:
            return
        
        # Extract data
        generations = [m.generation for m in history]
        t_pos_vars = [max(m.t_position_variance, 1e-6) for m in history]  # Avoid log(0)
        t_ang_vars = [max(m.t_angle_variance, 1e-6) for m in history]
        n_best = [m.fitness_best for m in history]
        n_avg = [m.fitness_avg for m in history]
        
        # Update T plot
        self.curve_t_pos.setData(generations, t_pos_vars)
        self.curve_t_ang.setData(generations, t_ang_vars)
        
        # Update N plot
        self.curve_n_best.setData(generations, n_best)
        self.curve_n_avg.setData(generations, n_avg)
        
        # Update stats
        latest = history[-1]
        self.stat_gen.setText(f"Generation: {latest.generation}")
        self.stat_t_var.setText(f"T Variance: {latest.t_position_variance:.2e}")
        self.stat_n_best.setText(f"N Best Fitness: {latest.fitness_best:.4f}")
        self.stat_n_avg.setText(f"N Avg Fitness: {latest.fitness_avg:.4f}")
        
        # Calculate convergence percentage (based on fitness improvement plateau)
        if len(history) > 10:
            recent_best = [m.fitness_best for m in history[-10:]]
            improvement = (max(recent_best) - min(recent_best)) / (max(recent_best) + 1e-6)
            convergence = max(0, 100 * (1 - improvement))
        else:
            convergence = 0
        
        self.stat_convergence.setText(f"Convergence: {convergence:.1f}%")
    
    def _clear_data(self):
        """Clear all recorded data."""
        self.tracker = ConvergenceTracker()
        self.curve_t_pos.setData([], [])
        self.curve_t_ang.setData([], [])
        self.curve_n_best.setData([], [])
        self.curve_n_avg.setData([], [])
        self.stat_gen.setText("Generation: 0")
        self.stat_t_var.setText("T Variance: --")
        self.stat_n_best.setText("N Best Fitness: --")
        self.stat_n_avg.setText("N Avg Fitness: --")
        self.stat_convergence.setText("Convergence: 0%")
    
    def _export_data(self):
        """Export metrics to CSV."""
        import csv
        from pathlib import Path
        
        history = self.tracker.get_history()
        if not history:
            QtWidgets.QMessageBox.warning(self, "No Data", "No convergence data to export.")
            return
        
        filepath = Path.cwd() / "convergence_metrics.csv"
        
        try:
            with open(filepath, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'generation', 't_position_variance', 't_angle_variance',
                    'fitness_best', 'fitness_avg', 'fitness_std', 'population_size'
                ])
                
                for m in history:
                    writer.writerow([
                        m.generation, m.t_position_variance, m.t_angle_variance,
                        m.fitness_best, m.fitness_avg, m.fitness_std, m.population_size
                    ])
            
            QtWidgets.QMessageBox.information(
                self, "Export Success", 
                f"Data exported to {filepath}"
            )
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Export Error", str(e))


def create_convergence_visualizer(parent=None) -> ConvergenceVisualizerWindow:
    """Factory function to create visualizer window."""
    return ConvergenceVisualizerWindow(parent)
