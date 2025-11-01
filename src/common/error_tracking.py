"""Error tracking utilities (Ticket 3).

This module wires optional third-party crash reporting services (e.g. Sentry)
into the application.  The integration is intentionally lazy: it only attempts
initialisation when a DSN or API key is present, and it gracefully degrades when
third-party SDKs are not installed.
"""
from __future__ import annotations

import logging
import os
from typing import Optional

_logger = logging.getLogger(__name__)

_SENTRY_INITIALISED = False


def init_sentry(
    dsn: Optional[str] = None,
    environment: Optional[str] = None,
    release: Optional[str] = None,
) -> bool:
    """Initialise Sentry if the SDK and configuration are available.

    Parameters
    ----------
    dsn:
        Optional Sentry DSN. Falls back to ``POLYLOG_SENTRY_DSN`` or ``SENTRY_DSN``
        environment variables when omitted.
    environment:
        Optional environment name (e.g., ``staging`` or ``production``). Falls
        back to ``POLYLOG_ENVIRONMENT``.
    release:
        Optional release identifier (e.g., Git commit hash). Falls back to
        ``POLYLOG_RELEASE``.
    """

    global _SENTRY_INITIALISED

    if _SENTRY_INITIALISED:
        return True

    try:
        import sentry_sdk  # type: ignore
    except Exception:  # pragma: no cover - SDK is optional
        _logger.debug("Sentry SDK not installed; skipping crash reporting")
        return False

    resolved_dsn = dsn or os.getenv("POLYLOG_SENTRY_DSN") or os.getenv("SENTRY_DSN")
    if not resolved_dsn:
        _logger.debug("No Sentry DSN provided; skipping crash reporting")
        return False

    options = {"dsn": resolved_dsn}

    resolved_env = environment or os.getenv("POLYLOG_ENVIRONMENT")
    if resolved_env:
        options["environment"] = resolved_env

    resolved_release = release or os.getenv("POLYLOG_RELEASE")
    if resolved_release:
        options["release"] = resolved_release

    try:
        sentry_sdk.init(**options)
    except Exception as exc:  # pragma: no cover - defensive guard
        _logger.error("Failed to initialise Sentry: %s", exc)
        return False

    _SENTRY_INITIALISED = True
    _logger.info("Sentry error tracking initialised")
    return True


def init_from_env() -> bool:
    """Initialise any configured error tracking providers."""

    activated = init_sentry()
    # Additional providers (e.g., Bugsnag) can be initialised here later.
    return activated


__all__ = ["init_sentry", "init_from_env"]
