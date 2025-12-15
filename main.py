import sys
import logging
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont

# Core Systems
from core.config_manager import config_manager
from core.theme_manager import theme_manager
from ui.main_window import MainWindow

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='[%(levelname)s] %(name)s: %(message)s'
    )

def main():
    setup_logging()
    logging.info("Starting Robot Studio Engine")

    # High DPI Scaling
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))

    # 1. Load Config (Hardware & Prefs)
    config_manager.load_all()

    # 2. Theme Application
    def apply_theme():
        # Get CSS from the Theme Manager
        stylesheet = theme_manager.generate_stylesheet()
        app.setStyleSheet(stylesheet)
        logging.info(f"Theme Applied: {theme_manager.current_theme_name}")

    # Initial Apply
    apply_theme()

    # 3. Connect Reactive Signals
    # When theme_manager changes (triggered by config_manager), update CSS
    theme_manager.theme_changed.connect(apply_theme)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main() 