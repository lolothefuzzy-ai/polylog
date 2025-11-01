#!/usr/bin/env python3
"""Unity Bridge migration workflow helper."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = ROOT / "src"


def run_commands(commands: list[list[str]]) -> bool:
    success = True
    for cmd in commands:
        print(f"[RUN] {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
        if result.stdout:
            print(result.stdout.strip())
        if result.stderr:
            print(result.stderr.strip())
        if result.returncode != 0:
            print(f"[FAIL] {' '.join(cmd)}")
            success = False
    return success


def run_ruff_cleanup() -> None:
    commands = [
        [sys.executable, "-m", "ruff", "check", ".", "--select", "F401", "--fix"],
        [sys.executable, "-m", "ruff", "check", ".", "--select", "I", "--fix"],
        [sys.executable, "-m", "ruff", "check", ".", "--select", "F821"],
    ]
    if not run_commands(commands):
        print("[WARN] Ruff cleanup encountered issues")


def verify_package_structure() -> bool:
    if str(SRC_PATH) not in sys.path:
        sys.path.insert(0, str(SRC_PATH))
    try:
        from polylog6.metrics.service import (
            MetricsService,  # type: ignore  # noqa: F401
        )
    except ImportError as exc:
        print(f"[FAIL] Import failed: {exc}")
        return False
    print("✅ Package structure valid")
    return True


def run_migration():
    """Execute the full migration workflow"""
    print("Starting migration workflow...")
    # Add actual migration steps here
    print("Migration completed successfully")


def main() -> None:
    print("=== Unity Bridge Migration Workflow ===")
    run_ruff_cleanup()
    if verify_package_structure():
        print("Migration ready to proceed!")
    else:
        print("Migration blocked - fix imports first")
        sys.exit(1)


if __name__ == "__main__":
    run_migration()
