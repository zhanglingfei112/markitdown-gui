#!/usr/bin/env python3
"""补测：minimax-m3 代码审查 + qwen3.7-max 全部"""
import json, os, sys, time, urllib.request, urllib.error

BASE = "https://opencode.ai/zen/go/v1"
env_path = os.path.expanduser("~/.hermes/.env")
api_key = None
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if line.startswith("OPENCODE_GO_API_KEY=") and not line.startswith("#"):
            parts = line.split("=", 1)
            if len(parts) > 1 and parts[1].strip():
                api_key = parts[1].strip()
                break

def call_chat(model, msgs, timeout=180):
    data = json.dumps({"model": model, "messages": msgs, "max_tokens": 4096, "temperature": 0.3}).encode()
    req = urllib.request.Request(f"{BASE}/chat/completions", data=data, headers={
        "Authorization": f"Bearer {api_key}", "Content-Type": "application/json", "User-Agent": "Mozilla/5.0",
    }, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode())
        return {"ok": True, "data": body}
    except urllib.error.HTTPError as e:
        detail = e.read().decode()[:500]
        print(f"    HTTP {e.code}: {detail[:200]}")
        return {"ok": False, "status": e.code, "detail": detail}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def call_msg(model, msgs, timeout=180):
    system_msg = None
    mlist = []
    for m in msgs:
        if m["role"] == "system":
            system_msg = m["content"]
        else:
            mlist.append({"role": m["role"], "content": m["content"]})
    body = {"model": model, "messages": mlist, "max_tokens": 8192}
    if system_msg:
        body["system"] = system_msg
    data = json.dumps(body).encode()
    req = urllib.request.Request(f"{BASE}/messages", data=data, headers={
        "x-api-key": api_key, "anthropic-version": "2023-06-01", "Content-Type": "application/json",
    }, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode())
        return {"ok": True, "data": body}
    except urllib.error.HTTPError as e:
        detail = e.read().decode()[:500]
        return {"ok": False, "status": e.code, "detail": detail}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def ext_chat(resp):
    if not resp.get("ok"):
        return f"[FAIL] {resp}", {}
    try:
        msg = resp["data"]["choices"][0]["message"]
        u = resp["data"].get("usage", {})
        return msg["content"], {"p": u.get("prompt_tokens","?"), "c": u.get("completion_tokens","?")}
    except Exception as e:
        return f"[PARSE] {e}", {}

def ext_msg(resp):
    if not resp.get("ok"):
        return f"[FAIL] {resp}", {}
    try:
        blocks = resp["data"]["content"]
        texts, thinks = [], []
        for b in blocks:
            if b["type"] == "text": texts.append(b["text"])
            elif b["type"] == "thinking": thinks.append(b["thinking"])
        u = resp["data"].get("usage", {})
        return "\n".join(texts), {"in": u.get("input_tokens","?"), "out": u.get("output_tokens","?")}
    except Exception as e:
        return f"[PARSE] {e}", {}

PROJECT_FILES = {
    "main.py": "42 lines, 应用入口。加载QSS样式→初始化Settings→创建MainWindow→exec",
    "main_window.py": "315 lines, 主窗口UI：菜单栏/分割布局/拖拽区/文件列表/预览区/按钮/状态栏。菜单有File/ Language/ Settings。支持语言切换。转换按钮→QThread后台执行。",
    "worker.py": "52 lines, QThread后台线程，遍历文件调用converter.convert()，通过信号progress/finished通知UI。",
    "converter.py": "36 lines, MarkItDown库封装，convert(file_path)→result.text_content",
    "settings.py": "88 lines, 类级单例(Settings)，json文件持久化(~/.markitdown_gui_settings.json)，含language/output_dir/ocr_enabled/llm_api_key，get_translations()加载i18n JSON。",
    "drop_area.py": "74 lines, drag/drop区域，QFrame虚线边框+active高亮。filesDropped信号。",
    "file_list.py": "157 lines, QListWidget自定义行布局(文件名+大小+状态标签)，status有pending/completed/failed/processing四种。",
    "preview.py": "47 lines, QTextEdit只读预览，黑色主题。",
    "settings_dialog.py": "75 lines, QDialog，表单含Language下拉/输出目录输入/OCR开关/API Key密码框。",
}
PROJECT_SUMMARY = (
    "PySide6桌面应用MarkItDown GUI，~930行代码，14个文件。"
    "功能：文件拖拽/选择→MarkItDown引擎转换→Markdown预览→导出。"
    "架构：MVC分层(app/ui/utils)，i18n通过JSON语言包(zh_CN/en_US)，"
    "QThread后台转换防阻塞，style.qss外部化暗色主题。"
)

