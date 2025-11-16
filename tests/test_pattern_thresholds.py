"""Unit tests for pattern threshold loading and filtering."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import polylog6.detection.patterns as patterns
from polylog6.detection.patterns import PatternAnalyzer, PatternAnalysisOptions


def _reset_threshold_cache() -> None:
    patterns._load_threshold_recommendations.cache_clear()  # type: ignore[attr-defined]


def test_analyzer_applies_threshold_recommendations(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    threshold_path = tmp_path / "pattern_thresholds.json"
    threshold_path.write_text(
        json.dumps(
            {
                "symmetry_threshold": 0.9,
                "fft_strength_threshold": 42.5,
                "fft_peak_median": 7.4,
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(patterns, "PATTERN_THRESHOLD_PATH", threshold_path)
    _reset_threshold_cache()

    analyzer = PatternAnalyzer()
    options = analyzer.options

    assert options.symmetry_threshold == pytest.approx(0.9)
    assert options.fft_strength_threshold == pytest.approx(42.5)
    assert options.max_period_peaks == 7


def test_filter_periods_respects_threshold_and_limit() -> None:
    analyzer = PatternAnalyzer(
        options=PatternAnalysisOptions(
            fft_strength_threshold=10.0,
            max_period_peaks=2,
        )
    )

    periods = [
        (1.0, 1.0, 5.0),
        (2.0, 2.0, 15.0),
        (3.0, 3.0, 30.0),
    ]

    filtered = analyzer._filter_periods(periods)
    assert filtered == [(2.0, 2.0, 15.0), (3.0, 3.0, 30.0)]
