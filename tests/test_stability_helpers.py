"""Unit tests for stability_helpers.py."""
from __future__ import annotations

import os
import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import pytest

from common.stability_helpers import (
    StabilityMetricsInput,
    cached_stability_score,
    clear_stability_cache,
)


# Mock scoring function for testing
@cached_stability_score
def mock_scoring(metrics_input: StabilityMetricsInput) -> float:
    """Simulate expensive computation."""
    time.sleep(0.01)  # Simulate processing time
    return sum(metrics_input.side_counts) / len(metrics_input.side_counts)

@pytest.fixture
def sample_input() -> StabilityMetricsInput:
    """Test fixture providing sample stability metrics input."""
    return StabilityMetricsInput(
        polyform_count=3,
        side_counts=(4, 5, 6),
        centroids=((1.0, 1.0, 1.0), (2.0, 2.0, 2.0)),
        bond_count=2,
        config={"default_score": 0.9},
    )

def test_cache_hit(sample_input: StabilityMetricsInput):
    """Test that repeated calls with same input hit cache."""
    # First call should compute
    result1 = mock_scoring(sample_input)
    
    # Second call should hit cache
    with patch.object(mock_scoring, '__wrapped__') as mock:
        result2 = mock_scoring(sample_input)
        mock.assert_not_called()
    
    assert result1 == result2

def test_cache_miss_after_ttl(sample_input: StabilityMetricsInput):
    """Test cache expiration after TTL."""
    # Set short TTL for this test
    os.environ["POLYLOG_USE_STABILITY_CACHE"] = "True"
    
    # First call caches result
    mock_scoring(sample_input)
    
    # Wait past TTL
    time.sleep(1)
    
    # Should recompute
    with patch.object(mock_scoring, '__wrapped__') as mock:
        mock_scoring(sample_input)
        mock.assert_called_once()

def test_thread_safety(sample_input: StabilityMetricsInput):
    """Test concurrent cache access doesn't cause race conditions."""
    def worker() -> float:
        return mock_scoring(sample_input)
    
    # Run multiple threads hitting same cache key
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(worker) for _ in range(10)]
        results = [f.result() for f in futures]
    
    # All results should be equal (no corruption)
    assert len(set(results)) == 1

def test_cache_clear():
    """Test clearing the cache works."""
    input1 = StabilityMetricsInput(
        polyform_count=1,
        side_counts=(4,),
        centroids=((1.0, 1.0, 1.0),),
        bond_count=0,
        config={},
    )
    
    # Cache a value
    mock_scoring(input1)
    
    # Clear cache
    clear_stability_cache()
    
    # Should recompute
    with patch.object(mock_scoring, '__wrapped__') as mock:
        mock_scoring(input1)
        mock.assert_called_once()

def test_feature_toggle(sample_input: StabilityMetricsInput):
    """Test cache can be disabled via feature flag."""
    os.environ["POLYLOG_USE_STABILITY_CACHE"] = "False"
    
    # Should always call through to wrapped function
    with patch.object(mock_scoring, '__wrapped__') as mock:
        mock_scoring(sample_input)
        mock_scoring(sample_input)
        assert mock.call_count == 2
