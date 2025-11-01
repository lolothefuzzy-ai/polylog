"""
Cleanup Script for Polylog

Removes temporary files and caches:
- Compiled Python files (.pyc)
- __pycache__ directories
- Demo output directories (optional)
- Log files (optional)

Usage:
    python cleanup.py              # Remove caches only
    python cleanup.py --all        # Remove caches and demo outputs
    python cleanup.py --logs       # Also remove log files
"""
import argparse
import os
import shutil
import sys


def remove_pycache(root_dir: str, verbose: bool = True) -> int:
    """Remove all __pycache__ directories and .pyc files."""
    removed_count = 0
    
    # Remove __pycache__ directories
    for dirpath, dirnames, filenames in os.walk(root_dir):
        if '__pycache__' in dirnames:
            cache_dir = os.path.join(dirpath, '__pycache__')
            try:
                shutil.rmtree(cache_dir)
                if verbose:
                    print(f"Removed: {cache_dir}")
                removed_count += 1
            except Exception as e:
                print(f"Warning: Could not remove {cache_dir}: {e}")
    
    # Remove standalone .pyc files
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith('.pyc'):
                pyc_file = os.path.join(dirpath, filename)
                try:
                    os.remove(pyc_file)
                    if verbose:
                        print(f"Removed: {pyc_file}")
                    removed_count += 1
                except Exception as e:
                    print(f"Warning: Could not remove {pyc_file}: {e}")
    
    return removed_count


def remove_demo_outputs(root_dir: str, verbose: bool = True) -> int:
    """Remove demo output directories."""
    removed_count = 0
    
    demo_dirs = [
        'demo_thumbnails',
        'demo_library',
    ]
    
    for demo_dir in demo_dirs:
        full_path = os.path.join(root_dir, demo_dir)
        if os.path.exists(full_path):
            try:
                shutil.rmtree(full_path)
                if verbose:
                    print(f"Removed: {full_path}")
                removed_count += 1
            except Exception as e:
                print(f"Warning: Could not remove {full_path}: {e}")
    
    return removed_count


def remove_logs(root_dir: str, verbose: bool = True) -> int:
    """Remove log files."""
    removed_count = 0
    
    # Remove .log files
    for filename in os.listdir(root_dir):
        if filename.endswith('.log'):
            log_file = os.path.join(root_dir, filename)
            try:
                os.remove(log_file)
                if verbose:
                    print(f"Removed: {log_file}")
                removed_count += 1
            except Exception as e:
                print(f"Warning: Could not remove {log_file}: {e}")
    
    # Optionally remove .jsonl log files
    log_files = ['provenance_log.jsonl']
    for log_file in log_files:
        full_path = os.path.join(root_dir, log_file)
        if os.path.exists(full_path):
            try:
                os.remove(full_path)
                if verbose:
                    print(f"Removed: {full_path}")
                removed_count += 1
            except Exception as e:
                print(f"Warning: Could not remove {full_path}: {e}")
    
    return removed_count


def main():
    parser = argparse.ArgumentParser(
        description="Cleanup temporary files and caches in Polylog project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cleanup.py              # Clean caches only
  python cleanup.py --all        # Clean caches and demo outputs
  python cleanup.py --logs       # Also remove log files
  python cleanup.py --all --logs # Full cleanup
        """
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='Remove demo outputs in addition to caches'
    )
    
    parser.add_argument(
        '--logs',
        action='store_true',
        help='Also remove log files'
    )
    
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Quiet mode (minimal output)'
    )
    
    args = parser.parse_args()
    verbose = not args.quiet
    
    # Get project root directory
    root_dir = os.path.dirname(os.path.abspath(__file__))
    
    if verbose:
        print(f"\nCleaning Polylog project at: {root_dir}\n")
        print("=" * 60)
    
    total_removed = 0
    
    # Always remove caches
    if verbose:
        print("\nRemoving Python caches...")
    cache_count = remove_pycache(root_dir, verbose)
    total_removed += cache_count
    if verbose:
        print(f"✓ Removed {cache_count} cache items")
    
    # Remove demo outputs if requested
    if args.all:
        if verbose:
            print("\nRemoving demo outputs...")
        demo_count = remove_demo_outputs(root_dir, verbose)
        total_removed += demo_count
        if verbose:
            print(f"✓ Removed {demo_count} demo directories")
    
    # Remove logs if requested
    if args.logs:
        if verbose:
            print("\nRemoving log files...")
        log_count = remove_logs(root_dir, verbose)
        total_removed += log_count
        if verbose:
            print(f"✓ Removed {log_count} log files")
    
    if verbose:
        print("\n" + "=" * 60)
        print(f"\nCleanup complete! Removed {total_removed} items total.\n")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
