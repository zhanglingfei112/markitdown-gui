#!/usr/bin/env python3 -u
"""minimax-m3 代码审查 — messages 端点 (正确方式)"""
import json, os, sys, time, urllib.request, urllib.error
sys.stdout.reconfigure(line_buffering=True)

BASE = "https://opencode.ai/zen/go/v1"
env_path = os.path.expanduser("~/.hermes/.env")
api_key = ""
with open(env_path) as f:
    for line in f:
        l = line.strip()
        if "OPENCODE_GO_API_KEY" in l and not l.startswith("#"):
            parts = l.split("=", 1)
            if len(parts) > 1:
                val = parts[1].strip()
                if len(val) > 10 and not val.startswith("#"):
                    api_key = val
                    break

headers = {
    "x-api-key": api_key,
    "anthropic-version": "2023-06-01",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0",
}

def call(prompt, timeout=300):
    body = json.dumps({
        "model": "minimax-m3",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 8192,
    }).encode()
    req = urllib.request.Request(f"{BASE}/messages", data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return {"ok": True, "data": json.loads(r.read().decode())}
    except urllib.error.HTTPError as e:
        detail = e.read().decode()[:500]
        return {"ok": False, "code": e.code, "detail": detail}
    except Exception as ex:
        return {"ok": False, "error": str(ex)}

def extract(resp):
    if not resp.get("ok"):
        return f"[FAIL {resp.get('code','?')}] {resp.get('detail','')[:200]}"
    try:
        texts = [b["text"] for b in resp["data"]["content"] if b["type"] == "text"]
        thinking = [b["thinking"] for b in resp["data"]["content"] if b["type"] == "thinking"]
        text = "\n".join(texts)
        usage = resp["data"].get("usage", {})
        return text, usage, thinking
    except Exception as e:
        return f"[PARSE ERROR] {e}: {json.dumps(resp['data'])[:200]}"

# 项目代码嵌入
project_code = """
## 项目文件总览 (MarkItDown GUI)

### main_window.py (315行, 主窗口)
```python
import sys
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QMenuBar, QMenu, QStatusBar, QFileDialog, QMessageBox
from markitdown_gui.ui.drop_area import DropArea
from markitdown_gui.ui.file_list import FileList
from markitdown_gui.ui.preview import PreviewArea
from markitdown_gui.ui.settings_dialog import SettingsDialog
from markitdown_gui.app.worker import ConvertWorker
from markitdown_gui.app.settings import Settings
from PySide6.QtWidgets import QPushButton

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MarkItDown GUI")
        self.resize(1200, 800)
        self.worker = None
        self.init_ui()
        self.update_ui_text()
        self.connect_signals()

    def init_ui(self):
        self.create_menus()
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        splitter = QSplitter()
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        self.drop_area = DropArea()
        self.file_list = FileList()
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
        self.preview_area = PreviewArea()
        splitter.addWidget(left_widget)
        splitter.addWidget(self.preview_area)
        splitter.setStretchFactor(1, 2)
        main_layout.addWidget(splitter)
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def create_menus(self):
        menubar = self.menuBar()
        self.menu_file = menubar.addMenu("File")
        self.action_open = self.menu_file.addAction("Open File")
        self.action_folder = self.menu_file.addAction("Open Folder")
        self.menu_file.addSeparator()
        self.action_exit = self.menu_file.addAction("Exit")
        self.action_exit.triggered.connect(self.close)
        self.menu_settings = menubar.addMenu("Settings")
        self.action_pref = self.menu_settings.addAction("Preferences")
        self.action_pref.triggered.connect(self.open_settings)
        self.menu_lang = menubar.addMenu("Language")
        self.action_zh = self.menu_lang.addAction("中文")
        self.action_en = self.menu_lang.addAction("English")

    def connect_signals(self):
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

    def start_conversion(self):
        files = self.file_list.get_all_files()
        if not files:
            QMessageBox.warning(self, "提示", "请先添加文件")
            return
        self.convert_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
        self.worker = ConvertWorker(files, Settings.get_all())
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.on_conversion_finished)
        self.worker.start()

    def export_files(self):
        output_dir = Settings.get("output_dir")
        if not output_dir:
            output_dir = QFileDialog.getExistingDirectory(self, "选择导出目录")
        if not output_dir:
            return
        files = self.file_list.get_completed_files()
        count = 0
        texts = Settings.get_translations(Settings.get("language", "zh_CN"))
        for path, content in files.items():
            base = os.path.splitext(os.path.basename(path))[0]
            save_path = os.path.join(output_dir, f"{base}.md")
            if os.path.exists(save_path):
                if not hasattr(self, '_overwrite_all'):
                    reply = QMessageBox.question(self, "确认",
                        "文件已存在，是否覆盖？",
                        QMessageBox.Yes | QMessageBox.No | QMessageBox.YesToAll | QMessageBox.NoToAll)
                    if reply == QMessageBox.YesToAll: self._overwrite_all = True
                    elif reply == QMessageBox.NoToAll:
                        self._overwrite_all = False; continue
                    elif reply == QMessageBox.No: continue
                elif not self._overwrite_all: continue
            try:
                with open(save_path, "w", encoding="utf-8") as f: f.write(content)
                count += 1
            except OSError as e:
                self.status_bar.showMessage(f"导出失败: {e}")
        self._overwrite_all = None
        self.status_bar.showMessage(f"已导出 {count} 个文件")

    def change_language(self, lang_code):
        Settings.set("language", lang_code)
        self.update_ui_text()

    def update_ui_text(self):
        lang = Settings.get("language", "zh_CN")
        texts = Settings.get_translations(lang)
        self.setWindowTitle(texts.get("app_title", "MarkItDown GUI"))
        self.convert_btn.setText(texts.get("btn_convert", "Start Conversion"))
        self.export_btn.setText(texts.get("btn_export", "Export"))
        self.remove_btn.setText(texts.get("btn_remove", "Remove Selected"))
        self.clear_btn.setText(texts.get("btn_clear", "Clear All"))
        self.menu_file.setTitle(texts.get("menu_file", "File"))
        self.menu_settings.setTitle(texts.get("menu_settings", "Settings"))
        self.menu_lang.setTitle(texts.get("menu_lang", "Language"))
        self.action_open.setText(texts.get("menu_open", "Open File"))
        self.action_folder.setText(texts.get("menu_folder", "Open Folder"))
        self.action_exit.setText(texts.get("menu_exit", "Exit"))
        self.action_pref.setText(texts.get("menu_preferences", "Preferences"))
        self.status_bar.showMessage(texts.get("status_ready", "Ready"))
        self.drop_area.update_text(texts)
        self.file_list.update_text(texts)
        self.preview_area.update_text(texts)

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            if not self.worker.wait(3000):
                pass
        event.accept()
```

### worker.py (52行)
```python
from PySide6.QtCore import QThread, Signal
from markitdown_gui.utils.converter import MarkItDownConverter

class ConvertWorker(QThread):
    progress = Signal(str, str, object, object)
    finished = Signal()

    def __init__(self, files, settings):
        super().__init__()
        self.files = files
        self.settings = settings
        self.is_running = True

    def run(self):
        converter = MarkItDownConverter(self.settings)
        for file_path in self.files:
            if not self.is_running:
                break
            try:
                self.progress.emit(file_path, "converting", None, None)
                result = converter.convert(file_path)
                self.progress.emit(file_path, "completed", result, None)
            except Exception as e:
                self.progress.emit(file_path, "failed", None, str(e))
        self.finished.emit()

    def stop(self):
        self.is_running = False
```

### converter.py (36行)
```python
from markitdown import MarkItDown

class MarkItDownConverter:
    def __init__(self, settings):
        self.settings = settings
        self.md = MarkItDown()
        if settings.get("ocr_enabled") and settings.get("llm_api_key"):
            pass  # LLM增强 - 未实现

    def convert(self, file_path: str) -> str:
        result = self.md.convert(file_path)
        return result.text_content
```

### settings.py (88行)
```python
import json, os

class Settings:
    CONFIG_FILE = os.path.expanduser("~/.markitdown_gui_settings.json")
    _data = {"language": "zh_CN", "output_dir": "", "ocr_enabled": False, "llm_api_key": ""}

    @classmethod
    def load(cls):
        if os.path.exists(cls.CONFIG_FILE):
            try:
                with open(cls.CONFIG_FILE, "r") as f: cls._data.update(json.load(f))
            except Exception as e: print(f"Load error: {e}")

    @classmethod
    def save(cls):
        with open(cls.CONFIG_FILE, "w") as f:
            json.dump(cls._data, f, indent=4, ensure_ascii=False)

    @classmethod
    def get(cls, key, default=None): return cls._data.get(key, default)
    @classmethod
    def set(cls, key, value): cls._data[key] = value; cls.save()
    @classmethod
    def get_all(cls): return cls._data.copy()

    @classmethod
    def get_translations(cls, lang_code):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        i18n_path = os.path.join(base_dir, "..", "i18n", f"{lang_code}.json")
        if os.path.exists(i18n_path):
            try:
                with open(i18n_path, "r") as f: return json.load(f)
            except: pass
        fallback = os.path.join(base_dir, "..", "i18n", "en_US.json")
        if os.path.exists(fallback):
            try:
                with open(fallback, "r") as f: return json.load(f)
            except: pass
        return {}
```

### drop_area.py (74行, 拖拽区域)
### file_list.py (157行, 文件列表)
### preview.py (47行, 预览)
### settings_dialog.py (75行, 设置对话框)
"""

# ── 测试1: 连通性确认 ──
print("=" * 60, flush=True)
print("  测试1: minimax-m3 via messages 连通性", flush=True)
print("=" * 60, flush=True)
t0 = time.time()
r = call("回复'OK_M3'这几个字。", timeout=60)
t = time.time() - t0
if r["ok"]:
    texts = [b["text"] for b in r["data"]["content"] if b["type"] == "text"]
    has_think = any(b["type"] == "thinking" for b in r["data"]["content"])
    print(f"  ✅ {t:.1f}s | has_think={has_think} | {''.join(texts)[:200]}", flush=True)
else:
    print(f"  ❌ {r.get('code','?')} | {r.get('detail','')[:200]}", flush=True)
    print("  如果失败尝试含UA...", flush=True)
    # Retry with UA variation
    headers2 = {**headers}
    r2 = call("回复'OK_M3'", timeout=60)
    if r2["ok"]:
        print(f"  ✅ 重试成功", flush=True)
    else:
        print(f"  ❌ 仍然失败，报告结果", flush=True)
        sys.exit(1)

time.sleep(3)

# ── 测试2: 代码审查 ──
print("\n" + "=" * 60, flush=True)
print("  测试2: minimax-m3 完整代码审查", flush=True)
print("=" * 60, flush=True)

review_prompt = f"""你是一个资深的PySide6/Python桌面应用安全与质量审查专家。请审查以下完整项目代码，从6个维度严格评估。

{project_code}

审查要求（每项给出P0/P1/P2等级+具体代码位置+修复建议）：

1. 【安全性】API Key明文存储风险、路径遍历、任意文件写入、注入攻击等
2. 【线程安全】QThread使用中的竞态条件、数据共享、UI更新线程问题
3. 【内存与性能】大文件批量转换时的内存溢出、QListWidget大量项目性能下降
4. 【用户体验】错误提示、进度反馈、拖拽交互、跨平台兼容性
5. 【国际化】i18n实现完整性、未翻译文本、语言切换的即时性
6. 【异常处理】try/except覆盖不足、静默吞异常、用户无反馈的错误

请用中文回答，对每个维度列出2-3个最重要的问题，每个问题1-2句话说明原因和修复方法。"""

t0 = time.time()
r = call(review_prompt, timeout=300)
t = time.time() - t0
if r["ok"]:
    texts = [b["text"] for b in r["data"]["content"] if b["type"] == "text"]
    thinks = [b["thinking"] for b in r["data"]["content"] if b["type"] == "thinking"]
    text = "\n".join(texts)
    usage = r["data"].get("usage", {})
    print(f"  ✅ 代码审查完成 {t:.1f}s", flush=True)
    print(f"  输出: {len(text)} chars", flush=True)
    print(f"  推理过程: {'有' if thinks else '无'} ({len(thinks)}段)", flush=True)
    print(f"  Usage: {usage}", flush=True)
    print(f"\n  {'─'*50}", flush=True)
    print(text[:4000], flush=True)
    if len(text) > 4000:
        print(f"\n  ... (后略, 共{len(text)}字符)", flush=True)
else:
    print(f"  ❌ {r.get('code','?')} | {r.get('detail','')[:300]}", flush=True)
    text = ""

# ── 保存 ──
outpath = os.path.expanduser("~/.hermes/cron/output/minimax-m3-review.json")
os.makedirs(os.path.dirname(outpath), exist_ok=True)
data = {
    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    "model": "minimax-m3",
    "endpoint": "messages (x-api-key+UA)",
    "connectivity_ok": r.get("ok", False),
    "review_time": round(t, 1),
    "review_length": len(text) if text else 0,
    "review_output": text[:5000] if text else str(r),
    "usage": r["data"].get("usage", {}) if r.get("ok") else {},
}
with open(outpath, "w") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
print(f"\n已保存: {outpath}", flush=True)
