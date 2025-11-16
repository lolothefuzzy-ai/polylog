#!/usr/bin/env python3
"""
Set up GitKraken Workflow
Configures Git for GitKraken-friendly workflow
"""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()

def setup_git_config():
    """Set up Git configuration for GitKraken workflow"""
    print("[SETUP] Configuring Git for GitKraken workflow...")
    
    configs = [
        ("commit.template", ".gitmessage"),
        ("init.defaultBranch", "main"),
        ("pull.rebase", "false"),
        ("push.default", "simple"),
        ("push.autoSetupRemote", "true"),
    ]
    
    for key, value in configs:
        try:
            subprocess.run(
                ["git", "config", key, value],
                cwd=PROJECT_ROOT,
                check=True
            )
            print(f"  [OK] Set {key} = {value}")
        except subprocess.CalledProcessError as e:
            print(f"  [WARN] Failed to set {key}: {e}")
    
    # Set commit template if it exists
    template_file = PROJECT_ROOT / ".gitmessage"
    if template_file.exists():
        try:
            subprocess.run(
                ["git", "config", "commit.template", ".gitmessage"],
                cwd=PROJECT_ROOT,
                check=True
            )
            print("  [OK] Commit template configured")
        except:
            pass

def create_develop_branch():
    """Create develop branch if it doesn't exist"""
    print("\n[SETUP] Checking for develop branch...")
    
    result = subprocess.run(
        ["git", "branch", "--list", "develop"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    
    if "develop" in result.stdout:
        print("  [OK] Develop branch already exists")
    else:
        print("  [INFO] Creating develop branch...")
        try:
            subprocess.run(
                ["git", "checkout", "-b", "develop"],
                cwd=PROJECT_ROOT,
                check=True
            )
            print("  [OK] Created develop branch")
            
            # Switch back to main
            subprocess.run(
                ["git", "checkout", "main"],
                cwd=PROJECT_ROOT,
                check=True
            )
            print("  [OK] Switched back to main")
        except subprocess.CalledProcessError as e:
            print(f"  [WARN] Failed to create develop branch: {e}")

def setup_gitignore():
    """Ensure test results are in .gitignore"""
    print("\n[SETUP] Checking .gitignore...")
    
    gitignore_file = PROJECT_ROOT / ".gitignore"
    if not gitignore_file.exists():
        print("  [WARN] .gitignore not found")
        return
    
    content = gitignore_file.read_text()
    
    # Check for test results patterns
    patterns = [
        "test-results/",
        "playwright-report/",
        ".gitkraken/",
        "*.gkuser"
    ]
    
    missing = []
    for pattern in patterns:
        if pattern not in content:
            missing.append(pattern)
    
    if missing:
        print(f"  [INFO] Adding missing patterns to .gitignore...")
        with open(gitignore_file, "a") as f:
            f.write("\n# GitKraken\n")
            for pattern in missing:
                f.write(f"{pattern}\n")
        print("  [OK] Updated .gitignore")
    else:
        print("  [OK] .gitignore already configured")

def main():
    print("=" * 70)
    print("GitKraken Workflow Setup")
    print("=" * 70)
    
    setup_git_config()
    create_develop_branch()
    setup_gitignore()
    
    print("\n" + "=" * 70)
    print("[SUCCESS] GitKraken workflow configured!")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Install GitKraken: https://www.gitkraken.com/")
    print("2. Open repository in GitKraken")
    print("3. Connect GitHub integration (optional)")
    print("4. Start using GitKraken for visual Git management")
    print("\nSee docs/GITKRAKEN_QUICK_START.md for detailed guide")

if __name__ == "__main__":
    main()

