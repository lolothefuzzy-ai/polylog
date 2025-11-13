# Priority 1 — Catalog Hydration (INT-009)

## TASK-CAT-001: Schema Validator

- **File:** `scripts/validate_polyform_schema.py`
- **Dependencies:** `jsonschema`
- **Code Stub:**

  ```python
  import json
  from pathlib import Path
  from jsonschema import validate, ValidationError

  SCHEMA = {
      "type": "object",
      "required": ["uuid", "composition"],
      "properties": {
          "uuid": {"type": "string", "pattern": "^[0-9a-f]{32}$"},
          "composition": {"type": "string"},
          "O": {"type": "integer", "minimum": 1},
          "I": {"type": "integer", "minimum": 1},
          "vertices": {"type": "array"},
      },
  }

  def validate_polyforms(path: Path) -> list[tuple[int, str]]:
      """Returns list of (line_number, error_message) tuples"""
      errors = []
      for i, line in enumerate(path.read_text().splitlines(), 1):
          try:
              entry = json.loads(line)
              validate(entry, SCHEMA)
          except (json.JSONDecodeError, ValidationError) as exc:
              errors.append((i, str(exc)))
      return errors

  if __name__ == "__main__":
      errors = validate_polyforms(Path("stable_polyforms.jsonl"))
      if errors:
          for line, msg in errors[:10]:
              print(f"Line {line}: {msg}")
          raise SystemExit(1)
      print("✓ Schema valid")
  ```

- **Validation:** exits 0 on valid input; exits 1 with first 10 errors otherwise
- **Resources:** <https://python-jsonschema.readthedocs.io/en/stable/>

## TASK-CAT-002: Catalog Checksum Tracking

- **File:** `scripts/populate_catalogs.py`
- **Code Addition:**

  ```python
  import hashlib
  import json
  from datetime import datetime
  from pathlib import Path

  def compute_checksum(path: Path) -> str:
      hasher = hashlib.sha256()
      with path.open("rb") as handle:
          hasher.update(handle.read())
      return hasher.hexdigest()

  def save_catalog_metadata(source_file: Path, output_dir: Path) -> None:
      metadata = {
          "source_file": source_file.name,
          "checksum": compute_checksum(source_file),
          "generated_at": datetime.utcnow().isoformat() + "Z",
          "entry_count": sum(1 for _ in source_file.read_text().splitlines()),
      }
      (output_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))
  ```

- **Usage:** invoke `save_catalog_metadata` after catalog generation completes
- **Validation:** `catalogs/metadata.json` contains checksum, timestamp, and entry count
- **Resources:** Python `hashlib` docs

## TASK-CAT-003: Parallel Catalog Generation

- **File:** `scripts/populate_catalogs.py`
- **Dependencies:** Python `multiprocessing`
- **Code Stub:**

  ```python
  from functools import partial
  from multiprocessing import Pool, cpu_count

  def process_polyform(entry: dict) -> dict:
      return {
          "uuid": entry["uuid"],
          "attachments": compute_attachments(entry),
          "scalers": compute_scalers(entry),
          "lod_levels": generate_lod_levels(entry),
      }

  def populate_catalogs_parallel(polyforms: list[dict], workers: int | None = None) -> list[dict]:
      workers = workers or cpu_count()
      with Pool(workers) as pool:
          return pool.map(process_polyform, polyforms)

  if __name__ == "__main__":
      polyforms = [json.loads(line) for line in Path("stable_polyforms.jsonl").read_text().splitlines()]
      results = populate_catalogs_parallel(polyforms)
      write_catalogs(results)
  ```

- **Validation:** generate 500-entry catalog in <15 minutes; results identical to single-threaded path
- **Usage Note:** The consolidated CLI `python scripts/populate_catalogs.py --workers auto` performs schema validation, writes refreshed artifacts to `catalogs/`, and emits `catalogs/metadata.json` with checksums for runbook auditing.
- **Resources:** <https://docs.python.org/3/library/multiprocessing.html>
