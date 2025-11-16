#!/usr/bin/env python3
"""
Organize Current Changes for GitKraken
Groups uncommitted changes into logical commits and creates feature branches
"""

import subprocess
import sys
from pathlib import Path
from typing import List, Dict

PROJECT_ROOT = Path(__file__).parent.parent.resolve()

def get_git_status() -> Dict[str, List[str]]:
    """Get current git status"""
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    
    changes = {
        "modified": [],
        "deleted": [],
        "untracked": []
    }
    
    for line in result.stdout.strip().split('\n'):
        if not line:
            continue
        
        status = line[:2]
        filename = line[3:]
        
        if status.startswith('M'):
            changes["modified"].append(filename)
        elif status.startswith('D'):
            changes["deleted"].append(filename)
        elif status.startswith('??'):
            changes["untracked"].append(filename)
    
    return changes

def categorize_changes(changes: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """Categorize changes into logical groups"""
    categories = {
        "test_results": [],
        "documentation": [],
        "scripts": [],
        "frontend_components": [],
        "frontend_utils": [],
        "frontend_tests": [],
        "backend_api": [],
        "backend_storage": [],
        "backend_generation": [],
        "config": [],
        "other": []
    }
    
    all_files = changes["modified"] + changes["deleted"] + changes["untracked"]
    
    for file in all_files:
        file_path = Path(file)
        
        # Test results
        if "test-results" in str(file_path) or "playwright-report" in str(file_path):
            categories["test_results"].append(file)
        # Documentation
        elif file_path.suffix == ".md" or "docs/" in str(file_path):
            categories["documentation"].append(file)
        # Scripts
        elif "scripts/" in str(file_path):
            categories["scripts"].append(file)
        # Frontend components
        elif "src/frontend/src/components/" in str(file_path):
            categories["frontend_components"].append(file)
        # Frontend utils
        elif "src/frontend/src/utils/" in str(file_path):
            categories["frontend_utils"].append(file)
        # Frontend tests
        elif "src/frontend/tests/" in str(file_path):
            categories["frontend_tests"].append(file)
        # Backend API
        elif "src/polylog6/api/" in str(file_path):
            categories["backend_api"].append(file)
        # Backend storage
        elif "src/polylog6/storage/" in str(file_path):
            categories["backend_storage"].append(file)
        # Backend generation
        elif "src/polylog6/generation/" in str(file_path):
            categories["backend_generation"].append(file)
        # Config
        elif file_path.name in [".gitignore", ".gitmessage", ".gitconfig.local"] or \
             ".github/" in str(file_path) or \
             "playwright.config.js" in str(file_path) or \
             "vite.config.js" in str(file_path):
            categories["config"].append(file)
        else:
            categories["other"].append(file)
    
    return categories

def suggest_branches(categories: Dict[str, List[str]]) -> List[Dict[str, any]]:
    """Suggest branches for categorized changes"""
    suggestions = []
    
    if categories["frontend_tests"]:
        suggestions.append({
            "branch": "test/interactive-workspace-tests",
            "files": categories["frontend_tests"],
            "message": "test(integration): Add interactive workspace monitor and Tier 0 tests",
            "type": "test"
        })
    
    if categories["frontend_components"]:
        suggestions.append({
            "branch": "feature/tier0-display-components",
            "files": categories["frontend_components"],
            "message": "feat(frontend): Add Tier 0 display and visualization components",
            "type": "feature"
        })
    
    if categories["frontend_utils"]:
        suggestions.append({
            "branch": "feature/tier0-utils-integration",
            "files": categories["frontend_utils"],
            "message": "feat(frontend): Add Tier 0 utilities and workspace integration",
            "type": "feature"
        })
    
    if categories["backend_api"]:
        suggestions.append({
            "branch": "feature/tier0-api-endpoints",
            "files": categories["backend_api"],
            "message": "feat(api): Add Tier 0 API endpoints and geometry endpoints",
            "type": "feature"
        })
    
    if categories["backend_storage"]:
        suggestions.append({
            "branch": "feature/tier0-storage-structures",
            "files": categories["backend_storage"],
            "message": "feat(storage): Add Tier 0 recursive structures and atomic chains",
            "type": "feature"
        })
    
    if categories["backend_generation"]:
        suggestions.append({
            "branch": "feature/tier-generation-system",
            "files": categories["backend_generation"],
            "message": "feat(generation): Add Tier 1/2 generation and decomposition",
            "type": "feature"
        })
    
    if categories["scripts"]:
        suggestions.append({
            "branch": "feature/development-scripts",
            "files": categories["scripts"],
            "message": "feat(scripts): Add development and testing scripts",
            "type": "feature"
        })
    
    if categories["documentation"]:
        suggestions.append({
            "branch": "docs/comprehensive-documentation",
            "files": categories["documentation"],
            "message": "docs: Add comprehensive architecture and workflow documentation",
            "type": "docs"
        })
    
    if categories["config"]:
        suggestions.append({
            "branch": "config/gitkraken-setup",
            "files": categories["config"],
            "message": "config: Add GitKraken workflow configuration",
            "type": "config"
        })
    
    return suggestions

def main():
    print("=" * 70)
    print("Organize Current Changes for GitKraken")
    print("=" * 70)
    
    # Get current status
    print("\n[INFO] Analyzing current changes...")
    changes = get_git_status()
    
    total_changes = len(changes["modified"]) + len(changes["deleted"]) + len(changes["untracked"])
    print(f"[INFO] Found {total_changes} total changes:")
    print(f"  - Modified: {len(changes['modified'])}")
    print(f"  - Deleted: {len(changes['deleted'])}")
    print(f"  - Untracked: {len(changes['untracked'])}")
    
    # Categorize changes
    print("\n[INFO] Categorizing changes...")
    categories = categorize_changes(changes)
    
    # Show categories
    print("\n[INFO] Change categories:")
    for category, files in categories.items():
        if files:
            print(f"  - {category}: {len(files)} files")
    
    # Suggest branches
    print("\n[INFO] Suggested branches:")
    suggestions = suggest_branches(categories)
    
    for i, suggestion in enumerate(suggestions, 1):
        print(f"\n{i}. {suggestion['branch']}")
        print(f"   Type: {suggestion['type']}")
        print(f"   Files: {len(suggestion['files'])}")
        print(f"   Message: {suggestion['message']}")
    
    # Test results cleanup
    if categories["test_results"]:
        print(f"\n[WARN] Found {len(categories['test_results'])} test result files")
        print("[INFO] These should be added to .gitignore and removed from tracking")
    
    print("\n" + "=" * 70)
    print("Recommendations:")
    print("=" * 70)
    print("\n1. Clean up test results first:")
    print("   git add .gitignore")
    print("   git commit -m 'chore: Update .gitignore for test results'")
    print("   git rm -r src/frontend/test-results/ src/frontend/playwright-report/data/")
    print("   git commit -m 'chore: Remove test result files'")
    
    print("\n2. Create feature branches for major changes:")
    for suggestion in suggestions:
        if suggestion['type'] in ['feature', 'test']:
            print(f"\n   git checkout -b {suggestion['branch']}")
            print(f"   git add {' '.join(suggestion['files'][:3])}...")
            print(f"   git commit -m \"{suggestion['message']}\"")
    
    print("\n3. Use GitKraken for visual branch management")
    print("4. Create PRs for each feature branch")
    print("5. Merge to develop, then to main")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()

