"""Combinatorial calculator for O/I metrics with cascading memoization."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from math import factorial
from typing import Dict, Iterable, List, Mapping, Optional

from polylog6.hardware import HardwareProfile
from polylog6.storage import SymbolRegistry


_PRIMITIVE_HINTS: Dict[str, tuple[str, int, str]] = {
    "A": ("triangle", 3, "T"),
    "B": ("square", 4, "O"),
    "C": ("pentagon", 5, "D_5"),
    "D": ("hexagon", 6, "D_6"),
}

_NAME_HINTS: Dict[str, tuple[str, int, str]] = {
    name: (name, sides, group)
    for name, sides, group in (
        ("triangle", 3, "T"),
        ("square", 4, "O"),
        ("pentagon", 5, "D_5"),
        ("hexagon", 6, "D_6"),
    )
}


@dataclass(slots=True)
class AssemblyView:
    """Lightweight view used by the calculator to inspect assemblies."""

    composition: Mapping[str, int]
    polygons: Iterable[object]
    clusters: Optional[Iterable[Dict[str, int]]] = None
    symmetry_group: str | None = None

    def polygon_count(self) -> int:
        return sum(self.composition.values())


class CombinatorialCalculator:
    """Compute O (distinct configurations) and I (image arrangements) metrics."""

    def __init__(
        self,
        scaler_tables: Mapping[str, object],
        *,
        registry: Optional[SymbolRegistry] = None,
        hardware_profile: Optional[HardwareProfile] = None,
    ) -> None:
        self.scaler_tables = scaler_tables
        self.registry = registry or SymbolRegistry()
        self.memo_O: Dict[str, float] = {}
        self.memo_I: Dict[str, float] = {}
        self.hardware_profile = hardware_profile
        self._gpu_batch_limit = self._determine_batch_limit()
        self.gpu_batch_count = 0
        self._seed_known_polyhedra()

    def _seed_known_polyhedra(self) -> None:
        polyforms = self.scaler_tables.get("polyforms") if isinstance(self.scaler_tables, Mapping) else None
        if isinstance(polyforms, Mapping):
            for _, data in polyforms.items():
                composition = self._normalise_composition(data.get("composition"))
                if composition is None:
                    continue
                signature = self._make_signature(composition)
                self.memo_O[signature] = float(data.get("o_value", data.get("O", 1.0)))
                self.memo_I[signature] = float(data.get("i_value", data.get("I", 1.0)))
        else:
            for value in self.scaler_tables.values() if isinstance(self.scaler_tables, Mapping) else ():
                if not isinstance(value, Mapping):
                    continue
                composition = self._normalise_composition(value.get("composition"))
                if composition is None:
                    continue
                signature = self._make_signature(composition)
                o_value = float(value.get("O", value.get("o_value", 1.0)))
                i_value = float(value.get("I", value.get("i_value", o_value)))
                self.memo_O[signature] = o_value
                self.memo_I[signature] = i_value

        self._seed_builtin_defaults()

    def _normalise_composition(self, payload: object) -> Optional[Mapping[str, int]]:
        if isinstance(payload, Mapping):
            try:
                return {str(symbol): int(count) for symbol, count in payload.items()}
            except (TypeError, ValueError):
                return None
        if isinstance(payload, str):
            counter = Counter(payload)
            return {symbol: count for symbol, count in counter.items()}
        return None

    def _seed_builtin_defaults(self) -> None:
        defaults = {
            "triangle4": (1.0, 7.0),
            "square6": (1.0, 24.0),
        }
        for signature, (o_value, i_value) in defaults.items():
            existing_o = self.memo_O.get(signature)
            if existing_o is None or existing_o < o_value:
                self.memo_O[signature] = o_value
            existing_i = self.memo_I.get(signature)
            if existing_i is None or existing_i < i_value:
                self.memo_I[signature] = i_value

    def _make_signature(self, composition: Mapping[str, int]) -> str:
        counter = Counter()
        for raw_symbol, count in composition.items():
            canonical = self._canonical_symbol(str(raw_symbol))
            counter[canonical] += int(count)
        return "".join(f"{symbol}{count}" for symbol, count in sorted(counter.items()))

    def _canonical_symbol(self, symbol: str) -> str:
        hint = self._lookup_hint(symbol)
        if hint is not None:
            name, _, _ = hint
            return name
        try:
            sides = self._sides_for_symbol(symbol)
            return f"sides{sides}"
        except Exception:
            return symbol.lower()

    def calculate_O(self, assembly: AssemblyView, method: str = "auto") -> float:
        signature = self._make_signature(assembly.composition)
        if signature in self.memo_O:
            return self.memo_O[signature]

        if method in ("auto", "cascading"):
            cascaded = self._try_cascading_O(assembly)
            if cascaded is not None:
                self.memo_O[signature] = cascaded
                return cascaded

        if method in ("auto", "estimation"):
            estimated = self._estimate_O_geometric(assembly)
            self.memo_O[signature] = estimated
            return estimated

        raise ValueError(f"Unsupported method: {method}")

    def calculate_I(self, assembly: AssemblyView, O_value: Optional[float] = None) -> float:
        signature = self._make_signature(assembly.composition)
        if signature in self.memo_I:
            stored_O = self.memo_O.get(signature)
            if O_value is None or stored_O is None or abs(stored_O - O_value) < 1e-9:
                return self.memo_I[signature]

        distinct_configurations = O_value if O_value is not None else self.calculate_O(assembly)
        s_total = self._calculate_s_total(assembly)
        arrangement = self._arrangement_capability(assembly)
        symmetry_factor = self._symmetry_correction(assembly)

        image_count = distinct_configurations * s_total * arrangement * symmetry_factor
        self.memo_I[signature] = image_count
        return image_count

    def batch_calculate_O(self, assemblies: Iterable[AssemblyView]) -> List[float]:
        """Calculate O across a collection, batching based on hardware tier."""

        batch_limit = max(1, self._gpu_batch_limit)
        self.gpu_batch_count = 0

        results: List[float] = []
        batch: List[AssemblyView] = []

        for assembly in assemblies:
            batch.append(assembly)
            if len(batch) >= batch_limit:
                results.extend(self._process_batch(batch))
                batch = []

        if batch:
            results.extend(self._process_batch(batch))

        return results

    def _try_cascading_O(self, assembly: AssemblyView) -> Optional[float]:
        clusters = assembly.clusters
        if not clusters:
            return None

        total = 1.0
        for cluster in clusters:
            signature = self._make_signature(cluster)
            cached = self.memo_O.get(signature)
            if cached is None:
                return None
            total *= cached
        return total

    def _estimate_O_geometric(self, assembly: AssemblyView) -> float:
        n = assembly.polygon_count()
        types = len(assembly.composition)
        base = max(types * 2, 1)
        rate = 1.4 + 0.1 * types
        return sum(base * (rate ** k) for k in range(1, n + 1))

    def _calculate_s_total(self, assembly: AssemblyView) -> float:
        value = 0.0
        for symbol, count in assembly.composition.items():
            sides = self._sides_for_symbol(symbol)
            value += sides ** count
        return float(value)

    def _process_batch(self, batch: List[AssemblyView]) -> List[float]:
        self.gpu_batch_count += 1
        return [self.calculate_O(assembly) for assembly in batch]

    def _determine_batch_limit(self) -> int:
        profile = self.hardware_profile
        if profile is None:
            return 64

        vram = profile.vram_gb
        if vram >= 16.0:
            return 128
        if vram >= 8.0:
            return 64
        if vram > 0:
            return 32
        # CPU-only hosts fall back to modest batching
        return 16

    def _arrangement_capability(self, assembly: AssemblyView) -> float:
        total = assembly.polygon_count()
        counts = Counter()
        for count in assembly.composition.values():
            counts[count] += 1

        numerator = factorial(total)
        denominator = 1
        for symbol_count in assembly.composition.values():
            denominator *= factorial(symbol_count)
        return float(numerator / denominator)

    def _symmetry_correction(self, assembly: AssemblyView) -> float:
        group = assembly.symmetry_group or self._infer_point_group(assembly)
        if group == "C_1":
            return 1.0
        if group.startswith("C_"):
            order = int(group.split("_")[1])
            return 1.0 / max(order, 1)
        table = {"D": 1.0 / 24, "T": 1.0 / 12, "O": 1.0 / 24, "I": 1.0 / 60}
        return table.get(group, 1.0)

    def _sides_for_symbol(self, symbol: str) -> int:
        hint = self._lookup_hint(symbol)
        if hint is not None:
            return hint[1]
        name_to_sides = {
            "triangle": 3,
            "square": 4,
            "pentagon": 5,
            "hexagon": 6,
            "heptagon": 7,
            "octagon": 8,
            "nonagon": 9,
            "decagon": 10,
            "hendecagon": 11,
            "dodecagon": 12,
        }

        if symbol in name_to_sides:
            return name_to_sides[symbol]

        try:
            return self.registry.primitive_sides(symbol)
        except ValueError:
            return 6

    def _infer_point_group(self, assembly: AssemblyView) -> str:
        if not assembly.composition:
            return "C_1"
        if len(assembly.composition) > 1:
            return "C_1"
        symbol = next(iter(assembly.composition))
        hint = self._lookup_hint(symbol)
        if hint is None:
            return "C_1"
        return hint[2]

    def _lookup_hint(self, symbol: str) -> Optional[tuple[str, int, str]]:
        if not symbol:
            return None
        if symbol in _PRIMITIVE_HINTS:
            return _PRIMITIVE_HINTS[symbol]
        upper = symbol.upper()
        if upper in _PRIMITIVE_HINTS:
            return _PRIMITIVE_HINTS[upper]
        lower = symbol.lower()
        if lower in _NAME_HINTS:
            return _NAME_HINTS[lower]
        return None
