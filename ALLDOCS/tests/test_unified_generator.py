"""
Integration test for unified generator system.

Tests the new BaseGenerator protocol, registry system, and UnifiedGenerator.
"""
import sys
sys.path.insert(0, '..')

from generator_protocol import get_generator_registry, GeneratorCapability


def test_registry():
    """Test generator registry functionality."""
    print("Testing Generator Registry...")
    
    registry = get_generator_registry()
    
    # List registered generators
    generators = registry.list_generators()
    print(f"  Registered generators: {generators}")
    
    # Check if basic generator is registered
    if 'basic' in generators:
        print("  ✓ Basic generator registered")
        caps = registry.get_capabilities('basic')
        print(f"    Capabilities: {caps}")
    
    # Find generators by capability
    basic_gens = registry.find_by_capability(GeneratorCapability.BASIC)
    print(f"  Generators with BASIC capability: {basic_gens}")
    
    print()


def test_base_generator():
    """Test BaseGenerator functionality."""
    print("Testing BaseGenerator Protocol...")
    
    # Try to import and instantiate
    try:
        from polyform_generation_engine import PolyformGenerationEngine
        
        # Create minimal assembly mock
        class MockAssembly:
            def __init__(self):
                self.polyforms = []
            
            def add_polyform(self, poly):
                self.polyforms.append(poly)
            
            def get_all_polyforms(self):
                return self.polyforms
        
        assembly = MockAssembly()
        gen = PolyformGenerationEngine(assembly, enable_3d_mode=True)
        
        # Test interface methods
        print("  ✓ Generator instantiated")
        print(f"  3D mode enabled: {gen.is_3d_mode()}")
        
        # Get stats
        stats = gen.get_stats()
        print(f"  Stats: {stats}")
        
        # Test 3D mode toggle
        gen.set_3d_mode(False)
        print(f"  3D mode after toggle: {gen.is_3d_mode()}")
        
        print()
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        print()


def test_unified_generator():
    """Test UnifiedGenerator with registry integration."""
    print("Testing UnifiedGenerator...")
    
    try:
        from unified_generator import UnifiedGenerator
        
        # Create minimal assembly mock
        class MockAssembly:
            def __init__(self):
                self.polyforms = []
            
            def add_polyform(self, poly):
                self.polyforms.append(poly)
            
            def get_all_polyforms(self):
                return self.polyforms
        
        assembly = MockAssembly()
        unified = UnifiedGenerator(assembly, enable_3d_mode=True)
        
        print("  ✓ UnifiedGenerator instantiated")
        print(f"  Available generators: {list(unified.generators.keys())}")
        
        # Test registry queries
        registered = unified.list_registered_generators()
        print(f"  Registered in global registry: {registered}")
        
        # Test capability search
        basic_gens = unified.find_generators_by_capability(GeneratorCapability.BASIC)
        print(f"  Generators with BASIC capability: {basic_gens}")
        
        # Test stats collection
        all_stats = unified.get_all_generator_stats()
        print(f"  Collected stats from {len(all_stats)} generators")
        
        # Test 3D mode control
        unified.set_3d_mode_all(False)
        print(f"  ✓ 3D mode toggled for all generators")
        
        print()
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        print()


def test_generator_generation():
    """Test actual generation with PolyformGenerationEngine."""
    print("Testing Generation...")
    
    try:
        from polyform_generation_engine import PolyformGenerationEngine
        
        # Create minimal assembly mock
        class MockAssembly:
            def __init__(self):
                self.polyforms = []
                self.next_id = 1
            
            def add_polyform(self, poly):
                if 'id' not in poly:
                    poly['id'] = f'poly_{self.next_id}'
                    self.next_id += 1
                self.polyforms.append(poly)
            
            def get_all_polyforms(self):
                return self.polyforms
        
        assembly = MockAssembly()
        gen = PolyformGenerationEngine(assembly, enable_3d_mode=False)  # 2D for simplicity
        
        # Test single generation
        poly_ids = gen.generate(method='single', sides=6)
        print(f"  ✓ Generated single polygon: {poly_ids}")
        
        # Check stats
        stats = gen.get_stats()
        print(f"  Stats after generation: {stats}")
        
        print()
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        print()


if __name__ == "__main__":
    print("=" * 60)
    print("Unified Generator System Integration Tests")
    print("=" * 60)
    print()
    
    test_registry()
    test_base_generator()
    test_unified_generator()
    test_generator_generation()
    
    print("=" * 60)
    print("Tests Complete!")
    print("=" * 60)
