"""Hardware capability detection and tier classification helpers."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Literal

import psutil

try:  # pragma: no cover - optional GPU detection dependency
    import pynvml
except ImportError:  # pragma: no cover - tolerate missing NVML bindings
    pynvml = None


HardwareTier = Literal["low", "mid", "high"]


@dataclass(slots=True)
class HardwareProfile:
    """Snapshot of host hardware resources used for adaptive configuration."""

    cpu_cores: int
    ram_gb: float
    vram_gb: float
    tier: HardwareTier

    @property
    def max_memory_mb(self) -> float:
        return self.ram_gb * 1024.0

    @property
    def max_vram_mb(self) -> float:
        return self.vram_gb * 1024.0


_RAM_THRESHOLDS = {
    "low": 8.0,
    "mid": 16.0,
    "high": 32.0,
}

_VRAM_THRESHOLDS = {
    "low": 4.0,
    "mid": 8.0,
    "high": 16.0,
}


@lru_cache(maxsize=1)
def detect_capability() -> HardwareProfile:
    """Detect system hardware profile and assign capability tier."""

    cpu_count = psutil.cpu_count(logical=False) or psutil.cpu_count() or 1
    ram_gb = psutil.virtual_memory().total / 1024**3
    vram_gb = _detect_vram_gb()

    tier = _classify_tier(ram_gb=ram_gb, vram_gb=vram_gb, cores=cpu_count)
    return HardwareProfile(cpu_cores=cpu_count, ram_gb=ram_gb, vram_gb=vram_gb, tier=tier)


def _detect_vram_gb() -> float:
    if pynvml is None:
        return 0.0

    try:
        pynvml.nvmlInit()
    except Exception:  # pragma: no cover - NVML init failure
        return 0.0

    try:
        device_count = pynvml.nvmlDeviceGetCount()
        if device_count == 0:
            return 0.0
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        info = pynvml.nvmlDeviceGetMemoryInfo(handle)
        return info.total / 1024**3
    except Exception:  # pragma: no cover - GPU detection fallback
        return 0.0
    finally:
        try:
            pynvml.nvmlShutdown()
        except Exception:  # pragma: no cover - ignore shutdown failure
            pass


def _classify_tier(*, ram_gb: float, vram_gb: float, cores: int) -> HardwareTier:
    if ram_gb >= _RAM_THRESHOLDS["high"] and vram_gb >= _VRAM_THRESHOLDS["high"] and cores >= 16:
        return "high"
    if ram_gb >= _RAM_THRESHOLDS["mid"] and vram_gb >= _VRAM_THRESHOLDS["mid"] and cores >= 8:
        return "mid"
    return "low"


__all__ = ["HardwareProfile", "detect_capability", "HardwareTier"]
