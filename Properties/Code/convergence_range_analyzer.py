"""
Convergence Range Analyzer - Visualize T/N behavior across different N ranges and detect novel interactions

Shows:
- How convergence changes as population size varies
- Novel interaction patterns (fitness jumps, variance collapses)
- Heatmaps of convergence metrics across ranges
- Generation-wise comparison across multiple N values
"""

from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtCore import Qt, QTimer
import pyqtgraph as pg
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict
import time


@dataclass
class RangeMetrics:
    """Convergence metrics for a specific N range."""
    population_size: int
    generation: int
    t_position_variance: float
    t_angle_variance: float
    fitness_best: float
    fitness_avg: float
    fitness_std: float
    timestamp: float


class NovelInteractionDetector:
    """Detect novel/anomalous convergence behaviors."""
    
    def __init__(self, threshold_std: float = 2.0):
        self.threshold_std = threshold_std
        self.history: List[Dict] = []
    
    def record_observation(self, pop_size: int, generation: int, metrics: RangeMetrics):
        """Record an observation."""
        self.history.append({
            'pop_size': pop_size,
            'generation': generation,
            'metrics': metrics,
            'timestamp': time.time()
        })
    
    def detect_anomalies(self) -> List[Dict]:
        """Detect novel interactions/anomalies."""
        if len(self.history) < 10:
            return []
        
        anomalies = []
        
        # Group by population size
        by_pop_size = defaultdict(list)
        for obs in self.history:
            by_pop_size[obs['pop_size']].append(obs)
        
        # Analyze each population size
        for pop_size, observations in by_pop_size.items():
            fitnesses = [o['metrics'].fitness_best for o in observations]
            variances = [o['metrics'].t_position_variance for o in observations]
            
            if len(fitnesses) < 5:
                continue
            
            # Detect fitness plateaus (convergence threshold crossing)
            for i in range(1, len(fitnesses)):
                jump = abs(fitnesses[i] - fitnesses[i-1])
                avg_jump = np.mean([abs(fitnesses[j] - fitnesses[j-1]) for j in range(1, len(fitnesses))])
                
                if jump > self.threshold_std * np.std([abs(fitnesses[j] - fitnesses[j-1]) for j in range(1, len(fitnesses))]):
                    anomalies.append({
                        'type': 'fitness_jump',
                        'pop_size': pop_size,
                        'generation': observations[i]['generation'],
                        'value': jump,
                        'reason': f"Sudden {jump:.3f} fitness improvement"
                    })
            
            # Detect variance collapses
            variance_ratios = []
            for i in range(1, len(variances)):
                if variances[i-1] > 1e-6:
                    ratio = variances[i] / variances[i-1]
                    variance_ratios.append(ratio)
            
            if variance_ratios:
                collapse_threshold = np.mean(variance_ratios) - self.threshold_std * np.std(variance_ratios)
                for i in range(1, len(variances)):
                    ratio = variances[i] / max(variances[i-1], 1e-6)
                    if ratio < collapse_threshold:
                        anomalies.append({
                            'type': 'variance_collapse',
                            'pop_size': pop_size,
                            'generation': observations[i]['generation'],
                            'value': ratio,
                            'reason': f"Sudden variance drop (ratio: {ratio:.3f})"
                        })
        
        return anomalies


