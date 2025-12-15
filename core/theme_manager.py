import logging
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QColor

logger = logging.getLogger('inmoov_v13')

class ThemeManager(QObject):
    """
    3.0 Reactive Design System.
    Manages semantic palettes and generates high-fidelity QSS dynamically.
    """
    # Signal emitted when the theme changes, allowing custom widgets (Icons, 3D View) to redraw.
    theme_changed = pyqtSignal()

    # --- PALETTE DEFINITIONS ---
    PALETTES = {
        "Cyber Dark": {
            "bg_app":       "#09090b",  # Void Black
            "bg_surface":   "#18181b",  # Zinc 900
            "bg_element":   "#27272a",  # Zinc 800
            "bg_hover":     "#3f3f46",  # Zinc 700
            "bg_input":     "#09090b",  
            "border_dim":   "#3f3f46",
            "border_focus": "#0ea5e9",  # Sky 500
            "text_primary": "#f4f4f5",  # Zinc 100
            "text_muted":   "#a1a1aa",  # Zinc 400
            "accent_main":  "#0ea5e9",  # Sky 500
            "accent_glow":  "rgba(14, 165, 233, 0.15)",
            "danger":       "#ef4444",  # Red 500
            "success":      "#22c55e",  # Green 500
            "warning":      "#f59e0b",  # Amber 500
        },
        "Engineering Grey": {
            "bg_app":       "#f4f4f5",  # Zinc 100
            "bg_surface":   "#ffffff",  # White
            "bg_element":   "#e4e4e7",  # Zinc 200
            "bg_hover":     "#d4d4d8",  # Zinc 300
            "bg_input":     "#ffffff",
            "border_dim":   "#d4d4d8",
            "border_focus": "#2563eb",  # Blue 600
            "text_primary": "#18181b",  # Zinc 900
            "text_muted":   "#71717a",  # Zinc 500
            "accent_main":  "#2563eb",  # Blue 600
            "accent_glow":  "rgba(37, 99, 235, 0.1)",
            "danger":       "#dc2626",  # Red 600
            "success":      "#16a34a",  # Green 600
            "warning":      "#d97706",  # Amber 600
        },
        "High Contrast": {
            "bg_app":       "#000000",
            "bg_surface":   "#000000",
            "bg_element":   "#000000",
            "bg_hover":     "#1a1a1a",
            "bg_input":     "#000000",
            "border_dim":   "#ffffff",
            "border_focus": "#ffff00",
            "text_primary": "#ffffff",
            "text_muted":   "#ffffff",
            "accent_main":  "#ffff00",  # Yellow
            "accent_glow":  "rgba(255, 255, 0, 0.2)",
            "danger":       "#ff0000",
            "success":      "#00ff00",
            "warning":      "#ff8800",
        }
    }

    def __init__(self):
        super().__init__()
        self.current_theme_name = "Cyber Dark"
        self.active_palette = self.PALETTES[self.current_theme_name]

    def set_theme(self, theme_name):
        """Updates the active palette and notifies the system."""
        if theme_name in self.PALETTES:
            self.current_theme_name = theme_name
            self.active_palette = self.PALETTES[theme_name]
            self.theme_changed.emit()
            logger.info(f"Theme switched to: {theme_name}")

    def get_color(self, key):
        """Returns the hex code for a specific semantic key."""
        return self.active_palette.get(key, "#ff00ff")

    def get_qcolor(self, key):
        """Returns a QColor object for a specific semantic key (for Painters)."""
        return QColor(self.get_color(key))

    def generate_stylesheet(self):
        """Compiles the CSS string using the active palette."""
        p = self.active_palette
        
        # Common layout rules injected with dynamic colors
        return f"""
            /* --- GLOBAL RESET --- */
            QMainWindow, QWidget {{
                background-color: {p['bg_app']};
                color: {p['text_primary']};
                font-family: 'Segoe UI', 'Roboto', sans-serif;
                font-size: 10pt;
                selection-background-color: {p['accent_main']};
                selection-color: {p['bg_app'] if self.current_theme_name != 'Cyber Dark' else '#ffffff'};
            }}

            /* --- SCROLLBARS --- */
            QScrollBar:vertical {{ border: none; background: {p['bg_app']}; width: 10px; margin: 0px; }}
            QScrollBar::handle:vertical {{ background: {p['bg_element']}; min-height: 20px; border-radius: 5px; }}
            QScrollBar::handle:vertical:hover {{ background: {p['accent_main']}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}

            /* --- DOCKS & CONTAINERS --- */
            QDockWidget {{
                titlebar-close-icon: url(none);
                titlebar-normal-icon: url(none);
            }}
            QDockWidget::title {{
                background: {p['bg_surface']};
                padding: 6px;
                border-bottom: 1px solid {p['border_dim']};
                font-weight: bold;
                color: {p['accent_main']};
            }}
            
            /* --- TABLES --- */
            QTableWidget {{
                background-color: {p['bg_app']};
                gridline-color: {p['border_dim']};
                border: 1px solid {p['border_dim']};
                border-radius: 4px;
            }}
            QHeaderView::section {{
                background-color: {p['bg_surface']};
                padding: 6px;
                border: none;
                border-bottom: 2px solid {p['accent_main']};
                color: {p['text_muted']};
                font-weight: bold;
            }}
            QTableWidget::item {{ border-bottom: 1px solid {p['bg_element']}; }}
            QTableWidget::item:selected {{ background-color: {p['accent_glow']}; color: {p['text_primary']}; }}

            /* --- BUTTONS --- */
            QPushButton {{
                background-color: {p['bg_element']};
                border: 1px solid {p['border_dim']};
                border-radius: 4px;
                color: {p['text_primary']};
                padding: 6px 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {p['bg_hover']};
                border-color: {p['accent_main']};
            }}
            QPushButton:pressed {{
                background-color: {p['accent_main']};
                color: {p['bg_app']};
            }}

            /* --- INPUTS --- */
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
                background-color: {p['bg_input']};
                border: 1px solid {p['border_dim']};
                border-radius: 4px;
                padding: 4px;
                color: {p['text_primary']};
            }}
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
                border: 1px solid {p['accent_main']};
            }}
            
            /* --- TABS --- */
            QTabWidget::pane {{ border: 1px solid {p['border_dim']}; background: {p['bg_surface']}; }}
            QTabBar::tab {{
                background: {p['bg_app']};
                color: {p['text_muted']};
                padding: 8px 16px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background: {p['bg_surface']};
                color: {p['accent_main']};
                border-top: 2px solid {p['accent_main']};
            }}

            /* --- GROUP BOX --- */
            QGroupBox {{
                border: 1px solid {p['border_dim']};
                border-radius: 6px;
                margin-top: 24px;
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: {p['accent_main']};
            }}
        """

# Global Instance
theme_manager = ThemeManager()