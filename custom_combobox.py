from PyQt5.QtWidgets import QComboBox, QMenu
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtCore import QObject
from styles import ThemeManager
from constants import PADDING, BORDER_RADIUS, STYLE_DEFAULTS

class CustomComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._context_menu = None
        self.setFocusPolicy(Qt.StrongFocus)
        self.view().viewport().installEventFilter(self)
        print("Combo box created")
        
    def set_context_menu(self, menu):
        self._context_menu = menu
        theme = ThemeManager.get_current_theme()
        text_color = theme['text'] if theme['name'] == 'Light Industrial' else '#E0E0E0'
        
        # Style the context menu
        self._context_menu.setStyleSheet(f"""
            QMenu {{
                background-color: {theme['surface']};
                color: {text_color};
                border: 1px solid {theme['border']};
                padding: {STYLE_DEFAULTS['padding']};
                border-radius: {STYLE_DEFAULTS['border_radius']};
            }}
            QMenu::item:selected {{
                background-color: {theme['primary']};
            }}
        """)
        print("Menu set and styled")
        
    def eventFilter(self, obj, event):
        if obj == self.view().viewport():
            if event.type() == event.MouseButtonPress:
                if event.button() == Qt.RightButton:
                    print("Right click in popup")
                    if self._context_menu:
                        index = self.view().indexAt(event.pos())
                        if index.isValid():
                            self.setCurrentIndex(index.row())
                            self._context_menu.exec_(self.view().viewport().mapToGlobal(event.pos()))
                            return True
        return super().eventFilter(obj, event)
        
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.RightButton:
            print("Right click detected")
            if self._context_menu:
                self._context_menu.exec_(event.globalPos())
        else:
            super().mouseReleaseEvent(event)