from enum import Enum
from PyQt5.QtCore import QSettings

class Theme(Enum):
    LIGHT_INDUSTRIAL = {
        'name': 'Light Industrial',
        'background': '#F0F0F0',
        'surface': '#FFFFFF',
        'surface_hover': '#E8E8E8',
        'primary': '#2196F3',
        'accent': '#FF4081',
        'text': '#212121',
        'text_secondary': '#757575',
        'border': '#BDBDBD',
        'warning': '#FFC107',
        'grid': '#CCCCCC'
    }
    DARK_INDUSTRIAL = {
        'name': 'Dark Industrial',
        'background': '#121212',
        'surface': '#1E1E1E',
        'surface_hover': '#2A2A2A',
        'primary': '#BB86FC',
        'accent': '#03DAC6',
        'text': '#FFFFFF',
        'text_secondary': '#B0B0B0',
        'border': '#333333',
        'warning': '#FF9800',
        'grid': '#333333'
    }
    INDUSTRIAL_BLUE = {
        'name': 'Industrial Blue',
        'background': '#0D1642',
        'surface': '#1A237E',
        'surface_hover': '#283593',
        'primary': '#5C6BC0',
        'accent': '#FF4081',
        'text': '#FFFFFF',
        'text_secondary': '#C5CAE9',
        'border': '#3949AB',
        'warning': '#FFC107',
        'grid': '#3F51B5'
    }

class ThemeManager:
    _current_theme = None
    _settings = QSettings('YourCompany', 'TempController')

    @classmethod
    def initialize(cls):
        # Load saved theme or use default
        saved_theme = cls._settings.value('theme', 'Light Industrial')
        print(f"Loading saved theme: {saved_theme}")
        
        # Reset settings if we detect old theme format
        needs_reset = False
        for theme in Theme:
            if theme.value['name'] == saved_theme:
                test_theme = theme.value
                try:
                    # Test for new keys
                    _ = test_theme['surface_hover']
                except KeyError:
                    needs_reset = True
                break
        
        if needs_reset:
            print("Updating theme format...")
            cls._settings.setValue('theme', 'Light Industrial')
            saved_theme = 'Light Industrial'
        
        # Set the theme
        for theme in Theme:
            if theme.value['name'] == saved_theme:
                cls._current_theme = theme.value
                print(f"Theme found and set: {theme.value['name']}")
                break
                
        if cls._current_theme is None:
            cls._current_theme = Theme.LIGHT_INDUSTRIAL.value
            print("Using default theme")

    @classmethod
    def get_current_theme(cls):
        if cls._current_theme is None:
            cls.initialize()
        return cls._current_theme

    @classmethod
    def set_theme(cls, theme):
        cls._current_theme = theme.value
        cls._settings.setValue('theme', theme.value['name'])
        cls._settings.sync()
        print(f"Theme saved: {theme.value['name']}")

def get_theme_dependent_styles():
    theme = ThemeManager.get_current_theme()
    
    return {
        'button': get_button_style(theme),
        'combo': get_combo_style(theme),
        'label': get_label_style(theme),
        'temp_display': get_temp_display_style(theme),
        'time_label': get_time_label_style(theme),
        'plot': get_plot_theme(theme)
    }

def get_temp_display_style(font_family=None, theme=None):
    if theme is None:
        theme = ThemeManager.get_current_theme()
    # Use white/light grey text for dark themes
    text_color = theme['text'] if theme['name'] == 'Light Industrial' else '#E0E0E0'
    return f"""
        background-color: {theme['background']};
        color: {text_color};
        font-size: 48px;
        font-family: '{font_family or "Arial"}';
        padding: 20px 40px;
        margin: 10px;
        border: 1px solid {theme['border']};
        border-radius: 4px;
    """

def get_label_style(theme=None):
    if theme is None:
        theme = ThemeManager.get_current_theme()
    # Use white/light grey text for dark themes
    text_color = theme['text'] if theme['name'] == 'Light Industrial' else '#E0E0E0'
    return f"""
        font-size: 16px;
        color: {text_color};
    """

def get_time_label_style(theme=None):
    if theme is None:
        theme = ThemeManager.get_current_theme()
    # Use white/light grey text for dark themes
    text_color = theme['text'] if theme['name'] == 'Light Industrial' else '#E0E0E0'
    return f"""
        color: {text_color};
        background-color: {theme['surface']};
        border: 1px solid {theme['border']};
        padding: 5px;
        font-family: 'Consolas', monospace;
        font-size: 14px;
        border-radius: 2px;
    """

