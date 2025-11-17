#!/usr/bin/env python3
"""Import Netlib bundle into workspace directory structure."""
import json
import re
from pathlib import Path

BUNDLE_PATH = "data/polyhedra/external/netlib/raw/netlib_bundle.json"
OUTPUT_DIR = "data/polyhedra/external/netlib/raw"

print(f"Importing Netlib bundle from {BUNDLE_PATH}...")

with open(BUNDLE_PATH) as f:
    bundle = json.load(f)

Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
count = 0

for file_id, content in bundle["polyhedra"].items():
    filename = f"{int(file_id):03d}.txt"
    path = Path(OUTPUT_DIR) / filename
    
    with open(path, "w") as f:
        f.write(content)
    count += 1

print(f"✓ Imported {count} polyhedra files")
print(f"Files saved to {OUTPUT_DIR}")
