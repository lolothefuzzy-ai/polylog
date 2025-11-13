"""Tier 3 complex polyform catalog scaffold.

This module defines the data structures and persistence utilities that back the
upcoming Tier 3 promotion pipeline. It focuses on:

* Normalised candidate metadata (assembly graphs, stability metrics, status).
* Deterministic Tier 3 symbol derivation shared by automation and tooling.
* JSONL-backed storage for pending candidates and promoted symbols.
* Hooks for probation tracking and promotion/demotion decision logging.

Higher-level promotion workflows and registry integration will build on top of
these primitives in subsequent tasks.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, MutableMapping, Optional

import hashlib
import json

__all__ = [
    "Tier3Candidate",
    "Tier3Symbol",
    "Tier3Catalog",
    "candidate_to_symbol",
    "now_iso",
    "parse_iso8601",
]


# ---------------------------------------------------------------------------
# Timestamp helpers
# ---------------------------------------------------------------------------

def now_iso() -> str:
    """Return the current UTC timestamp in ISO 8601 format."""

    return datetime.now(timezone.utc).isoformat()


def parse_iso8601(value: str) -> datetime:
    """Parse an ISO 8601 timestamp.

    Python's ``datetime.fromisoformat`` does not accept ``Z`` suffixes prior to
    Python 3.11, so we normalise the value before parsing for compatibility.
    """

    value = value.strip()
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)


# ---------------------------------------------------------------------------
# Tier 3 data model
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class Tier3Candidate:
    """Represents a complex polyform awaiting Tier 3 promotion."""

    candidate_id: str
    signature: str
    core_components: List[str]
    assembly_graph: Dict[str, Dict[str, Any]]
    raw_metrics: Dict[str, float]
    stability_score: float
    created_at: str
    last_promoted_at: Optional[str]
    probation_until: Optional[str]
    status: str  # 'pending', 'eligible', 'probation', 'promoted', 'demoted'
    eligible_for_unicode: bool = False
    tags: List[str] = field(default_factory=list)
    notes: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    promotion_log: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialise the candidate for JSON storage."""

        return {
            "candidate_id": self.candidate_id,
            "signature": self.signature,
            "core_components": list(self.core_components),
            "assembly_graph": self.assembly_graph,
            "raw_metrics": self.raw_metrics,
            "stability_score": self.stability_score,
            "created_at": self.created_at,
            "last_promoted_at": self.last_promoted_at,
            "probation_until": self.probation_until,
            "status": self.status,
            "eligible_for_unicode": self.eligible_for_unicode,
            "tags": list(self.tags),
            "notes": self.notes,
            "metadata": self.metadata,
            "promotion_log": list(self.promotion_log),
        }

    @classmethod
    def from_dict(cls, payload: MutableMapping[str, Any]) -> "Tier3Candidate":
        """Create a candidate from a JSON payload."""

        return cls(
            candidate_id=str(payload["candidate_id"]),
            signature=str(payload.get("signature", "")),
            core_components=list(payload.get("core_components", [])),
            assembly_graph=dict(payload.get("assembly_graph", {})),
            raw_metrics=dict(payload.get("raw_metrics", {})),
            stability_score=float(payload.get("stability_score", 0.0)),
            created_at=str(payload.get("created_at", now_iso())),
            last_promoted_at=payload.get("last_promoted_at"),
            probation_until=payload.get("probation_until"),
            status=str(payload.get("status", "pending")),
            eligible_for_unicode=bool(payload.get("eligible_for_unicode", False)),
            tags=list(payload.get("tags", [])),
            notes=payload.get("notes"),
            metadata=dict(payload.get("metadata", {})),
            promotion_log=list(payload.get("promotion_log", [])),
        )

    # ------------------------------------------------------------------
    # Behaviour helpers
    # ------------------------------------------------------------------
    def is_in_probation(self, current_time: Optional[datetime] = None) -> bool:
        if self.status != "probation" or not self.probation_until:
            return False
        current_time = current_time or datetime.now(timezone.utc)
        return current_time >= parse_iso8601(self.probation_until)

    def register_decision(
        self,
        *,
        decision: str,
        justification: Dict[str, Any],
        notes: Optional[str] = None,
        timestamp: Optional[str] = None,
    ) -> None:
        """Record a promotion/demotion decision for auditing."""

        entry = {
            "decision": decision,
            "timestamp": timestamp or now_iso(),
            "justification": justification,
        }
        if notes:
            entry["notes"] = notes
        self.promotion_log.append(entry)

    def last_decision_timestamp(self, decision: str) -> Optional[datetime]:
        """Return the timestamp of the most recent matching decision, if any."""

        for entry in reversed(self.promotion_log):
            if entry.get("decision") != decision:
                continue
            ts_value = entry.get("timestamp")
            if not ts_value:
                continue
            try:
                return parse_iso8601(str(ts_value))
            except Exception:
                continue
        return None

    def recent_decision_count(
        self,
        decision: str,
        *,
        within: timedelta,
        reference_time: Optional[datetime] = None,
    ) -> int:
        """Count matching decisions that occurred within the provided window."""

        reference = reference_time or datetime.now(timezone.utc)
        cutoff = reference - within
        count = 0
        for entry in reversed(self.promotion_log):
            if entry.get("decision") != decision:
                continue
            ts_value = entry.get("timestamp")
            if not ts_value:
                continue
            try:
                ts = parse_iso8601(str(ts_value))
            except Exception:
                continue
            if ts < cutoff:
                break
            count += 1
        return count


