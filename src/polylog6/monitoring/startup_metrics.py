"""
Tracks startup metrics for the monitoring system.
"""
import time
from typing import Dict, Any


class StartupMetrics:
    """Collects and reports startup performance metrics."""
    
    def __init__(self):
        self.metrics = {
            "unicode_load_time": 0.0,
            "schema_index_build": 0.0,
            "total_startup": 0.0
        }
        self.start_time = time.perf_counter()
    
    def record(self, metric_name: str, duration: float):
        """Record a specific metric duration."""
        self.metrics[metric_name] = duration
    
    def finalize(self):
        """Finalize total startup time."""
        self.metrics["total_startup"] = (time.perf_counter() - self.start_time) * 1000
    
    def as_dict(self) -> Dict[str, float]:
        """Return metrics as dictionary."""
        return self.metrics
