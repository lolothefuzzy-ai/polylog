"""Combinatorial simulator engine (minimal viable implementation).

Provides fast parameter grid generation and assisted vs automated sweep
strategies with lightweight history tracking. Designed as a foundation for
subsequent GUI, API, and automation integrations.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Generator, List, Optional

import numpy as np


class ExplorationMode(Enum):
    """Exploration strategies supported by the simulator."""

    ASSISTED = "assisted"
    AUTOMATED = "automated"


@dataclass
class SimulationParameters:
    """Parameter ranges for T, N, n, s axes."""

    T_range: tuple[float, float] = (0.1, 10.0)
    N_range: tuple[int, int] = (1, 1000)
    n_range: tuple[int, int] = (2, 50)
    s_range: tuple[int, int] = (1, 10)


class CombinatorialSimulator:
    """Minimal combinatorial simulator with history capture."""

    def __init__(self) -> None:
        self.params = SimulationParameters()
        self.mode: ExplorationMode = ExplorationMode.ASSISTED
        self.live_tracking: bool = True
        self.history: List[Dict[str, float]] = []

    # ------------------------------------------------------------------
    # Parameter space utilities
    # ------------------------------------------------------------------
    def generate_parameter_grid(self) -> Generator[Dict[str, float], None, None]:
        """Generate T×N combinations with fixed n and s for MVP."""

        T_start, T_stop = self.params.T_range
        N_start, N_stop = self.params.N_range

        for T in np.linspace(T_start, T_stop, num=10):
            for N in range(N_start, N_stop + 1, max(1, (N_stop - N_start) // 10 or 1)):
                yield {"T": float(T), "N": int(N), "n": 5, "s": 2}

    # ------------------------------------------------------------------
    # Execution helpers
    # ------------------------------------------------------------------
    def run_parameter_sweep(self, params: Optional[Dict[str, float]] = None) -> Dict[str, object]:
        """Execute simulation using current mode and record results."""

        params = params or {}
        combinations = list(self.generate_parameter_grid())
        self.history.extend(combinations)

        return {
            "status": "simulated",
            "mode": self.mode.value,
            "parameters": params,
            "samples": len(combinations),
        }

    def set_mode(self, mode: ExplorationMode) -> None:
        """Update exploration mode."""

        self.mode = mode

    def toggle_live_tracking(self, enabled: bool) -> None:
        """Enable or disable live tracking output."""

        self.live_tracking = enabled

    def clear_history(self) -> None:
        """Reset stored simulation combinations."""

        self.history.clear()
