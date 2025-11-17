#!/usr/bin/env python3
"""
Validate Polylog6 repository structure
Ensures all files are in their correct locations after reorganization
"""

import os
from pathlib import Path
import json

def validate_structure():
    """Validate the repository structure"""
    # Use absolute path
    root = Path("c:/Users/Nauti/AppData/Local/Programs/Windsurf/polylog6")
    issues = []
    
    # Expected structure
    expected_dirs = [
        "src/polylog6",
        "src/frontend", 
        "src/desktop",
        "src/shared",
        "tests",
        "docs",
        "scripts",
        "config",
        "data",
        "requirements",
        "storage"
    ]
    
    # Check expected directories exist
    for dir_path in expected_dirs:
        full_path = root / dir_path
        if not full_path.exists():
            issues.append(f"Missing directory: {dir_path}")
        elif not full_path.is_dir():
            issues.append(f"Path exists but is not a directory: {dir_path}")
    
    # Check key files exist
    key_files = [
        "README.md",
        ".gitignore",
        "src/README.md",
        "docs/README.md",
        "tests/README.md",
        "scripts/launcher.py",
        "config/monitoring.yaml"
    ]
    
    for file_path in key_files:
        full_path = root / file_path
        if not full_path.exists():
            issues.append(f"Missing file: {file_path}")
    
    # Check no files in root that should be elsewhere
    root_files = [f.name for f in root.iterdir() if f.is_file()]
    allowed_root_files = {
        "README.md",
        ".gitignore",
        "REORGANIZATION_COMPLETE.md",
        "REORGANIZATION_PLAN.md",
        "package.json",
        "package-lock.json",
        "tsconfig.json",
        "pytest.ini",
        ".coverage",
        "compression_metrics.json",
        "stable_polyforms.jsonl",
        "tier0_dataset.jsonl",
        "tmp_metrics.json",
        "tmp_storage_metrics.json"
    }
    
    unexpected_files = set(root_files) - allowed_root_files
    for file_name in unexpected_files:
        if not file_name.startswith('.') and file_name != "Polylog6":
            issues.append(f"Unexpected file in root: {file_name}")
    
    # Check Python package structure
    pylog6_dir = root / "src" / "polylog6"
    if pylog6_dir.exists():
        init_file = pylog6_dir / "__init__.py"
        if not init_file.exists():
            issues.append("Missing __init__.py in src/polylog6/")
        
        # Check key modules
        modules = ["api", "detection", "simulation", "storage", "monitoring"]
        for module in modules:
            module_dir = pylog6_dir / module
            if module_dir.exists():
                module_init = module_dir / "__init__.py"
                if not module_init.exists():
                    issues.append(f"Missing __init__.py in src/polylog6/{module}/")
    
    # Check frontend structure
    frontend_dir = root / "src" / "frontend"
    if frontend_dir.exists():
        package_json = frontend_dir / "package.json"
        if not package_json.exists():
            issues.append("Missing package.json in src/frontend/")
    
    # Check desktop/Tauri structure
    desktop_dir = root / "src" / "desktop"
    if desktop_dir.exists():
        tauri_dir = desktop_dir / "src-tauri"
        if tauri_dir.exists():
            cargo_toml = tauri_dir / "Cargo.toml"
            if not cargo_toml.exists():
                issues.append("Missing Cargo.toml in src/desktop/src-tauri/")
    
    return issues

def generate_report():
    """Generate validation report"""
    issues = validate_structure()
    
    print("=" * 60)
    print("Polylog6 Repository Structure Validation")
    print("=" * 60)
    
    if not issues:
        print("✅ All checks passed! Repository structure is correct.")
        return 0
    else:
        print(f"❌ Found {len(issues)} issues:")
        print()
        for i, issue in enumerate(issues, 1):
            print(f"{i}. {issue}")
        print()
        return 1

if __name__ == "__main__":
    exit_code = generate_report()
    exit(exit_code)