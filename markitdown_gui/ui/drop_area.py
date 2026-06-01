from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt, Signal

class DropArea(QWidget):
    """
    文件拖拽区域
    """
    filesDropped = Signal(list)

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 视觉装饰框
        self.frame = QFrame()
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setMinimumHeight(120)
        self.frame.setStyleSheet("""
            QFrame {
                border: 2px dashed #444444;
                border-radius: 10px;
                background-color: #252526;
            }
            QFrame[active="true"] {
                border: 2px dashed #007acc;
                background-color: #2a2d2e;
            }
        """)
        
        self.label = QLabel("拖拽文件到此处\n(Drop files here)")
        self.label.setAlignment(Qt.AlignCenter)
        
        frame_layout = QVBoxLayout(self.frame)
        frame_layout.addWidget(self.label)
        
        layout.addWidget(self.frame)

    def update_text(self, texts):
        """
        更新界面文字
        """
        self.label.setText(texts.get("drop_text", "Drag and Drop Files Here"))

    def add_files(self, files):
        """
        手动添加文件 (由按钮调用)
        """
        self.filesDropped.emit(files)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
            self.frame.setProperty("active", "true")
            self.frame.style().unpolish(self.frame)
            self.frame.style().polish(self.frame)
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.frame.setProperty("active", "false")
        self.frame.style().unpolish(self.frame)
        self.frame.style().polish(self.frame)

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        files = [url.toLocalFile() for url in urls if url.toLocalFile()]
        self.frame.setProperty("active", "false")
        self.frame.style().unpolish(self.frame)
        self.frame.style().polish(self.frame)
        self.filesDropped.emit(files)
