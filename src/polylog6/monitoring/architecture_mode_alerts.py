"""
Alerts for architecture mode.
"""
from typing import Dict, Any


class ArchitectureModeAlerts:
    """Alerts for architecture mode performance."""
    
    def __init__(self):
        self.thresholds = {
            "fold_latency_warn": 2000,  # ms
            "fold_latency_fail": 10000,
            "cache_hit_rate_min": 0.95,
            "geometric_rebuild_rate_max": 0.1
        }
        
    def check(
        self,
        fold_latency: float,
        cache_hit_rate: float,
        rebuild_rate: float
    ) -> Dict[str, Any]:
        """Check metrics against thresholds."""
        alerts = []
        
        if fold_latency > self.thresholds["fold_latency_fail"]:
            alerts.append({
                "code": "high_fold_latency",
                "severity": "ERROR",
                "message": f"Fold latency {fold_latency:.1f}ms > {self.thresholds['fold_latency_fail']}ms"
            })
        elif fold_latency > self.thresholds["fold_latency_warn"]:
            alerts.append({
                "code": "warn_fold_latency",
                "severity": "WARN",
                "message": f"Fold latency {fold_latency:.1f}ms > {self.thresholds['fold_latency_warn']}ms"
            })
            
        if cache_hit_rate < self.thresholds["cache_hit_rate_min"]:
            alerts.append({
                "code": "low_cache_hit_rate",
                "severity": "WARN",
                "message": f"Cache hit rate {cache_hit_rate:.2%} < {self.thresholds['cache_hit_rate_min']:.0%}"
            })
            
        if rebuild_rate > self.thresholds["geometric_rebuild_rate_max"]:
            alerts.append({
                "code": "high_rebuild_rate",
                "severity": "WARN",
                "message": f"Geometric rebuild rate {rebuild_rate:.2%} > {self.thresholds['geometric_rebuild_rate_max']:.0%}"
            })
            
        return {"alerts": alerts}
