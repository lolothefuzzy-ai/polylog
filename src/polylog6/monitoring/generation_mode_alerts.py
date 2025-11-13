"""
Alerts for generation mode.
"""
from typing import Dict, Any


class GenerationModeAlerts:
    """Alerts for generation mode performance."""
    
    def __init__(self):
        self.thresholds = {
            "discovery_rate_min": 10,  # polyforms/min
            "queue_depth_max": 1000,
            "unicode_remaining_warn": 100
        }
        
    def check(
        self,
        discovery_rate: float,
        queue_depth: int,
        unicode_remaining: int
    ) -> Dict[str, Any]:
        """Check metrics against thresholds."""
        alerts = []
        
        if discovery_rate < self.thresholds["discovery_rate_min"]:
            alerts.append({
                "code": "low_discovery_rate",
                "severity": "WARN",
                "message": f"Discovery rate {discovery_rate:.1f} < {self.thresholds['discovery_rate_min']} polyforms/min"
            })
            
        if queue_depth > self.thresholds["queue_depth_max"]:
            alerts.append({
                "code": "high_queue_depth",
                "severity": "ERROR",
                "message": f"Queue depth {queue_depth} > {self.thresholds['queue_depth_max']}"
            })
            
        if unicode_remaining < self.thresholds["unicode_remaining_warn"]:
            alerts.append({
                "code": "low_unicode_symbols",
                "severity": "WARN",
                "message": f"Only {unicode_remaining} unicode symbols remaining"
            })
            
        return {"alerts": alerts}
