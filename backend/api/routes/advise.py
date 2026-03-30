"""
培养方案缺口分析路由
"""
import os
import tempfile
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from backend.agent.runner import run_gap_analysis
from backend.api.deps import get_config
from backend.config import Settings
from backend.schemas.advise import GapAnalysisResponse

router = APIRouter(prefix="/advise", tags=["advise"])


@router.post(
    "/gap-analysis",
    response_model=GapAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="培养方案缺口分析",
    description="接收入学年份、班级和成绩单PDF，分析已修课程与培养方案的差距",
)
async def gap_analysis(
    enrollment_year: Annotated[int, Form(..., ge=2021, le=2025, description="入学年份")],
    class_name: Annotated[str, Form(..., min_length=1, description="班级名称，如'未央-电11'")],
    transcript: Annotated[UploadFile, File(..., description="成绩单PDF文件")],
    config: Annotated[Settings, Depends(get_config)],
) -> GapAnalysisResponse:
    """
    培养方案缺口分析
    
    - **enrollment_year**: 入学年份（2021-2025）
    - **class_name**: 班级名称，如"未央-电11"
    - **transcript**: 成绩单PDF文件
    
    返回：
    - 学分完成情况
    - 课组完成情况
    - 未修课程列表
    - 选课建议
    """
    # 验证文件类型
    if transcript.content_type != "application/pdf":
        if not transcript.filename or not transcript.filename.endswith(".pdf"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="只支持PDF格式文件"
            )
    
    # 保存上传的文件到临时位置
    temp_file_path = None
    try:
        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf", mode="wb") as tmp:
            content = await transcript.read()
            tmp.write(content)
            temp_file_path = tmp.name
        
        # 调用 LangGraph Agent 进行分析
        result = run_gap_analysis(
            year=str(enrollment_year),
            class_name=class_name,
            pdf_path=temp_file_path
        )
        
        if not result.get("success"):
            error_msg = result.get("error", "分析失败")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg
            )
        
        # 构建响应
        analysis_result = result.get("result", "")
        
        return GapAnalysisResponse(
            success=True,
            message=f"分析完成：{class_name}（{enrollment_year}级）",
            analysis_result=analysis_result,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"分析过程出错: {str(e)}"
        )
    finally:
        # 清理临时文件
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except:
                pass
