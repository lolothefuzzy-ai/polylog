"""
Monitors memory footprint to ensure bounded growth.
"""
import os
import psutil
from typing import Dict, Any


class MemoryFootprintMonitor:
    """Monitors memory usage of the application."""
    
    def __init__(self):
        self.process = psutil.Process(os.getpid())
        
    def get_memory_usage(self) -> Dict[str, Any]:
        """Get current memory usage."""
        mem_info = self.process.memory_info()
        return {
            "rss": mem_info.rss,  # Resident Set Size
            "vms": mem_info.vms,  # Virtual Memory Size
            "percent": self.process.memory_percent()
        }
