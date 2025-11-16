"""Deterministic digest helpers for monitoring parity checks (INT-003/INT-004)."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

__all__ = ["compute_registry_digest"]


def _canonicalize(value: Any) -> Any:
    """Return a JSON-serializable structure with deterministic ordering."""

    if isinstance(value, Mapping):
        return {key: _canonicalize(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [_canonicalize(item) for item in value]
    return value


def compute_registry_digest(storage_state: Mapping[str, Any]) -> str:
    """Compute a canonical SHA256 digest for the registry state."""

    canonical = json.dumps(
        _canonicalize(storage_state),
        separators=(",", ":"),
        ensure_ascii=False,
    )
    hasher = hashlib.sha256()
    hasher.update(canonical.encode("utf-8"))
    return hasher.hexdigest()
