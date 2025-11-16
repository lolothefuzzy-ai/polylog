#!/usr/bin/env python3
"""Generate ~750 common attachment patterns (linear, triangular, hexagonal, cubic, tetrahedral)."""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any
import itertools

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT / "src"))

def generate_linear_patterns(polygon_symbols: List[str], max_length: int = 10) -> List[Dict[str, Any]]:
    """Generate linear chain patterns."""
    patterns = []
    
    for length in range(2, max_length + 1):
        # All same polygon
        for symbol in polygon_symbols[:20]:  # Limit to first 20 for performance
            pattern = {
                'pattern_type': 'linear',
                'pattern_id': f"LINEAR_{symbol}_{length}",
                'length': length,
                'composition': symbol * length,
                'polygons': [symbol] * length,
                'attachment_sequence': [
                    {'from': i, 'to': i+1, 'edge_a': 0, 'edge_b': 0}
                    for i in range(length - 1)
                ],
                'metadata': {
                    'open_edges': 2,  # Two ends
                    'closure_type': 'open_chain'
                }
            }
            patterns.append(pattern)
    
    return patterns

def generate_triangular_patterns(polygon_symbols: List[str]) -> List[Dict[str, Any]]:
    """Generate triangular (3-way junction) patterns."""
    patterns = []
    
    # All same polygon triangles
    for symbol in polygon_symbols[:15]:
        pattern = {
            'pattern_type': 'triangular',
            'pattern_id': f"TRIANGLE_{symbol}",
            'composition': symbol * 3,
            'polygons': [symbol] * 3,
            'attachment_sequence': [
                {'from': 0, 'to': 1, 'edge_a': 0, 'edge_b': 0},
                {'from': 1, 'to': 2, 'edge_a': 1, 'edge_b': 0},
                {'from': 2, 'to': 0, 'edge_a': 1, 'edge_b': 1}
            ],
            'metadata': {
                'open_edges': 3,  # Three outer edges
                'closure_type': 'partial_triangle'
            }
        }
        patterns.append(pattern)
    
    # Mixed polygon triangles
    for combo in itertools.combinations(polygon_symbols[:10], 3):
        pattern = {
            'pattern_type': 'triangular',
            'pattern_id': f"TRIANGLE_MIXED_{''.join(combo)}",
            'composition': ''.join(combo),
            'polygons': list(combo),
            'attachment_sequence': [
                {'from': 0, 'to': 1, 'edge_a': 0, 'edge_b': 0},
                {'from': 1, 'to': 2, 'edge_a': 1, 'edge_b': 0},
                {'from': 2, 'to': 0, 'edge_a': 1, 'edge_b': 1}
            ],
            'metadata': {
                'open_edges': 3,
                'closure_type': 'partial_triangle'
            }
        }
        patterns.append(pattern)
    
    return patterns

def generate_hexagonal_patterns(polygon_symbols: List[str]) -> List[Dict[str, Any]]:
    """Generate hexagonal (6-way junction) patterns."""
    patterns = []
    
    for symbol in polygon_symbols[:12]:
        pattern = {
            'pattern_type': 'hexagonal',
            'pattern_id': f"HEXAGON_{symbol}",
            'composition': symbol * 6,
            'polygons': [symbol] * 6,
            'attachment_sequence': [
                {'from': i, 'to': (i+1) % 6, 'edge_a': 0, 'edge_b': 0}
                for i in range(6)
            ],
            'metadata': {
                'open_edges': 6,  # Six outer edges
                'closure_type': 'hexagonal_ring'
            }
        }
        patterns.append(pattern)
    
    return patterns

def generate_cubic_patterns(polygon_symbols: List[str]) -> List[Dict[str, Any]]:
    """Generate cubic (8-way junction) patterns."""
    patterns = []
    
    # Cube face pattern (8 polygons forming cube)
    for symbol in polygon_symbols[:10]:
        pattern = {
            'pattern_type': 'cubic',
            'pattern_id': f"CUBE_{symbol}",
            'composition': symbol * 8,
            'polygons': [symbol] * 8,
            'attachment_sequence': [
                # Top face (4 polygons)
                {'from': 0, 'to': 1, 'edge_a': 0, 'edge_b': 0},
                {'from': 1, 'to': 2, 'edge_a': 1, 'edge_b': 0},
                {'from': 2, 'to': 3, 'edge_a': 1, 'edge_b': 0},
                {'from': 3, 'to': 0, 'edge_a': 1, 'edge_b': 1},
                # Bottom face (4 polygons)
                {'from': 4, 'to': 5, 'edge_a': 0, 'edge_b': 0},
                {'from': 5, 'to': 6, 'edge_a': 1, 'edge_b': 0},
                {'from': 6, 'to': 7, 'edge_a': 1, 'edge_b': 0},
                {'from': 7, 'to': 4, 'edge_a': 1, 'edge_b': 1},
                # Connect top to bottom
                {'from': 0, 'to': 4, 'edge_a': 2, 'edge_b': 2},
                {'from': 1, 'to': 5, 'edge_a': 2, 'edge_b': 2},
                {'from': 2, 'to': 6, 'edge_a': 2, 'edge_b': 2},
                {'from': 3, 'to': 7, 'edge_a': 2, 'edge_b': 2}
            ],
            'metadata': {
                'open_edges': 0,  # Closed cube
                'closure_type': 'cubic_closed'
            }
        }
        patterns.append(pattern)
    
    return patterns

