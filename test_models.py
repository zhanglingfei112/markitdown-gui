#!/usr/bin/env python3
"""
全面测试 OpenCode Go 上的三个模型：
1. kimi-k2.6       → chat_completions (Bearer + UA)
2. minimax-m3      → chat_completions (Bearer + UA)  
3. qwen3.7-max     → messages / Anthropic 格式 (x-api-key)
"""
import json, os, sys, time, traceback
import urllib.request
import urllib.error

# ── 配置 ──────────────────────────────────────────────
BASE = "https://opencode.ai/zen/go/v1"

# 从 .env 读 key
env_path = os.path.expanduser("~/.hermes/.env")
api_key = None
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if line.startswith("OPENCODE_GO_API_KEY="):
            api_key = line.split("=", 1)[1].strip()
            break

if not api_key or api_key.startswith("#"):
    print("FATAL: OPENCODE_GO_API_KEY not found in .env")
    sys.exit(1)

print(f"API Key found (len={len(api_key)})")

# ── 调用函数 ──────────────────────────────────────────

def call_chat_completions(model, messages, max_tokens=4096):
    """标准 OpenAI chat_completions 格式 (kimi-k2.6, minimax-m3)"""
    data = json.dumps({
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.3
    }).encode()
    req = urllib.request.Request(
        f"{BASE}/chat/completions",
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = json.loads(resp.read().decode())
        return {"ok": True, "data": body}
    except urllib.error.HTTPError as e:
        detail = e.read().decode()
        return {"ok": False, "status": e.code, "detail": detail[:500]}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def call_messages(model, messages, max_tokens=8192):
    """Anthropic messages 格式 (qwen3.7-max)"""
    # 转换 OpenAI messages → Anthropic 格式
    system_msg = None
    msgs = []
    for m in messages:
        if m["role"] == "system":
            system_msg = m["content"]
        else:
            msgs.append({"role": m["role"], "content": m["content"]})
    
    body = {
        "model": model,
        "messages": msgs,
        "max_tokens": max_tokens,
    }
    if system_msg:
        body["system"] = system_msg
    
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        f"{BASE}/messages",
        data=data,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = json.loads(resp.read().decode())
        return {"ok": True, "data": body}
    except urllib.error.HTTPError as e:
        detail = e.read().decode()
        print(f"  [HTTP {e.code}] {detail[:300]}")
        return {"ok": False, "status": e.code, "detail": detail[:500]}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def get_content_chat(resp):
    """从 chat_completions 响应中提取文本"""
    if not resp.get("ok"):
        return f"[ERROR] {resp.get('status', '?')} {resp.get('detail', resp.get('error', 'unknown'))}"
    try:
        return resp["data"]["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        return f"[PARSE ERROR] {e} | raw: {json.dumps(resp['data'], ensure_ascii=False)[:300]}"


def get_content_messages(resp):
    """从 messages / Anthropic 响应中提取文本"""
    if not resp.get("ok"):
        return f"[ERROR] {resp.get('status', '?')} {resp.get('detail', resp.get('error', 'unknown'))}"
    try:
        blocks = resp["data"]["content"]
        texts = []
        for b in blocks:
            if b["type"] == "text":
                texts.append(b["text"])
            elif b["type"] == "thinking":
                texts.append(f"[thinking: {b['thinking'][:200]}...]")
        return "\n".join(texts)
    except (KeyError, IndexError) as e:
        return f"[PARSE ERROR] {e} | raw: {json.dumps(resp['data'], ensure_ascii=False)[:300]}"


def get_usage_chat(resp):
    if not resp.get("ok"):
        return {}
    try:
        u = resp["data"].get("usage", {})
        if isinstance(u, dict):
            return {
                "prompt": u.get("prompt_tokens", "?"),
                "completion": u.get("completion_tokens", "?"),
                "total": u.get("total_tokens", "?")
            }
    except Exception:
        pass
    return {}


def get_usage_messages(resp):
    if not resp.get("ok"):
        return {}
    try:
        u = resp["data"].get("usage", {})
        return {
            "input": u.get("input_tokens", "?"),
            "output": u.get("output_tokens", "?"),
        }
    except Exception:
        return {}


# ── 测试用例 ──────────────────────────────────────────

PROJECT_FILES = {
    "main.py": "42 lines, 应用入口。加载QSS样式→初始化Settings→创建MainWindow→exec",
    "main_window.py": "315 lines, 主窗口UI：菜单栏/分割布局/拖拽区/文件列表/预览区/按钮/状态栏。菜单有File/ Language/ Settings。支持语言切换(zh_CN/en_US)。转换按钮→QThread后台执行。",
    "worker.py": "52 lines, QThread后台线程，遍历文件调用converter.convert()，通过信号progress/finished通知UI。",
    "converter.py": "36 lines, MarkItDown库封装，convert(file_path)→result.text_content",
    "settings.py": "88 lines, 类级单例(Settings)，json文件持久化(~/.markitdown_gui_settings.json)，包含language/output_dir/ocr_enabled/llm_api_key，get_translations()加载i18n JSON。",
    "drop_area.py": "74 lines, drag/drop区域，QFrame虚线边框+active高亮。filesDropped信号。",
    "file_list.py": "157 lines, QListWidget自定义行布局(文件名+大小+状态标签)，status有pending/completed/failed/processing四种状态。",
    "preview.py": "47 lines, QTextEdit只读预览，黑色主题。",
    "settings_dialog.py": "75 lines, QDialog，表单含Language下拉/输出目录输入/OCR开关/API Key密码框。",
}

PROJECT_SUMMARY = (
    "这是一个PySide6桌面应用MarkItDown GUI，共~930行代码，14个文件。"
    "功能：文件拖拽/选择→MarkItDown引擎转换→Markdown预览→导出。"
    "架构：MVC分层(app/ui/utils)，i18n通过JSON语言包(zh_CN/en_US)实现，"
    "QThread后台转换防阻塞，style.qss外部化暗色主题。"
    "支持格式：pdf,docx,pptx,xlsx,csv,html,json,xml,epub,zip,md,txt,jpg,png等。"
)

def make_tests():
    """构建测试提示词列表"""
    tests = []
    
    # ── 维度1：基础能力 ──
    tests.append(("【基础能力】Transformer核心创新简述", "knowledge_transformer"))
    tests.append(("【基础能力】将以下英文翻译为中文：'The transformer architecture revolutionized NLP by introducing self-attention mechanisms that enable parallel processing of sequence data, overcoming the sequential limitations of RNNs.'", "knowledge_translate"))
    
    # ── 维度2：逻辑推理 ──
    tests.append(("【逻辑推理】如果A比B高，B比C高，C比D高，问A比D高吗？请给出推理过程。", "logic_deduction"))
    tests.append(("【逻辑推理】一个笼子里有鸡和兔子，共35个头，94只脚，问鸡和兔子各有多少只？请给出解题步骤。", "logic_math"))
    
    # ── 维度3：代码审查 ──
    code_review_prompt = f"""【代码审查】审查以下PySide6项目的代码安全性和潜在问题。

项目概况：{PROJECT_SUMMARY}

关键代码文件简述：
{chr(10).join(f'  - {k}: {v}' for k, v in PROJECT_FILES.items())}

请审查以下方面：
1. 安全性：settings中存储API Key是否有风险？如何改进？
2. 线程安全：QThread使用有无竞态条件隐患？
3. 内存/性能：大文件批量转换时的内存管理
4. 用户体验：有那些明显不完善的地方
5. 国际化：i18n实现是否完整？
6. 异常处理：那地方异常捕获不足？

每个问题给出：严重等级(P0/P1/P2) + 具体问题 + 修复建议"""
    tests.append((code_review_prompt, "code_review"))
    
    # ── 维度4：复杂架构分析 ──
    arch_prompt = f"""【架构分析】深入分析这个PySide6项目的架构和设计：

{PROJECT_SUMMARY}

请分析：
1. MVC分层是否合理？MainWindow是否承担了过多责任？
2. 如果未来要支持插件系统（扩展MarkItDown不支持的文件格式），当前架构需要如何改造？
3. 如果未来要支持增量转换/缓存/断点续传，需要怎么设计？
4. 当前Settings使用类级单例，是否有更好的替代方案？
5. 如果项目变大到100+文件，当前哪些模块会成为瓶颈？

给出改进优先级和实施路径。"""
    tests.append((arch_prompt, "architecture_review"))
    
    return tests


# ── 主测试逻辑 ────────────────────────────────────────

def run_test(model, model_type, tests, label):
    """测试一个模型所有维度"""
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"  模型: {model}")
    print(f"{'='*60}")
    
    results = {}
    token_stats = {}
    
    for prompt, test_id in tests:
        print(f"\n  ── [{test_id}] ──")
        print(f"  发送请求... ", end="", flush=True)
        start = time.time()
        
        if model_type == "messages":
            msgs = [{"role": "user", "content": prompt}]
            resp = call_messages(model, msgs)
            content = get_content_messages(resp)
            usage = get_usage_messages(resp)
        else:
            msgs = [{"role": "user", "content": prompt}]
            resp = call_chat_completions(model, msgs)
            content = get_content_chat(resp)
            usage = get_usage_chat(resp)
        
        elapsed = time.time() - start
        token_stats[test_id] = usage
        
        if resp.get("ok"):
            # 输出摘要
            lines = content.strip().split("\n")
            summary = content[:500] + ("..." if len(content) > 500 else "")
            print(f"✓ {elapsed:.1f}s | tokens: {usage}")
            print(f"  首行: {lines[0][:100] if lines else '(empty)'}")
            print(f"  长度: {len(content)} chars")
        else:
            print(f"✗ FAIL | {elapsed:.1f}s")
            summary = content
        
        results[test_id] = {
            "content": content,
            "elapsed": round(elapsed, 1),
            "usage": usage,
            "success": resp.get("ok", False),
            "summary": summary
        }
        
        # 节流——等2秒避免 RPM 超限
        time.sleep(2)
    
    return results, token_stats


def print_summary_table(all_results):
    """打印汇总对比表"""
    print(f"\n\n{'='*60}")
    print(f"  模型测试汇总对比")
    print(f"{'='*60}")
    
    categories = {
        "knowledge_transformer": "基础知识",
        "knowledge_translate": "翻译能力",
        "logic_deduction": "逻辑推理(三段论)",
        "logic_math": "逻辑推理(数学)",
        "code_review": "代码审查",
        "architecture_review": "架构分析",
    }
    
    # 按测试维度打出对比
    for test_id, cat_name in categories.items():
        print(f"\n  【{cat_name}】")
        for model_name, (results, _) in all_results.items():
            if test_id in results:
                r = results[test_id]
                status = "✓" if r["success"] else "✗"
                elapsed = r["elapsed"]
                length = len(r["content"]) if r["content"] else 0
                usage = r.get("usage", {})
                usage_str = str(usage) if usage else "-"
                print(f"    {status} {model_name:30s} {elapsed:5.1f}s  {length:5d}chars  tokens={usage_str}")


def print_detail(all_results):
    """打印每个模型的详细输出"""
    for model_name, (results, tokens) in all_results.items():
        print(f"\n\n{'#'*70}")
        print(f"#  {model_name}")
        print(f"{'#'*70}")
        for test_id, r in results.items():
            print(f"\n{'─'*60}")
            print(f"  [{test_id}]  {'✓' if r['success'] else '✗'}  {r['elapsed']}s  tokens={r['usage']}")
            print(f"{'─'*60}")
            if r["success"]:
                # 输出前2000字符
                content = r["content"]
                print(content[:2500])
                if len(content) > 2500:
                    print(f"\n... (truncated, total {len(content)} chars)")
            else:
                print(r["content"])


# ── 执行 ──────────────────────────────────────────────

if __name__ == "__main__":
    tests = make_tests()
    all_results = {}
    
    # 1. kimi-k2.6
    print("\n>>> 开始测试 kimi-k2.6 ...")
    try:
        r, t = run_test("kimi-k2.6", "chat", tests, "🧪 MiniMax M3 对比 — Kimi K2.6")
        all_results["kimi-k2.6"] = (r, t)
    except Exception as e:
        print(f"  kimi-k2.6 FAILED: {e}")
        traceback.print_exc()
    
    # 2. minimax-m3
    print("\n>>> 开始测试 minimax-m3 ...")
    try:
        r, t = run_test("minimax-m3", "chat", tests, "🧪 MiniMax M3")
        all_results["minimax-m3"] = (r, t)
    except Exception as e:
        print(f"  minimax-m3 FAILED: {e}")
        traceback.print_exc()
    
    # 3. qwen3.7-max (Anthropic messages endpoint)
    print("\n>>> 开始测试 qwen3.7-max ...")
    try:
        r, t = run_test("qwen3.7-max", "messages", tests, "🧪 Qwen3.7-Max (深度审查)")
        all_results["qwen3.7-max"] = (r, t)
    except Exception as e:
        print(f"  qwen3.7-max FAILED: {e}")
        traceback.print_exc()
    
    # 输出汇总
    print_summary_table(all_results)
    
    # 保存详细结果到文件
    output_path = os.path.expanduser("~/.hermes/cron/output/model_test_results.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # 仅保存摘要
    summary_data = {}
    for model_name, (results, _) in all_results.items():
        summary_data[model_name] = {}
        for test_id, r in results.items():
            summary_data[model_name][test_id] = {
                "success": r["success"],
                "elapsed": r["elapsed"],
                "length": len(r.get("content", "")),
                "usage": r.get("usage", {}),
                "first_line": r.get("content", "").strip().split("\n")[0][:200] if r.get("content") else "",
            }
    
    with open(output_path, "w") as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n\n汇总已保存到: {output_path}")
    
    # 详细输出
    print_detail(all_results)
