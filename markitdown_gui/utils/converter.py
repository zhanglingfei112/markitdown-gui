from markitdown import MarkItDown

class MarkItDownConverter:
    """
    MarkItDown 转换引擎封装类
    """
    def __init__(self, settings):
        """
        初始化转换器
        :param settings: 配置字典
        """
        self.settings = settings
        # 初始化微软 MarkItDown 引擎
        self.md = MarkItDown()
        
        # 如果配置了 LLM API Key，则配置 LLM 增强 (示例性实现)
        # MarkItDown 官方支持通过 llm_client 增强转换
        if settings.get("ocr_enabled") and settings.get("llm_api_key"):
            # 这里根据 MarkItDown 实际 API 进行配置
            # 例如: self.md = MarkItDown(llm_client=...)
            pass

    def convert(self, file_path: str) -> str:
        """
        将指定文件转换为 Markdown 文本
        :param file_path: 文件绝对路径
        :return: 转换后的 Markdown 字符串
        :raises: 转换过程中抛出的任何异常
        """
        try:
            # 调用官方引擎转换
            result = self.md.convert(file_path)
            return result.text_content
        except Exception as e:
            # 重新抛出以供 Worker 处理
            raise RuntimeError(f"Conversion failed: {str(e)}")
