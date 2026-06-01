from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLabel
from PySide6.QtCore import Qt

class PreviewArea(QWidget):
    """
    Markdown 预览区域
    """
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        self.title_label = QLabel("Markdown 预览")
        self.title_label.setStyleSheet("font-weight: bold; margin-bottom: 5px;")
        
        self.editor = QTextEdit()
        self.editor.setReadOnly(True)
        self.editor.setPlaceholderText("转换结果将在此显示...")
        
        # 简单的 Markdown 风格模拟 (仅文本)
        self.editor.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 13px;
                border: 1px solid #3c3c3c;
            }
        """)
        
        layout.addWidget(self.title_label)
        layout.addWidget(self.editor)

    def update_text(self, texts):
        """
        更新界面文字
        """
        self.title_label.setText(texts.get("preview_title", "Markdown Preview"))
        self.editor.setPlaceholderText(texts.get("preview_placeholder", "Conversion results will be displayed here..."))

    def set_content(self, content):
        """
        设置显示的内容
        """
        self.editor.setPlainText(content)
