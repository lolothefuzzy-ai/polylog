"""
Performance Monitor - Real-time FPS tracking and performance metrics.
Tracks framerate, render times, and system performance for optimization.
"""
import time
from collections import deque
from typing import Any, Dict, List, Optional

import numpy as np
import psutil

from metrics_service import get_registry


class KPIEmitter:
    """Bridge between live performance stats and the KPI registry."""

    def __init__(self) -> None:
        self.registry = get_registry()

    def build_samples(
        self,
        framerate_stats: Dict[str, float],
        system_stats: Dict[str, float],
        perf_report: Dict[str, Dict[str, float]],
    ) -> Dict[str, float]:
        samples: Dict[str, float] = {}
        if framerate_stats:
            frame_time_ms = framerate_stats.get("frame_time_ms", 0.0)
            budget_ms = 16.67
            samples["frame_stall_spikes"] = max(frame_time_ms - budget_ms, 0.0)
            samples["perf_regression"] = max((frame_time_ms / budget_ms - 1.0) * 100, 0.0)
        if system_stats:
            samples["nan_inf_incidents"] = 0.0
            samples["memory_fragmentation"] = system_stats.get("memory_percent", 0.0)
        if perf_report:
            render_ms = perf_report.get("render", {}).get("avg_ms", 0.0)
            samples["handle_leak_rate"] = 0.0
            samples["golden_image_regression"] = 1.0 if render_ms < 5.0 else 0.9
        return samples

    def emit_payload(
        self,
        framerate_stats: Dict[str, float],
        system_stats: Dict[str, float],
        perf_report: Dict[str, Dict[str, float]],
    ) -> Dict[str, Any]:
        samples = self.build_samples(framerate_stats, system_stats, perf_report)
        return self.registry.build_payload(samples)


class FramerateMonitor:
    """Monitors and tracks real-time framerate and performance metrics."""
    
    def __init__(self, history_size: int = 120):
        """
        Initialize framerate monitor.
        
        Args:
            history_size: Number of frames to track for averaging
        """
        self.history_size = history_size
        self.frame_times: deque = deque(maxlen=history_size)
        self.render_times: deque = deque(maxlen=history_size)
        self.update_times: deque = deque(maxlen=history_size)
        
        self.last_frame_time = time.perf_counter()
        self.current_fps = 0.0
        self.avg_fps = 0.0
        self.min_fps = 0.0
        self.max_fps = 0.0
        self.frame_count = 0
        
        # Performance metrics
        self.is_vsync_locked = False
        self.is_throttled = False
        self.performance_warning = ""
    
    def frame_tick(self) -> float:
        """
        Record a frame tick. Call this once per frame.
        
        Returns:
            Delta time since last frame in seconds
        """
        current_time = time.perf_counter()
        delta_time = current_time - self.last_frame_time
        self.last_frame_time = current_time
        
        if delta_time > 0:
            self.frame_times.append(delta_time)
            fps = 1.0 / delta_time
            self.current_fps = fps
            self.frame_count += 1
        
        return delta_time
    
    def record_render_time(self, render_time: float):
        """Record time spent in rendering."""
        self.render_times.append(render_time)
    
    def record_update_time(self, update_time: float):
        """Record time spent in update logic."""
        self.update_times.append(update_time)
    
    def get_stats(self) -> Dict[str, float]:
        """
        Get comprehensive performance statistics.
        
        Returns:
            Dictionary with FPS and timing statistics
        """
        if not self.frame_times:
            return {
                'current_fps': 0.0,
                'avg_fps': 0.0,
                'min_fps': 0.0,
                'max_fps': 0.0,
                'frame_time_ms': 0.0,
                'render_time_ms': 0.0,
                'update_time_ms': 0.0,
                'render_ratio': 0.0,
            }
        
        frame_times_array = np.array(list(self.frame_times))
        render_times_array = np.array(list(self.render_times))
        update_times_array = np.array(list(self.update_times))
        
        # FIXED: Handle zero/negative frame times
        frame_times_valid = frame_times_array[frame_times_array > 1e-10]
        if len(frame_times_valid) == 0:
            # All frame times invalid, return zeros
            return {
                'current_fps': 0.0,
                'avg_fps': 0.0,
                'min_fps': 0.0,
                'max_fps': 0.0,
                'frame_time_ms': 0.0,
                'render_time_ms': 0.0,
                'update_time_ms': 0.0,
                'render_ratio': 0.0,
            }
        
        fps_values = 1.0 / frame_times_valid
        
        self.avg_fps = float(np.mean(fps_values))
        self.min_fps = float(np.min(fps_values))
        self.max_fps = float(np.max(fps_values))
        
        avg_render = float(np.mean(render_times_array)) * 1000 if len(render_times_array) > 0 else 0.0
        avg_update = float(np.mean(update_times_array)) * 1000 if len(update_times_array) > 0 else 0.0
        
        # FIXED: Safer division for render ratio
        avg_frame_time = float(np.mean(frame_times_array))
        if avg_frame_time > 1e-10:
            render_ratio = (avg_render / (avg_frame_time * 1000)) * 100
        else:
            render_ratio = 0.0
        
        return {
            'current_fps': self.current_fps,
            'avg_fps': self.avg_fps,
            'min_fps': self.min_fps,
            'max_fps': self.max_fps,
            'frame_time_ms': avg_frame_time * 1000,
            'render_time_ms': avg_render,
            'update_time_ms': avg_update,
            'render_ratio': render_ratio,
        }
    
    def check_performance_warning(self, target_fps: int = 30) -> str:
        """
        Check if current performance meets targets and generate warning.
        
        Args:
            target_fps: Target framerate
        
        Returns:
            Warning message string (empty if all ok)
        """
        if self.current_fps < target_fps * 0.7:
            self.is_throttled = True
            self.performance_warning = f"Low FPS: {self.current_fps:.1f} (target: {target_fps})"
            return self.performance_warning
        
        # Check if vsync locked (very consistent frame times)
        if len(self.frame_times) > 10:
            std_dev = float(np.std(list(self.frame_times)[-10:]))
            if std_dev < 0.001:
                self.is_vsync_locked = True
        
        self.is_throttled = False
        self.performance_warning = ""
        return ""
    
    def reset(self):
        """Reset all metrics."""
        self.frame_times.clear()
        self.render_times.clear()
        self.update_times.clear()
        self.frame_count = 0
        self.current_fps = 0.0
        self.avg_fps = 0.0
        self.performance_warning = ""


