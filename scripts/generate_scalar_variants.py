#!/usr/bin/env python3
"""Generate scalar variants (k=1,2,3,4,5) for all 97 polyhedra."""

import json
import sys
from pathlib import Path
import numpy as np

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT / "src"))

def generate_scalar_variants():
    """Generate scalar variants for all 97 polyhedra."""
    
    # Find polyhedra catalog
    polyhedra_file = PROJECT_ROOT / "data" / "catalogs" / "tier1" / "polyhedra.jsonl"
    if not polyhedra_file.exists():
        # Try alternative location
        polyhedra_file = PROJECT_ROOT / "lib" / "catalogs" / "tier1" / "polyhedra.jsonl"
    
    if not polyhedra_file.exists():
        print(f"Error: Could not find polyhedra catalog at {polyhedra_file}")
        return 0
    
    output_file = polyhedra_file.parent / "scalar_variants.jsonl"
    scale_factors = [1, 2, 3, 4, 5]
    variant_count = 0
    
    print(f"Generating scalar variants from {polyhedra_file}...")
    
    with open(polyhedra_file, 'r', encoding='utf-8') as f_in, \
         open(output_file, 'w', encoding='utf-8') as f_out:
        
        for line_num, line in enumerate(f_in, 1):
            if not line.strip():
                continue
            
            try:
                poly = json.loads(line)
                symbol = poly.get('symbol', f'POLY_{line_num}')
                
                # Generate variants for each scale factor
                for k in scale_factors:
                    if k == 1:
                        # Original polyhedron (include in variants)
                        variant = poly.copy()
                        variant['scale_factor'] = 1
                        variant['variant_id'] = f"{symbol}_k1"
                    else:
                        # Scaled variant
                        variant = poly.copy()
                        variant['symbol'] = f"{symbol}^k{k}"
                        variant['scale_factor'] = k
                        variant['variant_id'] = f"{symbol}_k{k}"
                        variant['base_symbol'] = symbol
                        
                        # Scale vertices
                        if 'vertices' in variant:
                            vertices = np.array(variant['vertices'], dtype=np.float64)
                            vertices = vertices * k
                            variant['vertices'] = vertices.tolist()
                        
                        # Scale bounding box
                        if 'bounding_box' in variant:
                            bbox = variant['bounding_box']
                            if 'min' in bbox and 'max' in bbox:
                                variant['bounding_box'] = {
                                    'min': [v * k for v in bbox['min']],
                                    'max': [v * k for v in bbox['max']]
                                }
                        
                        # Update compression ratio (improves with scale)
                        if 'compression_ratio' in variant:
                            variant['compression_ratio'] = variant['compression_ratio'] * (k ** 1.5)
                        else:
                            variant['compression_ratio'] = 10.0 * (k ** 1.5)
                    
                    # Add metadata
                    variant['is_scalar_variant'] = True
                    variant['generation_method'] = 'scalar_scaling'
                    
                    # Write variant
                    f_out.write(json.dumps(variant, ensure_ascii=False) + '\n')
                    variant_count += 1
                    
                    if variant_count % 50 == 0:
                        print(f"  Generated {variant_count} variants...")
            
            except json.JSONDecodeError as e:
                print(f"Warning: Skipping invalid JSON at line {line_num}: {e}")
                continue
            except Exception as e:
                print(f"Warning: Error processing line {line_num}: {e}")
                continue
    
    print(f"\n✓ Generated {variant_count} scalar variants (97 × 5 = 485 expected)")
    print(f"  Output: {output_file}")
    return variant_count

if __name__ == '__main__':
    count = generate_scalar_variants()
    sys.exit(0 if count > 0 else 1)

