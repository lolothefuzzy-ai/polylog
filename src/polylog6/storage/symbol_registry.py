"""Symbol registry aligned with the hierarchical dictionary specification.

The registry keeps deterministic mappings between geometric structures and
Unicode symbols so that encoder/decoder pipelines can translate between expanded
polyform data and the compressed string representation described in the
Structure & Science files.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
import os
import threading
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from .descriptors import to_subscript
from .tier0_generator import ConnectivityChain, Tier0Generator


# ---------------------------------------------------------------------------
# Tier 0 canonical ordering (maintained for backward compatibility).
_PRIMARY_SYMBOL_ORDER: List[Tuple[str, int]] = [
    ("a1", 11),
    ("a2", 13),
    ("a3", 3),
    ("a4", 15),
    ("a5", 5),
    ("a6", 17),
    ("a7", 7),
    ("a8", 19),
    ("a9", 9),
    ("b1", 20),
    ("b2", 4),
    ("b3", 6),
    ("b4", 8),
    ("b5", 10),
    ("b6", 12),
    ("b7", 14),
    ("b8", 16),
    ("b9", 18),
]

class EdgeConnectivityIndex:
    """Tier 0 lookup index backed by the hierarchical generator."""

    __slots__ = (
        "generator",
        "catalog",
        "by_edges",
        "by_chain_length",
        "by_series_pair",
        "primary_by_edges",
        "symbol_to_edges",
    )

    def __init__(self, generator: Tier0Generator | None = None) -> None:
        self.generator = generator or Tier0Generator()
        self.catalog = self.generator.generate_all()
        self.by_edges = self.generator.by_edges
        self.by_chain_length = self.generator.by_chain_length
        self.by_series_pair = self.generator.by_series_pair

        # Maintain primitive ordering for compatibility with prior Tier 0 table.
        self.primary_by_edges: Dict[int, str] = {}
        self.symbol_to_edges: Dict[str, int] = {}

        for symbol, chain in self.catalog.items():
            for edges in chain.polygons:
                self.symbol_to_edges[symbol] = chain.polygons[0]

            if len(chain.polygons) == 1:
                edges = chain.polygons[0]
                if edges not in self.primary_by_edges:
                    self.primary_by_edges[edges] = symbol

        # Override ordering with legacy canonical sequence to avoid churn.
        for raw_symbol, edges in _PRIMARY_SYMBOL_ORDER:
            self.primary_by_edges[edges] = raw_symbol

    @staticmethod
    def default() -> "EdgeConnectivityIndex":
        return EdgeConnectivityIndex()

    def lookup_by_edges(self, edge_count: int) -> List[str]:
        return list(self.by_edges.get(edge_count, ()))

    def lookup_by_chain_length(self, length: int) -> List[str]:
        return list(self.by_chain_length.get(length, ()))

    def lookup_by_series_pair(self, base_series: str, second_series: str) -> List[str]:
        key = (base_series.upper(), second_series.upper())
        return list(self.by_series_pair.get(key, ()))

    def primary_symbol(self, edge_count: int) -> str:
        if edge_count not in self.primary_by_edges:
            raise ValueError(f"Unsupported polygon with {edge_count} edges")
        return self.primary_by_edges[edge_count]

    def edges_for_symbol(self, symbol: str) -> int:
        key = symbol.lower()
        chain = self.catalog.get(key)
        if not chain:
            raise ValueError(f"Unknown Tier 0 symbol: {symbol}")
        return chain.polygons[0]

    def get_chain(self, symbol: str) -> Optional[ConnectivityChain]:
        return self.catalog.get(symbol.lower())

    def iter_primary_items(self) -> Iterable[Tuple[int, str]]:
        for edges in sorted(self.primary_by_edges):
            yield edges, self.primary_by_edges[edges]


def _new_edge_index() -> EdgeConnectivityIndex:
    return EdgeConnectivityIndex.default()


_DEFAULT_TIER0_INDEX = _new_edge_index()

PRIMITIVE_SYMBOLS: Dict[int, str] = {edges: symbol for edges, symbol in _DEFAULT_TIER0_INDEX.iter_primary_items()}
PRIMITIVE_BY_SYMBOL: Dict[str, int] = {symbol: edges for symbol, edges in _DEFAULT_TIER0_INDEX.symbol_to_edges.items()}


# Pre-allocated Greek symbols for common pairs.
PAIR_SYMBOLS: Dict[Tuple[str, str], str] = {}
PAIR_BY_SYMBOL: Dict[str, Tuple[str, str]] = {}

_GREEK_LOWER = [
    "α",
    "β",
    "γ",
    "δ",
    "ε",
    "ζ",
    "η",
    "θ",
    "ι",
    "κ",
    "λ",
    "μ",
    "ν",
    "ξ",
    "ο",
    "π",
    "ρ",
    "σ",
    "τ",
    "υ",
    "φ",
    "χ",
    "ψ",
    "ω",
]
_GREEK_UPPER = [
    "Α",
    "Β",
    "Γ",
    "Δ",
    "Ε",
    "Ζ",
    "Η",
    "Θ",
    "Ι",
    "Κ",
    "Λ",
    "Μ",
    "Ν",
    "Ξ",
    "Ο",
    "Π",
    "Ρ",
    "Σ",
    "Τ",
    "Υ",
    "Φ",
    "Χ",
    "Ψ",
    "Ω",
]
_EXTENDED_LATIN = [
    "À",
    "Á",
    "Â",
    "Ã",
    "Ä",
    "Å",
    "Æ",
    "Ç",
    "È",
    "É",
    "Ê",
    "Ë",
    "Ì",
    "Í",
    "Î",
    "Ï",
    "Ð",
    "Ñ",
    "Ò",
    "Ó",
    "Ô",
    "Õ",
    "Ö",
    "Ø",
    "Ù",
    "Ú",
    "Û",
    "Ü",
    "Ý",
    "Þ",
    "ß",
]
_PAIR_SYMBOL_SEQUENCE = _GREEK_LOWER + _GREEK_UPPER + _EXTENDED_LATIN


def _initialize_pair_symbols() -> None:
    index = 0
    primitives = list(PRIMITIVE_SYMBOLS.values())
    for i, a in enumerate(primitives):
        for b in primitives[i:]:  # ordered pairs without duplicates
            if index >= len(_PAIR_SYMBOL_SEQUENCE):
                return
            symbol = _PAIR_SYMBOL_SEQUENCE[index]
            PAIR_SYMBOLS[(a, b)] = symbol
            PAIR_BY_SYMBOL[symbol] = (a, b)
            index += 1


_initialize_pair_symbols()


LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class VisualizationPayload:
    """Validated visualization asset references."""

    mesh_ref: str
    net_ref: str
    thumbnail_uri: str

    def is_valid(self) -> bool:
        """Reject partial payloads."""

        return all((self.mesh_ref, self.net_ref, self.thumbnail_uri))


@dataclass(slots=True)
class ScaffoldingAsset:
    """Metadata describing a reusable scaffolding component."""

    symbol: str
    symmetry_group: str
    edge_signatures: List[str]
    scaler_table_ref: str
    mesh_ref: str
    thumbnail_uri: Optional[str] = None
    metadata: Dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class SymbolRegistry:
    """Registry handling allocation and lookup of Unicode symbols."""

    cluster_prefix: str = "Ω"
    flexible_prefix: str = "Φ"
    assembly_prefix: str = "Ψ"
    mega_prefix: str = "Ξ"

    tier0_index: EdgeConnectivityIndex = field(default_factory=_new_edge_index)

    clusters: Dict[str, str] = field(default_factory=dict)
    cluster_by_symbol: Dict[str, str] = field(default_factory=dict)
    assemblies: Dict[str, str] = field(default_factory=dict)
    assembly_by_symbol: Dict[str, str] = field(default_factory=dict)
    megas: Dict[str, str] = field(default_factory=dict)
    mega_by_symbol: Dict[str, str] = field(default_factory=dict)
    scaffolding_assets: Dict[str, ScaffoldingAsset] = field(default_factory=dict)
    compatibility_index: Dict[str, List[str]] = field(default_factory=dict)
    visualization_index: Dict[str, Dict[str, object]] = field(default_factory=dict)

    _batch_lock: threading.RLock = field(init=False, repr=False)
    _batch_stats: Dict[str, object] = field(init=False, repr=False)
    _refresh_debounce_timer: Optional[threading.Timer] = field(init=False, default=None, repr=False)
    _refresh_debounce_sec: float = field(init=False, default=2.0, repr=False)
    _refresh_in_progress: bool = field(init=False, default=False, repr=False)

    def __post_init__(self) -> None:
        self._batch_lock = threading.RLock()
        self._batch_stats = {
            "committed": 0,
            "queued_for_viz": 0,
            "validation_failures": 0,
            "threshold_decisions": [],
        }

    def primitive_symbol(self, sides: int) -> str:
        """Return the canonical tier 0 symbol for a primitive polygon."""
        return self.tier0_index.primary_symbol(sides)

    def primitive_sides(self, symbol: str) -> int:
        """Resolve the number of sides from a Tier 0 symbol."""
        return self.tier0_index.edges_for_symbol(symbol)

    def pair_symbol(self, first: str, second: str) -> Optional[str]:
        """Return the predefined symbol for a primitive pair."""
        pair = (first, second) if first <= second else (second, first)
        return PAIR_SYMBOLS.get(pair)

    def allocate_cluster(self, signature: str, *, flexible: bool = False) -> str:
        """Register (or retrieve) a symbol for a cluster signature."""
        store = self.clusters if not flexible else self.assemblies
        reverse = self.cluster_by_symbol if not flexible else self.assembly_by_symbol
        prefix = self.cluster_prefix if not flexible else self.flexible_prefix

        if signature in store:
            return store[signature]

        symbol = self._generate_symbol(prefix, len(store) + 1)
        store[signature] = symbol
        reverse[symbol] = signature
        return symbol

    def get_cluster_signature(self, symbol: str) -> Optional[str]:
        """Resolve the signature previously registered for a cluster."""
        return self.cluster_by_symbol.get(symbol)

    def allocate_assembly(self, signature: str) -> str:
        """Allocate an assembly symbol (Ψ series)."""
        if signature in self.assemblies:
            return self.assemblies[signature]
        symbol = self._generate_symbol(self.assembly_prefix, len(self.assemblies) + 1)
        self.assemblies[signature] = symbol
        self.assembly_by_symbol[symbol] = signature
        return symbol

    def allocate_mega(self, signature: str) -> str:
        """Allocate a mega-structure symbol (Ξ series)."""
        if signature in self.megas:
            return self.megas[signature]
        symbol = self._generate_symbol(self.mega_prefix, len(self.megas) + 1)
        self.megas[signature] = symbol
        self.mega_by_symbol[symbol] = signature
        return symbol

    def _generate_symbol(self, base: str, index: int) -> str:
        """Generate a Unicode symbol with subscripted index."""
        return f"{base}{to_subscript(index)}"

    def export_state(self) -> Dict[str, Dict[str, str]]:
        """Return a JSON-serializable snapshot of registry state."""
        return {
            "clusters": self.clusters,
            "assemblies": self.assemblies,
            "megas": self.megas,
        }

    def load_state(self, state: Dict[str, Dict[str, str]]) -> None:
        """Restore registry state from storage."""

        self.clusters = state.get("clusters", {})
        self.cluster_by_symbol = {symbol: signature for signature, symbol in self.clusters.items()}
        self.assemblies = state.get("assemblies", {})
        self.assembly_by_symbol = {symbol: signature for signature, symbol in self.assemblies.items()}
        self.megas = state.get("megas", {})
        self.mega_by_symbol = {symbol: signature for signature, symbol in self.megas.items()}

    def load_scaffolding_assets(self, catalog_path: Path | str) -> None:
        """Load reusable scaffolding assets and compatibility indices.

        ``catalog_path`` may point to the scaffolding directory or directly to
        the metadata JSONL file. The directory form expects:

        * ``metadata.jsonl`` – JSON object per line describing each asset.
        * ``compatibility_index.json`` – mapping of edge signatures to symbols.
        """

        base_path = Path(catalog_path)
        metadata_path: Path
        compat_path: Optional[Path] = None

        if base_path.is_dir():
            metadata_path = base_path / "metadata.jsonl"
            compat_index_candidate = base_path / "compatibility_index.json"
            if compat_index_candidate.exists():
                compat_path = compat_index_candidate
        else:
            metadata_path = base_path
            compat_candidate = metadata_path.with_name("compatibility_index.json")
            if compat_candidate.exists():
                compat_path = compat_candidate

        if not metadata_path.exists():
            LOGGER.debug("Scaffolding metadata not found at %s", metadata_path)
            return

        loaded_assets: Dict[str, ScaffoldingAsset] = {}
        with metadata_path.open("r", encoding="utf-8") as handle:
            for line_number, raw in enumerate(handle, start=1):
                data = raw.strip()
                if not data:
                    continue
                try:
                    payload = json.loads(data)
                except json.JSONDecodeError as exc:
                    LOGGER.warning(
                        "Skipping scaffolding asset line %s (invalid JSON): %s",
                        line_number,
                        exc,
                    )
                    continue

                symbol = str(payload.get("symbol", "")).strip()
                if not symbol:
                    LOGGER.warning(
                        "Skipping scaffolding asset line %s (missing symbol)",
                        line_number,
                    )
                    continue

                edge_signatures = payload.get("edge_signatures", [])
                if not isinstance(edge_signatures, list):
                    LOGGER.warning(
                        "Skipping scaffolding asset %s due to malformed edge_signatures",
                        symbol,
                    )
                    continue

                asset = ScaffoldingAsset(
                    symbol=symbol,
                    symmetry_group=str(payload.get("symmetry_group", "")),
                    edge_signatures=[str(sig) for sig in edge_signatures],
                    scaler_table_ref=str(payload.get("scaler_table_ref", "")),
                    mesh_ref=str(payload.get("mesh_ref", "")),
                    thumbnail_uri=payload.get("thumbnail_uri"),
                    metadata=dict(payload.get("metadata", {})),
                )
                loaded_assets[symbol] = asset

        self.scaffolding_assets = loaded_assets

        if compat_path and compat_path.exists():
            try:
                compat_payload = json.loads(compat_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                LOGGER.warning("Failed to parse compatibility index %s: %s", compat_path, exc)
                compat_payload = {}
        else:
            compat_payload = {}

        compatibility: Dict[str, List[str]] = {}
        for signature, symbols in compat_payload.items():
            if not isinstance(symbols, list):
                LOGGER.debug(
                    "Ignoring malformed compatibility entry for %s (expected list)",
                    signature,
                )
                continue
            compatibility[str(signature)] = [str(symbol) for symbol in symbols]

        if not compatibility:
            for asset in self.scaffolding_assets.values():
                for signature in asset.edge_signatures:
                    compatibility.setdefault(signature, []).append(asset.symbol)

        self.compatibility_index = compatibility

    def lookup_scaffold(self, symbol: str) -> Optional[ScaffoldingAsset]:
        """Return the scaffolding asset metadata for a given symbol, if any."""

        return self.scaffolding_assets.get(symbol)

    def lookup_by_attachment(self, edge_signature: str) -> List[ScaffoldingAsset]:
        """Return scaffolding assets compatible with the provided edge signature."""

        symbols = self.compatibility_index.get(edge_signature, [])
        return [asset for symbol in symbols if (asset := self.scaffolding_assets.get(symbol))]

    def batch_commit_scaffolding(
        self,
        assets: List[Dict[str, object]],
        visualization_payloads: Optional[Dict[str, Dict[str, str]]] = None,
    ) -> Tuple[List[str], List[str]]:
        """Atomically commit a batch of scaffolding assets."""

        committed: List[str] = []
        queued_for_viz: List[str] = []

        if visualization_payloads:
            for symbol, payload in visualization_payloads.items():
                viz_payload = VisualizationPayload(**payload)
                if not viz_payload.is_valid():
                    LOGGER.error(
                        "Invalid visualization payload for %s: missing mesh_ref, net_ref, or thumbnail_uri",
                        symbol,
                    )
                    self._batch_stats["validation_failures"] += 1
                    raise ValueError(f"Incomplete visualization payload for symbol {symbol}")

        base_fields = {
            "symbol",
            "symmetry_group",
            "edge_signatures",
            "scaler_table_ref",
            "mesh_ref",
            "thumbnail_uri",
            "metadata",
        }

        with self._batch_lock:
            for asset in assets:
                symbol = str(asset["symbol"])
                edge_signatures = [str(sig) for sig in asset.get("edge_signatures", [])]

                existing = self.scaffolding_assets.get(symbol)
                if isinstance(existing, ScaffoldingAsset):
                    metadata: Dict[str, object] = dict(existing.metadata)
                    base_symmetry = existing.symmetry_group
                    base_edge_sigs = list(existing.edge_signatures)
                    scaler_table_ref = existing.scaler_table_ref
                    mesh_ref = existing.mesh_ref
                    thumbnail_uri = existing.thumbnail_uri
                elif isinstance(existing, dict):
                    metadata = dict(existing.get("metadata", {}))
                    base_symmetry = str(existing.get("symmetry_group", asset.get("symmetry_group", "")))
                    base_edge_sigs = [str(sig) for sig in existing.get("edge_signatures", edge_signatures)]
                    scaler_table_ref = str(existing.get("scaler_table_ref", asset.get("scaler_table_ref", "")))
                    mesh_ref = str(existing.get("mesh_ref", asset.get("mesh_ref", "")))
                    thumbnail_uri = existing.get("thumbnail_uri")
                else:
                    metadata = {}
                    base_symmetry = str(asset.get("symmetry_group", ""))
                    base_edge_sigs = edge_signatures
                    scaler_table_ref = str(asset.get("scaler_table_ref", ""))
                    mesh_ref = str(asset.get("mesh_ref", ""))
                    thumbnail_uri = asset.get("thumbnail_uri")

                incoming_metadata = dict(asset.get("metadata", {}))
                metadata.update(incoming_metadata)

                extra_fields = {k: v for k, v in asset.items() if k not in base_fields}
                if extra_fields:
                    metadata.setdefault("attributes", {}).update(extra_fields)

                if edge_signatures:
                    base_edge_sigs = edge_signatures
                if asset.get("symmetry_group"):
                    base_symmetry = str(asset["symmetry_group"])
                if asset.get("scaler_table_ref"):
                    scaler_table_ref = str(asset["scaler_table_ref"])
                if asset.get("mesh_ref"):
                    mesh_ref = str(asset["mesh_ref"])
                if asset.get("thumbnail_uri") is not None:
                    thumbnail_uri = asset.get("thumbnail_uri")

                if (
                    asset.get("commit_visualization")
                    and visualization_payloads
                    and symbol in visualization_payloads
                ):
                    payload = visualization_payloads[symbol]
                    mesh_ref = payload["mesh_ref"]
                    metadata.setdefault("visualization", {}).update(payload)
                    queued_for_viz.append(symbol)
                    LOGGER.info(
                        "Committed visualization for %s: mesh=%s",
                        symbol,
                        payload.get("mesh_ref"),
                    )

                updated_asset = ScaffoldingAsset(
                    symbol=symbol,
                    symmetry_group=base_symmetry,
                    edge_signatures=list(base_edge_sigs),
                    scaler_table_ref=scaler_table_ref,
                    mesh_ref=mesh_ref,
                    thumbnail_uri=thumbnail_uri,
                    metadata=metadata,
                )

                self.scaffolding_assets[symbol] = updated_asset
                committed.append(symbol)

                for signature in edge_signatures:
                    bucket = self.compatibility_index.setdefault(signature, [])
                    if symbol not in bucket:
                        bucket.append(symbol)
                        LOGGER.debug(
                            "Mapped edge signature '%s' → %s (%s total)",
                            signature,
                            symbol,
                            len(bucket),
                        )

        self._batch_stats["committed"] += len(committed)
        self._batch_stats["queued_for_viz"] += len(queued_for_viz)

        LOGGER.info(
            "Batch commit: %s scaffolding assets, %s queued for visualization",
            len(committed),
            len(queued_for_viz),
        )

        return committed, queued_for_viz

    def refresh_visualization_catalog_debounced(self, catalog_root: str = "catalogs/polyform_library") -> None:
        """Schedule a catalog refresh after a debounce delay."""

        if self._refresh_debounce_timer:
            self._refresh_debounce_timer.cancel()

        timer = threading.Timer(
            self._refresh_debounce_sec,
            self.refresh_visualization_catalog,
            args=(catalog_root,),
        )
        timer.daemon = True
        timer.start()
        self._refresh_debounce_timer = timer

        LOGGER.debug(
            "Scheduled visualization catalog refresh (debounce: %.2fs)",
            self._refresh_debounce_sec,
        )

    def refresh_visualization_catalog(self, catalog_root: str = "catalogs/polyform_library") -> None:
        """Scan the visualization catalog and update the in-memory index."""

        if self._refresh_in_progress:
            LOGGER.debug("Visualization catalog refresh already in progress; skipping")
            return

        self._refresh_in_progress = True

        try:
            LOGGER.info("Refreshing visualization catalog from %s", catalog_root)
            new_index: Dict[str, Dict[str, object]] = {}

            if not os.path.exists(catalog_root):
                LOGGER.warning("Visualization catalog root not found: %s", catalog_root)
                with self._batch_lock:
                    self.visualization_index = new_index
                return

            for symbol_dir in os.listdir(catalog_root):
                symbol_path = os.path.join(catalog_root, symbol_dir)
                if not os.path.isdir(symbol_path):
                    continue

                manifest: Dict[str, object] = {
                    "symbol": symbol_dir,
                    "assets": {},
                }

                mesh_path = os.path.join(symbol_path, "mesh.glb")
                if os.path.exists(mesh_path):
                    manifest["assets"]["mesh_3d"] = {
                        "path": mesh_path,
                        "format": "glTF",
                        "mtime": os.path.getmtime(mesh_path),
                    }

                simplified_path = os.path.join(symbol_path, "mesh_simplified.glb")
                if os.path.exists(simplified_path):
                    manifest["assets"]["mesh_simplified"] = {
                        "path": simplified_path,
                        "format": "glTF",
                        "mtime": os.path.getmtime(simplified_path),
                    }

                net_path = os.path.join(symbol_path, "net.svg")
                if os.path.exists(net_path):
                    manifest["assets"]["net_2d"] = {
                        "path": net_path,
                        "format": "SVG",
                        "mtime": os.path.getmtime(net_path),
                    }

                thumb_path = os.path.join(symbol_path, "thumb_256.png")
                if os.path.exists(thumb_path):
                    manifest["assets"]["thumbnail"] = {
                        "path": thumb_path,
                        "mtime": os.path.getmtime(thumb_path),
                    }

                if manifest["assets"]:
                    new_index[symbol_dir] = manifest

            with self._batch_lock:
                self.visualization_index = new_index

            LOGGER.info("Visualization catalog refreshed: %s assets indexed", len(new_index))

        finally:
            self._refresh_in_progress = False

    def iter_primitives(self) -> Iterable[Tuple[int, str]]:
        """Yield primitive polygon side counts and symbols."""
        yield from self.tier0_index.iter_primary_items()

    def iter_pairs(self) -> Iterable[Tuple[Tuple[str, str], str]]:
        """Yield primitive-pair symbols."""
        return PAIR_SYMBOLS.items()


PolyformSymbolRegistry = SymbolRegistry


__all__ = [
    "SymbolRegistry",
    "PolyformSymbolRegistry",
    "EdgeConnectivityIndex",
    "PRIMITIVE_SYMBOLS",
    "PRIMITIVE_BY_SYMBOL",
    "PAIR_SYMBOLS",
    "PAIR_BY_SYMBOL",
]
