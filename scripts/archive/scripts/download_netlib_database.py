"""Download Netlib polyhedra database."""
import argparse
import requests
import time
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description='Download Netlib polyhedra database')
    parser.add_argument('--output', type=str, required=True, help='Output directory')
    parser.add_argument('--start', type=int, default=0, help='Start file ID')
    parser.add_argument('--end', type=int, default=141, help='End file ID')
    parser.add_argument('--delay', type=float, default=0.5, help='Delay between downloads')
    
    args = parser.parse_args()
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    base_url = "https://netlib.org/polyhedra/"
    
    print(f"Downloading Netlib polyhedra {args.start}–{args.end}...")
    
    for file_id in range(args.start, args.end + 1):
        url = f"{base_url}{file_id}"
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
        
        time.sleep(args.delay)
    
    print(f"Download complete. Files saved to {output_dir}")


if __name__ == "__main__":
    main()
