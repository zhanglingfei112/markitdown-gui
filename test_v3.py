#!/usr/bin/env python3 -u
import json, os, sys, time, urllib.request, urllib.error, subprocess
sys.stdout.reconfigure(line_buffering=True)

BASE = "https://opencode.ai/zen/go/v1"
env_path = os.path.expanduser("~/.hermes/.env")
api_key = ""
with open(env_path) as f:
    for line in f:
        l = line.strip()
        prefix = "OPENCODE_GO_API_KEY="
        if l.startswith(prefix) and not l.startswith("#"):
            val = l[len(prefix):].strip()
            if len(val) > 10:
                api_key = val
                break

print(f"key len={len(api_key)}", flush=True)

def http(url, data, headers, timeout=120):
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return {"ok": True, "data": json.loads(r.read().decode()), "code": r.status}
    except urllib.error.HTTPError as e:
        return {"ok": False, "code": e.code, "body": e.read().decode()[:500]}
    except Exception as ex:
        return {"ok": False, "error": str(ex)}

# Test 1: minimax-m3 via messages endpoint (as per routing table)
print("\n=== Test 1: minimax-m3 via messages (anthropic_messages) ===", flush=True)
body = json.dumps({"model": "minimax-m3", "messages": [{"role":"user","content":"Hi，回复OK"}], "max_tokens": 100}).encode()
r = http(f"{BASE}/messages", body, {"x-api-key": api_key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"})
if r["ok"]: print(f"  OK via messages: {json.dumps(r['data'])[:200]}", flush=True)
else: print(f"  FAIL via messages: {r['code']} | {r.get('body','')[:200]}", flush=True)

# Test 2: qwen3.7-max via messages with UA
print("\n=== Test 2: qwen3.7-max via messages (anthropic_messages) ===", flush=True)
for i, (variant, headers) in enumerate([
    ("x-api-key + UA", {"x-api-key": api_key, "anthropic-version": "2023-06-01", "Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}),
    ("x-api-key no UA", {"x-api-key": api_key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"}),
]):
    body = json.dumps({"model": "qwen3.7-max", "messages": [{"role":"user","content":"Hi，回复OK_CONNECTED"}], "max_tokens": 100}).encode()
    r = http(f"{BASE}/messages", body, headers)
    if r["ok"]:
        texts = [b.get("text","") for b in r["data"]["content"] if b.get("type")=="text"]
        has_think = any(b.get("type")=="thinking" for b in r["data"]["content"])
        print(f"  [{variant}] OK | has_thinking={has_think} | {''.join(texts)[:100]}", flush=True)
    else:
        print(f"  [{variant}] {r['code']} | {r.get('body','')[:150]}", flush=True)
    time.sleep(3)

# Test 3: qwen3.7-max via chat_completions (should fail)
print("\n=== Test 3: qwen3.7-max via chat_completions ===", flush=True)
body = json.dumps({"model": "qwen3.7-max", "messages": [{"role":"user","content":"Hi"}], "max_tokens": 50}).encode()
r = http(f"{BASE}/chat/completions", body, {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
if r["ok"]: print(f"  OK: {r['data']['choices'][0]['message']['content'][:100]}", flush=True)
else: print(f"  {r['code']} | {r.get('body','')[:150]}", flush=True)

# Test 4: curl native test for qwen3.7-max
print("\n=== Test 4: curl for qwen3.7-max ===", flush=True)
key = api_key
for auth_type in ["x-api-key", "Authorization: Bearer"]:
    if auth_type == "x-api-key":
        h = f"x-api-key: {key}"
    else:
        h = f"Authorization: Bearer {key}"
    cmd = ["curl", "-s", "-w", "\\nHTTP_CODE:%{http_code}", f"{BASE}/messages",
           "-H", h, "-H", "anthropic-version: 2023-06-01", "-H", "Content-Type: application/json",
           "-H", "User-Agent: Mozilla/5.0",
           "-d", json.dumps({"model":"qwen3.7-max","messages":[{"role":"user","content":"回复OK"}],"max_tokens":50})]
    r2 = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    last = r2.stdout.strip().split("\n")[-1]
    print(f"  [{auth_type.split(':')[0]}] {last}", flush=True)

# Test 5: minimax-m3 via chat with review prompt (100-200 chars)
print("\n=== Test 5: minimax-m3 chat_completions with medium prompt ===", flush=True)
prompts = [
    ("short", "审查PySide6代码：QMainWindow含菜单栏和拖拽区。找3个安全隐患。"),
    ("medium", "审查代码：class MainWindow(QMainWindow):\n  def __init__(self):\n    self.init_ui()\n    self.connect_signals()\n  def init_ui(self):\n    # 创建菜单\n    create_menus()\n  def create_menus(self):\n    file_menu = self.menuBar().addMenu('File')\n    file_menu.addAction('Open')\n  # 安全检查\n  def open_file_dialog(self):\n    files, _ = QFileDialog.getOpenFileNames()\n    return files"),
]
for name, prompt in prompts:
    body = json.dumps({"model": "minimax-m3", "messages": [{"role":"user","content":prompt}], "max_tokens": 2048, "temperature": 0.3}).encode()
    t0 = time.time()
    r = http(f"{BASE}/chat/completions", body, {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
    t = time.time() - t0
    if r["ok"]:
        c = r["data"]["choices"][0]["message"]["content"]
        print(f"  [{name}] OK {t:.1f}s | {len(c)} chars | First: {c[:100]}", flush=True)
    else:
        print(f"  [{name}] {r['code']} {t:.1f}s | {r.get('body','')[:200]}", flush=True)
    time.sleep(3)

print(flush=True)
print("=== DONE ===", flush=True)
