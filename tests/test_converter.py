import unittest
import tempfile
import os
from markitdown_gui.utils.converter import MarkItDownConverter

class TestConverter(unittest.TestCase):
    """
    测试 MarkItDownConverter 的转换功能
    """

    def test_basic_text_conversion(self):
        """
        测试纯文本文件的转换
        """
        # 创建一个临时文本文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Hello, World!\nThis is a test.")
            temp_path = f.name
        
        try:
            converter = MarkItDownConverter({})
            result = converter.convert(temp_path)
            # 检查返回结果是否包含原始文本
            self.assertIn("Hello, World!", result)
            self.assertIn("This is a test.", result)
        finally:
            os.remove(temp_path)

    def test_empty_settings(self):
        """
        测试使用空设置初始化转换器
        """
        converter = MarkItDownConverter({})
        self.assertIsNotNone(converter.md)
        self.assertFalse(converter.settings.get("ocr_enabled", False))

    def test_missing_file_raises_error(self):
        """
        测试转换不存在文件时是否抛出异常
        """
        converter = MarkItDownConverter({})
        with self.assertRaises(RuntimeError):
            converter.convert("/path/to/nonexistent/file.txt")

if __name__ == '__main__':
    unittest.main()