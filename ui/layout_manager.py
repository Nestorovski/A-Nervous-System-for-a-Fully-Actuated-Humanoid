from PyQt6.QtWidgets import (QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, 
                             QFrame, QPushButton, QLabel, QSplitter)
from PyQt6.QtCore import Qt
import logging

# Import Panels
from ui.viewport_3d import Viewport3D
from ui.modes.engineer_mode import EngineerMode
from ui.modes.documentation_mode import DocumentationMode
from ui.modes.settings_mode import SettingsMode
from ui.modes.code_mode import CodeMode  # <--- NEW IMPORT

from ui.panels.sidebar import Sidebar
from ui.panels.inspector import InspectorPanel
from ui.panels.sequencer import SequencerPanel
from ui.panels.quick_actions import QuickActionsPanel
from ui.panels.ik_panel import IKPanel

logger = logging.getLogger('inmoov_v13')

class LayoutManager:
    """
    Manages the 'IDE-Style' Layout.
    """
    def __init__(self, main_window, robot_model, kinematics, serial, controller):
        self.mw = main_window
        self.robot_model = robot_model
        self.kinematics = kinematics
        self.serial = serial
        self.controller = controller
        
        self.architect = None
        self.viewport = None

    def setup_ui(self):
        # 1. Main Container
        main_container = QWidget()
        main_layout = QHBoxLayout(main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 2. Sidebar (Fixed Left)
        self.sidebar = Sidebar()
        main_layout.addWidget(self.sidebar)
        
        # 3. Tool Panel (Dynamic Left)
        self._create_tool_panel(main_layout)
        
        # 4. Central Stack
        self.central_stack = QStackedWidget()
        
        # Index 0: Home
        self.viewport = Viewport3D(self.kinematics)
        self.central_stack.addWidget(self.viewport)
        
        # Index 1: Engineer
        self.engineer = EngineerMode(self.serial)
        self.central_stack.addWidget(self.engineer)
        
        # Index 2: Docs
        self.docs = DocumentationMode()
        self.central_stack.addWidget(self.docs)
        
        # Index 3: Settings
        self.settings = SettingsMode()
        self.central_stack.addWidget(self.settings)
        
        # Index 4: Code Mode (NEW)
        self.code_mode = CodeMode()
        self.central_stack.addWidget(self.code_mode)
        
        main_layout.addWidget(self.central_stack, 1)
        
        self.mw.setCentralWidget(main_container)

        # 5. Right Dock (Inspector)
        if self.robot_model.root:
            self.inspector = InspectorPanel(self.mw, self.robot_model, self.kinematics, self.viewport)
            self.mw.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.inspector)
            self.architect = self.inspector.architect_widget

    def _create_tool_panel(self, parent_layout):
        self.tool_container = QWidget()
        self.tool_container.setFixedWidth(300)
        self.tool_container.setStyleSheet("background-color: #1e1e1e; border-right: 1px solid #3e3e42;")
        
        layout = QVBoxLayout(self.tool_container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QWidget()
        header.setStyleSheet("background-color: #252526; border-bottom: 1px solid #3e3e42; min-height: 35px;")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(15, 0, 5, 0)
        
        self.lbl_tool_title = QLabel("TOOLS")
        self.lbl_tool_title.setStyleSheet("font-weight: bold; color: #ccc; font-size: 11px;")
        hl.addWidget(self.lbl_tool_title)
        hl.addStretch()
        
        btn_close = QPushButton("✕")
        btn_close.setFixedSize(30, 30)
        btn_close.setFlat(True)
        btn_close.clicked.connect(self.close_tool_panel)
        hl.addWidget(btn_close)
        
        layout.addWidget(header)
        
        # Stack
        self.tool_stack = QStackedWidget()
        self.quick_actions = QuickActionsPanel(self.mw, self.kinematics)
        self.ik_panel = IKPanel(self.mw, self.kinematics)
        self.sequencer_panel = SequencerPanel(self.mw, self.kinematics)
        
        self.tool_stack.addWidget(self.quick_actions) # 0
        self.tool_stack.addWidget(self.ik_panel)      # 1
        self.tool_stack.addWidget(self.sequencer_panel) # 2
        
        layout.addWidget(self.tool_stack)
        
        parent_layout.addWidget(self.tool_container)
        self.tool_container.hide()

    def connect_signals(self):
        sb = self.sidebar
        
        # Navigation connections
        sb.btn_home.clicked.connect(lambda: self.set_view(0))
        sb.btn_engineer.clicked.connect(lambda: self.set_view(1))
        sb.btn_docs.clicked.connect(lambda: self.set_view(2))
        sb.btn_settings.clicked.connect(lambda: self.set_view(3))
        sb.btn_code.clicked.connect(lambda: self.set_view(4)) # New Connection
        sb.btn_debug.clicked.connect(lambda: self.set_view(1)) # Redirect debug to engineer for now
        
        # Tool connections
        sb.btn_actions.clicked.connect(lambda: self.toggle_tool(0, "QUICK ACTIONS"))
        sb.btn_ik.clicked.connect(lambda: self.toggle_tool(1, "INVERSE KINEMATICS"))
        sb.btn_seq.clicked.connect(lambda: self.toggle_tool(2, "ANIMATION SEQUENCER"))
        
        # Data connections
        self.serial.raw_log_received.connect(self.engineer.on_raw_log)
        self.serial.pots_updated.connect(self.engineer.on_pots_update)
        self.serial.pots_updated.connect(self.controller.update_sensors)

        if self.viewport and self.architect:
            self.architect.link_selected.connect(self.viewport.select_link)
            self.viewport.nudge_requested.connect(self.architect.on_viewport_nudge)

    def set_view(self, index):
        self.central_stack.setCurrentIndex(index)
        is_3d = (index == 0)
        
        if is_3d:
            self.inspector.show()
        else:
            self.inspector.hide()
            self.close_tool_panel()
            
        # Update Icon States
        self.sidebar.btn_home.setChecked(index == 0)
        self.sidebar.btn_engineer.setChecked(index == 1)
        self.sidebar.btn_docs.setChecked(index == 2)
        self.sidebar.btn_settings.setChecked(index == 3)
        self.sidebar.btn_code.setChecked(index == 4)

    def toggle_tool(self, index, title):
        # Force 3D view
        if self.central_stack.currentIndex() != 0:
            self.set_view(0)

        # Logic: If clicking same tool, close it. Else open/switch.
        if self.tool_container.isVisible() and self.tool_stack.currentIndex() == index:
            self.close_tool_panel()
        else:
            self.tool_stack.setCurrentIndex(index)
            self.lbl_tool_title.setText(title)
            self.tool_container.show()
            self._update_tool_buttons(index)

    def close_tool_panel(self):
        self.tool_container.hide()
        self._update_tool_buttons(-1)

    def _update_tool_buttons(self, idx):
        self.sidebar.btn_actions.setChecked(idx == 0)
        self.sidebar.btn_ik.setChecked(idx == 1)
        self.sidebar.btn_seq.setChecked(idx == 2)