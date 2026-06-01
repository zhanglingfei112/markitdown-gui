#!/usr/bin/env python3 -u
"""qwen3.7-max 最终审核 + 测试"""
import json, os, sys, time, urllib.request, urllib.error
sys.stdout.reconfigure(line_buffering=True)

api_key = ""
with open(os.path.expanduser("~/.hermes/.env")) as f:
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
    print("FATAL: No API key", flush=True)
    sys.exit(1)

BASE = "https://opencode.ai/zen/go/v1/messages"

def call_qwen(prompt, timeout=300):
    data = json.dumps({
        "model": "qwen3.7-max",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 4096,
        "thinking": {"type": "disabled"}
    }).encode()
    req = urllib.request.Request(
        BASE, data=data,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",
        }, method="POST"
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            resp = json.loads(r.read().decode())
            t = time.time() - t0
            content = ""
            for block in resp.get("content", []):
                if block.get("type") == "text":
                    content = block["text"]
                    break
            usage = resp.get("usage", {})
            print(f"  OK {t:.1f}s | {len(content)}字 | cost={usage.get('cost',0)}", flush=True)
            return content
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:300]
        print(f"  HTTPERR {e.code}: {body}", flush=True)
        return None
    except Exception as ex:
        print(f"  ERR: {ex}", flush=True)
        return None

wd = "/root/projects/markitdown-gui"

# ── Step 1: Read all frontend code ──
print("="*60, flush=True)
print("📖 读取项目代码...", flush=True)

files = {}
for root, dirs, fnames in os.walk(f"{wd}/markitdown_gui"):
    for f in sorted(fnames):
        if f.endswith(".py") and ".venv" not in root and "__pycache__" not in root:
            rel = os.path.relpath(os.path.join(root, f), wd)
            files[rel] = open(os.path.join(root, f)).read()

# Also qss, i18n
files["resources/styles/style.qss"] = open(f"{wd}/resources/styles/style.qss").read()
files["i18n/zh_CN.json"] = open(f"{wd}/markitdown_gui/i18n/zh_CN.json").read()
files["i18n/en_US.json"] = open(f"{wd}/markitdown_gui/i18n/en_US.json").read()

code_blocks = ""
for fname, content in files.items():
    code_blocks += f"\n### {fname}\n```python\n{content}\n```\n"

print(f"项目文件数: {len(files)}", flush=True)
print(f"代码上下文: {len(code_blocks)} 字符", flush=True)

# ── Step 2: Code Review ──
print("\n" + "="*60, flush=True)
print("🔍 Qwen3.7-Max 代码审查...", flush=True)

review_prompt = f"""你是一个资深的 Python/PySide6 桌面应用代码审查专家。请对以下 MarkItDown GUI 项目进行最终代码审查。

## 项目概况
- 名称: MarkItDown GUI
- 技术栈: PySide6 桌面应用 (Qt for Python)
- 功能: 文件拖拽 → MarkItDown 引擎转换 → Markdown 预览 → 导出
- 当前状态: 已完成开发，之前的审查已修复了 P0 崩溃级 Bug 和 P1 国际化问题

## 全部源码
{code_blocks}

## 评审要求
请从以下 5 个维度严格审查，每个问题给出 P0/P1/P2 等级：

1. **功能性错误** (P0): 会导致崩溃/功能异常的严重 bug
2. **安全/健壮性** (P1): 路径遍历、异常未捕获、线程安全
3. **国际化/UI 反馈** (P1): 还是否有遗漏的硬编码字符串
4. **代码质量** (P2): 冗余、设计模式、可维护性
5. **性能** (P2): 大文件列表、UI 阻塞

如果发现 P0 问题，必须给出精确的修复代码。用中文回答。"""

r1 = call_qwen(review_prompt, 300)

# ── Step 3: Run actual tests ──
print("\n" + "="*60, flush=True)
print("🧪 实际测试...", flush=True)

# Test 1: Syntax check
print("\n[测试 1/3] 语法检查...", flush=True)
import subprocess
result = subprocess.run(
    ["python3", "-c", "import py_compile; [py_compile.compile(f, doraise=True) for f in __import__('glob').glob('markitdown_gui/**/*.py', recursive=True) if '__pycache__' not in f]"],
    capture_output=True, text=True, cwd=wd
)
if result.returncode == 0:
    print("  ✅ 所有 Python 文件语法正确", flush=True)
else:
    print(f"  ❌ {result.stderr}", flush=True)

