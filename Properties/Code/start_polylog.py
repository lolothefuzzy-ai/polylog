"""
Enhanced Startup Script for Polylog Simulator GUI

Features:
- Dependency checking
- Helpful error messages
- Environment validation
- Auto-launch GUI if all checks pass
"""
import sys
import os

def print_header():
    """Print welcome header."""
    print("=" * 60)
    print("  Polylog Simulator GUI v0.2.0")
    print("  Integrated Polyform Design & Assembly Tool")
    print("=" * 60)
    print()

def check_python_version():
    """Check if Python version is compatible."""
    print("Checking Python version...", end=" ")
    version = sys.version_info
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ FAILED")
        print(f"  Found: Python {version.major}.{version.minor}.{version.micro}")
        print("  Required: Python 3.8 or higher")
        print("  Please upgrade your Python installation.")
        return False
    
    print(f"✓ OK (Python {version.major}.{version.minor}.{version.micro})")
    return True

def check_dependency(package_name, import_name=None):
    """Check if a package is installed."""
    if import_name is None:
        import_name = package_name
    
    print(f"Checking {package_name}...", end=" ")
    
    try:
        __import__(import_name)
        print("✓ OK")
        return True
    except ImportError:
        print("❌ MISSING")
        return False

def check_dependencies():
    """Check all required dependencies."""
    print("\nChecking dependencies:")
    print("-" * 60)
    
    all_ok = True
    missing = []
    
    # Core dependencies
    deps = [
        ("PySide6", "PySide6"),
        ("PyOpenGL", "OpenGL"),
        ("NumPy", "numpy"),
    ]
    
    for pkg_name, import_name in deps:
        if not check_dependency(pkg_name, import_name):
            all_ok = False
            missing.append(pkg_name)
    
    print("-" * 60)
    
    if not all_ok:
        print("\n⚠️  Missing dependencies detected!")
        print("\nTo install missing packages, run:")
        print(f"  pip install {' '.join(missing)}")
        print("\nOr install all at once:")
        print("  pip install PySide6 PyOpenGL numpy")
        return False
    
    print("\n✓ All dependencies satisfied!")
    return True

def check_project_structure():
    """Check if required project files exist."""
    print("\nChecking project structure:")
    print("-" * 60)
    
    required_files = [
        "gui/main_window.py",
        "gui/viewport.py",
        "generator_protocol.py",
        "unified_bonding_system.py",
        "hinge_manager.py",
        "collision_validator.py",
        "stable_library.py",
    ]
    
    all_ok = True
    
    for file_path in required_files:
        exists = os.path.exists(file_path)
        status = "✓" if exists else "❌"
        print(f"  {status} {file_path}")
        if not exists:
            all_ok = False
    
    print("-" * 60)
    
    if not all_ok:
        print("\n⚠️  Some project files are missing!")
        print("Make sure you're running from the project root directory.")
        return False
    
    print("\n✓ Project structure is complete!")
    return True

def show_quick_start():
    """Show quick start instructions."""
    print("\n" + "=" * 60)
    print("  Quick Start Guide")
    print("=" * 60)
    print()
    print("1. Select a generator (top right panel)")
    print("2. Press 'G' to generate polyforms")
    print("3. Press 'B' to discover bonds")
    print("4. Create bonds from the candidate list")
    print("5. Press 'Ctrl+T' to validate assembly")
    print("6. Press 'Ctrl+S' to save your work")
    print()
    print("Press 'F1' in the GUI for full keyboard shortcuts!")
    print()
    print("Documentation:")
    print("  - GUI_README.md - Full user guide")
    print("  - QUICK_REFERENCE.md - Cheat sheet")
    print("  - Press F1 in GUI - Keyboard shortcuts")
    print("=" * 60)

def launch_gui():
    """Launch the GUI application."""
    print("\n🚀 Launching Polylog Simulator GUI...")
    print()
    
    try:
        from gui.app import run_gui
        run_gui()
    except ImportError:
        # Fallback to direct launch
        try:
            from PySide6.QtWidgets import QApplication
            from gui.main_window import MainWindow
            
            app = QApplication(sys.argv)
            window = MainWindow()
            window.show()
            
            print("✓ GUI launched successfully!")
            print("  Close this window or press Ctrl+C to exit.")
            print()
            
            sys.exit(app.exec())
        except Exception as e:
            print(f"\n❌ Failed to launch GUI: {e}")
            print("\nTry running directly:")
            print("  python launch_gui.py")
            return False
    
    return True

def main():
    """Main startup routine."""
    print_header()
    
    # Step 1: Check Python version
    if not check_python_version():
        return 1
    
    # Step 2: Check dependencies
    if not check_dependencies():
        return 1
    
    # Step 3: Check project structure
    if not check_project_structure():
        return 1
    
    # Step 4: Show quick start
    show_quick_start()
    
    # Step 5: Launch GUI
    print("\nPress Enter to launch GUI (or Ctrl+C to cancel)...")
    try:
        input()
    except KeyboardInterrupt:
        print("\n\nStartup cancelled.")
        return 0
    
    if not launch_gui():
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
