"""Unit tests for monitoring digest helpers."""

from __future__ import annotations

from polylog6.monitoring.digest import compute_registry_digest


def test_digest_deterministic() -> None:
    state = {"registry": {"uuid1": {"O": 1}, "uuid2": {"O": 2}}}

    digest1 = compute_registry_digest(state)
    digest2 = compute_registry_digest(state)

    assert digest1 == digest2
    assert len(digest1) == 64


def test_digest_order_independent() -> None:
    state1 = {"registry": {"a": 1, "b": 2}}
    state2 = {"registry": {"b": 2, "a": 1}}

    assert compute_registry_digest(state1) == compute_registry_digest(state2)
