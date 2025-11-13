"""Tier 3 promotion pipeline and CLI entry points."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Callable, Deque, Dict, Iterable, List, Optional, Tuple
import threading

import argparse
import json
import sys

from .tier3_catalog import Tier3Catalog, Tier3Candidate, Tier3Symbol, now_iso

__all__ = ["Tier3PromotionConfig", "Tier3PromotionService", "main"]


@dataclass(slots=True)
class Tier3PromotionConfig:
    """Centralised thresholds governing Tier 3 promotion decisions."""

    promotion_threshold: float = 0.8
    demotion_threshold: float = 0.5
    default_probation_days: int = 7
    promotion_cooldown_hours: int = 24
    promotion_window_days: int = 14
    promotion_window_limit: int = 3
    demotion_window_days: int = 7
    demotion_window_limit: int = 2


@dataclass
class PromotionDecision:
    candidate_id: str
    decision: str  # 'promote' or 'demote'
    justification: Dict[str, Any]
    notes: Optional[str] = None
    promotion_type: str = "system"
    event_type: Optional[str] = None


class Tier3PromotionService:
    """Manage Tier 3 candidate promotion/demotion along with telemetry hooks."""

    def __init__(
        self,
        *,
        catalog: Tier3Catalog,
        config: Optional[Tier3PromotionConfig] = None,
        telemetry_emit: Optional[Callable[[Dict[str, Any]], None]] = None,
        simulation_enqueue: Optional[Callable[[str, str], None]] = None,
        registry_invalidator: Optional[Callable[[], None]] = None,
        telemetry_buffer_size: int = 128,
    ) -> None:
        self.catalog = catalog
        self.config = config or Tier3PromotionConfig()
        self._telemetry_emit = telemetry_emit
        self._simulation_enqueue = simulation_enqueue
        self._registry_invalidator = registry_invalidator
        self._lock = threading.RLock()
        self._telemetry_buffer: Deque[Dict[str, Any]] = deque(maxlen=max(1, telemetry_buffer_size))

    # ------------------------------------------------------------------
    # Promotion / demotion
    # ------------------------------------------------------------------
    def promote(
        self,
        candidate_id: str,
        *,
        promotion_type: str,
        notes: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        probation_days: Optional[int] = None,
    ) -> Tier3Symbol:
        with self._lock:
            candidate = self._require_candidate(candidate_id)
            now = datetime.now(timezone.utc)
            eligible, reason = self._evaluate_promotion_constraints(candidate, reference_time=now)
            if not eligible:
                raise ValueError(
                    f"Candidate {candidate_id} does not meet promotion rules: {reason}"
                )

            symbol_entry = self.catalog.promote_candidate(
                candidate_id,
                promotion_type=promotion_type,
                probation_days=probation_days or self.config.default_probation_days,
                notes=notes,
                metadata=metadata,
            )
            payload = self._build_payload(
                candidate,
                event_type="promoted",
                notes=notes,
                extra={
                    "promotion_type": promotion_type,
                    "metadata": metadata or {},
                },
            )
            self._emit_event(payload)
            self._enqueue_candidate(candidate_id, "promoted")
            self._invalidate_registry()
            return symbol_entry

    def demote(
        self,
        candidate_id: str,
        *,
        justification: Optional[Dict[str, Any]] = None,
        notes: Optional[str] = None,
        event_type: str = "demoted",
    ) -> None:
        with self._lock:
            candidate = self._require_candidate(candidate_id)
            justification_payload = justification or {}
            self.catalog.demote_candidate(candidate_id, notes=notes, justification=justification_payload)
            payload = self._build_payload(
                candidate,
                event_type=event_type,
                notes=notes,
                extra={"justification": justification_payload},
            )
            self._emit_event(payload)
            self._enqueue_candidate(candidate_id, event_type)
            self._invalidate_registry()

    def apply_decision(self, decision: PromotionDecision) -> Optional[Tier3Symbol]:
        if decision.decision == "promote":
            return self.promote(
                decision.candidate_id,
                promotion_type=decision.promotion_type,
                notes=decision.notes,
                metadata=decision.justification,
            )
        if decision.decision == "demote":
            self.demote(
                decision.candidate_id,
                justification=decision.justification,
                notes=decision.notes,
                event_type=decision.event_type or "demoted",
            )
            return None
        raise ValueError(f"Unknown decision type: {decision.decision}")

    # ------------------------------------------------------------------
    # Telemetry
    # ------------------------------------------------------------------
    def _build_payload(
        self,
        candidate: Tier3Candidate,
        *,
        event_type: str,
        notes: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        symbol_entry = self.catalog.get_promoted_symbol(candidate.candidate_id)
        payload: Dict[str, Any] = {
            "candidate_id": candidate.candidate_id,
            "signature": candidate.signature,
            "promotion_state": event_type,
            "timestamp": now_iso(),
            "stability_score": candidate.stability_score,
            "raw_metrics": candidate.raw_metrics,
            "status": candidate.status,
            "notes": notes,
        }
        if symbol_entry is not None:
            payload["symbol"] = symbol_entry.symbol
            payload["symbol_metadata"] = symbol_entry.to_dict()
        if extra:
            payload.update(extra)
        return payload

    def _emit_event(self, payload: Dict[str, Any]) -> None:
        self._telemetry_buffer.append(dict(payload))
        if self._telemetry_emit is None:
            return
        try:
            self._telemetry_emit(payload)
        except Exception:  # pragma: no cover - telemetry sinks are best-effort
            return

    def _enqueue_candidate(self, candidate_id: str, event_type: str) -> None:
        if self._simulation_enqueue is None:
            return
        try:
            self._simulation_enqueue(candidate_id, event_type)
        except TypeError:
            self._simulation_enqueue(candidate_id, event_type)  # pragma: no cover - consistent signature enforced

    def _invalidate_registry(self) -> None:
        if self._registry_invalidator is None:
            return
        try:
            self._registry_invalidator()
        except Exception:  # pragma: no cover - cache invalidation is best-effort
            return

    def process_probation_expiry(
        self,
        *,
        current_time: Optional[datetime] = None,
        notes: Optional[str] = None,
    ) -> Iterable[str]:
        """Demote any candidates whose probation window has elapsed."""

        current_time = current_time or datetime.now(timezone.utc)
        demoted: list[str] = []
        for candidate in self.catalog.iter_candidates(statuses=("probation",)):
            if candidate.is_in_probation(current_time) and self.should_demote(candidate):
                self.demote(
                    candidate.candidate_id,
                    justification={"reason": "probation_expired"},
                    notes=notes,
                    event_type="probation_expired",
                )
                demoted.append(candidate.candidate_id)
        return demoted

    def _require_candidate(self, candidate_id: str) -> Tier3Candidate:
        candidate = self.catalog.get_candidate(candidate_id)
        if candidate is None:
            raise KeyError(f"Unknown Tier 3 candidate: {candidate_id}")
        return candidate

    # ------------------------------------------------------------------
    # Threshold helpers
    # ------------------------------------------------------------------
    def should_promote(self, candidate: Tier3Candidate) -> bool:
        eligible, _ = self._evaluate_promotion_constraints(candidate)
        return eligible

    def should_demote(self, candidate: Tier3Candidate) -> bool:
        if candidate.status == "probation" and candidate.is_in_probation():
            return True

        if candidate.stability_score <= self.config.demotion_threshold:
            return True

        if self.config.demotion_window_limit > 0 and self.config.demotion_window_days > 0:
            window = timedelta(days=self.config.demotion_window_days)
            demotion_count = candidate.recent_decision_count(
                "demote",
                within=window,
            )
            if demotion_count >= self.config.demotion_window_limit:
                return True

        return False

    # ------------------------------------------------------------------
    # Promotion gating helpers
    # ------------------------------------------------------------------
    def _evaluate_promotion_constraints(
        self,
        candidate: Tier3Candidate,
        *,
        reference_time: Optional[datetime] = None,
    ) -> Tuple[bool, Optional[str]]:
        now = reference_time or datetime.now(timezone.utc)
        score = candidate.stability_score
        if score < self.config.promotion_threshold:
            return (
                False,
                f"stability score {score:.3f} below threshold {self.config.promotion_threshold:.3f}",
            )

        cooldown_hours = self.config.promotion_cooldown_hours
        if cooldown_hours > 0:
            last_promoted = candidate.last_decision_timestamp("promote")
            if last_promoted is not None:
                elapsed = now - last_promoted
                if elapsed < timedelta(hours=cooldown_hours):
                    remaining = timedelta(hours=cooldown_hours) - elapsed
                    remaining_hours = max(remaining.total_seconds() / 3600, 0.0)
                    return (
                        False,
                        f"promotion cooldown active for another {remaining_hours:.1f}h",
                    )

        window_days = self.config.promotion_window_days
        window_limit = self.config.promotion_window_limit
        if window_limit > 0 and window_days > 0:
            window = timedelta(days=window_days)
            promotions_in_window = candidate.recent_decision_count(
                "promote",
                within=window,
                reference_time=now,
            )
            if promotions_in_window >= window_limit:
                return (
                    False,
                    f"{promotions_in_window} promotions in last {window_days} days exceeds limit {window_limit}",
                )

        demotion_window_limit = self.config.demotion_window_limit
        demotion_window_days = self.config.demotion_window_days
        if demotion_window_limit > 0 and demotion_window_days > 0:
            demotion_window = timedelta(days=demotion_window_days)
            demotions_in_window = candidate.recent_decision_count(
                "demote",
                within=demotion_window,
                reference_time=now,
            )
            if demotions_in_window >= demotion_window_limit:
                return (
                    False,
                    f"{demotions_in_window} demotions in last {demotion_window_days} days requires stability review",
                )

        return True, None

    # ------------------------------------------------------------------
    # Introspection helpers
    # ------------------------------------------------------------------
    def recent_events(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Return the most recent telemetry events (most recent last)."""

        events = list(self._telemetry_buffer)
        if limit is not None:
            return events[-limit:]
        return events


