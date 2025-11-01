"""Entry point for Polylog's GUI application using PyQt5.

Contains the top-level code for initializing and running the GUI.
Uses PyQt5 for the UI framework with OpenGL support.
"""

import os
import sys

from PyQt5.QtOpenGL import QGLFormat
from PyQt5.QtWidgets import QApplication, QMessageBox

from gui.main_window_qt5 import MainWindow

# Set environment variable to enable software OpenGL if needed
if os.environ.get('POLYLOG_SOFTWARE_OPENGL'):
    os.environ['QT_OPENGL'] = 'software'


def main():
    """Initialize and run the PyQt5 GUI."""
    try:
        # Check OpenGL support before creating app
        fmt = QGLFormat.defaultFormat()
        if not fmt.hasOpenGL():
            QMessageBox.critical(None, "Error", 
                               "OpenGL support not available. Please check your graphics drivers.")
            return 1
            
        app = QApplication(sys.argv)
        app.setApplicationName("Polylog Designer")
        app.setOrganizationName("Polylog")
        
        # Set OpenGL format for the application
        fmt.setVersion(2, 1)  # OpenGL 2.1 for compatibility
        fmt.setProfile(QGLFormat.NoProfile)
        fmt.setSampleBuffers(True)
        QGLFormat.setDefaultFormat(fmt)
        
        try:
            window = MainWindow()
            window.show()
            
            # Check if window's OpenGL context is valid
            if not window.viewport.isValid():
                raise RuntimeError("Failed to create OpenGL context")
                
            return app.exec_()
            
        except Exception as e:
            QMessageBox.critical(None, "Error",
                               f"Failed to initialize application: {str(e)}\n\n"
                               "Try setting POLYLOG_SOFTWARE_OPENGL=1 environment variable\n"
                               "if you're having graphics driver issues.")
            return 1
            
    except Exception as e:
        QMessageBox.critical(None, "Critical Error",
                           f"Failed to start application: {str(e)}")
        return 1


if __name__ == '__main__':
    sys.exit(main())