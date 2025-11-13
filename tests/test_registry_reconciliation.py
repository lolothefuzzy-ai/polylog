from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from polylog6.monitoring.registry_reconciliation import (
    RegistryReconciliationHarness,
    RegistrySnapshot,
    compute_digest,
)
from polylog6.monitoring.alerts import ListAlertSink
from polylog6.storage.manager import PolyformStorageManager
from polylog6.storage.symbol_registry import PolyformSymbolRegistry


def test_compute_digest_is_deterministic() -> None:
    state_a = {
        "clusters": {"triangle": "Δ"},
        "assemblies": {},
        "megas": {},
    }
    state_b = {
        "assemblies": {},
        "megas": {},
        "clusters": {"triangle": "Δ"},
    }

    assert compute_digest(state_a) == compute_digest(state_b)


def test_registry_snapshot_from_registry() -> None:
    registry = PolyformSymbolRegistry()
    registry.load_state({"clusters": {"square": "☐"}, "assemblies": {}, "megas": {}})

    snapshot = RegistrySnapshot.from_registry("baseline", registry)

    expected_state = {
        "clusters": {"square": "☐"},
        "assemblies": {},
        "megas": {},
    }
    assert snapshot.state == expected_state
    assert snapshot.digest == compute_digest(expected_state)


def test_registry_diff_detects_variations() -> None:
    baseline = RegistrySnapshot(
        label="baseline",
        state={
            "clusters": {"triangle": "Δ"},
            "assemblies": {"tetra": "T"},
            "megas": {},
        },
        digest="baseline",
    )
    candidate = RegistrySnapshot(
        label="candidate",
        state={
            "clusters": {"triangle": "Δ", "square": "☐"},
            "assemblies": {"tetra": "τ"},
            "megas": {},
        },
        digest="candidate",
    )

    stub_manager = SimpleNamespace(encoder=SimpleNamespace(registry=PolyformSymbolRegistry()))
    harness = RegistryReconciliationHarness(stub_manager)  # type: ignore[arg-type]

    diff = harness.diff(baseline, candidate)

    assert diff.missing_symbols == {}
    assert diff.unexpected_symbols == {"square": ("clusters", "☐")}
    assert "tetra" in diff.mismatched_symbols


def test_registry_reconciliation_roundtrip(tmp_path: Path) -> None:
    manager = PolyformStorageManager(tmp_path)
    harness = RegistryReconciliationHarness(manager)

    baseline_state = {
        "clusters": {"triangle": "Δ"},
        "assemblies": {"tetra": "T"},
        "megas": {},
    }
    manager.encoder.registry.load_state(baseline_state)

    baseline = harness.capture_snapshot("baseline")

    # Introduce drift in the live registry.
    drift_state = {
        "clusters": {"triangle": "Δ", "square": "☐"},
        "assemblies": {"tetra": "τ"},
        "megas": {},
    }
    manager.encoder.registry.load_state(drift_state)

    parity, diff = harness.verify_parity(baseline)
    assert parity is False
    assert diff.unexpected_symbols == {"square": ("clusters", "☐")}

    reconcile_diff = harness.reconcile(baseline)
    assert reconcile_diff.has_diffs() is False

    parity_after, diff_after = harness.verify_parity(baseline)
    assert parity_after is True
    assert diff_after.has_diffs() is False


def test_registry_reconciliation_emits_alerts_on_drift(tmp_path: Path) -> None:
    manager = PolyformStorageManager(tmp_path)
    sink = ListAlertSink()
    harness = RegistryReconciliationHarness(manager, sinks=[sink])

    baseline_state = {
        "clusters": {"triangle": "Δ"},
        "assemblies": {},
        "megas": {},
    }
    manager.encoder.registry.load_state(baseline_state)
    baseline = harness.capture_snapshot("baseline")

    drift_state = {
        "clusters": {"triangle": "Δ", "square": "☐"},
        "assemblies": {},
        "megas": {},
    }
    manager.encoder.registry.load_state(drift_state)

    parity, diff = harness.verify_parity(baseline)
    assert parity is False
    assert diff.unexpected_symbols == {"square": ("clusters", "☐")}
    assert sink.alerts(), "Expected alert sink to capture alerts"
