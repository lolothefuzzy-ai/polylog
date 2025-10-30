"""
Smoke test for polyform generation and loading.
Verifies that core polyform functionality works after cleanup.
"""

import sys
from pathlib import Path

from random_polyform_generator import (
    RandomPolyformGenerator, 
    GenerationParams, 
    DistributionMode, 
    ShapeVariety
)

def test_basic_generation():
    """Test basic polyform generation."""
    print("\nTesting basic polyform generation...")
    
    params = GenerationParams(
        n=10,
        distribution=DistributionMode.UNIFORM,
        shape_variety=ShapeVariety.REGULAR_ONLY,
        bounds_x=(-10, 10),
        bounds_y=(-10, 10),
        bounds_z=(-2, 2)
    )
    
    generator = RandomPolyformGenerator(params=params)
    polyforms = generator.generate_batch()
    
    print(f"Generated {len(polyforms)} polyforms")
    if len(polyforms) != 10:
        print("❌ Failed: Wrong number of polyforms generated")
        return False
        
    for i, poly in enumerate(polyforms):
        if not all(key in poly for key in ['id', 'vertices', 'position', 'bonds']):
            print(f"❌ Failed: Polyform {i} missing required fields")
            return False
    
    print("✓ Basic generation test passed")
    return True

def test_all_shape_varieties():
    """Test generation of all shape varieties."""
    print("\nTesting all shape varieties...")
    
    for variety in ShapeVariety:
        print(f"\nTesting {variety.value}...")
        params = GenerationParams(
            n=5,
            shape_variety=variety
        )
        generator = RandomPolyformGenerator(params=params)
        polyforms = generator.generate_batch()
        
        if len(polyforms) != 5:
            print(f"❌ Failed: {variety.value} generation failed")
            return False
        
        # Verify shape-specific properties
        for poly in polyforms:
            if not poly.get('shape_variety') == variety.value:
                print(f"❌ Failed: Wrong shape variety for {variety.value}")
                return False
    
    print("✓ All shape varieties test passed")
    return True

def run_smoke_tests():
    """Run all smoke tests."""
    print("Running polyform smoke tests...")
    
    tests = [
        test_basic_generation,
        test_all_shape_varieties
    ]
    
    failed = False
    for test in tests:
        if not test():
            failed = True
            
    if failed:
        print("\n❌ Some tests failed!")
        return False
    else:
        print("\n✓ All smoke tests passed!")
        return True

if __name__ == '__main__':
    success = run_smoke_tests()
    sys.exit(0 if success else 1)