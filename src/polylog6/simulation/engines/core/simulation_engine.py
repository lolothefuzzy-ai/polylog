"""Primary simulation engine coordinating geometry runtime and checkpoints."""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import asdict
from pathlib import Path
from statistics import StatisticsError, mean, pstdev
from typing import Callable, Dict, Iterable, List, Optional, Sequence

from polylog6.storage.encoder import EncodedPolygon
from polylog6.storage.manager import PolyformStorageManager

from ..checkpointing.polyform_engine import CheckpointSummary, PolyformEngine
from ..checkpointing.workspace import PolyformWorkspace
from ..guardrails import GuardrailConfig, GuardrailStatus, evaluate_guardrails
from polylog6.hardware import HardwareProfile, detect_capability
from polylog6.simulation.metrics import (
    CandidateEvent,
    CanonicalSignatureFactory,
    FrequencyCounterPersistence,
    MetricsEmitter,
)

try:  # pragma: no cover - optional dependency during early integration
    from polylog6.storage.analyzers.symmetry_alignment import SymmetryAlignmentAnalyzer
except ImportError:  # pragma: no cover - analyzer introduced in later phases
    SymmetryAlignmentAnalyzer = None  # type: ignore


logger = logging.getLogger(__name__)


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
        metrics_emitter: Optional[MetricsEmitter] = None,
        frequency_counter: Optional[FrequencyCounterPersistence] = None,
        session_id: Optional[str] = None,
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

        self._metrics_emitter = metrics_emitter or MetricsEmitter()
        self._frequency_counter = frequency_counter or FrequencyCounterPersistence()
        self._frequency_counter.load()
        self._session_id = session_id or self._generate_session_id()
        self._symmetry_analyzer = (
            SymmetryAlignmentAnalyzer() if SymmetryAlignmentAnalyzer else None
        )
        self._metrics_enabled = True

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

        summary = self.polyform_engine.checkpoint(checkpoint_label)

        if summary is not None:
            self._handle_checkpoint(summary)

        return summary

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

    # ------------------------------------------------------------------
    # Metrics helpers
    # ------------------------------------------------------------------
    @property
    def session_id(self) -> str:
        """Return the current simulation session identifier."""

        return self._session_id

    def _handle_checkpoint(self, summary: CheckpointSummary) -> None:
        if not self._metrics_enabled:
            return

        try:
            candidates = self._extract_candidates(summary)
        except Exception:  # pragma: no cover - defensive logging
            logger.exception("Failed to extract candidates for summary %s", summary.label)
            candidates = []

        emitted = 0
        for candidate in candidates:
            try:
                self._emit_candidate(candidate)
                emitted += 1
            except Exception:  # pragma: no cover - defensive logging
                logger.exception("Failed to emit candidate event: %s", candidate)

        if emitted:
            logger.debug("Emitted %d candidate events for checkpoint %s", emitted, summary.label)

        try:
            rotated = self._frequency_counter.maybe_rotate()
            if rotated:
                logger.debug(
                    "Frequency counters rotated (rotation_count=%d)",
                    self._frequency_counter.rotation_count,
                )
        except Exception:  # pragma: no cover - defensive logging
            logger.exception("Failed to rotate frequency counters")

    def _extract_candidates(self, summary: CheckpointSummary) -> List[Dict]:
        snapshot = self._collect_checkpoint_snapshot(summary)
        if not snapshot:
            return []

        assemblies: Sequence[Dict] = snapshot.get("assemblies", [])  # type: ignore[assignment]
        if not assemblies:
            return []

        slider_state = snapshot.get("slider_state") or getattr(self.workspace, "slider_state", {})

        candidates: List[Dict] = []
        for assembly in assemblies:
            candidate = self._score_assembly(assembly, slider_state)
            if candidate is not None:
                candidates.append(candidate)
        return candidates

    def _collect_checkpoint_snapshot(self, summary: CheckpointSummary) -> Dict:
        workspace = self.workspace

        extractor = None
        for attr in (
            "serialize_for_metrics",
            "export_for_metrics",
            "to_metrics_payload",
            "to_dict",
            "as_dict",
        ):
            extractor = getattr(workspace, attr, None)
            if callable(extractor):
                break

        if callable(extractor):
            payload = extractor()
            if isinstance(payload, dict):
                return payload

        snapshot: Dict[str, Dict] = {
            "assemblies": getattr(workspace, "assemblies", []),
        }
        slider_state = getattr(workspace, "slider_state", None)
        if slider_state is not None:
            snapshot["slider_state"] = slider_state
        return snapshot

    def _score_assembly(self, assembly: Dict, slider_state: Dict) -> Optional[Dict]:
        polygons = self._coerce_polygon_list(assembly)
        if not polygons:
            return None

        composition = tuple(sorted(int(value) for value in polygons))

        symmetry_result = self._analyze_symmetry(assembly)
        symmetry_score = float(assembly.get("symmetry_score", symmetry_result["score"]))
        symmetry_group = assembly.get("symmetry_group", symmetry_result["group"])
        multi_edge_count = int(assembly.get("multi_edge_count", symmetry_result["multi_edge_count"]))

        scalers: List[float] = [float(val) for val in assembly.get("attachment_scalers", [])]
        scaler_stability = float(
            assembly.get("scaler_stability", self._compute_scaler_stability(scalers))
        )

        canonical_signature = CanonicalSignatureFactory.compute(
            composition,
            str(symmetry_group),
            scaler_stability,
        )

        self._frequency_counter.increment(canonical_signature)
        freq_entry = self._frequency_counter.map[canonical_signature]
        frequency_in_session = int(freq_entry["count"])

        shared_edges = self._count_shared_edges(assembly)

        if not self._passes_thresholds(
            symmetry_score=symmetry_score,
            shared_edges=shared_edges,
            scaler_stability=scaler_stability,
            frequency=frequency_in_session,
        ):
            return None

        candidate = CandidateEvent(
            event_id=self._generate_event_id(),
            session_id=self._session_id,
            timestamp=time.time(),
            canonical_signature=canonical_signature,
            composition=composition,
            symmetry_group=str(symmetry_group),
            symmetry_score=symmetry_score,
            shared_edges=shared_edges,
            multi_edge_count=multi_edge_count,
            attachment_scalers=scalers,
            scaler_stability=scaler_stability,
            frequency_in_session=frequency_in_session,
            slider_params=slider_state or {},
            candidate_hash=canonical_signature,
        )

        if not candidate.is_valid():
            return None

        return asdict(candidate)

    def _coerce_polygon_list(self, assembly: Dict) -> List[int]:
        if "composition" in assembly:
            value = assembly["composition"]
        else:
            value = assembly.get("polygons", [])

        if isinstance(value, dict):
            return [int(k) for k in value.values()]
        if isinstance(value, Sequence):
            return [int(v) for v in value]
        return []

    def _passes_thresholds(
        self,
        *,
        symmetry_score: float,
        shared_edges: int,
        scaler_stability: float,
        frequency: int,
    ) -> bool:
        return (
            symmetry_score >= 0.7
            and shared_edges >= 3
            and scaler_stability >= 0.75
            and frequency >= 3
        )

    def _emit_candidate(self, candidate: Dict) -> None:
        if not self._metrics_enabled:
            return
        self._metrics_emitter.emit(candidate)

    def _analyze_symmetry(self, assembly: Dict) -> Dict[str, float | int | str]:
        if "symmetry_group" in assembly and "symmetry_score" in assembly:
            return {
                "group": assembly["symmetry_group"],
                "score": float(assembly["symmetry_score"]),
                "multi_edge_count": int(assembly.get("multi_edge_count", 0)),
            }

        if not self._symmetry_analyzer:
            return {"group": "C1", "score": 0.0, "multi_edge_count": 0}

        try:
            result = self._symmetry_analyzer.detect_compound_structure(assembly)
        except Exception:  # pragma: no cover - analyzer may not be ready
            logger.exception("Symmetry analysis failed for assembly: %s", assembly)
            return {"group": "C1", "score": 0.0, "multi_edge_count": 0}

        if not result:
            return {"group": "C1", "score": 0.0, "multi_edge_count": 0}

        try:
            group = result.symmetry.group
            score = float(result.symmetry.score)
            multi_edge_count = len(getattr(result, "base_symbols", []))
        except AttributeError:  # pragma: no cover - defensive
            return {"group": "C1", "score": 0.0, "multi_edge_count": 0}

        return {"group": group, "score": score, "multi_edge_count": multi_edge_count}

    def _count_shared_edges(self, assembly: Dict) -> int:
        if "shared_edges" in assembly:
            try:
                return int(assembly["shared_edges"])
            except (TypeError, ValueError):  # pragma: no cover - defensive
                return 0

        adjacency = assembly.get("adjacency")
        if isinstance(adjacency, Sequence):
            return sum(
                1 for item in adjacency if isinstance(item, Sequence) and len(list(item)) >= 2
            )

        polygons = self._coerce_polygon_list(assembly)
        if len(polygons) <= 1:
            return 0
        return len(polygons) - 1

    def _compute_scaler_stability(self, scalers: Sequence[float]) -> float:
        if not scalers:
            return 1.0
        if len(scalers) == 1:
            return 1.0

        abs_scalers = [abs(float(val)) for val in scalers]
        mean_val = mean(abs_scalers)
        if mean_val == 0:
            return 0.0

        try:
            variability = pstdev(abs_scalers)
        except StatisticsError:  # pragma: no cover - should not happen when len >= 2
            variability = 0.0

        stability = max(0.0, 1.0 - variability / mean_val)
        return float(min(1.0, stability))

    @staticmethod
    def _generate_session_id() -> str:
        return f"sess_{uuid.uuid4().hex[:16]}"

    @staticmethod
    def _generate_event_id() -> str:
        return f"evt_{uuid.uuid4().hex[:16]}"


__all__ = ["SimulationEngine"]
