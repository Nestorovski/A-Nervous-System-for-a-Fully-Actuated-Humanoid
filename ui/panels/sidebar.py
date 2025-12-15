from PyQt6.QtWidgets import (QDockWidget, QWidget, QVBoxLayout, QButtonGroup, QFrame, QLabel)
from PyQt6.QtCore import Qt
from ui.widgets.custom_icons import ModernSidebarButton
from core.theme_manager import theme_manager

class Sidebar(QDockWidget):
    """
    The Fixed Navigation Bar.
    """
    def __init__(self, parent=None):
        super().__init__("Modes", parent)
        self.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.setTitleBarWidget(QWidget()) # Hide title bar
        self.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea)
        
        self.container = QWidget()
        self.container.setFixedWidth(64) 
        
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(0, 10, 0, 10)
        layout.setSpacing(5)
        
        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)

        # --- PRIMARY VIEWS ---
        self._add_label(layout, "VIEW")
        self.btn_home = self._add_btn(layout, "home", "3D Pilot View")
        self.btn_engineer = self._add_btn(layout, "engineer", "Hardware Setup & Testing")
        self.btn_docs = self._add_btn(layout, "docs", "Documentation")
        self.btn_settings = self._add_btn(layout, "settings", "Settings")
        
        self._add_separator(layout)
        
        # --- TOOLS ---
        self._add_label(layout, "TOOL")
        self.btn_actions = self._add_btn(layout, "bolt", "Quick Actions")
        self.btn_ik = self._add_btn(layout, "ik", "Inverse Kinematics")
        self.btn_seq = self._add_btn(layout, "sequencer", "Sequencer")
        
        layout.addStretch()
        self._add_separator(layout)
        
        # --- SYSTEM / DEV ---
        self.btn_code = self._add_btn(layout, "code", "Developer Mode (JSON Editor)")
        self.btn_debug = self._add_btn(layout, "debug", "Debug Console")
        
        # Set Default
        self.btn_home.setChecked(True)
        self.setWidget(self.container)
        
        # Initial Theme Apply & Listen
        self.update_theme()
        theme_manager.theme_changed.connect(self.update_theme)

    def update_theme(self):
        """Updates background colors and separator lines."""
        p = theme_manager.active_palette
        self.container.setStyleSheet(f"""
            background-color: {p['bg_surface']}; 
            border-right: 1px solid {p['border_dim']};
        """)
        
        # Manually update separators since they are QFrames
        separator_style = f"background-color: {p['border_dim']}; margin: 10px 5px;"
        for child in self.container.findChildren(QFrame):
            if child.frameShape() == QFrame.Shape.HLine:
                child.setStyleSheet(separator_style)
        
        # Update Labels
        for child in self.container.findChildren(QLabel):
            child.setStyleSheet(f"color: {p['text_muted']}; font-size: 9px; font-weight: bold; margin-top: 5px;")
            
        # Trigger repaint on buttons
        for btn in self.btn_group.buttons():
            btn.update()

    def _add_btn(self, layout, icon, tip):
        btn = ModernSidebarButton(icon, tip)
        layout.addWidget(btn)
        self.btn_group.addButton(btn) 
        return btn

    def _add_separator(self, layout):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)

    def _add_label(self, layout, text):
        lbl = QLabel(text)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Style is set in update_theme
        layout.addWidget(lbl)