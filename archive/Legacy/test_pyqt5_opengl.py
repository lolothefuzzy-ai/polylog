import sys

from OpenGL.GL import GL_COLOR_BUFFER_BIT, glClear, glClearColor, glViewport
from PyQt5.QtWidgets import QApplication, QMainWindow, QOpenGLWidget


class MinimalGLWidget(QOpenGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
    def initializeGL(self):
        glClearColor(0.2, 0.3, 0.3, 1.0)
        
    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT)
        
    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt5 OpenGL Test")
        self.setGeometry(100, 100, 800, 600)
        
        # Create OpenGL Widget
        self.glWidget = MinimalGLWidget(self)
        self.setCentralWidget(self.glWidget)

if __name__ == '__main__':
    print("Initializing PyQt5 OpenGL test...")
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    print("Window created successfully. If you see a colored window, OpenGL is working.")
    sys.exit(app.exec_())