import json
import os
import logging
from PyQt6.QtCore import QObject, pyqtSignal
from .theme_manager import theme_manager

logger = logging.getLogger('inmoov_v13')

class ConfigManager(QObject):
    """
    Central Configuration Hub.
    Manages Hardware Maps, Robot Anatomy, User Preferences, and Macros.
    """
    # Signals
    preference_changed = pyqtSignal(str, object)
    visual_changed = pyqtSignal()
    hardware_map_changed = pyqtSignal()
    macros_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Paths
        self.map_file = os.path.join(self.base_dir, "config", "hardware", "map_default.json")
        self.prefs_file = os.path.join(self.base_dir, "config", "profiles", "user_prefs.json")
        self.macro_file = os.path.join(self.base_dir, "config", "profiles", "macros.json")
        
        # Data Stores
        self.hardware_map = {}
        self.current_map_file = self.map_file
        self.macros = {}
        
        self.user_prefs = {
            "app_theme": "Cyber Dark",
            "skeleton_color": "Bone",
            "safety_collision_enabled": True,
            "motor_max_speed": 80,
            "motor_tolerance": 15,
            "visual_ghost_opacity": 0.3,
            "last_serial_port": None
        }

    def load_all(self):
        """Bootloader: Reads all config files."""
        self.load_hardware_map(self.current_map_file)
        self.load_user_prefs()
        self.load_macros()
        
        # Apply initial theme from loaded prefs
        theme_manager.set_theme(self.user_prefs.get("app_theme", "Cyber Dark"))
        return True

    # --- HARDWARE MAPS ---
    def load_hardware_map(self, file_path=None):
        if file_path is None: file_path = self.current_map_file

        if not os.path.exists(file_path):
            logger.error(f"Hardware Map file not found: {file_path}")
            return False

        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                self.hardware_map = data.get("mapping", {})
                self.current_map_file = file_path
                self.hardware_map_changed.emit()
                logger.info(f"Loaded Hardware Map from {os.path.basename(file_path)}")
                return True
        except Exception as e:
            logger.error(f"Failed to load hardware map: {e}")
            self.hardware_map = {}
            return False

    def save_hardware_map(self, new_map_data: dict, file_path=None):
        target_path = file_path if file_path else self.current_map_file
        try:
            full_data = {
                "metadata": {
                    "version": "1.3",
                    "description": "InMoov Distributed Hardware Map",
                    "source": os.path.basename(target_path)
                },
                "mapping": new_map_data
            }
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            with open(target_path, 'w') as f:
                json.dump(full_data, f, indent=4)
            
            self.hardware_map = new_map_data
            self.current_map_file = target_path
            self.hardware_map_changed.emit()
            return True
        except Exception as e:
            logger.error(f"Failed to save hardware map: {e}")
            return False

    # --- MACROS ---
    def load_macros(self):
        if os.path.exists(self.macro_file):
            try:
                with open(self.macro_file, 'r') as f:
                    self.macros = json.load(f)
                self.macros_changed.emit()
            except Exception as e:
                logger.error(f"Failed to load macros: {e}")
                self.macros = {}
        return self.macros

    def save_macros(self, macros_data):
        try:
            os.makedirs(os.path.dirname(self.macro_file), exist_ok=True)
            with open(self.macro_file, 'w') as f:
                json.dump(macros_data, f, indent=4)
            self.macros = macros_data
            self.macros_changed.emit()
            return True
        except Exception as e:
            logger.error(f"Failed to save macros: {e}")
            return False

    # --- PREFERENCES ---
    def load_user_prefs(self):
        if os.path.exists(self.prefs_file):
            try:
                with open(self.prefs_file, 'r') as f:
                    self.user_prefs.update(json.load(f))
            except Exception as e:
                logger.error(f"Prefs load error: {e}")

    def save_user_prefs(self):
        try:
            os.makedirs(os.path.dirname(self.prefs_file), exist_ok=True)
            with open(self.prefs_file, 'w') as f:
                json.dump(self.user_prefs, f, indent=4)
        except Exception as e:
            logger.error(f"Prefs save error: {e}")

    def get(self, key):
        return self.user_prefs.get(key)

    def set(self, key, value):
        if self.user_prefs.get(key) != value:
            self.user_prefs[key] = value
            self.save_user_prefs()
            self.preference_changed.emit(key, value)
            
            if key == "app_theme":
                theme_manager.set_theme(value)
                self.visual_changed.emit()
            elif key in ["skeleton_color", "visual_ghost_opacity"]:
                self.visual_changed.emit()

    def get_pin_config(self, joint_id):
        return self.hardware_map.get(str(joint_id), {})

# Global Instance
config_manager = ConfigManager()