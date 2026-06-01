#!/usr/bin/env python3 -u
"""Kimi K2.6 前端 UI 专项审查"""
import json, os, sys, time, urllib.request, urllib.error
sys.stdout.reconfigure(line_buffering=True)

# Load API key
API_KEY = ""
env_path = os.path.expanduser("~/.hermes/.env")
with open(env_path) as f:
    for line in f:
        l = line.strip()
        if "OPENCODE_GO_API_KEY" in l and not l.startswith("#"):
            parts = l.split("=", 1)
            if len(parts) > 1 and len(parts[1].strip()) > 10:
                API_KEY = parts[1].strip()
                break

if not API_KEY:
    print("FATAL: No API key found")
    sys.exit(1)

print(f"API_KEY loaded: YES", flush=True)

BASE = "https://opencode.ai/zen/go/v1"

def call_kimi(prompt, timeout=600):
    data = json.dumps({
        "model": "kimi-k2.6",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 8192,
        "temperature": 0.3
    }).encode()
    req = urllib.request.Request(
        f"{BASE}/chat/completions",
        data=data,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",
        },
        method="POST"
    )
    try:
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=timeout) as r:
            resp = json.loads(r.read().decode())
            t = time.time() - t0
            content = resp["choices"][0]["message"]["content"]
            usage = resp.get("usage", {})
            print(f"\nOK {t:.1f}s | {len(content)}字 | tokens={json.dumps(usage)}", flush=True)
            return content
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:500]
        print(f"\nHTTPERR {e.code}: {body}", flush=True)
        return None
    except Exception as ex:
        print(f"\nERR: {ex}", flush=True)
        return None

# Read all UI files
workdir = "/root/projects/markitdown-gui"
files = {
    "ui/drop_area.py": open(f"{workdir}/markitdown_gui/ui/drop_area.py").read(),
    "ui/file_list.py": open(f"{workdir}/markitdown_gui/ui/file_list.py").read(),
    "ui/preview.py": open(f"{workdir}/markitdown_gui/ui/preview.py").read(),
    "ui/settings_dialog.py": open(f"{workdir}/markitdown_gui/ui/settings_dialog.py").read(),
    "app/main_window.py": open(f"{workdir}/markitdown_gui/app/main_window.py").read(),
    "main.py": open(f"{workdir}/markitdown_gui/main.py").read(),
    "app/settings.py": open(f"{workdir}/markitdown_gui/app/settings.py").read(),
    "app/worker.py": open(f"{workdir}/markitdown_gui/app/worker.py").read(),
    "resources/styles/style.qss": open(f"{workdir}/resources/styles/style.qss").read(),
    "i18n/zh_CN.json": open(f"{workdir}/markitdown_gui/i18n/zh_CN.json").read(),
    "i18n/en_US.json": open(f"{workdir}/markitdown_gui/i18n/en_US.json").read(),
}

code_blocks = ""
for fname, content in files.items():
    code_blocks += f"\n### {fname}\n```python\n{content}\n```\n"

review_prompt = f"""你是一个专业的 PySide6/Qt 桌面应用前端 UI/UX 审查专家。请严格审查以下 Python 桌面 GUI 应用的 UI 前端代码。

## 项目概况
- 名称: MarkItDown GUI
- 技术栈: PySide6 (Qt for Python) 桌面应用
- 功能: 文件拖拽/选择 → MarkItDown 引擎转换 → Markdown 预览 → 导出
- 规模: 约 10 个前端文件 / ~900 行
- 特性: 中英双语(JSON文件), QThread 后台转换, 外部 QSS 暗色主题, QSplitter 左文件列表右预览布局

## 全部前端代码
{code_blocks}

## 评审维度
请逐项评审，每项给出优先级 (P0/P1/P2) + 代码位置 + 问题描述 + 修复建议:

1. 【视觉一致性】主题色、字体回退栈、间距、hover/active 状态
2. 【控件布局】QSplitter 比例、minimumSize、窗口缩放响应
3. 【拖拽交互】dragEnter/dragLeave/drop 反馈、style().unpolish/polish 生效性
4. 【状态可视化】转换进度、进度条缺失、多文件 ETA
5. 【信号/槽正确性】参数类型匹配、lambda 闭包、线程安全
6. 【跨平台兼容】字体 fallback、路径分隔符、macOS 差异、HiDPI
7. 【无障碍/Tab顺序】Tab 顺序、快捷键、focus 指示器
8. 【国际化完整性】所有文本是否走 i18n
9. 【异常处理】IO/转换/配置加载的 UI 反馈
10. 【性能】大列表 QListWidget、大文本预览渲染

## 输出格式
按优先级排序。每个问题格式:
[P0/P1/P2] 文件名 — 问题简述
  ▸ 详细描述
  ▸ 修复建议

最后给出总体评价 (A/B/C/D) 和改进优先级排序。用中文回答。"""

print("==== Kimi K2.6 前端审查开始 ====", flush=True)
print(f"代码上下文: {len(code_blocks)} 字符", flush=True)

result = call_kimi(review_prompt, 600)

if result:
    out_path = os.path.expanduser("~/.hermes/cron/output/kimi-k26-ui-review-result.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump({"review": result}, f, indent=2, ensure_ascii=False)
    print(f"\n结果已保存: {out_path}", flush=True)
    print("==== 审查完成 ====", flush=True)
else:
    print("FAILED: kimi-k2.6 returned no result", flush=True)

print("DONE", flush=True)
