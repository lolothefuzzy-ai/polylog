"""Asset/configuration loader for the INT-014 detection pipeline."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

try:  # pragma: no cover - optional dependency
    import yaml  # type: ignore
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore


@dataclass(slots=True)
class DetectionAssetsReport:
    """Summary of loaded detection assets."""

    polyform_count: int
    scaler_keys: List[str]
    segmentation_config: Dict[str, Any]
    errors: List[str]

    @property
    def is_ready(self) -> bool:
        return self.polyform_count > 0 and bool(self.scaler_keys) and not self.errors


def default_assets_dir() -> Path:
    """Return the built-in fixtures directory shipped with the package."""

    return Path(__file__).resolve().parent / "fixtures"


class DetectionAssets:
    """Load polyform catalogs, scaler tables, and segmentation defaults."""

    def __init__(
        self,
        assets_dir: Path | str,
        *,
        polyforms_file: str = "polyforms.jsonl",
        scalers_file: str = "unicode_scalers.json",
        segmentation_file: Optional[str] = None,
        expect_files: bool = False,
    ) -> None:
        self.assets_dir = Path(assets_dir)
        self.polyforms_file = polyforms_file
        self.scalers_file = scalers_file
        self.segmentation_file = segmentation_file or "segmentation_config.yaml"
        self.expect_files = expect_files

        self.polyforms: List[Dict[str, Any]] = []
        self.scalers: Dict[str, Any] = {}
        self.segmentation_config: Dict[str, Any] = {}
        self.errors: List[str] = []

        self.refresh()

    def refresh(self) -> None:
        """Reload assets from disk."""

        self.polyforms = self._load_jsonl(self.polyforms_file)
        self.scalers = self._load_json(self.scalers_file)
        self.segmentation_config = self._load_structured(self.segmentation_file)

    def _load_jsonl(self, filename: str) -> List[Dict[str, Any]]:
        path = self.assets_dir / filename
        if not path.exists():
            self._maybe_record_error(f"Missing catalog: {path}")
            return []

        records: List[Dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    records.append(json.loads(stripped))
                except json.JSONDecodeError as exc:
                    self.errors.append(f"{path}:{line_number} JSON decode error: {exc}")
        return records

    def _load_json(self, filename: str) -> Dict[str, Any]:
        path = self.assets_dir / filename
        if not path.exists():
            self._maybe_record_error(f"Missing scaler table: {path}")
            return {}

        try:
            with path.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        except json.JSONDecodeError as exc:
            self.errors.append(f"{path} JSON decode error: {exc}")
            return {}

    def _load_structured(self, filename: str) -> Dict[str, Any]:
        path = self.assets_dir / filename
        if not path.exists():
            # Try JSON fallback (same stem, .json suffix)
            json_path = path.with_suffix(".json")
            if json_path.exists():
                return self._load_json(json_path.name)
            self._maybe_record_error(f"Missing segmentation config: {path}")
            return {}

        if path.suffix.lower() in {".yaml", ".yml"}:
            if yaml is None:
                self.errors.append(
                    f"{path} requires PyYAML (optional dependency) to parse segmentation config."
                )
                return {}
            with path.open("r", encoding="utf-8") as handle:
                data = yaml.safe_load(handle) or {}
        else:
            try:
                with path.open("r", encoding="utf-8") as handle:
                    data = json.load(handle)
            except json.JSONDecodeError as exc:
                self.errors.append(f"{path} JSON decode error: {exc}")
                return {}
        if isinstance(data, dict):
            return data
        self.errors.append(f"{path} segmentation config must be a mapping")
        return {}

    def _maybe_record_error(self, message: str) -> None:
        if self.expect_files:
            self.errors.append(message)

    def report(self) -> DetectionAssetsReport:
        """Return a lightweight report of the asset state."""

        return DetectionAssetsReport(
            polyform_count=len(self.polyforms),
            scaler_keys=sorted(self.scalers.keys()),
            segmentation_config=self.segmentation_config,
            errors=list(self.errors),
        )

    @property
    def is_ready(self) -> bool:
        return self.report().is_ready


__all__ = ["DetectionAssets", "DetectionAssetsReport", "default_assets_dir"]
