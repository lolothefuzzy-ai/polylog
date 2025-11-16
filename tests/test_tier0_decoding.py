"""Comprehensive Tier 0 symbol decoding tests."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from polylog6.storage.tier0_generator import (  # noqa: E402
    EDGE_TO_SERIES_REFS,
    SERIES_TABLE,
    decode_tier0_symbol,
)


class TestSingleDigitPrimitives:
    """1-9: Single primitives A1-D9"""

    def test_triangle_A1(self):
        """A1 = 3 edges (triangle)"""
        result = decode_tier0_symbol("A1")
        assert result.symbol == "A1"
        assert result.polygons == [3]
        assert result.series == ["A"]
        assert result.positions == [1]

    def test_square_B2(self):
        """B2 = 4 edges (square)"""
        result = decode_tier0_symbol("B2")
        assert result.polygons == [4]

    def test_pentagon_A5(self):
        """A5 = 5 edges"""
        result = decode_tier0_symbol("A5")
        assert result.polygons == [5]

    def test_all_series_at_position_1(self):
        """A1, B1, C1, D1 all valid"""
        for series in ["A", "B", "C", "D"]:
            result = decode_tier0_symbol(f"{series}1")
            assert len(result.polygons) == 1
            assert result.series == [series]

    def test_all_positions_1_to_9(self):
        """Positions 1-9 all valid for each series"""
        for pos in range(1, 10):
            result = decode_tier0_symbol(f"A{pos}")
            assert result.positions == [pos]

    def test_redundant_references_triangle(self):
        """A1 and C1 both decode to 3 edges"""
        a1 = decode_tier0_symbol("A1")
        c1 = decode_tier0_symbol("C1")
        assert a1.polygons == c1.polygons == [3]

    def test_redundant_references_square(self):
        """B2 and D6 both decode to 4 edges"""
        b2 = decode_tier0_symbol("B2")
        d6 = decode_tier0_symbol("D6")
        assert b2.polygons == d6.polygons == [4]


class TestTwoDigitConnections:
    """10-99: Base + B connections (XY, skip X0)"""

    def test_triangle_square_A11(self):
        """A11 = A1 (3 edges) + B1 (20 edges)"""
        result = decode_tier0_symbol("A11")
        assert result.symbol == "A11"
        assert result.polygons == [3, 20]
        assert result.series == ["A", "B"]
        assert result.positions == [1, 1]

    def test_square_decagon_B25(self):
        """B25 = B2 (4 edges) + B5 (10 edges)"""
        result = decode_tier0_symbol("B25")
        assert result.polygons == [4, 10]

    def test_skip_rule_X0_rejects_A10(self):
        """A10 violates skip rule (ones digit = 0)"""
        with pytest.raises(ValueError, match="skip rule"):
            decode_tier0_symbol("A10")

    def test_skip_rule_X0_rejects_C20(self):
        """C20 violates skip rule"""
        with pytest.raises(ValueError, match="skip rule"):
            decode_tier0_symbol("C20")

    def test_skip_rule_X0_rejects_D30(self):
        """D30 violates skip rule"""
        with pytest.raises(ValueError, match="skip rule"):
            decode_tier0_symbol("D30")

    def test_two_digit_all_valid_tens_and_ones(self):
        """For XY where X,Y ∈ [1-9] (no 0), all valid"""
        valid = 0
        for tens in range(1, 10):
            for ones in range(1, 10):
                try:
                    result = decode_tier0_symbol(f"A{tens}{ones}")
                    assert len(result.polygons) == 2
                    valid += 1
                except ValueError:
                    pass

        assert valid == 81, "Should have 81 valid two-digit combinations (9×9)"

    def test_cyclic_pattern_B_connections(self):
        """A + B always valid (cyclic pattern A→B)"""
        result = decode_tier0_symbol("A19")
        assert result.series == ["A", "B"]


class TestThreeDigitChains:
    """100-899: Three-polygon chains (HXYY, skip X00, X0Y, X*0)"""

    def test_base_C_connection_A111(self):
        """A111 = A1 (3) + C1 (3) [2-polygon via C-series]"""
        result = decode_tier0_symbol("A111")
        assert result.polygons == [3, 3]
        assert result.series == ["A", "C"]
        assert result.positions == [1, 1]

    def test_base_D_connection_A219(self):
        """A219 = A2 (4) + D9 (19) [2-polygon via D-series]"""
        result = decode_tier0_symbol("A219")
        assert result.polygons == [4, 19]
        assert result.series == ["A", "D"]
        assert result.positions == [2, 9]

    def test_three_chain_tens_reference_A324(self):
        """A324 = 3-chain with tens reference (A3, B2, C4)"""
        result = decode_tier0_symbol("A324")
        assert result.polygons == [5, 4, 12]
        assert len(result.polygons) == 3

    def test_three_chain_ones_reference_A615(self):
        """A615 = 3-chain with ones reference (A6, B1, C5)"""
        result = decode_tier0_symbol("A615")
        assert result.polygons == [8, 20, 15]

    def test_skip_rule_X00_rejects_A100(self):
        """A100 violates skip rule (tens=0, ones=0)"""
        with pytest.raises(ValueError, match="skip rule"):
            decode_tier0_symbol("A100")

    def test_skip_rule_X0Y_rejects_A101(self):
        """A101 violates skip rule (tens=0)"""
        with pytest.raises(ValueError, match="skip rule"):
            decode_tier0_symbol("A101")

    def test_skip_rule_XY0_rejects_A120(self):
        """A120 violates skip rule (ones=0)"""
        with pytest.raises(ValueError, match="skip rule"):
            decode_tier0_symbol("A120")

    def test_hundreds_digit_determines_secondary_series(self):
        """Hundreds digit selects which series: 1=C, 2=D, etc."""
        a111 = decode_tier0_symbol("A111")
        a211 = decode_tier0_symbol("A211")

        assert "C" in a111.series
        assert "D" in a211.series

    def test_three_digit_all_valid_combinations(self):
        """For AXYY where H ∈ [1-8], X,Y ∈ [1-9], all valid"""
        valid = 0
        for hundreds in range(1, 9):
            for tens in range(1, 10):
                for ones in range(1, 10):
                    try:
                        result = decode_tier0_symbol(f"A{hundreds}{tens}{ones}")
                        assert len(result.polygons) in [2, 3]
                        valid += 1
                    except ValueError:
                        pass

        assert valid == 648, f"Expected 648 valid three-digit, got {valid}"


class TestReservedRange:
    """900-999: Reserved block"""

    def test_reserved_A900_raises(self):
        """A900 is in reserved range"""
        with pytest.raises(ValueError, match="reserved"):
            decode_tier0_symbol("A900")

    def test_reserved_D999_raises(self):
        """D999 is in reserved range"""
        with pytest.raises(ValueError, match="reserved"):
            decode_tier0_symbol("D999")

    def test_entire_900_999_range_reserved(self):
        """All 900-999 raise ValueError"""
        for tens in range(0, 10):
            for ones in range(0, 10):
                with pytest.raises(ValueError, match="reserved"):
                    decode_tier0_symbol(f"A9{tens}{ones}")


class TestRedundancyLookup:
    """EDGE_TO_SERIES_REFS: edge count → all valid (series, pos) refs"""

    def test_triangle_3_edges_references(self):
        """3 edges can be A1 or C1"""
        refs = EDGE_TO_SERIES_REFS[3]
        assert ("A", 1) in refs
        assert ("C", 1) in refs

    def test_square_4_edges_references(self):
        """4 edges can be B2 or D6"""
        refs = EDGE_TO_SERIES_REFS[4]
        assert ("B", 2) in refs
        assert ("D", 6) in refs

    def test_pentagon_5_edges_references(self):
        """5 edges can be A5 or D8"""
        refs = EDGE_TO_SERIES_REFS[5]
        assert ("A", 5) in refs
        assert ("D", 8) in refs

    def test_hexagon_6_edges_references(self):
        """6 edges can be B3 or C2"""
        refs = EDGE_TO_SERIES_REFS[6]
        assert ("B", 3) in refs
        assert ("C", 2) in refs

    def test_all_20_edge_counts_covered(self):
        """All distinct edge counts in series have at least 1 reference"""
        assert len(EDGE_TO_SERIES_REFS) >= 20

    def test_redundancy_consistency(self):
        """If (series, pos) → edge_count, then edge_count → includes (series, pos)"""
        for edge_count, refs in EDGE_TO_SERIES_REFS.items():
            for series, pos in refs:
                assert SERIES_TABLE[series][pos - 1] == edge_count


class TestRoundTrip:
    """Encode → Decode consistency"""

    def test_round_trip_all_singles(self):
        """A1-D9: Encode and decode match"""
        for series in ["A", "B", "C", "D"]:
            for pos in range(1, 10):
                symbol = f"{series}{pos}"
                result = decode_tier0_symbol(symbol)
                assert result.symbol == symbol

    def test_round_trip_all_twos(self):
        """10-99: Sample of valid combinations"""
        for symbol in ["A11", "A25", "A99", "B19", "C34", "D56"]:
            result = decode_tier0_symbol(symbol)
            assert result.symbol == symbol
            assert len(result.polygons) == 2

    def test_round_trip_all_threes(self):
        """100-899: Sample of valid combinations"""
        for symbol in ["A111", "A219", "A324", "A615", "B456", "D789"]:
            result = decode_tier0_symbol(symbol)
            assert result.symbol == symbol
            assert len(result.polygons) in [2, 3]


class TestLegacyPolyformsRegression:
    """Regression: Existing polyform Tier0 indices decode identically"""

    @pytest.mark.parametrize(
        "tier0_index",
        [
            "4(A111)",
            "8(A111) + 6(B222)",
            "4(A111) + 4(B333)",
        ],
    )
    def test_decode_polyform_indices(self, tier0_index):
        symbols = re.findall(r"[ABCD]\d{1,3}", tier0_index)
        assert symbols, "Expected at least one Tier0 symbol in composition string"
        for symbol in symbols:
            chain = decode_tier0_symbol(symbol)
            assert chain.symbol == symbol


class TestEdgeCases:
    """Boundary conditions and malformed input"""

    def test_lowercase_rejects(self):
        with pytest.raises(ValueError):
            decode_tier0_symbol("a1")

    def test_empty_string_rejects(self):
        with pytest.raises(ValueError):
            decode_tier0_symbol("")

    def test_single_char_rejects(self):
        with pytest.raises(ValueError):
            decode_tier0_symbol("A")

    def test_five_digit_rejects(self):
        with pytest.raises(ValueError):
            decode_tier0_symbol("A1111")

    def test_invalid_series_rejects(self):
        with pytest.raises(ValueError):
            decode_tier0_symbol("E1")

    def test_position_zero_rejects(self):
        with pytest.raises(ValueError):
            decode_tier0_symbol("A0")

    def test_position_above_nine_rejects(self):
        with pytest.raises(ValueError):
            decode_tier0_symbol("A10")
