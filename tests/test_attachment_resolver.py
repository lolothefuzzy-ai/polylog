from __future__ import annotations

from dataclasses import dataclass
from typing import List

import pytest

from polylog6.simulation.placement.attachment_resolver import (
    AttachmentOption,
    ContextAwareAttachmentResolver,
)
from polylog6.storage import POLYGON_PAIR_ATTACHMENT_MATRIX


@dataclass
class DummyPolygon:
    sides: int


@dataclass
class DummyWorkspace:
    dimension: str = "3d"
    symmetry_group: str | None = None
    closure_ratio: float | None = None
    polygons: List[DummyPolygon] | None = None

    def polygon_count(self) -> int:
        return len(self.polygons or [])


@pytest.fixture
def resolver() -> ContextAwareAttachmentResolver:
    return ContextAwareAttachmentResolver(POLYGON_PAIR_ATTACHMENT_MATRIX)


def test_resolver_returns_options(resolver: ContextAwareAttachmentResolver) -> None:
    source = DummyPolygon(3)
    target = DummyPolygon(3)
    workspace = DummyWorkspace(dimension="2d", polygons=[source, target])

    options = resolver.find_all_attachments(source, target, workspace, prefer_context="dim_2d_planar")

    assert options, "Expected at least one attachment option"
    for option in options:
        assert isinstance(option, AttachmentOption)
        assert option.char
        assert option.schema_code


def test_resolver_context_switch(resolver: ContextAwareAttachmentResolver) -> None:
    source = DummyPolygon(3)
    target = DummyPolygon(4)
    workspace_2d = DummyWorkspace(dimension="2d", polygons=[source, target])
    workspace_3d = DummyWorkspace(dimension="3d", polygons=[source, target])

    option_2d = resolver.resolve_best_attachment(source, target, workspace_2d)
    option_3d = resolver.resolve_best_attachment(source, target, workspace_3d)

    assert option_2d is not None
    assert option_3d is not None
    assert option_2d.char != option_3d.char


def test_resolver_fallback_to_user_defined(resolver: ContextAwareAttachmentResolver) -> None:
    source = DummyPolygon(19)  # beyond registry default, expect placeholder
    target = DummyPolygon(19)
    workspace = DummyWorkspace(dimension="3d", polygons=[source, target])

    option = resolver.resolve_best_attachment(source, target, workspace)

    assert option is not None
    assert option.char
