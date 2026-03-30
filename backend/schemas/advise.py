"""
培养方案相关 Pydantic 模型
"""
from pydantic import BaseModel, Field


class GapAnalysisRequest(BaseModel):
    """培养方案缺口分析请求模型"""

    enrollment_year: int = Field(..., ge=2021, le=2025, description="入学年份")
    class_name: str = Field(..., min_length=1, description="班级名称，如'未央-电11'")


class GapAnalysisResponse(BaseModel):
    """培养方案缺口分析响应模型"""

    success: bool = Field(True, description="是否分析成功")
    message: str = Field("", description="提示信息")
    analysis_result: str = Field("", description="分析结果（Markdown格式）")
