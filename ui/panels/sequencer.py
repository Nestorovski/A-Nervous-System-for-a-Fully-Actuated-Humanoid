from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QListWidget, QCheckBox, QFileDialog, QLabel, QFrame)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QBrush
import json
import math
import os
from core.theme_manager import theme_manager
from ui.widgets.custom_icons import ModernSidebarButton

class SequencerPanel(QWidget):
    def __init__(self, parent_window, kinematics):
        super().__init__(parent_window)
        self.kinematics = kinematics
        self.frames = []
        self.is_playing = False
        
        self.current_frame_idx = 0
        self.sub_step = 0
        self.total_steps = 40  
        
        self.timer = QTimer()
        self.timer.timeout.connect(self._tick)
        
        self._setup_ui()
        theme_manager.theme_changed.connect(self.update_theme)

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # --- LEFT: TIMELINE LIST ---
        self.list_frames = QListWidget()
        self.list_frames.setAlternatingRowColors(True)
        layout.addWidget(self.list_frames, 3)
        
        # --- RIGHT: CONTROL PANEL ---
        self.ctrl_widget = QWidget()
        ctrl_layout = QVBoxLayout(self.ctrl_widget)
        ctrl_layout.setContentsMargins(10, 10, 10, 10)
        ctrl_layout.setSpacing(10)
        
        self.lbl_header = QLabel("ANIMATION")
        self.lbl_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_header.setStyleSheet("font-weight: bold; font-size: 11px; letter-spacing: 2px;")
        ctrl_layout.addWidget(self.lbl_header)
        
        # --- Transport Controls (Using Custom Icons) ---
        transport_layout = QHBoxLayout()
        btn_size = (40, 35)
        
        self.btn_rec = ModernSidebarButton("media_rec", "Record Keyframe", size=btn_size)
        self.btn_rec.setCheckable(False)
        self.btn_rec.clicked.connect(self._record_frame)
        
        self.btn_play = ModernSidebarButton("media_play", "Play Sequence", size=btn_size)
        self.btn_play.setCheckable(False)
        self.btn_play.clicked.connect(self._toggle_play)
        
        transport_layout.addWidget(self.btn_rec)
        transport_layout.addWidget(self.btn_play)
        ctrl_layout.addLayout(transport_layout)
        
        # Options
        self.chk_smooth = QCheckBox("Smooth Motion")
        self.chk_smooth.setChecked(True)
        ctrl_layout.addWidget(self.chk_smooth)
        
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        ctrl_layout.addWidget(line)
        
        # --- File IO (Using Custom Icons) ---
        # Save
        row_save = QHBoxLayout()
        self.btn_save = ModernSidebarButton("save", "Save Sequence", size=(30, 30))
        self.btn_save.setCheckable(False)
        self.btn_save.clicked.connect(self._save)
        row_save.addWidget(self.btn_save)
        row_save.addWidget(QLabel("Save"))
        row_save.addStretch()
        ctrl_layout.addLayout(row_save)

        # Load
        row_load = QHBoxLayout()
        self.btn_load = ModernSidebarButton("open", "Load Sequence", size=(30, 30))
        self.btn_load.setCheckable(False)
        self.btn_load.clicked.connect(self._load)
        row_load.addWidget(self.btn_load)
        row_load.addWidget(QLabel("Load"))
        row_load.addStretch()
        ctrl_layout.addLayout(row_load)

        # Clear
        row_clear = QHBoxLayout()
        self.btn_clear = ModernSidebarButton("trash", "Clear Timeline", size=(30, 30))
        self.btn_clear.setCheckable(False)
        self.btn_clear.clicked.connect(self._clear)
        row_clear.addWidget(self.btn_clear)
        row_clear.addWidget(QLabel("Clear"))
        row_clear.addStretch()
        ctrl_layout.addLayout(row_clear)
        
        ctrl_layout.addStretch()
        layout.addWidget(self.ctrl_widget, 2)
        
        self.update_theme()

    def update_theme(self):
        p = theme_manager.active_palette
        
        # List Styling
        self.list_frames.setStyleSheet(f"""
            QListWidget {{
                background-color: {p['bg_input']};
                color: {p['text_primary']};
                border: none;
                font-family: Consolas;
            }}
            QListWidget::item {{ padding: 5px; }}
            QListWidget::item:selected {{
                background-color: {p['accent_glow']};
                color: {p['accent_main']};
                border-left: 3px solid {p['accent_main']};
            }}
            QListWidget::item:alternate {{ background-color: {p['bg_element']}; }}
        """)
        
        # Right Panel
        self.ctrl_widget.setStyleSheet(f"background-color: {p['bg_surface']}; border-left: 1px solid {p['border_dim']};")
        self.lbl_header.setStyleSheet(f"color: {p['text_muted']}; font-weight: bold; font-size: 11px; letter-spacing: 2px;")
        
        # Update text labels
        for lbl in self.ctrl_widget.findChildren(QLabel):
            if lbl != self.lbl_header:
                lbl.setStyleSheet(f"color: {p['text_primary']}; font-weight: bold;")

        self.chk_smooth.setStyleSheet(f"color: {p['text_primary']};")
        
        # Trigger redraw of custom icons
        self.btn_rec.update()
        self.btn_play.update()

    def _record_frame(self):
        if not self.kinematics: return
        state = self.kinematics.current_state.copy()
        self.frames.append(state)
        self.list_frames.addItem(f"Frame {len(self.frames):02d} | {len(state)} Joints")
        self.list_frames.scrollToBottom()

    def _toggle_play(self):
        if not self.frames: return
        
        self.is_playing = not self.is_playing
        if self.is_playing:
            # Change icon to Stop
            self.btn_play.icon_type = "media_stop"
            self.btn_play.update()
            
            self.current_frame_idx = 0
            self.sub_step = 0
            self.timer.start(20) 
            self.btn_rec.setEnabled(False)
            self.btn_clear.setEnabled(False)
        else:
            # Change icon to Play
            self.btn_play.icon_type = "media_play"
            self.btn_play.update()
            
            self.timer.stop()
            self.btn_rec.setEnabled(True)
            self.btn_clear.setEnabled(True)

    def _clear(self):
        self.frames.clear()
        self.list_frames.clear()
        self.timer.stop()
        self.btn_play.icon_type = "media_play"
        self.btn_play.update()

    def _tick(self):
        # (Same interpolation logic as before)
        if not self.frames: return
        if self.current_frame_idx >= len(self.frames) - 1:
            self.current_frame_idx = 0
            
        start_frame = self.frames[self.current_frame_idx]
        next_idx = (self.current_frame_idx + 1) % len(self.frames)
        end_frame = self.frames[next_idx]
        
        t = self.sub_step / self.total_steps
        self.list_frames.setCurrentRow(self.current_frame_idx)
        
        if self.chk_smooth.isChecked():
            p = -(math.cos(math.pi * t) - 1) / 2
            interp_state = {}
            all_keys = set(start_frame.keys()) | set(end_frame.keys())
            for k in all_keys:
                v1 = start_frame.get(k, 90.0)
                v2 = end_frame.get(k, 90.0)
                interp_state[k] = v1 + (v2 - v1) * p
            self.kinematics.set_target_pose(interp_state)
        else:
            self.kinematics.set_target_pose(start_frame)

        self.sub_step += 1
        if self.sub_step > self.total_steps:
            self.sub_step = 0
            self.current_frame_idx += 1

    def _save(self):
        fname, _ = QFileDialog.getSaveFileName(self, "Save Animation", "config/profiles", "JSON (*.json)")
        if fname:
            try:
                with open(fname, 'w') as f:
                    json.dump(self.frames, f, indent=4)
            except Exception as e:
                print(f"Save failed: {e}")

    def _load(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Load Animation", "config/profiles", "JSON (*.json)")
        if fname:
            try:
                with open(fname, 'r') as f:
                    self.frames = json.load(f)
                self.list_frames.clear()
                for i, f in enumerate(self.frames):
                    self.list_frames.addItem(f"Frame {i+1:02d} | {len(f)} Joints")
            except Exception as e:
                print(f"Load failed: {e}")