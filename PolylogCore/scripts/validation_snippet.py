"""Quick validation for Polylog6 metrics package structure."""

import importlib.util


def main() -> None:
    spec = importlib.util.find_spec("polylog6.metrics.service")
    if spec is None:
        print("❌ Import failed: module not found")
        return

    module = spec.loader.load_module() if spec.loader else None  # type: ignore[attr-defined]
    if module is None:
        print("❌ Import failed: loader returned None")
        return

    if hasattr(module, "MetricsService"):
        print("✅ Package structure valid")
    else:
        print("⚠️ MetricsService missing in module")


if __name__ == "__main__":
    main()
