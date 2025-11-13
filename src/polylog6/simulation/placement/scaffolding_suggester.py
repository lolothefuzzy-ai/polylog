"""Scaffolding suggestion utilities backed by the symbol registry."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence

from polylog6.storage.symbol_registry import ScaffoldingAsset, SymbolRegistry


@dataclass(slots=True)
class ScaffoldingSuggestion:
    """Represents a ranked scaffolding asset candidate."""

    symbol: str
    asset: ScaffoldingAsset
    score: float
    reasons: Dict[str, object] = field(default_factory=dict)

    @property
    def thumbnail_uri(self) -> Optional[str]:
        return self.asset.thumbnail_uri


class ScaffoldingSuggestionService:
    """Suggest reusable scaffolding assets for open attachment signatures."""

    def __init__(self, *, registry: Optional[SymbolRegistry] = None) -> None:
        self._registry = registry or SymbolRegistry()

    def suggest_for_gaps(
        self,
        edge_signatures: Sequence[str] | Iterable[str],
        *,
        symmetry_group: Optional[str] = None,
        limit: int = 5,
    ) -> List[ScaffoldingSuggestion]:
        """Return a ranked list of scaffolding assets covering the provided gaps."""

        ranked: List[ScaffoldingSuggestion] = []
        seen_symbols: set[str] = set()

        for signature in edge_signatures:
            assets = self._registry.lookup_by_attachment(str(signature))
            for asset in assets:
                if asset.symbol in seen_symbols:
                    continue
                suggestion = self._score_asset(
                    asset,
                    edge_signature=str(signature),
                    symmetry_group=symmetry_group,
                )
                ranked.append(suggestion)
                seen_symbols.add(asset.symbol)

        ranked.sort(key=lambda item: item.score, reverse=True)
        if limit > 0:
            return ranked[:limit]
        return ranked

    def suggest_single(
        self,
        edge_signature: str,
        *,
        symmetry_group: Optional[str] = None,
    ) -> Optional[ScaffoldingSuggestion]:
        """Return the top scaffolding asset for a single attachment signature."""

        suggestions = self.suggest_for_gaps(
            [edge_signature],
            symmetry_group=symmetry_group,
            limit=1,
        )
        return suggestions[0] if suggestions else None

    def _score_asset(
        self,
        asset: ScaffoldingAsset,
        *,
        edge_signature: str,
        symmetry_group: Optional[str],
    ) -> ScaffoldingSuggestion:
        """Derive a heuristic score for a scaffolding asset."""

        score = 1.0
        reasons: Dict[str, object] = {"edge_signature": edge_signature}

        if symmetry_group and asset.symmetry_group:
            if asset.symmetry_group.lower() == symmetry_group.lower():
                score += 0.35
                reasons["symmetry_match"] = True
            else:
                score -= 0.1
                reasons["symmetry_match"] = False

        priority = asset.metadata.get("priority") if asset.metadata else None
        if isinstance(priority, (int, float)):
            # Normalise around nominal priority of 10
            score += min(max(priority / 20.0, -0.25), 0.5)
            reasons["priority_hint"] = priority

        reuse_count = asset.metadata.get("reuse_count") if asset.metadata else None
        if isinstance(reuse_count, int) and reuse_count > 0:
            score += min(reuse_count / 100.0, 0.4)
            reasons["reuse_count"] = reuse_count

        return ScaffoldingSuggestion(symbol=asset.symbol, asset=asset, score=score, reasons=reasons)


__all__ = ["ScaffoldingSuggestion", "ScaffoldingSuggestionService"]
