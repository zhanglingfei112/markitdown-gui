#!/usr/bin/env python3 -u
"""Kimi K2.6 前端 UI 审查 - v3 (compact)"""
import json, os, sys, time, urllib.request, urllib.error
sys.stdout.reconfigure(line_buffering=True)

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

def call(prompt, timeout=600):
    data = json.dumps({"model":"kimi-k2.6","messages":[{"role":"user","content":prompt}],"max_tokens":4096,"temperature":0.3}).encode()
    req = urllib.request.Request(f"{BASE}/chat/completions", data=data, headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type":"application/json",
        "User-Agent":"Mozilla/5.0",
    }, method="POST")
    t0 = time.time()
    print("Calling API...", flush=True)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            resp = json.loads(r.read().decode())
            t = time.time() - t0
            content = resp["choices"][0]["message"]["content"] or "[null]"
            usage = resp.get("usage",{})
            print(f"OK {t:.1f}s | {len(content)}字 | cost={usage.get('cost',0)}", flush=True)
            return content
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:300]
        print(f"HTTPERR {e.code}: {body}", flush=True)
        return None
    except Exception as ex:
        print(f"ERR: {ex}", flush=True)
        return None

wd = "/root/projects/markitdown-gui"

# Build a focused code context
code = ""
code += "\n### ui/drop_area.py\n" + open(f"{wd}/markitdown_gui/ui/drop_area.py").read()
code += "\n### ui/file_list.py\n" + open(f"{wd}/markitdown_gui/ui/file_list.py").read()
code += "\n### ui/preview.py\n" + open(f"{wd}/markitdown_gui/ui/preview.py").read()
code += "\n### ui/settings_dialog.py\n" + open(f"{wd}/markitdown_gui/ui/settings_dialog.py").read()

# Main window only UI parts (omit business logic to reduce size)
mw_src = open(f"{wd}/markitdown_gui/app/main_window.py").read()
code += "\n### app/main_window.py\n" + mw_src

code += "\n### resources/styles/style.qss\n" + open(f"{wd}/resources/styles/style.qss").read()

print(f"Context: {len(code)} chars", flush=True)

prompt = f"""Review this PySide6 desktop app's frontend UI code (MarkItDown GUI - file converter). Focus on UI/UX issues.

{code}

Rate each finding: P0(blocker) / P1(should fix) / P2(nice to have).

Check:
1. Visual consistency (colors, fonts, spacing, hover states)
2. Layout (QSplitter ratios, min sizes, resize behavior)
3. Drag-drop feedback (enter/leave/drop signals, style updates)
4. Status feedback (no progress bar during batch convert)
5. Signal/slot correctness (type matching, lambda issues, thread safety)
6. Cross-platform (font fallbacks, paths, macOS menus, HiDPI)
7. Accessibility (Tab order, keyboard shortcuts, focus indicators)
8. i18n completeness (any hardcoded strings?)
9. Error handling (IO errors, config load failures)
10. Performance (1000+ files in QListWidget, large text preview)

Output as markdown with severity labels. Be concise. Chinese. """

print("=== Calling Kimi K2.6 ===", flush=True)
result = call(prompt, 600)

if result:
    out = os.path.expanduser("~/.hermes/cron/output/kimi-k26-ui-review-result.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump({"review": result}, f, indent=2, ensure_ascii=False)
    print(f"Saved: {out}", flush=True)
    print("\n" + "="*50, flush=True)
    print(result, flush=True)
    print("="*50, flush=True)
else:
    print("FAILED - no result", flush=True)

print("DONE", flush=True)