class RangeConvergenceAnalyzer(QtWidgets.QMainWindow):
    """Analyze convergence behavior across N ranges."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📈 Range Convergence Analysis")
        self.setGeometry(100, 100, 1400, 900)
        
        # Data storage: {pop_size: [metrics]}
        self.range_data: Dict[int, List[RangeMetrics]] = defaultdict(list)
        self.anomaly_detector = NovelInteractionDetector()
        
        self._setup_ui()
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_displays)
        self.update_timer.start(500)
    
    def _setup_ui(self):
        """Setup UI with multiple views."""
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        
        central.setStyleSheet("""
            QMainWindow { background-color: #0a0e27; }
            QWidget { background-color: #0a0e27; }
            QLabel { color: #e0e6ff; }
        """)
        
        layout = QtWidgets.QVBoxLayout(central)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title = QtWidgets.QLabel("Multi-Range Convergence Analysis")
        title.setStyleSheet("color: #ff3333; font-weight: bold; font-size: 14px;")
        layout.addWidget(title)
        
        # Tab widget for different views
        tabs = QtWidgets.QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget { background-color: #0a0e27; }
            QTabBar::tab { background-color: #151a2b; color: #e0e6ff; padding: 8px 20px; }
            QTabBar::tab:selected { background-color: #ff3333; }
        """)
        
        # Tab 1: Fitness across ranges
        tab1 = self._create_fitness_tab()
        tabs.addTab(tab1, "Fitness Ranges")
        
        # Tab 2: Variance across ranges
        tab2 = self._create_variance_tab()
        tabs.addTab(tab2, "Variance Ranges")
        
        # Tab 3: Heatmap
        tab3 = self._create_heatmap_tab()
        tabs.addTab(tab3, "Convergence Heatmap")
        
        # Tab 4: Novel Interactions
        tab4 = self._create_anomalies_tab()
        tabs.addTab(tab4, "Novel Interactions")
        
        layout.addWidget(tabs)
        
        # Bottom stats
        stats_layout = QtWidgets.QHBoxLayout()
        self.stat_ranges = QtWidgets.QLabel("Population Ranges: --")
        self.stat_anomalies = QtWidgets.QLabel("Novel Events: 0")
        self.stat_generations = QtWidgets.QLabel("Generations: 0")
        
        stats_layout.addWidget(self.stat_ranges)
        stats_layout.addWidget(self.stat_anomalies)
        stats_layout.addWidget(self.stat_generations)
        
        layout.addLayout(stats_layout)
    
    def _create_fitness_tab(self) -> QtWidgets.QWidget:
        """Tab showing fitness convergence across N ranges."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        
        pg.setConfigOption('background', '#0a0e27')
        pg.setConfigOption('foreground', '#e0e6ff')
        
        self.plot_fitness = pg.PlotWidget(
            title="Best Fitness vs Generation (by Population Size)",
            labels={'left': 'Fitness', 'bottom': 'Generation'}
        )
        self.plot_fitness.setStyleSheet("border: 1px solid #2a3550;")
        self.fitness_curves = {}
        self.plot_fitness.addLegend()
        
        layout.addWidget(self.plot_fitness)
        return widget
    
    def _create_variance_tab(self) -> QtWidgets.QWidget:
        """Tab showing variance across N ranges."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        
        pg.setConfigOption('background', '#0a0e27')
        pg.setConfigOption('foreground', '#e0e6ff')
        
        self.plot_variance = pg.PlotWidget(
            title="Position Variance vs Generation (by Population Size, Log Scale)",
            labels={'left': 'Variance (log)', 'bottom': 'Generation'}
        )
        self.plot_variance.setLogMode(False, True)
        self.plot_variance.setStyleSheet("border: 1px solid #2a3550;")
        self.variance_curves = {}
        self.plot_variance.addLegend()
        
        layout.addWidget(self.plot_variance)
        return widget
    
    def _create_heatmap_tab(self) -> QtWidgets.QWidget:
        """Tab showing convergence as heatmap."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        
        self.heatmap_img = pg.ImageView()
        self.heatmap_img.setStyleSheet("border: 1px solid #2a3550;")
        
        layout.addWidget(self.heatmap_img)
        
        info = QtWidgets.QLabel(
            "Heatmap: X=Generation, Y=Population Size\n"
            "Color intensity = Best Fitness (warmer = better)"
        )
        info.setStyleSheet("color: #4169e1; font-size: 11px;")
        layout.addWidget(info)
        
        return widget
    
    def _create_anomalies_tab(self) -> QtWidgets.QWidget:
        """Tab showing detected novel interactions."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        
        # List of anomalies
        self.anomaly_list = QtWidgets.QListWidget()
        self.anomaly_list.setStyleSheet("""
            QListWidget { 
                background-color: #151a2b; 
                color: #e0e6ff; 
                border: 1px solid #2a3550;
            }
            QListWidget::item { padding: 8px; }
            QListWidget::item:selected { background-color: #ff3333; }
        """)
        
        layout.addWidget(QtWidgets.QLabel("Detected Novel Interactions:"))
        layout.addWidget(self.anomaly_list)
        
        # Buttons
        btn_layout = QtWidgets.QHBoxLayout()
        
        clear_btn = QtWidgets.QPushButton("Clear")
        clear_btn.clicked.connect(self._clear_all)
        
        export_btn = QtWidgets.QPushButton("Export Analysis")
        export_btn.clicked.connect(self._export_analysis)
        
        btn_layout.addStretch()
        btn_layout.addWidget(clear_btn)
        btn_layout.addWidget(export_btn)
        
        layout.addLayout(btn_layout)
        
        return widget
    
    def record_observation(self, population_size: int, generation: int,
                          polygons: List[Dict], fitness_scores: List[float]):
        """Record a single observation."""
        # Compute T metrics
        positions = np.array([p['position'][:2] for p in polygons])
        t_position_variance = float(np.var(positions))
        
        center = np.mean(positions, axis=0) if len(positions) > 0 else np.array([0, 0])
        angles = [np.arctan2(p[1] - center[1], p[0] - center[0]) for p in positions]
        t_angle_variance = float(np.var(angles)) if angles else 0.0
        
        # Compute N metrics
        fitness_best = float(np.max(fitness_scores))
        fitness_avg = float(np.mean(fitness_scores))
        fitness_std = float(np.std(fitness_scores))
        
        metric = RangeMetrics(
            population_size=population_size,
            generation=generation,
            t_position_variance=t_position_variance,
            t_angle_variance=t_angle_variance,
            fitness_best=fitness_best,
            fitness_avg=fitness_avg,
            fitness_std=fitness_std,
            timestamp=time.time()
        )
        
        self.range_data[population_size].append(metric)
        self.anomaly_detector.record_observation(population_size, generation, metric)
    
    def _update_displays(self):
        """Update all visualization tabs."""
        if not self.range_data:
            return
        
        # Color palette for different population sizes
        colors = {
            10: '#ff3333',   # Red
            20: '#4169e1',   # Blue
            30: '#00ff00',   # Green
            50: '#ffaa00',   # Orange
            100: '#9932cc',  # Purple
        }
        
        # Update fitness plot
        self.plot_fitness.clear()
        self.fitness_curves = {}
        for pop_size in sorted(self.range_data.keys()):
            metrics = self.range_data[pop_size]
            generations = [m.generation for m in metrics]
            fitnesses = [m.fitness_best for m in metrics]
            
            color = colors.get(pop_size, f'#{np.random.randint(0, 256):02x}{np.random.randint(0, 256):02x}{np.random.randint(0, 256):02x}')
            curve = self.plot_fitness.plot(
                generations, fitnesses,
                pen=pg.mkPen(color, width=2),
                name=f'N={pop_size}'
            )
            self.fitness_curves[pop_size] = curve
        
        # Update variance plot
        self.plot_variance.clear()
        self.variance_curves = {}
        for pop_size in sorted(self.range_data.keys()):
            metrics = self.range_data[pop_size]
            generations = [m.generation for m in metrics]
            variances = [max(m.t_position_variance, 1e-6) for m in metrics]
            
            color = colors.get(pop_size, f'#{np.random.randint(0, 256):02x}{np.random.randint(0, 256):02x}{np.random.randint(0, 256):02x}')
            curve = self.plot_variance.plot(
                generations, variances,
                pen=pg.mkPen(color, width=2),
                name=f'N={pop_size}'
            )
            self.variance_curves[pop_size] = curve
        
        # Update heatmap
        self._update_heatmap()
        
        # Update anomalies
        self._update_anomalies()
        
        # Update stats
        pop_sizes = list(self.range_data.keys())
        max_gen = max([max([m.generation for m in metrics]) for metrics in self.range_data.values()])
        anomalies = self.anomaly_detector.detect_anomalies()
        
        self.stat_ranges.setText(f"Population Ranges: {min(pop_sizes)}-{max(pop_sizes)}")
        self.stat_anomalies.setText(f"Novel Events: {len(anomalies)}")
        self.stat_generations.setText(f"Generations: {max_gen + 1}")
    
    def _update_heatmap(self):
        """Create heatmap visualization."""
        pop_sizes = sorted(self.range_data.keys())
        if not pop_sizes:
            return
        
        max_gen = max([max([m.generation for m in self.range_data[ps]]) for ps in pop_sizes]) + 1
        
        # Create heatmap data
        heatmap_data = np.zeros((len(pop_sizes), max_gen))
        
        for i, pop_size in enumerate(pop_sizes):
            for metric in self.range_data[pop_size]:
                heatmap_data[i, metric.generation] = metric.fitness_best
        
        self.heatmap_img.setImage(heatmap_data, autoRange=False, autoLevels=True)
    
    def _update_anomalies(self):
        """Update anomalies display."""
        anomalies = self.anomaly_detector.detect_anomalies()
        
        self.anomaly_list.clear()
        for anomaly in anomalies[-20:]:  # Show last 20
            text = (f"[N={anomaly['pop_size']}] Gen {anomaly['generation']}: "
                   f"{anomaly['type'].replace('_', ' ').title()} - {anomaly['reason']}")
            
            item = QtWidgets.QListWidgetItem(text)
            if anomaly['type'] == 'fitness_jump':
                item.setForeground(QtGui.QColor('#00ff00'))
            elif anomaly['type'] == 'variance_collapse':
                item.setForeground(QtGui.QColor('#ffaa00'))
            
            self.anomaly_list.addItem(item)
    
    def _clear_all(self):
        """Clear all data."""
        self.range_data.clear()
        self.anomaly_detector.history.clear()
        self.anomaly_list.clear()
    
    def _export_analysis(self):
        """Export analysis to CSV."""
        import csv
        from pathlib import Path
        
        if not self.range_data:
            QtWidgets.QMessageBox.warning(self, "No Data", "No data to export.")
            return
        
        filepath = Path.cwd() / "range_analysis.csv"
        
        try:
            with open(filepath, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'population_size', 'generation', 't_position_variance',
                    't_angle_variance', 'fitness_best', 'fitness_avg', 'fitness_std'
                ])
                
                for pop_size in sorted(self.range_data.keys()):
                    for m in self.range_data[pop_size]:
                        writer.writerow([
                            m.population_size, m.generation, m.t_position_variance,
                            m.t_angle_variance, m.fitness_best, m.fitness_avg, m.fitness_std
                        ])
            
            QtWidgets.QMessageBox.information(self, "Export Success", f"Saved to {filepath}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Export Error", str(e))


def create_range_analyzer(parent=None) -> RangeConvergenceAnalyzer:
    """Factory function."""
    return RangeConvergenceAnalyzer(parent)
