# MarkItDown GUI

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/UI-PySide6-green.svg)](https://슬라이드.org/)

MarkItDown GUI is a local graphical client for Microsoft's official `markitdown` engine. It transforms complex command-line conversion operations into a simple and intuitive drag-and-drop interface, allowing you to quickly convert various document formats (PDF, DOCX, XLSX, PPTX, HTML, JSON, XML, EPUB, etc.) into high-quality Markdown.

## ✨ Features

- **Multi-format Support**: Fully inherits all supported formats of Microsoft MarkItDown.
- **Drag-and-Drop**: Supports dragging single or multiple files directly into the interface.
- **Real-time Preview**: Built-in Markdown rendering preview area with dark theme.
- **Batch Processing**: Supports folder import for fast processing of large numbers of documents.
- **Bilingual Interface**: Full support for switching between 中文 (Chinese) and English.
- **Flexible Export**: Save as `.md` files, copy to clipboard, or batch export.
- **Configuration Management**: Customize output paths, interface language, and LLM API configuration (for image/audio conversion).

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or higher
- `markitdown` and `PySide6` installed

### Installation Steps
```bash
# Clone the project
git clone https://github.com/your-username/markitdown-gui.git
cd markitdown-gui

# Install dependencies using uv (recommended)
uv pip install .
```

## 🛠️ Usage

1. **Launch App**: Run `python src/main.py`.
2. **Import Files**: Drag files into the left area or click the "Add Files" button.
3. **Convert**: Click "Start Conversion". The program will process in a background thread without freezing the UI.
4. **Preview**: Click a completed file in the list to view the converted Markdown content in the right preview area.
5. **Export**: Click the "Export" button to save results locally.

## ⚙️ Settings

- **Interface Language**: Switch in Menu -> [Settings] -> [Language].
- **Output Directory**: Define the default save location for converted files.
- **OCR/LLM Enhancement**: Configure API Key in the settings dialog to enable AI conversion for images and audio.

## ❓ FAQ

**Q: Why is the conversion slow?**
A: Speed depends on file size and complexity. For large files, please wait for the background thread to finish.

**Q: Why are some images not converting?**
A: Image conversion requires an LLM API Key. Please enable and configure it in [Settings].

## 📄 License
This project is licensed under the [MIT License](./LICENSE).
