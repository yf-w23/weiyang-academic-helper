"""
培养方案缺口分析路由
"""
import os
import tempfile
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from backend.agent.runner import run_gap_analysis
from backend.agent.tools import extract_transcript_from_pdf
from backend.api.deps import get_config
from backend.config import Settings
from backend.schemas.advise import GapAnalysisResponse
from backend.services.transcript_parser import extract_student_info

router = APIRouter(prefix="/advise", tags=["advise"])


@router.post(
    "/gap-analysis",
    response_model=GapAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="培养方案缺口分析",
    description="接收成绩单PDF，自动识别年级班级并分析已修课程与培养方案的差距",
)
async def gap_analysis(
    transcript: Annotated[UploadFile, File(..., description="成绩单PDF文件")],
    config: Annotated[Settings, Depends(get_config)],
) -> GapAnalysisResponse:
    """
    培养方案缺口分析
    
    - **transcript**: 成绩单PDF文件
    
    系统自动从成绩单中识别入学年份和班级信息，返回：
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
        
        # 先从成绩单中提取年级和班级信息
        transcript_md = extract_transcript_from_pdf(temp_file_path)
        info = extract_student_info(transcript_md)
        year = info.get("year")
        class_name = info.get("class_name")
        
        if not year or not class_name:
            missing = []
            if not year:
                missing.append("入学年份")
            if not class_name:
                missing.append("班级")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无法从成绩单中识别{'、'.join(missing)}信息，请确认上传的是有效的清华大学成绩单"
            )
        
        # 调用 LangGraph Agent 进行分析
        result = run_gap_analysis(
            year=year,
            class_name=class_name,
            transcript_md=transcript_md
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
            message=f"分析完成：{class_name}（{year}级）",
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
