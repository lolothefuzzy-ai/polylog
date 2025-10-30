"""
Polylog GUI Launcher

Launches the Polylog Simulator GUI with all integrated systems.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run
from PySide6.QtWidgets import QApplication
from gui.main_window import MainWindow


def main():
    """Launch the Polylog GUI application."""
    print("=" * 60)
    print("POLYLOG SIMULATOR v0.2.0")
    print("=" * 60)
    print()
    
    # Create application
    app = QApplication(sys.argv)
    
    # Set application metadata
    app.setApplicationName("Polylog Simulator")
    app.setApplicationVersion("0.2.0")
    app.setOrganizationName("Polylog Team")
    
    # Create and show main window
    print("Initializing main window...")
    window = MainWindow()
    window.show()
    
    print()
    print("=" * 60)
    print("GUI READY - Press Ctrl+Q to quit")
    print("=" * 60)
    print()
    
    # Run event loop
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
