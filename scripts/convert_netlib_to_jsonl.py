"""Convert parsed Netlib data to our JSONL schema."""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description='Convert Netlib data to JSONL schema')
    parser.add_argument('--input', type=str, required=True, help='Input JSONL file')
    parser.add_argument('--output', type=str, required=True, help='Output JSONL file')
    
    args = parser.parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(input_path) as f_in, open(output_path, 'w') as f_out:
        for line in f_in:
            netlib_data = json.loads(line)
            
            # Convert to our schema
            polyform = {
                "uuid": f"netlib_{netlib_data['file_id']}",
                "name": netlib_data['name'],
                "source": "netlib",
                "source_id": netlib_data['file_id'],
                "vertices": netlib_data['vertices'],
                "faces": netlib_data['faces'],
                "edges": netlib_data['edges'],
                "volume": netlib_data['solid_volume'],
                "dihedral_angles": {"primary": netlib_data['dihedral_angle']} if netlib_data['dihedral_angle'] else {},
                "metadata": {
                    "symbol": netlib_data['symbol'],
                    "dual_source_id": netlib_data['dual_file_id'],
                }
            }
            
            f_out.write(json.dumps(polyform) + '\n')
    
    print(f"Converted {input_path} to {output_path}")


if __name__ == "__main__":
    main()
