"""Convenience runner for catalog generation scaffolds."""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

CATALOG_SCRIPTS = [
    "scripts.generate_geometry_catalog",
    "scripts.generate_attachment_graph",
    "scripts.generate_scaler_tables",
    "scripts.generate_lod_metadata",
]


def run_generators() -> dict[str, Path]:
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    outputs: dict[str, Path] = {}
    for module_name in CATALOG_SCRIPTS:
        module = importlib.import_module(module_name)
        output_path = module.CATALOG_PATH  # type: ignore[attr-defined]
        if not hasattr(module, "main"):
            raise RuntimeError(f"Generator {module_name} is missing a main() function")
        module.main()
        outputs[module_name] = Path(output_path)
    return outputs


def main() -> None:
    outputs = run_generators()
    for module_name, path in outputs.items():
        print(f"Generated {path} via {module_name}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover - convenience script
        print(f"Catalog generation failed: {exc}", file=sys.stderr)
        sys.exit(1)
