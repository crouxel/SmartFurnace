from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QComboBox, QMenu
from PyQt5.QtCore import Qt
import sys

class TestCombo(QComboBox):
    def __init__(self):
        super().__init__()
        self.addItems(["Item 1", "Item 2", "Item 3"])
        self._menu = QMenu()
        self._menu.addAction("Test Action")
        
    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            print("Right click!")
            self._menu.exec_(event.globalPos())
        else:
            super().mousePressEvent(event)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        combo = TestCombo()
        layout.addWidget(combo)
        self.setLayout(layout)

app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec_()) 