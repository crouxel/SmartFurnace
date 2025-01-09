from enum import Enum
from PyQt5.QtCore import QSettings

class Theme(Enum):
    DARK = {
        'name': 'Dark Industrial',
        'background': '#1E1E1E',
        'surface': '#2C2C2C',
        'primary': '#00A5E3',    # Bright blue
        'secondary': '#404040',  # Dark gray
        'accent': '#00FF00',     # Green for temps/time
        'text': '#FFFFFF',
        'text_secondary': '#B0B0B0',
        'warning': '#FF4444',
        'grid': (64, 64, 64),
        'border': '#404040'
    }
    
    LIGHT = {
        'name': 'Light Industrial',
        'background': '#E6E9F0',  # Steel blue gray
        'surface': '#FFFFFF',
        'primary': '#0066CC',    # Deep blue
        'secondary': '#D0D4DC',  # Light gray
        'accent': '#008060',     # Forest green for temps/time
        'text': '#1A1A1A',
        'text_secondary': '#666666',
        'warning': '#CC0000',
        'grid': (180, 180, 180),
        'border': '#B8B8B8'
    }
    
    INDUSTRIAL = {
        'name': 'Industrial Blue',
        'background': '#1B2838',  # Deep blue-gray
        'surface': '#2A3F5A',
        'primary': '#66B2FF',
        'secondary': '#394E64',
        'accent': '#00FF99',
        'text': '#E6E6E6',
        'text_secondary': '#99A8B8',
        'warning': '#FF6B6B',
        'grid': (50, 65, 85),
        'border': '#394E64'
    }

class ThemeManager:
    _current_theme = None
    _settings = QSettings('YourCompany', 'TempController')

    @classmethod
    def initialize(cls):
        # Load saved theme or use default
        saved_theme = cls._settings.value('theme', 'Light Industrial')
        print(f"Loading saved theme: {saved_theme}")  # Debug print
        for theme in Theme:
            if theme.value['name'] == saved_theme:
                cls._current_theme = theme.value
                print(f"Theme found and set: {theme.value['name']}")  # Debug print
                break
        if cls._current_theme is None:
            cls._current_theme = Theme.LIGHT_INDUSTRIAL.value
            print("Using default theme")  # Debug print

    @classmethod
    def get_current_theme(cls):
        if cls._current_theme is None:
            cls.initialize()
        return cls._current_theme

    @classmethod
    def set_theme(cls, theme):
        cls._current_theme = theme.value
        cls._settings.setValue('theme', theme.value['name'])
        cls._settings.sync()  # Force save
        print(f"Theme saved: {theme.value['name']}")  # Debug print

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
    return f"""
        background-color: {theme['background']};
        color: {theme['accent']};
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
    return f"""
        font-size: 16px;
        color: {theme['text']};
    """

def get_time_label_style(theme=None):
    if theme is None:
        theme = ThemeManager.get_current_theme()
    return f"""
        color: {theme['accent']};
        background-color: {theme['surface']};
        border: 1px solid {theme['border']};
        padding: 5px;
        font-family: 'Consolas', monospace;
        font-size: 14px;
        border-radius: 2px;
    """

def get_button_style(theme=None, embossed=False):
    if theme is None:
        theme = ThemeManager.get_current_theme()
        
    base_style = f"""
        QPushButton {{
            background-color: {theme['surface']};
            color: {theme['text']};
            font-weight: bold;
            padding: 5px 15px;
            border-radius: 2px;
    """
    
    if embossed:
        base_style += f"""
            border: 1px solid {theme['background']};
            border-top: 1px solid {theme['border']};
            border-left: 1px solid {theme['border']};
        """
    else:
        base_style += f"""
            border: 1px solid {theme['border']};
        """
    
    base_style += """
        }
        
        QPushButton:hover {
            background-color: #404040;
        }
        
        QPushButton:pressed {
            background-color: #1a1a1a;
    """
    
    if embossed:
        base_style += f"""
            border: 1px solid {theme['background']};
            border-bottom: 1px solid {theme['border']};
            border-right: 1px solid {theme['border']};
        """
    
    base_style += "}"
    return base_style

def get_combo_style(theme=None, embossed=False):
    if theme is None:
        theme = ThemeManager.get_current_theme()
        
    base_style = f"""
        QComboBox {{
            background-color: {theme['surface']};
            color: {theme['text']};
            padding: 5px;
            border-radius: 2px;
    """
    
    if embossed:
        base_style += f"""
            border: 1px solid {theme['background']};
            border-top: 1px solid {theme['border']};
            border-left: 1px solid {theme['border']};
        """
    else:
        base_style += f"""
            border: 1px solid {theme['border']};
        """
    
    base_style += f"""
        }}
        
        QComboBox::drop-down {{
            border: none;
        }}
        
        QComboBox::down-arrow {{
            width: 12px;
            height: 12px;
        }}
        
        QComboBox:on {{
            background-color: {theme['secondary']};
        }}
        
        QComboBox QAbstractItemView {{
            background-color: {theme['surface']};
            color: {theme['text']};
            selection-background-color: {theme['primary']};
            border: 1px solid {theme['border']};
        }}
    """
    return base_style

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