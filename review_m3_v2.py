#!/usr/bin/env python3 -u
"""minimax-m3 代码审查 v2 — 精简 prompt"""
import json, os, sys, time, urllib.request, urllib.error
sys.stdout.reconfigure(line_buffering=True)

BASE = "https://opencode.ai/zen/go/v1"
api_key = ""
with open(os.path.expanduser("~/.hermes/.env")) as f:
    for line in f:
        l = line.strip()
        if "OPENCODE_GO_API_KEY" in l and not l.startswith("#"):
            parts = l.split("=", 1)
            if len(parts) > 1:
                val = parts[1].strip()
                if len(val) > 10 and not val.startswith("#"):
                    api_key = val; break

def call(prompt, timeout=300):
    body = json.dumps({"model":"minimax-m3","messages":[{"role":"user","content":prompt}],"max_tokens":8192}).encode()
    req = urllib.request.Request(f"{BASE}/messages", data=body, headers={
        "x-api-key": api_key, "anthropic-version":"2023-06-01", "Content-Type":"application/json", "User-Agent":"Mozilla/5.0"
    }, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return {"ok": True, "data": json.loads(r.read().decode())}
    except urllib.error.HTTPError as e:
        return {"ok": False, "code": e.code, "body": e.read().decode()[:400]}
    except Exception as ex:
        return {"ok": False, "error": str(ex)}

def prompt_and_print(name, prompt, timeout=300):
    print(f"  [{name}] 发送...", end=" ", flush=True)
    t0 = time.time()
    r = call(prompt, timeout)
    t = time.time() - t0
    if r["ok"]:
        texts = [b["text"] for b in r["data"]["content"] if b["type"]=="text"]
        thinks = [b["thinking"] for b in r["data"]["content"] if b["type"]=="thinking"]
        text = "\n".join(texts)
        usage = r["data"].get("usage", {})
        print(f"✅ {t:.1f}s | {len(text)}字 | reasoning={'有' if thinks else '无'}", flush=True)
        print(f"  {'─'*40}", flush=True)
        print(text[:2500], flush=True)
        if len(text) > 2500: print(f"\n  ...(共{len(text)}字)", flush=True)
        return text, usage, True
    else:
        print(f"❌ {r['code']} {t:.1f}s | {r.get('body','')[:150]}", flush=True)
        return str(r), {}, False
    time.sleep(2)

results = {}

# 1. 基础知识
print("\n=== 1. 基础知识 ===", flush=True)
r, u, _ = prompt_and_print("transformer", "简述Transformer的核心创新是什么？请用3-5句话回答。", 60)
results["基础·知识"] = r[:500]

# 2. 逻辑推理
print("\n=== 2. 逻辑推理 ===", flush=True)
r, u, _ = prompt_and_print("逻辑", "鸡兔同笼问题：35个头，94只脚，鸡和兔各几只？写出完整解题步骤。", 120)
results["逻辑·推理"] = r[:500]

# 3. 代码审查（精简版）
print("\n=== 3. 代码审查 ===", flush=True)
review_prompt = """审查这个PySide6桌面项目(约930行,14文件,MarkItDown转换工具)：

架构：
- main.py: 入口,加载QSS→启动MainWindow
- main_window.py(315行): 主窗口,含菜单栏(File/Settings/Language)、QSplitter左右分割、文件拖拽区、文件列表(QListWidget)、4个按钮(转换/导出/删除/清空)、预览区(QTextEdit)、状态栏。转换通过QThread后台执行。支持中/英语言切换。导出支持YesToAll/NoToAll覆盖选择。
- worker.py(52行): QThread,遍历文件列表→调用MarkItDownConverter→信号通知UI
- converter.py(36行): 封装MarkItDown库,支持pdf/docx/pptx/xlsx/csv/html/json等格式
- settings.py(88行): 单例模式,JSON文件持久化~/.markitdown_gui_settings.json,含language/output_dir/ocr_enabled/llm_api_key字段
- drop_area.py(74行): 拖拽区QFrame,虚线边框+active高亮
- file_list.py(157行): 自定义行布局(文件名+大小+状态标签),状态: pending/completed/failed/processing
- preview.py(47行): QTextEdit只读预览
- settings_dialog.py(75行): QDialog,语言下拉/输出目录/OCR开关/API密钥密码框

请严格审查以下6个维度,每个维度列出1-3个具体问题(P0/P1/P2等级+代码位置+1句修复建议):
1. 安全性 2. 线程安全 3. 内存/性能 4. 用户体验 5. 国际化 6. 异常处理"""

r, u, ok = prompt_and_print("代码审查", review_prompt, 300)
results["代码审查"] = r[:1000] if ok else f"失败: {r}"

# 4. 架构分析
print("\n=== 4. 架构分析 ===", flush=True)
arch_prompt = """分析PySide6桌面应用的架构(930行,MVC分层,QThread后台,JSON i18n,外部QSS):

当前架构：
- app/层: main_window, worker, settings — 业务逻辑
- ui/层: drop_area, file_list, preview, settings_dialog — 界面组件
- utils/: converter — 工具

请分析：
1. MVC分层是否合理？MainWindow(315行)是否过重？
2. 未来要加插件系统(扩展文件格式支持),架构需如何改？
3. 批量转换(1000+文件)时,性能瓶颈在哪？怎么优化？
4. 类级单例Settings有无问题？更好的替代方案？
5. 项目扩到5000+行时,哪些模块会成瓶颈？

每项1-2句话,给建议。"""

r, u, ok = prompt_and_print("架构分析", arch_prompt, 300)
results["架构分析"] = r[:1000] if ok else f"失败: {r}"

# 保存
outpath = os.path.expanduser("~/.hermes/cron/output/minimax-m3-review-v2.json")
os.makedirs(os.path.dirname(outpath), exist_ok=True)
with open(outpath, "w") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
print(f"\n✅ 结果保存: {outpath}", flush=True)
print("\n=== 全部完成 ===", flush=True)
