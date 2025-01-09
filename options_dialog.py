from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                           QComboBox, QLabel, QPushButton, QGroupBox,
                           QWidget)
from styles import Theme, ThemeManager, get_combo_style, get_button_style
from PyQt5.QtCore import QSize
from constants import (COMPANY_NAME, APP_NAME, STYLE_DEFAULTS, 
                      PADDING, BORDER_RADIUS)

class OptionsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Options")
        self.setFixedWidth(400)
        self.init_ui()
        
    def init_ui(self):
        theme = ThemeManager.get_current_theme()
        # Set dialog background and text color
        text_color = '#212121' if theme['name'] == 'Light Industrial' else '#E0E0E0'
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {theme['background']};
            }}
            QLabel {{
                color: {text_color};
            }}
            QLineEdit {{
                background-color: {theme['surface']};
                color: {text_color};
                border: 1px solid {theme['border']};
                padding: 5px;
                border-radius: 4px;
            }}
            QLineEdit:focus {{
                border: 1px solid {theme['primary']};
            }}
        """)
        
        layout = QVBoxLayout()
        
        # Theme selector
        theme_group = self.create_group_box("Interface Theme")
        theme_layout = QHBoxLayout()
        
        theme_label = QLabel("Theme:")
        theme_label.setStyleSheet(f"color: {text_color};")
        
        self.theme_combo = QComboBox()
        self.theme_combo.setStyleSheet(get_combo_style())
        self.theme_combo.addItems([t.value['name'] for t in Theme])
        current_theme = theme['name']
        self.theme_combo.setCurrentText(current_theme)
        self.theme_combo.currentTextChanged.connect(self.on_theme_changed)
        
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_combo)
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)
        
        # Add preview section
        preview = QWidget()
        preview.setFixedHeight(100)
        preview.setStyleSheet(f"background-color: {theme['surface']}; border: 1px solid {theme['border']};")
        layout.addWidget(preview)
        
        # Buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        
        for button in [ok_button, cancel_button]:
            button.setStyleSheet(get_button_style())
            button_layout.addWidget(button)
        
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def create_group_box(self, title):
        theme = ThemeManager.get_current_theme()
        text_color = '#212121' if theme['name'] == 'Light Industrial' else '#E0E0E0'
        group = QGroupBox(title)
        group.setStyleSheet(f"""
            QGroupBox {{
                color: {text_color};
                border: 1px solid {theme['border']};
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 16px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
            }}
        """)
        return group
    
    def on_theme_changed(self, theme_name):
        for theme in Theme:
            if theme.value['name'] == theme_name:
                ThemeManager.set_theme(theme)
                if self.parent():
                    self.parent().apply_theme()
