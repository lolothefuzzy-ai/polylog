#!/usr/bin/env python3
"""
GitKraken Workflow Helper
Utilities to integrate GitKraken features into our development workflow
"""

import subprocess
import sys
from pathlib import Path
from typing import Optional, List
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.resolve()

class GitKrakenWorkflow:
    """Helper class for GitKraken workflow integration"""
    
    def __init__(self):
        self.project_root = PROJECT_ROOT
    
    def create_feature_branch(self, feature_name: str, issue_number: Optional[int] = None) -> bool:
        """
        Create a feature branch with GitKraken-friendly naming
        
        Args:
            feature_name: Name of the feature (e.g., 'tier0-integration')
            issue_number: Optional issue number to link
        
        Returns:
            True if successful
        """
        branch_name = f"feature/{feature_name}"
        if issue_number:
            branch_name = f"feature/{feature_name}-#{issue_number}"
        
        try:
            # Check current branch
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            current_branch = result.stdout.strip()
            
            # Create and checkout branch
            subprocess.run(
                ["git", "checkout", "-b", branch_name],
                cwd=self.project_root,
                check=True
            )
            
            print(f"[OK] Created feature branch: {branch_name}")
            if issue_number:
                print(f"[INFO] Linked to issue #{issue_number}")
            
            return True
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Failed to create branch: {e}")
            return False
    
    def create_hotfix_branch(self, fix_description: str, issue_number: Optional[int] = None) -> bool:
        """Create a hotfix branch"""
        branch_name = f"hotfix/{fix_description}"
        if issue_number:
            branch_name = f"hotfix/{fix_description}-#{issue_number}"
        
        try:
            subprocess.run(
                ["git", "checkout", "-b", branch_name],
                cwd=self.project_root,
                check=True
            )
            print(f"[OK] Created hotfix branch: {branch_name}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Failed to create branch: {e}")
            return False
    
    def commit_with_message(self, message: str, issue_number: Optional[int] = None, 
                          commit_type: str = "feat") -> bool:
        """
        Create a commit with conventional commit message format
        
        Args:
            message: Commit message
            issue_number: Optional issue number
            commit_type: Type of commit (feat, fix, docs, test, etc.)
        """
        full_message = f"{commit_type}: {message}"
        if issue_number:
            full_message += f"\n\nFixes #{issue_number}"
        
        try:
            subprocess.run(
                ["git", "commit", "-m", full_message],
                cwd=self.project_root,
                check=True
            )
            print(f"[OK] Committed: {full_message}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Failed to commit: {e}")
            return False
    
    def get_branch_info(self) -> dict:
        """Get current branch information"""
        try:
            branch_result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            branch = branch_result.stdout.strip()
            
            status_result = subprocess.run(
                ["git", "status", "--short"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            changes = status_result.stdout.strip().split('\n') if status_result.stdout.strip() else []
            
            return {
                "branch": branch,
                "changes": changes,
                "has_changes": len(changes) > 0
            }
        except Exception as e:
            return {"error": str(e)}
    
    def suggest_branch_name(self, feature_type: str, description: str) -> str:
        """Suggest a branch name based on feature type and description"""
        # Clean description
        clean_desc = description.lower().replace(" ", "-").replace("_", "-")
        clean_desc = ''.join(c for c in clean_desc if c.isalnum() or c == '-')
        
        # Map feature types
        type_map = {
            "feature": "feature",
            "fix": "fix",
            "bug": "fix",
            "hotfix": "hotfix",
            "test": "test",
            "docs": "docs",
            "refactor": "refactor",
            "perf": "perf"
        }
        
        prefix = type_map.get(feature_type.lower(), "feature")
        return f"{prefix}/{clean_desc}"
    
    def create_pr_template(self, title: str, description: str, issue_number: Optional[int] = None) -> str:
        """Generate a PR template"""
        template = f"""# {title}

## Description
{description}

"""
        if issue_number:
            template += f"Fixes #{issue_number}\n\n"
        
        template += """## Changes
- [ ] Change 1
- [ ] Change 2

## Testing
- [ ] Tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings
"""
        return template

def main():
    """CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description="GitKraken Workflow Helper")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Create feature branch
    feature_parser = subparsers.add_parser("feature", help="Create feature branch")
    feature_parser.add_argument("name", help="Feature name")
    feature_parser.add_argument("--issue", type=int, help="Issue number")
    
    # Create hotfix branch
    hotfix_parser = subparsers.add_parser("hotfix", help="Create hotfix branch")
    hotfix_parser.add_argument("description", help="Fix description")
    hotfix_parser.add_argument("--issue", type=int, help="Issue number")
    
    # Commit
    commit_parser = subparsers.add_parser("commit", help="Create commit")
    commit_parser.add_argument("message", help="Commit message")
    commit_parser.add_argument("--type", default="feat", help="Commit type")
    commit_parser.add_argument("--issue", type=int, help="Issue number")
    
    # Status
    status_parser = subparsers.add_parser("status", help="Show branch status")
    
    # Suggest branch name
    suggest_parser = subparsers.add_parser("suggest", help="Suggest branch name")
    suggest_parser.add_argument("type", help="Feature type")
    suggest_parser.add_argument("description", help="Description")
    
    args = parser.parse_args()
    
    workflow = GitKrakenWorkflow()
    
    if args.command == "feature":
        workflow.create_feature_branch(args.name, args.issue)
    elif args.command == "hotfix":
        workflow.create_hotfix_branch(args.description, args.issue)
    elif args.command == "commit":
        workflow.commit_with_message(args.message, args.issue, args.type)
    elif args.command == "status":
        info = workflow.get_branch_info()
        print(f"Current branch: {info.get('branch', 'unknown')}")
        print(f"Has changes: {info.get('has_changes', False)}")
        if info.get('changes'):
            print("\nChanges:")
            for change in info['changes']:
                print(f"  {change}")
    elif args.command == "suggest":
        suggestion = workflow.suggest_branch_name(args.type, args.description)
        print(f"Suggested branch name: {suggestion}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

