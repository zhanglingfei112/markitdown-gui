import sys
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QMenuBar, QMenu, QStatusBar, QFileDialog, QMessageBox
from markitdown_gui.ui.drop_area import DropArea
from markitdown_gui.ui.file_list import FileList
from markitdown_gui.ui.preview import PreviewArea
from markitdown_gui.ui.settings_dialog import SettingsDialog
from markitdown_gui.app.worker import ConvertWorker
from markitdown_gui.app.settings import Settings
from markitdown_gui import __version__
from PySide6.QtWidgets import QPushButton

class MainWindow(QMainWindow):
    """
    主窗口类，负责整体布局和组件协调
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MarkItDown GUI")
        self.resize(1200, 800)
        
        # 状态管理
        self.worker = None
        
        self.init_ui()
        self.update_ui_text()
        self.connect_signals()

    def init_ui(self):
        """
        初始化界面布局
        """
        # 1. 菜单栏
        self.create_menus()
        
        # 2. 主部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 3. 分割窗格 (左侧操作区, 右侧预览区)
        splitter = QSplitter()
        
        # --- 左侧操作区 ---
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        self.drop_area = DropArea()
        self.file_list = FileList()
        
        # 按钮区域
        self.convert_btn = QPushButton("开始转换")
        self.export_btn = QPushButton("导出文件")
        self.remove_btn = QPushButton("删除选中")
        self.clear_btn = QPushButton("清空列表")
        
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.convert_btn)
        btn_layout.addWidget(self.export_btn)
        btn_layout.addWidget(self.remove_btn)
        btn_layout.addWidget(self.clear_btn)
        
        left_layout.addWidget(self.drop_area)
        left_layout.addWidget(self.file_list)
        left_layout.addLayout(btn_layout)
        
        # --- 右侧预览区 ---
        self.preview_area = PreviewArea()
        
        splitter.addWidget(left_widget)
        splitter.addWidget(self.preview_area)
        splitter.setStretchFactor(1, 2)
        
        main_layout.addWidget(splitter)
        
        # 4. 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def create_menus(self):
        """
        创建顶部菜单栏
        """
        menubar = self.menuBar()
        
        # 文件菜单
        self.menu_file = menubar.addMenu("File")
        self.action_open = self.menu_file.addAction("Open File")
        self.action_folder = self.menu_file.addAction("Open Folder")
        self.menu_file.addSeparator()
        self.action_exit = self.menu_file.addAction("Exit")
        self.action_exit.triggered.connect(self.close)
        
        # 设置菜单
        self.menu_settings = menubar.addMenu("Settings")
        self.action_pref = self.menu_settings.addAction("Preferences")
        self.action_pref.triggered.connect(self.open_settings)
        
        # 语言菜单
        self.menu_lang = menubar.addMenu("Language")
        self.action_zh = self.menu_lang.addAction("中文")
        self.action_en = self.menu_lang.addAction("English")

    def connect_signals(self):
        """
        连接信号和槽
        """
        self.action_open.triggered.connect(self.open_file_dialog)
        self.action_folder.triggered.connect(self.open_folder_dialog)
        self.action_zh.triggered.connect(lambda: self.change_language("zh_CN"))
        self.action_en.triggered.connect(lambda: self.change_language("en_US"))
        self.convert_btn.clicked.connect(self.start_conversion)
        self.export_btn.clicked.connect(self.export_files)
        self.remove_btn.clicked.connect(self.remove_selected_file)
        self.clear_btn.clicked.connect(self.clear_file_list)
        self.drop_area.filesDropped.connect(self.file_list.add_files)
        self.file_list.list_widget.itemClicked.connect(self.show_preview)

    def open_file_dialog(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Files")
        if files:
            self.file_list.add_files(files)

    def open_folder_dialog(self):
        """
        打开文件夹并扫描支持的文件
        """
        import os
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            supported = ('.pdf','.docx','.pptx','.xlsx','.xls','.csv','.html','.htm',
                        '.json','.xml','.epub','.zip','.md','.txt','.jpg','.jpeg',
                        '.png','.gif','.webp','.mp3','.wav','.msg')
            files = []
            for root, dirs, filenames in os.walk(folder):
                # 跳过隐藏目录
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                for f in filenames:
                    if f.lower().endswith(supported):
                        files.append(os.path.join(root, f))
            self.file_list.add_files(files)

    def remove_selected_file(self):
        """
        删除选中的文件
        """
        count = self.file_list.remove_selected()
        texts = getattr(self, 'texts', {})
        if count > 0:
            self.status_bar.showMessage(texts.get("status_removed", "已移除选中文件"))
        else:
            self.status_bar.showMessage(texts.get("status_select_remove", "请先选择要移除的文件"))

    def clear_file_list(self):
        """
        清空文件列表
        """
        self.file_list.clear_all()
        texts = getattr(self, 'texts', {})
        self.status_bar.showMessage(texts.get("status_list_cleared", "列表已清空"))

    def start_conversion(self):
        """
        启动后台转换线程
        """
        files = self.file_list.get_all_files()
        if not files:
            QMessageBox.warning(self, self.texts.get("app_title", "提示"), self.texts.get("msg_no_files", "Please add files to convert first!"))
            return
            
        # 禁用按钮防止重复点击
        self.convert_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
        
        self.worker = ConvertWorker(files, Settings.get_all())
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.on_conversion_finished)
        self.worker.start()

    def show_preview(self, item):
        """
        显示选中文件的转换结果
        """
        path = self.file_list.get_file_path_from_item(item)
        if path in self.file_list.files_data:
            data = self.file_list.files_data[path]
            if data["status"] == "completed" and data["result"]:
                self.preview_area.set_content(data["result"])

    def update_progress(self, file_path, status, result=None, error=None):
        """
        更新文件列表中的状态
        """
        self.file_list.update_file_status(file_path, status, result, error)
        
    def on_conversion_finished(self):
        """
        转换完成回调
        """
        self.convert_btn.setEnabled(True)
        self.export_btn.setEnabled(True)
        texts = getattr(self, 'texts', {})
        self.status_bar.showMessage(texts.get("status_all_done", "所有任务处理完成"))

    def export_files(self):
        """
        导出转换后的文件
        """
        # 优先使用设置中的输出目录，否则弹出文件夹选择对话框
        output_dir = Settings.get("output_dir")
        if not output_dir:
            output_dir = QFileDialog.getExistingDirectory(self, "Select Export Directory")

        if not output_dir:
            return

        import os
        files = self.file_list.get_completed_files()
        count = 0
        errors = []
        texts = getattr(self, 'texts', Settings.get_translations(Settings.get("language", "zh_CN")))
        overwrite_all = None  # 局部变量，每次导出独立判断

        for path, content in files.items():
            base = os.path.splitext(os.path.basename(path))[0]
            save_path = os.path.join(output_dir, f"{base}.md")

            if os.path.exists(save_path):
                if overwrite_all is None:
                    reply = QMessageBox.question(
                        self,
                        texts.get("msg_title_warning", "Warning"),
                        texts.get("msg_overwrite", "File already exists. Overwrite?"),
                        QMessageBox.Yes | QMessageBox.No | QMessageBox.YesToAll | QMessageBox.NoToAll
                    )
                    if reply == QMessageBox.YesToAll:
                        overwrite_all = True
                    elif reply == QMessageBox.NoToAll:
                        overwrite_all = False
                        continue
                    elif reply == QMessageBox.No:
                        continue
                elif not overwrite_all:
                    continue

            try:
                with open(save_path, "w", encoding="utf-8") as f:
                    f.write(content)
                count += 1
            except OSError as e:
                errors.append(f"{os.path.basename(save_path)}: {e}")

        # 显示结果
        if errors:
            err_summary = "; ".join(errors[:3])
            if len(errors) > 3:
                err_summary += f" ... 及其他 {len(errors)-3} 个错误"
            msg = texts.get("status_export_error_summary", "导出 {success} 个，{fail} 个失败: {errors}")
            self.status_bar.showMessage(msg.format(success=count, fail=len(errors), errors=err_summary))
        else:
            msg = texts.get("msg_export_success", "Exported {count} files to: {path}")
            self.status_bar.showMessage(msg.format(count=count, path=output_dir))

    def change_language(self, lang_code):
        """
        切换语言
        """
        Settings.set("language", lang_code)
        self.update_ui_text()

    def update_ui_text(self):
        """
        根据当前语言设置更新所有界面文字
        """
        lang = Settings.get("language", "zh_CN")
        texts = Settings.get_translations(lang)
        self.texts = texts  # 存储供 start_conversion 等方法使用
        
        # 窗口标题
        title = texts.get("app_title", "MarkItDown GUI")
        self.setWindowTitle(f"{title} v{__version__}")
        
        # 按钮
        self.convert_btn.setText(texts.get("btn_convert", "Start Conversion"))
        self.export_btn.setText(texts.get("btn_export", "Export"))
        self.remove_btn.setText(texts.get("btn_remove", "Remove Selected"))
        self.clear_btn.setText(texts.get("btn_clear", "Clear All"))
        
        # 菜单
        self.menu_file.setTitle(texts.get("menu_file", "File"))
        self.menu_settings.setTitle(texts.get("menu_settings", "Settings"))
        self.menu_lang.setTitle(texts.get("menu_lang", "Language"))
        
        # 菜单项
        self.action_open.setText(texts.get("menu_open", "Open File"))
        self.action_folder.setText(texts.get("menu_folder", "Open Folder"))
        self.action_exit.setText(texts.get("menu_exit", "Exit"))
        self.action_pref.setText(texts.get("menu_preferences", "Preferences"))
        
        # 状态栏
        self.status_bar.showMessage(texts.get("status_ready", "Ready"))
        
        # 通知子组件更新
        self.drop_area.update_text(texts)
        self.file_list.update_text(texts)
        self.preview_area.update_text(texts)

    def closeEvent(self, event):
        """
        窗口关闭事件，确保线程安全退出
        """
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            if not self.worker.wait(3000):  # 3秒超时防止永久阻塞
                pass  # 超时后强制关闭
        event.accept()

    def open_settings(self):
        """
        打开设置对话框
        """
        dialog = SettingsDialog(self)
        if dialog.exec():
            self.update_ui_text()
            texts = getattr(self, 'texts', {})
            self.status_bar.showMessage(texts.get("status_settings_updated", "设置已更新"))