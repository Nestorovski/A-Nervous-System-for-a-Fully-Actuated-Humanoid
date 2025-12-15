import logging
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QCheckBox, QFrame, QHBoxLayout, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QVector3D
from core.theme_manager import theme_manager
from ui.widgets.custom_icons import ModernSidebarButton

try:
    import pyqtgraph.opengl as gl
    HAS_GL = True
except ImportError:
    HAS_GL = False

logger = logging.getLogger('inmoov_v13')

class Viewport3D(QWidget):
    nudge_requested = pyqtSignal(int, float)
    joint_dragged = pyqtSignal(str, float)

    def __init__(self, kinematics_engine):
        super().__init__()
        self.kinematics = kinematics_engine
        self.view_widget = None
        self.gizmo_item = None
        self.selected_link_name = None
        self.last_mouse_pos = None
        
        self._setup_ui()
        if HAS_GL and self.kinematics:
            self._init_scene()
            
        theme_manager.theme_changed.connect(self.update_hud_theme)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        if HAS_GL:
            self.view_widget = gl.GLViewWidget()
            self.view_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            self.view_widget.setBackgroundColor((30, 30, 35, 255))
            self.view_widget.setCameraPosition(distance=1000, elevation=30, azimuth=45)
            
            self.view_widget.mousePressEvent = self.on_mouse_press
            self.view_widget.mouseMoveEvent = self.on_mouse_move
            self.view_widget.mouseReleaseEvent = self.on_mouse_release
            self.view_widget.keyPressEvent = self.keyPressEvent

            grid = gl.GLGridItem()
            grid.setSize(2000, 2000, 1)
            grid.setSpacing(100, 100, 1)
            grid.setColor((60, 60, 60, 255))
            self.view_widget.addItem(grid)
            
            self.gizmo_item = gl.GLAxisItem()
            self.gizmo_item.setSize(100, 100, 100)
            self.gizmo_item.setVisible(False)
            self.view_widget.addItem(self.gizmo_item)
            
            layout.addWidget(self.view_widget, 1)
            self._create_hud(layout)
            self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        else:
            layout.addWidget(QLabel("No 3D Support"))

    def _create_hud(self, parent_layout):
        self.hud = QFrame()
        self.hud.setFixedHeight(60)
        
        hl = QHBoxLayout(self.hud)
        hl.setContentsMargins(15, 5, 15, 5)
        hl.setSpacing(10)
        
        # --- NAVIGATION GROUP (Using ModernSidebarButton) ---
        btn_size = (36, 36)
        
        self.btn_home = ModernSidebarButton("home", "Reset View", size=btn_size)
        self.btn_home.clicked.connect(self.reset_view)
        # Use setCheckable(False) so they behave like click buttons, not toggles
        self.btn_home.setCheckable(False) 
        
        self.btn_in = ModernSidebarButton("plus", "Zoom In", size=btn_size)
        self.btn_in.clicked.connect(self.zoom_in)
        self.btn_in.setCheckable(False)
        
        self.btn_out = ModernSidebarButton("minus", "Zoom Out", size=btn_size)
        self.btn_out.clicked.connect(self.zoom_out)
        self.btn_out.setCheckable(False)
        
        self.btn_front = ModernSidebarButton("cube_front", "Front View", size=btn_size)
        # FIX: -90 usually points to Front in PyQtGraph's default coordinate system
        self.btn_front.clicked.connect(lambda: self.set_angle(-90, 0)) 
        self.btn_front.setCheckable(False)
        
        self.btn_side = ModernSidebarButton("cube_side", "Side View", size=btn_size)
        # FIX: 0 usually points to Side (Right)
        self.btn_side.clicked.connect(lambda: self.set_angle(0, 0))
        self.btn_side.setCheckable(False)

        hl.addWidget(self.btn_home)
        hl.addWidget(self.btn_in)
        hl.addWidget(self.btn_out)
        hl.addWidget(self.btn_front)
        hl.addWidget(self.btn_side)

        # Divider
        line = QFrame()
        line.setFrameShape(QFrame.Shape.VLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setFixedWidth(2)
        hl.addWidget(line)

        # --- VISUALS GROUP ---
        lbl = QLabel("LAYERS:")
        lbl.setStyleSheet("font-weight: bold; font-size: 11px; margin-right: 5px;")
        hl.addWidget(lbl)
        
        self.chk_ghost = QCheckBox("Target")
        self.chk_ghost.setChecked(True)
        self.chk_ghost.toggled.connect(self._toggle_layers)
        hl.addWidget(self.chk_ghost)
        
        self.chk_col = QCheckBox("Safety")
        self.chk_col.toggled.connect(self._toggle_layers)
        hl.addWidget(self.chk_col)
        
        hl.addStretch()
        
        self.hint = QLabel("Ctrl+Click to Drag Link")
        self.hint.setStyleSheet("font-style: italic; font-size: 11px;")
        hl.addWidget(self.hint)
        
        parent_layout.addWidget(self.hud, 0)
        self.update_hud_theme()

    # --- NAVIGATION LOGIC ---
    def reset_view(self):
        if self.view_widget:
            self.view_widget.setCameraPosition(pos=QVector3D(0,0,0), distance=1000, elevation=30, azimuth=45)

    def zoom_in(self):
        if self.view_widget:
            self.view_widget.opts['distance'] *= 0.8
            self.view_widget.update()

    def zoom_out(self):
        if self.view_widget:
            self.view_widget.opts['distance'] *= 1.2
            self.view_widget.update()

    def set_angle(self, azimuth, elevation):
        if self.view_widget:
            self.view_widget.setCameraPosition(pos=QVector3D(0,0,0), distance=1000, elevation=elevation, azimuth=azimuth)

    def update_hud_theme(self):
        p = theme_manager.active_palette
        self.hud.setStyleSheet(f"background-color: {p['bg_surface']}; border-top: 2px solid {p['accent_main']};")
        self.hint.setStyleSheet(f"color: {p['text_muted']}; font-style: italic;")
        
        # Checkbox Styling
        chk_css = f"""
            QCheckBox {{ 
                color: {p['text_primary']}; 
                font-weight: bold; 
                spacing: 8px;
            }}
            QCheckBox::indicator {{ 
                width: 16px; 
                height: 16px; 
                border: 1px solid {p['border_dim']}; 
                border-radius: 3px; 
                background: {p['bg_input']}; 
            }}
            QCheckBox::indicator:checked {{ 
                background: {p['accent_main']}; 
                border-color: {p['accent_main']}; 
                image: url(none); 
            }}
        """
        self.chk_ghost.setStyleSheet(chk_css)
        self.chk_col.setStyleSheet(chk_css)

        # Force Button Repaint via Theme Manager Trigger (handled by class internal connection)
        self.btn_home.update()
        
        # 3D BG
        if theme_manager.current_theme_name == "Engineering Grey":
            self.view_widget.setBackgroundColor((220, 220, 225, 255))
        else:
            self.view_widget.setBackgroundColor((30, 30, 35, 255))

    def _toggle_layers(self):
        if self.kinematics:
            self.kinematics.set_visibility(self.chk_ghost.isChecked(), self.chk_col.isChecked())

    def _init_scene(self):
        self.kinematics.initialize_view(self.view_widget)

    def update_view(self):
        if self.view_widget: 
            self.view_widget.update()
            self._update_gizmo_pos()

    def select_link(self, link_name):
        self.selected_link_name = link_name
        self.gizmo_item.setVisible(True)
        self._update_gizmo_pos()
        self.setFocus()

    def _update_gizmo_pos(self):
        if not self.selected_link_name or not self.kinematics: return
        if self.selected_link_name in self.kinematics.scene_nodes:
            mesh = self.kinematics.scene_nodes[self.selected_link_name]
            self.gizmo_item.setTransform(mesh.transform())

    def keyPressEvent(self, event):
        if not self.selected_link_name:
            super().keyPressEvent(event)
            return
        step = 10.0
        if event.modifiers() & Qt.KeyboardModifier.ShiftModifier: step = 50.0
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier: step = 1.0
        if event.key() == Qt.Key.Key_Left:     self.nudge_requested.emit(0, -step)
        elif event.key() == Qt.Key.Key_Right:  self.nudge_requested.emit(0, step)
        elif event.key() == Qt.Key.Key_Up:     self.nudge_requested.emit(1, step)
        elif event.key() == Qt.Key.Key_Down:   self.nudge_requested.emit(1, -step)
        elif event.key() == Qt.Key.Key_PageUp:   self.nudge_requested.emit(2, step)
        elif event.key() == Qt.Key.Key_PageDown: self.nudge_requested.emit(2, -step)
        else: super().keyPressEvent(event)

    def on_mouse_press(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton and (ev.modifiers() & Qt.KeyboardModifier.ControlModifier):
            self.last_mouse_pos = ev.pos()
            ev.accept()
        else:
            gl.GLViewWidget.mousePressEvent(self.view_widget, ev)

    def on_mouse_move(self, ev):
        if self.last_mouse_pos and (ev.modifiers() & Qt.KeyboardModifier.ControlModifier):
            dy = ev.pos().y() - self.last_mouse_pos.y()
            delta = -dy * 0.5 
            self.joint_dragged.emit("ACTIVE", delta) 
            self.last_mouse_pos = ev.pos()
            ev.accept()
        else:
            gl.GLViewWidget.mouseMoveEvent(self.view_widget, ev)

    def on_mouse_release(self, ev):
        self.last_mouse_pos = None
        gl.GLViewWidget.mouseReleaseEvent(self.view_widget, ev)