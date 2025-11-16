"""Regression coverage for monitoring configuration helpers."""
from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

import polylog6.monitoring.config as monitoring_config


def _reset_cache() -> None:
    monitoring_config.load_monitoring_settings.cache_clear()


def test_load_settings_from_yaml(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / "monitoring.yaml"
    context_path = tmp_path / "logs" / "context-brief.jsonl"
    fallback_path = tmp_path / "fallback" / "context-brief.jsonl"

    config_path.write_text(
        dedent(
            f"""
            enabled: false
            context_brief:
              path: "{context_path}"
              fallback_paths:
                - "{fallback_path}"
              create_if_missing: true
              poll_interval_ms: 250
            """
        ).strip(),
        encoding="utf-8",
    )

    monkeypatch.setattr(monitoring_config, "DEFAULT_CONFIG_PATH", config_path)
    _reset_cache()

    settings = monitoring_config.load_monitoring_settings()
    assert settings.enabled is False
    assert settings.context_brief.path == context_path
    assert settings.context_brief.fallback_paths == (fallback_path,)
    assert settings.context_brief.create_if_missing is True
    assert pytest.approx(settings.context_brief.poll_interval_seconds, rel=0.01) == 0.25

    assert pytest.approx(monitoring_config.monitoring_poll_interval(), rel=0.01) == 0.25


def test_environment_overrides(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / "monitoring.yaml"
    config_path.write_text("enabled: true\n", encoding="utf-8")

    env_context_path = tmp_path / "env" / "context-brief.jsonl"

    monkeypatch.setattr(monitoring_config, "DEFAULT_CONFIG_PATH", config_path)
    monkeypatch.setenv("POLYLOG_MONITORING_ENABLED", "0")
    monkeypatch.setenv("POLYLOG_CONTEXT_BRIEF_PATH", str(env_context_path))
    monkeypatch.setenv("POLYLOG_MONITORING_POLL_MS", "1500")
    _reset_cache()

    assert monitoring_config.monitoring_enabled() is False
    assert monitoring_config.resolve_context_brief_path() == env_context_path
    assert pytest.approx(monitoring_config.monitoring_poll_interval(), rel=0.01) == 1.5


def test_resolve_context_brief_creates_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / "monitoring.yaml"
    context_path = tmp_path / "runtime" / "context-brief.jsonl"

    config_path.write_text(
        dedent(
            f"""
            enabled: true
            context_brief:
              path: "{context_path}"
              create_if_missing: true
            """
        ).strip(),
        encoding="utf-8",
    )

    monkeypatch.setattr(monitoring_config, "DEFAULT_CONFIG_PATH", config_path)
    _reset_cache()

    assert context_path.exists() is False
    resolved = monitoring_config.resolve_context_brief_path(ensure_exists=True)
    assert resolved == context_path
    assert context_path.exists() is True
*** End Patch
