import json
import os
from pathlib import Path

class Settings:
    """
    配置管理类，负责读取、保存和提供全局配置
    """
    CONFIG_FILE = os.path.expanduser("~/.markitdown_gui_settings.json")

    _data = {
        "language": "zh_CN",
        "output_dir": "",
        "ocr_enabled": False,
        "llm_api_key": ""
    }

    @classmethod
    def load(cls):
        """
        从本地文件加载配置
        """
        if os.path.exists(cls.CONFIG_FILE):
            try:
                with open(cls.CONFIG_FILE, "r", encoding="utf-8") as f:
                    cls._data.update(json.load(f))
            except Exception as e:
                print(f"Error loading settings from {cls.CONFIG_FILE}: {e}")

    @classmethod
    def save(cls):
        """
        将当前配置保存到本地文件
        """
        try:
            with open(cls.CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(cls._data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving settings: {e}")

    @classmethod
    def get(cls, key, default=None):
        """
        获取配置值
        """
        return cls._data.get(key, default)

    @classmethod
    def set(cls, key, value):
        """
        设置配置值并保存
        """
        cls._data[key] = value
        cls.save()

    @classmethod
    def get_all(cls):
        """
        获取所有配置副本
        """
        return cls._data.copy()

    @classmethod
    def get_translations(cls, lang_code):
        """
        根据语言代码加载对应的翻译文件
        使用 pathlib 获取包路径，兼容开发环境和打包环境
        """
        # 使用 pathlib 定位 i18n 目录 (settings.py → app/ → markitdown_gui/ → i18n/)
        base_dir = Path(__file__).resolve().parent.parent / "i18n"

        def _load(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading translations from {path}: {e}")
                return {}

        result = _load(base_dir / f"{lang_code}.json")
        if result:
            return result

        # Fallback to en_US
        fallback = _load(base_dir / "en_US.json")
        return fallback if fallback else {}
