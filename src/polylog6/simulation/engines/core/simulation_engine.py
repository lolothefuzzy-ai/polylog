"""Primary simulation engine coordinating geometry runtime and checkpoints."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Iterable, Optional

from polylog6.storage.encoder import EncodedPolygon
from polylog6.storage.manager import PolyformStorageManager

from ..checkpointing.polyform_engine import CheckpointSummary, PolyformEngine
from ..checkpointing.workspace import PolyformWorkspace
from ..guardrails import GuardrailConfig, GuardrailStatus, evaluate_guardrails
from polylog6.hardware import HardwareProfile, detect_capability


class SimulationEngine:
    """Facade that feeds the polyform workspace and produces periodic checkpoints."""

    def __init__(
        self,
        *,
        workspace: Optional[PolyformWorkspace] = None,
        storage_manager: Optional[PolyformStorageManager] = None,
        checkpoint_interval: int = 5,
        checkpoint_prefix: str = "checkpoint",
        inbox_path: Optional[Path] = None,
        guardrail_config: Optional[GuardrailConfig] = None,
        guardrail_alert: Optional[Callable[[GuardrailStatus], None]] = None,
        hardware_profile: Optional[HardwareProfile] = None,
        capability_detector: Callable[[], HardwareProfile] = detect_capability,
    ) -> None:
        if checkpoint_interval <= 0:
            raise ValueError("checkpoint_interval must be positive")

        self.hardware_profile = hardware_profile or capability_detector()
        self._checkpoint_interval = self._cap_interval_for_profile(
            checkpoint_interval,
            self.hardware_profile,
        )
        self._checkpoint_prefix = checkpoint_prefix
        self._checkpoint_index = 0
        self._tick_count = 0
        self._guardrail_config = guardrail_config
        self._guardrail_alert = guardrail_alert
        self._last_guardrail_status: Optional[GuardrailStatus] = None

        self.polyform_engine = PolyformEngine(
            workspace=workspace,
            storage_manager=storage_manager,
            inbox_path=inbox_path,
        )

    # ------------------------------------------------------------------
    # Workspace mutation helpers
    # ------------------------------------------------------------------
    @property
    def workspace(self) -> PolyformWorkspace:
        return self.polyform_engine.workspace

    def add_polygon(
        self,
        *,
        sides: int,
        orientation_index: int,
        rotation_count: int,
        delta: tuple[int, int, int],
    ) -> None:
        """Append a raw polygon produced by the geometry runtime."""

        self.workspace.add_polygon(
            sides=sides,
            orientation_index=orientation_index,
            rotation_count=rotation_count,
            delta=delta,
        )

    def add_encoded(self, polygon: EncodedPolygon) -> None:
        """Append an already-encoded polygon."""

        self.workspace.add_encoded(polygon)

    def extend(self, polygons: Iterable[EncodedPolygon]) -> None:
        """Append multiple encoded polygons."""

        self.workspace.extend(polygons)

    # ------------------------------------------------------------------
    # Checkpoint lifecycle
    # ------------------------------------------------------------------
    def tick(self, *, force: bool = False, label: Optional[str] = None) -> Optional[CheckpointSummary]:
        """Advance the checkpoint cadence and emit a checkpoint when due."""

        if not force:
            self._tick_count += 1
            if self._tick_count < self._checkpoint_interval:
                return None
        self._tick_count = 0
        checkpoint_label = label or self._next_label()

        if self._guardrail_config or self._guardrail_alert:
            self._last_guardrail_status = evaluate_guardrails(
                self.workspace,
                self._guardrail_config,
                on_alert=self._guardrail_alert,
            )
        else:
            self._last_guardrail_status = None

        return self.polyform_engine.checkpoint(checkpoint_label)

    def _next_label(self) -> str:
        label = f"{self._checkpoint_prefix}-{self._checkpoint_index:04d}"
        self._checkpoint_index += 1
        return label

    def restore(self, checkpoint_path: Path) -> None:
        """Restore workspace from a checkpoint file."""

        self.polyform_engine.restore_from(checkpoint_path)

    def clear(self) -> None:
        """Reset the managed workspace state."""

        self.workspace.clear()

    @property
    def last_guardrail_status(self) -> Optional[GuardrailStatus]:
        """Return the evaluation result from the most recent tick."""

        return self._last_guardrail_status

    @staticmethod
    def _cap_interval_for_profile(interval: int, profile: HardwareProfile) -> int:
        if interval <= 1:
            return 1

        tier_caps = {
            "low": 2,
            "mid": 5,
            "high": 10,
        }
        cap = tier_caps.get(profile.tier, 5)
        return max(1, min(interval, cap))


__all__ = ["SimulationEngine"]
