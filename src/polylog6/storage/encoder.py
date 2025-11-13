"""Unicode-based encoder/decoder for hierarchical polyform storage."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Tuple, Union

from .compression_tree import CompressionTree
from .symbol_registry import SymbolRegistry
import multiprocessing

# ---------------------------------------------------------------------------
# VLQ helpers (private-use Unicode block to keep payload printable)
# ---------------------------------------------------------------------------
_VLQ_BASE = 0xE000
_VLQ_CONTINUATION = 0x0080
_VLQ_VALUE_MASK = 0x007F


def _encode_vlq(value: int) -> str:
    if value < 0:
        raise ValueError("VLQ expects non-negative integers")
    chunks: List[int] = []
    while True:
        chunk = value & _VLQ_VALUE_MASK
        value >>= 7
        if value:
            chunk |= _VLQ_CONTINUATION
        chunks.append(chunk)
        if not value:
            break
    return "".join(chr(_VLQ_BASE + chunk) for chunk in chunks)


def _decode_vlq(data: Sequence[str], start: int = 0) -> tuple[int, int]:
    value = 0
    shift = 0
    index = start
    while index < len(data):
        code_point = ord(data[index]) - _VLQ_BASE
        chunk = code_point & _VLQ_VALUE_MASK
        value |= chunk << shift
        if not (code_point & _VLQ_CONTINUATION):
            return value, index + 1
        shift += 7
        index += 1
    raise ValueError("Invalid VLQ sequence")


def _encode_signed_vlq(value: int) -> str:
    zigzag = (value << 1) ^ (value >> 63)
    return _encode_vlq(zigzag)


def _decode_signed_vlq(data: Sequence[str], start: int = 0) -> tuple[int, int]:
    zigzag, index = _decode_vlq(data, start)
    value = (zigzag >> 1) ^ -(zigzag & 1)
    return value, index


# ---------------------------------------------------------------------------
# Orientation helpers
# ---------------------------------------------------------------------------
_CIRCLED_ZERO = "⓿"
_CIRCLED_DIGITS = [
    "①",
    "②",
    "③",
    "④",
    "⑤",
    "⑥",
    "⑦",
    "⑧",
    "⑨",
    "⑩",
    "⑪",
    "⑫",
    "⑬",
    "⑭",
    "⑮",
    "⑯",
    "⑰",
    "⑱",
    "⑲",
    "⑳",
]


def _encode_orientation(index: int) -> str:
    if index < 0:
        raise ValueError("Orientation index must be non-negative")
    if index == 0:
        return _CIRCLED_ZERO
    if 0 < index <= len(_CIRCLED_DIGITS):
        return _CIRCLED_DIGITS[index - 1]
    return "∘" + _encode_vlq(index)


def _decode_orientation(data: Sequence[str], start: int = 0) -> tuple[int, int]:
    if data[start] == _CIRCLED_ZERO:
        return 0, start + 1
    if data[start] in _CIRCLED_DIGITS:
        return _CIRCLED_DIGITS.index(data[start]) + 1, start + 1
    if data[start] != "∘":
        raise ValueError("Invalid orientation token")
    value, index = _decode_vlq(data, start + 1)
    return value, index


# ---------------------------------------------------------------------------
# Polygon entry representation
# ---------------------------------------------------------------------------
@dataclass(slots=True)
class EncodedPolygon:
    sides: int
    orientation_index: int
    rotation_count: int
    delta: tuple[int, int, int]


# ---------------------------------------------------------------------------
# Public encoder / decoder
# ---------------------------------------------------------------------------
class PolyformEncoder:
    """High-level encoder that produces Unicode payloads."""

    def __init__(self, *, registry: Optional[SymbolRegistry] = None, tree: Optional[CompressionTree] = None) -> None:
        self.registry = registry or SymbolRegistry()
        self.tree = tree or CompressionTree(self.registry)

    def encode_polygons(self, polygons: Iterable[EncodedPolygon]) -> str:
        entries = [self._encode_polygon(entry) for entry in polygons]
        return "".join(entries)

    def encode_module_reference(self, module_index: int) -> str:
        if module_index < 0:
            raise ValueError("Module index must be non-negative")
        return "M" + _encode_vlq(module_index)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _encode_polygon(self, polygon: EncodedPolygon) -> str:
        primitive_symbol = self.registry.primitive_symbol(polygon.sides)
        orientation = _encode_orientation(polygon.orientation_index)
        rotation = _encode_vlq(polygon.rotation_count)
        dx, dy, dz = polygon.delta
        payload = [
            "P",
            primitive_symbol,
            orientation,
            rotation,
            _encode_signed_vlq(dx),
            _encode_signed_vlq(dy),
            _encode_signed_vlq(dz),
        ]
        return "".join(payload)


class PolyformDecoder:
    """Decode Unicode payloads into polygon entries and module references."""

    def __init__(self, *, registry: Optional[SymbolRegistry] = None, tree: Optional[CompressionTree] = None) -> None:
        self.registry = registry or SymbolRegistry()
        self.tree = tree or CompressionTree(self.registry)

    def decode(self, payload: str) -> List[Tuple[str, Union[int, EncodedPolygon]]]:
        index = 0
        tokens: List[Tuple[str, Union[int, EncodedPolygon]]] = []
        data = list(payload)
        while index < len(data):
            token = data[index]
            if token == "M":
                module_index, index = _decode_vlq(data, index + 1)
                tokens.append(("module", module_index))
                continue
            if token != "P":
                raise ValueError(f"Unexpected token: {token}")
            entry, index = self._decode_polygon(data, index + 1)
            tokens.append(("polygon", entry))
        return tokens

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _decode_polygon(self, data: Sequence[str], start: int) -> tuple[EncodedPolygon, int]:
        primitive_symbol = data[start]
        sides = self.registry.primitive_sides(primitive_symbol)
        orientation_index, index = _decode_orientation(data, start + 1)
        rotation_count, index = _decode_vlq(data, index)
        dx, index = _decode_signed_vlq(data, index)
        dy, index = _decode_signed_vlq(data, index)
        dz, index = _decode_signed_vlq(data, index)
        entry = EncodedPolygon(
            sides=sides,
            orientation_index=orientation_index,
            rotation_count=rotation_count,
            delta=(dx, dy, dz),
        )
        return entry, index


class TieredUnicodeEncoder:
    """Encodes polyforms using tiered Unicode allocation."""
    
    def __init__(self):
        # Tier 1: High-frequency (500 symbols)
        self.tier1_start = 0x1F300
        self.tier1_end = self.tier1_start + 499
        
        # Tier 2: Medium-frequency (5000 symbols)
        self.tier2_start = 0x1F900
        self.tier2_end = self.tier2_start + 4999
        
        # Tier 3: User-defined (reserve 0x1FA00–0x1FAFF)
        self.user_start = 0x1FA00
        self.user_end = 0x1FAFF
        
        self.next_tier1 = self.tier1_start
        self.next_tier2 = self.tier2_start
        self.overflow_map = {}
    
    def allocate(self, polyform_id: str, frequency: int) -> str:
        """Allocate Unicode symbol based on frequency tier."""
        # Tier 1: High-frequency
        if frequency > 1000 and self.next_tier1 <= self.tier1_end:
            char = chr(self.next_tier1)
            self.next_tier1 += 1
            return char
        
        # Tier 2: Medium-frequency
        if frequency > 100 and self.next_tier2 <= self.tier2_end:
            char = chr(self.next_tier2)
            self.next_tier2 += 1
            return char
        
        # Overflow: Use hash-based encoding
        if polyform_id not in self.overflow_map:
            hash_val = hash(polyform_id) & 0xFFFFFF
            char = f"U+{hash_val:06X}"
            self.overflow_map[polyform_id] = char
        return self.overflow_map[polyform_id]

    def allocate_parallel(self, polyform_ids: list[str], frequencies: list[int]) -> list[str]:
        """Allocate symbols in parallel."""
        with multiprocessing.Pool() as pool:
            args = [(id, freq) for id, freq in zip(polyform_ids, frequencies)]
            return pool.starmap(self.allocate, args)
