#!/usr/bin/env python3
"""Tests for PolygonRangeSlider module."""

import unittest
from Properties.Code.PolygonRangeSlider import PolygonRangeSlider

class TestPolygonRangeSlider(unittest.TestCase):
    def test_initialization(self):
        """Test slider initialization."""
        slider = PolygonRangeSlider()
        self.assertEqual(slider.min_value, 0)
        self.assertEqual(slider.max_value, 100)
        
    def test_value_range(self):
        slider = PolygonRangeSlider()
        slider.setRange(0, 50)
        self.assertEqual(slider.min_value, 0)
        self.assertEqual(slider.max_value, 50)
        
    def test_value_setting(self):
        slider = PolygonRangeSlider()
        slider.setValue(25)
        self.assertEqual(slider.value, 25)
        
    def test_edge_values(self):
        slider = PolygonRangeSlider()
        slider.setRange(0, 100)
        slider.setValue(0)
        self.assertEqual(slider.value, 0)
        slider.setValue(100)
        self.assertEqual(slider.value, 100)
        
    def test_out_of_range(self):
        slider = PolygonRangeSlider()
        slider.setRange(10, 90)
        with self.assertRaises(ValueError):
            slider.setValue(5)
        with self.assertRaises(ValueError):
            slider.setValue(95)

if __name__ == "__main__":
    unittest.main()
