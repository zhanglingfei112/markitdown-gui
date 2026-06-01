# MarkItDown GUI

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/UI-PySide6-green.svg)](https:// 슬라이드.org/)

MarkItDown GUI 是微软官方 `markitdown` 引擎的本地图形化客户端。它将复杂的命令行转换操作转化为简单直观的拖拽式界面，让您可以快速将各种文档格式（PDF, DOCX, XLSX, PPTX, HTML, JSON, XML, EPUB 等）转换为高质量的 Markdown 格式。

## ✨ 功能特性

- **多格式支持**：完整继承微软 MarkItDown 的所有支持格式。
- **拖拽转换**：支持单个或多个文件直接拖入界面进行转换。
- **实时预览**：内置 Markdown 渲染预览区，支持暗色主题，转换后立即查看。
- **批量处理**：支持文件夹导入，可快速处理大量文档。
- **双语界面**：完整支持 中文 和 English 切换。
- **灵活导出**：支持保存为 `.md` 文件、复制到剪贴板或批量导出。
- **配置管理**：可自定义输出路径、界面语言及 LLM API 配置（用于图片/音频转换）。

## 🚀 快速安装

### 前置条件
- Python 3.10 或更高版本
- 已安装 `markitdown` 和 `PySide6`

### 安装步骤
```bash
# 克隆项目
git clone https://github.com/your-username/markitdown-gui.git
cd markitdown-gui

# 使用 uv 安装依赖 (推荐)
uv pip install .
```

## 🛠️ 使用说明

1. **启动应用**：运行 `python src/main.py`。
2. **导入文件**：将文件拖入左侧区域，或点击“添加文件”按钮。
3. **执行转换**：点击“开始转换”按钮，程序将在后台线程处理，不卡顿界面。
4. **预览结果**：在文件列表中点击已完成的文件，右侧预览区将显示转换后的 Markdown 内容。
5. **导出内容**：点击“导出”按钮将结果保存到本地。

## ⚙️ 设置项

- **界面语言**：在菜单栏【设置】->【语言】中切换。
- **输出目录**：定义转换后文件的默认保存位置。
- **OCR/LLM 增强**：在设置对话框中配置 API Key 以启用图片和音频的 AI 转换能力。

## ❓ 常见问题

**Q: 转换速度慢怎么办？**
A: 转换速度取决于文件大小和复杂度。对于大文件，请耐心等待后台线程完成处理。

**Q: 为什么某些图片无法转换？**
A: 图片转换需要配置 LLM API Key。请在【设置】中开启并配置相关 API。

## 📄 许可证
本项目采用 [MIT License](./LICENSE) 协议。
