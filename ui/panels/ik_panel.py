from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QDoubleSpinBox, QGroupBox, QComboBox)
from PyQt6.QtCore import Qt

class IKPanel(QWidget):
    """
    Universal Inverse Kinematics Control.
    Select ANY robot link and move it to a Cartesian target.
    """
    def __init__(self, parent_window, kinematics):
        super().__init__(parent_window)
        self.kinematics = kinematics
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # --- HEADER ---
        lbl = QLabel("UNIVERSAL IK SOLVER")
        lbl.setStyleSheet("font-weight: bold; color: #007acc; font-size: 11px; letter-spacing: 1px;")
        layout.addWidget(lbl)
        
        # --- TARGET SELECTION ---
        sel_group = QGroupBox("Target End-Effector")
        sel_group.setStyleSheet("QGroupBox { border: 1px solid #3e3e42; font-weight: bold; margin-top: 10px; } QGroupBox::title { color: #ccc; }")
        sel_layout = QVBoxLayout(sel_group)
        
        self.cb_links = QComboBox()
        self.cb_links.setStyleSheet("padding: 5px; background: #333; color: #fff;")
        sel_layout.addWidget(self.cb_links)
        
        layout.addWidget(sel_group)
        
        # --- COORDINATES ---
        coord_group = QGroupBox("Target Coordinates (mm)")
        coord_group.setStyleSheet("QGroupBox { border: 1px solid #3e3e42; font-weight: bold; margin-top: 10px; } QGroupBox::title { color: #ccc; }")
        cg_layout = QVBoxLayout(coord_group)
        
        self.inputs = []
        for axis in ["X", "Y", "Z"]:
            h = QHBoxLayout()
            h.addWidget(QLabel(f"{axis}:"))
            sp = QDoubleSpinBox()
            sp.setRange(-5000, 5000)
            sp.setSingleStep(10)
            sp.setValue(0)
            sp.setStyleSheet("background-color: #252526; padding: 4px; border: 1px solid #555;")
            h.addWidget(sp)
            cg_layout.addLayout(h)
            self.inputs.append(sp)
            
        # Helper: Get Current Pos
        btn_get = QPushButton("GET CURRENT POSITION")
        btn_get.setStyleSheet("background-color: #444; color: #aaa; padding: 4px; font-size: 9pt;")
        btn_get.clicked.connect(self._get_current_pos)
        cg_layout.addWidget(btn_get)
            
        layout.addWidget(coord_group)
        
        # --- ACTION ---
        btn_solve = QPushButton("SOLVE & MOVE")
        btn_solve.setMinimumHeight(40)
        btn_solve.setStyleSheet("""
            QPushButton { background-color: #2e7d32; color: white; font-weight: bold; font-size: 11pt; border-radius: 4px; }
            QPushButton:hover { background-color: #388e3c; }
            QPushButton:pressed { background-color: #1b5e20; }
        """)
        btn_solve.clicked.connect(self._solve)
        layout.addWidget(btn_solve)
        
        layout.addStretch()
        
        # Populate List
        self._refresh_link_list()

    def _refresh_link_list(self):
        """Scans the robot model and fills the dropdown."""
        self.cb_links.clear()
        if self.kinematics and self.kinematics.model:
            # Sort links alphabetically
            links = sorted(self.kinematics.model.links.keys())
            
            # Prioritize common end-effectors for usability
            priority = []
            others = []
            for l in links:
                if any(x in l.lower() for x in ['hand', 'wrist', 'head', 'foot', 'tip']):
                    priority.append(l)
                else:
                    others.append(l)
            
            self.cb_links.addItems(priority)
            self.cb_links.insertSeparator(len(priority))
            self.cb_links.addItems(others)
            
            # Select first item
            if self.cb_links.count() > 0:
                self.cb_links.setCurrentIndex(0)

    def _get_current_pos(self):
        """Reads the Ghost Node position and fills the spinboxes."""
        link_name = self.cb_links.currentText()
        if not link_name or not self.kinematics: return
        
        if link_name in self.kinematics.ghost_nodes:
            node = self.kinematics.ghost_nodes[link_name]
            # Get absolute position (0,0,0 local mapped to world)
            from PyQt6.QtGui import QVector3D
            pos = node.transform().map(QVector3D(0,0,0))
            
            self.inputs[0].setValue(pos.x())
            self.inputs[1].setValue(pos.y())
            self.inputs[2].setValue(pos.z())

    def _solve(self):
        link_name = self.cb_links.currentText()
        coords = [s.value() for s in self.inputs]
        
        if self.kinematics:
            self.kinematics.solve_ik(coords, link_name)