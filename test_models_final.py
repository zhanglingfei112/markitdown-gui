#!/usr/bin/env python3 -u
"""补测 minimax-m3 + qwen3.7-max，带实时flush"""
import json, os, sys, time, urllib.request, urllib.error
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

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
print(f"API key found (len={len(api_key)})", flush=True)

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
        print(f"    HTTP {e.code}: {detail[:200]}", flush=True)
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
        print(f"    HTTP {e.code}: {detail[:200]}", flush=True)
        return {"ok": False, "status": e.code, "detail": detail}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def ext_chat(resp):
    if not resp.get("ok"):
        return f"[FAIL]", {}
    try:
        msg = resp["data"]["choices"][0]["message"]
        u = resp["data"].get("usage", {})
        return msg["content"], {"p": u.get("prompt_tokens","?"), "c": u.get("completion_tokens","?")}
    except Exception as e:
        return f"[PARSE] {e}", {}

def ext_msg(resp):
    if not resp.get("ok"):
        return f"[FAIL]", {}
    try:
        blocks = resp["data"]["content"]
        texts = [b["text"] for b in blocks if b["type"] == "text"]
        u = resp["data"].get("usage", {})
        return "\n".join(texts), {"in": u.get("input_tokens","?"), "out": u.get("output_tokens","?")}
    except Exception as e:
        return f"[PARSE] {e}", {}

PROJECT_FILES = {
    "main.py": "42 lines",
    "main_window.py": "315 lines, 含菜单栏/分割布局/按钮/QThread启动/语言切换",
    "worker.py": "52 lines, QThread",
    "converter.py": "36 lines, MarkItDown封装",
    "settings.py": "88 lines, 类级单例+JSON持久化",
    "drop_area.py": "74 lines, drag/drop",
    "file_list.py": "157 lines, 自定义列表",
    "preview.py": "47 lines, 预览区域",
    "settings_dialog.py": "75 lines, 设置对话框",
}
PROJECT_SUMMARY = "PySide6桌面应用，~930行代码，14文件。MVC分层，i18n通过JSON，QThread后台转换，暗色主题。"

code_review_prompt = f"""审查以下PySide6项目：

{PROJECT_SUMMARY}

关键文件：{chr(10).join(f'  - {k}: {v}' for k, v in PROJECT_FILES.items())}

审查：1.安全性 2.线程安全 3.内存/性能 4.用户体验 5.i18n完整性 6.异常处理
每个问题标注P0/P1/P2级别 + 具体位置 + 修复建议。"""

arch_prompt = f"""分析PySide6项目架构：

{PROJECT_SUMMARY}

分析：1.MVC分层合理性 2.插件系统扩展 3.增量转换/缓存设计 4.Settings单例替代方案 5.扩大到100+文件的瓶颈
给出改进优先级和实施路径。"""

PROMPTS = [
    ("code_review", code_review_prompt),
    ("architecture_review", arch_prompt),
]

results = {}

# ═══ minimax-m3 补测 ═══
print("\n>>> minimax-m3 code review + architecture", flush=True)
for tid, prompt in PROMPTS:
    print(f"  [{tid}] ...", end=" ", flush=True)
    t0 = time.time()
    resp = call_chat("minimax-m3", [{"role": "user", "content": prompt}], timeout=300)
    content, usage = ext_chat(resp)
    t = time.time() - t0
    ok = resp.get("ok", False)
    print(f"{'✓' if ok else '✗'} {t:.1f}s | {len(content)} chars | tokens={usage}", flush=True)
    print(f"  首行: {content.strip()[:200]}", flush=True)
    results.setdefault("minimax-m3", {})[tid] = {
        "content": content[:3000] if ok else str(content),
        "usage": usage, "time": round(t, 1), "ok": ok
    }
    time.sleep(3)

# ═══ qwen3.7-max 全部测试 ═══
print("\n>>> qwen3.7-max 全部测试", flush=True)
qwen_tests = [
    ("knowledge_transformer", "简述Transformer的核心创新是什么？"),
    ("knowledge_translate", "翻译为中文：'The transformer architecture revolutionized NLP by introducing self-attention mechanisms that enable parallel processing of sequence data.'"),
    ("logic_deduction", "如果A比B高，B比C高，C比D高，A比D高吗？推理过程。"),
    ("logic_math", "鸡兔同笼：35头94脚，各几只？解题步骤。"),
    ("code_review", code_review_prompt),
    ("architecture_review", arch_prompt),
]
for tid, prompt in qwen_tests:
    print(f"  [{tid}] ...", end=" ", flush=True)
    t0 = time.time()
    resp = call_msg("qwen3.7-max", [{"role": "user", "content": prompt}], timeout=300)
    content, usage = ext_msg(resp)
    t = time.time() - t0
    ok = resp.get("ok", False)
    print(f"{'✓' if ok else '✗'} {t:.1f}s | {len(content)} chars | tokens={usage}", flush=True)
    if ok:
        print(f"  首行: {content.strip()[:200]}", flush=True)
    results.setdefault("qwen3.7-max", {})[tid] = {
        "content": content[:3000] if ok else str(content),
        "usage": usage, "time": round(t, 1), "ok": ok
    }
    time.sleep(3)

# 保存
outpath = os.path.expanduser("~/.hermes/cron/output/model_test_results_full.json")
os.makedirs(os.path.dirname(outpath), exist_ok=True)
with open(outpath, "w") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
print(f"\n✅ 结果已保存到 {outpath}", flush=True)

# 汇总
print("\n" + "=" * 58)
print("  模型对比汇总")
print("=" * 58)
test_names = {"knowledge_transformer": "基础·Transformer", "knowledge_translate": "基础·翻译",
              "logic_deduction": "逻辑·三段论", "logic_math": "逻辑·鸡兔同笼",
              "code_review": "任务·代码审查", "architecture_review": "任务·架构分析"}
for model in ["minimax-m3", "qwen3.7-max"]:
    print(f"\n  ── {model} ──")
    for tid, r in results.get(model, {}).items():
        status = "✓" if r.get("ok") else "✗"
        name = test_names.get(tid, tid)
        print(f"    {status} {name:20s} {r.get('time',0):>6.1f}s  {r.get('usage','')}")
print(flush=True)

# 输出详细内容
print("\n\n========== 详细输出 ==========", flush=True)
for model in ["minimax-m3", "qwen3.7-max"]:
    print(f"\n{'#'*60}")
    print(f"#  {model}")
    print(f"{'#'*60}", flush=True)
    for tid, r in results.get(model, {}).items():
        name = test_names.get(tid, tid)
        status = "✓" if r.get("ok") else "✗"
        print(f"\n{'─'*50}")
        print(f"  {name}  {status}  {r.get('time',0)}s  tokens={r.get('usage','')}")
        print(f"{'─'*50}")
        print(r.get("content", "(empty)")[:2500])
        print(flush=True)
