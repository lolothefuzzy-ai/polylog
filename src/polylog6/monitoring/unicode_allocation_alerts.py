"""
Alerts for unicode symbol allocation.
"""
from typing import Dict, Any


class UnicodeAllocationAlerts:
    """Alerts for unicode symbol allocation."""
    
    def __init__(self):
        self.thresholds = {
            "unicode_remaining_warn": 100,
            "unicode_remaining_critical": 10
        }
        
    def check(self, unicode_remaining: int) -> Dict[str, Any]:
        """Check unicode allocation against thresholds."""
        alerts = []
        
        if unicode_remaining < self.thresholds["unicode_remaining_critical"]:
            alerts.append({
                "code": "critical_unicode_symbols",
                "severity": "CRITICAL",
                "message": f"Only {unicode_remaining} unicode symbols remaining"
            })
        elif unicode_remaining < self.thresholds["unicode_remaining_warn"]:
            alerts.append({
                "code": "warn_unicode_symbols",
                "severity": "WARN",
                "message": f"Only {unicode_remaining} unicode symbols remaining"
            })
            
        return {"alerts": alerts}
