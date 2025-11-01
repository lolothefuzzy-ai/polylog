#!/usr/bin/env python
"""Portable launcher for Polylog6.

The script performs light-touch environment checks and then delegates execution
to the canonical entry point in ``Properties.Code.main``. It avoids modifying
system state so the project remains portable across different machines.
"""
from __future__ import annotations

import argparse
import importlib
import os
import sys
from types import ModuleType
from typing import Iterable

REQUIRED_PACKAGES: tuple[str, ...] = (
    "numpy",
    "scipy",
    "celery",
    "prometheus_client",
)


# ---------------------------------------------------------------------------
# Environment helpers
# ---------------------------------------------------------------------------

def _running_inside_virtualenv() -> bool:
    """Return True when the interpreter appears to be inside a virtualenv."""

    if hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    ):
        return True
    return bool(os.environ.get("VIRTUAL_ENV"))


def _warn_if_outside_venv() -> None:
    if _running_inside_virtualenv():
        return

    print(
        "\n[launcher] Warning: running outside a virtual environment.\n"
        "Consider activating your project venv before launching Polylog6 to\n"
        "ensure dependency isolation (e.g. .\\.venv\\Scripts\\activate on Windows).\n"
    )


def _check_dependencies(packages: Iterable[str]) -> None:
    missing: list[str] = []
    for pkg in packages:
        module_name = pkg.replace("-", "_")
        try:
            importlib.import_module(module_name)
        except ImportError:
            missing.append(pkg)

    if missing:
        print(
            "[launcher] Warning: missing optional dependencies: "
            + ", ".join(sorted(missing))
            + "\n  Run `pip install -r requirements.txt` to install them.\n"
        )


# ---------------------------------------------------------------------------
# Delegation into Polylog6 entry point
# ---------------------------------------------------------------------------

def _load_polylog_module() -> ModuleType:
    try:
        return importlib.import_module("Properties.Code.main")
    except ImportError as exc:  # pragma: no cover - fatal path
        print(
            "[launcher] Error: unable to import Properties.Code.main.\n"
            "Ensure you are running from the Polylog6 project root and that\n"
            "dependencies are installed (pip install -r requirements.txt).\n"
            f"Details: {exc}",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc


def _delegate_to_polylog(argv: list[str]) -> int:
    module = _load_polylog_module()
    main_func = getattr(module, "main", None)
    if not callable(main_func):
        print(
            "[launcher] Error: Properties.Code.main.main() is not callable.",
            file=sys.stderr,
        )
        return 1

    original_argv = sys.argv
    sys.argv = [original_argv[0], *argv]
    try:
        result = main_func()
        return int(result) if result is not None else 0
    finally:
        sys.argv = original_argv


# ---------------------------------------------------------------------------
# CLI plumbing
# ---------------------------------------------------------------------------

def _parse_launcher_args(args: list[str]) -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(
        prog="polylog-launcher",
        description="Polylog6 launcher wrapper",
        add_help=False,
    )
    parser.add_argument("--no-env-check", action="store_true", help="Skip venv warning")
    parser.add_argument(
        "--no-deps-check", action="store_true", help="Skip dependency import checks"
    )
    parser.add_argument("-h", "--help", action="store_true", help="Show Polylog help")

    opts, remainder = parser.parse_known_args(args)

    # If the user asked the launcher for help, forward --help to the inner app
    if opts.help and "--help" not in remainder and "-h" not in remainder:
        remainder = ["--help", *remainder]

    return opts, remainder


def main(argv: list[str] | None = None) -> int:
    raw_args = list(sys.argv[1:] if argv is None else argv)
    opts, remainder = _parse_launcher_args(raw_args)

    if not opts.no_env_check:
        _warn_if_outside_venv()
    if not opts.no_deps_check:
        _check_dependencies(REQUIRED_PACKAGES)

    return _delegate_to_polylog(remainder)


if __name__ == "__main__":
    raise SystemExit(main())
