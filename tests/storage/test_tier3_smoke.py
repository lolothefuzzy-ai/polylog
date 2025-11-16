"""End-to-end smoke tests for the Tier 3 promotion pipeline."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

from polylog6.simulation.engines.checkpointing.polyform_engine import CheckpointSummary
from polylog6.simulation.engines.checkpointing.workspace import PolyformWorkspace
from polylog6.storage.tier3_catalog import Tier3Catalog, Tier3Candidate
from polylog6.storage.tier3_promotion import Tier3PromotionConfig, Tier3PromotionService
from polylog6.simulation.tier3_ingestion import Tier3CandidateIngestionPipeline


def _build_sample_workspace() -> PolyformWorkspace:
    workspace = PolyformWorkspace()
    workspace.add_polygon(sides=4, orientation_index=0, rotation_count=0, delta=(0, 0, 0))
    workspace.add_polygon(sides=3, orientation_index=1, rotation_count=0, delta=(1, 0, 0))
    return workspace


def test_tier3_smoke_pipeline(tmp_path: Path) -> None:
    catalog = Tier3Catalog(base_path=tmp_path, candidate_flush_threshold=1)
    pipeline = Tier3CandidateIngestionPipeline(catalog=catalog)

    workspace = _build_sample_workspace()
    summary = CheckpointSummary(
        label="checkpoint-001",
        path=tmp_path / "checkpoint-001.jsonl",
        polygons=workspace.polygon_count(),
        chunk_count=1,
        module_refs=len(workspace.module_references()),
        registry_digest="dummy",
        timestamp=0.0,
    )

    pipeline.ingest_checkpoint(summary, workspace)

    candidates = list(catalog.iter_candidates())
    assert candidates, "Expected ingestion to produce at least one candidate"
    candidate_id = candidates[0].candidate_id

    # Boost stability metrics to guarantee promotion eligibility
    candidate = catalog.get_candidate(candidate_id)
    assert isinstance(candidate, Tier3Candidate)
    candidate.stability_score = 0.95
    candidate.raw_metrics["density"] = 10.0
    catalog.upsert_candidate(candidate)

    telemetry_events: List[Dict[str, object]] = []
    queue_events: List[Tuple[str, str]] = []
    invalidations: List[bool] = []

    def emit(payload: Dict[str, object]) -> None:
        telemetry_events.append(payload)

    def enqueue(candidate_id: str, event_type: str) -> None:
        queue_events.append((candidate_id, event_type))

    def invalidate() -> None:
        invalidations.append(True)

    service = Tier3PromotionService(
        catalog=catalog,
        config=Tier3PromotionConfig(promotion_threshold=0.8, demotion_threshold=0.4),
        telemetry_emit=emit,
        simulation_enqueue=enqueue,
        registry_invalidator=invalidate,
        telemetry_buffer_size=16,
    )

    symbol = service.promote(candidate_id, promotion_type="system", notes="auto")

    assert symbol.symbol in [entry.symbol for entry in catalog.iter_promoted()]
    assert queue_events[-1] == (candidate_id, "promoted")
    assert telemetry_events[-1]["promotion_state"] == "promoted"
    assert invalidations, "Registry invalidator should be called on promotion"
    assert service.recent_events()[-1]["promotion_state"] == "promoted"

    service.demote(candidate_id, justification={"reason": "regression"}, notes="rollback")

    assert queue_events[-1] == (candidate_id, "demoted")
    assert telemetry_events[-1]["promotion_state"] == "demoted"
    assert len(invalidations) == 2, "Registry invalidation should fire on demotion"
    assert service.recent_events(limit=1)[0]["promotion_state"] == "demoted"

    # Ensure candidate reverts to demoted state in catalog
    demoted = catalog.get_candidate(candidate_id)
    assert demoted is not None
    assert demoted.status == "demoted"