@dataclass(slots=True)
class Tier3Symbol:
    """Represents a promoted Tier 3 Unicode symbol."""

    symbol: str
    candidate_id: str
    signature: str
    promoted_at: str
    promotion_type: str  # e.g. 'system', 'user'
    status: str = "probation"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "candidate_id": self.candidate_id,
            "signature": self.signature,
            "promoted_at": self.promoted_at,
            "promotion_type": self.promotion_type,
            "status": self.status,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, payload: MutableMapping[str, Any]) -> "Tier3Symbol":
        return cls(
            symbol=str(payload["symbol"]),
            candidate_id=str(payload.get("candidate_id", "")),
            signature=str(payload.get("signature", "")),
            promoted_at=str(payload.get("promoted_at", now_iso())),
            promotion_type=str(payload.get("promotion_type", "system")),
            status=str(payload.get("status", "probation")),
            metadata=dict(payload.get("metadata", {})),
        )


# ---------------------------------------------------------------------------
# Symbol helper
# ---------------------------------------------------------------------------

def candidate_to_symbol(candidate: Tier3Candidate, prefix: str = "Ω") -> str:
    """Derive a deterministic Tier 3 symbol from the candidate id."""

    digest = hashlib.sha256(candidate.candidate_id.encode("utf-8")).hexdigest()
    return f"{prefix}{digest[:8]}"


# ---------------------------------------------------------------------------
# JSONL-backed catalog
# ---------------------------------------------------------------------------

