"""
Test script for PolyformGenerationEngine.
Tests single polygon generation, range generation, and 3D tracking.
"""
import sys
from typing import Dict, Any

# Mock Assembly class for testing
class TestAssembly:
    def __init__(self):
        self.polyforms = {}
        self.bonds = []
        self._next_id = 1
    
    def add_polyform(self, p: Dict[str, Any]):
        try:
            from gui.polyform_adapter import normalize_polyform
            norm = normalize_polyform(p)
        except Exception:
            norm = dict(p)
            if 'id' not in norm:
                norm['id'] = f"poly_{self._next_id}"
                self._next_id += 1
            verts = []
            for v in norm.get('vertices', []):
                if isinstance(v, (list, tuple)):
                    if len(v) == 2:
                        verts.append((float(v[0]), float(v[1]), 0.0))
                    else:
                        verts.append((float(v[0]), float(v[1]), float(v[2]) if len(v) > 2 else 0.0))
            if verts:
                norm['vertices'] = verts
        self.polyforms[norm['id']] = norm
        print(f"  Added polyform: {norm['id']} ({norm.get('sides', 0)} sides)")
    
    def get_polyform(self, pid: str):
        return self.polyforms.get(pid)
    
    def get_all_polyforms(self):
        return list(self.polyforms.values())
    
    def get_bonds(self):
        return list(self.bonds)


def test_single_polygon_generation():
    """Test single polygon generation with 3D tracking."""
    print("\n" + "="*60)
    print("TEST 1: Single Polygon Generation")
    print("="*60)
    
    from polyform_generation_engine import PolyformGenerationEngine
    
    assembly = TestAssembly()
    engine = PolyformGenerationEngine(assembly, enable_3d_mode=True)
    
    # Test generating polygons with different sides
    for sides in [3, 4, 5, 6]:
        print(f"\nGenerating {sides}-sided polygon...")
        poly_id = engine.generate_single(sides, position=(sides * 2.0, 0, 0))
        poly = assembly.get_polyform(poly_id)
        
        # Verify polygon properties
        assert poly is not None, f"Polygon {poly_id} not found"
        assert len(poly['vertices']) == sides, f"Wrong number of vertices"
        assert poly.get('has_3d_mesh') == True, "3D mesh not created"
        assert 'mesh' in poly, "Mesh data missing"
        print(f"  ✓ Polygon {poly_id} created successfully")
        print(f"    - Vertices: {len(poly['vertices'])}")
        print(f"    - Has 3D mesh: {poly.get('has_3d_mesh')}")
        print(f"    - Position: {poly['position']}")
    
    stats = engine.get_statistics()
    print(f"\nGeneration statistics:")
    print(f"  Total generated: {stats['total_generated']}")
    
    print("\n✓ Test 1 PASSED")
    return True


def test_range_generation():
    """Test range generation with different layouts."""
    print("\n" + "="*60)
    print("TEST 2: Range Generation")
    print("="*60)
    
    from polyform_generation_engine import PolyformGenerationEngine
    
    assembly = TestAssembly()
    engine = PolyformGenerationEngine(assembly, enable_3d_mode=True)
    
    # Test circular layout
    print("\nGenerating range (3-6 sides) with circular layout...")
    poly_ids = engine.generate_range(3, 6, layout='circular', spacing=5.0)
    
    assert len(poly_ids) == 4, "Wrong number of polygons generated"
    print(f"  ✓ Generated {len(poly_ids)} polygons: {poly_ids}")
    
    # Verify all have 3D meshes
    for poly_id in poly_ids:
        poly = assembly.get_polyform(poly_id)
        assert poly.get('has_3d_mesh') == True, f"Polygon {poly_id} missing 3D mesh"
        print(f"  ✓ {poly_id}: {poly['sides']} sides, 3D mesh: ✓")
    
    # Test linear layout
    assembly2 = TestAssembly()
    engine2 = PolyformGenerationEngine(assembly2, enable_3d_mode=True)
    
    print("\nGenerating range (5-8 sides) with linear layout...")
    poly_ids2 = engine2.generate_range(5, 8, layout='linear', spacing=3.0)
    
    assert len(poly_ids2) == 4, "Wrong number of polygons generated"
    print(f"  ✓ Generated {len(poly_ids2)} polygons: {poly_ids2}")
    
    # Test grid layout
    assembly3 = TestAssembly()
    engine3 = PolyformGenerationEngine(assembly3, enable_3d_mode=True)
    
    print("\nGenerating range (3-8 sides) with grid layout...")
    poly_ids3 = engine3.generate_range(3, 8, layout='grid', spacing=2.5)
    
    assert len(poly_ids3) == 6, "Wrong number of polygons generated"
    print(f"  ✓ Generated {len(poly_ids3)} polygons: {poly_ids3}")
    
    print("\n✓ Test 2 PASSED")
    return True


