#!/usr/bin/env python3 -u
"""Kimi K2.6 前端 UI 审查 - v2"""
import json, os, sys, time, urllib.request, urllib.error
sys.stdout.reconfigure(line_buffering=True)

# Read API key from env
api_key = ""
env_path = os.path.expanduser("~/.hermes/.env")
with open(env_path) as f:
    for line in f:
        l = line.strip()
        if "OPENCODE_GO_API_KEY" in l and not l.startswith("#"):
            parts = l.split("=", 1)
            if len(parts) > 1:
                val = parts[1].strip().strip("'\"")
                if len(val) > 10:
                    api_key = val
                    break

if not api_key:
    print("FATAL: No API key")
    sys.exit(1)

BASE = "https://opencode.ai/zen/go/v1"

def call(prompt, timeout=300):
    data = json.dumps({"model":"kimi-k2.6","messages":[{"role":"user","content":prompt}],"max_tokens":4096,"temperature":0.3}).encode()
    req = urllib.request.Request(f"{BASE}/chat/completions", data=data, headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type":"application/json",
        "User-Agent":"Mozilla/5.0",
    }, method="POST")
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            resp = json.loads(r.read().decode())
            t = time.time() - t0
            content = resp["choices"][0]["message"]["content"] or "[null]"
            usage = resp.get("usage",{})
            print(f"OK {t:.1f}s | {len(content)}字 | {json.dumps(usage)}", flush=True)
            return content
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:300]
        print(f"HTTPERR {e.code}: {body}", flush=True)
        return None
    except Exception as ex:
        print(f"ERR: {ex}", flush=True)
        return None

wd = "/root/projects/markitdown-gui"

files = {
    "ui/drop_area.py": open(f"{wd}/markitdown_gui/ui/drop_area.py").read(),
    "ui/file_list.py": open(f"{wd}/markitdown_gui/ui/file_list.py").read(),
    "ui/preview.py": open(f"{wd}/markitdown_gui/ui/preview.py").read(),
    "ui/settings_dialog.py": open(f"{wd}/markitdown_gui/ui/settings_dialog.py").read(),
    "app/main_window.py": open(f"{wd}/markitdown_gui/app/main_window.py").read(),
    "style.qss": open(f"{wd}/resources/styles/style.qss").read(),
}

all_code = ""
for name, src in files.items():
    all_code += f"\n--- {name} ---\n{src}\n"

print(f"Context: {len(all_code)} chars", flush=True)

prompt = f"""你是一个 PySide6 桌面应用 UI/UX 审查专家。请审查以下 MarkItDown GUI 前端代码。

{all_code}

从以下10个维度评审，每项给 P0/P1/P2 + 文件名 + 问题 + 修复建议：
1. 视觉一致性（颜色/字体/间距）
2. 控件布局（QSplitter/窗口缩放）
3. 拖拽交互反馈
4. 状态可视化（进度/进度条）
5. 信号/槽正确性
6. 跨平台兼容
7. 无障碍/Tab顺序
8. 国际化完整性
9. 异常处理
10. 性能（大列表/大文本）

只输出评审内容。用中文。"""

print("=== Kimi K2.6 前端审查 ===", flush=True)
result = call(prompt, 300)

if result:
    out = os.path.expanduser("~/.hermes/cron/output/kimi-k26-ui-review-result.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump({"review": result}, f, indent=2, ensure_ascii=False)
    print(f"Saved: {out}", flush=True)
else:
    print("FAILED", flush=True)

print("DONE", flush=True)
