#!/usr/bin/env python3 -u
"""针对性补测"""
import json, os, sys, time, urllib.request, urllib.error
sys.stdout.reconfigure(line_buffering=True)

BASE = "https://opencode.ai/zen/go/v1"
env_path = os.path.expanduser("~/.hermes/.env")
api_key = ""
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if line.startswith("OPENCODE_GO_API_KEY=*** and not line.startswith("#"):
            parts = line.split("=", 1)
            if len(parts) > 1 and len(parts[1].strip()) > 10:
                api_key = parts[1].strip()
                break
print(f"key len={len(api_key)}", flush=True)

def req(url, data, headers, timeout=120):
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return {"ok": True, "data": json.loads(r.read().decode()), "status": r.status}
    except urllib.error.HTTPError as e:
        return {"ok": False, "status": e.code, "body": e.read().decode()[:500]}
    except Exception as ex:
        return {"ok": False, "error": str(ex)}

# ── 测试1: minimax-m3 走 messages 端点 ──
print("\n=== 测试1: minimax-m3 走 anthropic_messages 端点 ===", flush=True)
for prompt_name, prompt in [
    ("简单", "Hi"),
    ("代码审查_短", "审查这段PySide6代码：class MainWindow(QMainWindow): def __init__(self): self.init_ui()。找出安全问题。")
]:
    body = json.dumps({
        "model": "minimax-m3",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 2048
    }).encode()
    t0 = time.time()
    r = req(f"{BASE}/messages", body, {
        "x-api-key": api_key, "anthropic-version": "2023-06-01", "Content-Type": "application/json",
    })
    t = time.time() - t0
    print(f"  [{prompt_name}] {r['status'] if r.get('ok') else r.get('status','?')} {t:.1f}s", flush=True)
    if r.get("ok"):
        try:
            texts = [b.get("text","") for b in r["data"]["content"] if b.get("type")=="text"]
            print(f"    响应: {''.join(texts)[:200]}", flush=True)
        except Exception as e:
            print(f"    解析错误: {e}: {json.dumps(r['data'])[:200]}", flush=True)
    else:
        print(f"    错误: {r.get('body','')[:200]}", flush=True)
    time.sleep(2)

# ── 测试2: minimax-m3 走 chat_completions + 长 prompt + 缩短版本 ──
print("\n=== 测试2: minimax-m3 短版代码审查 (chat_completions) ===", flush=True)
short_prompt = "审查PySide6应用代码：主窗口含菜单栏和文件拖拽。请找出3个安全隐患和3个性能问题，各标注P0/P1/P2。"
body = json.dumps({
    "model": "minimax-m3",
    "messages": [{"role": "user", "content": short_prompt}],
    "max_tokens": 4096,
    "temperature": 0.3
}).encode()
t0 = time.time()
r = req(f"{BASE}/chat/completions", body, {
    "Authorization": f"Bearer {api_key}", "Content-Type": "application/json", "User-Agent": "Mozilla/5.0",
})
t = time.time() - t0
print(f"  短版 [{r['status'] if r.get('ok') else r.get('status','?')}] {t:.1f}s", flush=True)
if r.get("ok"):
    try:
        c = r["data"]["choices"][0]["message"]["content"]
        print(f"  响应 ({len(c)} chars): {c[:500]}", flush=True)
    except Exception as e:
        print(f"  解析错: {e}", flush=True)
else:
    print(f"  错误: {r.get('body','')[:300]}", flush=True)
time.sleep(3)

# ── 测试3: qwen3.7-max 走 messages + 加 User-Agent ──
print("\n=== 测试3: qwen3.7-max messages + User-Agent ===", flush=True)
for prompt_name, prompt in [
    ("简单", "Hi, 请回复'OK_CONNECTED'"),
    ("代码审查短", "审查PySide6代码：主窗口QMainWindow含菜单栏和按钮。找出主要安全问题。"),
]:
    body = json.dumps({
        "model": "qwen3.7-max",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 2048
    }).encode()
    t0 = time.time()
    r = req(f"{BASE}/messages", body, {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0",
    })
    t = time.time() - t0
    print(f"  [{prompt_name}] {r['status'] if r.get('ok') else r.get('status','?')} {t:.1f}s", flush=True)
    if r.get("ok"):
        try:
            texts = [b.get("text","") for b in r["data"]["content"] if b.get("type")=="text"]
            print(f"  响应 ({sum(len(t) for t in texts)} chars): {''.join(texts)[:300]}", flush=True)
            if any(b.get("type")=="thinking" for b in r["data"]["content"]):
                print(f"  → 含 thinking 推理过程", flush=True)
        except Exception as e:
            print(f"  解析: {json.dumps(r['data'])[:200]}", flush=True)
    else:
        print(f"  错误: {r.get('body','')[:300]}", flush=True)
    time.sleep(3)

# ── 测试4: qwen3.7-max 走 messages + 用 curl 方式(requests) ──
print("\n=== 测试4: qwen3.7-max messages + Authorization: Bearer 试试 ===", flush=True)
body = json.dumps({
    "model": "qwen3.7-max",
    "messages": [{"role": "user", "content": "回复'OK'" }],
    "max_tokens": 50
}).encode()
r = req(f"{BASE}/messages", body, {
    "Authorization": f"Bearer {api_key}",
    "anthropic-version": "2023-06-01",
    "Content-Type": "application/json",
})
print(f"  Bearer: {r['status'] if r.get('ok') else r.get('status','?')} | {r.get('body','')[:200]}", flush=True)

# ── 测试5: 直接用 curl 调 qwen3.7-max ──
print("\n=== 测试5: curl 直接调 qwen3.7-max ===", flush=True)
import subprocess
key = api_key
for header_type in ["x-api-key", "Authorization: Bearer"]:
    if header_type == "x-api-key":
        h = f"x-api-key: {key}"
    else:
        h = f"Authorization: Bearer {key}"
    cmd = [
        "curl", "-s", "-w", "\\nHTTP_CODE:%{http_code}",
        f"{BASE}/messages",
        "-H", h,
        "-H", "anthropic-version: 2023-06-01",
        "-H", "Content-Type: application/json",
        "-H", "User-Agent: Mozilla/5.0",
        "-d", json.dumps({"model":"qwen3.7-max","messages":[{"role":"user","content":"回复OK_CONNECTED"}],"max_tokens":50})
    ]
    r2 = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    print(f"  {header_type.split(':')[0]}: {r2.stdout[-80:]}", flush=True)

print("\n✅ 测试完", flush=True)
