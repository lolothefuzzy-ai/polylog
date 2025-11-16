"""Check availability of detection + monitoring dependencies."""

from __future__ import annotations

import importlib
from dataclasses import dataclass


@dataclass(frozen=True)
class Dependency:
    module: str
    package: str
    required: bool = True
    note: str | None = None


HARD_DEPENDENCIES: tuple[Dependency, ...] = (
    Dependency(module="cv2", package="opencv-python"),
    Dependency(module="numpy", package="numpy"),
    Dependency(module="scipy", package="scipy"),
    Dependency(module="yaml", package="pyyaml"),
)

SOFT_DEPENDENCIES: tuple[Dependency, ...] = (
    Dependency(
        module="skimage",
        package="scikit-image",
        required=False,
        note="Enables Felzenszwalb pre-segmentation",
    ),
    Dependency(
        module="trimesh",
        package="trimesh",
        required=False,
        note="Improves topology hull accuracy",
    ),
    Dependency(
        module="skgeom",
        package="scikit-geometry",
        required=False,
        note="Optional CGAL-backed hull backend",
    ),
)

def _check(dependencies: tuple[Dependency, ...], *, heading: str) -> tuple[list[str], list[str]]:
    print(f"\n=== {heading} ===")
    missing: list[str] = []
    versions: list[str] = []

    for dep in dependencies:
        try:
            module = importlib.import_module(dep.module)
        except ImportError:
            print(f"✗ {dep.module} (pip install {dep.package})")
            if dep.required:
                missing.append(dep.package)
            else:
                versions.append(dep.package)
            if dep.note:
                print(f"  ↳ {dep.note}")
        else:
            version = getattr(module, "__version__", "unknown")
            print(f"✓ {dep.module} {version}")
            if dep.note:
                print(f"  ↳ {dep.note}")

    return missing, versions


def main() -> int:
    hard_missing, _ = _check(HARD_DEPENDENCIES, heading="Required")
    soft_missing, _ = _check(SOFT_DEPENDENCIES, heading="Optional")

    if hard_missing:
        print(f"\nInstall required packages: pip install {' '.join(sorted(set(hard_missing)))}")
        if soft_missing:
            print(f"Optional enhancements: pip install {' '.join(sorted(set(soft_missing)))}")
        return 1

    if soft_missing:
        print(
            f"\nOptional enhancements available: pip install {' '.join(sorted(set(soft_missing)))}"
        )

    print("\n✓ All required dependencies available")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
