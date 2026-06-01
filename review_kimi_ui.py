#!/usr/bin/env python3 -u
"""kimi-k2.6 前端/UI 审查"""
import json, os, sys, time, urllib.request, urllib.error
sys.stdout.reconfigure(line_buffering=True)

BASE = "https://opencode.ai/zen/go/v1"
api_key = ""
with open(os.path.expanduser("~/.hermes/.env")) as f:
    for line in f:
        l = line.strip()
        if "OPENCODE_GO_API_KEY" in l and not l.startswith("#"):
            parts = l.split("=", 1)
            if len(parts) > 1 and len(parts[1].strip()) > 10 and not parts[1].startswith("#"):
                api_key = parts[1].strip()
                break

def call(prompt, timeout=300):
    data = json.dumps({"model":"kimi-k2.6","messages":[{"role":"user","content":prompt}],"max_tokens":8192,"temperature":0.3}).encode()
    req = urllib.request.Request(f"{BASE}/chat/completions", data=data, headers={
        "Authorization": "Bearer " + api_key,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0",
    }, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return {"ok": True, "data": json.loads(r.read().decode())}
    except urllib.error.HTTPError as e:
        return {"ok": False, "code": e.code, "body": e.read().decode()[:500]}
    except Exception as ex:
        return {"ok": False, "error": str(ex)}

def run(name, prompt, timeout=300):
    print("[" + name + "] 发送...", end=" ", flush=True)
    t0 = time.time()
    r = call(prompt, timeout)
    t = time.time() - t0
    if r["ok"]:
        c = r["data"]["choices"][0]["message"]["content"]
        u = r["data"].get("usage", {})
        print("OK " + str(t) + "s | " + str(len(c)) + "字 | tokens=" + str(u), flush=True)
        return c
    else:
        print("FAIL " + str(r.get("code", "?")) + " " + str(t) + "s | " + str(r.get("body",""))[:200], flush=True)
        return None
    time.sleep(2)

# Build the review prompt without f-string to avoid brace issues
code_context = """
## 项目概况
- 名称: MarkItDown GUI
- 类型: PySide6 桌面应用
- 规模: 930行 / 14文件
- 功能: 文件拖拽/选择 -> MarkItDown转换 -> Markdown预览 -> 导出
- 特性: 中英双语(QJSON语言包), QThread后台转换, QSS暗色主题, 20+格式支持

## UI 类文件源码

### drop_area.py (拖拽放置区域)
```python
class DropArea(QWidget):
    filesDropped = Signal(list)
    def __init__(self):
        super().__init__(); self.setAcceptDrops(True); self.init_ui()
    def init_ui(self):
        self.frame = QFrame(); self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setMinimumHeight(120)
        self.frame.setStyleSheet('''QFrame { border: 2px dashed #444; border-radius: 10px; } QFrame[active=true] { border: 2px dashed #007acc; }''')
        self.label = QLabel("拖拽文件到此处\\n(Drop files here)"); self.label.setAlignment(Qt.AlignCenter)
    def update_text(self, texts): self.label.setText(texts.get("drop_text", "..."))
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): event.accept(); self.frame.setProperty("active","true")
        else: event.ignore()
    def dragLeaveEvent(self, event): self.frame.setProperty("active","false")
    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls() if u.toLocalFile()]
        self.frame.setProperty("active","false"); self.filesDropped.emit(files)
```

### file_list.py (文件列表)
```python
class FileList(QWidget):
    def __init__(self):
        super().__init__(); self.init_ui()
        self.files_data = {}; self.texts = {}
    def init_ui(self):
        self.title_label = QLabel("待转换文件"); self.title_label.setStyleSheet("font-weight:bold;margin-bottom:5px")
        self.list_widget = QListWidget(); self.list_widget.setSelectionMode(QListWidget.SingleSelection)
    def add_files(self, files):
        for path in files:
            if path in self.files_data: continue
            item = QListWidgetItem(); widget = QWidget()
            row = QHBoxLayout(widget); row.setContentsMargins(5,2,5,2)
            name = QLabel("["+str(os.path.getsize(path)/1024)[:4]+"KB] "+os.path.basename(path))
            status = QLabel("Pending"); status.setStyleSheet("color:#888")
            row.addWidget(name); row.addStretch(); row.addWidget(status)
            item.setSizeHint(widget.sizeHint())
            self.list_widget.addItem(item); self.list_widget.setItemWidget(item,widget)
            self.files_data[path] = {"item":item,"status_label":status,"status":"pending","result":None}
    def update_file_status(self, path, status, result=None, error=None):
        if path not in self.files_data: return
        data = self.files_data[path]; data["status"]=status; data["result"]=result
        t = self.texts or {}
        color = {"completed":"#4caf50","failed":"#f44336","processing":"#094771"}.get(status,"#888")
        label = {"completed":t.get("status_done","Done"),"failed":t.get("status_failed","Failed"),
                 "processing":t.get("status_processing","Processing...")}.get(status,"Pending")
        if status=="failed":
            label += ": "+str(error)[:15]
        data["status_label"].setText(label); data["status_label"].setStyleSheet("color:"+color)
    def get_all_files(self): return list(self.files_data.keys())
    def get_completed_files(self): return {p:d["result"] for p,d in self.files_data.items() if d["status"]=="completed"}
    def remove_selected(self):
        item = self.list_widget.currentItem()
        if not item: return 0
        for p,d in self.files_data.items():
            if d["item"]==item: self.list_widget.takeItem(self.list_widget.row(item)); del self.files_data[p]; return 1
        return 0
    def clear_all(self): self.list_widget.clear(); self.files_data.clear()
```

### preview.py (预览区域)
```python
class PreviewArea(QWidget):
    def __init__(self): super().__init__(); self.init_ui()
    def init_ui(self):
        self.title_label = QLabel("Markdown 预览"); self.title_label.setStyleSheet("font-weight:bold;margin-bottom:5px")
        self.editor = QTextEdit(); self.editor.setReadOnly(True)
        self.editor.setPlaceholderText("转换结果将在此显示...")
        self.editor.setStyleSheet("QTextEdit{background:#1e1e1e;color:#d4d4d4;font-family:Consolas,Monaco,'Courier New',monospace;font-size:13px;border:1px solid #3c3c3c}")
        self.editor.setPlainText(content)
    def set_content(self, content): self.editor.setPlainText(content)
    def update_text(self, texts):
        self.title_label.setText(texts.get("preview_title","Preview"))
        self.editor.setPlaceholderText(texts.get("preview_placeholder","Results here..."))
```

### settings_dialog.py (设置对话框)
```python
class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent); self.setWindowTitle("Preferences"); self.resize(400,300)
        self.init_ui(); self.update_text()
    def init_ui(self):
        self.lang_combo = QComboBox(); self.lang_combo.addItems(["zh_CN","en_US"])
        self.output_edit = QLineEdit(); self.ocr_check = QCheckBox()
        self.api_edit = QLineEdit(); self.api_edit.setEchoMode(QLineEdit.Password)
    def update_text(self):
        texts = Settings.get_translations(Settings.get("language","zh_CN"))
        self.setWindowTitle(texts.get("pref_title","Preferences"))
    def accept_settings(self):
        Settings.set("language",self.lang_combo.currentText())
        Settings.save(); self.accept()
```

### main_window.py (UI 布局部分)
```python
def init_ui(self):
    self.create_menus()
    central_widget = QWidget(); self.setCentralWidget(central_widget)
    main_layout = QHBoxLayout(central_widget); main_layout.setContentsMargins(10,10,10,10)
    splitter = QSplitter()
    left_widget = QWidget(); left_layout = QVBoxLayout(left_widget)
    left_layout.setContentsMargins(0,0,0,0)
    self.drop_area = DropArea(); self.file_list = FileList()
    self.convert_btn = QPushButton("开始转换"); self.export_btn = QPushButton("导出文件")
    self.remove_btn = QPushButton("删除选中"); self.clear_btn = QPushButton("清空列表")
    btn_layout = QHBoxLayout()
    for b in [self.convert_btn,self.export_btn,self.remove_btn,self.clear_btn]: btn_layout.addWidget(b)
    left_layout.addWidget(self.drop_area); left_layout.addWidget(self.file_list); left_layout.addLayout(btn_layout)
    self.preview_area = PreviewArea()
    splitter.addWidget(left_widget); splitter.addWidget(self.preview_area)
    splitter.setStretchFactor(1, 2)
    main_layout.addWidget(splitter)
    self.status_bar = QStatusBar(); self.setStatusBar(self.status_bar)
    self.status_bar.showMessage("Ready")

def create_menus(self):
    menubar = self.menuBar()
    self.menu_file = menubar.addMenu("File"); self.menu_settings = menubar.addMenu("Settings")
    self.menu_lang = menubar.addMenu("Language")
    self.action_open = self.menu_file.addAction("Open File")
    self.action_folder = self.menu_file.addAction("Open Folder")
    self.action_exit = self.menu_file.addAction("Exit"); self.action_exit.triggered.connect(self.close)
    self.action_pref = self.menu_settings.addAction("Preferences"); self.action_pref.triggered.connect(self.open_settings)
    self.action_zh = self.menu_lang.addAction("中文"); self.action_en = self.menu_lang.addAction("English")

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

def show_preview(self, item):
    path = self.file_list.get_file_path_from_item(item)
    if path in self.file_list.files_data:
        d = self.file_list.files_data[path]
        if d["status"]=="completed" and d["result"]: self.preview_area.set_content(d["result"])
"""

review_prompt = """你是一个专业的 PySide6/Qt 桌面应用前端 UI/UX 审查专家。请审查以下桌面 GUI 应用的 UI 代码：

""" + code_context + """

## 审查要求 (前端/UI/UX 角度)

1. 【视觉一致性】主题色、字体、间距、交互反馈是否统一？
2. 【响应式布局】窗口缩放时组件表现如何？Splitter比例、最小尺寸？
3. 【拖拽交互】drag/drop反馈是否完善？有无错误提示？
4. 【状态可视化】转换进度、成功/失败对用户的可见反馈？缺不缺进度条？
5. 【跨平台兼容】字体fallback、路径分隔符、macOS菜单栏差异、HiDPI？
6. 【无障碍】Tab顺序、键盘导航、屏幕阅读器支持？
7. 【国际化】所有硬编码字符串都走i18n？切换语言即时更新？

每个问题标 P0/P1/P2 + 代码位置(文件名/行号范围) + 1-2句修复建议。用中文回答。"""

r1 = run("UI审查", review_prompt, 300)

# Second part
arch_prompt = """基于同一个 PySide6 桌面项目 (930行, PySide6, 文件拖拽转Markdown)，请从 UI 架构角度给出建议：

当前UI组件：
- ui/drop_area.py - 拖拽区域
- ui/file_list.py - 文件列表 (QListWidget)
- ui/preview.py - 预览 (QTextEdit)
- ui/settings_dialog.py - 设置对话框
- app/main_window.py - 主窗口, 负责所有UI组装+信号连接

请对以下6点各给1-3句具体建议：
1. MVVM vs MVC: PySide6项目中UI层更适合哪种模式？
2. MainWindow(315行)是否UI装配过重？如何拆解？
3. QListWidget在1000+文件时性能如何？替代方案？
4. 批量转换的UI反馈方案（进度条/ETA/缓存）？
5. 亮色/暗色主题热切换方案？
6. macOS/Linux/Windows三平台适配要点？

用中文回答。"""

r2 = run("UI架构", arch_prompt, 300)

# Save
results = {"ui_review": r1[:8000] if r1 else "FAIL", "ui_architecture": r2[:8000] if r2 else "FAIL"}
out = os.path.expanduser("~/.hermes/cron/output/kimi-k26-ui-review.json")
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, "w") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
print("\n结果保存: " + out, flush=True)
