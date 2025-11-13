"""Workspace utilities supporting streamed polyform checkpoints."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Tuple, Union

from polylog6.storage.encoder import EncodedPolygon


@dataclass(slots=True)
class WorkspacePolygon:
    """Internal representation retained inside the simulation workspace."""

    sides: int
    orientation_index: int
    rotation_count: int
    position_delta: Tuple[int, int, int]

    def to_encoded(self) -> EncodedPolygon:
        """Convert the workspace entry into an :class:`EncodedPolygon`."""

        return EncodedPolygon(
            sides=self.sides,
            orientation_index=self.orientation_index,
            rotation_count=self.rotation_count,
            delta=self.position_delta,
        )


class PolyformWorkspace:
    """Acts as both producer and consumer for encoded polygon streams."""

    def __init__(self) -> None:
        self._polygons: List[WorkspacePolygon] = []
        self._module_refs: List[Tuple[int, int]] = []  # (chunk_index, module_id)

    # ------------------------------------------------------------------
    # Mutation helpers
    # ------------------------------------------------------------------
    def add_polygon(
        self,
        *,
        sides: int,
        orientation_index: int,
        rotation_count: int,
        delta: Tuple[int, int, int],
    ) -> None:
        """Add a polygon emitted by the geometry runtime."""

        self._polygons.append(
            WorkspacePolygon(
                sides=sides,
                orientation_index=orientation_index,
                rotation_count=rotation_count,
                position_delta=delta,
            )
        )

    def add_encoded(self, polygon: EncodedPolygon) -> None:
        """Insert an encoded polygon directly."""

        self.add_polygon(
            sides=polygon.sides,
            orientation_index=polygon.orientation_index,
            rotation_count=polygon.rotation_count,
            delta=polygon.delta,
        )

    def extend(self, polygons: Iterable[EncodedPolygon]) -> None:
        """Append an iterable of encoded polygons."""

        for polygon in polygons:
            self.add_encoded(polygon)

    # ------------------------------------------------------------------
    # Producer interface
    # ------------------------------------------------------------------
    def iter_encoded_polygons(self) -> Iterable[EncodedPolygon]:
        """Yield encoded polygons for the storage manager."""

        for polygon in self._polygons:
            yield polygon.to_encoded()

    # ------------------------------------------------------------------
    # Consumer interface
    # ------------------------------------------------------------------
    def ingest_tokens(
        self,
        chunk_index: int,
        tokens: List[Tuple[str, Union[int, EncodedPolygon]]],
    ) -> None:
        """Apply decoded tokens during a restore sequence."""

        for token_type, payload in tokens:
            if token_type == "polygon":
                assert isinstance(payload, EncodedPolygon)
                self.add_encoded(payload)
            elif token_type == "module":
                module_id = int(payload)
                self._module_refs.append((chunk_index, module_id))
            else:
                raise ValueError(f"Unknown token type: {token_type}")

    # ------------------------------------------------------------------
    # Introspection helpers
    # ------------------------------------------------------------------
    def clear(self) -> None:
        """Reset the workspace state."""

        self._polygons.clear()
        self._module_refs.clear()

    def polygon_count(self) -> int:
        """Return the number of polygons held in memory."""

        return len(self._polygons)

    def module_references(self) -> List[Tuple[int, int]]:
        """Return recorded module references."""

        return list(self._module_refs)
