from PyQt5.QtGui import QPainter, QColor, QPen
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtWidgets import QWidget
from styles import ThemeManager

class GearIcon(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(24, 24)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        theme = ThemeManager.get_current_theme()
        # Use white for dark themes, dark for light theme
        if theme['name'] == 'Light Industrial':
            color = QColor(theme['text'])
        else:
            color = QColor('white')
            
        painter.setPen(QPen(color, 2))
        
        # Draw gear
        rect = QRect(2, 2, 20, 20)
        painter.drawEllipse(rect)
        
        # Draw gear teeth
        for i in range(8):
            painter.save()
            painter.translate(12, 12)
            painter.rotate(i * 45)
            painter.drawLine(8, 0, 11, 0)
            painter.restore() 