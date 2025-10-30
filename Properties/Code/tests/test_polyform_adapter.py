"""
Tests for the polyform adapter module.

Verifies the normalize_polyform() function correctly handles various input cases
and produces consistently formatted output.
"""

import unittest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import just the normalize_polyform function to avoid GUI dependencies
import importlib.util
adapter_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                           "gui", "polyform_adapter.py")
spec = importlib.util.spec_from_file_location("polyform_adapter", adapter_path)
if spec is None or spec.loader is None:
    raise ImportError(f"Failed to load module from {adapter_path}")
    
polyform_adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(polyform_adapter)
normalize_polyform = polyform_adapter.normalize_polyform

class TestPolyformAdapter(unittest.TestCase):
    
    def test_minimal_input(self):
        """Test normalization of minimal input data."""
        input_data = {
            'vertices': [(1.0, 0.0), (0.0, 1.0), (-1.0, 0.0)]
        }
        
        result = normalize_polyform(input_data)
        
        # Check required fields
        self.assertIn('id', result)
        self.assertIn('type', result)
        self.assertEqual(result['sides'], 3)
        self.assertEqual(len(result['vertices']), 3)
        self.assertEqual(len(result['position']), 3)
        self.assertIsInstance(result['bonds'], list)
        self.assertEqual(result['original_data'], input_data)
        
        # Verify 2D to 3D conversion
        for v in result['vertices']:
            self.assertEqual(len(v), 3)
            self.assertEqual(v[2], 0.0)

    def test_complete_input(self):
        """Test preservation of existing valid data."""
        input_data = {
            'id': 'test1',
            'type': 'regular',
            'sides': 4,
            'vertices': [(1,0,0), (0,1,0), (-1,0,0), (0,-1,0)],
            'position': (0,0,1),
            'bonds': [{'type': 'edge', 'target': 'test2'}],
            'extra_field': 'preserved'
        }
        
        result = normalize_polyform(input_data)
        
        # Check all fields preserved
        self.assertEqual(result['id'], 'test1')
        self.assertEqual(result['type'], 'regular')
        self.assertEqual(result['sides'], 4)
        self.assertEqual(len(result['vertices']), 4)
        self.assertEqual(result['position'], (0,0,1))
        self.assertEqual(len(result['bonds']), 1)
        self.assertEqual(result['extra_field'], 'preserved')

    def test_field_variants(self):
        """Test handling of variant field names."""
        input_data = {
            'n_sides': 5,
            'center': (1,1,1),
            'vertices': [(0,0), (1,0), (1,1), (0,1), (-1,0.5)]
        }
        
        result = normalize_polyform(input_data)
        
        self.assertEqual(result['sides'], 5)
        self.assertEqual(result['position'][:2], (1,1))
        self.assertEqual(len(result['vertices']), 5)
        for v in result['vertices']:
            self.assertEqual(len(v), 3)

    def test_computed_position(self):
        """Test position computation from vertices."""
        input_data = {
            'vertices': [(1,0,0), (-1,0,0), (0,1,0)]
        }
        
        result = normalize_polyform(input_data)
        
        # Position should be centroid (0,1/3,0)
        self.assertAlmostEqual(result['position'][0], 0)
        self.assertAlmostEqual(result['position'][1], 1/3)
        self.assertAlmostEqual(result['position'][2], 0)

if __name__ == '__main__':
    unittest.main()