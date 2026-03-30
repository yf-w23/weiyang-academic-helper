"""
LLM 服务模块 - 使用 DeepSeek API 进行分析

依赖：
    pip install openai
"""

from typing import Optional

from backend.config import settings


class LLMServiceError(Exception):
    """LLM 服务异常"""
    pass


class LLMService:
    """
    LLM 服务类 - 使用 DeepSeek API
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        """
        初始化 LLM 服务

        Args:
            api_key: DeepSeek API Key（可选，默认从配置读取）
            base_url: DeepSeek Base URL（可选，默认从配置读取）
            model: 模型名称（可选，默认从配置读取）
        """
        self.api_key = api_key or settings.DEEPSEEK_API_KEY
        self.base_url = base_url or settings.DEEPSEEK_BASE_URL
        self.model = model or settings.DEEPSEEK_MODEL

        if not self.api_key:
            raise LLMServiceError("DEEPSEEK_API_KEY 未配置")

        # 延迟导入
        try:
            from openai import OpenAI
            self._client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )
        except ImportError as e:
            raise LLMServiceError(f"无法加载 OpenAI 库: {e}")

    def chat_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        调用 LLM 进行对话补全

        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词（可选）
            temperature: 温度参数（默认 0.7）
            max_tokens: 最大 token 数（可选）

        Returns:
            str: LLM 回复内容

        Raises:
            LLMServiceError: 调用失败
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content
        except Exception as e:
            raise LLMServiceError(f"LLM 调用失败: {e}")

    def analyze_gap(
        self,
        schema: str,
        transcript: str,
        year: str,
        class_name: str,
    ) -> str:
        """
        分析培养方案缺口

        Args:
            schema: 培养方案内容
            transcript: 成绩单内容
            year: 入学年份
            class_name: 班级名称

        Returns:
            str: 分析报告（Markdown 格式）
        """
        from backend.agent.prompts import get_gap_analysis_prompt

        system_prompt = """你是一位专业的学业规划顾问，负责帮助学生分析培养方案完成情况。
请确保分析准确、建议实用，帮助学生明确下一步的选课方向。"""

        prompt = get_gap_analysis_prompt(
            schema=schema,
            transcript=transcript,
            year=year,
            class_name=class_name
        )

        return self.chat_completion(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.5,
            max_tokens=4000,
        )


# 便捷函数
def analyze_gap_with_llm(
    schema: str,
    transcript: str,
    year: str,
    class_name: str,
) -> str:
    """
    便捷函数：分析培养方案缺口

    Args:
        schema: 培养方案内容
        transcript: 成绩单内容
        year: 入学年份
        class_name: 班级名称

    Returns:
        str: 分析报告
    """
    service = LLMService()
    return service.analyze_gap(schema, transcript, year, class_name)
