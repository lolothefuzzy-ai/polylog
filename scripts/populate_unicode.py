"""Populate Unicode symbols for Tier 1, Tier 2, and overflow polyforms."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Tuple

from polylog6.storage.polyform_storage import PolyformStorage


# Tier configuration
TIER1_COUNT = 500
TIER2_COUNT = 5000
TIER1_FREQUENCY = 1500
TIER2_FREQUENCY = 250
OVERFLOW_FREQUENCY = 25


def resolve_dataset_path() -> Path:
    """Locate the stable polyforms dataset."""

    candidates: Iterable[Path] = (
        Path("catalogs/stable_polyforms.jsonl"),
        Path("stable_polyforms.jsonl"),
    )
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError(
        "Unable to locate stable_polyforms.jsonl. Expected it in 'catalogs/' or the project root."
    )


def tier_for_index(index: int) -> Tuple[str, int]:
    """Return tier label and allocation frequency for a dataset index."""

    if index < TIER1_COUNT:
        return "tier1", TIER1_FREQUENCY
    if index < TIER1_COUNT + TIER2_COUNT:
        return "tier2", TIER2_FREQUENCY
    return "overflow", OVERFLOW_FREQUENCY


def main() -> None:
    storage = PolyformStorage()
    dataset_path = resolve_dataset_path()

    mapping: dict[str, dict[str, object]] = {}

    with dataset_path.open("r", encoding="utf-8") as handle:
        for idx, line in enumerate(handle):
            payload = json.loads(line)
            polyform_id = payload["uuid"]
            tier, frequency = tier_for_index(idx)
            symbol = storage.add(polyform_id, payload, frequency)

            mapping[symbol] = {
                "uuid": polyform_id,
                "tier": tier,
                "frequency": frequency,
                "name": payload.get("name"),
                "source": payload.get("source"),
            }

            if idx < 10 or idx % 1000 == 0:
                print(f"[{tier.upper()}] {polyform_id} -> {symbol} (freq={frequency})")

    catalogs_dir = Path("catalogs")
    catalogs_dir.mkdir(parents=True, exist_ok=True)
    mapping_path = catalogs_dir / "unicode_mapping.json"

    with mapping_path.open("w", encoding="utf-8") as handle:
        json.dump({"symbols": mapping}, handle, indent=2, ensure_ascii=False)

    print(f"Saved Unicode mapping to {mapping_path}")


if __name__ == "__main__":
    main()