def generate_tetrahedral_patterns(polygon_symbols: List[str]) -> List[Dict[str, Any]]:
    """Generate tetrahedral (4-way junction) patterns."""
    patterns = []
    
    for symbol in polygon_symbols[:15]:
        pattern = {
            'pattern_type': 'tetrahedral',
            'pattern_id': f"TETRA_{symbol}",
            'composition': symbol * 4,
            'polygons': [symbol] * 4,
            'attachment_sequence': [
                {'from': 0, 'to': 1, 'edge_a': 0, 'edge_b': 0},
                {'from': 0, 'to': 2, 'edge_a': 1, 'edge_b': 0},
                {'from': 0, 'to': 3, 'edge_a': 2, 'edge_b': 0},
                {'from': 1, 'to': 2, 'edge_a': 1, 'edge_b': 1},
                {'from': 1, 'to': 3, 'edge_a': 2, 'edge_b': 1},
                {'from': 2, 'to': 3, 'edge_a': 2, 'edge_b': 2}
            ],
            'metadata': {
                'open_edges': 0,  # Closed tetrahedron
                'closure_type': 'tetrahedral_closed'
            }
        }
        patterns.append(pattern)
    
    return patterns

def generate_attachment_patterns():
    """Generate all attachment patterns."""
    
    # Load polygon symbols from catalog
    polyhedra_file = PROJECT_ROOT / "data" / "catalogs" / "tier1" / "polyhedra.jsonl"
    if not polyhedra_file.exists():
        polyhedra_file = PROJECT_ROOT / "lib" / "catalogs" / "tier1" / "polyhedra.jsonl"
    
    polygon_symbols = []
    if polyhedra_file.exists():
        with open(polyhedra_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        poly = json.loads(line)
                        symbol = poly.get('symbol', '')
                        if symbol:
                            polygon_symbols.append(symbol)
                    except:
                        continue
    
    # Fallback to basic symbols
    if not polygon_symbols:
        polygon_symbols = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T']
    
    print(f"Generating attachment patterns using {len(polygon_symbols)} polygon symbols...")
    
    # Generate all pattern types
    all_patterns = []
    all_patterns.extend(generate_linear_patterns(polygon_symbols, max_length=8))
    print(f"  Generated {len(all_patterns)} linear patterns")
    
    all_patterns.extend(generate_triangular_patterns(polygon_symbols))
    print(f"  Generated {len(all_patterns) - sum(len(generate_linear_patterns(polygon_symbols, max_length=8)) for _ in [1])} triangular patterns")
    
    all_patterns.extend(generate_hexagonal_patterns(polygon_symbols))
    print(f"  Generated {len([p for p in all_patterns if p['pattern_type'] == 'hexagonal'])} hexagonal patterns")
    
    all_patterns.extend(generate_cubic_patterns(polygon_symbols))
    print(f"  Generated {len([p for p in all_patterns if p['pattern_type'] == 'cubic'])} cubic patterns")
    
    all_patterns.extend(generate_tetrahedral_patterns(polygon_symbols))
    print(f"  Generated {len([p for p in all_patterns if p['pattern_type'] == 'tetrahedral'])} tetrahedral patterns")
    
    # Write to file
    output_file = polyhedra_file.parent / "attachment_patterns.jsonl"
    with open(output_file, 'w', encoding='utf-8') as f_out:
        for pattern in all_patterns:
            f_out.write(json.dumps(pattern, ensure_ascii=False) + '\n')
    
    print(f"\n✓ Generated {len(all_patterns)} attachment patterns")
    print(f"  Output: {output_file}")
    
    # Summary by type
    by_type = {}
    for pattern in all_patterns:
        ptype = pattern['pattern_type']
        by_type[ptype] = by_type.get(ptype, 0) + 1
    
    print("\nPattern breakdown:")
    for ptype, count in sorted(by_type.items()):
        print(f"  {ptype}: {count}")
    
    return len(all_patterns)

if __name__ == '__main__':
    count = generate_attachment_patterns()
    sys.exit(0 if count > 0 else 1)

