#!/usr/bin/env python3
"""
Run this script OUTSIDE the restricted environment to create a Netlib JSON bundle.
Save the output file and import it into your workspace.
"""
import requests
import json
import os
from pathlib import Path

NETLIB_URL = "https://netlib.org/polyhedra/"
BUNDLE_PATH = "netlib_bundle.json"

print(f"Generating Netlib bundle at {BUNDLE_PATH}...")
bundle = {"meta": {"source": NETLIB_URL, "count": 0}, "polyhedra": {}}

for file_id in range(0, 142):
    url = f"{NETLIB_URL}{file_id}"
    print(f"  Fetching {url}...")
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        bundle["polyhedra"][file_id] = response.text
        bundle["meta"]["count"] += 1
    except Exception as e:
        print(f"    ✗ Failed: {str(e)}")

with open(BUNDLE_PATH, "w") as f:
    json.dump(bundle, f)

print(f"✓ Bundle created with {bundle['meta']['count']}/142 files")
print(f"Copy {BUNDLE_PATH} to data/polyhedra/external/netlib/raw/ in your workspace")
