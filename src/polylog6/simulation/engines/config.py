"""Shared configuration defaults for Polylog6 simulation engines."""

from __future__ import annotations

from typing import Mapping

DEFAULT_SCORE: float = 0.9

SMOOTHING_WINDOWS: Mapping[str, int] = {
    "stability": 5,
    "optimization": 3,
}