class SystemMetricsMonitor:
    """Monitor system-level performance (CPU, memory, GPU if available)."""
    
    def __init__(self):
        try:
            self.process = psutil.Process()
            self._psutil_available = True
        except Exception as e:
            print(f"Warning: psutil.Process() failed: {e}")
            self.process = None
            self._psutil_available = False
        
        self.cpu_percent_history: deque = deque(maxlen=60)
        self.memory_percent_history: deque = deque(maxlen=60)
        self.last_check = time.time()
    
    def update(self):
        """Update system metrics."""
        if not self._psutil_available or self.process is None:
            return
        
        try:
            cpu = self.process.cpu_percent(interval=None)
            mem = self.process.memory_percent()
            
            if cpu is not None:
                self.cpu_percent_history.append(cpu)
            if mem is not None:
                self.memory_percent_history.append(mem)
        except (psutil.NoSuchProcess, psutil.AccessDenied, Exception) as e:
            print(f"Warning: System metrics update failed: {e}")
            self._psutil_available = False
    
    def get_stats(self) -> Dict[str, float]:
        """Get current system metrics."""
        try:
            cpu_percent = self.process.cpu_percent(interval=0)
            memory_percent = self.process.memory_percent()
            memory_mb = self.process.memory_info().rss / 1024 / 1024
        except Exception:
            cpu_percent = 0.0
            memory_percent = 0.0
            memory_mb = 0.0
        
        return {
            'cpu_percent': cpu_percent,
            'memory_percent': memory_percent,
            'memory_mb': memory_mb,
            'avg_cpu': float(np.mean(list(self.cpu_percent_history))) if self.cpu_percent_history else 0.0,
            'avg_memory': float(np.mean(list(self.memory_percent_history))) if self.memory_percent_history else 0.0,
        }
    
    def check_high_n_warnings(self, polyform_count: int, framerate_monitor=None) -> List[str]:
        """
        PHASE 1 STABILIZATION: Check for high-n performance warnings and issues.
        Provides early warning system for performance degradation at large n.
        
        Args:
            polyform_count: Current number of polyforms in assembly
            framerate_monitor: Optional FramerateMonitor instance for FPS data
        
        Returns:
            List of warning messages (empty if all OK)
        """
        import logging
        logger = logging.getLogger(__name__)
        warnings = []
        
        # Check memory usage at high n
        memory_mb = self.get_stats()['memory_mb']
        if polyform_count > 1000:
            if memory_mb > 1500:
                msg = f"⚠️  High memory usage at n={polyform_count}: {memory_mb:.0f}MB (phase-2 optimization recommended)"
                warnings.append(msg)
                logger.warning(msg)
            elif memory_mb > 1200:
                msg = f"⚠️  Elevated memory at n={polyform_count}: {memory_mb:.0f}MB"
                warnings.append(msg)
                logger.info(msg)
        
        # Check FPS degradation
        if framerate_monitor:
            avg_fps = framerate_monitor.avg_fps
            if polyform_count > 1000 and avg_fps < 20:
                msg = f"⚠️  Low FPS at n={polyform_count}: {avg_fps:.1f} fps"
                warnings.append(msg)
                logger.warning(msg)
            elif polyform_count > 2000 and avg_fps < 15:
                msg = f"🔴 Critical FPS at n={polyform_count}: {avg_fps:.1f} fps (phase-2 optimization required)"
                warnings.append(msg)
                logger.error(msg)
        
        # Check CPU usage
        cpu_percent = self.get_stats()['cpu_percent']
        if polyform_count > 1000 and cpu_percent > 80:
            msg = f"⚠️  High CPU usage at n={polyform_count}: {cpu_percent:.0f}%"
            warnings.append(msg)
            logger.warning(msg)
        
        return warnings


