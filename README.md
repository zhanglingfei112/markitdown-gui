# MarkItDown GUI

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/UI-PySide6-green.svg)](https://pypi.org/project/PySide6/)
[![GitHub release](https://img.shields.io/github/v/release/zhanglingfei112/markitdown-gui)](https://github.com/zhanglingfei112/markitdown-gui/releases)
[![GitHub stars](https://img.shields.io/github/stars/zhanglingfei112/markitdown-gui)](https://github.com/zhanglingfei112/markitdown-gui)

> 🇨🇳 [中文](./README.zh-CN.md) | 🇬🇧 English

**MarkItDown GUI** is a desktop graphical client for Microsoft's official [`markitdown`](https://github.com/microsoft/markitdown) engine. It transforms complex command-line conversion operations into a simple drag-and-drop interface, allowing you to quickly convert various document formats into high-quality Markdown.

## ✨ Features

- **📄 Multi-format Support** — PDF, DOCX, XLSX, PPTX, HTML, CSV, JSON, XML, EPUB, images, audio, and more (20+ formats)
- **🎯 Drag-and-Drop** — Drag files directly into the interface; no commands needed
- **⚡ Batch Processing** — Import entire folders; convert hundreds of files at once
- **👁️ Real-time Preview** — Built-in dark-theme Markdown preview panel
- **🌐 Bilingual Interface** — Seamless switch between Chinese and English
- **💾 Flexible Export** — Save as `.md` files or batch export to directory
- **🧵 Non-blocking** — Background thread conversion keeps UI responsive
- **🔧 Configurable** — Custom output directory, interface language, and optional LLM API for image/audio enhancement

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- `pip` or `uv` package manager

### Installation

```bash
# Clone the repository
git clone https://github.com/zhanglingfei112/markitdown-gui.git
cd markitdown-gui

# Install dependencies (using uv — recommended)
uv pip install .

# Or using pip
pip install .
```

### Usage

```bash
# Launch the application
python -m markitdown_gui.main
```

1. **Import files** — Drag and drop files into the left panel, or use `File > Open File/Folder`
2. **Convert** — Click "Start Conversion"; files are processed in background threads
3. **Preview** — Click completed items in the list to see Markdown output
4. **Export** — Click "Export" to save `.md` files to your output directory

## 🖼️ Screenshots

> *Screenshots coming soon — contributions welcome!*

## ⚙️ Configuration

| Setting | Description |
|---|---|
| **Language** | Switch between 中文/English via `Settings > Language` menu |
| **Output Directory** | Default save location for converted `.md` files |
| **OCR/LLM Enhancement** | Enable AI-powered image and audio conversion (requires API key) |

## 📁 Project Structure

```
markitdown-gui/
├── markitdown_gui/
│   ├── main.py           # Application entry point
│   ├── app/
│   │   ├── main_window.py  # Main window UI and logic
│   │   ├── settings.py     # Configuration management
│   │   └── worker.py       # Background conversion thread
│   ├── ui/
│   │   ├── drop_area.py    # Drag-and-drop zone
│   │   ├── file_list.py    # File list widget
│   │   ├── preview.py      # Markdown preview panel
│   │   └── settings_dialog.py  # Settings dialog
│   ├── utils/
│   │   └── converter.py    # MarkItDown engine wrapper
│   └── i18n/               # Internationalization files
├── resources/styles/       # QSS stylesheets
├── tests/                  # Unit tests
└── pyproject.toml          # Project metadata
```

## 🧪 Running Tests

```bash
python -m unittest tests.test_converter -v
```

## 🤝 Contributing

Contributions are welcome! Feel free to open [issues](https://github.com/zhanglingfei112/markitdown-gui/issues) or submit pull requests.

## 📄 License

This project is licensed under the [MIT License](./LICENSE).
