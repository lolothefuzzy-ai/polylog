"""
Phase 2 GUI Integration Test

Quick test to verify polygon generation and rendering integration.
Run this to test the GUI without launching it visually.
"""

import sys
import traceback
from typing import List


def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")
    try:
        from PySide6.QtWidgets import QApplication
        from gui.main_window import MainWindow
        from gui.viewport import Viewport3D
        from gui.panels.controls_panel import ControlsPanel
        from gui.panels.library_panel import LibraryPanel
        from gui.utils import (
            gui_params_to_generator_params,
            extract_vertices_3d,
            get_polygon_color,
            format_polygon_for_display,
        )
        from random_assembly_generator import RandomAssemblyGenerator
        print("✓ All imports successful")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        traceback.print_exc()
        return False


def test_polygon_generation():
    """Test polygon generation."""
    print("\nTesting polygon generation...")
    try:
        from random_assembly_generator import RandomAssemblyGenerator
        
        generator = RandomAssemblyGenerator()
        polygon = generator.generate_random_assembly(
            num_polyforms=1,
            allow_types=[6],
            use_3d=True
        )[0]
        
        assert polygon is not None, "Polygon is None"
        assert 'sides' in polygon, "Missing 'sides' key"
        assert 'vertices' in polygon, "Missing 'vertices' key"
        assert polygon['sides'] == 6, f"Expected 6 sides, got {polygon['sides']}"
        
        print(f"✓ Polygon generated: {polygon['sides']}-sided shape")
        print(f"  Vertices: {len(polygon['vertices'])}")
        print(f"  Position: {polygon.get('position')}")
        return polygon
    except Exception as e:
        print(f"✗ Polygon generation failed: {e}")
        traceback.print_exc()
        return None


def test_polygon_formatting(polygon):
    """Test polygon formatting for display."""
    print("\nTesting polygon formatting...")
    try:
        from gui.utils import format_polygon_for_display
        
        formatted = format_polygon_for_display(polygon)
        
        assert formatted is not None, "Formatted polygon is None"
        assert 'vertices' in formatted, "Missing vertices in formatted polygon"
        assert 'mesh' in formatted, "Missing mesh in formatted polygon"
        assert formatted['sides'] == polygon['sides'], "Sides mismatch"
        
        print(f"✓ Polygon formatted successfully")
        print(f"  Formatted vertices: {len(formatted['vertices'])}")
        print(f"  Mesh faces: {formatted['mesh']['face_count']}")
        return formatted
    except Exception as e:
        print(f"✗ Polygon formatting failed: {e}")
        traceback.print_exc()
        return None


def test_parameter_conversion():
    """Test GUI parameter to generator parameter conversion."""
    print("\nTesting parameter conversion...")
    try:
        from gui.utils import gui_params_to_generator_params
        
        params = gui_params_to_generator_params(sides=8, complexity=0.75, symmetry=0.5)
        
        assert params['sides'] == 8, "Sides not converted correctly"
        assert 0 <= params['complexity'] <= 1.0, "Complexity out of range"
        assert 0 <= params['symmetry'] <= 1.0, "Symmetry out of range"
        assert 'scale' in params, "Missing scale in params"
        assert 'is_regular' in params, "Missing is_regular in params"
        
        print(f"✓ Parameters converted successfully")
        print(f"  Sides: {params['sides']}")
        print(f"  Complexity: {params['complexity']}")
        print(f"  Symmetry: {params['symmetry']}")
        print(f"  Scale: {params['scale']}")
        return params
    except Exception as e:
        print(f"✗ Parameter conversion failed: {e}")
        traceback.print_exc()
        return None


def test_color_assignment():
    """Test polygon color assignment."""
    print("\nTesting color assignment...")
    try:
        from gui.utils import get_polygon_color
        
        colors = []
        for i in range(8):
            color = get_polygon_color(i)
            assert len(color) == 3, f"Color should have 3 components, got {len(color)}"
            assert all(0.0 <= c <= 1.0 for c in color), f"Color values out of range: {color}"
            colors.append(color)
        
        # Verify colors are different
        unique_colors = set(colors[:4])
        assert len(unique_colors) > 1, "Colors should vary"
        
        print(f"✓ Color assignment working")
        print(f"  Generated {len(unique_colors)} unique colors")
        for i, color in enumerate(unique_colors):
            print(f"  Color {i}: {tuple(f'{c:.2f}' for c in color)}")
        return True
    except Exception as e:
        print(f"✗ Color assignment failed: {e}")
        traceback.print_exc()
        return False


def test_multiple_polygons():
    """Test generating multiple polygons."""
    print("\nTesting multiple polygon generation...")
    try:
        from random_assembly_generator import RandomAssemblyGenerator
        from gui.utils import format_polygon_for_display
        
        generator = RandomAssemblyGenerator()
        polygons = []
        
        for sides in [3, 4, 5, 6]:
            polygon = generator.generate_random_assembly(
                num_polyforms=1,
                allow_types=[sides],
                use_3d=True
            )[0]
            formatted = format_polygon_for_display(polygon)
            polygons.append(formatted)
        
        assert len(polygons) == 4, "Should have 4 polygons"
        
        print(f"✓ Generated {len(polygons)} polygons")
        for i, poly in enumerate(polygons):
            print(f"  Polygon {i}: {poly['sides']}-sided")
        return polygons
    except Exception as e:
        print(f"✗ Multiple polygon generation failed: {e}")
        traceback.print_exc()
        return None


def test_mesh_generation():
    """Test mesh generation for rendering."""
    print("\nTesting mesh generation...")
    try:
        from gui.utils import create_polygon_mesh
        
        vertices = [
            (1.0, 0.0, 0.0),
            (0.5, 0.866, 0.0),
            (-0.5, 0.866, 0.0),
            (-1.0, 0.0, 0.0),
            (-0.5, -0.866, 0.0),
            (0.5, -0.866, 0.0),
        ]
        
        mesh = create_polygon_mesh(vertices)
        
        assert 'vertices' in mesh, "Missing vertices in mesh"
        assert 'faces' in mesh, "Missing faces in mesh"
        assert len(mesh['vertices']) == 6, "Should have 6 vertices"
        assert mesh['face_count'] == 4, f"Should have 4 faces, got {mesh['face_count']}"
        
        print(f"✓ Mesh generated successfully")
        print(f"  Vertices: {len(mesh['vertices'])}")
        print(f"  Faces: {len(mesh['faces'])}")
        return mesh
    except Exception as e:
        print(f"✗ Mesh generation failed: {e}")
        traceback.print_exc()
        return None


def main():
    """Run all tests."""
    print("=" * 60)
    print("Phase 2 GUI Integration Test Suite")
    print("=" * 60)
    
    results = {
        'imports': test_imports(),
    }
    
    if not results['imports']:
        print("\n" + "=" * 60)
        print("Cannot continue - imports failed")
        print("=" * 60)
        return False
    
    polygon = test_polygon_generation()
    results['generation'] = polygon is not None
    
    if polygon:
        formatted = test_polygon_formatting(polygon)
        results['formatting'] = formatted is not None
    
    results['parameters'] = test_parameter_conversion() is not None
    results['colors'] = test_color_assignment()
    
    polygons = test_multiple_polygons()
    results['multiple'] = polygons is not None
    
    results['mesh'] = test_mesh_generation() is not None
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    print()
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print("=" * 60)
    
    if passed == total:
        print("\n🎉 All tests passed! Phase 2 integration is working.")
        return True
    else:
        print(f"\n❌ {total - passed} test(s) failed.")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
