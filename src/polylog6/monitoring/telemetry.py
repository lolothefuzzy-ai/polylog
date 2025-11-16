"""Telemetry for monitoring loop."""
import time
from dataclasses import dataclass, field
from typing import List


@dataclass
class MonitoringTelemetry:
    """Records telemetry for monitoring operations."""
    dispatch_times: List[float] = field(default_factory=list)
    total_iterations: int = 0
    
    def record_dispatch(self, duration: float):
        """Record a dispatch iteration duration."""
        self.dispatch_times.append(duration)
        
    def record_loop_completion(self, iterations: int):
        """Record loop completion with total iterations."""
        self.total_iterations = iterations
