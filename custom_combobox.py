from PyQt5.QtWidgets import QComboBox, QMenu
from PyQt5.QtCore import Qt, QEvent

class CustomComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.context_menu = QMenu(self)
        self.view().viewport().installEventFilter(self)

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self.context_menu.exec_(self.mapToGlobal(event.pos()))
        else:
            super().mousePressEvent(event)

    def eventFilter(self, source, event):
        if event.type() == QEvent.MouseButtonPress and event.button() == Qt.RightButton:
            index = self.view().indexAt(event.pos())
            if index.isValid():
                self.setCurrentIndex(index.row())
                self.context_menu.exec_(self.view().mapToGlobal(event.pos()))
                return True
        return super().eventFilter(source, event)

    def set_context_menu(self, menu):
        self.context_menu = menu