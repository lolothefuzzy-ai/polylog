"""Locked schema and signature helpers for simulation candidate events."""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Dict, List, Optional, Tuple

SCHEMA_VERSION: str = "1.0"


class CanonicalSignatureFactory:
    """Immutable canonical signature computation (SHA256[:16])."""

    @staticmethod
    def compute(
        sorted_polygon_types: Tuple[int, ...],
        symmetry_group: str,
        scaler_stability: float,
    ) -> str:
        """Compute deterministic 16-char hash for a candidate composition."""
        if not sorted_polygon_types:
            raise ValueError("sorted_polygon_types must not be empty")
        if symmetry_group is None:
            raise ValueError("symmetry_group must not be None")

        polygons_sorted = tuple(sorted(sorted_polygon_types))
        scaler_fmt = f"{scaler_stability:.2f}"
        polygon_str = ",".join(str(p) for p in polygons_sorted)
        composition_string = f"{polygon_str}|{symmetry_group}|{scaler_fmt}"

        digest = hashlib.sha256(composition_string.encode("utf-8"))
        return digest.hexdigest()[:16]


@dataclass
class CandidateEvent:
    """Versioned (v1.0) candidate event payload for tier capture."""

    event_id: str
    session_id: str
    timestamp: float
    canonical_signature: str
    composition: Tuple[int, ...]

    symmetry_group: str
    symmetry_score: float
    shared_edges: int
    multi_edge_count: int
    attachment_scalers: List[float]
    scaler_stability: float
    frequency_in_session: int

    slider_params: Dict
    candidate_hash: str

    tier: Optional[int] = None
    compression_metadata: Optional[Dict] = None

    def to_json(self) -> str:
        """Serialize the event to a JSON string."""
        return json.dumps(asdict(self))

    @staticmethod
    def from_json(json_str: str) -> "CandidateEvent":
        """Deserialize a JSON string to a :class:`CandidateEvent`."""
        data = json.loads(json_str)

        optional_tier = data.pop("tier", None)
        optional_compression = data.pop("compression_metadata", None)

        composition = tuple(data["composition"])
        attachment_scalers = [float(val) for val in data["attachment_scalers"]]

        event = CandidateEvent(
            event_id=data["event_id"],
            session_id=data["session_id"],
            timestamp=float(data["timestamp"]),
            canonical_signature=data["canonical_signature"],
            composition=composition,
            symmetry_group=data["symmetry_group"],
            symmetry_score=float(data["symmetry_score"]),
            shared_edges=int(data["shared_edges"]),
            multi_edge_count=int(data["multi_edge_count"]),
            attachment_scalers=attachment_scalers,
            scaler_stability=float(data["scaler_stability"]),
            frequency_in_session=int(data["frequency_in_session"]),
            slider_params=data.get("slider_params", {}),
            candidate_hash=data["candidate_hash"],
            tier=optional_tier,
            compression_metadata=optional_compression,
        )
        return event

    def is_valid(self) -> bool:
        """Return ``True`` when all capture thresholds are satisfied."""
        return (
            self.symmetry_score >= 0.7
            and self.shared_edges >= 3
            and self.scaler_stability >= 0.75
            and self.frequency_in_session >= 3
        )
