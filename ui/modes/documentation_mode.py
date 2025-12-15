import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
                             QTextBrowser, QLabel, QSplitter)
from PyQt6.QtCore import Qt

class DocumentationMode(QWidget):
    """
    Knowledge Base Reader.
    Displays project Markdown files.
    """
    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._load_file_list()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left: File List
        list_container = QWidget()
        l_layout = QVBoxLayout(list_container)
        l_layout.setContentsMargins(0,0,0,0)
        
        lbl_files = QLabel("SOURCE DOCUMENTS")
        lbl_files.setStyleSheet("font-weight: bold; color: #007acc; padding: 5px;")
        l_layout.addWidget(lbl_files)
        
        self.file_list = QListWidget()
        self.file_list.setStyleSheet("""
            QListWidget { background-color: #252526; border: none; font-size: 11pt; }
            QListWidget::item { padding: 10px; }
            QListWidget::item:selected { background-color: #094771; color: white; }
        """)
        self.file_list.itemClicked.connect(self._on_file_selected)
        l_layout.addWidget(self.file_list)
        
        splitter.addWidget(list_container)
        
        # Right: Content Viewer
        self.viewer = QTextBrowser()
        self.viewer.setOpenExternalLinks(True)
        self.viewer.setStyleSheet("""
            QTextBrowser { 
                background-color: #1e1e1e; 
                color: #d4d4d4; 
                padding: 20px; 
                font-family: 'Segoe UI', sans-serif;
                border-left: 1px solid #3e3e42;
            }
        """)
        splitter.addWidget(self.viewer)
        
        splitter.setStretchFactor(1, 4) # Viewer is 4x wider
        layout.addWidget(splitter)

    def _load_file_list(self):
        # Look in the sourcetruth directory
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        docs_dir = os.path.join(base_dir, "sourcetruth")
        
        if os.path.exists(docs_dir):
            files = [f for f in os.listdir(docs_dir) if f.endswith('.md')]
            files.sort()
            for f in files:
                self.file_list.addItem(f)
                
            if files:
                self.file_list.setCurrentRow(0)
                self._load_content(os.path.join(docs_dir, files[0]))
        else:
            self.viewer.setText(f"Documentation directory not found: {docs_dir}")

    def _on_file_selected(self, item):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        docs_dir = os.path.join(base_dir, "sourcetruth")
        path = os.path.join(docs_dir, item.text())
        self._load_content(path)

    def _load_content(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Simple Markdown rendering
                self.viewer.setMarkdown(content)
        except Exception as e:
            self.viewer.setText(f"Error loading file: {e}")