import os
import logging
from PyQt6.QtWidgets import (QMainWindow, QWidget, QLabel, QMessageBox, QStackedWidget)
from PyQt6.QtCore import Qt

from core.robot_loader import RobotModel
from core.kinematics import KinematicsEngine
from core.config_manager import config_manager
from core.control_loop import BangBangController
from communication.serial_manager import SerialManager

# UI Components
from ui.layout_manager import LayoutManager

logger = logging.getLogger('inmoov_v13')

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Robot Studio - Universal Platform")
        self.resize(1366, 768) # Standard Laptop Res
        
        # 1. Initialize Singletons
        config_manager.load_all()
        self.serial = SerialManager()
        self.controller = BangBangController(self.serial, config_manager)
        
        # 2. Core Components
        self.robot_model = RobotModel()
        self.kinematics = None
        
        # 3. Load Data
        self._load_robot()
        
        # 4. Initialize UI via Layout Manager
        self.ui = LayoutManager(self, self.robot_model, self.kinematics, self.serial, self.controller)
        self.ui.setup_ui()
        self.ui.connect_signals()
        
        # Set Default View
        self.ui.set_view(0)

    def _load_robot(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(base_dir, "config", "robots", "inmoov_standard.json")
        
        if self.robot_model.load_from_file(config_path):
            self.kinematics = KinematicsEngine(self.robot_model)
        else:
            logger.error("Failed to initialize Robot Model.")

    # --- Callbacks ---
    def _reload_robot_from_file(self, file_path):
        """Called by Architect Mode to reload the robot."""
        logger.info(f"Reloading robot from {file_path}")
        if self.robot_model.load_from_file(file_path):
            # Recreate Kinematics
            self.kinematics = KinematicsEngine(self.robot_model)
            
            # Recreate Viewport Scene
            if self.ui.viewport:
                self.ui.viewport.kinematics = self.kinematics
                self.ui.viewport._init_scene()
            
            # Recreate Inspector (to refresh sliders)
            # Accessing LayoutManager's internal inspector reference
            if self.ui.inspector:
                self.removeDockWidget(self.ui.inspector)
                self.ui.inspector.deleteLater()
            
            from ui.panels.inspector import InspectorPanel
            self.ui.inspector = InspectorPanel(self, self.robot_model, self.kinematics, self.ui.viewport)
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.ui.inspector)
            self.ui.architect = self.ui.inspector.architect_widget
            
            # Re-bind signals since we destroyed the inspector
            self.ui.connect_signals() 
            
            QMessageBox.information(self, "Loaded", f"Loaded {os.path.basename(file_path)}")
        else:
            QMessageBox.warning(self, "Error", "Failed to load file.")

    def _on_structure_change(self):
        if self.kinematics and self.ui.viewport:
            self.kinematics.rebuild_scene(self.ui.viewport.view_widget)

    def _on_joint_move(self, joint_id, value):
        if self.kinematics:
            # 1. Update Visuals
            self.kinematics.update_state_from_sensors({str(joint_id): float(value)})
            if self.ui.viewport: self.ui.viewport.update_view()
            
            # 2. Hardware Control
            hw_config = config_manager.get_pin_config(joint_id)
            if hw_config:
                m_type = hw_config.get('motor_type', 'n20')
                if m_type == 'sg90':
                    cmd = self.serial.protocol_translator.translate_servo_command(int(joint_id), float(value), hw_config)
                    if cmd: self.serial.send_raw(cmd)
                else:
                    self.controller.set_target(joint_id, value)