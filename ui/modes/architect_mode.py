from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem, 
                             QGroupBox, QFormLayout, QDoubleSpinBox, QPushButton, QLabel, 
                             QComboBox, QScrollArea, QMessageBox, QFileDialog, QToolBar, QLineEdit)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QIcon
import logging
import os

# Uses Custom Buttons for Toolbar
from ui.widgets.custom_icons import ModernSidebarButton

logger = logging.getLogger('inmoov_v13')

class ArchitectMode(QWidget):
    model_changed = pyqtSignal()
    link_selected = pyqtSignal(str) 
    request_load = pyqtSignal(str) 

    def __init__(self, robot_model):
        super().__init__()
        self.model = robot_model
        self.selected_link = None
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # --- TOOLBAR ---
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(10, 10, 10, 5)
        toolbar.setSpacing(10)
        
        btn_size = (40, 40)
        
        # Using Icon Type names from custom_icons.py
        btn_open = ModernSidebarButton("open", "Open Robot File", size=btn_size)
        btn_open.clicked.connect(self._open_file)
        
        btn_save = ModernSidebarButton("save", "Save Robot As...", size=btn_size)
        btn_save.clicked.connect(self._save_file)
        
        btn_add = ModernSidebarButton("add", "Add New Part", size=btn_size)
        btn_add.clicked.connect(self._add_part)
        
        toolbar.addWidget(btn_open)
        toolbar.addWidget(btn_save)
        toolbar.addStretch()
        toolbar.addWidget(btn_add)
        
        main_layout.addLayout(toolbar)

        # --- SPLIT VIEW ---
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(5, 5, 5, 5)

        # 1. Tree
        tree_group = QGroupBox("Structure")
        tree_group.setStyleSheet("QGroupBox { border: 1px solid #3e3e42; font-weight: bold; margin-top: 10px; } QGroupBox::title { color: #007acc; }")
        tree_layout = QVBoxLayout(tree_group)
        
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Hierarchy")
        self.tree.setStyleSheet("border: none; background-color: #1e1e1e;")
        self.tree.itemClicked.connect(self._on_item_selected)
        tree_layout.addWidget(self.tree)
        content_layout.addWidget(tree_group, 1)

        # 2. Inspector
        props_group = QGroupBox("Properties")
        props_group.setStyleSheet("QGroupBox { border: 1px solid #3e3e42; font-weight: bold; margin-top: 10px; } QGroupBox::title { color: #007acc; }")
        self.props_layout = QVBoxLayout(props_group)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background-color: transparent; border: none;")
        self.props_container = QWidget()
        self.form_layout = QFormLayout(self.props_container)
        self.form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        scroll.setWidget(self.props_container)
        
        self.props_layout.addWidget(scroll)
        content_layout.addWidget(props_group, 1)

        main_layout.addLayout(content_layout)
        self.refresh_tree()

    def refresh_tree(self):
        self.tree.clear()
        if self.model.root:
            self._add_tree_node(self.model.root, self.tree.invisibleRootItem())
        self.tree.expandAll()

    def _add_tree_node(self, link, parent_item):
        item = QTreeWidgetItem(parent_item)
        item.setText(0, link.name)
        item.setData(0, Qt.ItemDataRole.UserRole, link)
        if link.joint:
            display_id = link.joint.id if link.joint.id else "Fixed"
            item.setText(0, f"{link.name} [{display_id}]")
        for child in link.children:
            self._add_tree_node(child, item)

    def _on_item_selected(self, item, column):
        link = item.data(0, Qt.ItemDataRole.UserRole)
        self.selected_link = link
        self._build_inspector(link)
        self.link_selected.emit(link.name)

    def _add_part(self):
        if not self.selected_link:
            QMessageBox.warning(self, "Select Parent", "Please select a parent link in the tree first.")
            return
            
        name = f"part_{len(self.model.links) + 1}"
        if hasattr(self.model, 'add_link') and self.model.add_link(name, self.selected_link.name):
            self.refresh_tree()
            self.model_changed.emit()
        else:
            QMessageBox.warning(self, "Error", "Failed to add part.")

    def _open_file(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Open Robot", "config/robots", "JSON Files (*.json)")
        if fname:
            self.request_load.emit(fname)

    def _save_file(self):
        fname, _ = QFileDialog.getSaveFileName(self, "Save Robot", "config/robots", "JSON Files (*.json)")
        if fname:
            if hasattr(self.model, 'save_to_file') and self.model.save_to_file(fname):
                QMessageBox.information(self, "Success", f"Robot saved to {os.path.basename(fname)}")
            else:
                QMessageBox.warning(self, "Error", "Failed to save file.")

    def on_viewport_nudge(self, axis, delta):
        if not self.selected_link or not self.selected_link.joint: return
        o = list(self.selected_link.joint.origin)
        o[axis] += delta
        self.selected_link.joint.origin = tuple(o)
        self._build_inspector(self.selected_link)
        self.model_changed.emit()

    def _build_inspector(self, link):
        while self.form_layout.count():
            child = self.form_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()

        header = QLabel(f"{link.name.upper()}")
        header.setStyleSheet("font-weight: bold; font-size: 14px; color: #007acc; margin-bottom: 10px;")
        self.form_layout.addRow(header)
        
        if link.joint:
            le_id = QLineEdit(str(link.joint.id) if link.joint.id else "")
            le_id.setPlaceholderText("ID (e.g. 14)")
            le_id.setStyleSheet("background-color: #333; padding: 4px; border: 1px solid #555;")
            le_id.textChanged.connect(lambda v: setattr(link.joint, 'id', v))
            self.form_layout.addRow("Hardware ID:", le_id)

            self._add_section_header("ORIGIN (mm)")
            self._add_spin("X (Red)", link.joint.origin[0], -1000, 1000, lambda v: self._update_origin(link, 0, v))
            self._add_spin("Y (Green)", link.joint.origin[1], -1000, 1000, lambda v: self._update_origin(link, 1, v))
            self._add_spin("Z (Blue)", link.joint.origin[2], -1000, 1000, lambda v: self._update_origin(link, 2, v))

        self._add_section_header("VISUALS")
        if hasattr(link.visual, 'method') and link.visual.method == "loft":
            self._add_spin("Length (mm)", link.visual.length_mm, 1, 2000, lambda v: self._update_visual(link, 'length_mm', v))
        
        if hasattr(link.visual, 'sections') and link.visual.sections:
            self._add_spin("Base Radius", link.visual.sections[0].get("radius", 10), 1, 500, lambda v: self._update_section(link, 0, "radius", v))

    def _add_section_header(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #aaa; font-weight: bold; margin-top: 15px; border-bottom: 1px solid #444;")
        self.form_layout.addRow(lbl)

    def _add_spin(self, label, value, min_v, max_v, callback):
        sb = QDoubleSpinBox()
        sb.setRange(min_v, max_v)
        sb.setValue(float(value))
        sb.valueChanged.connect(callback)
        self.form_layout.addRow(label, sb)

    def _update_origin(self, link, axis, val):
        o = list(link.joint.origin)
        o[axis] = val
        link.joint.origin = tuple(o)
        self.model_changed.emit()

    def _update_visual(self, link, attr, val):
        setattr(link.visual, attr, val)
        self.model_changed.emit()

    def _update_section(self, link, idx, key, val):
        link.visual.sections[idx][key] = val
        self.model_changed.emit()