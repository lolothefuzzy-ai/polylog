#!/usr/bin/env python3
"""
Repository Cleanup Script
Cleans up GitHub repository by removing redundant files and consolidating documentation
"""

import shutil
import os
from pathlib import Path
from typing import List, Set

PROJECT_ROOT = Path(__file__).parent.parent.resolve()

# Colors for output
class Colors:
    OKGREEN = '\033[92m'
    OKCYAN = '\033[96m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_success(msg):
    print(f"{Colors.OKGREEN}✓ {msg}{Colors.ENDC}")

def print_info(msg):
    print(f"{Colors.OKCYAN}ℹ {msg}{Colors.ENDC}")

def print_warning(msg):
    print(f"{Colors.WARNING}⚠ {msg}{Colors.ENDC}")

def print_error(msg):
    print(f"{Colors.FAIL}✗ {msg}{Colors.ENDC}")

def safe_remove(path: Path, description: str = ""):
    """Safely remove a file or directory"""
    try:
        if path.exists():
            if path.is_file():
                path.unlink()
                print_success(f"Removed file: {path.relative_to(PROJECT_ROOT)} {description}")
            elif path.is_dir():
                shutil.rmtree(path)
                print_success(f"Removed directory: {path.relative_to(PROJECT_ROOT)} {description}")
            return True
        else:
            print_warning(f"Path does not exist: {path.relative_to(PROJECT_ROOT)}")
            return False
    except Exception as e:
        print_error(f"Error removing {path.relative_to(PROJECT_ROOT)}: {e}")
        return False

def safe_move(src: Path, dst: Path, description: str = ""):
    """Safely move a file or directory"""
    try:
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            print_success(f"Moved: {src.relative_to(PROJECT_ROOT)} → {dst.relative_to(PROJECT_ROOT)} {description}")
            return True
        else:
            print_warning(f"Source does not exist: {src.relative_to(PROJECT_ROOT)}")
            return False
    except Exception as e:
        print_error(f"Error moving {src.relative_to(PROJECT_ROOT)}: {e}")
        return False

def consolidate_documentation():
    """Consolidate documentation from documentation/ into docs/archive/"""
    print_info("Consolidating documentation...")
    
    docs_dir = PROJECT_ROOT / "docs"
    archive_dir = docs_dir / "archive" / "documentation"
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    documentation_dir = PROJECT_ROOT / "documentation"
    
    if not documentation_dir.exists():
        print_warning("documentation/ directory does not exist")
        return
    
    # Files to keep in main docs (essential)
    essential_docs = {
        "PROJECT_SCOPE_AND_BLOCKERS.md": "Essential project scope",
        "IMPLEMENTATION_ROADMAP.md": "Implementation roadmap"
    }
    
    # Move essential docs to docs/ (if not already there)
    for doc_file, description in essential_docs.items():
        src = documentation_dir / doc_file
        dst = docs_dir / doc_file
        if src.exists() and not dst.exists():
            safe_move(src, dst, f"(essential: {description})")
    
    # Move all other docs to archive
    for doc_file in documentation_dir.iterdir():
        if doc_file.is_file() and doc_file.suffix == ".md":
            if doc_file.name not in essential_docs:
                dst = archive_dir / doc_file.name
                safe_move(doc_file, dst, "(archived)")
    
    # Remove documentation/ directory if empty
    try:
        if documentation_dir.exists() and not any(documentation_dir.iterdir()):
            documentation_dir.rmdir()
            print_success("Removed empty documentation/ directory")
    except:
        pass

def archive_state_files():
    """Move state/ directory to docs/archive/"""
    print_info("Archiving state files...")
    
    state_dir = PROJECT_ROOT / "state"
    archive_dir = PROJECT_ROOT / "docs" / "archive" / "state"
    
    if state_dir.exists():
        archive_dir.mkdir(parents=True, exist_ok=True)
        
        # Move all state files to archive
        for state_file in state_dir.iterdir():
            if state_file.is_file():
                dst = archive_dir / state_file.name
                safe_move(state_file, dst, "(archived)")
        
        # Remove state/ directory if empty
        try:
            if not any(state_dir.iterdir()):
                state_dir.rmdir()
                print_success("Removed empty state/ directory")
        except:
            pass

def handle_cursor_directory():
    """Move cursor/ to .gitignore or archive"""
    print_info("Handling cursor/ directory...")
    
    cursor_dir = PROJECT_ROOT / "cursor"
    archive_dir = PROJECT_ROOT / "docs" / "archive" / "cursor"
    
    if cursor_dir.exists():
        archive_dir.mkdir(parents=True, exist_ok=True)
        
        # Move cursor files to archive
        for cursor_file in cursor_dir.iterdir():
            if cursor_file.is_file():
                dst = archive_dir / cursor_file.name
                safe_move(cursor_file, dst, "(archived)")
        
        # Remove cursor/ directory if empty
        try:
            if not any(cursor_dir.iterdir()):
                cursor_dir.rmdir()
                print_success("Removed empty cursor/ directory")
        except:
            pass

