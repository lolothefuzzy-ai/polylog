"""
Professional UI Styling Module for Polylog
Provides modern, polished components with clean aesthetics
"""

from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtCore import Qt

# ==================== PROFESSIONAL STYLESHEET ====================
PROFESSIONAL_STYLESHEET = """
/* Main Window */
QMainWindow {
    background-color: #0a0e27;
    border: none;
}

/* Central Widget */
QWidget {
    background-color: #0a0e27;
}

/* Groupbox */
QGroupBox {
    background-color: #151a2b;
    border: 1px solid #2a3550;
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 8px;
    font-weight: bold;
    color: #e0e6ff;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0px 4px;
}

/* Sliders */
QSlider::groove:horizontal {
    background-color: #1a2540;
    height: 6px;
    border-radius: 3px;
    border: 1px solid #2a3550;
}

QSlider::handle:horizontal {
    background-color: #ff3333;
    width: 16px;
    margin: -5px 0px;
    border-radius: 8px;
    border: 2px solid #ff5555;
    margin-left: -8px;
    margin-right: -8px;
}

QSlider::handle:horizontal:hover {
    background-color: #ff5555;
    border: 2px solid #ff7777;
}

QSlider::handle:horizontal:pressed {
    background-color: #cc2222;
}

QSlider::sub-page:horizontal {
    background-color: #ff3333;
    border-radius: 3px;
}

/* Push Buttons */
QPushButton {
    background-color: #ff3333;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 10px 20px;
    font-weight: bold;
    font-size: 12px;
    min-width: 80px;
    min-height: 32px;
}

QPushButton:hover {
    background-color: #ff5555;
    padding: 10px 20px;
}

QPushButton:pressed {
    background-color: #cc2222;
}

QPushButton:disabled {
    background-color: #4a5570;
    color: #888888;
}

/* Secondary Buttons */
QPushButton#secondaryButton {
    background-color: #4169e1;
}

QPushButton#secondaryButton:hover {
    background-color: #5a7fff;
}

QPushButton#secondaryButton:pressed {
    background-color: #3050c0;
}

/* Exploration Buttons */
QPushButton#explorationButton {
    background-color: #9932cc;
}

QPushButton#explorationButton:hover {
    background-color: #bb44ff;
}

QPushButton#explorationButton:pressed {
    background-color: #7722aa;
}

/* Stop Buttons */
QPushButton#stopButton {
    background-color: #cc3333;
}

QPushButton#stopButton:hover {
    background-color: #ee5555;
}

QPushButton#stopButton:pressed {
    background-color: #bb2222;
}

/* Labels */
QLabel {
    color: #e0e6ff;
    font-size: 12px;
}

QLabel#titleLabel {
    color: #ff3333;
    font-weight: bold;
    font-size: 14px;
}

QLabel#sectionLabel {
    color: #4169e1;
    font-weight: bold;
    font-size: 13px;
}

/* Spinboxes & Combobox */
QSpinBox, QDoubleSpinBox {
    background-color: #151a2b;
    color: #e0e6ff;
    border: 1px solid #2a3550;
    border-radius: 4px;
    padding: 6px;
    min-width: 60px;
}

QComboBox {
    background-color: #151a2b;
    color: #e0e6ff;
    border: 1px solid #2a3550;
    border-radius: 4px;
    padding: 6px;
    min-height: 28px;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox::down-arrow {
    image: none;
    color: #4169e1;
}

/* List Widget */
QListWidget {
    background-color: #151a2b;
    color: #e0e6ff;
    border: 1px solid #2a3550;
    border-radius: 4px;
}

QListWidget::item:hover {
    background-color: #1f2a40;
}

QListWidget::item:selected {
    background-color: #2a3a50;
    color: #ff3333;
}

/* Tree Widget */
QTreeWidget {
    background-color: #151a2b;
    color: #e0e6ff;
    border: 1px solid #2a3550;
    border-radius: 4px;
}

/* Text Edit */
QPlainTextEdit, QTextEdit {
    background-color: #151a2b;
    color: #00ff00;
    border: 1px solid #2a3550;
    border-radius: 4px;
    padding: 6px;
    font-family: 'Courier New', monospace;
}

/* Progress Bar */
QProgressBar {
    background-color: #1a2540;
    border: 1px solid #2a3550;
    border-radius: 4px;
    color: #e0e6ff;
    height: 20px;
}

QProgressBar::chunk {
    background-color: #4169e1;
    border-radius: 3px;
}

/* Tab Widget */
QTabWidget::pane {
    border: 1px solid #2a3550;
}

QTabBar::tab {
    background-color: #1a2540;
    color: #8899ff;
    padding: 8px 20px;
    margin-right: 2px;
    border: 1px solid #2a3550;
    border-bottom: none;
    border-radius: 4px 4px 0px 0px;
}

QTabBar::tab:selected {
    background-color: #2a3a50;
    color: #ff3333;
    border: 1px solid #4169e1;
}

QTabBar::tab:hover:!selected {
    background-color: #1f2a40;
}

/* Scrollbars */
QScrollBar:vertical {
    background-color: #0a0e27;
    width: 12px;
    border: 1px solid #2a3550;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: #4169e1;
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #5a7fff;
}

QScrollBar:horizontal {
    background-color: #0a0e27;
    height: 12px;
    border: 1px solid #2a3550;
    border-radius: 6px;
}

QScrollBar::handle:horizontal {
    background-color: #4169e1;
    border-radius: 6px;
    min-width: 20px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #5a7fff;
}

QScrollBar::add-line, QScrollBar::sub-line {
    border: none;
    background: none;
}

/* Menu Bar */
QMenuBar {
    background-color: #0a0e27;
    color: #e0e6ff;
    border-bottom: 1px solid #2a3550;
    padding: 4px;
}

QMenuBar::item:selected {
    background-color: #1f2a40;
}

/* Menu */
QMenu {
    background-color: #151a2b;
    color: #e0e6ff;
    border: 1px solid #2a3550;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #2a3a50;
    color: #ff3333;
}

/* Toolbar */
QToolBar {
    background-color: #0f1321;
    border-bottom: 1px solid #2a3550;
    padding: 6px;
    spacing: 4px;
}

QToolBar::separator {
    background-color: #2a3550;
    width: 1px;
    margin: 4px 2px;
}

/* Status Bar */
QStatusBar {
    background-color: #0f1321;
    color: #e0e6ff;
    border-top: 1px solid #2a3550;
    padding: 4px;
}

/* Line Edit */
QLineEdit {
    background-color: #151a2b;
    color: #e0e6ff;
    border: 1px solid #2a3550;
    border-radius: 4px;
    padding: 6px;
    min-height: 28px;
}

QLineEdit:focus {
    border: 2px solid #4169e1;
}

/* Checkbox */
QCheckBox {
    color: #e0e6ff;
    spacing: 6px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
}

QCheckBox::indicator:unchecked {
    background-color: #151a2b;
    border: 1px solid #2a3550;
    border-radius: 3px;
}

QCheckBox::indicator:checked {
    background-color: #ff3333;
    border: 1px solid #ff3333;
    border-radius: 3px;
}

/* Radio Button */
QRadioButton {
    color: #e0e6ff;
    spacing: 6px;
}

QRadioButton::indicator {
    width: 16px;
    height: 16px;
}

QRadioButton::indicator:unchecked {
    background-color: #151a2b;
    border: 1px solid #2a3550;
    border-radius: 8px;
}

QRadioButton::indicator:checked {
    background-color: #ff3333;
    border: 1px solid #ff3333;
    border-radius: 8px;
}

/* Separator */
QFrame {
    color: #2a3550;
}

/* Tooltips */
QToolTip {
    background-color: #1a2540;
    color: #e0e6ff;
    border: 1px solid #4169e1;
    border-radius: 4px;
    padding: 4px 8px;
}
"""