class Tier3Catalog:
    """Persistent store for Tier 3 candidates and promoted symbols."""

    def __init__(
        self,
        *,
        base_path: Path,
        candidates_file: str = "tier3_candidates.jsonl",
        promoted_file: str = "tier3_promoted.jsonl",
        candidate_flush_threshold: int = 16,
    ) -> None:
        self.base_path = Path(base_path)
        self.candidates_path = self.base_path / candidates_file
        self.promoted_path = self.base_path / promoted_file

        self.base_path.mkdir(parents=True, exist_ok=True)

        self._candidates: Dict[str, Tier3Candidate] = {}
        self._promoted: Dict[str, Tier3Symbol] = {}
        self._candidate_flush_threshold = max(1, candidate_flush_threshold)
        self._dirty_candidate_count = 0

        self._load_candidates()
        self._load_promoted()

    # ------------------------------------------------------------------
    # Public accessors
    # ------------------------------------------------------------------
    def upsert_candidate(self, candidate: Tier3Candidate) -> None:
        self._candidates[candidate.candidate_id] = candidate
        self._dirty_candidate_count += 1
        if self._dirty_candidate_count >= self._candidate_flush_threshold:
            self._write_candidates()

    def get_candidate(self, candidate_id: str) -> Optional[Tier3Candidate]:
        return self._candidates.get(candidate_id)

    def iter_candidates(self, *, statuses: Optional[Iterable[str]] = None) -> Iterator[Tier3Candidate]:
        if statuses is None:
            yield from self._candidates.values()
        else:
            allowed = set(statuses)
            yield from (candidate for candidate in self._candidates.values() if candidate.status in allowed)

    def iter_promoted(self) -> Iterator[Tier3Symbol]:
        yield from self._promoted.values()

    def get_promoted_symbol(self, candidate_id: str) -> Optional[Tier3Symbol]:
        for symbol in self._promoted.values():
            if symbol.candidate_id == candidate_id:
                return symbol
        return None

    def promote_candidate(
        self,
        candidate_id: str,
        *,
        promotion_type: str,
        probation_days: int = 7,
        notes: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Tier3Symbol:
        candidate = self._require_candidate(candidate_id)

        symbol = candidate_to_symbol(candidate)
        now = datetime.now(timezone.utc)
        promoted_at = now.isoformat()
        probation_end = (now + timedelta(days=probation_days)).isoformat()

        candidate.status = "probation"
        candidate.eligible_for_unicode = True
        candidate.last_promoted_at = promoted_at
        candidate.probation_until = probation_end
        candidate.register_decision(
            decision="promote",
            justification={
                "stability_score": candidate.stability_score,
                "raw_metrics": candidate.raw_metrics,
                "promotion_type": promotion_type,
            },
            notes=notes,
            timestamp=promoted_at,
        )

        symbol_entry = Tier3Symbol(
            symbol=symbol,
            candidate_id=candidate.candidate_id,
            signature=candidate.signature,
            promoted_at=promoted_at,
            promotion_type=promotion_type,
            status="probation",
            metadata=metadata or {},
        )
        self._promoted[symbol] = symbol_entry

        self._write_candidates()
        self._write_promoted()
        return symbol_entry

    def demote_candidate(
        self,
        candidate_id: str,
        *,
        notes: Optional[str] = None,
        justification: Optional[Dict[str, Any]] = None,
    ) -> None:
        candidate = self._require_candidate(candidate_id)
        candidate.status = "demoted"
        candidate.eligible_for_unicode = False
        candidate.probation_until = None
        candidate.register_decision(
            decision="demote",
            justification=justification or {},
            notes=notes,
        )

        # Remove any promoted entry tied to this candidate.
        to_remove: List[str] = [symbol for symbol, entry in self._promoted.items() if entry.candidate_id == candidate_id]
        for symbol in to_remove:
            self._promoted.pop(symbol, None)

        self._write_candidates()
        self._write_promoted()

    def mark_candidate_status(
        self,
        candidate_id: str,
        *,
        status: str,
        eligible_for_unicode: Optional[bool] = None,
        probation_until: Optional[str] = None,
    ) -> None:
        candidate = self._require_candidate(candidate_id)
        candidate.status = status
        if eligible_for_unicode is not None:
            candidate.eligible_for_unicode = eligible_for_unicode
        candidate.probation_until = probation_until
        self._write_candidates()

    def flush(self) -> None:
        """Persist in-memory catalog state to disk."""

        self._write_candidates()
        self._write_promoted()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _require_candidate(self, candidate_id: str) -> Tier3Candidate:
        candidate = self._candidates.get(candidate_id)
        if not candidate:
            raise KeyError(f"Unknown Tier 3 candidate: {candidate_id}")
        return candidate

    def _load_candidates(self) -> None:
        if not self.candidates_path.exists():
            return
        with self.candidates_path.open("r", encoding="utf-8") as stream:
            for line in stream:
                line = line.strip()
                if not line:
                    continue
                payload = json.loads(line)
                candidate = Tier3Candidate.from_dict(payload)
                self._candidates[candidate.candidate_id] = candidate

    def _load_promoted(self) -> None:
        if not self.promoted_path.exists():
            return
        with self.promoted_path.open("r", encoding="utf-8") as stream:
            for line in stream:
                line = line.strip()
                if not line:
                    continue
                payload = json.loads(line)
                symbol = Tier3Symbol.from_dict(payload)
                self._promoted[symbol.symbol] = symbol

    def _write_candidates(self) -> None:
        with self.candidates_path.open("w", encoding="utf-8") as stream:
            for candidate in self._candidates.values():
                stream.write(json.dumps(candidate.to_dict()))
                stream.write("\n")
        self._dirty_candidate_count = 0

    def _write_promoted(self) -> None:
        with self.promoted_path.open("w", encoding="utf-8") as stream:
            for symbol in self._promoted.values():
                stream.write(json.dumps(symbol.to_dict()))
                stream.write("\n")
