from PyQt5.QtWidgets import QComboBox, QMenu
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QMouseEvent

class CustomComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._context_menu = None
        self.setFocusPolicy(Qt.StrongFocus)
        self.view().viewport().installEventFilter(self)
        print("Combo box created")
        
    def set_context_menu(self, menu):
        self._context_menu = menu
        print("Menu set")
        
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