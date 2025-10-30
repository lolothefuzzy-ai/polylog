#!/usr/bin/env python3
"""
Quick test of PolygonRangeSlider module for syntax and import validation.
"""

import sys

def test_imports():
    """Test that all imports work."""
    try:
        print("Testing imports...")
        from polygon_range_slider import (
            PolygonRangeSliderWidget,
            PolygonGenerationAnimator,
            integrate_polygon_range_slider_into_gui
        )
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_module_contents():
    """Test that module has expected classes."""
    try:
        print("\nTesting module contents...")
        from polygon_range_slider import PolygonRangeSliderWidget
        
        # Check class has expected methods
        widget = PolygonRangeSliderWidget()
        assert hasattr(widget, 'on_generate'), "Missing on_generate method"
        assert hasattr(widget, 'set_generation_progress'), "Missing set_generation_progress"
        assert hasattr(widget, 'generation_started'), "Missing generation_started signal"
        
        print("✓ PolygonRangeSliderWidget has all expected methods")
        return True
    except Exception as e:
        print(f"✗ Module content test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_animator_class():
    """Test animator class structure."""
    try:
        print("\nTesting PolygonGenerationAnimator...")
        from polygon_range_slider import PolygonGenerationAnimator
        
        # Check that class exists and has methods
        assert hasattr(PolygonGenerationAnimator, 'animate_polygon_generation')
        assert hasattr(PolygonGenerationAnimator, '__init__')
        
        print("✓ PolygonGenerationAnimator structure is valid")
        return True
    except Exception as e:
        print(f"✗ Animator test failed: {e}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("Polygon Range Slider Module Tests")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_module_contents,
        test_animator_class,
    ]
    
    results = [test() for test in tests]
    
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)
    
    sys.exit(0 if all(results) else 1)
