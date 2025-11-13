"""Quick smoke test for polyform generation."""
import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)

# Add Code directory to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / 'Code'))

from random_polyform_generator import DistributionMode, GenerationParams, RandomPolyformGenerator, ShapeVariety


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
        
        return True
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)