def remove_redundant_gitkraken_docs():
    """Remove redundant GitKraken documentation"""
    print_info("Removing redundant GitKraken docs...")
    
    docs_dir = PROJECT_ROOT / "docs"
    
    # Keep only one GitKraken guide, archive the rest
    gitkraken_docs = [
        "GITKRAKEN_INTEGRATION_GUIDE.md",
        "GITKRAKEN_QUICK_START.md",
        "GITKRAKEN_WORKFLOW_BENEFITS.md",
        "GITKRAKEN_WORKFLOW_INTEGRATION.md",
        "GITKRAKEN_WORKFLOW_SUMMARY.md"
    ]
    
    archive_dir = docs_dir / "archive" / "gitkraken"
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    # Keep GITKRAKEN_QUICK_START.md, archive others
    for doc in gitkraken_docs:
        doc_path = docs_dir / doc
        if doc_path.exists():
            if doc == "GITKRAKEN_QUICK_START.md":
                print_info(f"Keeping {doc} (essential)")
            else:
                dst = archive_dir / doc
                safe_move(doc_path, dst, "(archived)")

def clean_root_level_files():
    """Clean up root-level duplicate/redundant files"""
    print_info("Cleaning root-level files...")
    
    # Root-level files that should be removed or moved
    root_files_to_remove = [
        "connect-to-github.ps1",  # Temporary script
        "push-to-github.ps1",     # Temporary script
    ]
    
    # Check if these files exist and remove them
    for file_name in root_files_to_remove:
        file_path = PROJECT_ROOT / file_name
        if file_path.exists():
            safe_remove(file_path, "(temporary script)")
    
    # Root-level duplicate files in src/
    root_duplicates = [
        "api.generated.ts",
        "App.css",
        "App.jsx",
        "index.css",
        "main.jsx",
    ]
    
    # These should be in src/frontend, not root
    for file_name in root_duplicates:
        file_path = PROJECT_ROOT / file_name
        if file_path.exists():
            # Check if it exists in frontend
            frontend_path = PROJECT_ROOT / "src" / "frontend" / "src" / file_name
            if frontend_path.exists():
                safe_remove(file_path, "(duplicate - exists in src/frontend)")
            else:
                print_warning(f"{file_name} exists in root but not in frontend - keeping for now")

def remove_redundant_docs():
    """Remove redundant documentation files"""
    print_info("Removing redundant documentation...")
    
    docs_dir = PROJECT_ROOT / "docs"
    
    # Redundant docs to remove (consolidated into ARCHITECTURE_UNIFIED.md)
    redundant_docs = [
        "CONSOLIDATED_REFERENCE.md",  # Redundant
        "docs/README.md",  # Not needed if we have main README
    ]
    
    for doc_path_str in redundant_docs:
        doc_path = PROJECT_ROOT / doc_path_str
        if doc_path.exists():
            safe_remove(doc_path, "(redundant - consolidated)")

def update_gitignore():
    """Update .gitignore to exclude cursor/ and state/ directories"""
    print_info("Updating .gitignore...")
    
    gitignore_path = PROJECT_ROOT / ".gitignore"
    
    if not gitignore_path.exists():
        print_warning(".gitignore does not exist, creating it...")
        gitignore_path.write_text("")
    
    gitignore_content = gitignore_path.read_text()
    
    # Add cursor/ and state/ if not already present
    additions = []
    if "cursor/" not in gitignore_content:
        additions.append("cursor/")
    if "state/" not in gitignore_content:
        additions.append("state/")
    if ".last_sync.txt" not in gitignore_content:
        additions.append(".last_sync.txt")
    
    if additions:
        gitignore_content += "\n# IDE-specific and temporary files\n"
        for addition in additions:
            gitignore_content += f"{addition}\n"
        
        gitignore_path.write_text(gitignore_content)
        print_success(f"Updated .gitignore with: {', '.join(additions)}")
    else:
        print_info(".gitignore already has cursor/ and state/")

def remove_empty_directories():
    """Remove empty directories"""
    print_info("Removing empty directories...")
    
    directories_to_check = [
        PROJECT_ROOT / "documentation",
        PROJECT_ROOT / "state",
        PROJECT_ROOT / "cursor",
    ]
    
    for dir_path in directories_to_check:
        if dir_path.exists() and dir_path.is_dir():
            try:
                if not any(dir_path.iterdir()):
                    dir_path.rmdir()
                    print_success(f"Removed empty directory: {dir_path.relative_to(PROJECT_ROOT)}")
            except Exception as e:
                print_warning(f"Could not remove {dir_path.relative_to(PROJECT_ROOT)}: {e}")

def main():
    print(f"{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}Polylog6 Repository Cleanup{Colors.ENDC}")
    print(f"{Colors.BOLD}{'='*60}{Colors.ENDC}\n")
    
    print_info("This script will:")
    print_info("  1. Consolidate documentation from documentation/ into docs/archive/")
    print_info("  2. Archive state/ directory")
    print_info("  3. Archive cursor/ directory")
    print_info("  4. Remove redundant GitKraken docs")
    print_info("  5. Clean up root-level duplicate files")
    print_info("  6. Update .gitignore")
    print_info("  7. Remove empty directories")
    print()
    
    # Run cleanup steps
    consolidate_documentation()
    archive_state_files()
    handle_cursor_directory()
    remove_redundant_gitkraken_docs()
    clean_root_level_files()
    remove_redundant_docs()
    update_gitignore()
    remove_empty_directories()
    
    print(f"\n{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print_success("Repository cleanup complete!")
    print(f"{Colors.BOLD}{'='*60}{Colors.ENDC}\n")
    
    print_info("Next steps:")
    print_info("  1. Review changes: git status")
    print_info("  2. Commit changes: git add -A && git commit -m 'chore: Clean up repository structure'")
    print_info("  3. Push to GitHub: git push")

if __name__ == "__main__":
    main()

