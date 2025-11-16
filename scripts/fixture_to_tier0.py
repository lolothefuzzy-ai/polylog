#!/usr/bin/env python3
"""Convert fixture polyforms to Tier 0 dataset with valid UUIDs."""
import json
import uuid
from pathlib import Path


def main():
    fixture_path = Path("src/polylog6/detection/fixtures/polyforms.jsonl")
    output_path = Path("tier0_dataset.jsonl")
    
    with fixture_path.open("r") as src, output_path.open("w") as dst:
        for line in src:
            entry = json.loads(line)
            # Generate a new UUID
            entry["uuid"] = str(uuid.uuid4()).replace("-", "")
            dst.write(json.dumps(entry) + "\n")
    
    print(f"Generated {output_path} from fixture with valid UUIDs")


if __name__ == "__main__":
    main()
