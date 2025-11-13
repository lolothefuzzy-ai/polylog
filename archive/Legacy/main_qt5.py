"""
Entry point for the Polylog application.
Launches the PyQt5-based GUI.
"""

import sys

from PyQt5.QtWidgets import QApplication

from gui.main_window_qt5 import MainWindow


def main():
    """Launch the application GUI."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()