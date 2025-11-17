#!/usr/bin/env python3
"""Merge external polyform catalogs into ``stable_polyforms.jsonl``.

Usage example::

    python scripts/merge_polyform_catalogs.py \
        --source data/polyhedra/polyhedra.json \
        --target stable_polyforms.jsonl \
        --family Johnson

The source file must be present locally (no network access).  The script
supports JSONL-first catalogs produced by ``generate_canonical_polyforms.py``
and generic JSON exports (e.g. Maeder/Antiprism datasets) containing ``name``,
``vertices`` and ``faces`` fields.
"""
from __future__ import annotations

import argparse
import json
import uuid
from pathlib import Path
from typing import Iterable

JSONLike = dict[str, object]


def load_jsonl(path: Path) -> list[JSONLike]:
    if not path.exists():
        return []
    items: list[JSONLike] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
    return items


def load_json(path: Path) -> list[JSONLike]:
    """Load JSON or JSONL data from a file."""
    data = []
    
    with path.open("r", encoding="utf-8") as handle:
        if path.suffix == ".jsonl":
            # JSON Lines format
            for line in handle:
                if line.strip():
                    data.append(json.loads(line))
        else:
            # Regular JSON
            data = json.load(handle)
    
    return data


def convert_external(items: Iterable[JSONLike], family: str) -> list[JSONLike]:
    converted: list[JSONLike] = []
    for item in items:
        entry = {
            "uuid": item.get("uuid") or str(uuid.uuid4()),
            "name": item.get("name", "Unknown"),
            "family": family,
            "composition": item.get("composition", ""),
            "O": item.get("O", 1),
            "I": item.get("I", 1),
            "vertices": item.get("vertices", []),
            "faces": item.get("faces", []),
            "edges": item.get("edges", 0),
            "volume": item.get("volume", 0.0),
            "surface_area": item.get("surface_area", 0.0),
            "metadata": {
                "source": item.get("metadata", {}).get("source", "external"),
                "family": family,
            },
        }
        converted.append(entry)
    return converted


def merge_catalogs(
    *,
    source: Path,
    target: Path,
    family: str,
    deduplicate: bool = True,
) -> None:
    print(f"Loading existing catalog from {target}…")
    existing = load_jsonl(target)
    print(f"  → {len(existing)} entries")

    print(f"Loading external dataset {source}…")
    external_raw = load_json(source)
    external = convert_external(external_raw, family)
    print(f"  → {len(external)} entries")

    if deduplicate:
        known_names = {entry.get("name") for entry in existing}
        before = len(external)
        external = [entry for entry in external if entry.get("name") not in known_names]
        print(f"  → {len(external)} entries after name dedup ({before - len(external)} skipped)")

    merged = existing + external
    with target.open("w", encoding="utf-8") as handle:
        for entry in merged:
            handle.write(json.dumps(entry, separators=(",", ":")) + "\n")

    print(f"✓ Catalog merged → {target} ({len(merged)} entries total)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge external polyform datasets")
    parser.add_argument("--source", type=Path, required=True, help="Path to external JSON dataset")
    parser.add_argument("--target", type=Path, default=Path("stable_polyforms.jsonl"))
    parser.add_argument("--family", type=str, default="External", help="Family label for imported entries")
    parser.add_argument("--no-dedup", action="store_true", help="Disable name-based deduplication")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    merge_catalogs(
        source=args.source,
        target=args.target,
        family=args.family,
        deduplicate=not args.no_dedup,
    )


if __name__ == "__main__":
    main()