def test_template_generation():
    """Test template generation."""
    print("\n" + "="*60)
    print("TEST 3: Template Generation")
    print("="*60)
    
    from polyform_generation_engine import PolyformGenerationEngine
    from template_library import TemplateLibrary
    
    assembly = TestAssembly()
    engine = PolyformGenerationEngine(assembly, enable_3d_mode=True)
    
    # List available templates
    templates = TemplateLibrary.list_all()
    print(f"\nAvailable templates: {len(templates)}")
    for template in templates:
        print(f"  - {template['id']}: {template['name']}")
    
    # Test cube net generation
    print("\nGenerating cube net template...")
    poly_ids = engine.generate_from_template('cube_net', position=(0, 0, 0))
    
    print(f"  ✓ Generated {len(poly_ids)} polygons from cube_net template")
    assert len(poly_ids) == 6, "Cube net should have 6 squares"
    
    # Verify all are squares with 3D meshes
    for poly_id in poly_ids:
        poly = assembly.get_polyform(poly_id)
        assert poly['sides'] == 4, f"Cube net should only have squares"
        assert poly.get('has_3d_mesh') == True, f"Polygon {poly_id} missing 3D mesh"
        print(f"  ✓ {poly_id}: Square with 3D mesh")
    
    # Test tetrahedron net
    assembly2 = TestAssembly()
    engine2 = PolyformGenerationEngine(assembly2, enable_3d_mode=True)
    
    print("\nGenerating tetrahedron net template...")
    poly_ids2 = engine2.generate_from_template('tetrahedron_net', position=(5, 0, 0))
    
    print(f"  ✓ Generated {len(poly_ids2)} polygons from tetrahedron_net template")
    assert len(poly_ids2) == 4, "Tetrahedron net should have 4 triangles"
    
    print("\n✓ Test 3 PASSED")
    return True


def test_3d_mode_toggle():
    """Test 3D mode on/off."""
    print("\n" + "="*60)
    print("TEST 4: 3D Mode Toggle")
    print("="*60)
    
    from polyform_generation_engine import PolyformGenerationEngine
    
    # Test with 3D mode OFF
    print("\nGenerating polygons with 3D mode OFF...")
    assembly = TestAssembly()
    engine = PolyformGenerationEngine(assembly, enable_3d_mode=False)
    
    poly_id = engine.generate_single(5, position=(0, 0, 0))
    poly = assembly.get_polyform(poly_id)
    
    assert poly.get('has_3d_mesh') != True, "3D mesh should not be created when 3D mode is off"
    print(f"  ✓ Polygon created without 3D mesh (as expected)")
    
    # Test with 3D mode ON
    print("\nGenerating polygons with 3D mode ON...")
    assembly2 = TestAssembly()
    engine2 = PolyformGenerationEngine(assembly2, enable_3d_mode=True)
    
    poly_id2 = engine2.generate_single(5, position=(0, 0, 0))
    poly2 = assembly2.get_polyform(poly_id2)
    
    assert poly2.get('has_3d_mesh') == True, "3D mesh should be created when 3D mode is on"
    print(f"  ✓ Polygon created with 3D mesh (as expected)")
    
    print("\n✓ Test 4 PASSED")
    return True


def test_learning_integration():
    """Test learning engine integration."""
    print("\n" + "="*60)
    print("TEST 5: Learning Engine Integration")
    print("="*60)
    
    from polyform_generation_engine import PolyformGenerationEngine
    
    assembly = TestAssembly()
    engine = PolyformGenerationEngine(assembly, enable_3d_mode=True)
    
    print("\nGenerating polygons to train learning engine...")
    for i in range(5):
        poly_id = engine.generate_single(4, position=(i * 3.0, 0, 0))
        print(f"  Generated: {poly_id}")
    
    # Check that learning engine observed creations
    assert len(engine.learning_engine.recent_creations) > 0, "Learning engine should have observations"
    print(f"  ✓ Learning engine recorded {len(engine.learning_engine.recent_creations)} observations")
    
    # Check scaler database
    scaler = engine.scaler_db.get_optimal_scaler(4)
    print(f"  ✓ Learned scaler for squares: {scaler:.3f}")
    
    print("\n✓ Test 5 PASSED")
    return True


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*60)
    print("POLYFORM GENERATION ENGINE TEST SUITE")
    print("="*60)
    
    tests = [
        ("Single Polygon Generation", test_single_polygon_generation),
        ("Range Generation", test_range_generation),
        ("Template Generation", test_template_generation),
        ("3D Mode Toggle", test_3d_mode_toggle),
        ("Learning Integration", test_learning_integration),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"\n✗ Test FAILED: {test_name}")
            print(f"  Error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n✓ ALL TESTS PASSED!")
    else:
        print(f"\n✗ {failed} test(s) failed")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
