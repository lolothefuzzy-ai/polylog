"""Validate the stable polyform catalog against a JSON schema.

Usage:
    python scripts/validate_polyform_schema.py [path_to_jsonl]

Outputs the first 10 validation errors (if any) and exits with status 1.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Iterable

try:  # pragma: no cover - optional dependency
    from jsonschema import ValidationError, validate
except ImportError:  # pragma: no cover
    raise SystemExit("✗ jsonschema not installed. Run `pip install jsonschema`.\n")

SCHEMA = {
    "type": "object",
    "required": ["uuid", "composition"],
    "properties": {
        "uuid": {"type": "string", "pattern": "^[0-9a-f]{32}$"},
        "composition": {"type": "string"},
        "O": {"type": "integer", "minimum": 1},
        "I": {"type": "integer", "minimum": 1},
        "unicode_char": {"type": "string", "minLength": 1, "maxLength": 2},
        "vertices": {"type": "array"},
        "fold_angles": {"type": "array"},
        "stability": {"type": "number", "minimum": 0.0, "maximum": 1.0},
    },
    "additionalProperties": True,
}

DEFAULT_PATH = Path("stable_polyforms.jsonl")


def _iter_lines(path: Path) -> Iterable[tuple[int, str]]:
    for idx, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.strip()
        if stripped:
            yield idx, stripped


def validate_polyforms(path: Path) -> list[tuple[int, str]]:
    errors: list[tuple[int, str]] = []

    for idx, line in _iter_lines(path):
        try:
            entry = json.loads(line)
            validate(entry, SCHEMA)
        except (json.JSONDecodeError, ValidationError) as exc:
            errors.append((idx, str(exc)))

    return errors


def main(args: list[str]) -> int:
    target = Path(args[0]) if args else DEFAULT_PATH
    if not target.exists():
        print(f"✗ File not found: {target}")
        return 1

    errors = validate_polyforms(target)
    if not errors:
        print(f"✓ Schema valid ({target})")
        return 0

    print(f"✗ Schema validation failed for {target} — showing first 10 issues:")
    for idx, message in errors[:10]:
        print(f"  • Line {idx}: {message}")
    if len(errors) > 10:
        print(f"  … {len(errors) - 10} additional issues omitted")

    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