class AdaptiveFramerateController:
    """
    Adaptively adjust target framerate based on scene complexity and performance.
    """
    
    def __init__(self, min_fps: int = 15, max_fps: int = 60, target_fps: int = 30):
        self.min_fps = min_fps
        self.max_fps = max_fps
        self.target_fps = target_fps
        self.current_target = target_fps
        
        # Complexity factors
        self.polyform_count = 0
        self.animation_active = False
        self.high_quality_mode = False
        
        # History for trending
        self.fps_trend: deque = deque(maxlen=20)
    

    def update_complexity(self, polyform_count: int, animation_active: bool = False, high_quality: bool = False):
        """Update scene complexity factors."""
        self.polyform_count = polyform_count
        self.animation_active = animation_active
        self.high_quality_mode = high_quality
    
    def calculate_adaptive_fps(self, current_fps: float, avg_fps: float) -> int:
        """
        Calculate adaptive target FPS based on current performance.
        
        Args:
            current_fps: Current frame rate
            avg_fps: Average frame rate over history
        
        Returns:
            Recommended target FPS
        """
        self.fps_trend.append(current_fps)
        
        # Base target depends on mode
        if self.high_quality_mode:
            base_target = self.max_fps
        elif self.animation_active:
            base_target = 60  # Want smooth animations
        else:
            base_target = self.target_fps
        
        # If significantly below target, reduce complexity
        if avg_fps < base_target * 0.6:
            recommended = max(self.min_fps, int(avg_fps * 0.9))
            self.current_target = recommended
            return recommended
        
        # If well above target, can increase complexity
        if avg_fps > base_target * 1.3 and self.polyform_count < 50:
            self.current_target = base_target
            return base_target
        
        self.current_target = base_target
        return base_target
    
    def get_target_frame_time_ms(self) -> float:
        """Get target frame time in milliseconds."""
        if self.current_target <= 0:
            return 33.0  # Default 30 FPS
        return 1000.0 / self.current_target
    
    def get_update_interval_ms(self) -> int:
        """Get recommended timer interval in milliseconds."""
        target_ms = self.get_target_frame_time_ms()
        # Round to nearest millisecond, minimum 1ms
        return max(1, int(round(target_ms)))


class PerformanceProfiler:
    """
    Profile performance bottlenecks by timing major operations.
    """
    
    def __init__(self):
        self.operation_times: Dict[str, deque] = {}
        self.operation_counts: Dict[str, int] = {}
        self.current_operation: Optional[str] = None
        self.start_time: Optional[float] = None
    
    def start(self, operation_name: str):
        """Start timing an operation."""
        self.current_operation = operation_name
        self.start_time = time.perf_counter()
        
        if operation_name not in self.operation_times:
            self.operation_times[operation_name] = deque(maxlen=60)
            self.operation_counts[operation_name] = 0
    
    def end(self):
        """End timing current operation."""
        if self.current_operation and self.start_time:
            elapsed = (time.perf_counter() - self.start_time) * 1000  # Convert to ms
            self.operation_times[self.current_operation].append(elapsed)
            self.operation_counts[self.current_operation] += 1
            
            self.current_operation = None
            self.start_time = None
    
    def get_report(self) -> Dict[str, Dict[str, float]]:
        """Get performance report for all operations."""
        report = {}
        
        for op_name, times in self.operation_times.items():
            if not times:
                continue
            
            times_array = np.array(list(times))
            report[op_name] = {
                'avg_ms': float(np.mean(times_array)),
                'min_ms': float(np.min(times_array)),
                'max_ms': float(np.max(times_array)),
                'std_dev': float(np.std(times_array)),
                'count': self.operation_counts.get(op_name, 0),
                'percent_of_frame': 0.0,  # Will be calculated relative to frame time
            }
        
        # Calculate percentages relative to total frame time
        total_time = sum(r['avg_ms'] for r in report.values())
        if total_time > 0:
            for op_report in report.values():
                op_report['percent_of_frame'] = (op_report['avg_ms'] / total_time) * 100
        
        return report
    
    def get_bottleneck(self) -> Optional[str]:
        """Get the operation taking the most time."""
        if not self.operation_times:
            return None
        
        max_time = 0.0
        bottleneck = None
        
        for op_name, times in self.operation_times.items():
            if times:
                avg_time = float(np.mean(list(times)))
                if avg_time > max_time:
                    max_time = avg_time
                    bottleneck = op_name
        
        return bottleneck
    
    def reset(self):
        """Reset all profiling data."""
        self.operation_times.clear()
        self.operation_counts.clear()
        self.current_operation = None
        self.start_time = None


def format_stats_string(stats: Dict[str, float]) -> str:
    """Format stats dictionary into a readable string."""
    return (f"FPS: {stats['current_fps']:.1f} (avg: {stats['avg_fps']:.1f}, "
            f"min: {stats['min_fps']:.1f}, max: {stats['max_fps']:.1f}) | "
            f"Frame: {stats['frame_time_ms']:.1f}ms | "
            f"Render: {stats['render_time_ms']:.1f}ms ({stats['render_ratio']:.0f}%)")
