import os
import json
import re
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
                             QPlainTextEdit, QLabel, QMessageBox, QSplitter, 
                             QPushButton, QFileDialog, QFrame)
from PyQt6.QtCore import Qt, QRegularExpression
from PyQt6.QtGui import QFont, QColor, QTextCharFormat, QSyntaxHighlighter
from core.config_manager import config_manager
from core.theme_manager import theme_manager
from ui.widgets.custom_icons import ModernSidebarButton

# --- SYNTAX HIGHLIGHTER ---
class JsonHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rules = []
        fmt_key = QTextCharFormat(); fmt_key.setForeground(QColor("#9cdcfe"))
        self.rules.append((r'"[^"\\]*"\s*:', fmt_key))
        fmt_val = QTextCharFormat(); fmt_val.setForeground(QColor("#ce9178"))
        self.rules.append((r':\s*"[^"\\]*"', fmt_val))
        fmt_num = QTextCharFormat(); fmt_num.setForeground(QColor("#b5cea8"))
        self.rules.append((r'\b[0-9.]+\b', fmt_num))
        fmt_bool = QTextCharFormat(); fmt_bool.setForeground(QColor("#569cd6"))
        self.rules.append((r'\b(true|false|null)\b', fmt_bool))

    def highlightBlock(self, text):
        for pattern, format in self.rules:
            expression = QRegularExpression(pattern)
            it = expression.globalMatch(text)
            while it.hasNext():
                match = it.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)

