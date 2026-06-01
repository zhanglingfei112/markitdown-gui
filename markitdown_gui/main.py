import sys
import json
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox
from markitdown_gui.app.main_window import MainWindow
from markitdown_gui.app.settings import Settings

def main():
    """
    应用程序入口函数
    """
    app = QApplication(sys.argv)
    
    # 设置全局样式 (从外部文件加载)
    base_dir = Path(__file__).resolve().parent.parent
    style_path = base_dir / "resources" / "styles" / "style.qss"
    try:
        with open(style_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    except Exception as e:
        print(f"Warning: Could not load stylesheet from {style_path}: {e}")
        # Fallback to simple style if file missing
        app.setStyleSheet("QWidget { background-color: #1e1e1e; color: #d4d4d4; }")

    try:
        # 初始化设置
        Settings.load()
        
        # 创建并显示主窗口
        window = MainWindow()
        window.show()
        
        sys.exit(app.exec())
    except Exception as e:
        # 捕获启动时的致命错误
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText(f"Fatal Error during startup: {str(e)}")
        msg.exec()

if __name__ == "__main__":
    main()
