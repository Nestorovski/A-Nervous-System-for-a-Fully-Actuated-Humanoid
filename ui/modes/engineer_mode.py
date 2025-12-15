from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                             QTableWidget, QTableWidgetItem, QHeaderView, 
                             QPushButton, QLabel, QComboBox, QPlainTextEdit,
                             QGridLayout, QMessageBox, QTabWidget,
                             QScrollArea, QSpinBox, QFileDialog, QFrame, QSlider)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QBrush
import serial.tools.list_ports
from core.config_manager import config_manager
from ui.widgets.custom_icons import ModernSidebarButton
from core.theme_manager import theme_manager
import logging
import os

logger = logging.getLogger('inmoov_v13')

class EngineerMode(QWidget):
    def __init__(self, serial_manager):
        super().__init__()
        self.serial = serial_manager
        self.live_scan = False
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.scroll.setStyleSheet("background-color: transparent;")
        
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background: transparent;")
        self._setup_ui(self.content_widget)
        
        self.scroll.setWidget(self.content_widget)
        main_layout.addWidget(self.scroll)
        
        # Diagnostics Timer
        self.scan_timer = QTimer()
        self.scan_timer.timeout.connect(self._on_scan_tick)
        self.scan_timer.setInterval(100) 

        # Signals
        config_manager.hardware_map_changed.connect(self._populate_table)
        theme_manager.theme_changed.connect(self._update_colors)

    def _setup_ui(self, container):
        layout = QVBoxLayout(container)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Header
        self.lbl_title = QLabel("ENGINEERING CONSOLE")
        layout.addWidget(self.lbl_title)
        
        self.tabs = QTabWidget()
        
        self.map_tab = QWidget()
        self._build_map_tab(self.map_tab)
        self.tabs.addTab(self.map_tab, "Pin Mapping Editor")

        self.tester_tab = QWidget()
        self._build_tester_tab(self.tester_tab)
        self.tabs.addTab(self.tester_tab, "System Diagnostic")
        
        layout.addWidget(self.tabs)
        self._update_colors() # Apply initial styling

    # ==========================================================
    # 🔧 TAB 1: PIN MAPPING EDITOR
    # ==========================================================
    def _build_map_tab(self, parent):
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(15, 15, 15, 15)
        
        self.lbl_file_status = QLabel(f"Current File: {os.path.basename(config_manager.current_map_file)}")
        layout.addWidget(self.lbl_file_status)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID", "Description", "Mux Port", "PCA Pin", "Device Type", "ADS Channel", "Live Test"])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.table)
        
        # --- ACTION BAR (Updated with ModernSidebarButton) ---
        action_bar = QHBoxLayout()
        action_bar.setSpacing(10)
        
        # Load Map
        self.btn_open = ModernSidebarButton("open", "Load Hardware Map File", size=(40, 40))
        self.btn_open.setCheckable(False)
        self.btn_open.clicked.connect(self._load_mapping_file)
        
        # Save As
        self.btn_save_as = ModernSidebarButton("add", "Save Hardware Map As...", size=(40, 40))
        self.btn_save_as.setCheckable(False)
        self.btn_save_as.clicked.connect(self._save_mapping_as)
        
        # Quick Save
        self.btn_save = ModernSidebarButton("save", "Overwrite Current File", size=(60, 40))
        self.btn_save.setCheckable(False)
        self.btn_save.clicked.connect(lambda: self._save_mapping(None))
        
        # Labels for clarity
        action_bar.addWidget(self.btn_open)
        action_bar.addWidget(QLabel("Load"))
        
        action_bar.addSpacing(20)
        
        action_bar.addWidget(self.btn_save_as)
        action_bar.addWidget(QLabel("Save As"))
        
        action_bar.addStretch()
        
        action_bar.addWidget(self.btn_save)
        action_bar.addWidget(QLabel("Save"))
        
        layout.addLayout(action_bar)
        
        self._populate_table()

    def _populate_table(self):
        self.lbl_file_status.setText(f"Current File: {os.path.basename(config_manager.current_map_file)}")
        mapping = config_manager.hardware_map
        self.table.setRowCount(0)
        
        sorted_ids = sorted(mapping.keys(), key=lambda x: int(x))
        self.table.setRowCount(len(sorted_ids))
        
        for row, jid in enumerate(sorted_ids):
            data = mapping[jid]
            
            # 0. ID
            item_id = QTableWidgetItem(str(jid))
            item_id.setFlags(item_id.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, item_id)
            
            # 1. Name
            self.table.setItem(row, 1, QTableWidgetItem(data.get("name", "Unknown")))
            
            # 2. Mux
            cb_mux = QComboBox()
            cb_mux.addItems([str(i) for i in range(8)])
            cb_mux.setCurrentText(str(data.get("mux_port", 0)))
            self.table.setCellWidget(row, 2, cb_mux)
            
            # 3. Pin
            sb_pin = QSpinBox()
            sb_pin.setRange(0, 15)
            sb_pin.setValue(int(data.get("pca_pin", 0)))
            self.table.setCellWidget(row, 3, sb_pin)
            
            # 4. Type
            cb_type = QComboBox()
            cb_type.addItems(["n20", "sg90", "stepper"])
            cb_type.setCurrentText(data.get("motor_type", "n20"))
            self.table.setCellWidget(row, 4, cb_type)
            
            # 5. ADS
            sb_ads = QSpinBox()
            sb_ads.setRange(-1, 3) 
            sb_ads.setValue(int(data.get("ads_channel")) if data.get("ads_channel") is not None else -1)
            sb_ads.setSpecialValueText("None")
            self.table.setCellWidget(row, 5, sb_ads)
            
            # 6. Live
            self.table.setItem(row, 6, QTableWidgetItem("-"))

    def _gather_table_data(self):
        new_map = {}
        for row in range(self.table.rowCount()):
            jid = self.table.item(row, 0).text()
            name = self.table.item(row, 1).text()
            mux = int(self.table.cellWidget(row, 2).currentText())
            pin = self.table.cellWidget(row, 3).value()
            mtype = self.table.cellWidget(row, 4).currentText()
            ads = self.table.cellWidget(row, 5).value()
            new_map[jid] = {"name": name, "mux_port": mux, "pca_pin": pin, "motor_type": mtype, "ads_channel": ads if ads != -1 else None}
        return new_map

    def _load_mapping_file(self):
        start_dir = os.path.join(config_manager.base_dir, "config", "hardware")
        fname, _ = QFileDialog.getOpenFileName(self, "Load Hardware Map", start_dir, "JSON Files (*.json)")
        if fname:
            if config_manager.load_hardware_map(fname):
                QMessageBox.information(self, "Success", f"Loaded configuration: {os.path.basename(fname)}")
            else:
                QMessageBox.critical(self, "Error", "Failed to load configuration file.")

    def _save_mapping_as(self):
        start_dir = os.path.join(config_manager.base_dir, "config", "hardware")
        fname, _ = QFileDialog.getSaveFileName(self, "Save Hardware Map", start_dir, "JSON Files (*.json)")
        if fname: self._save_mapping(fname)

    def _save_mapping(self, path):
        data = self._gather_table_data()
        if config_manager.save_hardware_map(data, path):
            QMessageBox.information(self, "Success", "Hardware configuration saved.")
        else:
            QMessageBox.critical(self, "Error", "Failed to save configuration.")

    # ==========================================================
    # ⚙️ TAB 2: SYSTEM TESTER
    # ==========================================================
    def _build_tester_tab(self, parent):
        layout = QVBoxLayout(parent)
        
        # Connection Box
        conn_box = QGroupBox("SERIAL CONNECTION")
        conn_layout = QHBoxLayout(conn_box)
        
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(200)
        self._refresh_ports()
        
        btn_refresh = ModernSidebarButton("refresh", "Refresh Ports", size=(40, 35))
        btn_refresh.setCheckable(False)
        btn_refresh.clicked.connect(self._refresh_ports)
        
        self.btn_connect = QPushButton("CONNECT")
        self.btn_connect.setFixedSize(140, 35)
        self.btn_connect.clicked.connect(self._toggle_connect)
        
        self.mod_combo = QComboBox()
        self.mod_combo.addItems(["Direct (No Mux)"] + [f"Port {i}" for i in range(8)])
        
        conn_layout.addWidget(QLabel("COM Port:"))
        conn_layout.addWidget(self.port_combo)
        conn_layout.addWidget(btn_refresh)
        conn_layout.addWidget(self.btn_connect)
        conn_layout.addSpacing(30)
        conn_layout.addWidget(QLabel("Mux Context:"))
        conn_layout.addWidget(self.mod_combo)
        conn_layout.addStretch()
        
        layout.addWidget(conn_box)
        
        grid = QHBoxLayout()
        
        # Left: Diagnostics
        diag_box = QGroupBox("DIAGNOSTICS")
        diag_layout = QVBoxLayout(diag_box)
        
        # I2C Scan
        row_i2c = QHBoxLayout()
        btn_scan = QPushButton("SCAN I2C BUS")
        btn_scan.clicked.connect(lambda: self._send_cmd("SCAN_I2C"))
        self.lbl_i2c = QLabel("Idle")
        row_i2c.addWidget(btn_scan)
        row_i2c.addWidget(self.lbl_i2c)
        diag_layout.addLayout(row_i2c)
        
        # --- POTS SNAPSHOT ---
        row_pots = QHBoxLayout()
        btn_read = QPushButton("READ SNAPSHOT")
        btn_read.clicked.connect(lambda: self._send_cmd("TEST_POTS"))
        self.lbl_raw_pots = QLabel("--  --  --  --")
        row_pots.addWidget(btn_read)
        row_pots.addWidget(self.lbl_raw_pots)
        diag_layout.addLayout(row_pots)
        
        # Live Stream
        self.btn_live = QPushButton("START LIVE DATA STREAM")
        self.btn_live.setCheckable(True)
        self.btn_live.setMinimumHeight(40)
        self.btn_live.clicked.connect(self._toggle_live)
        diag_layout.addWidget(self.btn_live)
        
        diag_layout.addStretch()
        grid.addWidget(diag_box, 1)
        
        # Right: Actuator Tests (Motors & Servos)
        actuator_col = QVBoxLayout()
        
        # A. DC MOTORS
        motor_box = QGroupBox("DC MOTORS (Full Speed Pulse)")
        motor_layout = QGridLayout(motor_box)
        motors = ["MOTOR1A", "MOTOR1B", "MOTOR2A", "MOTOR2B"]
        for i, m in enumerate(motors):
            motor_layout.addWidget(QLabel(m), i, 0)
            btn_fwd = QPushButton("FWD")
            # Uses value 50, but Firmware will treat as 100% Bang-Bang
            btn_fwd.pressed.connect(lambda m=m: self._send_cmd(f"TEST_{m}_FWD:50"))
            btn_fwd.released.connect(lambda m=m: self._send_cmd(f"TEST_{m}_FWD:0"))
            motor_layout.addWidget(btn_fwd, i, 1)
            
            btn_rev = QPushButton("REV")
            btn_rev.pressed.connect(lambda m=m: self._send_cmd(f"TEST_{m}_REV:50"))
            btn_rev.released.connect(lambda m=m: self._send_cmd(f"TEST_{m}_REV:0"))
            motor_layout.addWidget(btn_rev, i, 2)
            
        actuator_col.addWidget(motor_box)

        # B. SERVOS (NEW ADDITION)
        servo_box = QGroupBox("SERVOS (0° - 180°)")
        servo_layout = QGridLayout(servo_box)
        servos = [("SERVO1", 6), ("SERVO2", 7), ("SERVO3", 14), ("SERVO4", 15)]
        
        for i, (name, pin) in enumerate(servos):
            servo_layout.addWidget(QLabel(f"{name} (P{pin})"), i, 0)
            
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(0, 180)
            slider.setValue(90)
            
            val_lbl = QLabel("90")
            val_lbl.setFixedWidth(30)
            val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
            
            # Using specific handler method to avoid lambda closure bug
            slider.valueChanged.connect(lambda val, n=name, l=val_lbl: self._on_servo_change(n, val, l))
            
            servo_layout.addWidget(slider, i, 1)
            servo_layout.addWidget(val_lbl, i, 2)
            
        actuator_col.addWidget(servo_box)
        
        grid.addLayout(actuator_col, 1)
        layout.addLayout(grid)
        
        # Log
        self.log_text = QPlainTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        layout.addWidget(self.log_text)

    # --- LOGIC & HELPERS ---
    def _on_servo_change(self, servo_name, value, label_widget):
        """Handler for servo slider changes"""
        label_widget.setText(str(value))
        self._send_cmd(f"SET_{servo_name}:{value}")

    def _update_colors(self):
        p = theme_manager.active_palette
        
        self.lbl_title.setStyleSheet(f"font-size: 24px; font-weight: 800; color: {p['accent_main']}; letter-spacing: 2px;")
        self.lbl_file_status.setStyleSheet(f"color: {p['text_muted']}; font-style: italic;")
        
        self.lbl_i2c.setStyleSheet(f"color: {p['accent_main']}; font-family: Consolas;")
        self.lbl_raw_pots.setStyleSheet(f"font-family: Consolas; font-weight: bold; color: {p['accent_main']}; font-size: 14px;")
        
        self.log_text.setStyleSheet(f"background-color: {p['bg_input']}; font-family: Consolas; color: {p['success']}; border: 1px solid {p['border_dim']};")
        
        if self.serial.connected:
            self.btn_connect.setStyleSheet(f"background-color: {p['danger']}; color: white;")
        else:
            self.btn_connect.setStyleSheet(f"background-color: {p['success']}; color: white;")

    def _refresh_ports(self):
        self.port_combo.clear()
        ports = [p.device for p in serial.tools.list_ports.comports()]
        self.port_combo.addItems(ports)

    def _toggle_connect(self):
        if not self.serial.connected:
            port = self.port_combo.currentText()
            if not port: return
            if self.serial.connect(port):
                self.btn_connect.setText("DISCONNECT")
                self.port_combo.setEnabled(False)
                self._update_colors()
        else:
            self.serial.disconnect()
            self.btn_connect.setText("CONNECT")
            self.port_combo.setEnabled(True)
            self._update_colors()
            if self.live_scan: self.btn_live.click()

    def get_prefix(self):
        txt = self.mod_combo.currentText()
        if "Direct" in txt: return "D"
        return txt.split(" ")[1]

    def _send_cmd(self, cmd):
        if self.serial.connected:
            full_cmd = f"{self.get_prefix()}:{cmd}"
            self.serial.send_raw(full_cmd)
            # Pause scan briefly to prioritize manual command
            if self.live_scan and "TEST_POTS" not in cmd:
                self.scan_timer.stop()
                QTimer.singleShot(200, self.scan_timer.start)
            
            if "TEST_POTS" not in cmd:
                self.log(f">> {full_cmd}")

    def _toggle_live(self):
        if self.btn_live.isChecked():
            if not self.serial.connected:
                self.btn_live.setChecked(False)
                return
            self.btn_live.setText("STOP STREAMING")
            self.btn_live.setStyleSheet(f"background-color: {theme_manager.get_color('danger')}; color: white; font-weight: bold;")
            self.scan_timer.start()
        else:
            self.btn_live.setText("START LIVE DATA STREAM")
            self.btn_live.setStyleSheet("") # Revert to default
            self.scan_timer.stop()

    def _on_scan_tick(self):
        if self.serial.connected:
            prefix = self.get_prefix()
            self.serial.send_raw(f"{prefix}:TEST_POTS")

    def on_raw_log(self, line):
        if "I2C_SCAN:" in line:
            self.lbl_i2c.setText(line.split(':')[1])
            self.log(line)
        elif not self.live_scan:
            self.log(line)

    def on_pots_update(self, pots_list):
        if isinstance(pots_list, list):
            formatted = "  |  ".join([f"{v}" for v in pots_list])
            self.lbl_raw_pots.setText(formatted)
            
            if self.live_scan and self.tabs.currentIndex() == 0:
                current_mux_str = self.get_prefix()
                if current_mux_str.isdigit():
                    cur_mux = int(current_mux_str)
                    rows = self.table.rowCount()
                    for r in range(rows):
                        w_mux = self.table.cellWidget(r, 2)
                        if w_mux and int(w_mux.currentText()) == cur_mux:
                            w_ads = self.table.cellWidget(r, 5)
                            if w_ads:
                                ch = w_ads.value()
                                if ch >= 0 and ch < len(pots_list):
                                    item = self.table.item(r, 6)
                                    item.setText(str(pots_list[ch]))
                                    item.setForeground(QBrush(QColor(theme_manager.get_color('success'))))

    def log(self, msg):
        self.log_text.appendPlainText(msg)
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())