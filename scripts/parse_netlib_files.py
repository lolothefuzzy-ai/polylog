"""Parse Netlib polyhedra files."""
import argparse
import json
import re
from pathlib import Path
import numpy as np


class NetlibParser:
    """Parse Netlib polyhedron file format."""
    
    def __init__(self):
        self.label_pattern = re.compile(r'^:(\w+)\s*(.*)')
    
    def parse_file(self, file_path: Path) -> dict:
        """Parse a single Netlib file."""
        content = file_path.read_text()
        lines = content.split('\n')
        
        data = {
            'name': None,
            'symbol': None,
            'vertices': [],
            'faces': [],
            'edges': [],
            'solid_volume': None,
            'dihedral_angle': None,
            'dual_file_id': None,
            'net_layout': None
        }
        
        current_section = None
        remaining_count = 0
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Check for section label
            match = self.label_pattern.match(line)
            if match:
                label, value = match.groups()
                current_section = label
                
                if label == 'name':
                    data['name'] = value
                elif label == 'symbol':
                    data['symbol'] = value
                elif label == 'vertices':
                    remaining_count = int(value)
                elif label == 'faces':
                    remaining_count = int(value)
                elif label == 'edges':
                    remaining_count = int(value)
                elif label == 'solid':
                    data['solid_volume'] = float(value) if value else None
                elif label == 'dihedral':
                    data['dihedral_angle'] = float(value) if value else None
                elif label == 'dual':
                    data['dual_file_id'] = int(value) if value else None
                elif label == 'net':
                    data['net_layout'] = value
                
                continue
            
            # Parse data lines
            if current_section == 'vertices' and remaining_count > 0:
                coords = [float(x) for x in line.split()]
                data['vertices'].append(coords)
                remaining_count -= 1
                
            elif current_section == 'faces' and remaining_count > 0:
                parts = line.split()
                if not parts:
                    continue
                face_size = int(parts[0])
                vertex_indices = [int(x) for x in parts[1:1+face_size]]
                data['faces'].append(vertex_indices)
                remaining_count -= 1
                
            elif current_section == 'edges' and remaining_count > 0:
                v1, v2 = [int(x) for x in line.split()]
                data['edges'].append((v1, v2))
                remaining_count -= 1
        
        return data


def main():
    parser = argparse.ArgumentParser(description='Parse Netlib polyhedra files')
    parser.add_argument('--input', type=str, required=True, help='Input directory')
    parser.add_argument('--corrections', type=str, help='Directory with corrected files')
    parser.add_argument('--output', type=str, required=True, help='Output JSONL file')
    
    args = parser.parse_args()
    input_dir = Path(args.input)
    output_path = Path(args.output)
    
    # Use corrections if provided
    corrections_dir = Path(args.corrections) if args.corrections else None
    
    parser = NetlibParser()
    results = []
    
    # Process each file
    for file_path in input_dir.glob('*.txt'):
        file_id = int(file_path.stem)
        
        # Use corrected version if available
        if corrections_dir and (corrections_dir / file_path.name).exists():
            file_path = corrections_dir / file_path.name
            
        print(f"Parsing {file_path}...")
        data = parser.parse_file(file_path)
        data['file_id'] = file_id
        results.append(data)
    
    # Write JSONL output
    with open(output_path, 'w') as f:
        for item in results:
            f.write(json.dumps(item) + '\n')
    
    print(f"Parsed {len(results)} files. Output: {output_path}")


if __name__ == "__main__":
    main()
