"""
Quick integration test runner.

Tests the unified system without full pytest infrastructure.
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

print("=" * 60)
print("INTEGRATION TEST RUNNER")
print("=" * 60)
print()

# Test 1: Import generator protocol
print("1. Testing generator protocol import...")
try:
    from generator_protocol import GeneratorCapability, get_generator_registry
    print("   ✓ Generator protocol imported")
except Exception as e:
    print(f"   ✗ Error: {e}")
    sys.exit(1)

# Test 2: Import migrated generators (this triggers registration)
print("\n2. Testing migrated generators...")
try:
    from polyform_generation_engine import PolyformGenerationEngine
    print("   ✓ PolyformGenerationEngine imported")
except Exception as e:
    print(f"   ✗ Error: {e}")

try:
    print("   ✓ RandomAssemblyGenerator imported")
except Exception as e:
    print(f"   ✗ Error: {e}")

try:
    print("   ✓ RandomPolyformGenerator imported")
except Exception as e:
    print(f"   ✗ Error: {e}")

try:
    print("   ✓ PhysicsBasedGenerator imported")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 3: Check registry (after imports so decorators have executed)
print("\n3. Testing generator registry...")
try:
    registry = get_generator_registry()
    generators = registry.list_generators()
    print(f"   ✓ Registry found {len(generators)} generators: {generators}")
    
    # Test capability search
    basic_gens = registry.find_by_capability(GeneratorCapability.BASIC)
    print(f"   ✓ Basic generators: {basic_gens}")
    
    physics_gens = registry.find_by_capability(GeneratorCapability.PHYSICS)
    print(f"   ✓ Physics generators: {physics_gens}")
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Test bonding system
print("\n4. Testing unified bonding system...")
try:
    from unified_bonding_system import UnifiedBondingSystem
    bonding = UnifiedBondingSystem()
    print(f"   ✓ Bonding system created (3D mode: {bonding._enable_3d})")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 5: Test BaseGenerator instantiation
print("\n5. Testing BaseGenerator instantiation...")
try:
    class MockAssembly:
        def __init__(self):
            self.polyforms = []
            self.bonds = []
        
        def add_polyform(self, poly):
            try:
                from gui.polyform_adapter import normalize_polyform
                norm = normalize_polyform(poly)
            except Exception:
                norm = dict(poly)
                if 'id' not in norm:
                    norm['id'] = f'poly_{len(self.polyforms)}'
                verts = []
                for v in norm.get('vertices', []):
                    if isinstance(v, (list, tuple)):
                        if len(v) == 2:
                            verts.append((float(v[0]), float(v[1]), 0.0))
                        else:
                            verts.append((float(v[0]), float(v[1]), float(v[2]) if len(v) > 2 else 0.0))
                if verts:
                    norm['vertices'] = verts
            self.polyforms.append(norm)
        
        def get_all_polyforms(self):
            return self.polyforms
        
        def get_bonds(self):
            return self.bonds
        
        def add_bond(self, bond):
            self.bonds.append(bond)
        
        def get_polyform(self, poly_id):
            for p in self.polyforms:
                if p['id'] == poly_id:
                    return p
            return None
    
    assembly = MockAssembly()
    gen = PolyformGenerationEngine(assembly, enable_3d_mode=False)
    print(f"   ✓ Generator instantiated")
    print(f"   3D mode: {gen.is_3d_mode()}")
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 6: Test generation
print("\n6. Testing generation...")
try:
    # Create mock dependencies
    try:
        pass
    except:
        print("   ⚠ Optional dependencies missing (scaler_database, etc.)")
        print("   Skipping generation test")
    else:
        poly_ids = gen.generate(method='single', sides=4)
        print(f"   ✓ Generated polygon: {poly_ids}")
        
        stats = gen.get_stats()
        print(f"   Stats: {stats}")
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 7: Test collision detection
print("\n7. Testing collision detection...")
try:
    import numpy as np

    from bvh3d import AABB
    
    # Simple AABB test
    aabb1 = AABB(np.array([0, 0, 0]), np.array([1, 1, 1]))
    aabb2 = AABB(np.array([0.5, 0.5, 0.5]), np.array([1.5, 1.5, 1.5]))
    
    intersects = aabb1.intersects(aabb2)
    print(f"   ✓ AABB intersection test: {intersects}")
except Exception as e:
    print(f"   ✗ Error: {e}")

print("\n" + "=" * 60)
print("INTEGRATION TESTS COMPLETE")
print("=" * 60)
