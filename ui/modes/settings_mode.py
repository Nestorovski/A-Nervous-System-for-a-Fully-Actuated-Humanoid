from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                             QLabel, QPushButton, QComboBox, QCheckBox, QSlider, QSpinBox)
from PyQt6.QtCore import Qt
from core.config_manager import config_manager
from core.theme_manager import theme_manager

class SettingsMode(QWidget):
    """
    Global Configuration Interface.
    Directly binds UI elements to the ConfigManager.
    """
    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._load_current_values()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # --- TITLE ---
        lbl_title = QLabel("GLOBAL SYSTEM SETTINGS")
        lbl_title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(lbl_title)
        
        # --- GROUP 1: SAFETY ---
        safe_grp = QGroupBox("Safety & Hardware Governor")
        sl = QVBoxLayout(safe_grp)
        
        self.chk_collision = QCheckBox("Enable Active Collision Prevention")
        self.chk_collision.toggled.connect(lambda v: config_manager.set("safety_collision_enabled", v))
        sl.addWidget(self.chk_collision)
        
        h_speed = QHBoxLayout()
        h_speed.addWidget(QLabel("Global Motor Speed Limit (%):"))
        self.spin_speed = QSpinBox()
        self.spin_speed.setRange(10, 100)
        self.spin_speed.setSingleStep(5)
        self.spin_speed.valueChanged.connect(lambda v: config_manager.set("motor_max_speed", v))
        h_speed.addWidget(self.spin_speed)
        sl.addLayout(h_speed)
        
        h_tol = QHBoxLayout()
        h_tol.addWidget(QLabel("Servo/Pot Tolerance (Deadband):"))
        self.spin_tol = QSpinBox()
        self.spin_tol.setRange(1, 50)
        self.spin_tol.valueChanged.connect(lambda v: config_manager.set("motor_tolerance", v))
        h_tol.addWidget(self.spin_tol)
        sl.addLayout(h_tol)
        
        layout.addWidget(safe_grp)
        
        # --- GROUP 2: VISUALS ---
        vis_grp = QGroupBox("Visual Customization")
        vl = QVBoxLayout(vis_grp)
        
        h1 = QHBoxLayout()
        h1.addWidget(QLabel("App Theme:"))
        self.cb_theme = QComboBox()
        # Must match keys in ThemeManager.PALETTES
        self.cb_theme.addItems(theme_manager.PALETTES.keys())
        self.cb_theme.currentTextChanged.connect(lambda v: config_manager.set("app_theme", v))
        h1.addWidget(self.cb_theme)
        vl.addLayout(h1)
        
        h_bone = QHBoxLayout()
        h_bone.addWidget(QLabel("Skeleton Material:"))
        self.cb_bone = QComboBox()
        self.cb_bone.addItems(["Bone", "Carbon", "Gold", "Steel"])
        self.cb_bone.currentTextChanged.connect(lambda v: config_manager.set("skeleton_color", v))
        h_bone.addWidget(self.cb_bone)
        vl.addLayout(h_bone)
        
        h_ghost = QHBoxLayout()
        h_ghost.addWidget(QLabel("Target (Ghost) Opacity:"))
        self.slide_ghost = QSlider(Qt.Orientation.Horizontal)
        self.slide_ghost.setRange(0, 100)
        self.slide_ghost.valueChanged.connect(lambda v: config_manager.set("visual_ghost_opacity", v/100.0))
        h_ghost.addWidget(self.slide_ghost)
        vl.addLayout(h_ghost)
        
        layout.addWidget(vis_grp)
        
        layout.addStretch()
        
        btn_reset = QPushButton("RESET TO FACTORY DEFAULTS")
        btn_reset.setMinimumHeight(40)
        btn_reset.clicked.connect(self._reset_defaults)
        layout.addWidget(btn_reset)

    def _load_current_values(self):
        """Populates UI from the ConfigManager state."""
        self.chk_collision.setChecked(config_manager.get("safety_collision_enabled") or True)
        self.spin_speed.setValue(config_manager.get("motor_max_speed") or 80)
        self.spin_tol.setValue(config_manager.get("motor_tolerance") or 15)
        
        current_theme = config_manager.get("app_theme")
        if current_theme in theme_manager.PALETTES:
            self.cb_theme.setCurrentText(current_theme)
        
        current_bone = config_manager.get("skeleton_color") or "Bone"
        self.cb_bone.setCurrentText(current_bone)
        
        opacity = config_manager.get("visual_ghost_opacity") or 0.3
        self.slide_ghost.setValue(int(opacity * 100))

    def _reset_defaults(self):
        config_manager.set("app_theme", "Cyber Dark")
        config_manager.set("skeleton_color", "Bone")
        config_manager.set("motor_max_speed", 80)
        self._load_current_values()