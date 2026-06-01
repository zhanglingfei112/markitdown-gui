import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QHBoxLayout, QLabel
from PySide6.QtCore import Qt

class FileList(QWidget):
    """
    文件列表展示组件
    """
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.files_data = {} # path -> {item, status_label, status, result}
        self.texts = {}

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 列表标题
        self.title_label = QLabel("待转换文件")
        self.title_label.setStyleSheet("font-weight: bold; margin-bottom: 5px; margin-top: 5px;")
        
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.SingleSelection)
        
        layout.addWidget(self.title_label)
        layout.addWidget(self.list_widget)

    def update_text(self, texts):
        """
        更新语言
        """
        self.texts = texts
        self.title_label.setText(texts.get("list_title", "File List"))
        # Update all existing status labels
        t = texts
        for path, data in self.files_data.items():
            st = data["status"]
            if st == "pending":
                data["status_label"].setText(t.get("status_pending", "Pending"))
            elif st == "completed":
                data["status_label"].setText(t.get("status_done", "Completed"))
            elif st == "failed":
                data["status_label"].setText(t.get("status_failed", "Failed"))
            elif st == "processing":
                data["status_label"].setText(t.get("status_processing", "Processing..."))

    def add_files(self, files):
        """
        向列表中添加文件
        """
        for path in files:
            if path in self.files_data:
                continue
                
            try:
                filename = os.path.basename(path)
                size = os.path.getsize(path) / 1024 # KB
                
                item = QListWidgetItem()
                
                # 构建行布局
                widget = QWidget()
                row_layout = QHBoxLayout(widget)
                row_layout.setContentsMargins(5, 2, 5, 2)
                
                name_label = QLabel(f"[{size:.1f}KB] {filename}")
                status_label = QLabel(self.texts.get("status_pending", "Pending"))
                status_label.setStyleSheet("color: #888")
                
                row_layout.addWidget(name_label)
                row_layout.addStretch()
                row_layout.addWidget(status_label)
                
                item.setSizeHint(widget.sizeHint())
                self.list_widget.addItem(item)
                self.list_widget.setItemWidget(item, widget)
                
                self.files_data[path] = {
                    "item": item,
                    "status_label": status_label,
                    "status": "pending",
                    "result": None
                }
            except Exception:
                continue

    def update_file_status(self, path, status, result=None, error=None):
        """
        更新特定文件的状态
        """
        if path not in self.files_data:
            return
            
        data = self.files_data[path]
        data["status"] = status
        data["result"] = result
        
        t = self.texts if self.texts else {}
        status_text = t.get("status_processing", "Processing...")
        color = "#094771"

        if status == "completed":
            status_text = t.get("status_done", "Completed")
            color = "#4caf50"
        elif status == "failed":
            error_msg = str(error)[:15] if error else t.get("status_failed", "Failed")
            status_text = f"{t.get('status_failed', 'Failed')}: {error_msg}"
            color = "#f44336"
        elif status == "pending":
            status_text = t.get("status_pending", "Pending")
            color = "#888888"
            
        data["status_label"].setText(status_text)
        data["status_label"].setStyleSheet(f"color: {color}")

    def get_all_files(self):
        """
        返回所有待转换的文件路径
        """
        return list(self.files_data.keys())

    def get_file_path_from_item(self, item):
        """
        根据 Item 对象获取对应的文件路径
        """
        for path, data in self.files_data.items():
            if data["item"] == item:
                return path
        return None

    def get_completed_files(self):
        """
        返回所有已完成转换的文件及其内容
        """
        return {path: d["result"] for path, d in self.files_data.items() if d["status"] == "completed"}

    def remove_selected(self):
        """
        删除选中的文件
        """
        current_item = self.list_widget.currentItem()
        if not current_item:
            return 0
        
        path = self.get_file_path_from_item(current_item)
        if path:
            # 从 UI 移除
            row = self.list_widget.row(current_item)
            self.list_widget.takeItem(row)
            # 从数据移除
            del self.files_data[path]
            return 1
        return 0

    def clear_all(self):
        """
        清空所有文件
        """
        self.list_widget.clear()
        self.files_data.clear()