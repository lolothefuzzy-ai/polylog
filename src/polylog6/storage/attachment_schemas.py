"""Attachment schema catalog for context-aware compression.

This module defines single-character schema tables for attachment properties and
polygon pair context matrices used by context-aware attachment resolution. It is
seeded with canonical categories but can be extended as catalogs are populated.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Mapping

from .symbol_registry import SymbolRegistry

# ---------------------------------------------------------------------------
# Primary schema categories (single-character glyphs)
# ---------------------------------------------------------------------------

FOLD_ANGLE_SCHEMAS: Dict[str, Dict[str, object]] = {
    "∠₀": {"angle": 0.0, "name": "planar_aligned"},
    "∠₁": {"angle": 45.0, "name": "gentle_fold"},
    "∠₂": {"angle": 60.0, "name": "dihedral_triangle"},
    "∠₃": {"angle": 70.5, "name": "tetrahedral"},
    "∠₄": {"angle": 90.0, "name": "orthogonal"},
    "∠₅": {"angle": 108.0, "name": "pentagonal"},
    "∠₆": {"angle": 120.0, "name": "hexagonal"},
    "∠₇": {"angle": 135.0, "name": "steep_fold"},
    "∠₈": {"angle": 150.0, "name": "steep_approach"},
    "∠₉": {"angle": 180.0, "name": "fully_open"},
    "∠ₐ": {"angle": "variable", "name": "flexible"},
    "∠ᵦ": {"angle": "adaptive", "name": "smart"},
}

STABILITY_SCHEMAS: Dict[str, Dict[str, object]] = {
    "◆₁": {"threshold": 0.90, "name": "ultra_stable"},
    "◆₂": {"threshold": 0.85, "name": "high_stable"},
    "◆₃": {"threshold": 0.75, "name": "stable"},
    "◆₄": {"threshold": 0.60, "name": "moderate_stable"},
    "◆₅": {"threshold": 0.45, "name": "marginal_stable"},
    "◆₆": {"threshold": 0.30, "name": "unstable"},
    "◆₇": {"threshold": 0.15, "name": "highly_unstable"},
    "◆₈": {"threshold": 0.00, "name": "experimental"},
}

CLOSURE_SCHEMAS: Dict[str, Dict[str, object]] = {
    "◯₁": {"ratio": 0.00, "name": "fully_open"},
    "◯₂": {"ratio": 0.25, "name": "mostly_open"},
    "◯₃": {"ratio": 0.50, "name": "half_closed"},
    "◯₄": {"ratio": 0.75, "name": "mostly_closed"},
    "◯₅": {"ratio": 0.95, "name": "nearly_closed"},
    "◯₆": {"ratio": 1.00, "name": "fully_closed"},
}

GENERATION_SCHEMAS: Dict[str, Dict[str, object]] = {
    "◈₁": {"method": "explore", "name": "random_explore"},
    "◈₂": {"method": "stable_iter", "name": "stable_iteration"},
    "◈₃": {"method": "stable_mult", "name": "stable_multiplication"},
    "◈₄": {"method": "linear", "name": "linear_growth"},
    "◈₅": {"method": "cubic", "name": "cubic_growth"},
    "◈₆": {"method": "explosive", "name": "explosive_growth"},
    "◈₇": {"method": "radial", "name": "radial_symmetry"},
    "◈₈": {"method": "cascading", "name": "cascading_build"},
    "◈₉": {"method": "manual", "name": "user_placed"},
    "◈ₐ": {"method": "hybrid", "name": "mixed_strategy"},
}

DIMENSION_SCHEMAS: Dict[str, Dict[str, object]] = {
    "⟿₂": {"dim": 2, "name": "2d_planar"},
    "⟿₃": {"dim": 3, "name": "3d_spatial"},
    "⟿ₘ": {"dim": "mixed", "name": "mixed_dimension"},
}

SCHEMA_PARTITIONS: Mapping[str, Dict[str, Dict[str, object]]] = {
    "fold_angle": FOLD_ANGLE_SCHEMAS,
    "stability": STABILITY_SCHEMAS,
    "closure": CLOSURE_SCHEMAS,
    "generation": GENERATION_SCHEMAS,
    "dimension": DIMENSION_SCHEMAS,
}

# ---------------------------------------------------------------------------
# Context-aware polygon pair matrix
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class ContextSchema:
    """Mapping between polygon-pair context and schema selection."""

    char: str
    primary: str
    schemas: List[str]


POLYGON_PAIR_ATTACHMENT_MATRIX: Dict[str, Dict[str, ContextSchema]] = {
    "A↔A": {
        "dim_2d_planar": ContextSchema(char="⬚₁", primary="∠₉◆₃◯₁◈₁⟿₂", schemas=["∠₉◆₃◯₁◈₁⟿₂", "∠₉◆₄◯₂◈₁⟿₂"]),
        "dim_3d_tetrahedral": ContextSchema(char="⬚₂", primary="∠₃◆₂◯₁◈₈⟿₃", schemas=["∠₃◆₂◯₁◈₈⟿₃", "∠₂◆₃◯₂◈₈⟿₃"]),
        "dim_3d_octahedral": ContextSchema(char="⬚₃", primary="∠₄◆₂◯₁◈₄⟿₃", schemas=["∠₄◆₂◯₁◈₄⟿₃"]),
        "user_defined": ContextSchema(char="⬚ᵤ", primary="∠ₐ◆₈◯₃◈ₐ⟿ₘ", schemas=["∠ₐ◆₈◯₃◈ₐ⟿ₘ"]),
    },
    "A↔B": {
        "dim_2d_planar": ContextSchema(char="⬛₁", primary="∠₉◆₃◯₁◈₁⟿₂", schemas=["∠₉◆₃◯₁◈₁⟿₂", "∠₉◆₂◯₂◈₁⟿₂"]),
        "dim_3d_mixed": ContextSchema(char="⬛₂", primary="∠₅◆₂◯₂◈₈⟿₃", schemas=["∠₅◆₂◯₂◈₈⟿₃", "∠₄◆₃◯₂◈₈⟿₃", "∠₆◆₂◯₂◈₆⟿₃"]),
        "closure_ratio_high": ContextSchema(char="⬛ₕ", primary="∠₁◆₂◯₅◈₄⟿₃", schemas=["∠₁◆₂◯₅◈₄⟿₃"]),
        "closure_ratio_low": ContextSchema(char="⬛ₗ", primary="∠₉◆₄◯₁◈₁⟿₂", schemas=["∠₉◆₄◯₁◈₁⟿₂"]),
        "user_defined": ContextSchema(char="⬛ᵤ", primary="∠ₐ◆₈◯ₘ◈ₐ⟿ₘ", schemas=["∠ₐ◆₈◯ₘ◈ₐ⟿ₘ"]),
    },
    "B↔B": {
        "dim_2d_planar": ContextSchema(char="⬜₁", primary="∠₉◆₃◯₁◈₁⟿₂", schemas=["∠₉◆₃◯₁◈₁⟿₂"]),
        "dim_3d_cubic": ContextSchema(char="⬜₂", primary="∠₄◆₂◯₁◈₄⟿₃", schemas=["∠₄◆₂◯₁◈₄⟿₃", "∠₄◆₃◯₂◈₄⟿₃"]),
        "workspace_symmetry_d4": ContextSchema(char="⬜₄", primary="∠₄◆₂◯₁◈₄⟿₃", schemas=["∠₄◆₂◯₁◈₄⟿₃"]),
        "user_defined": ContextSchema(char="⬜ᵤ", primary="∠ₐ◆₈◯ₘ◈ₐ⟿ₘ", schemas=["∠ₐ◆₈◯ₘ◈ₐ⟿ₘ"]),
    },
}

# Placeholder for expanding remaining primitive pairs; populated during catalog
# generation. This ensures the resolver can iterate known pairs even before data
# is complete.
_tier0_registry = SymbolRegistry()

for sides_a, symbol_a in _tier0_registry.iter_primitives():
    for sides_b, symbol_b in _tier0_registry.iter_primitives():
        if symbol_a > symbol_b:
            continue
        pair_key = f"{symbol_a}↔{symbol_b}"
        POLYGON_PAIR_ATTACHMENT_MATRIX.setdefault(pair_key, {}).setdefault(
            "user_defined",
            ContextSchema(
                char="⬳",
                primary="∠ₐ◆₈◯₃◈ₐ⟿ₘ",
                schemas=["∠ₐ◆₈◯₃◈ₐ⟿ₘ"],
            ),
        )


def is_placeholder_context(entry: ContextSchema) -> bool:
    """Return True if the context entry is using fallback placeholder data."""

    return entry.char == "⬳"


__all__ = [
    "ContextSchema",
    "FOLD_ANGLE_SCHEMAS",
    "STABILITY_SCHEMAS",
    "CLOSURE_SCHEMAS",
    "GENERATION_SCHEMAS",
    "DIMENSION_SCHEMAS",
    "SCHEMA_PARTITIONS",
    "POLYGON_PAIR_ATTACHMENT_MATRIX",
    "is_placeholder_context",
]
