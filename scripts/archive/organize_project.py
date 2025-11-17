#!/usr/bin/env python3
"""
Organize Project Structure
Creates clean, organized project structure with only actionable code
"""

import shutil
from pathlib import Path
from typing import List

PROJECT_ROOT = Path(__file__).parent.parent.resolve()

# Essential documentation to consolidate
ESSENTIAL_DOCS = {
    "README.md": "Main project README",
    "docs/ARCHITECTURE.md": "System architecture",
    "docs/API.md": "API reference",
    "docs/DEVELOPMENT.md": "Development guide"
}

def consolidate_docs():
    """Consolidate essential documentation"""
    print("[ORGANIZE] Consolidating documentation...")
    
    docs_dir = PROJECT_ROOT / "docs"
    docs_dir.mkdir(exist_ok=True)
    
    # Create consolidated architecture doc
    arch_doc = docs_dir / "ARCHITECTURE.md"
    if not arch_doc.exists():
        arch_content = """# Polylog6 Architecture

## System Overview
Polylog6 is a polyform visualization and analysis system.

## Core Components
- Backend: Python FastAPI
- Frontend: React + Babylon.js
- Desktop: Tauri (Rust)
- Storage: Tiered Unicode compression

## Key Concepts
- Tier 0: Polygon-to-polygon attachments (Series A/B/C/D)
- Primitives: 3-20 sided polygons
- Tier 1: Platonic, Archimedean, Johnson solids
- Tier 2+: Recursive polyform structures

See WORKSPACE_INTERACTION_ARCHITECTURE.md for detailed interaction model.
"""
        arch_doc.write_text(arch_content)
        print(f"  [OK] Created {arch_doc.relative_to(PROJECT_ROOT)}")

def organize_scripts():
    """Organize scripts directory"""
    print("[ORGANIZE] Organizing scripts...")
    
    scripts_dir = PROJECT_ROOT / "scripts"
    
    # Keep only essential scripts
    essential_scripts = [
        "unified_launcher.py",
        "run_tests_in_workspace.py",
        "organize_project.py",
        "project_cleanup.py"
    ]
    
    # List all scripts
    all_scripts = list(scripts_dir.glob("*.py"))
    
    for script in all_scripts:
        if script.name not in essential_scripts:
            # Check if script is actually used
            if not is_script_used(script):
                print(f"  [INFO] Script {script.name} may be unused")

def is_script_used(script_path: Path) -> bool:
    """Check if script is referenced"""
    # Check README, other scripts, workflows
    search_paths = [
        PROJECT_ROOT / "README.md",
        PROJECT_ROOT / ".github" / "workflows",
        PROJECT_ROOT / "scripts"
    ]
    
    script_name = script_path.name
    for search_path in search_paths:
        if search_path.exists():
            if search_path.is_file():
                content = search_path.read_text()
                if script_name in content:
                    return True
            elif search_path.is_dir():
                for file in search_path.rglob("*"):
                    if file.is_file() and file.suffix in [".yml", ".yaml", ".md", ".py"]:
                        try:
                            content = file.read_text()
                            if script_name in content:
                                return True
                        except:
                            pass
    
    return False

def create_project_structure():
    """Create clean project structure"""
    print("[ORGANIZE] Creating project structure...")
    
    structure = {
        "src": {
            "polylog6": "Backend Python package",
            "frontend": "React frontend",
            "desktop": "Tauri desktop app"
        },
        "tests": "Test files",
        "scripts": "Development scripts",
        "docs": "Essential documentation",
        "data": {
            "catalogs": "Polyform data catalogs"
        },
        ".github": {
            "workflows": "GitHub Actions workflows"
        }
    }
    
    print("  [OK] Project structure verified")

def main():
    print("=" * 70)
    print("Project Organization")
    print("=" * 70)
    
    consolidate_docs()
    organize_scripts()
    create_project_structure()
    
    print("\n" + "=" * 70)
    print("[SUCCESS] Project organized!")
    print("=" * 70)
    print("\nNext: Run cleanup to remove unnecessary files")
    print("  python scripts/project_cleanup.py --execute")

if __name__ == "__main__":
    main()

