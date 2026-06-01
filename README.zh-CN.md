# MarkItDown GUI

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/UI-PySide6-green.svg)](https://pypi.org/project/PySide6/)
[![GitHub release](https://img.shields.io/github/v/release/zhanglingfei112/markitdown-gui)](https://github.com/zhanglingfei112/markitdown-gui/releases)
[![GitHub stars](https://img.shields.io/github/stars/zhanglingfei112/markitdown-gui)](https://github.com/zhanglingfei112/markitdown-gui)

> 🇨🇳 中文 | [🇬🇧 English](./README.en.md)

**MarkItDown GUI** 是微软官方 [`markitdown`](https://github.com/microsoft/markitdown) 引擎的本地图形化客户端。它将复杂的命令行操作转化为简单直观的拖拽式界面，让您可以快速将各种文档格式转换为高质量的 Markdown。

## ✨ 功能特性

- **📄 多格式支持** — PDF、DOCX、XLSX、PPTX、HTML、CSV、JSON、XML、EPUB、图片、音频等 20+ 种格式
- **🎯 拖拽转换** — 直接将文件拖入界面，无需输入任何命令
- **⚡ 批量处理** — 支持导入整个文件夹，一次性批量转换
- **👁️ 实时预览** — 内置暗色主题 Markdown 预览面板
- **🌐 双语界面** — 中文/English 即时切换
- **💾 灵活导出** — 保存为 `.md` 文件或批量导出到指定目录
- **🧵 后台转换** — 后台线程处理，界面不卡顿
- **🔧 可配置** — 自定义输出目录、界面语言、可选的 LLM API（用于图片/音频增强）

## 🚀 快速开始

### 前置条件

- Python 3.10 或更高版本
- `pip` 或 `uv` 包管理器

### 安装步骤

```bash
# 克隆项目
git clone https://github.com/zhanglingfei112/markitdown-gui.git
cd markitdown-gui

# 使用 uv 安装依赖 (推荐)
uv pip install .

# 或使用 pip
pip install .
```

### 使用方式

```bash
# 启动应用
python -m markitdown_gui.main
```

1. **导入文件** — 将文件拖入左侧面板，或通过 `文件 > 打开文件/文件夹`
2. **执行转换** — 点击"开始转换"，后台线程处理，界面不卡顿
3. **预览结果** — 点击列表中的已完成文件，右侧查看 Markdown 内容
4. **导出文件** — 点击"导出"将转换结果保存到本地

## 🖼️ 界面截图

> *截图待补充 — 欢迎贡献！*

## ⚙️ 设置项

| 设置 | 说明 |
|---|---|
| **界面语言** | 通过 `设置 > 语言` 菜单在中文/English 间切换 |
| **输出目录** | 转换后 `.md` 文件的默认保存位置 |
| **OCR/LLM 增强** | 启用 AI 图片和音频转换（需配置 API Key） |

## 📁 项目结构

```
markitdown-gui/
├── markitdown_gui/
│   ├── main.py               # 应用程序入口
│   ├── app/
│   │   ├── main_window.py    # 主窗口 UI 与逻辑
│   │   ├── settings.py       # 配置管理
│   │   └── worker.py         # 后台转换线程
│   ├── ui/
│   │   ├── drop_area.py      # 拖拽放置区域
│   │   ├── file_list.py      # 文件列表组件
│   │   ├── preview.py        # Markdown 预览面板
│   │   └── settings_dialog.py # 设置对话框
│   ├── utils/
│   │   └── converter.py      # MarkItDown 引擎封装
│   └── i18n/                 # 国际化语言包
├── resources/styles/         # QSS 样式表
├── tests/                    # 单元测试
└── pyproject.toml            # 项目元数据
```

## 🧪 运行测试

```bash
python -m unittest tests.test_converter -v
```

## 🤝 贡献指南

欢迎贡献代码和提交 [Issue](https://github.com/zhanglingfei112/markitdown-gui/issues)！

## 📄 许可证

本项目采用 [MIT License](./LICENSE) 协议。
