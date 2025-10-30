"""
Library panel for stored polygon designs.

Features:
- Scrollable list of saved polygon designs
- Drag and drop support
- Right-click context menu
- Search/filter capability
"""

from PySide6.QtWidgets import (
    QGroupBox, QVBoxLayout, QListWidget, QListWidgetItem,
    QLineEdit, QContextMenuEvent
)
from PySide6.QtCore import Qt, Signal, QMimeData
from PySide6.QtGui import QColor, QDrag


class DragEnabledListWidget(QListWidget):
    """Custom list widget that properly supports drag and drop."""
    
    def startDrag(self, supportedActions):
        """Start drag operation with item text as MIME data."""
        item = self.currentItem()
        if item:
            # Create MIME data with item text
            mime_data = QMimeData()
            mime_data.setText(item.text())
            
            # Create drag object
            drag = QDrag(self)
            drag.setMimeData(mime_data)
            
            # Execute drag
            drag.exec(Qt.DropAction.CopyAction)


class LibraryPanel(QGroupBox):
    """Panel for managing library of polygon designs."""
    
    # Signals
    design_selected = Signal(str)
    design_double_clicked = Signal(str)
    
    def __init__(self):
        super().__init__("Library")
        self.setStyleSheet("QGroupBox { font-weight: bold; }")
        
        layout = QVBoxLayout()
        
        # Search box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search library...")
        self.search_box.textChanged.connect(self._filter_library)
        layout.addWidget(self.search_box)
        
        # Library list (custom widget with proper drag support)
        self.library_list = DragEnabledListWidget()
        self.library_list.setSelectionMode(self.library_list.SingleSelection)
        self.library_list.itemSelectionChanged.connect(self._on_selection_changed)
        self.library_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        
        # Enable drag only mode
        self.library_list.setDragDropMode(QListWidget.DragOnly)
        
        layout.addWidget(self.library_list)
        
        # Sample library items (will be loaded from files)
        self._populate_sample_library()
        
        self.setLayout(layout)
        print("✓ LibraryPanel initialized")
    
    def _populate_sample_library(self):
        """Populate library with sample designs."""
        sample_designs = [
            "Triangle Basic",
            "Square Simple",
            "Pentagon Star",
            "Hexagon Complex",
            "Octagon Pattern",
            "Decagon Design",
            "Custom Mix 1",
            "Custom Mix 2",
            "Symmetrical Form",
            "Asymmetric Shape",
        ]
        
        for design in sample_designs:
            item = QListWidgetItem(design)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsDragEnabled)
            self.library_list.addItem(item)
    
    def _on_selection_changed(self):
        """Handle library item selection."""
        selected = self.library_list.selectedItems()
        if selected:
            self.design_selected.emit(selected[0].text())
    
    def _on_item_double_clicked(self, item):
        """Handle double click on library item."""
        self.design_double_clicked.emit(item.text())
    
    def _filter_library(self, text: str):
        """Filter library items by search text."""
        for i in range(self.library_list.count()):
            item = self.library_list.item(i)
            item.setHidden(text.lower() not in item.text().lower())
    
    def add_design(self, name: str, data: dict):
        """Add a new design to the library."""
        item = QListWidgetItem(name)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsDragEnabled)
        self.library_list.addItem(item)
    
    def get_selected_design(self) -> str:
        """Get currently selected design name."""
        selected = self.library_list.selectedItems()
        return selected[0].text() if selected else None
    
    def clear_library(self):
        """Clear all library items."""
        self.library_list.clear()
