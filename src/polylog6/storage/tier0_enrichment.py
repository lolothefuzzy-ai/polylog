"""Tier 0 metadata enrichment helpers.

This module augments the base ``ConnectivityChain`` exported by the Tier 0
generator with additional metadata required by downstream consumers (frontend
pre-warming, scaler routing, telemetry).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Tuple


@dataclass(slots=True)
class Tier0Metadata:
    """Enrichment payload describing a Tier 0 symbol."""

    tier: int
    range_name: str
    range_code: str
    base_series: str
    attachment_hint: str
    unicode_codepoint: str | None
    symmetry_group: str | None
    frequency_rank: float
    generated_at: str

    def to_dict(self) -> Dict[str, object]:
        """Serialize metadata into a dictionary."""

        return {
            "tier": self.tier,
            "range_name": self.range_name,
            "range_code": self.range_code,
            "base_series": self.base_series,
            "attachment_hint": self.attachment_hint,
            "unicode_codepoint": self.unicode_codepoint,
            "symmetry_group": self.symmetry_group,
            "frequency_rank": self.frequency_rank,
            "generated_at": self.generated_at,
        }


_RANGE_LOOKUP: Dict[str, Tuple[str, str, str]] = {
    "1": ("Single Primitives", "1-9", "none"),
    "2": ("Two-Polygon AB", "10-99", "base_B_connection"),
    "3": ("Two-Polygon AC", "100-199", "base_C_connection"),
    "4": ("Two-Polygon AD", "200-299", "base_D_connection"),
    "5": ("Three-Polygon ABC (tens)", "300-399", "tens_reference_C"),
    "6": ("Three-Polygon ABD (tens)", "400-499", "tens_reference_D"),
    "7": ("Three-Polygon ABC (ones)", "500-599", "ones_reference_C"),
    "8": ("Three-Polygon ABD (ones)", "600-699", "ones_reference_D"),
    "9": ("Four-Polygon ABA", "700-799", "pattern_ABA"),
    "10": ("Four-Polygon ACA", "800-899", "pattern_ACA"),
    "11": ("Four-Polygon ACD", "900-999", "pattern_ACD"),
}


def build_tier0_metadata(symbol: str) -> Tier0Metadata:
    """Create metadata for a Tier 0 symbol based on its subscript."""

    if not symbol or len(symbol) < 2:
        raise ValueError(f"Invalid Tier 0 symbol: {symbol!r}")

    base_series = symbol[0].upper()
    subscript = symbol[1:]

    if not subscript.isdigit():
        raise ValueError(f"Tier 0 subscript must be numeric: {symbol!r}")

    if len(subscript) == 1:
        range_name, range_code, attachment_hint = _RANGE_LOOKUP["1"]
    elif len(subscript) == 2:
        range_name, range_code, attachment_hint = _RANGE_LOOKUP["2"]
    else:
        hundreds = subscript[0]
        key = {
            "1": "3",
            "2": "4",
            "3": "5",
            "4": "6",
            "5": "7",
            "6": "8",
            "7": "9",
            "8": "10",
            "9": "11",
        }.get(hundreds)
        if key is None:
            raise ValueError(f"Unsupported hundreds digit in symbol: {symbol!r}")
        range_name, range_code, attachment_hint = _RANGE_LOOKUP[key]

    return Tier0Metadata(
        tier=0,
        range_name=range_name,
        range_code=range_code,
        base_series=base_series,
        attachment_hint=attachment_hint,
        unicode_codepoint=None,
        symmetry_group=None,
        frequency_rank=0.5,
        generated_at=datetime.utcnow().isoformat(timespec="seconds") + "Z",
    )
