#!/usr/bin/env python3
"""Tests for PolygonRangeSlider module."""

import unittest
from Properties.Code import PolygonRangeSlider

class TestPolygonRangeSlider(unittest.TestCase):
    def test_initialization(self):
        """Test slider initialization."""
        slider = PolygonRangeSlider()
        self.assertEqual(slider.min_value, 0)
        self.assertEqual(slider.max_value, 100)

if __name__ == "__main__":
    unittest.main()
