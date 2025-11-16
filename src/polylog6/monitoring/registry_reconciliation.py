"""Registry reconciliation utilities (INT-006).

Provides helpers to capture registry snapshots, compute digests, and diff two
states to highlight offline vs. live mismatches.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, Mapping, Optional, Tuple

from polylog6.storage.manager import PolyformStorageManager
from polylog6.storage.symbol_registry import SymbolRegistry
from .alerts import AlertSink, render_registry_diff_alerts

RegistryState = Mapping[str, Mapping[str, str]]


def _normalize_state(state: RegistryState) -> Dict[str, Dict[str, str]]:
    """Return a deep-copied, deterministically ordered state mapping."""

    normalized: Dict[str, Dict[str, str]] = {}
    for namespace, entries in state.items():
        normalized[namespace] = dict(sorted(entries.items()))
    return normalized


def compute_digest(state: RegistryState) -> str:
    """Compute a stable digest for a registry state."""

    normalized = _normalize_state(state)
    payload = json.dumps(normalized, sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass(slots=True)
class RegistrySnapshot:
    """Represents a captured registry state and its digest."""

    label: str
    state: Dict[str, Dict[str, str]]
    digest: str

    @classmethod
    def from_registry(cls, label: str, registry: SymbolRegistry) -> "RegistrySnapshot":
        state = _normalize_state(registry.export_state())
        return cls(label=label, state=state, digest=compute_digest(state))


@dataclass(slots=True)
class RegistryDiff:
    """Symmetric diff between baseline and candidate registry states."""

    baseline_label: str
    candidate_label: str
    missing_symbols: Dict[str, Tuple[str, str]] = field(default_factory=dict)
    unexpected_symbols: Dict[str, Tuple[str, str]] = field(default_factory=dict)
    mismatched_symbols: Dict[str, Tuple[str, str]] = field(default_factory=dict)

    def has_diffs(self) -> bool:
        return bool(self.missing_symbols or self.unexpected_symbols or self.mismatched_symbols)


class RegistryReconciliationHarness:
    """Compare live registry state against a baseline snapshot."""

    def __init__(
        self,
        storage_manager: PolyformStorageManager,
        *,
        sinks: Optional[Iterable[AlertSink]] = None,
    ) -> None:
        self._storage_manager = storage_manager
        self._sinks: list[AlertSink] = list(sinks or [])

    def add_sink(self, sink: AlertSink) -> None:
        """Register an additional alert sink."""

        self._sinks.append(sink)

    def _emit_alerts(self, diff: RegistryDiff) -> None:
        for alert in render_registry_diff_alerts(diff):
            for sink in self._sinks:
                sink.emit(alert)

    # ------------------------------------------------------------------
    # Snapshot helpers
    # ------------------------------------------------------------------
    def capture_snapshot(self, label: str) -> RegistrySnapshot:
        """Capture the current registry state managed by the storage manager."""

        return RegistrySnapshot.from_registry(label, self._storage_manager.encoder.registry)

    def load_snapshot(self, path: Path) -> RegistrySnapshot:
        data = json.loads(path.read_text(encoding="utf-8"))
        state = _normalize_state(data["state"])
        digest = data.get("digest") or compute_digest(state)
        label = data.get("label", path.stem)
        return RegistrySnapshot(label=label, state=state, digest=digest)

    def save_snapshot(self, snapshot: RegistrySnapshot, path: Path) -> None:
        payload = {"label": snapshot.label, "digest": snapshot.digest, "state": snapshot.state}
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    # ------------------------------------------------------------------
    # Diff utilities
    # ------------------------------------------------------------------
    def diff(self, baseline: RegistrySnapshot, candidate: RegistrySnapshot) -> RegistryDiff:
        """Produce a symmetric diff between two snapshots."""

        diff = RegistryDiff(
            baseline_label=baseline.label,
            candidate_label=candidate.label,
        )

        for namespace in sorted(set(baseline.state) | set(candidate.state)):
            base_entries = baseline.state.get(namespace, {})
            cand_entries = candidate.state.get(namespace, {})

            for signature, symbol in base_entries.items():
                cand_symbol = cand_entries.get(signature)
                if cand_symbol is None:
                    diff.missing_symbols[signature] = (namespace, symbol)
                elif cand_symbol != symbol:
                    diff.mismatched_symbols[signature] = (
                        namespace,
                        f"expected {symbol!r}, found {cand_symbol!r}",
                    )

            for signature, symbol in cand_entries.items():
                if signature not in base_entries:
                    diff.unexpected_symbols[signature] = (namespace, symbol)

        return diff

    def verify_parity(
        self,
        baseline: RegistrySnapshot,
        candidate: Optional[RegistrySnapshot] = None,
    ) -> Tuple[bool, RegistryDiff]:
        """Return parity status and diff for the current registry.

        If ``candidate`` is omitted the current runtime registry is captured.
        """

        current = candidate or self.capture_snapshot("runtime")
        diff = self.diff(baseline, current)
        if diff.has_diffs():
            self._emit_alerts(diff)
        return (not diff.has_diffs(), diff)

    # ------------------------------------------------------------------
    # Reconciliation helpers
    # ------------------------------------------------------------------
    def reconcile(self, baseline: RegistrySnapshot) -> RegistryDiff:
        """Reload the baseline registry state into the storage manager."""

        self._storage_manager.encoder.registry.load_state(baseline.state)
        current = self.capture_snapshot("post-reload")
        diff = self.diff(baseline, current)
        if diff.has_diffs():
            self._emit_alerts(diff)
        return diff


__all__ = [
    "RegistryReconciliationHarness",
    "RegistrySnapshot",
    "RegistryDiff",
    "compute_digest",
]
