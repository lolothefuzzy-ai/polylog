"""Context-aware attachment resolver leveraging schema compression tables."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from polylog6.storage import (
    POLYGON_PAIR_ATTACHMENT_MATRIX,
    SCHEMA_PARTITIONS,
    ContextSchema,
    SymbolRegistry,
    is_placeholder_context,
)

_ATTACHMENT_ORDER = [
    "fold_angle",
    "stability",
    "closure",
    "generation",
    "dimension",
]


@dataclass(frozen=True)
class AttachmentOption:
    """Resolved attachment option returned by the resolver."""

    pair: str
    context: str
    char: str
    schema_code: str
    schema_components: Dict[str, Dict[str, object]]
    score: float


class ContextAwareAttachmentResolver:
    """Resolve polygon attachments using context-specific schema characters."""

    def __init__(
        self,
        *,
        matrix: Optional[Dict[str, Dict[str, ContextSchema]]] = None,
        registry: Optional[SymbolRegistry] = None,
    ) -> None:
        self._matrix = matrix or POLYGON_PAIR_ATTACHMENT_MATRIX
        self._cache: Dict[Tuple[str, str], AttachmentOption] = {}
        self._registry = registry or SymbolRegistry()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def find_all_attachments(
        self,
        source_polygon,
        target_polygon,
        workspace,
        *,
        prefer_context: Optional[str] = None,
        limit: int = 5,
    ) -> List[AttachmentOption]:
        """Return ranked attachment options for the polygon pair."""

        pair_key = self._make_pair_key(source_polygon, target_polygon)
        contexts = self._matrix.get(pair_key)
        if not contexts:
            return []

        ranked: List[AttachmentOption] = []
        for context_name, entry in contexts.items():
            if prefer_context and context_name != prefer_context:
                continue
            option = self._build_option(
                pair_key,
                context_name,
                entry,
                workspace,
                preferred_context=prefer_context,
            )
            ranked.append(option)

        # No entries matched preference – fall back to all contexts.
        if not ranked and prefer_context:
            for context_name, entry in contexts.items():
                option = self._build_option(
                    pair_key,
                    context_name,
                    entry,
                    workspace,
                    preferred_context=None,
                )
                ranked.append(option)

        ranked.sort(key=lambda opt: opt.score, reverse=True)
        return ranked[:limit]

    def resolve_best_attachment(
        self,
        source_polygon,
        target_polygon,
        workspace,
        *,
        prefer_context: Optional[str] = None,
    ) -> Optional[AttachmentOption]:
        """Return the highest scoring attachment option for the given pair."""

        pair_key = self._make_pair_key(source_polygon, target_polygon)
        context_key = self._determine_context(workspace, prefer_context)
        cache_key = (pair_key, context_key)

        if cache_key in self._cache:
            return self._cache[cache_key]

        contexts = self._matrix.get(pair_key)
        if not contexts:
            return None

        context_entry = contexts.get(context_key)
        if context_entry is None:
            context_entry = contexts.get("user_defined") or next(iter(contexts.values()))

        option = self._build_option(
            pair_key,
            context_key,
            context_entry,
            workspace,
            preferred_context=context_key,
        )
        self._cache[cache_key] = option
        return option

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _make_pair_key(self, source_polygon, target_polygon) -> str:
        source_symbol = self._primitive_symbol(source_polygon.sides)
        target_symbol = self._primitive_symbol(target_polygon.sides)
        first, second = sorted([source_symbol, target_symbol])
        return f"{first}↔{second}"

    def _primitive_symbol(self, sides: int) -> str:
        return self._registry.primitive_symbol(sides)

    def _determine_context(self, workspace, prefer_context: Optional[str]) -> str:
        if prefer_context:
            return prefer_context

        dimension = getattr(workspace, "dimension", None)
        symmetry = getattr(workspace, "symmetry_group", None)
        closure_ratio = getattr(workspace, "closure_ratio", None)

        if symmetry:
            key = f"workspace_symmetry_{symmetry.lower()}"
            return key

        if dimension == "2d":
            return "dim_2d_planar"
        if dimension == "3d":
            return "dim_3d_mixed"

        if isinstance(closure_ratio, (int, float)):
            if closure_ratio >= 0.75:
                return "closure_ratio_high"
            return "closure_ratio_low"

        return "user_defined"

    def _build_option(
        self,
        pair_key: str,
        context_name: str,
        entry: ContextSchema,
        workspace,
        preferred_context: Optional[str],
    ) -> AttachmentOption:
        schema_code = entry.primary
        schema_components = self._expand_schema_code(schema_code)
        score = self._score_attachment(
            schema_components,
            workspace,
            context_name=context_name,
            preferred_context=preferred_context,
            placeholder=is_placeholder_context(entry),
        )
        return AttachmentOption(
            pair=pair_key,
            context=context_name,
            char=entry.char,
            schema_code=schema_code,
            schema_components=schema_components,
            score=score,
        )

    def _expand_schema_code(self, schema_code: str) -> Dict[str, Dict[str, object]]:
        remaining = schema_code
        components: Dict[str, Dict[str, object]] = {}

        for partition in _ATTACHMENT_ORDER:
            table = SCHEMA_PARTITIONS[partition]
            token, remaining = _extract_token(remaining, table)
            if token is not None:
                components[partition] = table[token]

        return components

    def _score_attachment(
        self,
        schema_components: Dict[str, Dict[str, object]],
        workspace,
        *,
        context_name: str,
        preferred_context: Optional[str],
        placeholder: bool,
    ) -> float:
        geometric_fit = self._estimate_geometric_fit(workspace)
        context_match = 1.0 if preferred_context == context_name else 0.8
        stability_threshold = schema_components.get("stability", {}).get("threshold", 0.5)
        stability_component = float(stability_threshold)

        placeholder_penalty = 0.6 if placeholder else 1.0
        return (geometric_fit * 0.4 + context_match * 0.3 + stability_component * 0.3) * placeholder_penalty

    @staticmethod
    def _estimate_geometric_fit(workspace) -> float:
        polygon_count = getattr(workspace, "polygon_count", None)
        if callable(polygon_count):
            count = polygon_count()
        else:
            count = len(getattr(workspace, "polygons", []))
        return 1.0 if count else 0.8


def _extract_token(
    schema_code: str,
    table: Dict[str, Dict[str, object]],
) -> Tuple[Optional[str], str]:
    if not schema_code:
        return None, schema_code

    for token in sorted(table.keys(), key=len, reverse=True):
        if schema_code.startswith(token):
            return token, schema_code[len(token) :]
    return None, schema_code


__all__ = ["AttachmentOption", "ContextAwareAttachmentResolver"]
