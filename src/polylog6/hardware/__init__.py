"""Hardware detection utilities for adaptive runtime configuration."""
from .capability import HardwareProfile, HardwareTier, detect_capability

__all__ = ["HardwareProfile", "HardwareTier", "detect_capability"]
