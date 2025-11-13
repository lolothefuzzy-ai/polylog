from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable

import json
import pytest

from polylog6.combinatorial import AssemblyView, CombinatorialCalculator


@dataclass
class StubAssembly:
    composition: Dict[str, int]
    polygons: Iterable[object]
    symmetry_group: str | None = None
    clusters: Iterable[Dict[str, int]] | None = None

    def polygon_count(self) -> int:
        return sum(self.composition.values())


@pytest.fixture(scope="module")
def scaler_tables() -> Dict[str, object]:
    with open("catalogs/scaler_tables.json", "r", encoding="utf-8") as handle:
        return json.load(handle)


@pytest.fixture
def calculator(scaler_tables: Dict[str, object]) -> CombinatorialCalculator:
    return CombinatorialCalculator(scaler_tables)


def test_calculate_O_known_polyhedron(calculator: CombinatorialCalculator) -> None:
    assembly = StubAssembly(composition={"triangle": 4}, polygons=[], symmetry_group="T")
    result = calculator.calculate_O(AssemblyView(composition=assembly.composition, polygons=assembly.polygons, symmetry_group=assembly.symmetry_group))
    assert pytest.approx(result, rel=1e-6) == 1.0


def test_calculate_I_known_polyhedron(calculator: CombinatorialCalculator) -> None:
    assembly = AssemblyView(composition={"triangle": 4}, polygons=[], symmetry_group="T")
    image_count = calculator.calculate_I(assembly, O_value=1.0)
    assert pytest.approx(image_count, rel=1e-6) == 7.0


def test_cascading_O_uses_clusters(calculator: CombinatorialCalculator) -> None:
    clusters = [{"triangle": 4}, {"square": 6}]
    assembly = AssemblyView(composition={"triangle": 4, "square": 6}, polygons=[], symmetry_group="O")
    assembly.clusters = clusters  # type: ignore[attr-defined]
    calculator.memo_O[calculator._make_signature(clusters[0])] = 1.0
    calculator.memo_O[calculator._make_signature(clusters[1])] = 1.0
    result = calculator.calculate_O(assembly, method="cascading")
    assert pytest.approx(result, rel=1e-6) == 1.0
