"""Populate catalog artifacts from stable polyform checkpoints.

This script consolidates the individual generator utilities so we can produce
production-grade JSON artifacts in one pass. It is intentionally light on
business logic and delegates to the specialized modules under ``scripts/``.
"""

from __future__ import annotations

import argparse
import json
import hashlib
import sys
from datetime import UTC, datetime
from collections import defaultdict
from multiprocessing import Pool, cpu_count
from pathlib import Path
from typing import Iterable, Sequence

try:
    from scripts.validate_polyform_schema import validate_polyforms
except ModuleNotFoundError:  # pragma: no cover - CLI execution path
    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    from scripts.validate_polyform_schema import validate_polyforms

STABLE_POLYFORMS = Path("stable_polyforms.jsonl")
CATALOG_DIR = Path("catalogs")


def _load_polyforms(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError("stable_polyforms.jsonl not found; sync INT-009 assets first")

    polyforms: list[dict] = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        polyforms.append(json.loads(line))
    return polyforms


def populate_attachment_graph(polyforms: Iterable[dict], catalog_dir: Path) -> Path:
    graph = defaultdict(lambda: {"pairs": [], "scores": {}})

    for polyform in polyforms:
        composition = polyform.get("composition", "")
        polygon_types = sorted(set(composition))

        for idx, type_a in enumerate(polygon_types):
            for type_b in polygon_types[idx:]:
                pair_key = f"{type_a}\u2194{type_b}"
                graph[pair_key]["pairs"].append(
                    {
                        "polyform_uuid": polyform.get("uuid"),
                        "fold_angles": polyform.get("fold_angles", []),
                        "stability_score": polyform.get("stability", 0.8),
                    }
                )

    output = catalog_dir / "attachment_graph.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(graph, indent=2, sort_keys=True))
    return output


def populate_scaler_tables(polyforms: Iterable[dict], catalog_dir: Path) -> Path:
    scalers = {}
    for polyform in polyforms:
        char = polyform.get("unicode_char", polyform.get("uuid", "")[:1])
        scalers[char] = {
            "O": polyform.get("O", 1),
            "I": polyform.get("I", polyform.get("O", 1) * 3),
            "composition": polyform.get("composition"),
        }

    output = catalog_dir / "scaler_tables.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(scalers, indent=2, sort_keys=True))
    return output


def compute_checksum(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def write_catalog_metadata(source_file: Path, outputs: dict[str, Path], catalog_dir: Path) -> Path:
    metadata = {
        "source_file": str(source_file.name),
        "source_checksum": compute_checksum(source_file) if source_file.exists() else None,
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "artifacts": {
            name: {
                "path": str(path.relative_to(Path.cwd()) if path.is_absolute() else path),
                "checksum": compute_checksum(path) if path.exists() else None,
            }
            for name, path in outputs.items()
        },
    }

    metadata_path = catalog_dir / "metadata.json"
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True))
    return metadata_path


def _process_polyform(polyform: dict) -> dict:
    # Placeholder for heavier computation; kept simple for now.
    return {
        "uuid": polyform.get("uuid"),
        "composition": polyform.get("composition"),
        "attachments": polyform.get("fold_angles", []),
    }


def _load_polyforms_parallel(path: Path, workers: int | None = None) -> list[dict]:
    polyforms = _load_polyforms(path)
    workers = workers or min(4, cpu_count() or 1)

    if workers <= 1 or len(polyforms) < workers * 2:
        return polyforms

    with Pool(processes=workers) as pool:
        processed = pool.map(_process_polyform, polyforms)

    # Merge processed fields back into original entries
    for original, processed_entry in zip(polyforms, processed, strict=False):
        original.setdefault("_preprocessed", {}).update(processed_entry)

    return polyforms


def _ensure_schema_valid(path: Path) -> None:
    errors = validate_polyforms(path)
    if errors:
        preview = "\n".join(f"  • line {idx}: {message}" for idx, message in errors[:5])
        if len(errors) > 5:
            preview += f"\n  • … {len(errors) - 5} additional issues"
        raise ValueError(f"Schema validation failed for {path}\n{preview}")


def populate_all(
    *,
    source: Path = STABLE_POLYFORMS,
    catalog_dir: Path = CATALOG_DIR,
    workers: int | None = None,
    validate_schema: bool = True,
) -> dict[str, Path]:
    if validate_schema:
        _ensure_schema_valid(source)

    polyforms = _load_polyforms_parallel(source, workers=workers)

    catalog_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        "attachment_graph": populate_attachment_graph(polyforms, catalog_dir),
        "scaler_tables": populate_scaler_tables(polyforms, catalog_dir),
    }
    outputs["metadata"] = write_catalog_metadata(source, outputs, catalog_dir)
    return outputs


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Populate Polylog catalog artifacts")
    parser.add_argument("--source", type=Path, default=STABLE_POLYFORMS, help="Path to stable_polyforms.jsonl")
    parser.add_argument(
        "--catalog-dir",
        type=Path,
        default=CATALOG_DIR,
        help="Directory to write catalog artifacts",
    )
    parser.add_argument("--workers", type=int, default=None, help="Maximum worker processes for preprocessing")
    parser.add_argument("--skip-schema", action="store_true", help="Skip JSON schema validation step")

    args = parser.parse_args(argv)

    try:
        outputs = populate_all(
            source=args.source,
            catalog_dir=args.catalog_dir,
            workers=args.workers,
            validate_schema=not args.skip_schema,
        )
    except Exception as exc:  # pragma: no cover - CLI convenience
        print(f"✗ Catalog population failed: {exc}", file=sys.stderr)
        return 1

    for name, path in outputs.items():
        print(f"[ok] {name}: {path}")
    return 0


if __name__ == "__main__":  # pragma: no cover - convenience script
    raise SystemExit(main())
