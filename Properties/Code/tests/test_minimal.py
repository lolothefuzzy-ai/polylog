"""Quick smoke test for polyform generation."""
import sys
from pathlib import Path

from minimal_generator import (
    RandomPolyformGenerator, 
    GenerationParams, 
    DistributionMode, 
    ShapeVariety
)

def main():
    """Run basic polyform generation test."""
    print("Testing polyform generation...")
    
    params = GenerationParams(
        n=2,  # Small number for testing
        distribution=DistributionMode.UNIFORM,
        shape_variety=ShapeVariety.REGULAR_ONLY,
        bounds_x=(-10, 10),
        bounds_y=(-10, 10),
        bounds_z=(-2, 2)
    )
    
    try:
        generator = RandomPolyformGenerator(params=params)
        print("\nGenerating polyforms...")
        polyforms = generator.generate_batch()
        
        print(f"\nSuccess! Generated {len(polyforms)} polyforms")
        print("\nSample polyform structure:")
        if polyforms:
            for key, value in polyforms[0].items():
                if isinstance(value, list):
                    print(f"{key}: [{len(value)} items]")
                else:
                    print(f"{key}: {value}")
        
        stats = generator.get_statistics()
        print("\nGeneration statistics:")
        for key, value in stats.items():
            print(f"{key}: {value}")
        
        return True
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)