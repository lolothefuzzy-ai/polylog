"""Placement runtime emitting GeometryEvent batches for SimulationEngine.

This draft ties the automated placement pipeline into the streaming storage
framework. A future iteration will hydrate real polyforms from the stable
library and attachment schemas; for now we provide a deterministic mock that
respects scalers and optional fold metadata without animating each fold.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional, Sequence

from polylog6.simulation.runtime import GeometryEvent
from polylog6.storage.encoder import EncodedPolygon
from polylog6.storage.manager import PolyformStorageManager
from .attachment_resolver import AttachmentOption, ContextAwareAttachmentResolver
from .scaffolding_suggester import ScaffoldingSuggestion, ScaffoldingSuggestionService
from .fold_sequencer import FoldSequencer


@dataclass(slots=True)
class PlacementSpec:
    """Describes a polyform placement operation for runtime execution."""

    polyform_id: str
    attachment_schema: str
    scaler: float = 1.0
    folds: Optional[Sequence[float]] = None
    preserve_fold_animation: bool = False
    checkpoint_label: Optional[str] = None


@dataclass(slots=True)
class PlacementEvent:
    """Event emitted by the placement engine with ready-to-stream polygons."""

    polygons: List[EncodedPolygon]
    label: str
    force_checkpoint: bool = False


@dataclass(slots=True)
class _SimplePolygon:
    sides: int


@dataclass(slots=True)
class _WorkspaceView:
    dimension: str = "3d"
    symmetry_group: Optional[str] = None
    closure_ratio: Optional[float] = None
    polygons: List[_SimplePolygon] = field(default_factory=list)

    def polygon_count(self) -> int:
        return len(self.polygons)


class PolyformHydrator:
    """Hydrates placement-ready polygon batches from catalog assets."""

    @dataclass(slots=True)
    class HydratorCatalogs:
        geometry: Dict[str, Any]
        attachment: Dict[str, Any]
        scaler: Dict[str, Any]
        lod: Dict[str, Any]

        def summary(self) -> Dict[str, object]:
            return {
                "geometry": self.geometry.get("version"),
                "attachment": self.attachment.get("version"),
                "scaler": self.scaler.get("version"),
                "lod": self.lod.get("version"),
            }

    def instantiate(
        self,
        *,
        polyform_id: str,
        scaler: float,
        folds: Optional[Sequence[float]],
    ) -> List[EncodedPolygon]:
        base = [
            EncodedPolygon(6, 0, 0, (0, 0, 0)),
            EncodedPolygon(4, 1, 1, (1, 0, 0)),
            EncodedPolygon(3, 2, 2, (1, 1, 0)),
        ]
        if folds and scaler < 1.0:
            # compact arrangement for dense fold sequences
            offsets = [(0, 0, 0), (0, 1, 0), (0, 2, 0)]
        else:
            offsets = [(dx, dy, dz) for dx, dy, dz in [p.delta for p in base]]

        scaled: List[EncodedPolygon] = []
        for polygon, offset in zip(base, offsets, strict=False):
            dx = int(round(offset[0] * scaler))
            dy = int(round(offset[1] * scaler))
            dz = int(round(offset[2] * scaler))
            scaled.append(
                EncodedPolygon(
                    sides=polygon.sides,
                    orientation_index=polygon.orientation_index,
                    rotation_count=polygon.rotation_count,
                    delta=(dx, dy, dz),
                )
            )
        return scaled


class PlacementRuntime:
    """Transforms placement specs into GeometryEvent sequences."""

    def __init__(
        self,
        *,
        storage_manager: PolyformStorageManager,
        scaler_registry: Optional[dict[str, float]] = None,
        hydrator: Optional[PolyformHydrator] = None,
        catalog_dir: Optional[Path] = None,
        attachment_resolver: Optional[ContextAwareAttachmentResolver] = None,
        scaffolding_suggester: Optional[ScaffoldingSuggestionService] = None,
        fold_sequencer: Optional[FoldSequencer] = None,
    ) -> None:
        self._storage_manager = storage_manager
        self._scaler_registry = scaler_registry or {}
        self._hydrator = hydrator or self._default_hydrator(catalog_dir)
        self._attachment_resolver = attachment_resolver or ContextAwareAttachmentResolver()
        self._scaffolding_suggester = scaffolding_suggester or ScaffoldingSuggestionService()
        self._fold_sequencer = fold_sequencer or self._default_fold_sequencer(self._hydrator)

    def emit_events(self, placements: Iterable[PlacementSpec]) -> Iterator[GeometryEvent]:
        for spec in placements:
            scaler = spec.scaler or self._scaler_registry.get(spec.polyform_id, 1.0)
            polygons = self._hydrator.instantiate(
                polyform_id=spec.polyform_id,
                scaler=scaler,
                folds=spec.folds,
            )
            attachment_schema = spec.attachment_schema
            if attachment_schema.lower() == "auto" and len(polygons) >= 2:
                option = self.resolve_attachment_schema(
                    polygons[0].sides,
                    polygons[1].sides,
                    dimension="2d" if scaler <= 1.0 else "3d",
                )
                if option is not None:
                    attachment_schema = option.char
                else:
                    scaffold = self.resolve_scaffolding_symbol(
                        polygons[0].sides,
                        polygons[1].sides,
                        dimension="2d" if scaler <= 1.0 else "3d",
                    )
                    if scaffold is not None:
                        attachment_schema = scaffold.symbol

            label = spec.checkpoint_label or attachment_schema
            metadata: Dict[str, object] = {}
            if self._fold_sequencer is not None:
                sequence = self._generate_fold_metadata(spec.polyform_id, scaler=scaler)
                if sequence:
                    metadata["fold_sequence"] = sequence
            yield GeometryEvent(
                polygons=polygons,
                force_checkpoint=spec.preserve_fold_animation,
                label_override=label,
                metadata=metadata or None,
            )

    # ------------------------------------------------------------------
    # Resolver helpers
    # ------------------------------------------------------------------
    def resolve_attachment_schema(
        self,
        source_sides: int,
        target_sides: int,
        *,
        dimension: str = "3d",
        symmetry_group: Optional[str] = None,
        closure_ratio: Optional[float] = None,
        prefer_context: Optional[str] = None,
    ) -> Optional[AttachmentOption]:
        """Resolve the best attachment schema for the given polygon pair."""

        source = _SimplePolygon(source_sides)
        target = _SimplePolygon(target_sides)
        workspace = _WorkspaceView(
            dimension=dimension,
            symmetry_group=symmetry_group,
            closure_ratio=closure_ratio,
            polygons=[source, target],
        )

        return self._attachment_resolver.resolve_best_attachment(
            source,
            target,
            workspace,
            prefer_context=prefer_context,
        )

    def resolve_scaffolding_symbol(
        self,
        source_sides: int,
        target_sides: int,
        *,
        dimension: str = "3d",
        symmetry_group: Optional[str] = None,
        closure_ratio: Optional[float] = None,
    ) -> Optional[ScaffoldingSuggestion]:
        """Suggest a scaffolding asset compatible with the inferred gap."""

        signature = self._make_edge_signature(source_sides, target_sides, dimension=dimension)
        return self._scaffolding_suggester.suggest_single(
            signature,
            symmetry_group=symmetry_group or ("d4" if closure_ratio and closure_ratio >= 0.75 else None),
        )

    @staticmethod
    def _make_edge_signature(
        source_sides: int,
        target_sides: int,
        *,
        dimension: str,
    ) -> str:
        first, second = sorted([source_sides, target_sides])
        return f"{first}:{second}@{dimension}"

    def _generate_fold_metadata(self, polyform_id: str, *, scaler: float) -> Optional[Dict[str, object]]:
        if self._fold_sequencer is None:
            return None
        try:
            sequence = self._fold_sequencer.generate_sequence(polyform_id, scaler=scaler)
        except Exception:
            return None
        steps = [
            {
                "index": step.index,
                "symbol": step.polygon_symbol,
                "angle_degrees": step.angle_degrees,
                "axis": step.axis,
                "duration_ms": step.duration_ms,
            }
            for step in sequence.steps
        ]
        return {
            "collisions": sequence.collisions_detected,
            "warnings": sequence.warnings,
            "lod_levels": list(sequence.lod_levels_used),
            "steps": steps,
        }


    @staticmethod
    def _default_hydrator(catalog_dir: Optional[Path]) -> PolyformHydrator:
        return CatalogBackedHydrator(catalog_dir=catalog_dir)

    @staticmethod
    def _default_fold_sequencer(hydrator: PolyformHydrator) -> Optional[FoldSequencer]:
        if isinstance(hydrator, CatalogBackedHydrator):
            catalogs = hydrator.catalogs
            return FoldSequencer(
                geometry_catalog=catalogs.geometry,
                scaler_catalog=catalogs.scaler,
                lod_metadata=catalogs.lod,
            )
        return None


@dataclass(slots=True)
class CatalogBackedHydrator(PolyformHydrator):
    """Concrete hydrator that loads catalog JSON assets on initialization."""

    catalog_dir: Path = Path("catalogs")

    def __post_init__(self) -> None:
        self.catalog_dir = self.catalog_dir if self.catalog_dir.is_absolute() else Path.cwd() / self.catalog_dir
        self.catalogs = self._load_catalogs()

    def instantiate(
        self,
        *,
        polyform_id: str,
        scaler: float,
        folds: Optional[Sequence[float]],
    ) -> List[EncodedPolygon]:
        components = self._resolve_components(polyform_id)
        if not components:
            return super().instantiate(polyform_id=polyform_id, scaler=scaler, folds=folds)

        polygons: List[EncodedPolygon] = []
        for component in components:
            sides = int(component.get("sides", 0))
            if sides < 3:
                continue
            cx, cy, cz = self._centroid(component.get("vertices", []))
            scaled_delta = (
                int(round(cx * scaler)),
                int(round(cy * scaler)),
                int(round(cz * scaler)),
            )
            polygons.append(
                EncodedPolygon(
                    sides=sides,
                    orientation_index=0,
                    rotation_count=0,
                    delta=scaled_delta,
                )
            )

        if not polygons:
            return super().instantiate(polyform_id=polyform_id, scaler=scaler, folds=folds)
        return polygons

    def _load_catalogs(self) -> PolyformHydrator.HydratorCatalogs:
        geometry = self._load_json("geometry/geometry_catalog.json")
        attachment = self._load_json("attachments/attachment_graph.json")
        scaler = self._load_json("geometry/scaler_tables.json")
        lod = self._load_json("geometry/lod_metadata.json")
        return PolyformHydrator.HydratorCatalogs(
            geometry=geometry,
            attachment=attachment,
            scaler=scaler,
            lod=lod,
        )

    def _load_json(self, name: str) -> Dict[str, Any]:
        path = self.catalog_dir / name
        if not path.exists():
            raise FileNotFoundError(f"Catalog asset missing: {path}")
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _resolve_components(self, polyform_id: str) -> List[Dict[str, Any]]:
        geometry = self.catalogs.geometry if hasattr(self, "catalogs") else {}
        primitives = geometry.get("primitives", {}) if isinstance(geometry, dict) else {}

        if polyform_id in primitives:
            return [primitives[polyform_id]]

        # Allow lookup by primitive symbol (A–R).
        for entry in primitives.values():
            if entry.get("symbol") == polyform_id:
                return [entry]

        polyhedra = geometry.get("polyhedra", {}) if isinstance(geometry, dict) else {}
        if polyform_id in polyhedra:
            results: List[Dict[str, Any]] = []
            for component in polyhedra[polyform_id].get("components", []):
                if isinstance(component, str):
                    results.extend(self._resolve_components(component))
                elif isinstance(component, dict):
                    results.append(component)
            return results

        return []

    @staticmethod
    def _centroid(vertices: Sequence[Sequence[float]]) -> tuple[float, float, float]:
        if not vertices:
            return (0.0, 0.0, 0.0)
        count = len(vertices)
        sx = sum(vertex[0] for vertex in vertices)
        sy = sum(vertex[1] for vertex in vertices)
        sz = sum(vertex[2] for vertex in vertices)
        return (sx / count, sy / count, sz / count)


__all__ = [
    "CatalogBackedHydrator",
    "PlacementRuntime",
    "PlacementSpec",
    "PlacementEvent",
    "PolyformHydrator",
]
