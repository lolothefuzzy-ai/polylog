"""Tests for Tier 3 catalog and promotion service."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Dict, List

import pytest

from polylog6.storage.tier3_catalog import Tier3Candidate, Tier3Catalog, now_iso
from polylog6.storage.tier3_promotion import Tier3PromotionConfig, Tier3PromotionService


def _make_candidate(
    *,
    candidate_id: str = "cand-1",
    signature: str = "sig-1",
    status: str = "pending",
    probation_until: str | None = None,
) -> Tier3Candidate:
    return Tier3Candidate(
        candidate_id=candidate_id,
        signature=signature,
        core_components=["R1"],
        assembly_graph={"edge-1": {"from": "A", "to": "B"}},
        raw_metrics={"energy": 0.1},
        stability_score=0.95,
        created_at=now_iso(),
        last_promoted_at=None,
        probation_until=probation_until,
        status=status,
    )


def test_catalog_promote_and_lookup(tmp_path):
    catalog = Tier3Catalog(base_path=tmp_path)

    candidate = _make_candidate()
    catalog.upsert_candidate(candidate)

    symbol_entry = catalog.promote_candidate(candidate.candidate_id, promotion_type="system")

    lookup = catalog.get_promoted_symbol(candidate.candidate_id)
    assert lookup is not None
    assert lookup.symbol == symbol_entry.symbol

    # Reload from disk to ensure persistence
    reopened = Tier3Catalog(base_path=tmp_path)
    restored = reopened.get_promoted_symbol(candidate.candidate_id)
    assert restored is not None
    assert restored.symbol == symbol_entry.symbol


def test_catalog_demote_clears_symbol(tmp_path):
    catalog = Tier3Catalog(base_path=tmp_path)
    candidate = _make_candidate()
    catalog.upsert_candidate(candidate)
    catalog.promote_candidate(candidate.candidate_id, promotion_type="system")

    catalog.demote_candidate(candidate.candidate_id, justification={"reason": "manual"})

    assert catalog.get_promoted_symbol(candidate.candidate_id) is None
    updated = catalog.get_candidate(candidate.candidate_id)
    assert updated is not None
    assert updated.status == "demoted"
    assert updated.eligible_for_unicode is False


def test_promotion_service_emits_telemetry_and_enqueues(tmp_path):
    catalog = Tier3Catalog(base_path=tmp_path)
    candidate = _make_candidate()
    catalog.upsert_candidate(candidate)

    telemetry: List[Dict[str, object]] = []
    queue: List[tuple[str, str]] = []

    def emit(payload: Dict[str, object]) -> None:
        telemetry.append(payload)

    def enqueue(candidate_id: str, event_type: str) -> None:
        queue.append((candidate_id, event_type))

    service = Tier3PromotionService(
        catalog=catalog,
        telemetry_emit=emit,
        simulation_enqueue=enqueue,
    )

    service.promote(candidate.candidate_id, promotion_type="user", notes="looks good")

    assert queue == [(candidate.candidate_id, "promoted")]
    assert telemetry
    promote_event = telemetry[-1]
    assert promote_event["promotion_state"] == "promoted"
    assert promote_event["symbol"]

    service.demote(
        candidate.candidate_id,
        justification={"reason": "unstable"},
        notes="rollback",
    )

    assert queue[-1] == (candidate.candidate_id, "demoted")
    demote_event = telemetry[-1]
    assert demote_event["promotion_state"] == "demoted"
    assert "symbol" not in demote_event  # symbol mapping removed post-demotion


def test_probation_expiry_triggers_demote(tmp_path):
    catalog = Tier3Catalog(base_path=tmp_path)
    past_time = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    candidate = _make_candidate(status="probation", probation_until=past_time)
    catalog.upsert_candidate(candidate)

    telemetry: List[Dict[str, object]] = []
    queue: List[tuple[str, str]] = []

    def emit(payload: Dict[str, object]) -> None:
        telemetry.append(payload)

    def enqueue(candidate_id: str, event_type: str) -> None:
        queue.append((candidate_id, event_type))

    service = Tier3PromotionService(
        catalog=catalog,
        telemetry_emit=emit,
        simulation_enqueue=enqueue,
    )

    demoted = list(service.process_probation_expiry(notes="auto-expire"))

    assert demoted == [candidate.candidate_id]
    assert queue == [(candidate.candidate_id, "probation_expired")]
    assert telemetry[-1]["promotion_state"] == "probation_expired"
    updated = catalog.get_candidate(candidate.candidate_id)
    assert updated is not None
    assert updated.status == "demoted"


def test_should_promote_respects_cooldown(tmp_path):
    catalog = Tier3Catalog(base_path=tmp_path)
    candidate = _make_candidate()
    candidate.stability_score = 0.95
    recent_promotion = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    candidate.register_decision(
        decision="promote",
        justification={"stability_score": 0.95},
        timestamp=recent_promotion,
    )
    catalog.upsert_candidate(candidate)

    config = Tier3PromotionConfig(
        promotion_threshold=0.8,
        promotion_cooldown_hours=2,
    )
    service = Tier3PromotionService(catalog=catalog, config=config)

    assert service.should_promote(candidate) is False
    with pytest.raises(ValueError, match="cooldown"):
        service.promote(candidate.candidate_id, promotion_type="system")


def test_should_promote_respects_window_limit(tmp_path):
    catalog = Tier3Catalog(base_path=tmp_path)
    candidate = _make_candidate()
    candidate.stability_score = 0.95
    now = datetime.now(timezone.utc)
    for days_ago in (1, 2):
        candidate.register_decision(
            decision="promote",
            justification={"sequence": days_ago},
            timestamp=(now - timedelta(days=days_ago)).isoformat(),
        )
    catalog.upsert_candidate(candidate)

    config = Tier3PromotionConfig(
        promotion_threshold=0.8,
        promotion_window_days=7,
        promotion_window_limit=2,
    )
    service = Tier3PromotionService(catalog=catalog, config=config)

    assert service.should_promote(candidate) is False
    with pytest.raises(ValueError, match="exceeds limit"):
        service.promote(candidate.candidate_id, promotion_type="system")


def test_should_demote_considers_recent_history(tmp_path):
    catalog = Tier3Catalog(base_path=tmp_path)
    candidate = _make_candidate()
    candidate.stability_score = 0.9
    now = datetime.now(timezone.utc)
    for hours_ago in (4, 20):
        candidate.register_decision(
            decision="demote",
            justification={"sequence": hours_ago},
            timestamp=(now - timedelta(hours=hours_ago)).isoformat(),
        )
    catalog.upsert_candidate(candidate)

    config = Tier3PromotionConfig(
        demotion_threshold=0.4,
        demotion_window_days=1,
        demotion_window_limit=2,
    )
    service = Tier3PromotionService(catalog=catalog, config=config)

    assert service.should_demote(candidate) is True
