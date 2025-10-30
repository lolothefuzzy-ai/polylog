"""
Integration tests for the polyform adapter and data pipeline.
Tests data flow through the main components using the normalized format.
"""

import unittest
from PySide6.QtWidgets import QApplication
import sys

import os
import sys

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from gui.polyform_adapter import normalize_polyform
from polyform_visualizer import PolyformVisualizer, Viewport3D

class TestPolyformIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create Qt application instance
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication(sys.argv)
    
    def setUp(self):
        self.visualizer = PolyformVisualizer()
        self.viewport = self.visualizer.viewport
    
    def test_add_basic_polygon(self):
        """Test adding a basic polygon through the pipeline."""
        # Create test data
        test_data = {
            'vertices': [(0,0), (1,0), (1,1), (0,1)],
            'n_sides': 4,
            'type': 'test_square'
        }
        
        # Add through viewport
        self.viewport.add_polygon(test_data)
        
        # Verify result
        self.assertEqual(len(self.viewport.polygons), 1)
        result = self.viewport.polygons[0]
        
        # Check normalization
        self.assertEqual(result['sides'], 4)
        self.assertEqual(len(result['vertices']), 4)
        self.assertTrue(all(len(v) == 3 for v in result['vertices']))
        self.assertEqual(result['type'], 'test_square')
        self.assertTrue('id' in result)
        self.assertTrue('position' in result)
        self.assertTrue('bonds' in result)
    
    def test_random_polyform_generation(self):
        """Test random polyform generation and normalization."""
        # Generate random polyform
        self.visualizer.add_random_polyform()
        
        # Verify result
        self.assertEqual(len(self.viewport.polygons), 1)
        result = self.viewport.polygons[0]
        
        # Check normalized format
        self.assertTrue('sides' in result)
        self.assertTrue('vertices' in result)
        self.assertTrue('position' in result)
        self.assertTrue('id' in result)
        self.assertTrue('type' in result)
        self.assertTrue('bonds' in result)
    
    def test_multiple_polygons(self):
        """Test adding multiple polygons in sequence."""
        test_data = [
            {'vertices': [(0,0), (1,0), (0,1)], 'type': 'triangle'},
            {'vertices': [(0,0), (1,0), (1,1), (0,1)], 'type': 'square'},
            {'vertices': [(0,0), (1,0), (1.5,0.5), (1,1), (0,1)], 'type': 'pentagon'}
        ]
        
        # Add polygons
        for data in test_data:
            self.viewport.add_polygon(data)
        
        # Verify results
        self.assertEqual(len(self.viewport.polygons), 3)
        
        # Check each polygon is properly normalized
        for i, result in enumerate(self.viewport.polygons):
            self.assertEqual(result['sides'], i + 3)  # 3,4,5 sides
            self.assertEqual(len(result['vertices']), i + 3)
            self.assertTrue(all(len(v) == 3 for v in result['vertices']))
            self.assertEqual(result['type'], test_data[i]['type'])
            self.assertTrue('id' in result)
            self.assertTrue('position' in result)
            self.assertTrue('bonds' in result)

if __name__ == '__main__':
    unittest.main()