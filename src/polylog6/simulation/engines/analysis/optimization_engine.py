"""Fold-angle smoothing and lightweight optimization helpers."""

from __future__ import annotations

from statistics import fmean
from typing import Callable, Iterable, List, Mapping, Optional, Sequence


class OptimizationEngine:
    """Apply simple smoothing heuristics to fold angles produced by the engine."""

    def __init__(
        self,
        *,
        smoothing_window: int = 5,
        config: Optional[Mapping[str, int]] = None,
    ) -> None:
        if config is not None:
            smoothing_window = int(config.get("smoothing_window", smoothing_window))
        if smoothing_window < 1:
            raise ValueError("smoothing_window must be >= 1")
        self._window = smoothing_window

    def optimize_fold(self, assembly) -> object:
        """Smooth fold angles in-place on ``assembly`` when available."""

        angles = _coerce_sequence(getattr(assembly, "get_fold_angles", None))
        if angles is None:
            return assembly

        smoothed = self._smooth_angles(angles)
        setter = getattr(assembly, "set_fold_angles", None)
        if callable(setter):
            setter(smoothed)
        return assembly

    def _smooth_angles(self, angles: Sequence[float]) -> List[float]:
        if len(angles) <= 1 or self._window == 1:
            return list(angles)

        half_window = self._window // 2
        padded = list(angles)
        result: List[float] = []
        for index in range(len(padded)):
            start = max(0, index - half_window)
            stop = min(len(padded), index + half_window + 1)
            window = padded[start:stop]
            result.append(float(fmean(window)))
        return result


def _coerce_sequence(func: Optional[Callable[[], Iterable[float]]]) -> Optional[Sequence[float]]:
    if not callable(func):
        return None
    try:
        values = func()
    except Exception:  # pragma: no cover - defensive guard
        return None
    if values is None:
        return None
    if isinstance(values, Iterable):
        return list(values)
    return None


__all__ = ["OptimizationEngine"]
