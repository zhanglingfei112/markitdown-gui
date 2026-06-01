from PySide6.QtCore import QThread, Signal
from markitdown_gui.utils.converter import MarkItDownConverter

class ConvertWorker(QThread):
    """
    后台转换线程，防止 UI 阻塞
    """
    # 信号: (文件路径, 状态, 结果, 错误信息)
    progress = Signal(str, str, object, object)
    finished = Signal()

    def __init__(self, files, settings):
        """
        初始化转换工人
        :param files: 需要转换的文件路径列表
        :param settings: 配置字典
        """
        super().__init__()
        self.files = files
        self.settings = settings
        self.is_running = True

    def run(self):
        """
        线程主执行逻辑
        """
        converter = MarkItDownConverter(self.settings)
        
        for file_path in self.files:
            if not self.is_running:
                break
                
            try:
                # 发送“转换中”状态
                self.progress.emit(file_path, "converting", None, None)
                
                # 执行转换
                result = converter.convert(file_path)
                
                # 发送“完成”状态
                self.progress.emit(file_path, "completed", result, None)
            except Exception as e:
                # 发送“失败”状态
                self.progress.emit(file_path, "failed", None, str(e))
        
        self.finished.emit()

    def stop(self):
        """
        停止转换
        """
        self.is_running = False
