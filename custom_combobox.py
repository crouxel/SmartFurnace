from PyQt5.QtWidgets import QComboBox, QMenu
from PyQt5.QtCore import Qt, QEvent

class CustomComboBox(QComboBox):
    """Custom combo box with right-click menu support for schedule operations."""
    
    def __init__(self, parent=None):
        """Initialize the combo box with context menu support."""
        super().__init__(parent)
        self.context_menu = QMenu(self)
        self.view().viewport().installEventFilter(self)
        self.setup_context_menu()
        
    def setup_context_menu(self):
        """Set up the context menu with Show Code, Edit and Delete actions."""
        self.context_menu.setStyleSheet("""
            QMenu {
                background-color: #2b2b2b;
                color: white;
                border: 1px solid #3d3d3d;
            }
            QMenu::item:selected {
                background-color: #3d3d3d;
            }
        """)
        
        # Add Show Code, Edit and Delete actions
        show_code_action = self.context_menu.addAction("Show Code")
        edit_action = self.context_menu.addAction("Edit")
        delete_action = self.context_menu.addAction("Delete")
        
        # Connect actions to parent window methods
        show_code_action.triggered.connect(lambda: self.parent().show_furnace_commands(self.currentText()))
        edit_action.triggered.connect(lambda: self.parent().edit_schedule())
        delete_action.triggered.connect(lambda: self.parent().delete_schedule())
    
    def mousePressEvent(self, event):
        """Handle mouse press events, showing context menu on right-click."""
        if event.button() == Qt.RightButton:
            current_text = self.currentText()
            if current_text and current_text != "Add Schedule":
                self.context_menu.exec_(self.mapToGlobal(event.pos()))
        else:
            super().mousePressEvent(event)
    
    def eventFilter(self, source, event):
        """Filter events to handle right-clicks in the dropdown view."""
        if event.type() == QEvent.MouseButtonPress and event.button() == Qt.RightButton:
            index = self.view().indexAt(event.pos())
            if index.isValid():
                text = self.itemText(index.row())
                if text and text != "Add Schedule":
                    self.setCurrentIndex(index.row())
                    self.context_menu.exec_(self.view().mapToGlobal(event.pos()))
                    return True
        return super().eventFilter(source, event)