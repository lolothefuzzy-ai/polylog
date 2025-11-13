"""Tier 3 candidate ingestion helpers wired to simulation checkpoints."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import math
import hashlib
import json
from typing import Callable, Dict, Iterable, List, Mapping, Optional

from polylog6.combinatorial import AssemblyView, CombinatorialCalculator
from polylog6.hardware import HardwareProfile, detect_capability
from polylog6.simulation.stability.calculator import StabilityCalculator, StabilityObservation
from polylog6.storage.tier3_catalog import Tier3Candidate, Tier3Catalog, now_iso
from polylog6.simulation.engines.checkpointing.polyform_engine import CheckpointSummary
from polylog6.simulation.engines.checkpointing.workspace import PolyformWorkspace


@dataclass(slots=True)
class CandidateSeed:
    """Lightweight payload describing a potential Tier 3 candidate."""

    summary: CheckpointSummary
    workspace: PolyformWorkspace


class Tier3CandidateIngestionPipeline:
    """Builds Tier 3 candidates from simulation checkpoints."""

    def __init__(
        self,
        catalog: Tier3Catalog,
        *,
        scaler_tables: Optional[Mapping[str, object]] = None,
        calculator: Optional[CombinatorialCalculator] = None,
        scaler_tables_path: Optional[Path] = None,
        hardware_profile: Optional[HardwareProfile] = None,
        capability_detector: Callable[[], HardwareProfile] = detect_capability,
        stability_calculator: Optional[StabilityCalculator] = None,
    ) -> None:
        self.catalog = catalog
        self._scaler_tables = scaler_tables or self._load_scaler_tables(scaler_tables_path)
        self.hardware_profile = hardware_profile or capability_detector()
        if calculator is None:
            self._calculator = CombinatorialCalculator(
                self._scaler_tables,
                hardware_profile=self.hardware_profile,
            )
        else:
            self._calculator = calculator
            if getattr(self._calculator, "hardware_profile", None) is None:
                self._calculator.hardware_profile = self.hardware_profile
        self._stability_calculator = stability_calculator or StabilityCalculator()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def ingest_checkpoint(self, summary: CheckpointSummary, workspace: PolyformWorkspace) -> None:
        """Extract, filter, and persist Tier 3 candidates for a checkpoint."""

        seeds = self._extract_candidates(summary, workspace)
        for seed in seeds:
            if not self._passes_filters(seed):
                continue
            candidate = self._build_candidate(seed)
            self.catalog.upsert_candidate(candidate)

    # ------------------------------------------------------------------
    # Extraction / filtering helpers
    # ------------------------------------------------------------------
    def _extract_candidates(
        self, summary: CheckpointSummary, workspace: PolyformWorkspace
    ) -> Iterable[CandidateSeed]:
        """Derive candidate seeds from a checkpoint.

        The default implementation treats the entire workspace as a single
        candidate seed. More advanced pipelines can override this method to
        yield multiple seeds per checkpoint (e.g., cluster-level assemblies).
        """

        if workspace is None:
            return []
        return [CandidateSeed(summary=summary, workspace=workspace)]

    def _passes_filters(self, seed: CandidateSeed) -> bool:
        """Apply baseline heuristics so we only ingest meaningful assemblies."""

        workspace = seed.workspace
        if workspace is None:
            return False

        polygon_count = workspace.polygon_count()
        if polygon_count == 0:
            # Discard empty checkpoints.
            return False

        # If every polygon lives in its own module and there is only a single
        # module reference, we skip to avoid duplicates attached to one face.
        module_refs = workspace.module_references()
        if len(module_refs) <= 1 and polygon_count == 1:
            return False

        return True

    # ------------------------------------------------------------------
    # Candidate construction
    # ------------------------------------------------------------------
    def _build_candidate(self, seed: CandidateSeed) -> Tier3Candidate:
        summary = seed.summary
        workspace = seed.workspace

        encoded_polygons = list(workspace.iter_encoded_polygons())
        polygon_count = workspace.polygon_count()
        module_refs = workspace.module_references()

        signature = self._signature_from_workspace(summary, workspace)
        candidate_id = f"{summary.label}-{signature[:8]}"

        core_components = self._derive_components(module_refs, polygon_count)
        assembly_graph = self._build_assembly_graph(module_refs)

        observation = self._stability_calculator.compute(
            encoded_polygons,
            require_two_axes=bool(module_refs),
        )

        raw_metrics = self._compute_metrics(summary, workspace, encoded_polygons, observation)
        raw_metrics.update(self._compute_combinatorial_metrics(encoded_polygons))
        stability_score = self._stability_from_metrics(raw_metrics, polygon_count)

        return Tier3Candidate(
            candidate_id=candidate_id,
            signature=signature,
            core_components=core_components,
            assembly_graph=assembly_graph,
            raw_metrics=raw_metrics,
            stability_score=stability_score,
            created_at=now_iso(),
            last_promoted_at=None,
            probation_until=None,
            status="pending",
            eligible_for_unicode=False,
            tags=["auto_ingested"],
            notes=f"Ingested from checkpoint {summary.label}",
            metadata={
                "checkpoint_label": summary.label,
                "chunk_count": summary.chunk_count,
            },
            promotion_log=[],
        )

    def _signature_from_workspace(self, summary: CheckpointSummary, workspace: PolyformWorkspace) -> str:
        payload: Dict[str, object] = {
            "label": summary.label,
            "polygons": workspace.polygon_count(),
            "module_refs": workspace.module_references(),
        }
        serialized = json.dumps(payload, sort_keys=True, default=repr).encode("utf-8")
        return hashlib.sha256(serialized).hexdigest()

    def _derive_components(self, module_refs: List[tuple[int, int]], polygon_count: int) -> List[str]:
        if module_refs:
            return [f"module-{chunk}-{ref}" for chunk, ref in module_refs]
        return [f"workspace-polygons-{polygon_count}"]

    def _build_assembly_graph(self, module_refs: List[tuple[int, int]]) -> Dict[str, Dict[str, object]]:
        graph: Dict[str, Dict[str, object]] = {}
        for index, (chunk, ref) in enumerate(module_refs):
            graph[f"edge-{index}"] = {
                "from": f"chunk-{chunk}",
                "to": f"module-{ref}",
            }
        return graph

    def _compute_metrics(
        self,
        summary: CheckpointSummary,
        workspace: PolyformWorkspace,
        encoded_polygons: Iterable,
        observation: StabilityObservation,
    ) -> Dict[str, float]:
        polygons = workspace.polygon_count()
        module_refs = len(workspace.module_references())
        metrics: Dict[str, float] = {
            "polygon_count": float(polygons),
            "module_ref_count": float(module_refs),
            "timestamp": float(summary.timestamp),
        }
        metrics.update(observation.as_dict())
        return metrics

    def _compute_combinatorial_metrics(self, encoded_polygons: List) -> Dict[str, float]:
        if not encoded_polygons:
            return {}

        composition: Dict[str, int] = {}
        for polygon in encoded_polygons:
            try:
                symbol = self._calculator.registry.primitive_symbol(polygon.sides)
            except ValueError:
                symbol = f"sides-{polygon.sides}"
            composition[symbol] = composition.get(symbol, 0) + 1

        assembly = AssemblyView(
            composition=composition,
            polygons=encoded_polygons,
            symmetry_group=None,
        )

        try:
            o_value = float(self._calculator.calculate_O(assembly))
        except Exception:
            o_value = 0.0

        if o_value <= 0.0:
            return {"O": 0.0, "I": 0.0, "log_O": float("-inf")}

        try:
            i_value = float(self._calculator.calculate_I(assembly, O_value=o_value))
        except Exception:
            i_value = 0.0

        log_o = math.log(o_value) if o_value > 0.0 else float("-inf")
        return {
            "O": o_value,
            "I": i_value,
            "log_O": float(log_o),
        }

    def _stability_from_metrics(self, metrics: Mapping[str, float], polygon_count: int) -> float:
        score = metrics.get("stability_score")
        if score is not None:
            return max(0.0, min(1.0, float(score)))
        if polygon_count == 0:
            return 0.0
        density = metrics.get("density", 0.0)
        return max(0.0, min(1.0, 1.0 - 1.0 / (density + 1.0)))

    def _load_scaler_tables(self, provided_path: Optional[Path]) -> Mapping[str, object]:
        path = provided_path or Path("catalogs/scaler_tables.json")
        if not path.exists():
            return {}
        try:
            with path.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        except Exception:
            return {}


__all__ = ["Tier3CandidateIngestionPipeline", "CandidateSeed"]