def get_button_style(embossed=False, theme=None):
    if theme is None:
        theme = ThemeManager.get_current_theme()
    # Use white/light grey text for dark themes
    text_color = theme['text'] if theme['name'] == 'Light Industrial' else '#E0E0E0'
    return f"""
        QPushButton {{
            background-color: {theme['surface']};
            color: {text_color};
            border: 1px solid {theme['border']};
            border-radius: 4px;
            padding: 5px 10px;
            {f"border-bottom: 2px solid {theme['border']};" if embossed else ""}
        }}
        QPushButton:hover {{
            background-color: {theme['surface_hover']};
            border: 1px solid {theme['primary']};
            {f"border-bottom: 2px solid {theme['primary']};" if embossed else ""}
        }}
        QPushButton:pressed {{
            background-color: {theme['surface']};
            border: 1px solid {theme['border']};
            {f"border-bottom: 1px solid {theme['border']};" if embossed else ""}
            padding-top: 6px;
            padding-bottom: 4px;
        }}
    """

def get_combo_style(embossed=False, theme=None):
    if theme is None:
        theme = ThemeManager.get_current_theme()
    # Use white/light grey text for dark themes
    text_color = theme['text'] if theme['name'] == 'Light Industrial' else '#E0E0E0'
    return f"""
        QComboBox {{
            background-color: {theme['surface']};
            color: {text_color};
            border: 1px solid {theme['border']};
            border-radius: 4px;
            padding: 5px;
            min-width: 6em;
        }}
        QComboBox:hover {{
            border: 1px solid {theme['primary']};
        }}
        QComboBox::drop-down {{
            border: none;
            padding-right: 10px;
        }}
        QComboBox::down-arrow {{
            image: none;
            border: none;
        }}
        QComboBox QAbstractItemView {{
            background-color: {theme['surface']};
            color: {text_color};
            selection-background-color: {theme['primary']};
            selection-color: {text_color};
            border: 1px solid {theme['border']};
        }}
    """

def get_plot_theme(theme=None):
    if theme is None:
        theme = ThemeManager.get_current_theme()
    return {
        'background': theme['background'],
        'foreground': theme['text'],
        'grid': theme['grid'],
        'axis': theme['text_secondary'],
        'text': theme['text'],
        'curve': theme['primary'],
        'current_time': theme['warning']
    }

def get_table_style(theme=None):
    if theme is None:
        theme = ThemeManager.get_current_theme()
    # Use white/light grey text for dark themes
    text_color = theme['text'] if theme['name'] == 'Light Industrial' else '#E0E0E0'
    return f"""
        QTableWidget {{
            background-color: {theme['surface']};
            color: {text_color};
            gridline-color: {theme['border']};
            border: 1px solid {theme['border']};
            border-radius: 4px;
        }}
        QTableWidget::item {{
            color: {text_color};
        }}
        QTableWidget::item:selected {{
            background-color: {theme['primary']};
            color: {text_color};
        }}
        QHeaderView::section {{
            background-color: {theme['surface']};
            color: {text_color};
            border: 1px solid {theme['border']};
            padding: 4px;
        }}
        QScrollBar {{
            background-color: {theme['surface']};
            border: 1px solid {theme['border']};
        }}
    """

def get_dialog_style(theme=None):
    if theme is None:
        theme = ThemeManager.get_current_theme()
    text_color = theme['text'] if theme['name'] == 'Light Industrial' else '#E0E0E0'
    return f"""
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
        QPushButton {{
            background-color: {theme['surface']};
            color: {text_color};
            border: 1px solid {theme['border']};
            padding: 5px 10px;
            border-radius: 4px;
        }}
        QPushButton:hover {{
            background-color: {theme['surface_hover']};
            border: 1px solid {theme['primary']};
        }}
        QTableWidget {{
            background-color: {theme['surface']};
            color: {text_color};
            gridline-color: {theme['border']};
        }}
        QTableWidget::item {{
            color: {text_color};
        }}
        QHeaderView::section {{
            background-color: {theme['surface']};
            color: {text_color};
            border: 1px solid {theme['border']};
        }}
        QSpinBox {{
            background-color: {theme['surface']};
            color: {text_color};
            border: 1px solid {theme['border']};
            padding: 5px;
            border-radius: 4px;
        }}
        QSpinBox::up-button, QSpinBox::down-button {{
            background-color: {theme['surface']};
            border: 1px solid {theme['border']};
        }}
        QMessageBox {{
            background-color: {theme['background']};
            color: {text_color};
        }}
        QMessageBox QLabel {{
            color: {text_color};
        }}
        QInputDialog {{
            background-color: {theme['background']};
            color: {text_color};
        }}
        QInputDialog QLabel {{
            color: {text_color};
        }}
    """

def get_message_box_style():
    """Get theme-aware style for message boxes."""
    theme = ThemeManager.get_current_theme()
    return f"""
        QMessageBox {{
            background-color: {theme['background']};
        }}
        QMessageBox QLabel {{
            color: {theme['primary']};
            font-size: 12px;
            padding: 10px;
        }}
        QMessageBox QPushButton {{
            background-color: {theme['background']};
            color: {theme['primary']};
            border: 1px solid {theme['border']};
            border-radius: 4px;
            padding: 5px 15px;
            min-width: 60px;
        }}
        QMessageBox QPushButton:hover {{
            background-color: {theme['border']};
        }}
    """