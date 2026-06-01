from PySide6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QCheckBox, QComboBox, QPushButton, QDialogButtonBox, QLabel
from markitdown_gui.app.settings import Settings

class SettingsDialog(QDialog):
    """
    设置对话框
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Preferences")
        self.resize(400, 300)
        self.init_ui()
        self.update_text()

    def init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        # 界面语言
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["zh_CN", "en_US"])
        self.lang_combo.setCurrentText(Settings.get("language", "zh_CN"))
        
        # 输出目录
        self.output_edit = QLineEdit()
        self.output_edit.setText(Settings.get("output_dir", ""))
        
        # OCR 增强
        self.ocr_check = QCheckBox()
        self.ocr_check.setChecked(Settings.get("ocr_enabled", False))
        
        # API Key
        self.api_edit = QLineEdit()
        self.api_edit.setEchoMode(QLineEdit.Password)
        self.api_edit.setText(Settings.get("llm_api_key", ""))
        
        self.label_lang = QLabel("Language:")
        self.label_output = QLabel("Output Directory:")
        self.label_api = QLabel("LLM API Key:")
        
        form.addRow(self.label_lang, self.lang_combo)
        form.addRow(self.label_output, self.output_edit)
        form.addRow(self.ocr_check)
        form.addRow(self.label_api, self.api_edit)
        
        layout.addLayout(form)
        
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept_settings)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

    def update_text(self):
        """
        更新设置对话框的国际化文本
        """
        texts = Settings.get_translations(Settings.get("language", "zh_CN"))
        self.setWindowTitle(texts.get("pref_title", "Preferences"))
        self.label_lang.setText(texts.get("label_lang", "Language:"))
        self.label_output.setText(texts.get("label_output_dir", "Output Directory:"))
        self.ocr_check.setText(texts.get("label_ocr", "Enable OCR / LLM Enhancement"))
        self.label_api.setText(texts.get("label_api_key", "LLM API Key:"))
        self.buttons.button(QDialogButtonBox.Ok).setText(texts.get("btn_ok", "OK"))
        self.buttons.button(QDialogButtonBox.Cancel).setText(texts.get("btn_cancel", "Cancel"))

    def accept_settings(self):
        """
        保存设置
        """
        Settings.set("language", self.lang_combo.currentText())
        Settings.set("output_dir", self.output_edit.text())
        Settings.set("ocr_enabled", self.ocr_check.isChecked())
        Settings.set("llm_api_key", self.api_edit.text())
        Settings.save()
        self.accept()