# ==================== UTILITY FUNCTIONS ====================

def apply_professional_stylesheet(widget):
    """Apply professional stylesheet to a widget"""
    widget.setStyleSheet(PROFESSIONAL_STYLESHEET)


def create_professional_button(text: str, color_type: str = "primary", icon_path: str = None) -> QtWidgets.QPushButton:
    """
    Create a professional button with proper styling
    
    Args:
        text: Button text
        color_type: 'primary' (red), 'secondary' (blue), 'exploration' (purple), 'stop' (dark red)
        icon_path: Optional path to icon
    
    Returns:
        Styled QPushButton
    """
    btn = QtWidgets.QPushButton(text)
    btn.setMinimumHeight(36)
    btn.setMinimumWidth(100)
    btn.setCursor(QtGui.QCursor(Qt.PointingHandCursor))
    
    color_map = {
        'primary': 'addButton',
        'secondary': 'secondaryButton',
        'exploration': 'explorationButton',
        'stop': 'stopButton',
    }
    
    if color_type in color_map:
        btn.setObjectName(color_map[color_type])
    
    if icon_path:
        icon = QtGui.QIcon(icon_path)
        btn.setIcon(icon)
        btn.setIconSize(QtCore.QSize(20, 20))
    
    return btn


def create_professional_slider(min_val: int = 0, max_val: int = 100, 
                               default: int = 50, label: str = None) -> tuple:
    """
    Create a professional slider with label
    
    Returns:
        Tuple of (container_widget, slider, label)
    """
    container = QtWidgets.QWidget()
    layout = QtWidgets.QVBoxLayout(container)
    
    if label:
        lbl = QtWidgets.QLabel(label)
        lbl.setStyleSheet("font-weight: bold; color: #4169e1;")
        layout.addWidget(lbl)
    
    slider = QtWidgets.QSlider(Qt.Horizontal)
    slider.setMinimum(min_val)
    slider.setMaximum(max_val)
    slider.setValue(default)
    slider.setMinimumHeight(28)
    slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
    slider.setTickInterval(max((max_val - min_val) // 10, 1))
    
    layout.addWidget(slider)
    layout.setContentsMargins(0, 4, 0, 4)
    
    value_label = QtWidgets.QLabel(str(default))
    value_label.setAlignment(Qt.AlignRight)
    value_label.setStyleSheet("color: #ff3333; font-weight: bold;")
    
    def update_value(val):
        value_label.setText(str(val))
    
    slider.valueChanged.connect(update_value)
    layout.addWidget(value_label)
    
    return container, slider, value_label


def create_professional_group(title: str, layout_type: str = "vertical") -> tuple:
    """
    Create a professional group box
    
    Args:
        title: Group title
        layout_type: 'vertical' or 'horizontal'
    
    Returns:
        Tuple of (groupbox, layout)
    """
    group = QtWidgets.QGroupBox(title)
    group.setMinimumHeight(100)
    
    if layout_type == "horizontal":
        layout = QtWidgets.QHBoxLayout(group)
    else:
        layout = QtWidgets.QVBoxLayout(group)
    
    layout.setContentsMargins(12, 12, 12, 12)
    layout.setSpacing(8)
    
    return group, layout


def create_professional_spinbox(min_val: float = 0, max_val: float = 100, 
                                default: float = 50, decimals: int = 0) -> QtWidgets.QDoubleSpinBox:
    """Create a professional spinbox"""
    spinbox = QtWidgets.QDoubleSpinBox()
    spinbox.setMinimum(min_val)
    spinbox.setMaximum(max_val)
    spinbox.setValue(default)
    spinbox.setDecimals(decimals)
    spinbox.setMinimumHeight(32)
    spinbox.setMinimumWidth(80)
    spinbox.setButtonSymbols(QtWidgets.QAbstractSpinBox.PlusMinus)
    return spinbox


def create_professional_combobox(items: list) -> QtWidgets.QComboBox:
    """Create a professional combobox"""
    combo = QtWidgets.QComboBox()
    combo.addItems(items)
    combo.setMinimumHeight(32)
    combo.setMinimumWidth(120)
    return combo


def set_window_properties(window: QtWidgets.QMainWindow, title: str = "Polylog", 
                          width: int = 1400, height: int = 900):
    """Set professional window properties"""
    window.setWindowTitle(title)
    window.resize(width, height)
    window.setMinimumSize(1000, 700)
    
    # Center window on screen
    screen = QtGui.QScreen.availableGeometry(QtWidgets.QApplication.primaryScreen())
    x = (screen.width() - width) // 2
    y = (screen.height() - height) // 2
    window.move(x, y)
    
    # Window icon (optional)
    window.setWindowIcon(QtGui.QIcon())
    
    # Apply stylesheet
    apply_professional_stylesheet(window)


def create_section_separator() -> QtWidgets.QFrame:
    """Create a professional separator line"""
    line = QtWidgets.QFrame()
    line.setFrameShape(QtWidgets.QFrame.HLine)
    line.setFrameShadow(QtWidgets.QFrame.Sunken)
    line.setMinimumHeight(2)
    line.setStyleSheet("color: #2a3550;")
    return line


def create_professional_label(text: str, label_type: str = "normal") -> QtWidgets.QLabel:
    """
    Create a professional label
    
    Args:
        text: Label text
        label_type: 'normal', 'title', 'section', or 'status'
    """
    label = QtWidgets.QLabel(text)
    
    styles = {
        'title': "color: #ff3333; font-weight: bold; font-size: 14px;",
        'section': "color: #4169e1; font-weight: bold; font-size: 13px;",
        'normal': "color: #e0e6ff; font-size: 12px;",
        'status': "color: #00ff00; font-family: 'Courier New'; font-size: 11px;",
    }
    
    if label_type in styles:
        label.setObjectName(label_type + 'Label')
        label.setStyleSheet(styles[label_type])
    
    return label


def apply_hover_effect(widget):
    """Apply hover effect to a widget"""
    widget.setCursor(QtGui.QCursor(Qt.PointingHandCursor))
    widget.setAttribute(Qt.WA_Hover, True)
