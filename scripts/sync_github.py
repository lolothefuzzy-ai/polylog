#!/usr/bin/env python3
"""
Sync GitHub Repository
Ensures GitHub repository is up to date and removes old code
"""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()

def run_git_command(cmd, check=True):
    """Run git command"""
    try:
        result = subprocess.run(
            ["git"] + cmd,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=check
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode == 0
    except subprocess.CalledProcessError as e:
        return e.stdout.strip(), e.stderr.strip(), False

def check_git_status():
    """Check git status"""
    print("[CHECK] Checking git status...")
    stdout, stderr, success = run_git_command(["status", "--porcelain"])
    
    if stdout:
        print("[INFO] Changes detected:")
        for line in stdout.split('\n'):
            if line.strip():
                print(f"  {line}")
        return True
    else:
        print("[OK] No uncommitted changes")
        return False

def sync_to_github():
    """Sync changes to GitHub"""
    print("=" * 70)
    print("Sync GitHub Repository")
    print("=" * 70)
    
    # Check if we're in a git repo
    stdout, stderr, success = run_git_command(["rev-parse", "--git-dir"], check=False)
    if not success:
        print("[ERROR] Not a git repository")
        print("[INFO] Initialize with: git init")
        return False
    
    # Check status
    has_changes = check_git_status()
    
    if not has_changes:
        print("\n[INFO] No changes to commit")
        print("[INFO] Checking if remote is up to date...")
        
        # Check if remote exists
        stdout, stderr, success = run_git_command(["remote", "-v"], check=False)
        if not stdout:
            print("[WARN] No remote repository configured")
            print("[INFO] Add remote with: git remote add origin <url>")
            return False
        
        # Fetch and check
        print("[INFO] Fetching from remote...")
        stdout, stderr, success = run_git_command(["fetch"], check=False)
        
        # Check if local is ahead/behind
        stdout, stderr, success = run_git_command(["status", "-sb"], check=False)
        if "ahead" in stdout:
            print("[INFO] Local branch is ahead of remote")
            print("[INFO] Run: git push")
        elif "behind" in stdout:
            print("[INFO] Local branch is behind remote")
            print("[INFO] Run: git pull")
        else:
            print("[OK] Repository is up to date")
        
        return True
    
    # Stage all changes
    print("\n[STAGE] Staging all changes...")
    stdout, stderr, success = run_git_command(["add", "-A"])
    if success:
        print("[OK] Changes staged")
    else:
        print(f"[ERROR] Failed to stage: {stderr}")
        return False
    
    # Commit
    print("\n[COMMIT] Committing changes...")
    commit_message = "chore: Project cleanup and integration updates"
    stdout, stderr, success = run_git_command(["commit", "-m", commit_message])
    if success:
        print(f"[OK] Committed: {commit_message}")
    else:
        if "nothing to commit" in stderr.lower():
            print("[INFO] Nothing to commit")
        else:
            print(f"[ERROR] Failed to commit: {stderr}")
            return False
    
    # Push
    print("\n[PUSH] Pushing to GitHub...")
    stdout, stderr, success = run_git_command(["push"], check=False)
    if success:
        print("[OK] Pushed to GitHub")
    else:
        if "no upstream branch" in stderr.lower():
            print("[INFO] No upstream branch set")
            print("[INFO] Set upstream with: git push -u origin main")
        else:
            print(f"[WARN] Push may have failed: {stderr}")
            print("[INFO] Try manually: git push")
    
    return True

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Sync GitHub repository")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("[DRY RUN] Would sync to GitHub")
        check_git_status()
        return
    
    sync_to_github()
    
    print("\n" + "=" * 70)
    print("[SUCCESS] GitHub sync complete!")
    print("=" * 70)

if __name__ == "__main__":
    main()

