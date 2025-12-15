from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                             QScrollArea, QLineEdit, QMessageBox, QFrame, QGridLayout)
from PyQt6.QtCore import Qt
from core.theme_manager import theme_manager
from core.config_manager import config_manager

class QuickActionsPanel(QWidget):
    """
    Dynamic Macro Control Pad.
    Allows triggering presets and recording new ones from current state.
    """
    def __init__(self, parent_window, kinematics):
        super().__init__(parent_window)
        self.kinematics = kinematics
        self.macros = {}
        self._load_data()
        self._setup_ui()
        theme_manager.theme_changed.connect(self.update_theme)

    def _load_data(self):
        loaded = config_manager.load_macros()
        if loaded:
            self.macros = loaded
        else:
            # Fallback if file missing
            self.macros = {"General": {"Home": {"1":90}}}

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # --- 1. HEADER / CREATOR ---
        creator_frame = QFrame()
        creator_frame.setFixedHeight(50)
        cf_layout = QHBoxLayout(creator_frame)
        cf_layout.setContentsMargins(10, 5, 10, 5)
        
        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("New Pose Name...")
        
        self.btn_save_new = QPushButton("✚ SAVE POSE")
        self.btn_save_new.clicked.connect(self._save_current_pose)
        
        cf_layout.addWidget(self.input_name)
        cf_layout.addWidget(self.btn_save_new)
        layout.addWidget(creator_frame)
        
        # --- 2. SCROLLABLE GRID ---
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("border: none; background: transparent;")
        
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setSpacing(15)
        self.content_layout.setContentsMargins(10, 10, 10, 10)
        
        self._build_grid()
        
        self.scroll.setWidget(self.content_widget)
        layout.addWidget(self.scroll)
        
        # Initial styling
        self.update_theme()

    def _build_grid(self):
        """Rebuilds the UI based on self.macros dictionary."""
        # Clear existing
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        for category, actions in self.macros.items():
            # Category Header
            cat_lbl = QLabel(category.upper())
            cat_lbl.setStyleSheet("font-weight: bold; font-size: 11px; letter-spacing: 1px; margin-top: 5px;")
            self.content_layout.addWidget(cat_lbl)
            
            # Grid for buttons
            grid_widget = QWidget()
            grid = QGridLayout(grid_widget)
            grid.setSpacing(8)
            grid.setContentsMargins(0, 5, 0, 0)
            
            row, col = 0, 0
            for name, data in actions.items():
                btn = QPushButton(name)
                btn.setMinimumHeight(45)
                btn.clicked.connect(lambda _, d=data: self._apply_pose(d))
                
                # Right-click to delete (Basic implementation)
                btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
                btn.customContextMenuRequested.connect(lambda pos, c=category, n=name: self._delete_macro(c, n))
                
                grid.addWidget(btn, row, col)
                
                col += 1
                if col > 1: # 2 Columns wide
                    col = 0
                    row += 1
            
            self.content_layout.addWidget(grid_widget)
            
        self.content_layout.addStretch()
        self.update_theme()

    def _apply_pose(self, pose_data):
        if self.kinematics:
            self.kinematics.set_target_pose(pose_data)

    def _save_current_pose(self):
        name = self.input_name.text().strip()
        if not name:
            return
        
        if not self.kinematics: return
        
        # Get current state from kinematics engine
        current_state = self.kinematics.current_state.copy()
        
        # Add to "Custom" category
        if "Custom" not in self.macros:
            self.macros["Custom"] = {}
            
        self.macros["Custom"][name] = current_state
        config_manager.save_macros(self.macros)
        
        self.input_name.clear()
        self._build_grid()

    def _delete_macro(self, category, name):
        # In a real app, show confirmation dialog
        if category in self.macros and name in self.macros[category]:
            del self.macros[category][name]
            config_manager.save_macros(self.macros)
            self._build_grid()

    def update_theme(self):
        p = theme_manager.active_palette
        
        # Input Styling
        self.input_name.setStyleSheet(f"""
            QLineEdit {{
                background-color: {p['bg_input']};
                color: {p['text_primary']};
                border: 1px solid {p['border_dim']};
                border-radius: 4px;
                padding: 5px;
            }}
        """)
        
        # Save Button
        self.btn_save_new.setStyleSheet(f"""
            QPushButton {{
                background-color: {p['bg_element']};
                color: {p['success']};
                font-weight: bold;
                border: 1px solid {p['border_dim']};
                border-radius: 4px;
            }}
            QPushButton:hover {{ background-color: {p['bg_hover']}; }}
        """)
        
        # Grid Buttons (found via children traversal)
        all_btns = self.content_widget.findChildren(QPushButton)
        for btn in all_btns:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {p['accent_main']}; 
                    color: {p['bg_app'] if theme_manager.current_theme_name == 'Cyber Dark' else '#fff'}; 
                    font-weight: bold; 
                    font-size: 11pt;
                    border-radius: 6px;
                    border: none;
                }}
                QPushButton:hover {{ background-color: {p['border_focus']}; }}
                QPushButton:pressed {{ background-color: {p['bg_hover']}; }}
            """)
            
        # Headers
        all_lbls = self.content_widget.findChildren(QLabel)
        for lbl in all_lbls:
            lbl.setStyleSheet(f"color: {p['text_muted']}; font-weight: bold; font-size: 10px; letter-spacing: 1px; margin-top: 10px;")