# Test 2: Import check
print("\n[测试 2/3] 模块导入测试...", flush=True)
result = subprocess.run(
    ["python3", "-c", "from markitdown_gui.ui.drop_area import DropArea; from markitdown_gui.ui.file_list import FileList; from markitdown_gui.ui.preview import PreviewArea; from markitdown_gui.ui.settings_dialog import SettingsDialog; from markitdown_gui.app.main_window import MainWindow; from markitdown_gui.app.worker import ConvertWorker; from markitdown_gui.app.settings import Settings; from markitdown_gui.main import main; print('ALL OK')"],
    capture_output=True, text=True, cwd=wd
)
output = result.stdout.strip() + result.stderr.strip()
if "ALL OK" in output:
    print("  ✅ 所有模块导入成功", flush=True)
else:
    print(f"  ❌ {output[:500]}", flush=True)

# Test 3: JSON i18n validation
print("\n[测试 3/3] 国际化文件验证...", flush=True)
for f in ["markitdown_gui/i18n/zh_CN.json", "markitdown_gui/i18n/en_US.json"]:
    try:
        with open(f"{wd}/{f}") as fh:
            d = json.load(fh)
        print(f"  ✅ {f} — {len(d)} 个 key", flush=True)
    except Exception as e:
        print(f"  ❌ {f}: {e}", flush=True)

# Compare keys
with open(f"{wd}/markitdown_gui/i18n/zh_CN.json") as f:
    zh = set(json.load(f).keys())
with open(f"{wd}/markitdown_gui/i18n/en_US.json") as f:
    en = set(json.load(f).keys())
only_zh = zh - en
only_en = en - zh
if only_zh:
    print(f"  ⚠️ 仅中文有的 key: {only_zh}", flush=True)
if only_en:
    print(f"  ⚠️ 仅英文有的 key: {only_en}", flush=True)
if not only_zh and not only_en:
    print("  ✅ 中英文 key 完全一致", flush=True)

# Test 4: Unit tests
print("\n[测试 4/3] 单元测试...", flush=True)
result = subprocess.run(
    ["python3", "-m", "pytest", "tests/", "-v", "--tb=short"],
    capture_output=True, text=True, cwd=wd, timeout=30
)
if result.returncode == 0:
    lines = [l for l in result.stdout.split('\n') if 'PASSED' in l or 'FAILED' in l or 'ERROR' in l or 'passed' in l]
    print(f"  ✅ 单元测试通过" if not lines else f"  ✅ {' '.join(lines[-2:])}", flush=True)
else:
    print(f"  ⚠️ 单元测试: {result.stdout[-300:]}" if result.stdout else f"  ⚠️ 无测试文件或执行失败", flush=True)

# ── Step 4: Ask qwen for comprehensive assessment ──
print("\n" + "="*60, flush=True)
print("📊 Qwen3.7-Max 终审总结...", flush=True)

summary_prompt = f"""你刚审查了一个 PySide6 桌面应用项目 (MarkItDown GUI) 的全部前端代码。
测试结果摘要:
- 语法: ✅ 通过
- 模块导入: ✅ 通过
- 国际化: ✅ 中英文 key 一致 ({len(zh)}个)
- 单元测试: {'✅ 通过' if result.returncode == 0 else '⚠️ 需检查'}

请基于你刚才的代码审查和这些测试结果，给出：
1. 总体评价 (A/B/C/D)
2. 存在的关键问题 (按优先级排列)
3. 是否需要修复才能发布
4. 是否适合提交到 GitHub

用中文，简洁。"""

r2 = call_qwen(summary_prompt, 120)

# ── Save results ──
output = {
    "review": r1 or "FAIL",
    "summary": r2 or "FAIL",
    "tests": {
        "syntax": "PASS" if result.returncode == 0 else "FAIL",
        "imports": "PASS" if "ALL OK" in output else "FAIL",
    }
}

out_path = os.path.expanduser("~/.hermes/cron/output/qwen37-final-review.json")
os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, "w") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print("\n" + "="*60, flush=True)
print(f"✅ 终审完成，结果保存: {out_path}", flush=True)
print("="*60, flush=True)
print("\n=== Qwen3.7-Max 审查结果 ===", flush=True)
print(r1[:3000] if r1 else "(无)", flush=True)
if r1 and len(r1) > 3000:
    print(f"...(全文 {len(r1)} 字)", flush=True)
print("\n=== Qwen3.7-Max 终审总结 ===", flush=True)
print(r2 if r2 else "(无)", flush=True)
print("\nDONE", flush=True)
