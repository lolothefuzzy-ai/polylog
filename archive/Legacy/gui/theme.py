"""
Theme management for Polylog GUI.

Implements the Polylog color scheme:
- Dark background
- Primary: Red (#FF0000)
- Secondary: Blue (#0000FF)
- Tertiary: Purple (#800080)
- Accent: Green (#00FF00)
"""



# Color definitions
COLORS = {
    'background': '#1a1a1a',      # Dark background
    'surface': '#2d2d2d',          # Surface
    'primary': '#FF0000',          # Red
    'secondary': '#0000FF',        # Blue
    'tertiary': '#800080',         # Purple
    'accent': '#00FF00',           # Green
    'text': '#FFFFFF',             # White text
    'text_secondary': '#CCCCCC',   # Gray text
    'border': '#444444',           # Border color
}


def apply_theme(widget):
    """Apply Polylog theme to a widget."""
    stylesheet = f"""
    QMainWindow {{
        background-color: {COLORS['background']};
        color: {COLORS['text']};
    }}
    
    QWidget {{
        background-color: {COLORS['background']};
        color: {COLORS['text']};
    }}
    
    QGroupBox {{
        color: {COLORS['text']};
        border: 1px solid {COLORS['border']};
        border-radius: 3px;
        margin-top: 8px;
        padding-top: 8px;
    }}
    
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 3px 0 3px;
    }}
    
    QPushButton {{
        background-color: {COLORS['primary']};
        color: {COLORS['text']};
        border: none;
        border-radius: 3px;
        padding: 5px;
        font-weight: bold;
    }}
    
    QPushButton:hover {{
        background-color: #FF3333;
    }}
    
    QPushButton:pressed {{
        background-color: #CC0000;
    }}
    
    QPushButton:disabled {{
        background-color: #666666;
    }}
    
    QSlider::groove:horizontal {{
        background-color: {COLORS['surface']};
        height: 8px;
        border-radius: 4px;
    }}
    
    QSlider::handle:horizontal {{
        background-color: {COLORS['primary']};
        width: 18px;
        margin: -5px 0;
        border-radius: 9px;
    }}
    
    QSlider::handle:horizontal:hover {{
        background-color: #FF3333;
    }}
    
    QSpinBox {{
        background-color: {COLORS['surface']};
        color: {COLORS['text']};
        border: 1px solid {COLORS['border']};
        border-radius: 3px;
        padding: 2px;
    }}
    
    QSpinBox::up-button, QSpinBox::down-button {{
        background-color: {COLORS['primary']};
        color: {COLORS['text']};
    }}
    
    QLineEdit {{
        background-color: {COLORS['surface']};
        color: {COLORS['text']};
        border: 1px solid {COLORS['border']};
        border-radius: 3px;
        padding: 5px;
    }}
    
    QLineEdit:focus {{
        border: 1px solid {COLORS['primary']};
    }}
    
    QListWidget {{
        background-color: {COLORS['surface']};
        color: {COLORS['text']};
        border: 1px solid {COLORS['border']};
        border-radius: 3px;
    }}
    
    QListWidget::item:selected {{
        background-color: {COLORS['primary']};
        color: {COLORS['text']};
    }}
    
    QListWidget::item:hover {{
        background-color: {COLORS['secondary']};
    }}
    
    QMenuBar {{
        background-color: {COLORS['surface']};
        color: {COLORS['text']};
        border-bottom: 1px solid {COLORS['border']};
    }}
    
    QMenuBar::item:selected {{
        background-color: {COLORS['primary']};
    }}
    
    QMenu {{
        background-color: {COLORS['surface']};
        color: {COLORS['text']};
        border: 1px solid {COLORS['border']};
    }}
    
    QMenu::item:selected {{
        background-color: {COLORS['primary']};
    }}
    
    QToolBar {{
        background-color: {COLORS['surface']};
        border-bottom: 1px solid {COLORS['border']};
    }}
    
    QStatusBar {{
        background-color: {COLORS['surface']};
        color: {COLORS['text']};
        border-top: 1px solid {COLORS['border']};
    }}
    
    QLabel {{
        color: {COLORS['text']};
    }}
    
    QOpenGLWidget {{
        background-color: {COLORS['background']};
    }}
    """
    
    widget.setStyleSheet(stylesheet)
