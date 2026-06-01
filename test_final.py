#!/usr/bin/env python3 -u
"""最终全面测试：正确调用方式"""
import json, os, sys, time
import urllib.request, urllib.error
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
print(f"key len={len(api_key)}", flush=True)

def http(url, data, headers, timeout=180):
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return {"ok": True, "data": json.loads(r.read().decode()), "code": r.status}
    except urllib.error.HTTPError as e:
        return {"ok": False, "code": e.code, "body": e.read().decode()[:500]}
    except Exception as ex:
        return {"ok": False, "error": str(ex)}

def call_minimax(prompt, timeout=180):
    data = json.dumps({"model":"minimax-m3","messages":[{"role":"user","content":prompt}],"max_tokens":4096,"temperature":0.3}).encode()
    return http(f"{BASE}/chat/completions", data, {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}, timeout=timeout)

def call_qwen37(prompt, timeout=300):
    body = json.dumps({"model":"qwen3.7-max","messages":[{"role":"user","content":prompt}],"max_tokens":8192}).encode()
    return http(f"{BASE}/messages", body, {"x-api-key": api_key, "anthropic-version":"2023-06-01", "Content-Type":"application/json", "User-Agent":"Mozilla/5.0"}, timeout=timeout)

def ext_chat(resp):
    if not resp.get("ok"): return f"[ERR {resp.get('code','?')}]", {}
    try:
        c = resp["data"]["choices"][0]["message"]["content"]
        u = resp["data"].get("usage", {})
        return c, u
    except Exception as e: return f"[PARSE] {e}", {}

def ext_msg(resp):
    if not resp.get("ok"): return f"[ERR {resp.get('code','?')}]", {}
    try:
        texts = [b["text"] for b in resp["data"]["content"] if b["type"]=="text"]
        u = resp["data"].get("usage", {})
        return "\n".join(texts), u
    except Exception as e: return f"[PARSE] {e}", {}

def run_test(model, caller, ext, prompt, timeout=300):
    print(f"  [{model}] 发送...", end=" ", flush=True)
    t0 = time.time()
    resp = caller(prompt, timeout=timeout)
    content, usage = ext(resp)
    t = time.time() - t0
    ok = resp.get("ok", False)
    status = resp.get("code", "?")
    print(f"{'✓' if ok else '✗'} {status} {t:.1f}s | {len(content)} chars | usage={usage}", flush=True)
    if ok:
        lines = content.strip().split("\n")
        print(f"  首行: {lines[0][:150] if lines else '(empty)'}", flush=True)
    else:
        print(f"  错误: {str(content)[:200]}", flush=True)
    time.sleep(3)
    return {"content": content[:4000] if ok else str(content), "usage": usage, "time": round(t,1), "ok": ok}

TESTS = [
    ("基础知识", "简述Transformer的核心创新是什么？", 120),
    ("基础翻译", "翻译为中文：'The transformer architecture revolutionized NLP by introducing self-attention mechanisms.'", 120),
    ("逻辑推理", "如果A比B高，B比C高，C比D高，A比D高吗？推理过程。", 120),
    ("逻辑数学", "鸡兔同笼：35头94脚，各几只？解题步骤。", 120),
    ("任务代码审查", "审查这个PySide6应用：主窗口含菜单栏(File/Settings/Language)、文件拖拽区、文件列表、按钮(转换/导出/删除/清空)和预览区。审查: 1)安全性 2)线程安全 3)性能 4)用户体验 5)国际化 6)异常处理。每个问题标P0/P1/P2并给出具体位置。", 300),
    ("任务架构分析", "分析PySide6桌面应用：MVC分层(930行14文件)，i18n用JSON语言包，QThread后台转换，QSS外部主题。分析: 1)分层合理性 2)插件扩展 3)缓存设计 4)单例替代 5)扩展瓶颈。", 300),
]

print("\n" + "="*60)
print("  kimi-k2.6 (第一轮已通过，结果可用)")
print("  minimax-m3 (chat_completions)")
print("  qwen3.7-max (messages, Anthropic)")
print("="*60)

results = {}

print("\n>>> minimax-m3 via chat_completions", flush=True)
results["minimax-m3"] = {}
for tid, prompt, to in TESTS:
    r = run_test("minimax-m3", call_minimax, ext_chat, prompt, timeout=to)
    results["minimax-m3"][tid] = r

print("\n>>> qwen3.7-max via messages", flush=True)
results["qwen3.7-max"] = {}
for tid, prompt, to in TESTS:
    r = run_test("qwen3.7-max", call_qwen37, ext_msg, prompt, timeout=to)
    results["qwen3.7-max"][tid] = r

outpath = os.path.expanduser("~/.hermes/cron/output/model_evals_final.json")
os.makedirs(os.path.dirname(outpath), exist_ok=True)
with open(outpath, "w") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
print(f"\n结果保存: {outpath}", flush=True)

print("\n" + "="*60)
print("  模型对比汇总")
print("="*60)
for model in ["minimax-m3", "qwen3.7-max"]:
    print(f"\n  {model}:")
    for tid in [t[0] for t in TESTS]:
        r = results[model].get(tid, {})
        s = "✓" if r.get("ok") else "✗"
        t = r.get("time", 0)
        u = r.get("usage", {})
        print(f"    {s} {tid:20s} {t:>6.1f}s  usage={u}")

print("\n\n========== 详细输出 ==========", flush=True)
for model in ["minimax-m3", "qwen3.7-max"]:
    print(f"\n{'#'*60}")
    print(f"#  {model}")
    print(f"{'#'*60}", flush=True)
    for tid, r in results[model].items():
        s = "✓" if r.get("ok") else "✗"
        print(f"\n{'─'*50}")
        print(f"  {tid}  {s}  {r.get('time',0)}s  usage={r.get('usage','')}")
        print(f"{'─'*50}")
        c = r.get("content", "")
        print(c[:3000], flush=True)
        if len(c) > 3000:
            print(f"\n... (total {len(c)} chars)", flush=True)
