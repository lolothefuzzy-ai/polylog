"""
Theme Manager for Polylog Desktop App
Applies native Qt dark theme with bold colors (red, blue, purple)
"""
from pathlib import Path

from PySide6 import QtWidgets


def load_theme(app: QtWidgets.QApplication) -> None:
    """
    Load and apply the dark theme stylesheet to the application.
    
    Usage:
        from theme_manager import load_theme
        
        app = QtWidgets.QApplication(sys.argv)
        load_theme(app)  # Apply theme before showing windows
        
    Args:
        app: QApplication instance
    """
    theme_path = Path(__file__).parent / "theme.qss"
    
    if not theme_path.exists():
        print(f"Warning: Theme file not found at {theme_path}")
        return
    
    with open(theme_path, 'r') as f:
        stylesheet = f.read()
    
    app.setStyle('Fusion')  # Use Fusion style as base for better cross-platform support
    app.setStyleSheet(stylesheet)
    print("✓ Dark theme applied successfully")


def set_button_color(button: QtWidgets.QPushButton, color_type: str) -> None:
    """
    Set button color type. Useful for dynamic button styling.
    
    Args:
        button: QPushButton to style
        color_type: One of 'primary' (red), 'secondary' (blue), 
                   'exploration' (purple), 'stop' (dark red)
    """
    color_map = {
        'primary': 'addButton',
        'secondary': 'secondaryButton',
        'evaluation': 'evaluateButton',
        'exploration': 'explorationButton',
        'stop': 'stopButton',
    }
    
    object_name = color_map.get(color_type)
    if object_name:
        button.setObjectName(object_name)


def set_label_color(label: QtWidgets.QLabel, label_type: str) -> None:
    """
    Set label color type.
    
    Args:
        label: QLabel to style
        label_type: One of 'title' or 'section'
    """
    if label_type == 'title':
        label.setObjectName('titleLabel')
    elif label_type == 'section':
        label.setObjectName('sectionLabel')
