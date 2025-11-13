"""
Polylog GUI Application Launcher.

Creates and runs the PySide6 Qt application with the main window.
"""

import sys

from PySide6.QtWidgets import QApplication

from gui.main_window import MainWindow


def run_gui():
    """Launch the Polylog GUI application."""
    app = QApplication(sys.argv)
    
    # Set application metadata
    app.setApplicationName("Polylog Simulator")
    app.setApplicationVersion("0.1.0")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Run event loop
    return app.exec()


if __name__ == '__main__':
    sys.exit(run_gui())
