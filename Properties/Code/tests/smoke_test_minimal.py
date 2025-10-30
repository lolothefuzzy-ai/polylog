"""
Small smoke test for polyform generation functionality.
"""

import sys
from random_polyform_generator import (
    RandomPolyformGenerator, 
    GenerationParams, 
    DistributionMode, 
    ShapeVariety
)

def test_basic_polyform():
    """Test simple polyform generation."""
    print("\nTesting basic polyform generation...")
    
    params = GenerationParams(
        n=2,
        distribution=DistributionMode.UNIFORM,
        shape_variety=ShapeVariety.REGULAR_ONLY
    )
    
    generator = RandomPolyformGenerator(params=params)
    polyforms = generator.generate()
    
    print(f"Generated {len(polyforms)} polyforms")
    if len(polyforms) != 2:
        print("❌ Failed: Wrong number of polyforms")
        return False
    
    print("✓ Basic generation passed")
    return True

if __name__ == '__main__':
    print("Running minimal polyform smoke test...")
    success = test_basic_polyform()
    sys.exit(0 if success else 1)