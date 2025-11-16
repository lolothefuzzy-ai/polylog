"""Python bridge functions exposed to the Tauri desktop shell."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

CATALOG_PATH = REPO_ROOT / "catalogs" / "unicode_mapping.json"


def _load_unicode_mapping() -> Dict[str, Dict[str, Any]]:
    if not CATALOG_PATH.exists():
        return {}
    with CATALOG_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def simulate(params: str) -> str:
    """Placeholder simulation entry point used by the Tauri bridge."""

    if params == "invalid_params":
        raise ValueError("Invalid simulation parameters")

    payload = {"status": "ok", "message": f"Simulated with: {params}"}
    return json.dumps(payload)


def get_unicode_symbols(params: str) -> str:
    """Return a list of Unicode symbols for the UI palette."""

    options = json.loads(params) if params else {}
    limit = options.get("limit")
    include_metadata = options.get("include_metadata", True)

    mapping = _load_unicode_mapping()
    symbols: Iterable[tuple[str, Dict[str, Any]]] = mapping.items()
    if limit:
        symbols = list(symbols)[: int(limit)]

    records = []
    for symbol, data in symbols:
        record = {"symbol": symbol, "polyform_id": data.get("uuid")}
        if include_metadata:
            record["name"] = data.get("name")
            record["source"] = data.get("source")
        records.append(record)

    return json.dumps({"symbols": records})


def launch_polyform(params: str) -> str:
    """Trigger a polyform launch from the desktop UI."""

    payload = json.loads(params) if params else {}
    symbol = payload.get("symbol")
    if not symbol:
        raise ValueError("Missing 'symbol' in payload")

    mapping = _load_unicode_mapping()
    record = mapping.get(symbol)
    if record is None:
        raise ValueError(f"Unknown symbol: {symbol}")

    response = {
        "status": "ok",
        "symbol": symbol,
        "polyform_id": record.get("uuid"),
        "message": "Launch request accepted",
    }
    return json.dumps(response)
