"""Hierarchical compression tree scaffolding.

This module provides the data structures and helper methods used by the encoder
and decoder to transform polyform assemblies into Unicode strings following the
five-tier hierarchy (primitives → pairs → clusters → assemblies → mega
structures). The implementation is intentionally incremental: caching hooks and
streaming modes are present but can be refined as the workspace evolves.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Tuple

from .symbol_registry import SymbolRegistry


@dataclass(slots=True)
class CompressionResult:
    """Container for compression outputs."""

    symbol: str
    is_new: bool
    encoding: str
    depth: int


class CompressionTree:
    """Manages hierarchical compression and lookup across symbol tiers."""

    def __init__(self, registry: Optional[SymbolRegistry] = None) -> None:
        self.registry = registry or SymbolRegistry()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def compress_polygon_sequence(self, sides: Sequence[int]) -> CompressionResult:
        """Compress a raw polygon side sequence into hierarchical encoding."""
        primitive_symbols = [self.registry.primitive_symbol(side) for side in sides]
        hierarchical = self._collapse_pairs(primitive_symbols)
        encoding = "".join(hierarchical)
        return CompressionResult(symbol=encoding, is_new=False, encoding=encoding, depth=1)

    def compress_cluster(self, signature: str, *, flexible: bool = False) -> CompressionResult:
        """Register or look up a cluster symbol."""
        symbol = self.registry.allocate_cluster(signature, flexible=flexible)
        return CompressionResult(symbol=symbol, is_new=True, encoding=symbol, depth=2)

    def compress_assembly(self, signature: str) -> CompressionResult:
        """Register or look up an assembly symbol."""
        symbol = self.registry.allocate_assembly(signature)
        return CompressionResult(symbol=symbol, is_new=True, encoding=symbol, depth=3)

    def compress_mega(self, signature: str) -> CompressionResult:
        """Register or look up a mega-structure symbol."""
        symbol = self.registry.allocate_mega(signature)
        return CompressionResult(symbol=symbol, is_new=True, encoding=symbol, depth=4)

    def expand_primitives(self, symbols: Iterable[str]) -> List[int]:
        """Expand primitive symbols back to polygon side counts."""
        return [self.registry.primitive_sides(symbol) for symbol in symbols]

    def expand_pairs(self, symbols: Iterable[str]) -> List[Tuple[str, str]]:
        """Expand pair symbols back to primitive symbol tuples."""
        return [self.registry.pair_symbol(symbol, symbol) or (symbol, symbol) for symbol in symbols]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _collapse_pairs(self, primitive_symbols: Sequence[str]) -> List[str]:
        """Replace primitive pairs with preallocated Unicode symbols."""
        collapsed: List[str] = []
        index = 0
        length = len(primitive_symbols)
        while index < length:
            current = primitive_symbols[index]
            if index + 1 < length:
                pair_symbol = self.registry.pair_symbol(current, primitive_symbols[index + 1])
                if pair_symbol:
                    collapsed.append(pair_symbol)
                    index += 2
                    continue
            collapsed.append(current)
            index += 1
        return collapsed

    # ------------------------------------------------------------------
    # Streaming / scaling hooks
    # ------------------------------------------------------------------
    def stream_encode(self, sequence: Iterable[Sequence[int]]) -> Iterable[str]:
        """Stream encode batches of polygon side sequences."""
        for batch in sequence:
            yield self.compress_polygon_sequence(batch).encoding

    def stream_decode(self, sequence: Iterable[str]) -> Iterable[List[int]]:
        """Stream decode batches back into side sequences."""
        for token in sequence:
            yield self.expand_primitives(token)
