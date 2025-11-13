from __future__ import annotations

import pytest

from polylog6.simulation.engines.guardrails import GuardrailBreachError, GuardrailConfig, evaluate_guardrails
from polylog6.simulation.engines.core import SimulationEngine
from polylog6.simulation.engines.checkpointing.workspace import PolyformWorkspace
from polylog6.storage.encoder import EncodedPolygon


def _populate_workspace(count: int, delta=(0, 0, 0)) -> PolyformWorkspace:
    workspace = PolyformWorkspace()
    for index in range(count):
        workspace.add_polygon(
            sides=3 + (index % 3),
            orientation_index=index,
            rotation_count=0,
            delta=(delta[0] + index, delta[1], delta[2]),
        )
    return workspace


def test_evaluate_guardrails_pass_with_warnings():
    workspace = _populate_workspace(5)
    status = evaluate_guardrails(workspace, GuardrailConfig())
    assert status.passed
    assert status.breaches == []
    assert status.dimension == "2d"
    assert "2D-exempt" in " ".join(status.warnings)
    assert 0.0 <= status.stability_score <= 1.0
    assert status.closure_ratio == 0.0


def test_evaluate_guardrails_breach_and_raise():
    workspace = PolyformWorkspace()
    status = evaluate_guardrails(workspace, GuardrailConfig(stability_threshold=0.5))
    assert status.passed

    config = GuardrailConfig(stability_threshold=1.5, raise_on_breach=True)
    workspace.add_polygon(sides=3, orientation_index=0, rotation_count=0, delta=(0, 0, 0))
    workspace.ingest_tokens(0, [("module", 1)])
    with pytest.raises(GuardrailBreachError):
        evaluate_guardrails(workspace, config)


def test_simulation_engine_guardrail_integration(tmp_path):
    engine = SimulationEngine(
        checkpoint_interval=1,
        guardrail_config=GuardrailConfig(stability_threshold=0.0),
    )
    encoded = [EncodedPolygon(3, 0, 0, (0, 0, 0))]
    engine.extend(encoded)

    summary = engine.tick(force=True)
    assert summary is not None
    status = engine.last_guardrail_status
    assert status is not None
    assert status.passed
    assert status.dimension == "2d"
    assert status.warnings

