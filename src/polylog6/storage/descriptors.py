"""Core descriptor data structures for the Unicode-based storage layer.

These classes mirror the specification in the Structure & Science documents and
provide helpers for compact serialization (e.g., fold-angle codes, symmetry
signatures) that the encoder/decoder leverage when producing Unicode streams.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


def to_superscript(value: int) -> str:
    """Convert an integer to Unicode superscript representation."""
    superscripts = "⁰¹²³⁴⁵⁶⁷⁸⁹"
    return "".join(superscripts[int(digit)] for digit in str(value))


def to_subscript(value: int) -> str:
    """Convert an integer to Unicode subscript representation."""
    subscripts = "₀₁₂₃₄₅₆₇₈₉"
    return "".join(subscripts[int(digit)] for digit in str(value))


@dataclass(slots=True)
class SymmetryDescriptor:
    """Compact descriptor for symmetry metadata."""

    point_group: str
    order: Optional[int] = None
    rotation_axes: List[Tuple[Sequence[float], int]] = field(default_factory=list)
    reflection_planes: List[Sequence[float]] = field(default_factory=list)
    is_chiral: bool = False
    symmetry_class: Optional[str] = None

    def to_code(self) -> str:
        """Return a compact string representation."""
        if self.order:
            return f"{self.point_group}:{self.order}"
        return self.point_group


@dataclass(slots=True)
class DihedralAngleSet:
    """Stores the fold angle configuration for a polyform."""

    is_rigid: bool = True
    unique_angles: List[float] = field(default_factory=list)
    angle_multiplicities: List[int] = field(default_factory=list)
    angle_ranges: List[Tuple[float, float]] = field(default_factory=list)

    def to_code(self) -> str:
        """Serialize the angle set into a compact token."""
        if self.is_rigid:
            if not self.unique_angles:
                return "θ=0"
            if len(self.unique_angles) == 1:
                return f"θ={self.unique_angles[0]:.1f}"
            angles = ",".join(f"{angle:.1f}" for angle in self.unique_angles)
            mults = ",".join(str(multiplicity) for multiplicity in self.angle_multiplicities)
            return f"θ=[{angles}]×[{mults}]"
        if len(self.angle_ranges) == 1:
            minimum, maximum = self.angle_ranges[0]
            midpoint = (minimum + maximum) / 2
            tolerance = (maximum - minimum) / 2
            return f"θ={midpoint:.1f}±{tolerance:.1f}"
        ranges = ",".join(
            f"({(minimum + maximum) / 2:.1f}±{(maximum - minimum) / 2:.1f})"
            for minimum, maximum in self.angle_ranges
        )
        mults = ",".join(str(multiplicity) for multiplicity in self.angle_multiplicities)
        return f"θ=[{ranges}]×[{mults}]"


def count_polygons(composition: Iterable[str]) -> int:
    """Count total polygons represented by a composition token."""
    total = 0
    for token in composition:
        if token.isnumeric():
            total += int(token)
        else:
            total += 1
    return total


@dataclass(slots=True)
class PolyformDescriptor:
    """Ultra-compact descriptor tying symbols to structural metadata."""

    symbol: str
    composition: str
    angles: DihedralAngleSet
    symmetry: SymmetryDescriptor
    closure_count: int
    metadata: Dict[str, str] = field(default_factory=dict)

    @property
    def polygon_count(self) -> int:
        """Approximate polygon count inferred from the composition string."""
        count = 0
        current_count = ""
        for character in self.composition:
            if character.isnumeric():
                current_count += character
                continue
            if current_count:
                count += int(current_count)
                current_count = ""
            count += 1
        if current_count:
            count += int(current_count)
        return count

    def to_encoding(self) -> str:
        """Produce the canonical compact encoding for the descriptor."""
        if self.metadata.get("rigid_symbol") == "known":
            return self.symbol
        angle_code = self.angles.to_code()
        symmetry_code = self.symmetry.to_code()
        return f"{self.symbol}⟨n={self.closure_count}, {angle_code}, σ={symmetry_code}⟩"

    def to_record(self) -> Dict[str, object]:
        """Return a JSON-serializable record for persistence."""
        return {
            "symbol": self.symbol,
            "composition": self.composition,
            "closure_count": self.closure_count,
            "angles": {
                "is_rigid": self.angles.is_rigid,
                "unique_angles": self.angles.unique_angles,
                "multiplicities": self.angles.angle_multiplicities,
                "angle_ranges": self.angles.angle_ranges,
            },
            "symmetry": {
                "point_group": self.symmetry.point_group,
                "order": self.symmetry.order,
                "is_chiral": self.symmetry.is_chiral,
                "symmetry_class": self.symmetry.symmetry_class,
            },
            "metadata": self.metadata,
        }