class CodeMode(QWidget):
    def __init__(self):
        super().__init__()
        self.current_file_path = None
        self._setup_ui()
        self._load_file_list()
        theme_manager.theme_changed.connect(self.update_theme)

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # --- LEFT: NAVIGATOR ---
        nav_widget = QWidget()
        nav_layout = QVBoxLayout(nav_widget)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(0)
        
        # Nav Header
        self.lbl_nav = QLabel("EXPLORER")
        self.lbl_nav.setFixedHeight(30)
        self.lbl_nav.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nav_layout.addWidget(self.lbl_nav)
        
        self.file_list = QListWidget()
        self.file_list.setFrameShape(QFrame.Shape.NoFrame)
        self.file_list.itemClicked.connect(self._on_file_selected)
        nav_layout.addWidget(self.file_list)
        
        splitter.addWidget(nav_widget)
        
        # --- RIGHT: EDITOR ---
        editor_widget = QWidget()
        ed_layout = QVBoxLayout(editor_widget)
        ed_layout.setContentsMargins(0, 0, 0, 0)
        ed_layout.setSpacing(0)
        
        # Toolbar (Top)
        toolbar = QFrame()
        toolbar.setFixedHeight(45)
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(10, 0, 10, 0)
        tb_layout.setSpacing(10)
        
        self.lbl_filename = QLabel("NO FILE SELECTED")
        self.lbl_filename.setStyleSheet("font-weight: bold;")
        tb_layout.addWidget(self.lbl_filename)
        
        tb_layout.addStretch()
        
        # Actions
        self.btn_import = ModernSidebarButton("open", "Import External", size=(30, 30))
        self.btn_import.clicked.connect(self._import_external)
        tb_layout.addWidget(self.btn_import)
        
        self.btn_revert = ModernSidebarButton("refresh", "Revert Changes", size=(30, 30))
        self.btn_revert.clicked.connect(self._revert_file)
        tb_layout.addWidget(self.btn_revert)
        
        self.btn_save = ModernSidebarButton("save", "Save & Apply", size=(30, 30))
        self.btn_save.clicked.connect(self._save_and_apply)
        tb_layout.addWidget(self.btn_save)
        
        ed_layout.addWidget(toolbar)
        
        # Editor
        self.editor = QPlainTextEdit()
        self.editor.setFont(QFont("Consolas", 11))
        self.editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.editor.setFrameShape(QFrame.Shape.NoFrame)
        self.highlighter = JsonHighlighter(self.editor.document())
        self.editor.textChanged.connect(self._on_text_changed)
        ed_layout.addWidget(self.editor)
        
        # Footer
        self.footer = QLabel(" Ready ")
        self.footer.setFixedHeight(20)
        self.footer.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        ed_layout.addWidget(self.footer)
        
        splitter.addWidget(editor_widget)
        splitter.setStretchFactor(1, 4)
        
        layout.addWidget(splitter)
        self.update_theme()

    def _load_file_list(self):
        self.file_list.clear()
        base = config_manager.base_dir
        targets = [
            ("Hardware Map", os.path.join(base, "config", "hardware", "map_default.json")),
            ("Robot Anatomy", os.path.join(base, "config", "robots", "inmoov_standard.json")),
            ("Macros", os.path.join(base, "config", "profiles", "macros.json")),
            ("User Prefs", os.path.join(base, "config", "profiles", "user_prefs.json"))
        ]
        for name, path in targets:
            from PyQt6.QtWidgets import QListWidgetItem
            item = QListWidgetItem(name)
            item.setData(Qt.ItemDataRole.UserRole, path)
            self.file_list.addItem(item)

    def _on_file_selected(self, item):
        self.current_file_path = item.data(Qt.ItemDataRole.UserRole)
        self._revert_file()

    def _on_text_changed(self):
        self.lbl_filename.setText(f"{os.path.basename(self.current_file_path)}*")
        self.footer.setText(" Unsaved Changes ")
        self.footer.setStyleSheet(f"background-color: {theme_manager.get_color('warning')}; color: #000;")

    def _revert_file(self):
        if not self.current_file_path: return
        if os.path.exists(self.current_file_path):
            try:
                with open(self.current_file_path, 'r') as f:
                    content = json.dumps(json.load(f), indent=4)
                    self.editor.setPlainText(content)
                    self._mark_clean()
            except Exception as e:
                self.footer.setText(f" Error: {e} ")
        else:
            self.editor.setPlainText("{}")
            self._mark_clean()

    def _mark_clean(self):
        self.lbl_filename.setText(os.path.basename(self.current_file_path))
        self.footer.setText(" Ready ")
        self.footer.setStyleSheet(f"background-color: {theme_manager.get_color('accent_main')}; color: #000;")

    def _import_external(self):
        if not self.current_file_path: return
        fname, _ = QFileDialog.getOpenFileName(self, "Import Config", config_manager.base_dir, "JSON (*.json)")
        if fname:
            try:
                with open(fname, 'r') as f:
                    content = json.dumps(json.load(f), indent=4)
                    self.editor.setPlainText(content)
                    self._on_text_changed() # Mark dirty
                    QMessageBox.information(self, "Imported", "File content loaded. Click Save to apply.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed: {e}")

    def _save_and_apply(self):
        if not self.current_file_path: return
        raw = self.editor.toPlainText()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "Syntax Error", str(e))
            return
            
        # Logic Check: If overwriting Standard InMoov with Spider
        if "inmoov_standard" in self.current_file_path and "spider" in str(data).lower():
             if QMessageBox.question(self, "Warning", "Overwrite Humanoid with Spider?", 
                                     QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No) == QMessageBox.StandardButton.No:
                 return

        try:
            with open(self.current_file_path, 'w') as f:
                json.dump(data, f, indent=4)
            config_manager.load_all()
            self._mark_clean()
        except Exception as e:
            QMessageBox.critical(self, "Save Error", str(e))

    def update_theme(self):
        p = theme_manager.active_palette
        self.lbl_nav.setStyleSheet(f"background-color: {p['bg_surface']}; color: {p['text_muted']}; font-size: 10px; font-weight: bold;")
        self.file_list.setStyleSheet(f"background-color: {p['bg_surface']}; color: {p['text_primary']};")
        self.editor.setStyleSheet(f"background-color: {p['bg_input']}; color: {p['text_primary']};")
        self.lbl_filename.setStyleSheet(f"color: {p['accent_main']}; font-family: Consolas; font-weight: bold;")