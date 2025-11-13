# Catalog Generation Roundup

This note tracks the quick scaffolding for the hydrator catalog assets. It is a
low-priority checklist that can be updated whenever new catalog tooling is
added.

## Current Assets

- `scripts/generate_geometry_catalog.py` – scaffolds primitive/polyhedra entries
  in `catalogs/geometry_catalog.json`.
- `scripts/generate_attachment_graph.py` – prepares the attachment graph shell.
- `scripts/generate_scaler_tables.py` – sets up the scaler table placeholder.
- `scripts/generate_lod_metadata.py` – writes the LOD metadata skeleton.
- `scripts/run_catalog_generators.py` – convenience wrapper that runs all
  generators and reports which catalogs were (re)created.

## Usage Pattern

1. `python scripts/run_catalog_generators.py`
2. Inspect the resulting JSON files under `catalogs/`.
3. Replace placeholders with production data via dedicated generation passes:
   - Geometry extraction from descriptor library
   - Parallel attachment enumeration
   - Cascading O/I scaler computation
   - Empirical LOD profiling

## Next Roundup Targets

- Add smoke tests that invoke the generator scripts and validate schema stubs.
- Record timing metrics when the real population routines are implemented.
- Document data provenance for geometry and scaler inputs once available.