# ---------------------------------------------------------------------------
# CLI support
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Tier 3 promotion tooling")
    parser.add_argument("catalog", type=Path, help="Path to Tier 3 catalog directory")

    subparsers = parser.add_subparsers(dest="command", required=True)

    promote_parser = subparsers.add_parser("promote", help="Promote a candidate to Tier 3")
    promote_parser.add_argument("candidate_id", help="Candidate identifier to promote")
    promote_parser.add_argument("--promotion-type", default="user", help="Promotion origin (user/system)")
    promote_parser.add_argument("--notes", help="Optional notes describing the promotion")
    promote_parser.add_argument("--probation-days", type=int, default=7, help="Probation length in days")
    promote_parser.add_argument("--metadata", help="JSON metadata payload")

    demote_parser = subparsers.add_parser("demote", help="Demote a candidate")
    demote_parser.add_argument("candidate_id", help="Candidate identifier to demote")
    demote_parser.add_argument("--justification", help="JSON justification payload")
    demote_parser.add_argument("--notes", help="Optional notes describing the demotion")

    show_parser = subparsers.add_parser("show", help="Display catalog state")
    show_parser.add_argument("--promoted", action="store_true", help="Show promoted entries instead of candidates")

    return parser


def load_json_argument(value: Optional[str]) -> Optional[Dict[str, Any]]:
    if not value:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:  # pragma: no cover - CLI convenience
        raise SystemExit(f"Invalid JSON payload: {exc}") from exc


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    catalog = Tier3Catalog(base_path=args.catalog)
    service = Tier3PromotionService(catalog=catalog)

    if args.command == "promote":
        metadata = load_json_argument(args.metadata)
        symbol = service.promote(
            args.candidate_id,
            promotion_type=args.promotion_type,
            notes=args.notes,
            metadata=metadata,
            probation_days=args.probation_days,
        )
        print(json.dumps(symbol.to_dict(), indent=2))
        return 0

    if args.command == "demote":
        justification = load_json_argument(args.justification)
        service.demote(args.candidate_id, justification=justification, notes=args.notes)
        print(json.dumps({"status": "demoted", "candidate_id": args.candidate_id}, indent=2))
        return 0

    if args.command == "show":
        if args.promoted:
            entries = [symbol.to_dict() for symbol in catalog.iter_promoted()]
        else:
            entries = [candidate.to_dict() for candidate in catalog.iter_candidates()]
        print(json.dumps(entries, indent=2))
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    sys.exit(main())
