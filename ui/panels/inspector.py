from PyQt6.QtWidgets import (QDockWidget, QWidget, QVBoxLayout, QTabWidget, 
                             QScrollArea, QFrame, QLabel, QSlider)
from PyQt6.QtCore import Qt
from ui.modes.architect_mode import ArchitectMode
from core.theme_manager import theme_manager

class InspectorPanel(QDockWidget):
    def __init__(self, parent_window, robot_model, kinematics, viewport):
        super().__init__("Inspector", parent_window)
        self.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)
        
        self.robot_model = robot_model
        self.kinematics = kinematics
        self.viewport = viewport
        self.main_window = parent_window 
        self.sliders = {}
        
        self.setTitleBarWidget(QWidget()) # Hide dock title
        self._setup_ui()
        
        theme_manager.theme_changed.connect(self.update_theme)

    def _setup_ui(self):
        self.tabs = QTabWidget()
        self.pilot_widget = self._create_pilot_tab()
        self.tabs.addTab(self.pilot_widget, "Pilot")
        self.architect_widget = ArchitectMode(self.robot_model)
        
        self.architect_widget.model_changed.connect(self.main_window._on_structure_change)
        self.architect_widget.request_load.connect(self.main_window._reload_robot_from_file)
        
        if self.viewport:
            self.architect_widget.link_selected.connect(self.viewport.select_link)
            self.viewport.nudge_requested.connect(self.architect_widget.on_viewport_nudge)
            
        self.tabs.addTab(self.architect_widget, "Architect")
        self.setWidget(self.tabs)
        self.update_theme()

    def update_theme(self):
        p = theme_manager.active_palette
        # Specific overrides for the Pilot Control inner frame
        if hasattr(self, 'inner_widget'):
            self.inner_widget.setStyleSheet(f"background-color: {p['bg_surface']};")
        
        # Update styling for all frames in pilot
        if hasattr(self, 'controls_layout'):
            for i in range(self.controls_layout.count()):
                item = self.controls_layout.itemAt(i)
                if item and item.widget() and isinstance(item.widget(), QFrame):
                    item.widget().setStyleSheet(f"background-color: {p['bg_element']}; border: 1px solid {p['border_dim']}; border-radius: 4px;")

    def _create_pilot_tab(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        
        self.inner_widget = QWidget()
        self.controls_layout = QVBoxLayout(self.inner_widget)
        self.controls_layout.setSpacing(8)
        
        title = QLabel("ACTUATOR CONTROL")
        title.setStyleSheet(f"font-weight: bold; font-size: 14px; padding: 10px; color: {theme_manager.get_color('accent_main')};")
        self.controls_layout.addWidget(title)

        if self.robot_model.root:
            self._recurse_controls(self.robot_model.root)

        self.controls_layout.addStretch()
        self.inner_widget.setLayout(self.controls_layout)
        scroll.setWidget(self.inner_widget)
        layout.addWidget(scroll)
        return container

    def _recurse_controls(self, link):
        if link.joint and link.joint.id:
            jid = str(link.joint.id)
            if jid.isdigit() and jid not in self.sliders:
                frame = QFrame()
                fl = QVBoxLayout(frame)
                
                lbl = QLabel(f"[{jid}] {link.joint.name}")
                lbl.setStyleSheet("font-weight: bold; border: none;")
                fl.addWidget(lbl)
                
                sl = QSlider(Qt.Orientation.Horizontal)
                sl.setRange(int(link.joint.limits[0]), int(link.joint.limits[1]))
                sl.setValue(90)
                sl.setStyleSheet("border: none;")
                
                val_lbl = QLabel("90")
                val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
                val_lbl.setStyleSheet(f"color: {theme_manager.get_color('accent_main')}; border: none;")
                fl.addWidget(val_lbl)

                sl.valueChanged.connect(lambda val, j=jid, l=val_lbl: [l.setText(str(val)), self.main_window._on_joint_move(j, val)])
                
                fl.addWidget(sl)
                self.controls_layout.addWidget(frame)
                self.sliders[jid] = sl

        for child in link.children:
            self._recurse_controls(child)