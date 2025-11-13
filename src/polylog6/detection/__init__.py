"""Detection pipeline package.

Exports service interfaces and FastAPI router for the INT-014 image detection track.
"""

from .service import ImageDetectionService, DetectionTask
from .api import router
from .assets import default_assets_dir

__all__ = [
    "ImageDetectionService",
    "DetectionTask",
    "router",
    "default_assets_dir",
]
