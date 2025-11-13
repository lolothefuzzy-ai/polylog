"""Download George Hart's corrected Netlib files."""
import argparse
import requests
from pathlib import Path

# Hart's corrected files
HART_CORRECTIONS = {
    66: "https://www.georgehart.com/virtual-polyhedra/netlib-info/066.txt",
    67: "https://www.georgehart.com/virtual-polyhedra/netlib-info/067.txt",
    68: "https://www.georgehart.com/virtual-polyhedra/netlib-info/068.txt",
    69: "https://www.georgehart.com/virtual-polyhedra/netlib-info/069.txt",
    70: "https://www.georgehart.com/virtual-polyhedra/netlib-info/070.txt",
    81: "https://www.georgehart.com/virtual-polyhedra/netlib-info/081.txt",
    108: "https://www.georgehart.com/virtual-polyhedra/netlib-info/108.txt",
    115: "https://www.georgehart.com/virtual-polyhedra/netlib-info/115.txt",
}


def main():
    parser = argparse.ArgumentParser(description="Download George Hart's corrected Netlib files")
    parser.add_argument('--output', type=str, required=True, help='Output directory')
    parser.add_argument('--files', type=str, help='Comma-separated list of file IDs to download (default: all)')
    
    args = parser.parse_args()
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    file_ids = [int(id) for id in args.files.split(',')] if args.files else list(HART_CORRECTIONS.keys())
    
    print(f"Downloading {len(file_ids)} corrected files to {output_dir}...")
    
    for file_id in file_ids:
        if file_id not in HART_CORRECTIONS:
            print(f"  ✗ File ID {file_id} not in Hart corrections")
            continue
            
        url = HART_CORRECTIONS[file_id]
        file_path = output_dir / f"{file_id:03d}.txt"
        
        print(f"  Downloading {url}...", end='', flush=True)
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            
            with open(file_path, 'w') as f:
                f.write(response.text)
            print(f" ✓")
            
        except Exception as e:
            print(f" ✗ Failed: {str(e)}")


if __name__ == "__main__":
    main()