code_review_prompt = f"""【代码审查】审查以下PySide6项目的代码安全性和潜在问题。

项目概况：{PROJECT_SUMMARY}

关键文件：
{chr(10).join(f'  - {k}: {v}' for k, v in PROJECT_FILES.items())}

审查以下方面：
1. 安全性：settings存储API Key的风险和改进
2. 线程安全：QThread使用的竞态条件
3. 内存/性能：大文件批量转换
4. 用户体验：不完善之处
5. 国际化：i18n完整性
6. 异常处理：不足的地方

每个问题标注P0/P1/P2级别 + 具体位置 + 修复建议。"""

arch_prompt = f"""【架构分析】分析PySide6项目：

{PROJECT_SUMMARY}

分析：
1. MVC分层合理性？MainWindow是否职责过重？
2. 插件系统扩展需要如何改造？
3. 增量转换/缓存设计？
4. Settings单例的替代方案？
5. 项目扩大到100+文件的瓶颈？

给出改进优先级和实施路径。"""

PROMPTS = [
    ("code_review", code_review_prompt),
    ("architecture_review", arch_prompt),
]

# ══════ minimax-m3 补测（只跑代码审查） ══════
print("=" * 60)
print("  minimax-m3 — 代码审查补测")
print("=" * 60)
results_m3 = {}
for tid, prompt in PROMPTS:
    print(f"\n  [{tid}] 发送...", end=" ", flush=True)
    t0 = time.time()
    resp = call_chat("minimax-m3", [{"role": "user", "content": prompt}], timeout=300)
    content, usage = ext_chat(resp)
    t = time.time() - t0
    if resp.get("ok"):
        print(f"✓ {t:.1f}s | tokens={usage}")
        print(f"  长度: {len(content)} chars")
        print(f"  首行: {content.strip()[:150]}")
        results_m3[tid] = {"content": content[:3000], "usage": usage, "time": round(t, 1)}
    else:
        print(f"✗ {t:.1f}s")
        print(f"  {content[:500]}")
        results_m3[tid] = {"content": str(content)[:500], "usage": usage, "time": round(t, 1)}
    time.sleep(3)

# ══════ qwen3.7-max 全部测试 ══════
print("\n\n" + "=" * 60)
print("  qwen3.7-max — 全部测试 (Anthropic messages)")
print("=" * 60)
results_qwen = {}

qwen_tests = [
    ("knowledge_transformer", "简述Transformer的核心创新是什么？"),
    ("knowledge_translate", "将以下英文翻译为中文：'The transformer architecture revolutionized NLP by introducing self-attention mechanisms that enable parallel processing of sequence data, overcoming the sequential limitations of RNNs.'"),
    ("logic_deduction", "如果A比B高，B比C高，C比D高，问A比D高吗？请给出推理过程。"),
    ("logic_math", "一个笼子里有鸡和兔子，共35个头，94只脚，问鸡和兔子各有多少只？请给出解题步骤。"),
    ("code_review", code_review_prompt),
    ("architecture_review", arch_prompt),
]

for tid, prompt in qwen_tests:
    print(f"\n  [{tid}] 发送...", end=" ", flush=True)
    t0 = time.time()
    resp = call_msg("qwen3.7-max", [{"role": "user", "content": prompt}], timeout=300)
    content, usage = ext_msg(resp)
    t = time.time() - t0
    if resp.get("ok"):
        print(f"✓ {t:.1f}s | tokens={usage}")
        print(f"  长度: {len(content)} chars")
        print(f"  首行: {content.strip()[:150]}")
        results_qwen[tid] = {"content": content[:3000], "usage": usage, "time": round(t, 1)}
    else:
        print(f"✗ {t:.1f}s")
        print(f"  {content[:500]}")
        results_qwen[tid] = {"content": str(content)[:500], "usage": usage, "time": round(t, 1)}
    time.sleep(3)

# 保存
out = {
    "minimax-m3": results_m3,
    "qwen3.7-max": results_qwen,
}
path = os.path.expanduser("~/.hermes/cron/output/model_test_round2.json")
os.makedirs(os.path.dirname(path), exist_ok=True)
with open(path, "w") as f:
    json.dump(out, f, indent=2, ensure_ascii=False)

# 汇总
print("\n\n" + "=" * 60)
print("  qwen3.7-max 汇总 + minimax-m3 补测")
print("=" * 60)
for model in ["minimax-m3", "qwen3.7-max"]:
    print(f"\n  ── {model} ──")
    for tid, r in out.get(model, {}).items():
        status = "✓" if "usage" in r and r.get("usage") else "?"
        print(f"    {status} {tid:30s} {r.get('time','?'):>5.1f}s  {len(str(r.get('content','')))} chars  {r.get('usage','')}")
